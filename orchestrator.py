"""
Orchestrator — the brain of the RAG chatbot.

Flow:
  user message → intent classify → query rewrite → hybrid retrieve
  → confidence check → context assemble → LLM generate → validate → respond
"""
from __future__ import annotations
import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Generator

from config import settings
from llm_client import LLMClient
from retrieval.engine import hybrid_retrieve, SearchResult

logger = logging.getLogger(__name__)


# ── Intent ───────────────────────────────────────────────────────────────────
class Intent(str, Enum):
    FACTUAL = "factual"
    COMPARISON = "comparison"
    FOLLOW_UP = "follow_up"
    CLARIFY = "clarify"
    OUT_OF_SCOPE = "out_of_scope"
    GREETING = "greeting"


# ── Confidence ───────────────────────────────────────────────────────────────
class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


CONF_META = {
    Confidence.HIGH:   {"color": "#22c55e", "icon": "🟢", "label": "High confidence"},
    Confidence.MEDIUM: {"color": "#f59e0b", "icon": "🟡", "label": "Medium — partial info"},
    Confidence.LOW:    {"color": "#f97316", "icon": "🟠", "label": "Low — limited info"},
    Confidence.NONE:   {"color": "#ef4444", "icon": "🔴", "label": "No relevant info found"},
}


@dataclass
class OrchestratorResult:
    response: str
    sources: list[dict] = field(default_factory=list)
    confidence: Confidence = Confidence.NONE
    intent: str = ""
    rewritten_query: str = ""
    latency_ms: float = 0.0
    fallback: bool = False


# ── Prompts ──────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a helpful assistant that answers questions using ONLY the provided context.

Rules:
- Answer based ONLY on the context below. NEVER fabricate information.
- If the context fully answers the question, answer clearly and cite which source you used.
- If it partially answers, answer what you can and state what's missing.
- If the context doesn't answer, say "I don't have enough information in my knowledge base to answer that."
- Be concise. Don't repeat the question back.
{confidence_note}

Context:
{context}"""

CONFIDENCE_NOTES = {
    Confidence.HIGH: "The context is highly relevant. Provide a confident, detailed answer.",
    Confidence.MEDIUM: "The context may only partially cover the question. Answer what you can, note gaps.",
    Confidence.LOW: "The context has low relevance. Only answer if you find directly relevant info, otherwise say you don't have enough information.",
}

INTENT_PROMPT = """Classify the user query intent. Categories:
- FACTUAL: any question about a topic, product, feature, data, or concept
- COMPARISON: comparing two or more things
- FOLLOW_UP: refers to previous conversation turn (uses "it", "that", "they", etc.)
- CLARIFY: asking for clarification of a previous answer
- GREETING: pure greeting with no question (hi, hello, good morning)
- OUT_OF_SCOPE: clearly personal/unrelated requests (jokes, weather, cooking, etc.) — use sparingly, default to FACTUAL if unsure

Conversation context: {context}
User query: {query}
Respond with ONLY the category name."""

REWRITE_PROMPT = """Rewrite as a self-contained search query using conversation context. If already clear, return unchanged.
Context: {context}
User: {query}
Rewritten query:"""


# ── Fast intent pre-classifier ───────────────────────────────────────────────
# End-anchored: matches ONLY if the whole message is a greeting — nothing else.
_GREETING_ONLY_RE = re.compile(
    r"^\s*(hi+|hello+|hey+|howdy|greetings|good\s+(?:morning|afternoon|evening|day)"
    r"|what'?s\s+up|sup)[\s!?.,]*$",
    re.IGNORECASE,
)


def _fast_classify(query: str) -> Intent | None:
    if _GREETING_ONLY_RE.match(query):
        return Intent.GREETING
    return None


# ── Orchestrator ─────────────────────────────────────────────────────────────
class Orchestrator:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def process(self, user_msg: str, history: list[dict] | None = None) -> OrchestratorResult:
        """Sync processing — returns full result."""
        start = time.time()
        history = history or []
        conv_ctx = self._history_text(history[-6:])

        # 1. classify intent
        intent = self._classify(user_msg, conv_ctx)
        logger.info("intent=%s query=%r", intent, user_msg)

        # 2. short-circuit
        if intent == Intent.GREETING:
            return OrchestratorResult(
                response="Hello! I can answer questions based on my knowledge base. What would you like to know?",
                confidence=Confidence.HIGH, intent=intent.value,
                latency_ms=(time.time()-start)*1000,
            )
        if intent == Intent.OUT_OF_SCOPE:
            return OrchestratorResult(
                response="That's outside the scope of my knowledge base. I can only answer questions about the documents and pages that have been added. Is there something else I can help with?",
                confidence=Confidence.NONE, intent=intent.value, fallback=True,
                latency_ms=(time.time()-start)*1000,
            )

        # 3. rewrite
        query = self._rewrite(user_msg, conv_ctx) if intent == Intent.FOLLOW_UP else user_msg
        if query != user_msg:
            logger.info("rewritten query=%r", query)

        # 4. retrieve
        results = hybrid_retrieve(query)
        logger.info("retrieve returned %d results, top_score=%.3f",
                    len(results), results[0].score if results else 0.0)

        # 5. confidence
        conf = self._assess_confidence(results)
        logger.info("confidence=%s", conf)

        # 6. fallback on NONE
        if conf == Confidence.NONE:
            logger.warning(
                "NONE confidence — top_score=%.4f threshold=%.4f — no answer returned",
                results[0].score if results else 0.0,
                settings.similarity_threshold,
            )
            return OrchestratorResult(
                response="I don't have enough information in my knowledge base to answer that. Could you rephrase, or ask about a topic covered in my sources?",
                confidence=conf, intent=intent.value, rewritten_query=query,
                fallback=True, latency_ms=(time.time()-start)*1000,
            )

        # 7. assemble context
        logger.debug("--- Retrieved chunks ---")
        for i, r in enumerate(results, 1):
            src = r.metadata.get("title", r.metadata.get("source", "?"))
            sec = r.metadata.get("section_title", "")
            preview = (r.text[:120] + "…") if len(r.text) > 120 else r.text
            logger.debug("  [%d] score=%.4f src=%s sec=%s | %s", i, r.score, src, sec, preview)
        context = self._assemble_context(results)
        logger.debug("--- Context sent to LLM (%d chars) ---\n%s", len(context), context)

        # 8. generate
        system = SYSTEM_PROMPT.format(
            confidence_note=CONFIDENCE_NOTES.get(conf, ""),
            context=context,
        )
        msgs = self._build_messages(history, user_msg)
        response = self.llm.generate_with_history(msgs, system=system)

        sources = self._extract_sources(results)
        return OrchestratorResult(
            response=response, sources=sources, confidence=conf,
            intent=intent.value, rewritten_query=query,
            latency_ms=(time.time()-start)*1000,
        )

    def process_stream(self, user_msg: str, history: list[dict] | None = None) -> Generator[str | OrchestratorResult, None, None]:
        """
        Streaming: yields str chunks, then a final OrchestratorResult.
        """
        start = time.time()
        history = history or []
        conv_ctx = self._history_text(history[-6:])

        intent = self._classify(user_msg, conv_ctx)

        # short-circuit
        if intent in (Intent.GREETING, Intent.OUT_OF_SCOPE):
            result = self.process(user_msg, history)
            yield result.response
            yield result
            return

        query = self._rewrite(user_msg, conv_ctx) if intent == Intent.FOLLOW_UP else user_msg
        results = hybrid_retrieve(query)
        conf = self._assess_confidence(results)

        if conf == Confidence.NONE:
            logger.warning(
                "NONE confidence — top_score=%.4f threshold=%.4f — no answer returned",
                results[0].score if results else 0.0,
                settings.similarity_threshold,
            )
            msg = "I don't have enough information in my knowledge base to answer that. Could you rephrase, or ask about a topic covered in my sources?"
            yield msg
            yield OrchestratorResult(
                response=msg, confidence=conf, intent=intent.value,
                rewritten_query=query, fallback=True,
                latency_ms=(time.time()-start)*1000,
            )
            return

        logger.debug("--- Retrieved chunks ---")
        for i, r in enumerate(results, 1):
            src = r.metadata.get("title", r.metadata.get("source", "?"))
            sec = r.metadata.get("section_title", "")
            preview = (r.text[:120] + "…") if len(r.text) > 120 else r.text
            logger.debug("  [%d] score=%.4f src=%s sec=%s | %s", i, r.score, src, sec, preview)
        context = self._assemble_context(results)
        logger.debug("--- Context sent to LLM (%d chars) ---\n%s", len(context), context)
        system = SYSTEM_PROMPT.format(
            confidence_note=CONFIDENCE_NOTES.get(conf, ""), context=context,
        )
        msgs = self._build_messages(history, user_msg)

        full = ""
        for chunk in self.llm.stream_with_history(msgs, system=system):
            full += chunk
            yield chunk

        yield OrchestratorResult(
            response=full, sources=self._extract_sources(results),
            confidence=conf, intent=intent.value, rewritten_query=query,
            latency_ms=(time.time()-start)*1000,
        )

    # ── helpers ──────────────────────────────────────────────────────────────
    def _classify(self, query: str, ctx: str) -> Intent:
        fast = _fast_classify(query)
        if fast:
            return fast
        try:
            resp = self.llm.generate(
                INTENT_PROMPT.format(query=query, context=ctx or "None"),
                system="Respond with ONLY the category.",
                max_tokens=15,
            ).strip().upper().replace(" ", "_")
            return Intent(resp.lower()) if resp.lower() in Intent._value2member_map_ else Intent.FACTUAL
        except Exception:
            logger.exception("Intent classify failed — defaulting to FACTUAL")
            return Intent.FACTUAL

    def _rewrite(self, query: str, ctx: str) -> str:
        try:
            r = self.llm.generate(
                REWRITE_PROMPT.format(query=query, context=ctx),
                system="Rewrite concisely.", max_tokens=80,
            ).strip()
            return r or query
        except Exception:
            logger.exception("Query rewrite failed — using original query")
            return query

    @staticmethod
    def _assess_confidence(results: list[SearchResult]) -> Confidence:
        if not results:
            return Confidence.NONE
        top = results[0].score
        avg = sum(r.score for r in results) / len(results)
        if top < settings.similarity_threshold:
            return Confidence.NONE
        if top < settings.low_confidence_threshold:
            return Confidence.LOW
        if top >= settings.low_confidence_threshold and avg > settings.low_confidence_threshold:
            return Confidence.HIGH
        return Confidence.MEDIUM

    @staticmethod
    def _assemble_context(results: list[SearchResult]) -> str:
        results_sorted = sorted(results, key=lambda r: r.score, reverse=True)  # most relevant first
        blocks, tokens = [], 0
        for i, r in enumerate(results_sorted, 1):
            text = r.parent_text if r.parent_text else r.text
            src = r.metadata.get("title", r.metadata.get("source", "?"))
            sec = r.metadata.get("section_title", "")
            label = f"[Source {i}: {src}" + (f" > {sec}]" if sec else "]")
            block = f"{label}\n{text}"
            est = len(text.split()) * 1.3
            if tokens + est > settings.context_tokens:
                block = f"{label}\n{r.text}"
                est = len(r.text.split()) * 1.3
                if tokens + est > settings.context_tokens:
                    break
            blocks.append(block)
            tokens += est
        return "\n\n---\n\n".join(blocks)

    @staticmethod
    def _extract_sources(results: list[SearchResult]) -> list[dict]:
        seen, sources = set(), []
        for r in results:
            key = r.metadata.get("source", "")
            if key and key not in seen:
                seen.add(key)
                sources.append({
                    "source": key,
                    "title": r.metadata.get("title", key),
                    "section": r.metadata.get("section_title", ""),
                    "score": round(r.score, 3),
                })
        return sources

    @staticmethod
    def _build_messages(history: list[dict], user_msg: str) -> list[dict]:
        msgs = []
        for h in history[-8:]:
            msgs.append({"role": h["role"], "content": h["content"]})
        msgs.append({"role": "user", "content": user_msg})
        return msgs

    @staticmethod
    def _history_text(history: list[dict]) -> str:
        return "\n".join(f"{h['role']}: {h['content']}" for h in history) if history else ""

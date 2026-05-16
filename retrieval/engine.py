"""
Hybrid retrieval engine combining:
  1. Vector search (cosine similarity via ChromaDB)
  2. BM25 keyword search (exact term matching)
  3. Reciprocal Rank Fusion to merge both
  4. Cross-encoder reranking for final precision
"""
from __future__ import annotations
import logging
import re
from dataclasses import dataclass, field

from rank_bm25 import BM25Okapi

from config import settings
from ingestion.pipeline import get_embeddings, get_collection

logger = logging.getLogger(__name__)

WORD_RE = re.compile(r"\w+")


@dataclass
class SearchResult:
    chunk_id: str
    text: str
    score: float
    metadata: dict = field(default_factory=dict)
    parent_text: str | None = None


# ── Vector search ────────────────────────────────────────────────────────────
def vector_search(query: str, top_k: int = 10, where: dict | None = None) -> list[SearchResult]:
    qvec = get_embeddings([query])[0]
    col = get_collection()

    kwargs = {"query_embeddings": [qvec], "n_results": top_k,
              "include": ["documents", "metadatas", "distances"]}
    if where:
        kwargs["where"] = where

    try:
        res = col.query(**kwargs)
    except Exception as e:
        logger.error("Vector search failed: %s", e)
        return []

    results = []
    if res and res["ids"] and res["ids"][0]:
        for i in range(len(res["ids"][0])):
            meta = dict(res["metadatas"][0][i]) if res["metadatas"] else {}
            parent = meta.pop("parent_text", None)
            results.append(SearchResult(
                chunk_id=res["ids"][0][i],
                text=res["documents"][0][i],
                score=1.0 - res["distances"][0][i],
                metadata=meta,
                parent_text=parent or None,
            ))
    return results


# ── BM25 keyword search ──────────────────────────────────────────────────────
_bm25_cache: dict | None = None  # {"count": int, "corpus": list, "bm25": BM25Okapi}


def _get_bm25_index() -> tuple[list, BM25Okapi | None]:
    global _bm25_cache
    col = get_collection()
    count = col.count()

    if _bm25_cache is not None and _bm25_cache["count"] == count and count > 0:
        return _bm25_cache["corpus"], _bm25_cache["bm25"]

    data = col.get(include=["documents", "metadatas"])
    if not data["ids"]:
        _bm25_cache = {"count": 0, "corpus": [], "bm25": None}
        return [], None

    corpus = []
    tokenized = []
    for i, cid in enumerate(data["ids"]):
        meta = dict(data["metadatas"][i]) if data["metadatas"] else {}
        parent = meta.pop("parent_text", None)
        corpus.append({
            "chunk_id": cid,
            "text": data["documents"][i],
            "metadata": meta,
            "parent_text": parent,
        })
        tokenized.append(WORD_RE.findall(data["documents"][i].lower()))

    bm25 = BM25Okapi(tokenized)
    _bm25_cache = {"count": count, "corpus": corpus, "bm25": bm25}
    return corpus, bm25


def keyword_search(query: str, top_k: int = 10) -> list[SearchResult]:
    corpus, bm25 = _get_bm25_index()
    if not corpus or bm25 is None:
        return []

    qtokens = WORD_RE.findall(query.lower())
    scores = bm25.get_scores(qtokens)
    mx = max(scores) if max(scores) > 0 else 1.0

    top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    results = []
    for idx in top_idx:
        if scores[idx] <= 0:
            continue
        d = corpus[idx]
        results.append(SearchResult(
            chunk_id=d["chunk_id"],
            text=d["text"],
            score=scores[idx] / mx,
            metadata=d["metadata"],
            parent_text=d.get("parent_text"),
        ))
    return results


# ── Reciprocal Rank Fusion ───────────────────────────────────────────────────
def rrf_fuse(lists: list[list[SearchResult]], k: int = 60) -> list[SearchResult]:
    scores: dict[str, float] = {}
    best: dict[str, SearchResult] = {}
    for lst in lists:
        for rank, r in enumerate(lst):
            scores[r.chunk_id] = scores.get(r.chunk_id, 0.0) + 1.0 / (k + rank + 1)
            if r.chunk_id not in best or r.score > best[r.chunk_id].score:
                best[r.chunk_id] = r
    ordered = sorted(scores, key=lambda cid: scores[cid], reverse=True)
    merged = []
    for cid in ordered:
        r = best[cid]
        r.score = scores[cid]
        merged.append(r)
    return merged


# ── Cross-encoder reranker ───────────────────────────────────────────────────
_reranker = None


def _get_reranker():
    global _reranker
    if _reranker is None:
        try:
            from sentence_transformers import CrossEncoder
            _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        except Exception:
            _reranker = False
    return _reranker if _reranker is not False else None


def rerank(query: str, results: list[SearchResult], top_k: int) -> list[SearchResult]:
    model = _get_reranker()
    if not model or not results:
        return results[:top_k]
    pairs = [(query, r.text) for r in results]
    sc = model.predict(pairs)
    for r, s in zip(results, sc):
        r.score = float(s)
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_k]


# ── Main entry point ─────────────────────────────────────────────────────────
def hybrid_retrieve(
    query: str,
    top_k: int | None = None,
    final_k: int | None = None,
    use_reranker: bool = True,
) -> list[SearchResult]:
    """Full pipeline: vector + BM25 → RRF → rerank → top results."""
    k = top_k or settings.top_k
    fk = final_k or settings.final_k

    vec = vector_search(query, top_k=k)
    kw = keyword_search(query, top_k=k)
    fused = rrf_fuse([vec, kw], k=settings.rrf_k)

    if use_reranker and len(fused) > fk:
        return rerank(query, fused, top_k=fk)
    return fused[:fk]

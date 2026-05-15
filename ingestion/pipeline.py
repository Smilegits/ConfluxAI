"""
Ingestion pipeline — orchestrates: load → chunk → enrich → embed → store.
Idempotent: re-ingesting replaces old chunks for the same source.
"""
from __future__ import annotations
import logging
import chromadb
from openai import AzureOpenAI

from config import settings
from ingestion.loaders import get_loader, TextLoader, RawDocument
from ingestion.chunker import Chunker, Chunk

logger = logging.getLogger(__name__)

# ── singleton clients ─────────────────────────────────────────────────────────
_embed_client: AzureOpenAI | None = None
_collection: chromadb.Collection | None = None


def _get_embed_client() -> AzureOpenAI:
    global _embed_client
    if _embed_client is None:
        _embed_client = AzureOpenAI(
            api_key=settings.azure_api_key,
            azure_endpoint=settings.azure_endpoint,
            api_version=settings.azure_api_version,
        )
    return _embed_client


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using text-embedding-3-large via Azure OpenAI."""
    client = _get_embed_client()
    response = client.embeddings.create(
        model=settings.azure_embedding_deployment,
        input=texts,
    )
    return [item.embedding for item in response.data]


def get_collection() -> chromadb.Collection:
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=settings.chroma_dir)
        _collection = client.get_or_create_collection(
            name=settings.collection_name, metadata={"hnsw:space": "cosine"},
        )
    return _collection


# ── enrichment (heuristic — no extra LLM call) ──────────────────────────────
def _enrich(chunk: Chunk) -> Chunk:
    section = chunk.metadata.get("section_title", "")
    src = chunk.metadata.get("source_type", "document")
    first = chunk.text.split(".")[0][:100]
    parts = []
    if section:
        parts.append(f"Section '{section}'")
    parts.append(f"from {src}")
    if first:
        parts.append(f"about: {first}")
    summary = ". ".join(parts)
    chunk.metadata["summary"] = summary
    chunk.text = f"[Context: {summary}]\n{chunk.text}"
    return chunk


# ── pipeline ─────────────────────────────────────────────────────────────────
class IngestionPipeline:
    def __init__(self):
        self.chunker = Chunker()

    def ingest_url(self, url: str) -> dict:
        loader, _ = get_loader(url)
        doc = loader.load(url)
        return self._process(doc, url)

    def ingest_file(self, path: str) -> dict:
        loader, _ = get_loader(path)
        doc = loader.load(path)
        return self._process(doc, path)

    def ingest_text(self, text: str, title: str = "Pasted Text") -> dict:
        doc = TextLoader().load(text, title)
        return self._process(doc, f"text:{title}")

    def _process(self, doc: RawDocument, source_key: str) -> dict:
        if not doc.text.strip():
            return {"source": source_key, "status": "empty", "chunks": 0}

        # chunk
        chunks = self.chunker.chunk(doc)
        if not chunks:
            return {"source": source_key, "status": "no_chunks", "chunks": 0}

        # enrich
        for c in chunks:
            _enrich(c)

        # remove old data for this source
        self._remove_source(source_key)

        # embed
        texts = [c.text for c in chunks]
        embeddings = get_embeddings(texts)

        # store
        col = get_collection()
        col.add(
            ids=[c.chunk_id for c in chunks],
            embeddings=embeddings,
            documents=texts,
            metadatas=[{**c.metadata, "content_hash": c.content_hash,
                        "parent_text": c.parent_text or ""} for c in chunks],
        )
        logger.info("Stored %d chunks from %s", len(chunks), source_key)
        return {"source": source_key, "status": "ok", "chunks": len(chunks),
                "title": doc.metadata.get("title", source_key)}

    def _remove_source(self, source_key: str):
        col = get_collection()
        try:
            existing = col.get(where={"source": {"$eq": source_key}})
            if existing and existing["ids"]:
                col.delete(ids=existing["ids"])
        except Exception:
            pass

    def list_sources(self) -> list[dict]:
        col = get_collection()
        try:
            data = col.get(include=["metadatas"])
            sources: dict[str, dict] = {}
            for m in (data["metadatas"] or []):
                key = m.get("source", "unknown")
                if key not in sources:
                    sources[key] = {"source": key, "title": m.get("title", key),
                                    "type": m.get("source_type", "?"), "chunks": 0}
                sources[key]["chunks"] += 1
            return list(sources.values())
        except Exception:
            return []

    def delete_source(self, source_key: str):
        self._remove_source(source_key)

    def total_chunks(self) -> int:
        try:
            return get_collection().count()
        except Exception:
            return 0

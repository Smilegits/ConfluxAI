"""
Ingestion pipeline — orchestrates: load → chunk → enrich → embed → store.
Idempotent: re-ingesting replaces old chunks for same source.
Schema v2: documents store raw text; enriched text used only for embedding.
"""
from __future__ import annotations
import logging
import chromadb
from openai import AzureOpenAI, OpenAI

from config import settings
from ingestion.loaders import get_loader, TextLoader, RawDocument
from ingestion.chunker import Chunker, Chunk

logger = logging.getLogger(__name__)

_SCHEMA_VERSION = "2"

# ── singleton clients ─────────────────────────────────────────────────────────
_embed_client: OpenAI | None = None
_collection: chromadb.Collection | None = None


def _get_embed_client() -> OpenAI:
    global _embed_client
    if _embed_client is None:
        if settings.llm_provider == "azure":
            _embed_client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                azure_endpoint=settings.azure_openai_endpoint,
                api_version=settings.azure_openai_api_version,
            )
        else:
            _embed_client = OpenAI(api_key=settings.openai_api_key)
    return _embed_client


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using the configured provider."""
    client = _get_embed_client()
    model = (
        settings.azure_openai_embedding_deployment
        if settings.llm_provider == "azure"
        else settings.openai_embedding_model
    )
    response = client.embeddings.create(model=model, input=texts)
    return [item.embedding for item in response.data]


def get_collection() -> chromadb.Collection:
    global _collection
    if _collection is None:
        import os
        abs_path = os.path.abspath(settings.chroma_dir)
        files = os.listdir(abs_path) if os.path.exists(abs_path) else ["<directory missing>"]
        logger.debug("ChromaDB path: %s  contents: %s", abs_path, files)
        client = chromadb.PersistentClient(path=abs_path)
        _collection = client.get_or_create_collection(
            name=settings.collection_name, metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _migrate_schema_if_needed(col: chromadb.Collection) -> None:
    """Clear v1 chunks (no source_hash) so a fresh ingest produces a consistent corpus."""
    try:
        data = col.get(include=["metadatas"])
    except Exception:
        logger.exception("Migration check failed — skipping")
        return
    logger.debug("Migration check: %d total chunks in DB", len(data["ids"]))
    if not data["ids"]:
        return
    old_ids = [
        cid for cid, meta in zip(data["ids"], data["metadatas"] or [])
        if (meta or {}).get("schema_version", "1") != _SCHEMA_VERSION
    ]
    logger.debug("Migration check: %d v1 (old) chunks, %d v2 (current) chunks",
                 len(old_ids), len(data["ids"]) - len(old_ids))
    if old_ids:
        logger.warning(
            "Schema upgrade: removing %d v1 chunk(s). Re-run `python ingest.py` to rebuild the knowledge base.",
            len(old_ids),
        )
        col.delete(ids=old_ids)
        logger.warning("Migration done. DB now has %d chunks.", col.count())


# ── enrichment ───────────────────────────────────────────────────────────────
def _enrich(chunk: Chunk) -> str:
    """Return enriched text for embedding. chunk.text stays raw (stored as document)."""
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
    return f"[Context: {summary}]\n{chunk.text}"


# ── pipeline ─────────────────────────────────────────────────────────────────
class IngestionPipeline:
    def __init__(self):
        self.chunker = Chunker()
        _migrate_schema_if_needed(get_collection())

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

        col = get_collection()

        # Skip if content unchanged (same source_hash stored)
        try:
            existing = col.get(where={"source": {"$eq": source_key}}, include=["metadatas"])
            if existing and existing["ids"]:
                stored_hash = (existing["metadatas"][0] or {}).get("source_hash", "")
                if stored_hash == doc.content_hash:
                    return {
                        "source": source_key,
                        "status": "skipped",
                        "chunks": len(existing["ids"]),
                        "title": doc.metadata.get("title", source_key),
                    }
        except Exception:
            logger.warning("Content hash check failed — proceeding with full re-ingest", exc_info=True)

        chunks = self.chunker.chunk(doc)
        if not chunks:
            return {"source": source_key, "status": "no_chunks", "chunks": 0}

        # Enrich → separate embedding texts, chunk.text stays raw
        embed_texts = [_enrich(c) for c in chunks]

        self._remove_source(source_key)

        embeddings = get_embeddings(embed_texts)

        col.add(
            ids=[c.chunk_id for c in chunks],
            embeddings=embeddings,
            documents=[c.text for c in chunks],          # raw text — BM25 searches this
            metadatas=[{
                **c.metadata,
                "content_hash": c.content_hash,
                "source_hash": doc.content_hash,         # whole-document hash for skip check
                "schema_version": _SCHEMA_VERSION,
                "parent_text": c.parent_text or "",
            } for c in chunks],
        )
        logger.info("Stored %d chunks from %s", len(chunks), source_key)
        return {
            "source": source_key,
            "status": "ok",
            "chunks": len(chunks),
            "title": doc.metadata.get("title", source_key),
        }

    def _remove_source(self, source_key: str):
        col = get_collection()
        try:
            existing = col.get(where={"source": {"$eq": source_key}})
            if existing and existing["ids"]:
                col.delete(ids=existing["ids"])
        except Exception:
            logger.exception("Failed to remove old chunks for source: %s", source_key)

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
            logger.exception("list_sources failed")
            return []

    def delete_source(self, source_key: str):
        self._remove_source(source_key)

    def total_chunks(self) -> int:
        try:
            return get_collection().count()
        except Exception:
            logger.exception("total_chunks failed")
            return 0

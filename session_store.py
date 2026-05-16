"""
MongoDB-backed session store.
Persists chat sessions across Streamlit restarts.
Collection: chat_sessions — one document per session.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection

from config import settings
from orchestrator import OrchestratorResult, Confidence

logger = logging.getLogger(__name__)


def _serialize_message(msg: dict) -> dict:
    """Convert in-memory message (may have OrchestratorResult) to MongoDB-safe dict."""
    out = {"role": msg["role"], "content": msg["content"]}
    if "meta" in msg and msg["meta"] is not None:
        m: OrchestratorResult = msg["meta"]
        out["meta"] = {
            "confidence": m.confidence.value,
            "latency_ms": m.latency_ms,
            "sources": m.sources,
            "intent": m.intent,
            "rewritten_query": m.rewritten_query,
            "fallback": m.fallback,
        }
    return out


def _deserialize_message(doc: dict) -> dict:
    """Reconstruct in-memory message from MongoDB document."""
    msg = {"role": doc["role"], "content": doc["content"]}
    if "meta" in doc and doc["meta"]:
        d = doc["meta"]
        msg["meta"] = OrchestratorResult(
            response=doc["content"],
            confidence=Confidence(d.get("confidence", "none")),
            latency_ms=d.get("latency_ms", 0.0),
            sources=d.get("sources", []),
            intent=d.get("intent", ""),
            rewritten_query=d.get("rewritten_query", ""),
            fallback=d.get("fallback", False),
        )
    return msg


class SessionStore:
    def __init__(self):
        self._client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)
        db = self._client[settings.mongodb_db]
        self._col: Collection = db["chat_sessions"]
        # Ping forces connection — raises immediately if MongoDB unreachable
        self._client.admin.command("ping")
        self._col.create_index([("updated_at", ASCENDING)])

    def load_all(self) -> dict[str, dict]:
        """Return {session_id: {name, messages}} sorted by creation time."""
        sessions: dict[str, dict] = {}
        try:
            for doc in self._col.find({}, sort=[("created_at", ASCENDING)]):
                sid = doc["_id"]
                sessions[sid] = {
                    "name": doc.get("name", sid),
                    "messages": [_deserialize_message(m) for m in doc.get("messages", [])],
                }
        except Exception as e:
            logger.error("MongoDB load failed: %s", e)
        return sessions

    def save(self, session_id: str, session: dict) -> None:
        """Upsert session to MongoDB."""
        try:
            self._col.update_one(
                {"_id": session_id},
                {"$set": {
                    "name": session["name"],
                    "messages": [_serialize_message(m) for m in session["messages"]],
                    "updated_at": datetime.now(timezone.utc),
                }, "$setOnInsert": {
                    "created_at": datetime.now(timezone.utc),
                }},
                upsert=True,
            )
        except Exception as e:
            logger.error("MongoDB save failed: %s", e)

    def delete(self, session_id: str) -> None:
        try:
            self._col.delete_one({"_id": session_id})
        except Exception as e:
            logger.error("MongoDB delete failed: %s", e)

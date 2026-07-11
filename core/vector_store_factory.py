"""
Vector Store Abstraction Layer - Enables easy migration between implementations.

This module provides an abstraction for vector storage backends, allowing
the RAG system to migrate from ChromaDB to distributed solutions (Weaviate, Milvus)
without changing the core application code.

Future Migration Path:
- Current: ChromaDB (POC, up to ~100K documents)
- Next: Weaviate Cloud or Self-hosted (100K-10M documents)
- Later: Milvus or Elasticsearch (10M-1B+ documents)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class BaseVectorStore(ABC):
    """Abstract interface for vector store implementations."""

    @abstractmethod
    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """
        Add documents with embeddings to the store.

        Args:
            ids: List of unique document IDs
            embeddings: List of embedding vectors
            documents: List of raw document texts (for BM25 search)
            metadatas: List of metadata dicts per document
        """
        pass

    @abstractmethod
    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of search results with scores
        """
        pass

    @abstractmethod
    def delete(self, ids: List[str], filter: Optional[Dict] = None) -> None:
        """Delete documents."""
        pass

    @abstractmethod
    def get(
        self,
        ids: Optional[List[str]] = None,
        filter: Optional[Dict] = None,
        include: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Retrieve documents."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Get total document count."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close connections and clean up resources."""
        pass


class ChromaVectorStore(BaseVectorStore):
    """ChromaDB implementation (current POC)."""

    def __init__(self, collection):
        """
        Initialize with ChromaDB collection.

        Args:
            collection: chromadb.Collection instance
        """
        self.collection = collection
        logger.info("Initialized ChromaVectorStore (POC, up to ~100K documents)")

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """Add documents to ChromaDB."""
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Search ChromaDB."""
        result = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=filter if filter else None,
            include=["documents", "metadatas", "distances"]
        )

        results = []
        if result and result["ids"] and result["ids"][0]:
            for idx, doc_id in enumerate(result["ids"][0]):
                distance = result["distances"][0][idx]
                score = 1.0 - (distance / 2.0)

                results.append({
                    "id": doc_id,
                    "score": score,
                    "document": result["documents"][0][idx] if result["documents"] else "",
                    "metadata": result["metadatas"][0][idx] if result["metadatas"] else {}
                })

        return results

    def delete(self, ids: List[str], filter: Optional[Dict] = None) -> None:
        """Delete documents from ChromaDB."""
        if ids:
            self.collection.delete(ids=ids)
        elif filter:
            data = self.collection.get(where=filter)
            if data and data["ids"]:
                self.collection.delete(ids=data["ids"])

    def get(
        self,
        ids: Optional[List[str]] = None,
        filter: Optional[Dict] = None,
        include: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Retrieve documents from ChromaDB."""
        return self.collection.get(
            ids=ids,
            where=filter if filter else None,
            include=include if include else ["documents", "metadatas"]
        )

    def count(self) -> int:
        """Get document count from ChromaDB."""
        return self.collection.count()

    def close(self) -> None:
        """ChromaDB doesn't require explicit closing."""
        pass


class WeaviateVectorStore(BaseVectorStore):
    """
    Weaviate implementation (future production scale).

    Supports:
    - 100K-1B+ documents
    - Distributed deployment on Azure/cloud
    - Multi-tenancy
    - Advanced filtering and metadata search

    Migration trigger: >100K documents or retrieval latency >2s (p95)
    Estimated cost: $200-500/month on Azure
    """

    def __init__(self, client):
        """Initialize Weaviate client."""
        self.client = client
        logger.warning(
            "Weaviate implementation is a stub. "
            "Migration needed when ChromaDB hits limits."
        )

    def add(self, ids, embeddings, documents, metadatas) -> None:
        """Add documents to Weaviate."""
        raise NotImplementedError("Weaviate migration not yet implemented")

    def search(self, query_vector, top_k=10, filter=None):
        """Search Weaviate."""
        raise NotImplementedError("Weaviate migration not yet implemented")

    def delete(self, ids, filter=None) -> None:
        """Delete documents from Weaviate."""
        raise NotImplementedError("Weaviate migration not yet implemented")

    def get(self, ids=None, filter=None, include=None):
        """Retrieve documents from Weaviate."""
        raise NotImplementedError("Weaviate migration not yet implemented")

    def count(self) -> int:
        """Get document count from Weaviate."""
        raise NotImplementedError("Weaviate migration not yet implemented")

    def close(self) -> None:
        """Close Weaviate connection."""
        pass


def get_vector_store(store_type: str = "chromadb", **kwargs) -> BaseVectorStore:
    """
    Factory function to create vector store instances.

    Args:
        store_type: Type of vector store ("chromadb", "weaviate", "milvus")
        **kwargs: Store-specific configuration

    Returns:
        Configured vector store instance
    """
    if store_type == "chromadb":
        collection = kwargs.get("collection")
        if not collection:
            raise ValueError("ChromaDB requires 'collection' parameter")
        return ChromaVectorStore(collection)

    elif store_type == "weaviate":
        client = kwargs.get("client")
        if not client:
            raise ValueError("Weaviate requires 'client' parameter")
        return WeaviateVectorStore(client)

    else:
        raise ValueError(f"Unknown vector store type: {store_type}")

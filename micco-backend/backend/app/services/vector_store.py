"""
Vector Store Service
Handles ChromaDB operations for storing and retrieving document embeddings.
"""
from __future__ import annotations

import logging
from typing import Sequence, Optional, TYPE_CHECKING
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Global ChromaDB client
_chroma_client: Optional[chromadb.HttpClient] = None


def get_chroma_client() -> chromadb.HttpClient:
    """Get or create the ChromaDB client singleton."""
    global _chroma_client

    if _chroma_client is None:
        logger.info(f"Connecting to ChromaDB at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
        _chroma_client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
            settings=ChromaSettings(
                anonymized_telemetry=False,
            )
        )
        # Test connection
        _chroma_client.heartbeat()
        logger.info("Connected to ChromaDB successfully")

    return _chroma_client


class VectorStore:
    """
    Vector store service for managing document embeddings in ChromaDB.
    Each knowledge base has its own collection for namespace isolation.
    """

    COLLECTION_PREFIX = "kb_"

    def __init__(self, workspace_id: int):
        self.workspace_id = workspace_id
        self.collection_name = f"{self.COLLECTION_PREFIX}{workspace_id}"
        self._collection = None

    @property
    def collection(self) -> chromadb.Collection:
        """Get or create the collection."""
        if self._collection is None:
            client = get_chroma_client()
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def _recreate_collection(self) -> None:
        """Delete and recreate the collection (resets cached reference)."""
        client = get_chroma_client()
        try:
            client.delete_collection(self.collection_name)
            logger.info(f"Deleted collection {self.collection_name} for dimension migration")
        except Exception:
            pass
        self._collection = None
        # Force re-creation
        _ = self.collection

    def add_documents(
        self,
        ids: Sequence[str],
        embeddings: Sequence[list[float]],
        documents: Sequence[str],
        metadatas: Sequence[dict] | None = None
    ) -> None:
        """
        Add documents with their embeddings to the collection.
        Auto-handles dimension mismatch: if the collection was created with
        a different embedding dimension, it is deleted and recreated.
        """
        if not ids:
            return

        try:
            self.collection.add(
                ids=list(ids),
                embeddings=list(embeddings),
                documents=list(documents),
                metadatas=list(metadatas) if metadatas else None
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "dimension" in error_msg:
                # Dimension mismatch — collection was created with old embedding model
                logger.warning(
                    f"Dimension mismatch in {self.collection_name}: {e}. "
                    f"Recreating collection for new embedding model."
                )
                self._recreate_collection()
                # Retry with fresh collection
                self.collection.add(
                    ids=list(ids),
                    embeddings=list(embeddings),
                    documents=list(documents),
                    metadatas=list(metadatas) if metadatas else None
                )
            else:
                raise

        logger.info(f"Added {len(ids)} documents to collection {self.collection_name}")

    def query(
        self,
        query_embedding: list[float],
        n_results: int = 5,
        where: dict | None = None,
        include: list[str] | None = None
    ) -> dict:
        """Query the collection for similar documents."""
        if include is None:
            include = ["documents", "metadatas", "distances"]

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=include
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "dimension" in error_msg:
                # Query with new-dimension embedding against old collection
                logger.warning(
                    f"Dimension mismatch on query in {self.collection_name}: {e}. "
                    f"Collection needs reindexing."
                )
                return {"ids": [], "documents": [], "metadatas": [], "distances": []}
            raise

        # Flatten single query results
        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "documents": results["documents"][0] if results.get("documents") else [],
            "metadatas": results["metadatas"][0] if results.get("metadatas") else [],
            "distances": results["distances"][0] if results.get("distances") else []
        }

    def delete_by_document_id(self, document_id: int) -> None:
        """Delete all chunks belonging to a specific document."""
        self.collection.delete(
            where={"document_id": document_id}
        )
        logger.info(f"Deleted chunks for document {document_id} from collection {self.collection_name}")

    def delete_collection(self) -> None:
        """Delete the entire collection for this knowledge base."""
        client = get_chroma_client()
        try:
            client.delete_collection(self.collection_name)
            self._collection = None
            logger.info(f"Deleted collection {self.collection_name}")
        except Exception as e:
            logger.warning(f"Failed to delete collection {self.collection_name}: {e}")

    def count(self) -> int:
        """Return the number of documents in the collection."""
        return self.collection.count()

    def get_by_ids(self, ids: Sequence[str]) -> dict:
        """Get documents by their IDs."""
        return self.collection.get(
            ids=list(ids),
            include=["documents", "metadatas"]
        )


def get_vector_store(workspace_id: int) -> VectorStore:
    """Factory function to create a VectorStore for a knowledge base."""
    return VectorStore(workspace_id)

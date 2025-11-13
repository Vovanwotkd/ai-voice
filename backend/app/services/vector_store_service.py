"""
Vector store service using ChromaDB for semantic search
"""

import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import uuid

from app.models import DocumentChunk
from app.database import Session

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing vector embeddings in ChromaDB"""

    def __init__(self, persist_directory: str = "data/chroma"):
        """
        Initialize ChromaDB client

        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))

        # Get or create collection
        self.collection_name = "restaurant_knowledge"
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Restaurant knowledge base for RAG"}
        )

        logger.info(f"✅ ChromaDB initialized with collection '{self.collection_name}'")

    async def add_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
        db: Session
    ) -> None:
        """
        Add document chunks with embeddings to vector store

        Args:
            chunks: List of DocumentChunk objects
            embeddings: Corresponding embedding vectors
            db: Database session
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")

        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        embeddings_list = []

        for chunk, embedding in zip(chunks, embeddings):
            # Generate unique ID for ChromaDB
            chromadb_id = str(uuid.uuid4())

            ids.append(chromadb_id)
            documents.append(chunk.content)

            # Metadata for filtering and retrieval
            metadata = {
                "chunk_id": str(chunk.id),
                "document_id": str(chunk.document_id),
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count or 0,
            }

            # Add any additional metadata from chunk
            if chunk.meta_data:
                metadata.update(chunk.meta_data)

            metadatas.append(metadata)
            embeddings_list.append(embedding)

            # Save ChromaDB ID back to chunk
            chunk.chromadb_id = chromadb_id

        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings_list,
            metadatas=metadatas
        )

        # Update chunks in database
        db.commit()

        logger.info(f"✅ Added {len(chunks)} chunks to vector store")

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for relevant chunks

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of search results with content and metadata
        """
        # Build where clause for filtering
        where = filter_metadata if filter_metadata else None

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where
        )

        # Format results
        search_results = []

        if results and results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                result = {
                    "id": doc_id,
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None
                }
                search_results.append(result)

        logger.info(f"Found {len(search_results)} results for query")
        return search_results

    async def delete_document_chunks(self, document_id: str) -> None:
        """
        Delete all chunks for a document from vector store

        Args:
            document_id: Document ID to delete
        """
        # Find all chunks for this document
        results = self.collection.get(
            where={"document_id": document_id}
        )

        if results and results['ids']:
            # Delete chunks
            self.collection.delete(
                ids=results['ids']
            )

            logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
        else:
            logger.warning(f"No chunks found for document {document_id}")

    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection

        Returns:
            Dict with collection stats
        """
        count = self.collection.count()

        return {
            "collection_name": self.collection_name,
            "total_chunks": count,
            "embedding_dimension": 1536  # OpenAI text-embedding-3-small
        }


# Create singleton instance
vector_store_service = VectorStoreService()

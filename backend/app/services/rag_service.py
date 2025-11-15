"""
RAG (Retrieval-Augmented Generation) service
Combines vector search with LLM to provide contextual answers
"""

import logging
from typing import List, Dict, Any, Optional

from app.services.embeddings_service import embeddings_service
from app.services.yandex_embeddings_service import yandex_embeddings_service
from app.services.vector_store_service import vector_store_service
from app.services.llm_service import llm_service
from app.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG-based question answering"""

    def __init__(self):
        # Select embeddings provider based on config
        if settings.EMBEDDINGS_PROVIDER == "yandex":
            self.embeddings = yandex_embeddings_service
            logger.info("✅ Using Yandex embeddings for RAG")
        else:
            self.embeddings = embeddings_service
            logger.info("✅ Using OpenAI embeddings for RAG")

        self.vector_store = vector_store_service
        self.llm = llm_service

        # RAG configuration
        self.top_k = 5  # Number of chunks to retrieve
        self.max_context_tokens = 2000  # Maximum tokens for context

    async def retrieve_context(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context chunks for a query

        Args:
            query: User query
            top_k: Number of chunks to retrieve (default: self.top_k)

        Returns:
            List of relevant chunks with content and metadata
        """
        k = top_k or self.top_k

        # Generate embedding for query
        query_embedding = await self.embeddings.generate_embedding(query)

        # Search vector store
        results = await self.vector_store.search(
            query_embedding=query_embedding,
            top_k=k
        )

        logger.info(f"Retrieved {len(results)} context chunks for query: '{query[:50]}...'")
        return results

    def build_context_prompt(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Build context string from retrieved chunks

        Args:
            chunks: List of retrieved chunks

        Returns:
            Formatted context string
        """
        if not chunks:
            return ""

        context_parts = []

        for i, chunk in enumerate(chunks, 1):
            content = chunk['content'].strip()
            context_parts.append(f"[Документ {i}]\n{content}")

        context = "\n\n".join(context_parts)

        return f"""
Используй следующую информацию из базы знаний для ответа на вопрос клиента:

{context}

Если информация не помогает ответить на вопрос, используй свои общие знания, но упомяни что конкретной информации нет в базе.
""".strip()

    async def answer_with_context(
        self,
        query: str,
        conversation_history: List[Dict[str, str]],
        system_prompt: str,
        use_rag: bool = True
    ) -> Dict[str, Any]:
        """
        Generate answer using RAG

        Args:
            query: User question
            conversation_history: Previous messages
            system_prompt: System prompt for the bot
            use_rag: Whether to use RAG (default: True)

        Returns:
            Dict with response and metadata
        """
        context_chunks = []
        rag_context = ""

        if use_rag:
            # Retrieve relevant context
            context_chunks = await self.retrieve_context(query)

            if context_chunks:
                # Build context prompt
                rag_context = self.build_context_prompt(context_chunks)

        # Combine system prompt with RAG context
        if rag_context:
            enhanced_prompt = f"{system_prompt}\n\n{rag_context}"
        else:
            enhanced_prompt = system_prompt

        # Generate response using LLM
        llm_response = await self.llm.generate_response(
            message=query,
            conversation_history=conversation_history,
            system_prompt=enhanced_prompt
        )

        # Add metadata
        result = {
            "content": llm_response["content"],
            "usage": llm_response.get("usage", {}),
            "rag_used": use_rag and len(context_chunks) > 0,
            "context_chunks": len(context_chunks),
            "chunks": context_chunks if context_chunks else []
        }

        logger.info(
            f"Generated RAG answer: {len(context_chunks)} chunks used, "
            f"response length: {len(result['content'])} chars"
        )

        return result

    async def index_document_chunks(
        self,
        chunks: List[Any],  # DocumentChunk objects
        db: Any  # Session
    ) -> None:
        """
        Index document chunks in vector store

        Args:
            chunks: List of DocumentChunk objects
            db: Database session
        """
        if not chunks:
            logger.warning("No chunks to index")
            return

        # Extract text content from chunks
        texts = [chunk.content for chunk in chunks]

        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = await self.embeddings.generate_embeddings_batch(texts)

        # Add to vector store
        await self.vector_store.add_chunks(
            chunks=chunks,
            embeddings=embeddings,
            db=db
        )

        logger.info(f"✅ Successfully indexed {len(chunks)} chunks")

    async def delete_document_from_index(self, document_id: str) -> None:
        """
        Remove document chunks from vector store

        Args:
            document_id: Document ID to remove
        """
        await self.vector_store.delete_document_chunks(document_id)
        logger.info(f"Deleted document {document_id} from index")


# Create singleton instance
rag_service = RAGService()

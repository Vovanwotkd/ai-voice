"""
Embeddings service for generating vector representations of text
Uses OpenAI embeddings API
"""

import logging
from typing import List
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service for generating text embeddings using OpenAI"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "text-embedding-3-small"  # 1536 dimensions, cheap and fast
        self.dimensions = 1536

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Input text

        Returns:
            List[float]: Embedding vector
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )

            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding for text: '{text[:50]}...'")

            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch

        Args:
            texts: List of input texts

        Returns:
            List[List[float]]: List of embedding vectors
        """
        try:
            # OpenAI allows up to 2048 inputs per request
            batch_size = 2048

            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]

                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )

                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                logger.info(f"Generated {len(batch_embeddings)} embeddings (batch {i // batch_size + 1})")

            logger.info(f"✅ Generated {len(all_embeddings)} embeddings total")
            return all_embeddings

        except Exception as e:
            logger.error(f"Failed to generate embeddings batch: {e}")
            raise


# Create singleton instance
embeddings_service = EmbeddingsService()

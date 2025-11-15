"""
Yandex Embeddings service for generating vector representations of text
Uses Yandex Foundation Models API
"""

import logging
from typing import List
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class YandexEmbeddingsService:
    """Service for generating text embeddings using Yandex Foundation Models"""

    def __init__(self):
        self.api_key = settings.YANDEX_API_KEY
        self.folder_id = settings.YANDEX_FOLDER_ID
        self.url = "https://llm.api.cloud.yandex.net/foundationModels/v1/textEmbedding"
        self.model_uri = f"emb://{self.folder_id}/text-search-doc/latest"
        self.dimensions = 256  # Yandex text-search-doc has 256 dimensions

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Input text

        Returns:
            List[float]: Embedding vector (256 dimensions)
        """
        try:
            headers = {
                "Authorization": f"Api-Key {self.api_key}",
                "Content-Type": "application/json",
                "x-folder-id": self.folder_id
            }

            data = {
                "modelUri": self.model_uri,
                "text": text
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.url, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()

                # Extract embedding from response
                embedding = result["embedding"]
                logger.debug(f"Generated embedding for text: '{text[:50]}...'")

                return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Note: Yandex doesn't support batch API, so we process one by one

        Args:
            texts: List of input texts

        Returns:
            List[List[float]]: List of embedding vectors
        """
        try:
            all_embeddings = []

            for i, text in enumerate(texts):
                embedding = await self.generate_embedding(text)
                all_embeddings.append(embedding)

                if (i + 1) % 10 == 0:
                    logger.info(f"Generated {i + 1}/{len(texts)} embeddings")

            logger.info(f"✅ Generated {len(all_embeddings)} Yandex embeddings total")
            return all_embeddings

        except Exception as e:
            logger.error(f"Failed to generate embeddings batch: {e}")
            raise


# Create singleton instance
yandex_embeddings_service = YandexEmbeddingsService()

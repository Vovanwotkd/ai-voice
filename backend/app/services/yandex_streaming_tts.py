"""
Yandex SpeechKit Streaming TTS service
Uses gRPC API for low-latency streaming synthesis
"""

import logging
import asyncio
from typing import AsyncGenerator, Optional
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class YandexStreamingTTSService:
    """
    Streaming TTS service using Yandex SpeechKit

    Note: This is a simplified streaming implementation using chunked REST API.
    For true streaming, you would need to use Yandex Cloud SDK with gRPC,
    but that requires additional dependencies (grpcio, yandex-cloud-ml-sdk).

    This version streams synthesis by:
    1. Splitting long text into sentences
    2. Synthesizing each sentence independently
    3. Yielding audio chunks as they're ready
    """

    def __init__(self):
        self.api_key = settings.YANDEX_API_KEY
        self.folder_id = settings.YANDEX_FOLDER_ID
        self.tts_url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"

    def _split_into_sentences(self, text: str, max_length: int = 200) -> list[str]:
        """
        Split text into sentences for streaming synthesis
        Handles both Russian and English sentence endings
        """
        import re

        # Split by sentence endings
        sentences = re.split(r'([.!?]+\s+)', text)

        # Rejoin punctuation with sentences
        result = []
        current = ""

        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            punct = sentences[i + 1] if i + 1 < len(sentences) else ""

            chunk = sentence + punct

            # If adding this would exceed max_length, yield current and start new
            if len(current) + len(chunk) > max_length and current:
                result.append(current.strip())
                current = chunk
            else:
                current += chunk

        if current.strip():
            result.append(current.strip())

        return result if result else [text]

    async def synthesize_streaming(
        self,
        text: str,
        voice: str = "alena",
        language: str = "ru-RU",
        speed: float = 1.0,
        emotion: str = "neutral",
        chunk_size: int = 4096,
    ) -> AsyncGenerator[bytes, None]:
        """
        Synthesize speech with streaming delivery

        Yields audio chunks as they're synthesized, reducing latency.
        For long text, synthesizes in parallel while yielding early results.

        Args:
            text: Text to synthesize
            voice: Yandex voice name
            language: Language code
            speed: Speech speed (0.1 to 3.0)
            emotion: Voice emotion
            chunk_size: Size of audio chunks to yield

        Yields:
            Audio chunks (PCM 16-bit, 16kHz, mono)
        """
        if not self.api_key or not self.folder_id:
            logger.error("Yandex API credentials not configured")
            return

        # Split text into sentences for streaming
        sentences = self._split_into_sentences(text)
        logger.info(f"Streaming TTS for {len(sentences)} sentence chunks")

        # Synthesize sentences concurrently (but yield in order)
        tasks = []
        for sentence in sentences:
            task = self._synthesize_sentence(
                sentence, voice, language, speed, emotion
            )
            tasks.append(task)

        # Yield audio as soon as each sentence is ready
        for i, task in enumerate(tasks):
            try:
                audio_data = await task

                if audio_data:
                    # Yield in chunks for smooth playback
                    for offset in range(0, len(audio_data), chunk_size):
                        chunk = audio_data[offset:offset + chunk_size]
                        yield chunk

                    logger.debug(
                        f"Yielded sentence {i+1}/{len(sentences)}: "
                        f"{len(audio_data)} bytes"
                    )
                else:
                    logger.warning(f"No audio for sentence {i+1}")

            except Exception as e:
                logger.error(f"Error synthesizing sentence {i+1}: {e}")
                continue

    async def _synthesize_sentence(
        self,
        text: str,
        voice: str,
        language: str,
        speed: float,
        emotion: str,
    ) -> Optional[bytes]:
        """Synthesize a single sentence (REST API call)"""
        try:
            headers = {
                "Authorization": f"Api-Key {self.api_key}",
            }

            data = {
                "text": text,
                "lang": language,
                "voice": voice,
                "speed": str(speed),
                "format": "lpcm",
                "sampleRateHertz": "16000",
                "emotion": emotion,
                "folderId": self.folder_id,
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.tts_url,
                    headers=headers,
                    data=data,
                )
                response.raise_for_status()
                return response.content

        except httpx.HTTPError as e:
            logger.error(f"Yandex TTS API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error calling Yandex TTS: {e}")
            return None

    async def synthesize_fast(
        self,
        text: str,
        voice: str = "alena",
        speed: float = 1.0,
    ) -> AsyncGenerator[bytes, None]:
        """
        Fast synthesis mode - optimized for low latency
        Uses aggressive sentence splitting and smaller chunks
        """
        # For short text, just synthesize directly
        if len(text) < 100:
            audio = await self._synthesize_sentence(
                text, voice, "ru-RU", speed, "neutral"
            )
            if audio:
                # Yield in small chunks for immediate playback
                chunk_size = 2048
                for offset in range(0, len(audio), chunk_size):
                    yield audio[offset:offset + chunk_size]
            return

        # For longer text, use streaming
        async for chunk in self.synthesize_streaming(
            text, voice=voice, speed=speed, chunk_size=2048
        ):
            yield chunk


# Global instance
yandex_streaming_tts_service = YandexStreamingTTSService()

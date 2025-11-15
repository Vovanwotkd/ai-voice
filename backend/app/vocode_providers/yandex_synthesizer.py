"""
Yandex SpeechKit Synthesizer for Vocode
Uses REST API for text-to-speech
"""

import asyncio
import logging
from typing import AsyncGenerator
import aiohttp

from vocode.streaming.synthesizer.base_synthesizer import BaseSynthesizer, SynthesisResult
from vocode.streaming.models.synthesizer import SynthesizerConfig
from vocode.streaming.models.audio import AudioEncoding

from app.config import settings

logger = logging.getLogger(__name__)


class YandexSynthesizerConfig(SynthesizerConfig):
    """Configuration for Yandex Synthesizer"""

    voice: str = "alena"  # Yandex voice
    language_code: str = "ru-RU"
    speed: float = 0.8  # Slower speech to compensate for fast playback
    emotion: str = "neutral"  # neutral | good | evil

    def __init__(self, **data):
        super().__init__(
            sampling_rate=16000,
            audio_encoding=AudioEncoding.LINEAR16,
            **data
        )


class YandexSynthesizer(BaseSynthesizer[YandexSynthesizerConfig]):
    """
    Yandex SpeechKit Synthesizer for Vocode
    Uses REST API for speech synthesis
    """

    def __init__(self, synthesizer_config: YandexSynthesizerConfig):
        super().__init__(synthesizer_config)

        self.api_key = settings.YANDEX_API_KEY
        if not self.api_key:
            raise ValueError("YANDEX_API_KEY is required")

        self.folder_id = settings.YANDEX_FOLDER_ID
        self.api_url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"

        logger.info(
            f"YandexSynthesizer initialized: voice={synthesizer_config.voice}, "
            f"language={synthesizer_config.language_code}"
        )

    async def create_speech_uncached(
        self,
        message: str,
        chunk_size: int,
        is_first_text_chunk: bool = False,
        is_sole_text_chunk: bool = False,
    ) -> SynthesisResult:
        """
        Synthesize speech from text

        Args:
            message: Text to synthesize
            chunk_size: Size of audio chunks
            is_first_text_chunk: Whether this is the first chunk
            is_sole_text_chunk: Whether this is the only chunk

        Returns:
            SynthesisResult with audio generator
        """

        async def chunk_generator() -> AsyncGenerator[bytes, None]:
            """Generator that yields audio chunks"""
            try:
                # Synthesize audio
                audio_data = await self._synthesize_yandex(message)

                if audio_data:
                    # Yield in chunks
                    for i in range(0, len(audio_data), chunk_size):
                        chunk = audio_data[i:i + chunk_size]
                        yield chunk

                    logger.info(f"Synthesized {len(audio_data)} bytes for: '{message[:50]}...'")
                else:
                    logger.warning(f"No audio data for: {message}")

            except Exception as e:
                logger.error(f"Error in chunk generator: {e}", exc_info=True)

        return SynthesisResult(
            chunk_generator=chunk_generator(),
            get_message_up_to=lambda seconds: message,  # Return full message
        )

    async def _synthesize_yandex(self, text: str) -> bytes:
        """Call Yandex TTS API for synthesis"""
        try:
            headers = {
                "Authorization": f"Api-Key {self.api_key}",
            }

            data = {
                "text": text,
                "lang": self.synthesizer_config.language_code,
                "voice": self.synthesizer_config.voice,
                "speed": str(self.synthesizer_config.speed),
                "format": "lpcm",
                "sampleRateHertz": "16000",
                "emotion": self.synthesizer_config.emotion,
            }

            if self.folder_id:
                data["folderId"] = self.folder_id

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        content_type = response.headers.get('Content-Type', 'unknown')
                        logger.info(f"Yandex TTS response: {len(audio_data)} bytes, Content-Type: {content_type}")
                        logger.debug(f"Request params: format=lpcm, sampleRateHertz=16000")
                        return audio_data
                    else:
                        error_text = await response.text()
                        logger.error(f"Yandex TTS error {response.status}: {error_text}")
                        return b""

        except Exception as e:
            logger.error(f"Error calling Yandex TTS: {e}")
            return b""

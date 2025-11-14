"""
Yandex SpeechKit Transcriber for Vocode
Simplified version using REST API
"""

import asyncio
import logging
import base64
from typing import Optional
import aiohttp

from vocode.streaming.transcriber.base_transcriber import BaseAsyncTranscriber, Transcription
from vocode.streaming.models.transcriber import TranscriberConfig
from vocode.streaming.models.audio import AudioEncoding

from app.config import settings

logger = logging.getLogger(__name__)


class YandexTranscriberConfig(TranscriberConfig):
    """Configuration for Yandex Transcriber"""

    language_code: str = "ru-RU"

    def __init__(self, **data):
        # Set required Vocode fields
        super().__init__(
            sampling_rate=16000,
            audio_encoding=AudioEncoding.LINEAR16,
            chunk_size=2048,  # 2048 bytes chunks
            **data
        )


class YandexTranscriber(BaseAsyncTranscriber[YandexTranscriberConfig]):
    """
    Yandex SpeechKit Transcriber for Vocode
    Uses REST API for speech recognition
    """

    def __init__(self, transcriber_config: YandexTranscriberConfig):
        super().__init__(transcriber_config)

        self.api_key = settings.YANDEX_API_KEY
        if not self.api_key:
            raise ValueError("YANDEX_API_KEY is required")

        self.folder_id = settings.YANDEX_FOLDER_ID
        self.api_url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"

        # Buffer for accumulating audio
        self.audio_buffer = bytearray()
        self.min_audio_length = 16000  # Minimum 1 second of audio

        logger.info(f"YandexTranscriber initialized: language={transcriber_config.language_code}")

    async def _run_loop(self):
        """Main transcription loop"""
        try:
            while not self._ended:
                try:
                    # Get audio chunk from input queue
                    chunk = await asyncio.wait_for(
                        self.input_queue.get(),
                        timeout=1.0
                    )

                    # Accumulate audio
                    self.audio_buffer.extend(chunk)

                    # When we have enough audio, transcribe it
                    if len(self.audio_buffer) >= self.min_audio_length:
                        await self._transcribe_buffer()

                except asyncio.TimeoutError:
                    # No audio for 1 second
                    # If we have accumulated audio, transcribe it
                    if len(self.audio_buffer) > 0:
                        await self._transcribe_buffer()
                    continue

        except Exception as e:
            logger.error(f"Error in transcription loop: {e}", exc_info=True)

    async def _transcribe_buffer(self):
        """Transcribe accumulated audio buffer"""
        if len(self.audio_buffer) == 0:
            return

        try:
            # Prepare audio data
            audio_data = bytes(self.audio_buffer)
            self.audio_buffer.clear()

            # Call Yandex API
            text = await self._recognize_yandex(audio_data)

            if text and text.strip():
                logger.info(f"Transcribed: {text}")

                # Send transcription result
                transcription = Transcription(
                    message=text,
                    confidence=1.0,
                    is_final=True
                )
                self.output_queue.put_nowait(transcription)

        except Exception as e:
            logger.error(f"Error transcribing buffer: {e}", exc_info=True)

    async def _recognize_yandex(self, audio_data: bytes) -> Optional[str]:
        """Call Yandex SpeechKit API for recognition"""
        try:
            headers = {
                "Authorization": f"Api-Key {self.api_key}",
            }

            params = {
                "lang": self.transcriber_config.language_code,
                "format": "lpcm",
                "sampleRateHertz": "16000",
            }

            if self.folder_id:
                params["folderId"] = self.folder_id

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    params=params,
                    data=audio_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("result", "")
                    else:
                        error_text = await response.text()
                        logger.error(f"Yandex API error {response.status}: {error_text}")
                        return None

        except Exception as e:
            logger.error(f"Error calling Yandex API: {e}")
            return None

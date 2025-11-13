"""
Yandex SpeechKit STT (Speech-to-Text) service
Converts audio to text using Yandex Cloud Speech Recognition API
"""

import httpx
import logging
import io
from typing import Optional
from pydub import AudioSegment
from app.config import settings

logger = logging.getLogger(__name__)


class YandexSTTService:
    """Service for converting speech to text using Yandex SpeechKit"""

    def __init__(self):
        self.api_key = settings.YANDEX_API_KEY
        self.folder_id = settings.YANDEX_FOLDER_ID
        self.stt_url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"

    def _convert_to_wav(self, audio_data: bytes, source_format: str = "webm") -> bytes:
        """
        Convert audio to WAV PCM format for Yandex STT.

        Args:
            audio_data: Input audio bytes
            source_format: Source format (webm, ogg, mp3, etc.)

        Returns:
            WAV audio bytes (16kHz, mono, 16-bit PCM)
        """
        try:
            # Load audio from bytes
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format=source_format)

            # Convert to the format Yandex expects:
            # - 16kHz sample rate
            # - Mono channel
            # - 16-bit PCM
            audio = audio.set_frame_rate(16000)
            audio = audio.set_channels(1)
            audio = audio.set_sample_width(2)  # 16-bit = 2 bytes

            # Export as WAV
            wav_buffer = io.BytesIO()
            audio.export(wav_buffer, format="wav")
            wav_bytes = wav_buffer.getvalue()

            logger.debug(f"Converted {len(audio_data)} bytes of {source_format} to {len(wav_bytes)} bytes of WAV")
            return wav_bytes

        except Exception as e:
            logger.error(f"Failed to convert audio: {e}")
            raise

    async def recognize_audio(
        self,
        audio_data: bytes,
        language: str = "ru-RU",
        format: str = "webm"
    ) -> Optional[str]:
        """
        Recognize speech from audio data.

        Args:
            audio_data: Audio file bytes
            language: Recognition language (default: ru-RU)
            format: Source audio format (webm, ogg, mp3, etc.)

        Returns:
            Recognized text or None if recognition failed

        Note:
        - Automatically converts audio to WAV PCM 16kHz mono for Yandex STT
        - Max 1MB per request
        - Max 30 seconds audio duration
        """
        if not self.api_key or not self.folder_id:
            logger.error("Yandex API credentials not configured")
            return None

        try:
            # Convert audio to WAV format for Yandex
            wav_data = self._convert_to_wav(audio_data, source_format=format)

            headers = {
                "Authorization": f"Api-Key {self.api_key}",
            }

            params = {
                "lang": language,
                "format": "lpcm",  # We're sending PCM WAV
                "sampleRateHertz": "16000",
                "folderId": self.folder_id,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.stt_url,
                    headers=headers,
                    params=params,
                    content=wav_data
                )
                response.raise_for_status()
                result = response.json()

                # Extract recognized text
                text = result.get("result", "")
                logger.info(f"✅ STT recognized: '{text}'")
                return text

        except httpx.TimeoutException:
            logger.error("STT request timeout")
            return None
        except httpx.HTTPError as e:
            logger.error(f"Yandex STT API error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response body: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error in STT (audio conversion or API): {e}")
            return None


# Create singleton instance
yandex_stt_service = YandexSTTService()

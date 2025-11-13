"""
Yandex SpeechKit STT (Speech-to-Text) service
Converts audio to text using Yandex Cloud Speech Recognition API
"""

import httpx
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class YandexSTTService:
    """Service for converting speech to text using Yandex SpeechKit"""

    def __init__(self):
        self.api_key = settings.YANDEX_API_KEY
        self.folder_id = settings.YANDEX_FOLDER_ID
        self.stt_url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"

    async def recognize_audio(
        self,
        audio_data: bytes,
        language: str = "ru-RU",
        format: str = "oggopus"
    ) -> Optional[str]:
        """
        Recognize speech from audio data.

        Args:
            audio_data: Audio file bytes
            language: Recognition language (default: ru-RU)
            format: Audio format (oggopus, lpcm, mp3)

        Returns:
            Recognized text or None if recognition failed

        Supported formats:
        - oggopus: OGG with Opus codec (recommended for web)
        - lpcm: Linear PCM
        - mp3: MP3

        Rate limits:
        - Max 1MB per request
        - Max 30 seconds audio duration
        """
        if not self.api_key or not self.folder_id:
            logger.error("Yandex API credentials not configured")
            return None

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
        }

        params = {
            "lang": language,
            "format": format,
            "folderId": self.folder_id,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.stt_url,
                    headers=headers,
                    params=params,
                    content=audio_data
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
            logger.error(f"Unexpected error in STT: {e}")
            return None


# Create singleton instance
yandex_stt_service = YandexSTTService()

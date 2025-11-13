"""
Yandex SpeechKit TTS (Text-to-Speech) service
Converts text to speech audio using Yandex Cloud Speech Synthesis API
"""

import httpx
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class YandexTTSService:
    """Service for converting text to speech using Yandex SpeechKit"""

    def __init__(self):
        self.api_key = settings.YANDEX_API_KEY
        self.folder_id = settings.YANDEX_FOLDER_ID
        self.tts_url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"

    async def synthesize_speech(
        self,
        text: str,
        language: str = "ru-RU",
        voice: str = "alena",
        emotion: str = "neutral",
        speed: float = 1.0,
        format: str = "oggopus"
    ) -> Optional[bytes]:
        """
        Convert text to speech audio.

        Args:
            text: Text to synthesize
            language: Voice language (ru-RU, en-US, etc.)
            voice: Voice name (alena, filipp, ermil, jane, omazh, zahar)
            emotion: Voice emotion (neutral, good, evil)
            speed: Speech speed (0.1 to 3.0)
            format: Audio format (oggopus, lpcm, mp3)

        Returns:
            Audio bytes or None if synthesis failed

        Popular Russian voices:
        - alena: Female, pleasant
        - filipp: Male, energetic
        - ermil: Male, calm
        - jane: Female, neutral
        - omazh: Female, energetic
        - zahar: Male, friendly

        Audio formats:
        - oggopus: OGG with Opus codec (recommended for web)
        - lpcm: Linear PCM (48kHz, 16-bit)
        - mp3: MP3
        """
        if not self.api_key or not self.folder_id:
            logger.error("Yandex API credentials not configured")
            return None

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
        }

        data = {
            "text": text,
            "lang": language,
            "voice": voice,
            "emotion": emotion,
            "speed": speed,
            "format": format,
            "folderId": self.folder_id,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.tts_url,
                    headers=headers,
                    data=data
                )
                response.raise_for_status()

                # Response is audio bytes
                audio_data = response.content
                logger.info(f"✅ TTS synthesized {len(audio_data)} bytes for text: '{text[:50]}...'")
                return audio_data

        except httpx.TimeoutException:
            logger.error("TTS request timeout")
            return None
        except httpx.HTTPError as e:
            logger.error(f"Yandex TTS API error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response body: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in TTS: {e}")
            return None


# Create singleton instance
yandex_tts_service = YandexTTSService()

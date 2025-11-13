"""
Yandex SpeechKit v3 Synthesizer for Vocode
Implements real-time text-to-speech synthesis
"""

import asyncio
import logging
from typing import Optional, AsyncGenerator
import grpc
from vocode.streaming.synthesizer.base_synthesizer import (
    BaseSynthesizer,
    SynthesisResult,
)
from vocode.streaming.models.synthesizer import SynthesizerConfig
from vocode.streaming.models.audio_encoding import AudioEncoding

# Yandex SpeechKit v3 imports
try:
    from yandex.cloud.ai.tts.v3 import tts_pb2, tts_service_pb2_grpc
except ImportError:
    # Fallback if yandex-speechkit package structure is different
    import sys
    import os
    pass

from app.config import settings

logger = logging.getLogger(__name__)


class YandexSynthesizerConfig(SynthesizerConfig):
    """Configuration for Yandex Synthesizer"""

    synthesizer_type: str = "synthesizer_yandex"

    # Voice selection
    voice: str = "alena"  # Popular female voice
    # Other options: filipp, ermil, jane, madirus, omazh, zahar, dasha, julia, lera, marina
    language_code: str = "ru-RU"

    # Audio format
    audio_encoding: AudioEncoding = AudioEncoding.LINEAR16
    sample_rate: int = 16000  # Vocode expects 16kHz

    # Speech parameters
    speed: float = 1.0  # 0.1 - 3.0
    pitch: float = 0.0  # -10.0 to 10.0
    volume: float = 0.0  # -145.0 to 0.0 (dB)

    # Output format for Yandex (will convert to Vocode format)
    yandex_format: str = "LINEAR16_PCM"  # LINEAR16_PCM | OGG_OPUS


class YandexSynthesizer(BaseSynthesizer[YandexSynthesizerConfig]):
    """
    Yandex SpeechKit v3 Synthesizer for Vocode.

    Converts text to speech using Yandex Cloud TTS.
    Supports streaming synthesis for low latency.
    """

    def __init__(self, synthesizer_config: YandexSynthesizerConfig):
        super().__init__(synthesizer_config)

        self.api_key = settings.YANDEX_API_KEY
        if not self.api_key:
            raise ValueError("YANDEX_API_KEY is required for YandexSynthesizer")

        # gRPC endpoint
        self.endpoint = "tts.api.cloud.yandex.net:443"

        # Connection state
        self._channel: Optional[grpc.aio.Channel] = None
        self._stub: Optional[tts_service_pb2_grpc.SynthesizerStub] = None

        logger.info(
            f"YandexSynthesizer initialized: voice={synthesizer_config.voice}, "
            f"language={synthesizer_config.language_code}"
        )

    async def _connect(self) -> None:
        """Establish gRPC connection to Yandex SpeechKit"""
        try:
            # Create secure channel
            credentials = grpc.ssl_channel_credentials()
            self._channel = grpc.aio.secure_channel(
                self.endpoint,
                credentials
            )

            self._stub = tts_service_pb2_grpc.SynthesizerStub(self._channel)

            logger.info("✅ Connected to Yandex TTS v3")

        except Exception as e:
            logger.error(f"Failed to connect to Yandex TTS: {e}")
            raise

    async def _disconnect(self) -> None:
        """Close gRPC connection"""
        if self._channel:
            await self._channel.close()
            self._channel = None
            self._stub = None

        logger.info("Disconnected from Yandex TTS")

    def _create_synthesis_request(self, text: str) -> tts_pb2.UtteranceSynthesisRequest:
        """Create synthesis request for Yandex TTS"""

        # Text input
        utterance = tts_pb2.Utterance(
            text=text
        )

        # Output audio specification
        output_audio_spec = tts_pb2.AudioFormatOptions()

        if self.synthesizer_config.yandex_format == "LINEAR16_PCM":
            output_audio_spec.raw_audio.CopyFrom(
                tts_pb2.RawAudio(
                    audio_encoding=tts_pb2.RawAudio.AudioEncoding.LINEAR16_PCM,
                    sample_rate_hertz=self.synthesizer_config.sample_rate,
                    audio_channel_count=1
                )
            )
        elif self.synthesizer_config.yandex_format == "OGG_OPUS":
            output_audio_spec.container_audio.CopyFrom(
                tts_pb2.ContainerAudio(
                    container_audio_type=tts_pb2.ContainerAudio.ContainerAudioType.OGG_OPUS
                )
            )

        # Voice hints
        hints = []

        # Voice selection hint
        hints.append(
            tts_pb2.Hints(
                voice=self.synthesizer_config.voice
            )
        )

        # Speed hint
        if self.synthesizer_config.speed != 1.0:
            hints.append(
                tts_pb2.Hints(
                    speed=self.synthesizer_config.speed
                )
            )

        # Pitch hint
        if self.synthesizer_config.pitch != 0.0:
            hints.append(
                tts_pb2.Hints(
                    pitch_shift=self.synthesizer_config.pitch
                )
            )

        # Volume hint
        if self.synthesizer_config.volume != 0.0:
            hints.append(
                tts_pb2.Hints(
                    volume=self.synthesizer_config.volume
                )
            )

        # Construct request
        request = tts_pb2.UtteranceSynthesisRequest(
            text=utterance.text,
            output_audio_spec=output_audio_spec,
            hints=hints,
            loudness_normalization_type=tts_pb2.UtteranceSynthesisRequest.LUFS
        )

        return request

    async def create_speech(
        self,
        message: str,
        chunk_size: int = 1024,
        **kwargs
    ) -> SynthesisResult:
        """
        Synthesize speech from text.

        Args:
            message: Text to synthesize
            chunk_size: Size of audio chunks to yield
            **kwargs: Additional parameters

        Returns:
            SynthesisResult with audio chunks
        """

        async def chunk_generator() -> AsyncGenerator[bytes, None]:
            """Generator that yields audio chunks from Yandex TTS"""

            try:
                # Connect if needed
                if not self._channel:
                    await self._connect()

                # Create synthesis request
                request = self._create_synthesis_request(message)

                # Create metadata with API key authentication
                metadata = (
                    ('authorization', f'Api-Key {self.api_key}'),
                )

                # Call streaming synthesis
                logger.debug(f"Synthesizing: '{message[:50]}...'")

                response_stream = self._stub.UtteranceSynthesis(
                    request,
                    metadata=metadata
                )

                # Process audio chunks
                total_bytes = 0
                async for response in response_stream:
                    if response.audio_chunk.data:
                        audio_data = response.audio_chunk.data
                        total_bytes += len(audio_data)

                        # Yield in chunks of requested size
                        for i in range(0, len(audio_data), chunk_size):
                            chunk = audio_data[i:i + chunk_size]
                            yield chunk

                logger.info(f"✅ Synthesized {total_bytes} bytes for: '{message[:50]}...'")

            except grpc.aio.AioRpcError as e:
                logger.error(f"gRPC error in synthesis: {e.code()} - {e.details()}")
                raise
            except Exception as e:
                logger.error(f"Error in synthesis: {e}", exc_info=True)
                raise

        return SynthesisResult(
            chunk_generator=chunk_generator(),
            get_message_up_to=lambda seconds: message,  # Return full message
        )

    async def terminate(self) -> None:
        """Terminate the synthesizer"""
        await self._disconnect()


# ==========================================
# Voice Presets
# ==========================================

YANDEX_VOICES = {
    # Female voices
    "alena": "Alena - Friendly female voice",
    "jane": "Jane - Neutral female voice",
    "omazh": "Omazh - Animated female voice",
    "dasha": "Dasha - Calm female voice",
    "julia": "Julia - Expressive female voice",
    "lera": "Lera - Young female voice",
    "marina": "Marina - Professional female voice",

    # Male voices
    "filipp": "Filipp - Neutral male voice",
    "ermil": "Ermil - Friendly male voice",
    "madirus": "Madirus - Deep male voice",
    "zahar": "Zahar - Professional male voice",
}


def get_yandex_synthesizer_config(
    voice: str = "alena",
    speed: float = 1.0,
    pitch: float = 0.0
) -> YandexSynthesizerConfig:
    """
    Helper function to create YandexSynthesizerConfig with common settings.

    Args:
        voice: Voice name (see YANDEX_VOICES)
        speed: Speech speed (0.1 - 3.0)
        pitch: Pitch shift (-10.0 to 10.0)

    Returns:
        Configured YandexSynthesizerConfig
    """
    if voice not in YANDEX_VOICES:
        logger.warning(f"Unknown voice '{voice}', defaulting to 'alena'")
        voice = "alena"

    return YandexSynthesizerConfig(
        voice=voice,
        speed=speed,
        pitch=pitch,
        sample_rate=16000,
        audio_encoding=AudioEncoding.LINEAR16
    )

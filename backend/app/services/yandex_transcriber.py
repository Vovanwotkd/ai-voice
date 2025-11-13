"""
Yandex SpeechKit v3 Transcriber for Vocode
Implements real-time streaming speech recognition
"""

import asyncio
import logging
from typing import Optional, AsyncGenerator
import grpc
from vocode.streaming.transcriber.base_transcriber import (
    BaseAsyncTranscriber,
    Transcription,
)
from vocode.streaming.models.transcriber import TranscriberConfig

# Yandex SpeechKit v3 imports
try:
    from yandex.cloud.ai.stt.v3 import stt_pb2, stt_service_pb2_grpc
except ImportError:
    # Fallback if yandex-speechkit package structure is different
    import sys
    import os
    # We'll implement manual proto definitions if needed
    pass

from app.config import settings

logger = logging.getLogger(__name__)


class YandexTranscriberConfig(TranscriberConfig):
    """Configuration for Yandex Transcriber"""

    transcriber_type: str = "transcriber_yandex"

    # Yandex SpeechKit settings
    language_code: str = "ru-RU"
    model: str = "general"  # general | general:rc | general:deprecated

    # Audio format (Vocode sends PCM)
    audio_encoding: str = "LINEAR16_PCM"
    sample_rate_hertz: int = 16000
    audio_channel_count: int = 1

    # Recognition settings
    profanity_filter: bool = False
    literature_text: bool = False
    enable_partial_results: bool = True
    enable_speaker_labeling: bool = False


class YandexTranscriber(BaseAsyncTranscriber[YandexTranscriberConfig]):
    """
    Yandex SpeechKit v3 Streaming Transcriber for Vocode.

    Uses gRPC bidirectional streaming for real-time speech recognition.
    Authentication via API key (no IAM token needed).
    """

    def __init__(self, transcriber_config: YandexTranscriberConfig):
        super().__init__(transcriber_config)

        self.api_key = settings.YANDEX_API_KEY
        if not self.api_key:
            raise ValueError("YANDEX_API_KEY is required for YandexTranscriber")

        # gRPC endpoint
        self.endpoint = "stt.api.cloud.yandex.net:443"

        # Connection state
        self._channel: Optional[grpc.aio.Channel] = None
        self._stub: Optional[stt_service_pb2_grpc.RecognizerStub] = None
        self._stream_call = None

        logger.info(f"YandexTranscriber initialized: language={transcriber_config.language_code}, model={transcriber_config.model}")

    async def _connect(self) -> None:
        """Establish gRPC connection to Yandex SpeechKit"""
        try:
            # Create secure channel
            credentials = grpc.ssl_channel_credentials()
            self._channel = grpc.aio.secure_channel(
                self.endpoint,
                credentials
            )

            self._stub = stt_service_pb2_grpc.RecognizerStub(self._channel)

            logger.info("✅ Connected to Yandex SpeechKit v3")

        except Exception as e:
            logger.error(f"Failed to connect to Yandex SpeechKit: {e}")
            raise

    async def _disconnect(self) -> None:
        """Close gRPC connection"""
        if self._stream_call:
            await self._stream_call.cancel()
            self._stream_call = None

        if self._channel:
            await self._channel.close()
            self._channel = None
            self._stub = None

        logger.info("Disconnected from Yandex SpeechKit")

    def _create_recognition_config(self) -> stt_pb2.RecognitionConfig:
        """Create Yandex recognition configuration"""

        # Audio format specification
        audio_format_options = stt_pb2.RawAudio(
            audio_encoding=stt_pb2.RawAudio.AudioEncoding.LINEAR16_PCM,
            sample_rate_hertz=self.transcriber_config.sample_rate_hertz,
            audio_channel_count=self.transcriber_config.audio_channel_count
        )

        # Recognition specification
        recognition_model_options = stt_pb2.RecognitionModelOptions(
            model=self.transcriber_config.model,
            audio_format=audio_format_options,
            text_normalization=stt_pb2.TextNormalizationOptions(
                text_normalization=stt_pb2.TextNormalizationOptions.TextNormalization.TEXT_NORMALIZATION_ENABLED,
                profanity_filter=self.transcriber_config.profanity_filter,
                literature_text=self.transcriber_config.literature_text
            ),
            language_restriction=stt_pb2.LanguageRestrictionOptions(
                restriction_type=stt_pb2.LanguageRestrictionOptions.LanguageRestrictionType.WHITELIST,
                language_code=[self.transcriber_config.language_code]
            ),
            audio_processing_type=stt_pb2.RecognitionModelOptions.AudioProcessingType.REAL_TIME
        )

        # Streaming options
        streaming_options = stt_pb2.StreamingOptions(
            recognition_model=recognition_model_options
        )

        return stt_pb2.RecognitionConfig(
            specification=streaming_options
        )

    async def _send_audio_generator(
        self,
        audio_queue: asyncio.Queue
    ) -> AsyncGenerator[stt_pb2.StreamingRequest, None]:
        """
        Generator that yields audio chunks from queue as StreamingRequest messages.
        First message contains config, subsequent messages contain audio data.
        """

        # First message: configuration
        config = self._create_recognition_config()
        yield stt_pb2.StreamingRequest(
            session_options=stt_pb2.StreamingRequest.SessionOptions(
                recognition_model=config.specification.recognition_model
            )
        )

        logger.info("Sent recognition config to Yandex SpeechKit")

        # Subsequent messages: audio chunks
        while True:
            try:
                audio_chunk = await asyncio.wait_for(
                    audio_queue.get(),
                    timeout=5.0  # 5 second timeout
                )

                if audio_chunk is None:
                    # Sentinel value to end stream
                    logger.info("Audio stream ended")
                    break

                # Send audio chunk
                yield stt_pb2.StreamingRequest(
                    chunk=stt_pb2.AudioChunk(data=audio_chunk)
                )

            except asyncio.TimeoutError:
                # No audio for 5 seconds, continue waiting
                continue
            except Exception as e:
                logger.error(f"Error in audio generator: {e}")
                break

    async def _process_responses(
        self,
        response_stream,
        transcription_queue: asyncio.Queue
    ) -> None:
        """Process recognition responses from Yandex"""
        try:
            async for response in response_stream:
                # Handle different event types
                if response.HasField("partial"):
                    # Partial (interim) result
                    partial = response.partial
                    for alternative in partial.alternatives:
                        text = alternative.text.strip()
                        if text:
                            logger.debug(f"Partial: {text}")

                            if self.transcriber_config.enable_partial_results:
                                await transcription_queue.put(
                                    Transcription(
                                        message=text,
                                        confidence=alternative.confidence,
                                        is_final=False
                                    )
                                )

                elif response.HasField("final"):
                    # Final result
                    final = response.final
                    for alternative in final.alternatives:
                        text = alternative.text.strip()
                        if text:
                            logger.info(f"Final: {text}")

                            await transcription_queue.put(
                                Transcription(
                                    message=text,
                                    confidence=alternative.confidence,
                                    is_final=True
                                )
                            )

                elif response.HasField("eou_update"):
                    # End of utterance
                    logger.debug("End of utterance detected")

                elif response.HasField("final_refinement"):
                    # Final refinement (optional improved transcription)
                    final_refinement = response.final_refinement
                    for alternative in final_refinement.normalized_text.alternatives:
                        text = alternative.text.strip()
                        if text:
                            logger.info(f"Refined: {text}")

                            await transcription_queue.put(
                                Transcription(
                                    message=text,
                                    confidence=alternative.confidence,
                                    is_final=True
                                )
                            )

                elif response.HasField("status_code"):
                    # Status code
                    status = response.status_code
                    logger.info(f"Status: {status.code_type} - {status.message}")

        except grpc.aio.AioRpcError as e:
            logger.error(f"gRPC error in response processing: {e.code()} - {e.details()}")
        except Exception as e:
            logger.error(f"Error processing responses: {e}")

    async def _run_loop(self) -> None:
        """Main transcription loop"""
        try:
            # Connect to Yandex SpeechKit
            await self._connect()

            # Queues for communication
            audio_queue = asyncio.Queue()
            transcription_queue = asyncio.Queue()

            # Create metadata with API key authentication
            metadata = (
                ('authorization', f'Api-Key {self.api_key}'),
                ('x-folder-id', settings.YANDEX_FOLDER_ID or ''),
            )

            # Start bidirectional streaming
            self._stream_call = self._stub.RecognizeStreaming(
                self._send_audio_generator(audio_queue),
                metadata=metadata
            )

            # Start response processor
            response_task = asyncio.create_task(
                self._process_responses(self._stream_call, transcription_queue)
            )

            # Main loop: read audio from input queue, send to Yandex, get transcriptions
            while not self._closed:
                try:
                    # Get audio from Vocode's input queue
                    audio_chunk = await asyncio.wait_for(
                        self.input_queue.get(),
                        timeout=1.0
                    )

                    # Forward to audio queue for gRPC stream
                    await audio_queue.put(audio_chunk)

                except asyncio.TimeoutError:
                    # No audio, check for transcriptions
                    pass

                # Check for transcriptions and send to output
                while not transcription_queue.empty():
                    transcription = await transcription_queue.get()
                    self.output_queue.put_nowait(transcription)

            # Cleanup
            await audio_queue.put(None)  # Signal end of audio
            await response_task

        except Exception as e:
            logger.error(f"Error in transcription loop: {e}", exc_info=True)

        finally:
            await self._disconnect()

    async def terminate(self) -> None:
        """Terminate the transcriber"""
        self._closed = True
        await self._disconnect()
        await super().terminate()

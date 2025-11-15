"""
Vocode WebRTC Voice Call API
Uses Vocode components: YandexTranscriber + HostessAgent + YandexSynthesizer
With rate limiting protection
"""

import asyncio
import logging
import uuid
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from app.vocode_providers.yandex_transcriber import YandexTranscriber, YandexTranscriberConfig
from app.vocode_providers.yandex_synthesizer import YandexSynthesizer, YandexSynthesizerConfig
from app.vocode_providers.hostess_agent import HostessAgent, HostessAgentConfig
from app.middleware.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

router = APIRouter()

# Active calls
active_calls: Dict[str, dict] = {}


@router.post("/start")
async def start_call() -> JSONResponse:
    """Initialize voice call"""
    call_id = str(uuid.uuid4())

    logger.info(f"Starting call: {call_id}")

    return JSONResponse({
        "call_id": call_id,
        "websocket_url": f"/api/vocode/ws/{call_id}",
        "status": "initialized"
    })


@router.websocket("/ws/{call_id}")
async def websocket_call(websocket: WebSocket, call_id: str):
    """
    WebSocket endpoint for voice call with rate limiting

    Protocol:
    - Client sends: PCM audio (16kHz, mono, int16)
    - Server sends:
      - JSON: {"type": "transcription", "text": "..."}
      - JSON: {"type": "response", "text": "..."}
      - Binary: PCM audio (TTS)
    """
    # Get client IP for rate limiting
    client_host = websocket.client.host if websocket.client else "unknown"
    client_id = f"{client_host}:{call_id}"

    # Check connection limit
    allowed, error_msg = rate_limiter.check_connection_limit(client_id)
    if not allowed:
        await websocket.close(code=1008, reason=error_msg)
        logger.warning(f"Connection rejected for {client_id}: {error_msg}")
        return

    await websocket.accept()
    logger.info(f"WebSocket connected: {call_id} from {client_host}")

    # Create Vocode components
    transcriber_config = YandexTranscriberConfig(language_code="ru-RU")
    transcriber = YandexTranscriber(transcriber_config)

    synthesizer_config = YandexSynthesizerConfig(voice="alena")
    synthesizer = YandexSynthesizer(synthesizer_config)

    agent_config = HostessAgentConfig(use_rag=True)
    agent = HostessAgent(agent_config)

    # Start transcriber
    transcriber_task = asyncio.create_task(transcriber._run_loop())

    try:
        # Send initial greeting
        initial_message = agent_config.initial_message
        if initial_message:
            await websocket.send_json({
                "type": "greeting",
                "text": initial_message
            })

            # Synthesize greeting
            synthesis_result = await synthesizer.create_speech_uncached(
                message=initial_message,
                chunk_size=2048
            )

            # Send audio chunks
            async for audio_chunk in synthesis_result.chunk_generator:
                await websocket.send_bytes(audio_chunk)

        # Main loop
        while True:
            try:
                # Check message rate limit
                allowed, error_msg = rate_limiter.check_message_rate(client_id)
                if not allowed:
                    await websocket.send_json({
                        "type": "error",
                        "message": error_msg
                    })
                    await asyncio.sleep(0.1)  # Brief pause
                    continue

                # Receive audio with timeout
                audio_data = await asyncio.wait_for(
                    websocket.receive_bytes(),
                    timeout=10.0
                )

                # Check bandwidth limit
                allowed, error_msg = rate_limiter.check_bandwidth(client_id, len(audio_data))
                if not allowed:
                    await websocket.send_json({
                        "type": "error",
                        "message": error_msg
                    })
                    continue

                # Validate audio data size (max 1MB per chunk)
                if len(audio_data) > 1_000_000:
                    logger.warning(f"Received oversized audio chunk: {len(audio_data)} bytes")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Audio chunk too large"
                    })
                    continue

                # Check queue size to prevent memory overflow
                if transcriber.input_queue.qsize() > 10:
                    logger.warning("Transcriber queue overflow, dropping chunk")
                    continue

                # Send to transcriber
                await transcriber.input_queue.put(audio_data)

                # Periodic cleanup
                rate_limiter.cleanup_old_buckets()

                # Check for transcription results
                while not transcriber.output_queue.empty():
                    transcription = await transcriber.output_queue.get()

                    if transcription.is_final:
                        user_text = transcription.message
                        logger.info(f"Transcribed: {user_text}")

                        # Send transcription to client
                        await websocket.send_json({
                            "type": "transcription",
                            "text": user_text
                        })

                        # Get agent response with timeout
                        response_text, end_conversation = await asyncio.wait_for(
                            agent.respond(
                                human_input=user_text,
                                conversation_id=call_id
                            ),
                            timeout=30.0  # 30 second timeout for LLM response
                        )

                        logger.info(f"Agent: {response_text}")

                        # Send response text
                        await websocket.send_json({
                            "type": "response",
                            "text": response_text
                        })

                        # Synthesize response
                        synthesis_result = await synthesizer.create_speech_uncached(
                            message=response_text,
                            chunk_size=2048
                        )

                        # Send audio chunks
                        async for audio_chunk in synthesis_result.chunk_generator:
                            await websocket.send_bytes(audio_chunk)

                        if end_conversation:
                            logger.info("Ending conversation")
                            break

            except asyncio.TimeoutError:
                continue

            except WebSocketDisconnect:
                logger.info(f"Client disconnected: {call_id}")
                break

    except Exception as e:
        logger.error(f"Error in WebSocket: {e}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass

    finally:
        # Cleanup
        logger.info(f"Cleaning up call: {call_id}")

        # Release rate limit connection
        rate_limiter.release_connection(client_id)

        # Stop transcriber
        transcriber._ended = True
        transcriber_task.cancel()

        try:
            await websocket.close()
        except:
            pass


@router.get("/status/{call_id}")
async def get_call_status(call_id: str):
    """Get call status"""
    return JSONResponse({"call_id": call_id, "status": "active" if call_id in active_calls else "ended"})


@router.post("/end/{call_id}")
async def end_call(call_id: str):
    """End call"""
    if call_id in active_calls:
        del active_calls[call_id]

    return JSONResponse({"call_id": call_id, "status": "ended"})


@router.get("/config")
async def get_config():
    """Get Vocode configuration"""
    return JSONResponse({
        "voices": {
            "alena": "Алена (женский, дружелюбный)",
            "filipp": "Филипп (мужской, нейтральный)",
            "ermil": "Ермил (мужской, дружелюбный)",
            "jane": "Джейн (женский, нейтральный)",
            "omazh": "Омаж (женский, анимированный)"
        },
        "system_prompts": {
            "default": "Вы - AI-ассистент ресторана. Помогайте гостям с бронированием и вопросами."
        },
        "audio_config": {
            "sample_rate": 16000,
            "encoding": "LINEAR16",
            "channels": 1
        }
    })


@router.get("/active")
async def get_active_calls():
    """Get active calls"""
    return JSONResponse({
        "active_calls": [
            {"call_id": call_id, "status": "active"}
            for call_id in active_calls.keys()
        ],
        "count": len(active_calls)
    })


@router.get("/rate-limit/stats")
async def get_rate_limit_stats():
    """Get rate limiter statistics (admin endpoint)"""
    return JSONResponse(rate_limiter.get_stats())

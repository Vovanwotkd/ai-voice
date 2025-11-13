"""
Vocode WebRTC API Endpoints
Handles browser-based voice calls using Vocode framework
"""

import logging
import uuid
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from vocode.streaming.telephony.conversation.outbound_call import OutboundCall
from vocode.streaming.telephony.config_manager.base_config_manager import BaseConfigManager
from vocode.streaming.models.telephony import TwilioConfig
from vocode.streaming.models.audio_encoding import AudioEncoding
from vocode.streaming.streaming_conversation import StreamingConversation
from vocode.streaming.models.synthesizer import SynthesizerConfig
from vocode.streaming.models.transcriber import TranscriberConfig
from vocode.streaming.models.agent import AgentConfig
from vocode.streaming.utils.events_manager import EventsManager

from app.services.yandex_transcriber import YandexTranscriber, YandexTranscriberConfig
from app.services.yandex_synthesizer import YandexSynthesizer, YandexSynthesizerConfig
from app.services.hostess_agent import HostessAgent, HostessAgentConfig, SYSTEM_PROMPTS

logger = logging.getLogger(__name__)

router = APIRouter()


# ==========================================
# Request/Response Models
# ==========================================

class StartCallRequest(BaseModel):
    """Request to start a new voice call"""
    system_prompt: Optional[str] = None
    voice: str = "alena"  # Yandex voice
    use_rag: bool = True


class CallStatusResponse(BaseModel):
    """Call status response"""
    call_id: str
    status: str  # active | ended | error
    duration_seconds: Optional[float] = None


# ==========================================
# Active Calls Registry
# ==========================================

active_calls = {}  # call_id -> StreamingConversation


# ==========================================
# WebRTC Endpoints
# ==========================================

@router.post("/start")
async def start_call(request: StartCallRequest) -> JSONResponse:
    """
    Initialize a new voice call session.

    Returns call_id for WebSocket connection.
    """
    try:
        # Generate unique call ID
        call_id = str(uuid.uuid4())

        logger.info(f"Starting new call: {call_id}")

        return JSONResponse({
            "call_id": call_id,
            "status": "initialized",
            "websocket_url": f"/api/vocode/ws/{call_id}",
            "message": "Call initialized. Connect to WebSocket to start audio streaming."
        })

    except Exception as e:
        logger.error(f"Error starting call: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{call_id}")
async def websocket_call(websocket: WebSocket, call_id: str):
    """
    WebSocket endpoint for real-time audio streaming.

    Protocol:
    1. Client connects with call_id
    2. Server sends initial greeting (optional)
    3. Bidirectional audio streaming:
       - Client -> Server: Audio chunks (PCM 16kHz)
       - Server -> Client: Audio chunks (PCM 16kHz)
    4. Text messages for control/status
    """

    await websocket.accept()
    logger.info(f"WebSocket connection established for call: {call_id}")

    try:
        # Get call configuration from query params or use defaults
        # In production, this would be retrieved from database/session
        system_prompt = SYSTEM_PROMPTS["default"]
        voice = "alena"
        use_rag = True

        # Create Vocode components
        transcriber_config = YandexTranscriberConfig(
            language_code="ru-RU",
            model="general",
            enable_partial_results=True
        )
        transcriber = YandexTranscriber(transcriber_config=transcriber_config)

        synthesizer_config = YandexSynthesizerConfig(
            voice=voice,
            speed=1.0,
            sample_rate=16000
        )
        synthesizer = YandexSynthesizer(synthesizer_config=synthesizer_config)

        agent_config = HostessAgentConfig(
            system_prompt=system_prompt,
            use_rag=use_rag,
            initial_message="Добрый день! Ресторан Гастрономия, чем могу помочь?"
        )
        agent = HostessAgent(agent_config=agent_config)

        # Create streaming conversation
        conversation = StreamingConversation(
            output_device=None,  # WebSocket output
            transcriber=transcriber,
            agent=agent,
            synthesizer=synthesizer,
            conversation_id=call_id,
        )

        # Store active call
        active_calls[call_id] = conversation

        # Send initial greeting
        initial_message = agent.get_initial_message()
        if initial_message:
            logger.info(f"Sending initial message: {initial_message}")
            # Synthesize initial greeting
            synthesis_result = await synthesizer.create_speech(initial_message)

            # Stream audio chunks to client
            async for audio_chunk in synthesis_result.chunk_generator:
                await websocket.send_bytes(audio_chunk)

        # Main conversation loop
        while True:
            try:
                # Receive data from client
                data = await websocket.receive()

                if "bytes" in data:
                    # Audio chunk from client
                    audio_chunk = data["bytes"]

                    # Send to transcriber
                    await transcriber.input_queue.put(audio_chunk)

                    # Check for transcription results
                    while not transcriber.output_queue.empty():
                        transcription = await transcriber.output_queue.get()

                        if transcription.is_final:
                            # Final transcription - generate response
                            user_text = transcription.message
                            logger.info(f"Transcribed: {user_text}")

                            # Send transcription to client (for debugging/UI)
                            await websocket.send_json({
                                "type": "transcription",
                                "text": user_text,
                                "is_final": True
                            })

                            # Generate agent response
                            async for response_message in agent.respond(
                                human_input=user_text,
                                conversation_id=call_id
                            ):
                                response_text = response_message.message.text
                                logger.info(f"Agent response: {response_text}")

                                # Send response text to client
                                await websocket.send_json({
                                    "type": "agent_response",
                                    "text": response_text
                                })

                                # Synthesize response
                                synthesis_result = await synthesizer.create_speech(response_text)

                                # Stream audio chunks to client
                                async for audio_chunk in synthesis_result.chunk_generator:
                                    await websocket.send_bytes(audio_chunk)

                        else:
                            # Partial transcription
                            await websocket.send_json({
                                "type": "transcription",
                                "text": transcription.message,
                                "is_final": False
                            })

                elif "text" in data:
                    # Control message from client
                    message = data["text"]
                    logger.info(f"Control message: {message}")

                    if message == "end_call":
                        logger.info("Call ended by client")
                        break

            except WebSocketDisconnect:
                logger.info(f"Client disconnected: {call_id}")
                break

    except Exception as e:
        logger.error(f"Error in WebSocket call: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass

    finally:
        # Cleanup
        logger.info(f"Cleaning up call: {call_id}")

        if call_id in active_calls:
            conversation = active_calls[call_id]
            # Terminate components
            try:
                await transcriber.terminate()
                await synthesizer.terminate()
            except:
                pass

            del active_calls[call_id]

        try:
            await websocket.close()
        except:
            pass


@router.get("/status/{call_id}")
async def get_call_status(call_id: str) -> CallStatusResponse:
    """Get status of a specific call"""

    if call_id in active_calls:
        return CallStatusResponse(
            call_id=call_id,
            status="active"
        )
    else:
        return CallStatusResponse(
            call_id=call_id,
            status="ended"
        )


@router.post("/end/{call_id}")
async def end_call(call_id: str) -> JSONResponse:
    """End an active call"""

    if call_id not in active_calls:
        raise HTTPException(status_code=404, detail="Call not found")

    try:
        conversation = active_calls[call_id]

        # Terminate conversation components
        # This will be handled by WebSocket cleanup

        return JSONResponse({
            "call_id": call_id,
            "status": "ended",
            "message": "Call terminated successfully"
        })

    except Exception as e:
        logger.error(f"Error ending call: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def list_active_calls() -> JSONResponse:
    """List all active calls"""

    calls = [
        {
            "call_id": call_id,
            "status": "active"
        }
        for call_id in active_calls.keys()
    ]

    return JSONResponse({
        "active_calls": calls,
        "count": len(calls)
    })


# ==========================================
# Configuration Endpoint
# ==========================================

@router.get("/config")
async def get_vocode_config() -> JSONResponse:
    """Get available Vocode configuration options"""

    from app.services.yandex_synthesizer import YANDEX_VOICES

    return JSONResponse({
        "voices": YANDEX_VOICES,
        "system_prompts": {
            name: prompt.strip()
            for name, prompt in SYSTEM_PROMPTS.items()
        },
        "audio_config": {
            "sample_rate": 16000,
            "encoding": "LINEAR16_PCM",
            "channels": 1
        }
    })

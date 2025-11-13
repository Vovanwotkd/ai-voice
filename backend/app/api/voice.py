"""
Voice Chat API with WebSocket support
Real-time voice communication with the hostess bot
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import logging
import json
import base64
from typing import Optional

from app.api.deps import get_db
from app.services.yandex_stt import yandex_stt_service
from app.services.yandex_tts import yandex_tts_service
from app.services.llm_service import llm_service
from app.services.prompt_service import prompt_service
from app.services.conversation_manager import conversation_manager
from app.core.constants import MESSAGE_ROLE_USER, MESSAGE_ROLE_ASSISTANT

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/voice")
async def voice_chat_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice chat.

    Protocol:
    Client -> Server:
    {
        "type": "audio",
        "data": "<base64_encoded_audio>",
        "format": "oggopus",
        "conversation_id": "optional-uuid"
    }

    Server -> Client:
    {
        "type": "status",
        "status": "listening|processing|speaking"
    }
    {
        "type": "transcription",
        "text": "recognized text"
    }
    {
        "type": "response",
        "text": "bot response text",
        "audio": "<base64_encoded_audio>",
        "conversation_id": "uuid",
        "latency_ms": 1234
    }
    {
        "type": "error",
        "message": "error description"
    }
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    conversation_id: Optional[str] = None

    try:
        # Get database session - NOTE: WebSocket doesn't support Depends directly
        # We'll create a session manually for now
        from app.database import SessionLocal
        db = SessionLocal()

        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")

            if message_type == "audio":
                await handle_audio_message(websocket, message, db, conversation_id)
                # Update conversation_id if returned
                conv_id = message.get("conversation_id")
                if conv_id:
                    conversation_id = conv_id

            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed by client")
    except Exception as e:
        logger.error(f"Error in WebSocket: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    finally:
        try:
            db.close()
        except:
            pass


async def handle_audio_message(
    websocket: WebSocket,
    message: dict,
    db: Session,
    conversation_id: Optional[str]
):
    """Handle incoming audio message and generate voice response"""
    import time
    start_time = time.time()

    try:
        # Extract audio data
        audio_base64 = message.get("data")
        audio_format = message.get("format", "oggopus")

        if not audio_base64:
            await websocket.send_json({
                "type": "error",
                "message": "No audio data provided"
            })
            return

        # Decode audio
        audio_data = base64.b64decode(audio_base64)
        logger.info(f"Received audio: {len(audio_data)} bytes, format: {audio_format}")

        # Step 1: Transcribe audio (STT)
        await websocket.send_json({"type": "status", "status": "listening"})

        transcribed_text = await yandex_stt_service.recognize_audio(
            audio_data=audio_data,
            format=audio_format
        )

        if not transcribed_text:
            await websocket.send_json({
                "type": "error",
                "message": "Could not recognize speech"
            })
            return

        logger.info(f"Transcribed: '{transcribed_text}'")
        await websocket.send_json({
            "type": "transcription",
            "text": transcribed_text
        })

        # Step 2: Get or create conversation
        conversation = await conversation_manager.get_or_create_conversation(
            db=db,
            conversation_id=conversation_id
        )
        conversation_id = str(conversation.id)

        # Get conversation history
        history = await conversation_manager.get_conversation_history(
            db=db,
            conversation_id=conversation_id,
            limit=10
        )

        # Step 3: Generate LLM response
        await websocket.send_json({"type": "status", "status": "processing"})

        # Get active prompt
        prompt_content = await prompt_service.load_active_prompt(db)
        system_prompt = prompt_service.render_prompt(prompt_content)

        # Generate response
        llm_response = await llm_service.generate_response(
            message=transcribed_text,
            conversation_history=history,
            system_prompt=system_prompt
        )

        response_text = llm_response["content"]
        logger.info(f"Generated response: '{response_text}'")

        # Step 4: Synthesize speech (TTS)
        await websocket.send_json({"type": "status", "status": "speaking"})

        audio_response = await yandex_tts_service.synthesize_speech(
            text=response_text,
            voice="alena",  # Female voice
            emotion="neutral",
            format="oggopus"  # Use oggopus for browser playback
        )

        if not audio_response:
            await websocket.send_json({
                "type": "error",
                "message": "Could not synthesize speech"
            })
            return

        # Encode audio to base64
        audio_response_base64 = base64.b64encode(audio_response).decode('utf-8')

        # Step 5: Save messages to database
        await conversation_manager.add_message(
            db=db,
            conversation_id=conversation_id,
            role=MESSAGE_ROLE_USER,
            content=transcribed_text
        )

        latency_ms = int((time.time() - start_time) * 1000)

        await conversation_manager.add_message(
            db=db,
            conversation_id=conversation_id,
            role=MESSAGE_ROLE_ASSISTANT,
            content=response_text,
            latency_ms=latency_ms
        )

        # Step 6: Send response to client
        await websocket.send_json({
            "type": "response",
            "text": response_text,
            "audio": audio_response_base64,
            "conversation_id": conversation_id,
            "latency_ms": latency_ms
        })

        logger.info(f"✅ Voice conversation completed in {latency_ms}ms")

    except Exception as e:
        logger.error(f"Error handling audio message: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Error processing audio: {str(e)}"
        })

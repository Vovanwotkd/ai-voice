"""
WebRTC SIP API endpoints
Handles telephone calls via SIP protocol
"""

import logging
from typing import Optional
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel

from app.services.webrtc_sip_service import webrtc_sip_service

logger = logging.getLogger(__name__)

router = APIRouter()


class MakeCallRequest(BaseModel):
    """Request to make outbound call"""
    to_number: str
    from_number: Optional[str] = None
    provider: str = "twilio"


class CallStatusRequest(BaseModel):
    """Request for call status"""
    call_sid: str
    provider: str = "twilio"


@router.post("/call/outbound")
async def make_outbound_call(request: MakeCallRequest):
    """
    Initiate outbound call to phone number

    Requires provider credentials configured in .env:
    - Twilio: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
    - Vonage: VONAGE_API_KEY, VONAGE_API_SECRET
    """
    try:
        call_data = await webrtc_sip_service.initiate_outbound_call(
            to_number=request.to_number,
            from_number=request.from_number,
            provider=request.provider,
        )

        return JSONResponse({
            "status": "success",
            "call": call_data,
        })

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=400,
        )
    except Exception as e:
        logger.error(f"Error making call: {e}", exc_info=True)
        return JSONResponse(
            {"status": "error", "message": "Failed to initiate call"},
            status_code=500,
        )


@router.post("/webhooks/twilio/voice")
async def twilio_voice_webhook(request: Request):
    """
    Webhook for incoming Twilio calls

    Twilio will POST to this endpoint when a call comes in.
    We return TwiML instructions for handling the call.

    Configure this URL in Twilio Console:
    https://console.twilio.com/phone-numbers
    """
    try:
        # Parse Twilio request parameters
        form_data = await request.form()
        call_data = dict(form_data)

        logger.info(f"📞 Incoming Twilio call: {call_data.get('CallSid')}")
        logger.debug(f"Call details: {call_data}")

        # Generate TwiML response
        twiml = await webrtc_sip_service.handle_inbound_call(
            call_data=call_data,
            provider="twilio",
        )

        return Response(
            content=twiml,
            media_type="application/xml",
        )

    except Exception as e:
        logger.error(f"Error handling Twilio webhook: {e}", exc_info=True)

        # Return error TwiML
        error_twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="ru-RU">
        Извините, произошла ошибка. Пожалуйста, попробуйте позже.
    </Say>
    <Hangup/>
</Response>"""

        return Response(
            content=error_twiml,
            media_type="application/xml",
        )


@router.post("/webhooks/twilio/status")
async def twilio_status_webhook(request: Request):
    """
    Webhook for Twilio call status updates

    Receives status updates: queued, ringing, in-progress, completed, etc.
    """
    try:
        form_data = await request.form()
        status_data = dict(form_data)

        call_sid = status_data.get("CallSid")
        call_status = status_data.get("CallStatus")

        logger.info(f"📊 Twilio call status: {call_sid} -> {call_status}")

        return JSONResponse({"status": "received"})

    except Exception as e:
        logger.error(f"Error handling status webhook: {e}")
        return JSONResponse({"status": "error"}, status_code=500)


@router.post("/webhooks/vonage/answer")
async def vonage_answer_webhook(request: Request):
    """
    Webhook for incoming Vonage calls

    Vonage will POST to this endpoint when a call comes in.
    We return NCCO (JSON) instructions for handling the call.
    """
    try:
        call_data = await request.json()

        logger.info(f"📞 Incoming Vonage call: {call_data.get('uuid')}")

        # Generate NCCO response
        ncco = await webrtc_sip_service.handle_inbound_call(
            call_data=call_data,
            provider="vonage",
        )

        return JSONResponse(ncco)

    except Exception as e:
        logger.error(f"Error handling Vonage webhook: {e}", exc_info=True)

        # Return error NCCO
        error_ncco = [
            {
                "action": "talk",
                "text": "Извините, произошла ошибка. Пожалуйста, попробуйте позже.",
                "language": "ru-RU",
            },
            {"action": "hangup"},
        ]

        return JSONResponse(error_ncco)


@router.post("/webhooks/vonage/events")
async def vonage_events_webhook(request: Request):
    """
    Webhook for Vonage call events

    Receives event updates during the call
    """
    try:
        event_data = await request.json()

        event_type = event_data.get("status")
        conversation_uuid = event_data.get("conversation_uuid")

        logger.info(f"📊 Vonage event: {conversation_uuid} -> {event_type}")

        return JSONResponse({"status": "received"})

    except Exception as e:
        logger.error(f"Error handling Vonage event: {e}")
        return JSONResponse({"status": "error"}, status_code=500)


@router.get("/call/status/{call_sid}")
async def get_call_status(call_sid: str, provider: str = "twilio"):
    """Get current status of a call"""
    try:
        status = await webrtc_sip_service.get_call_status(call_sid, provider)
        return JSONResponse(status)

    except Exception as e:
        logger.error(f"Error getting call status: {e}")
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500,
        )


@router.post("/call/end/{call_sid}")
async def end_call(call_sid: str, provider: str = "twilio"):
    """End an active call"""
    try:
        success = await webrtc_sip_service.end_call(call_sid, provider)

        return JSONResponse({
            "status": "success" if success else "error",
            "call_sid": call_sid,
        })

    except Exception as e:
        logger.error(f"Error ending call: {e}")
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500,
        )


@router.get("/providers")
async def get_available_providers():
    """
    Get list of configured SIP providers

    Returns which providers are configured and ready to use
    """
    providers = {
        "twilio": {
            "configured": bool(
                webrtc_sip_service.twilio_account_sid
                and webrtc_sip_service.twilio_auth_token
            ),
            "phone_number": webrtc_sip_service.twilio_phone_number,
        },
        "vonage": {
            "configured": bool(
                webrtc_sip_service.vonage_api_key
                and webrtc_sip_service.vonage_api_secret
            ),
        },
        "custom_sip": {
            "configured": bool(webrtc_sip_service.sip_server_url),
            "server": webrtc_sip_service.sip_server_url,
        },
    }

    return JSONResponse(providers)

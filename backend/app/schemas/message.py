"""
Pydantic schemas for Message model and Chat API
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.core.constants import MESSAGE_ROLE_USER, MESSAGE_ROLE_ASSISTANT


class MessageBase(BaseModel):
    """Base schema for Message"""
    role: str = Field(..., description=f"Message role: '{MESSAGE_ROLE_USER}' or '{MESSAGE_ROLE_ASSISTANT}'")
    content: str = Field(..., min_length=1, max_length=4000, description="Message content")


class MessageCreate(MessageBase):
    """Schema for creating a new Message"""
    conversation_id: UUID
    audio_url: Optional[str] = Field(None, description="TTS audio URL")
    latency_ms: Optional[int] = Field(None, description="Response generation time (ms)")


class MessageResponse(MessageBase):
    """Schema for Message responses"""
    id: UUID
    conversation_id: UUID
    audio_url: Optional[str]
    latency_ms: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


# Chat API specific schemas

class ChatRequest(BaseModel):
    """Schema for chat message request"""
    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID (optional)")
    generate_audio: bool = Field(default=False, description="Whether to generate TTS audio")


class ChatResponse(BaseModel):
    """Schema for chat message response"""
    conversation_id: str = Field(..., description="Conversation ID")
    message: str = Field(..., description="Assistant response")
    audio_url: Optional[str] = Field(None, description="TTS audio URL (if requested)")
    latency_ms: int = Field(..., description="Response generation time (ms)")


class VoiceMessageRequest(BaseModel):
    """Schema for voice message request (Yandex STT)"""
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    # audio file will be in request.file


class VoiceMessageResponse(BaseModel):
    """Schema for voice message response"""
    conversation_id: str = Field(..., description="Conversation ID")
    transcription: str = Field(..., description="Speech-to-text result")
    message: str = Field(..., description="Assistant response")
    audio_url: Optional[str] = Field(None, description="TTS audio URL")
    latency_ms: int = Field(..., description="Total processing time (ms)")

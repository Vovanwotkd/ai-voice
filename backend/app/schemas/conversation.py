"""
Pydantic schemas for Conversation model
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, TYPE_CHECKING
from datetime import datetime
from uuid import UUID

if TYPE_CHECKING:
    from app.schemas.message import MessageResponse


class ConversationBase(BaseModel):
    """Base schema for Conversation"""
    session_id: Optional[str] = Field(None, max_length=100, description="Client session ID")
    metadata: Optional[Dict] = Field(default_factory=dict, description="Additional metadata")


class ConversationCreate(ConversationBase):
    """Schema for creating a new Conversation"""
    pass


class ConversationUpdate(BaseModel):
    """Schema for updating an existing Conversation"""
    ended_at: Optional[datetime] = Field(None, description="Conversation end time")
    metadata: Optional[Dict] = Field(None, description="Updated metadata")


class ConversationResponse(ConversationBase):
    """Schema for Conversation responses"""
    id: UUID
    started_at: datetime
    ended_at: Optional[datetime]
    message_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationWithMessages(ConversationResponse):
    """Schema for Conversation with messages"""
    messages: List["MessageResponse"] = Field(default_factory=list, description="Conversation messages")


class ConversationListResponse(BaseModel):
    """Schema for paginated conversation list"""
    conversations: List[ConversationResponse]
    total: int
    limit: int
    offset: int


# Import for forward reference resolution
from app.schemas.message import MessageResponse  # noqa: E402
ConversationWithMessages.model_rebuild()

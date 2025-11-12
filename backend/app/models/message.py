"""
Message model for storing individual messages in conversations
"""

from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.core.constants import MESSAGE_ROLE_USER, MESSAGE_ROLE_ASSISTANT


class Message(BaseModel):
    """
    Model for storing individual messages in a conversation.
    Each message has a role (user/assistant) and content.
    """

    __tablename__ = "messages"

    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to conversation"
    )

    role = Column(
        String(20),
        nullable=False,
        index=True,
        comment=f"Message role: '{MESSAGE_ROLE_USER}' or '{MESSAGE_ROLE_ASSISTANT}'"
    )

    content = Column(
        Text,
        nullable=False,
        comment="Message text content"
    )

    audio_url = Column(
        Text,
        nullable=True,
        comment="URL to TTS-generated audio file (if applicable)"
    )

    latency_ms = Column(
        Integer,
        nullable=True,
        comment="Time taken to generate response (in milliseconds)"
    )

    # Relationship to conversation
    conversation = relationship(
        "Conversation",
        back_populates="messages"
    )

    def __repr__(self) -> str:
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(role='{self.role}', content='{content_preview}')>"

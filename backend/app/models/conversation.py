"""
Conversation model for tracking chat sessions
"""

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Conversation(BaseModel):
    """
    Model for storing conversation sessions.
    A conversation represents a single chat session with the bot.
    """

    __tablename__ = "conversations"

    session_id = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Client-side session identifier (from browser/phone)"
    )

    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
        index=True,
        comment="When the conversation started"
    )

    ended_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the conversation ended (null if still active)"
    )

    message_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total number of messages in this conversation"
    )

    metadata = Column(
        JSONB,
        nullable=True,
        default=dict,
        comment="Additional metadata (browser info, user agent, etc.)"
    )

    # Relationship to messages
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<Conversation(id='{self.id}', messages={self.message_count})>"

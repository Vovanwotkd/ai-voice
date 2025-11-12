"""
Conversation Manager for handling chat sessions and messages
"""

from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, update
from uuid import UUID
import logging

from app.models.conversation import Conversation
from app.models.message import Message
from app.core.constants import (
    MESSAGE_ROLE_USER,
    MESSAGE_ROLE_ASSISTANT,
    MAX_CONVERSATION_HISTORY
)

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Service for managing conversations and messages.
    Handles creation, retrieval, and history management.
    """

    async def get_or_create_conversation(
        self,
        db: Session,
        conversation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Conversation:
        """
        Get existing conversation or create new one.

        Args:
            db: Database session
            conversation_id: Existing conversation UUID (optional)
            session_id: Client session identifier (optional)
            metadata: Additional metadata (optional)

        Returns:
            Conversation model
        """
        if conversation_id:
            # Try to get existing conversation
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()

            if conversation:
                return conversation

        # Create new conversation
        conversation = Conversation(
            session_id=session_id,
            metadata=metadata or {}
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        logger.info(f"✅ Created new conversation: {conversation.id}")
        return conversation

    async def add_message(
        self,
        db: Session,
        conversation_id: UUID,
        role: str,
        content: str,
        audio_url: Optional[str] = None,
        latency_ms: Optional[int] = None
    ) -> Message:
        """
        Add message to conversation.

        Args:
            db: Database session
            conversation_id: Conversation UUID
            role: Message role ('user' or 'assistant')
            content: Message text content
            audio_url: URL to TTS audio (optional)
            latency_ms: Response generation time (optional)

        Returns:
            Created Message model
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            audio_url=audio_url,
            latency_ms=latency_ms
        )
        db.add(message)

        # Increment message count
        db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(message_count=Conversation.message_count + 1)
        )

        db.commit()
        db.refresh(message)

        logger.debug(f"Added {role} message to conversation {conversation_id}")
        return message

    async def get_conversation_history(
        self,
        db: Session,
        conversation_id: UUID,
        limit: int = MAX_CONVERSATION_HISTORY
    ) -> List[Dict[str, str]]:
        """
        Get conversation history formatted for LLM.

        Args:
            db: Database session
            conversation_id: Conversation UUID
            limit: Maximum number of messages to retrieve

        Returns:
            List of message dicts with 'role' and 'content' keys
        """
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.created_at.asc()
        ).limit(limit).all()

        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    async def get_all_conversations(
        self,
        db: Session,
        limit: int = 50,
        offset: int = 0
    ) -> List[Conversation]:
        """
        Get all conversations with pagination.

        Args:
            db: Database session
            limit: Number of conversations to retrieve
            offset: Number of conversations to skip

        Returns:
            List of Conversation models
        """
        return db.query(Conversation).order_by(
            desc(Conversation.started_at)
        ).limit(limit).offset(offset).all()

    async def get_conversation_with_messages(
        self,
        db: Session,
        conversation_id: str
    ) -> Optional[Dict]:
        """
        Get conversation with all its messages.

        Args:
            db: Database session
            conversation_id: Conversation UUID

        Returns:
            Dict with conversation and messages, or None if not found
        """
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            return None

        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).all()

        return {
            "conversation": conversation,
            "messages": messages
        }

    async def end_conversation(
        self,
        db: Session,
        conversation_id: UUID
    ) -> Optional[Conversation]:
        """
        Mark conversation as ended.

        Args:
            db: Database session
            conversation_id: Conversation UUID

        Returns:
            Updated Conversation model or None if not found
        """
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            return None

        conversation.ended_at = datetime.utcnow()
        db.commit()
        db.refresh(conversation)

        logger.info(f"✅ Ended conversation: {conversation_id}")
        return conversation

    async def delete_conversation(
        self,
        db: Session,
        conversation_id: str
    ) -> bool:
        """
        Delete conversation and all its messages.

        Args:
            db: Database session
            conversation_id: Conversation UUID

        Returns:
            True if deleted, False if not found
        """
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            return False

        db.delete(conversation)
        db.commit()

        logger.info(f"🗑️ Deleted conversation: {conversation_id}")
        return True

    async def get_conversation_count(self, db: Session) -> int:
        """
        Get total number of conversations.

        Args:
            db: Database session

        Returns:
            Total conversation count
        """
        return db.query(Conversation).count()


# Create singleton instance
conversation_manager = ConversationManager()

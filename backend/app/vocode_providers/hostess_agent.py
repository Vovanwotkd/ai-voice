"""
Hostess Agent for Vocode with RAG integration
"""

import asyncio
import logging
from typing import Optional, AsyncGenerator
import uuid

from vocode.streaming.agent.base_agent import BaseAgent, AgentResponseMessage
from vocode.streaming.models.agent import AgentConfig
from vocode.streaming.models.message import BaseMessage

from app.services.rag_service import rag_service
from app.services.prompt_service import prompt_service
from app.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.core.constants import MESSAGE_ROLE_USER, MESSAGE_ROLE_ASSISTANT
from sqlalchemy import select

logger = logging.getLogger(__name__)


class HostessAgentConfig(AgentConfig):
    """Configuration for Hostess Agent"""

    use_rag: bool = True
    initial_message: Optional[str] = "Добрый день! Ресторан Гастрономия, чем могу помочь?"


class HostessAgent(BaseAgent[HostessAgentConfig]):
    """
    AI Hostess Agent with RAG capabilities for Vocode
    """

    def __init__(self, agent_config: HostessAgentConfig):
        super().__init__(agent_config=agent_config)

        self.conversation_history = []
        self.conversation_id = None

        logger.info(f"HostessAgent initialized with RAG={'enabled' if agent_config.use_rag else 'disabled'}")

    async def respond(
        self,
        human_input,
        conversation_id: str,
        is_interrupt: bool = False,
    ) -> tuple[Optional[str], bool]:
        """
        Generate response to human input (simple version)

        Returns:
            Tuple of (response_text, end_conversation)
        """
        try:
            # Initialize conversation if needed
            if not self.conversation_id:
                self.conversation_id = uuid.UUID(conversation_id)
                await self._load_conversation_history()

            # Get system prompt from DB
            system_prompt = None
            async for db in get_db():
                system_prompt = await prompt_service.get_active_prompt(db)
                break

            # Generate response using RAG
            if self.agent_config.use_rag:
                rag_response = await rag_service.answer_with_context(
                    query=human_input,
                    conversation_history=self.conversation_history,
                    system_prompt=system_prompt,
                    use_rag=True
                )
                response_text = rag_response["content"]
            else:
                # Without RAG
                from app.services.llm_service import llm_service
                llm_response = await llm_service.generate_response(
                    message=human_input,
                    conversation_history=self.conversation_history,
                    system_prompt=system_prompt
                )
                response_text = llm_response["content"]

            # Save to history
            self.conversation_history.append({"role": "user", "content": human_input})
            self.conversation_history.append({"role": "assistant", "content": response_text})

            # Save to DB
            await self._save_messages(human_input, response_text)

            logger.info(f"Response: {response_text[:100]}...")

            # Check if we should end conversation
            end_conversation = self._should_end_conversation(response_text)

            return response_text, end_conversation

        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return "Извините, произошла ошибка. Попробуйте повторить вопрос.", False

    async def generate_response(
        self,
        human_input,
        conversation_id: str,
        is_interrupt: bool = False,
    ) -> AsyncGenerator[AgentResponseMessage, None]:
        """
        Generate response as async generator (for streaming)
        """
        response_text, end_conversation = await self.respond(
            human_input,
            conversation_id,
            is_interrupt
        )

        if response_text:
            yield AgentResponseMessage(message=BaseMessage(text=response_text))

    async def _load_conversation_history(self):
        """Load conversation history from DB"""
        try:
            async for db in get_db():
                # Get or create conversation
                result = await db.execute(
                    select(Conversation).where(Conversation.id == self.conversation_id)
                )
                conversation = result.scalar_one_or_none()

                if not conversation:
                    conversation = Conversation(
                        id=self.conversation_id,
                        user_id=None,
                        title="Voice Call",
                        is_voice=True
                    )
                    db.add(conversation)
                    await db.commit()

                # Load messages
                result = await db.execute(
                    select(Message)
                    .where(Message.conversation_id == self.conversation_id)
                    .order_by(Message.created_at)
                )
                messages = result.scalars().all()

                self.conversation_history = [
                    {"role": msg.role, "content": msg.content}
                    for msg in messages
                ]

                logger.info(f"Loaded {len(self.conversation_history)} messages")

        except Exception as e:
            logger.error(f"Error loading conversation: {e}")

    async def _save_messages(self, user_input: str, assistant_response: str):
        """Save messages to DB"""
        try:
            async for db in get_db():
                # Save user message
                user_msg = Message(
                    conversation_id=self.conversation_id,
                    role=MESSAGE_ROLE_USER,
                    content=user_input
                )
                db.add(user_msg)

                # Save assistant message
                assistant_msg = Message(
                    conversation_id=self.conversation_id,
                    role=MESSAGE_ROLE_ASSISTANT,
                    content=assistant_response
                )
                db.add(assistant_msg)

                await db.commit()

        except Exception as e:
            logger.error(f"Error saving messages: {e}")

    def _should_end_conversation(self, response: str) -> bool:
        """Check if conversation should end"""
        # Simple heuristic - can be improved
        end_phrases = ["до свидания", "всего доброго", "спасибо за звонок"]
        return any(phrase in response.lower() for phrase in end_phrases)

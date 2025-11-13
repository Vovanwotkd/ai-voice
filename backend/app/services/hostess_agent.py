"""
Hostess Agent for Vocode with RAG Integration
Handles conversational AI with restaurant knowledge base
"""

import logging
from typing import Optional, AsyncGenerator, List, Dict, Any
from vocode.streaming.agent.base_agent import BaseAgent, AgentResponseMessage
from vocode.streaming.models.agent import AgentConfig
from vocode.streaming.models.message import BaseMessage

from app.services.rag_service import rag_service
from app.services.llm_service import llm_service
from app.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

logger = logging.getLogger(__name__)


class HostessAgentConfig(AgentConfig):
    """Configuration for Hostess Agent"""

    agent_type: str = "agent_hostess"

    # System prompt
    system_prompt: str = """
Ты - профессиональная хостес ресторана "Гастрономия".

Твоя роль:
- Отвечать на вопросы о ресторане, меню, акциях
- Помогать с бронированием столиков
- Предоставлять информацию о режиме работы
- Быть вежливой, дружелюбной и профессиональной

Стиль общения:
- Естественный разговорный русский язык
- Краткие, но информативные ответы
- Избегай длинных списков - предлагай уточнить детали
- Используй базу знаний для точной информации

Если информации нет в базе знаний - честно скажи об этом и предложи уточнить у менеджера.
"""

    # RAG settings
    use_rag: bool = True
    rag_top_k: int = 5

    # Conversation settings
    initial_message: Optional[str] = "Добрый день! Ресторан Гастрономия, я ваша виртуальная хостес. Чем могу помочь?"
    generate_responses: bool = True
    end_conversation_on_goodbye: bool = False

    # Response generation settings
    interrupt_sensitivity: str = "high"  # low | medium | high
    allow_agent_to_be_cut_off: bool = True


class HostessAgent(BaseAgent[HostessAgentConfig]):
    """
    AI Hostess Agent with RAG capabilities.

    Integrates with:
    - RAG service for knowledge base queries
    - LLM service for response generation
    - Database for conversation persistence
    """

    def __init__(self, agent_config: HostessAgentConfig):
        super().__init__(agent_config)

        self.system_prompt = agent_config.system_prompt
        self.use_rag = agent_config.use_rag

        # Conversation state
        self.conversation_id: Optional[uuid.UUID] = None
        self.conversation_history: List[Dict[str, str]] = []

        logger.info(f"HostessAgent initialized with RAG={'enabled' if self.use_rag else 'disabled'}")

    async def _initialize_conversation(self, call_id: str) -> None:
        """Initialize or load conversation from database"""
        try:
            async for db in get_db():
                # Try to find existing conversation by call_id
                result = await db.execute(
                    select(Conversation).where(Conversation.id == uuid.UUID(call_id))
                )
                conversation = result.scalar_one_or_none()

                if not conversation:
                    # Create new conversation
                    conversation = Conversation(
                        id=uuid.UUID(call_id),
                        user_id=None,  # Anonymous voice calls
                        title="Voice Call",
                        is_voice=True
                    )
                    db.add(conversation)
                    await db.commit()
                    await db.refresh(conversation)

                    logger.info(f"Created new conversation: {conversation.id}")

                self.conversation_id = conversation.id

                # Load conversation history
                result = await db.execute(
                    select(Message)
                    .where(Message.conversation_id == conversation.id)
                    .order_by(Message.created_at)
                )
                messages = result.scalars().all()

                self.conversation_history = [
                    {
                        "role": msg.role.value,
                        "content": msg.content
                    }
                    for msg in messages
                ]

                logger.info(f"Loaded {len(self.conversation_history)} messages from history")

        except Exception as e:
            logger.error(f"Error initializing conversation: {e}")
            # Continue without database persistence
            self.conversation_id = uuid.uuid4()

    async def _save_message(
        self,
        role: MessageRole,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save message to database"""
        if not self.conversation_id:
            return

        try:
            async for db in get_db():
                message = Message(
                    conversation_id=self.conversation_id,
                    role=role,
                    content=content,
                    metadata=metadata or {}
                )
                db.add(message)
                await db.commit()

                # Add to in-memory history
                self.conversation_history.append({
                    "role": role.value,
                    "content": content
                })

        except Exception as e:
            logger.error(f"Error saving message: {e}")

    async def respond(
        self,
        human_input: str,
        conversation_id: Optional[str] = None,
        is_interrupt: bool = False,
    ) -> AsyncGenerator[AgentResponseMessage, None]:
        """
        Generate response to human input.

        Args:
            human_input: User's message
            conversation_id: Unique conversation/call identifier
            is_interrupt: Whether this is interrupting agent speech

        Yields:
            AgentResponseMessage with response text
        """

        try:
            # Initialize conversation if needed
            if conversation_id and not self.conversation_id:
                await self._initialize_conversation(conversation_id)

            # Save user message
            logger.info(f"User: {human_input}")
            await self._save_message(MessageRole.USER, human_input)

            # Handle interruption
            if is_interrupt:
                logger.debug("User interrupted - stopping current response")
                # Vocode will handle stopping synthesis

            # Generate response using RAG
            if self.use_rag:
                # Use RAG service for context-aware response
                rag_response = await rag_service.answer_with_context(
                    query=human_input,
                    conversation_history=self.conversation_history,
                    system_prompt=self.system_prompt,
                    use_rag=True
                )

                response_text = rag_response["content"]
                rag_used = rag_response.get("rag_used", False)
                chunks_count = len(rag_response.get("chunks", []))

                logger.info(f"RAG response: {response_text[:100]}... (RAG used: {rag_used}, chunks: {chunks_count})")

                # Save assistant message with metadata
                await self._save_message(
                    MessageRole.ASSISTANT,
                    response_text,
                    metadata={
                        "rag_used": rag_used,
                        "chunks_count": chunks_count,
                        "latency_ms": rag_response.get("usage", {}).get("latency_ms", 0)
                    }
                )

            else:
                # Direct LLM response without RAG
                llm_response = await llm_service.generate_response(
                    message=human_input,
                    conversation_history=self.conversation_history,
                    system_prompt=self.system_prompt
                )

                response_text = llm_response["content"]
                logger.info(f"LLM response: {response_text[:100]}...")

                # Save assistant message
                await self._save_message(MessageRole.ASSISTANT, response_text)

            # Yield response as single message
            # Vocode will handle streaming to TTS
            yield AgentResponseMessage(message=BaseMessage(text=response_text))

        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)

            # Yield error message
            error_message = "Извините, произошла ошибка. Попробуйте повторить ваш вопрос."
            yield AgentResponseMessage(message=BaseMessage(text=error_message))

    async def generate_completion(
        self,
        human_input: str,
        conversation_id: Optional[str] = None,
        is_interrupt: bool = False,
    ) -> str:
        """
        Generate a single complete response (non-streaming version).

        Used by some Vocode components that expect full response.
        """
        response_text = ""

        async for response_message in self.respond(
            human_input=human_input,
            conversation_id=conversation_id,
            is_interrupt=is_interrupt
        ):
            response_text += response_message.message.text

        return response_text

    def get_initial_message(self) -> Optional[str]:
        """Get initial greeting message"""
        return self.agent_config.initial_message

    async def update_system_prompt(self, new_prompt: str) -> None:
        """Update system prompt dynamically"""
        self.system_prompt = new_prompt
        logger.info(f"System prompt updated: {new_prompt[:100]}...")


# ==========================================
# Helper Functions
# ==========================================

def create_hostess_agent(
    system_prompt: Optional[str] = None,
    use_rag: bool = True,
    initial_message: Optional[str] = None
) -> HostessAgent:
    """
    Factory function to create a HostessAgent with custom configuration.

    Args:
        system_prompt: Custom system prompt
        use_rag: Enable RAG for knowledge base queries
        initial_message: Custom initial greeting

    Returns:
        Configured HostessAgent instance
    """

    config = HostessAgentConfig(
        system_prompt=system_prompt or HostessAgentConfig().system_prompt,
        use_rag=use_rag,
        initial_message=initial_message or HostessAgentConfig().initial_message
    )

    return HostessAgent(agent_config=config)


# ==========================================
# Example System Prompts
# ==========================================

SYSTEM_PROMPTS = {
    "default": """
Ты - профессиональная хостес ресторана "Гастрономия".
Отвечай на вопросы о ресторане, меню, бронировании.
Будь вежливой, дружелюбной и профессиональной.
Используй базу знаний для точной информации.
""",

    "casual": """
Привет! Я виртуальная хостес ресторана "Гастрономия".
Общаюсь дружелюбно и непринужденно.
Помогу с выбором блюд, бронированием и любыми вопросами о ресторане.
""",

    "formal": """
Добрый день. Я представитель ресторана "Гастрономия".
Предоставляю профессиональную консультацию по всем вопросам:
- Меню и рекомендации блюд
- Бронирование столиков
- Режим работы и услуги
Используйте базу знаний для предоставления точной информации.
""",

    "promotional": """
Добро пожаловать в ресторан "Гастрономия"!
Я помогу вам узнать о наших специальных предложениях, акциях и новинках меню.
Расскажу о преимуществах нашего заведения и помогу с бронированием.
Активно предлагай актуальные акции и специальные блюда.
"""
}

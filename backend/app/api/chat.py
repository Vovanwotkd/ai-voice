"""
Chat API endpoints for communicating with the hostess bot
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.api.deps import get_db
from app.schemas.message import ChatRequest, ChatResponse
from app.schemas.conversation import ConversationResponse, ConversationWithMessages
from app.services.llm_service import llm_service
from app.services.prompt_service import prompt_service
from app.services.conversation_manager import conversation_manager
from app.services.rag_service import rag_service
from app.core.constants import MESSAGE_ROLE_USER, MESSAGE_ROLE_ASSISTANT

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Send a text message to the bot and get response.

    Args:
        request: Chat request with message and optional conversation_id
        db: Database session

    Returns:
        Chat response with bot message, conversation_id, and latency

    Example:
        POST /api/chat/message
        {
            "message": "Здравствуйте, хочу забронировать столик",
            "conversation_id": null,
            "generate_audio": false
        }
    """
    try:
        # Get or create conversation
        conversation = await conversation_manager.get_or_create_conversation(
            db=db,
            conversation_id=request.conversation_id
        )

        # Get conversation history
        history = await conversation_manager.get_conversation_history(
            db=db,
            conversation_id=conversation.id,
            limit=10  # Last 10 messages for context
        )

        # Get active prompt and render with variables
        prompt_content = await prompt_service.load_active_prompt(db)
        if not prompt_content:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No active system prompt found"
            )

        system_prompt = prompt_service.render_prompt(prompt_content)

        # Generate response with RAG (if enabled)
        use_rag = getattr(request, 'use_rag', True)  # RAG enabled by default
        rag_response = await rag_service.answer_with_context(
            query=request.message,
            conversation_history=history,
            system_prompt=system_prompt,
            use_rag=use_rag
        )

        # Extract response content and metadata
        response_content = rag_response["content"]
        latency_ms = rag_response.get("usage", {}).get("latency_ms", 0)

        # Debug: log the response
        logger.info(f"RAG response: '{response_content}' (RAG used: {rag_response['rag_used']}, chunks: {rag_response['context_chunks']})")

        # Save user message
        await conversation_manager.add_message(
            db=db,
            conversation_id=conversation.id,
            role=MESSAGE_ROLE_USER,
            content=request.message
        )

        # Save assistant message
        await conversation_manager.add_message(
            db=db,
            conversation_id=conversation.id,
            role=MESSAGE_ROLE_ASSISTANT,
            content=response_content,
            latency_ms=latency_ms
        )

        # TODO: Generate TTS audio if requested (Phase 3)
        audio_url = None
        if request.generate_audio:
            logger.info("TTS audio generation requested (not implemented yet)")

        return ChatResponse(
            conversation_id=str(conversation.id),
            message=response_content,
            audio_url=audio_url,
            latency_ms=latency_ms
        )

    except Exception as e:
        logger.error(f"Error in send_message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get("/history", response_model=List[ConversationResponse])
async def get_chat_history(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get all conversations with pagination.

    Args:
        limit: Number of conversations to retrieve (max 100)
        offset: Number of conversations to skip
        db: Database session

    Returns:
        List of conversations

    Example:
        GET /api/chat/history?limit=20&offset=0
    """
    if limit > 100:
        limit = 100

    try:
        conversations = await conversation_manager.get_all_conversations(
            db=db,
            limit=limit,
            offset=offset
        )
        return conversations

    except Exception as e:
        logger.error(f"Error in get_chat_history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat history: {str(e)}"
        )


@router.get("/conversation/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """
    Get conversation with all messages.

    Args:
        conversation_id: Conversation UUID
        db: Database session

    Returns:
        Conversation with messages

    Example:
        GET /api/chat/conversation/550e8400-e29b-41d4-a716-446655440000
    """
    try:
        result = await conversation_manager.get_conversation_with_messages(
            db=db,
            conversation_id=conversation_id
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )

        return {
            **result["conversation"].__dict__,
            "messages": result["messages"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation: {str(e)}"
        )


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete conversation and all its messages.

    Args:
        conversation_id: Conversation UUID
        db: Database session

    Returns:
        Success message

    Example:
        DELETE /api/chat/conversation/550e8400-e29b-41d4-a716-446655440000
    """
    try:
        deleted = await conversation_manager.delete_conversation(
            db=db,
            conversation_id=conversation_id
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )

        return {"message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )

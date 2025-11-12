"""
Prompts Management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.api.deps import get_db
from app.schemas.prompt import (
    PromptResponse,
    PromptUpdate,
    PromptReloadResponse,
    PromptPreviewRequest,
    PromptPreviewResponse,
    PromptVariablesResponse
)
from app.services.prompt_service import prompt_service
from app.services.llm_service import llm_service
from app.models.prompt import Prompt

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[PromptResponse])
async def get_all_prompts(
    db: Session = Depends(get_db)
):
    """
    Get all prompts from database.

    Returns:
        List of all prompts

    Example:
        GET /api/prompts
    """
    try:
        prompts = db.query(Prompt).all()
        return prompts

    except Exception as e:
        logger.error(f"Error in get_all_prompts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve prompts: {str(e)}"
        )


@router.get("/active", response_model=PromptResponse)
async def get_active_prompt(
    db: Session = Depends(get_db)
):
    """
    Get currently active system prompt.

    Returns:
        Active prompt

    Example:
        GET /api/prompts/active
    """
    try:
        prompt = await prompt_service.get_active_prompt(db)

        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active system prompt found"
            )

        return prompt

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_active_prompt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve active prompt: {str(e)}"
        )


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt_by_id(
    prompt_id: str,
    db: Session = Depends(get_db)
):
    """
    Get prompt by ID.

    Args:
        prompt_id: Prompt UUID
        db: Database session

    Returns:
        Prompt

    Example:
        GET /api/prompts/550e8400-e29b-41d4-a716-446655440000
    """
    try:
        prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()

        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt {prompt_id} not found"
            )

        return prompt

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_prompt_by_id: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve prompt: {str(e)}"
        )


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: str,
    update_data: PromptUpdate,
    db: Session = Depends(get_db)
):
    """
    Update prompt.

    Args:
        prompt_id: Prompt UUID
        update_data: Updated prompt data
        db: Database session

    Returns:
        Updated prompt

    Example:
        PUT /api/prompts/550e8400-e29b-41d4-a716-446655440000
        {
            "content": "Ты - улучшенный помощник-хостес...",
            "is_active": true
        }
    """
    try:
        prompt = await prompt_service.update_prompt(
            db=db,
            prompt_id=prompt_id,
            content=update_data.content,
            is_active=update_data.is_active
        )

        logger.info(f"✅ Updated prompt {prompt_id} (version {prompt.version})")
        return prompt

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in update_prompt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update prompt: {str(e)}"
        )


@router.post("/reload", response_model=PromptReloadResponse)
async def reload_prompts(
    db: Session = Depends(get_db)
):
    """
    🔥 Hot reload - reload active prompt without restarting service.

    This endpoint reloads the active system prompt from database
    and updates both PromptService and LLMService caches.

    Returns:
        Reload status and active prompt

    Example:
        POST /api/prompts/reload
    """
    try:
        # Reload prompt from database
        prompt_content = await prompt_service.reload_prompt(db)

        if not prompt_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active system prompt found"
            )

        # Get the active prompt model
        active_prompt = await prompt_service.get_active_prompt(db)

        logger.info("🔥 Prompt hot reloaded successfully")

        return PromptReloadResponse(
            status="reloaded",
            active_prompt=active_prompt
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reload_prompts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload prompts: {str(e)}"
        )


@router.get("/variables/available", response_model=PromptVariablesResponse)
async def get_available_variables():
    """
    Get all available template variables with their current values.

    Returns:
        Dict of variable names to values

    Example:
        GET /api/prompts/variables/available
        Response:
        {
            "variables": {
                "{date}": "12.11.2024",
                "{time}": "15:30",
                "{restaurant_name}": "Гастрономия",
                ...
            }
        }
    """
    try:
        variables = prompt_service.get_available_variables()
        return PromptVariablesResponse(variables=variables)

    except Exception as e:
        logger.error(f"Error in get_available_variables: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get variables: {str(e)}"
        )


@router.post("/preview", response_model=PromptPreviewResponse)
async def preview_prompt(
    request: PromptPreviewRequest
):
    """
    Preview prompt with variable substitution.

    Useful for testing prompt templates before saving.

    Args:
        request: Prompt content to preview

    Returns:
        Rendered prompt with variables replaced

    Example:
        POST /api/prompts/preview
        {
            "content": "Ты - хостес {restaurant_name}. Сегодня {date}"
        }
    """
    try:
        rendered = prompt_service.render_prompt(request.content)
        return PromptPreviewResponse(preview=rendered)

    except Exception as e:
        logger.error(f"Error in preview_prompt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview prompt: {str(e)}"
        )

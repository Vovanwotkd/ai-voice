"""
Pydantic schemas for Prompt model
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime
from uuid import UUID


class PromptBase(BaseModel):
    """Base schema for Prompt"""
    name: str = Field(..., max_length=100, description="Prompt identifier")
    content: str = Field(..., description="Prompt text content")
    variables: Optional[Dict] = Field(default_factory=dict, description="Template variables")
    description: Optional[str] = Field(None, description="Prompt description")


class PromptCreate(PromptBase):
    """Schema for creating a new Prompt"""
    is_active: bool = Field(default=True, description="Whether prompt is active")


class PromptUpdate(BaseModel):
    """Schema for updating an existing Prompt"""
    content: Optional[str] = Field(None, description="Updated prompt content")
    variables: Optional[Dict] = Field(None, description="Updated variables")
    is_active: Optional[bool] = Field(None, description="Update active status")
    description: Optional[str] = Field(None, description="Updated description")


class PromptResponse(PromptBase):
    """Schema for Prompt responses"""
    id: UUID
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PromptPreviewRequest(BaseModel):
    """Schema for prompt preview request"""
    content: str = Field(..., description="Prompt content to preview")


class PromptPreviewResponse(BaseModel):
    """Schema for prompt preview response"""
    preview: str = Field(..., description="Rendered prompt with variables")


class PromptReloadResponse(BaseModel):
    """Schema for prompt reload response"""
    status: str = Field(default="reloaded", description="Reload status")
    active_prompt: PromptResponse


class PromptVariablesResponse(BaseModel):
    """Schema for available variables response"""
    variables: Dict[str, str] = Field(..., description="Available template variables")

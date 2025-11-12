"""
Prompt model for storing system prompts
"""

from sqlalchemy import Column, String, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import BaseModel


class Prompt(BaseModel):
    """
    Model for storing system prompts that guide the hostess bot behavior.
    Supports versioning and hot reload.
    """

    __tablename__ = "prompts"

    name = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Prompt identifier (e.g., 'system_prompt')"
    )

    content = Column(
        Text,
        nullable=False,
        comment="Prompt text content with variable placeholders"
    )

    variables = Column(
        JSONB,
        nullable=True,
        default=dict,
        comment="Variables for prompt template (e.g., restaurant info)"
    )

    version = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Prompt version number"
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether this prompt is currently active"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Optional description of what this prompt does"
    )

    def __repr__(self) -> str:
        return f"<Prompt(name='{self.name}', version={self.version}, active={self.is_active})>"

"""
Prompt Service for managing system prompts in database
"""

from typing import Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.models.prompt import Prompt
from app.core.default_prompts import DEFAULT_SYSTEM_PROMPT
from app.core.constants import PROMPT_TYPE_SYSTEM
from app.config import settings
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class PromptService:
    """
    Service for managing prompts in database.
    Handles creation, retrieval, updating, and variable rendering.
    """

    def __init__(self):
        self._cached_prompt: Optional[str] = None

    async def initialize_default_prompt(self) -> None:
        """
        Initialize default system prompt in database if it doesn't exist.
        Called on application startup.
        """
        db = SessionLocal()
        try:
            # Check if system prompt exists
            existing = db.query(Prompt).filter(
                Prompt.name == PROMPT_TYPE_SYSTEM,
                Prompt.is_active == True
            ).first()

            if not existing:
                # Create default prompt
                default_prompt = Prompt(
                    name=PROMPT_TYPE_SYSTEM,
                    content=DEFAULT_SYSTEM_PROMPT,
                    is_active=True,
                    description="Default system prompt for restaurant hostess bot"
                )
                db.add(default_prompt)
                db.commit()
                logger.info("✅ Default system prompt created")
            else:
                logger.info("✅ System prompt already exists")

            # Load into memory
            await self.load_active_prompt(db)

        except Exception as e:
            logger.error(f"❌ Failed to initialize default prompt: {e}")
            db.rollback()
        finally:
            db.close()

    async def load_active_prompt(self, db: Session) -> Optional[str]:
        """
        Load active system prompt from database.

        Args:
            db: Database session

        Returns:
            Prompt content or None
        """
        try:
            prompt = db.query(Prompt).filter(
                Prompt.name == PROMPT_TYPE_SYSTEM,
                Prompt.is_active == True
            ).first()

            if prompt:
                self._cached_prompt = prompt.content
                logger.debug(f"Loaded prompt (version {prompt.version})")
                return prompt.content
            else:
                logger.warning("No active system prompt found")
                return None

        except Exception as e:
            logger.error(f"Failed to load active prompt: {e}")
            return None

    def get_active_prompt_sync(self) -> Optional[str]:
        """
        Synchronous version of get_active_prompt.
        Used by LLM service initialization.

        Returns:
            Cached prompt content or None
        """
        if self._cached_prompt:
            return self._cached_prompt

        # Load from database if not cached
        db = SessionLocal()
        try:
            prompt = db.query(Prompt).filter(
                Prompt.name == PROMPT_TYPE_SYSTEM,
                Prompt.is_active == True
            ).first()

            if prompt:
                self._cached_prompt = prompt.content
                return prompt.content
            return None

        except Exception as e:
            logger.error(f"Failed to get active prompt: {e}")
            return None
        finally:
            db.close()

    async def get_active_prompt(self, db: Session) -> Optional[Prompt]:
        """
        Get active system prompt model from database.

        Args:
            db: Database session

        Returns:
            Prompt model or None
        """
        return db.query(Prompt).filter(
            Prompt.name == PROMPT_TYPE_SYSTEM,
            Prompt.is_active == True
        ).first()

    async def update_prompt(
        self,
        db: Session,
        prompt_id: str,
        content: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Prompt:
        """
        Update existing prompt.

        Args:
            db: Database session
            prompt_id: Prompt UUID
            content: New content (optional)
            is_active: New active status (optional)

        Returns:
            Updated Prompt model

        Raises:
            ValueError: If prompt not found
        """
        prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if not prompt:
            raise ValueError(f"Prompt with id {prompt_id} not found")

        if content is not None:
            prompt.content = content
            prompt.version += 1

        if is_active is not None:
            prompt.is_active = is_active

        db.commit()
        db.refresh(prompt)

        # Reload into cache if this is the active system prompt
        if prompt.name == PROMPT_TYPE_SYSTEM and prompt.is_active:
            self._cached_prompt = prompt.content
            logger.info(f"✅ Prompt updated (version {prompt.version})")

        return prompt

    def render_prompt(self, prompt_template: str) -> str:
        """
        Render prompt template with variable substitution.

        Available variables:
        - {date}: Current date
        - {time}: Current time
        - {restaurant_name}: Restaurant name
        - {restaurant_phone}: Restaurant phone
        - {restaurant_address}: Restaurant address

        Args:
            prompt_template: Prompt text with {variable} placeholders

        Returns:
            Rendered prompt with variables replaced
        """
        variables = self.get_available_variables()

        rendered = prompt_template
        for var, value in variables.items():
            rendered = rendered.replace(var, value)

        return rendered

    def get_available_variables(self) -> Dict[str, str]:
        """
        Get all available template variables and their current values.

        Returns:
            Dict of variable names to values
        """
        now = datetime.now()

        return {
            "{date}": now.strftime("%d.%m.%Y"),
            "{time}": now.strftime("%H:%M"),
            "{restaurant_name}": settings.RESTAURANT_NAME,
            "{restaurant_phone}": settings.RESTAURANT_PHONE,
            "{restaurant_address}": settings.RESTAURANT_ADDRESS,
        }

    async def reload_prompt(self, db: Session) -> Optional[str]:
        """
        🔥 Hot reload - reload prompt from database without restart.

        Args:
            db: Database session

        Returns:
            Reloaded prompt content
        """
        prompt_content = await self.load_active_prompt(db)
        if prompt_content:
            # Also reload in LLM service
            from app.services.llm_service import llm_service
            llm_service.reload_prompt(self.render_prompt(prompt_content))
            logger.info("🔥 Prompt hot reloaded successfully")

        return prompt_content


# Create singleton instance
prompt_service = PromptService()

"""
LLM Service for generating responses using various AI providers
Supports: Claude (Anthropic), OpenAI GPT-4, Yandex GPT
"""

from typing import List, Dict, Optional
import anthropic
import openai
import httpx
import time
import logging

from app.config import settings
from app.core.constants import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    LLM_PROVIDER_CLAUDE,
    LLM_PROVIDER_OPENAI,
    LLM_PROVIDER_YANDEX
)

logger = logging.getLogger(__name__)


class LLMService:
    """
    Unified LLM service supporting multiple providers.
    Handles prompt loading, variable substitution, and response generation.
    """

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self._current_prompt: Optional[str] = None
        self._initialize_clients()

    def _initialize_clients(self) -> None:
        """Initialize API clients based on configured provider"""
        try:
            if self.provider == LLM_PROVIDER_CLAUDE:
                if not settings.ANTHROPIC_API_KEY:
                    raise ValueError("ANTHROPIC_API_KEY is required for Claude provider")
                self.anthropic_client = anthropic.Anthropic(
                    api_key=settings.ANTHROPIC_API_KEY
                )
                logger.info("✅ Claude (Anthropic) client initialized")

            elif self.provider == LLM_PROVIDER_OPENAI:
                if not settings.OPENAI_API_KEY:
                    raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
                openai.api_key = settings.OPENAI_API_KEY
                logger.info("✅ OpenAI client initialized")

            elif self.provider == LLM_PROVIDER_YANDEX:
                if not settings.YANDEX_API_KEY or not settings.YANDEX_FOLDER_ID:
                    raise ValueError("YANDEX_API_KEY and YANDEX_FOLDER_ID are required for Yandex provider")
                logger.info("✅ Yandex GPT client initialized")

            else:
                raise ValueError(f"Unknown LLM provider: {self.provider}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM client: {e}")
            raise

    def load_prompt(self, prompt_content: str) -> None:
        """
        Load system prompt into memory.

        Args:
            prompt_content: System prompt text
        """
        self._current_prompt = prompt_content
        logger.debug(f"Loaded prompt ({len(prompt_content)} chars)")

    def reload_prompt(self, prompt_content: str) -> None:
        """
        🔥 Hot reload - reload prompt without restarting service.

        Args:
            prompt_content: New system prompt text
        """
        self.load_prompt(prompt_content)
        logger.info(f"🔥 Prompt hot reloaded successfully. Provider: {self.provider}")

    async def generate_response(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE
    ) -> Dict:
        """
        Generate response from LLM.

        Args:
            message: User message
            conversation_history: Previous messages in conversation
            system_prompt: System prompt (overrides loaded prompt)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 to 1.0)

        Returns:
            Dict with 'content', 'latency_ms', 'provider'

        Raises:
            Exception: If LLM generation fails
        """
        if conversation_history is None:
            conversation_history = []

        # Use provided system prompt or loaded one
        prompt = system_prompt or self._current_prompt
        if not prompt:
            raise ValueError("No system prompt loaded. Call load_prompt() first.")

        # Add current message to history
        messages = conversation_history + [
            {"role": "user", "content": message}
        ]

        start_time = time.time()

        try:
            # Generate based on provider
            if self.provider == LLM_PROVIDER_CLAUDE:
                response_text = await self._generate_claude(
                    system_prompt=prompt,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            elif self.provider == LLM_PROVIDER_OPENAI:
                response_text = await self._generate_openai(
                    system_prompt=prompt,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            elif self.provider == LLM_PROVIDER_YANDEX:
                response_text = await self._generate_yandex(
                    system_prompt=prompt,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            else:
                raise ValueError(f"Unknown provider: {self.provider}")

            latency_ms = int((time.time() - start_time) * 1000)

            logger.info(f"✅ Generated response in {latency_ms}ms using {self.provider}")

            return {
                "content": response_text,
                "latency_ms": latency_ms,
                "provider": self.provider
            }

        except Exception as e:
            logger.error(f"❌ LLM generation error ({self.provider}): {e}")
            raise

    async def _generate_claude(
        self,
        system_prompt: str,
        messages: List[Dict],
        max_tokens: int,
        temperature: float
    ) -> str:
        """Generate response using Claude (Anthropic)"""
        try:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages
            )
            return response.content[0].text

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise

    async def _generate_openai(
        self,
        system_prompt: str,
        messages: List[Dict],
        max_tokens: int,
        temperature: float
    ) -> str:
        """Generate response using OpenAI GPT-4"""
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *messages
                ]
            )
            return response.choices[0].message.content

        except openai.error.OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    async def _generate_yandex(
        self,
        system_prompt: str,
        messages: List[Dict],
        max_tokens: int,
        temperature: float
    ) -> str:
        """Generate response using Yandex GPT"""
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

        headers = {
            "Authorization": f"Api-Key {settings.YANDEX_API_KEY}",
            "Content-Type": "application/json",
            "x-folder-id": settings.YANDEX_FOLDER_ID
        }

        # Convert messages format for Yandex
        yandex_messages = [
            {"role": "system", "text": system_prompt}
        ]
        for msg in messages:
            yandex_messages.append({
                "role": msg["role"],
                "text": msg["content"]
            })

        data = {
            "modelUri": f"gpt://{settings.YANDEX_FOLDER_ID}/yandexgpt/latest",
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": str(max_tokens)
            },
            "messages": yandex_messages
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()

                # Debug: log the full response
                logger.debug(f"Yandex GPT response: {result}")

                # Extract text from Yandex response format
                response_text = result["result"]["alternatives"][0]["message"]["text"]
                logger.debug(f"Extracted text: {response_text}")
                return response_text

        except httpx.HTTPError as e:
            logger.error(f"Yandex GPT API error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response body: {e.response.text}")
            raise


# Create singleton instance
llm_service = LLMService()

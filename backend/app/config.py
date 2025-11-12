"""
Application configuration using pydantic-settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    DEBUG: bool = False
    SECRET_KEY: str
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string into a list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # LLM Provider Configuration
    LLM_PROVIDER: str = "claude"  # claude | openai | yandex
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    YANDEX_API_KEY: Optional[str] = None
    YANDEX_FOLDER_ID: Optional[str] = None

    # Restaurant Information
    RESTAURANT_NAME: str = "Гастрономия"
    RESTAURANT_PHONE: str = "+7-XXX-XXX-XX-XX"
    RESTAURANT_ADDRESS: str = "Москва, ул. Примерная, 1"

    # RAG Configuration (for future use)
    VECTOR_DB_TYPE: str = "chromadb"  # chromadb | qdrant
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 5
    RAG_MIN_SCORE: float = 0.7

    # Vocode Configuration (for future use)
    VOCODE_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    def validate_llm_provider(self) -> None:
        """Validate that required API keys are present for selected LLM provider"""
        if self.LLM_PROVIDER == "claude" and not self.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=claude")
        elif self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        elif self.LLM_PROVIDER == "yandex" and (not self.YANDEX_API_KEY or not self.YANDEX_FOLDER_ID):
            raise ValueError("YANDEX_API_KEY and YANDEX_FOLDER_ID are required when LLM_PROVIDER=yandex")


# Create global settings instance
settings = Settings()

# Validate LLM provider configuration
try:
    settings.validate_llm_provider()
except ValueError as e:
    import sys
    print(f"⚠️  Configuration Error: {e}")
    if not settings.DEBUG:
        sys.exit(1)

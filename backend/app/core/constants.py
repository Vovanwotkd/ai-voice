"""
Application constants
"""

# Prompt types
PROMPT_TYPE_SYSTEM = "system_prompt"
PROMPT_TYPE_USER = "user_prompt"

# Conversation statuses
CONVERSATION_STATUS_ACTIVE = "active"
CONVERSATION_STATUS_ENDED = "ended"

# Message roles
MESSAGE_ROLE_USER = "user"
MESSAGE_ROLE_ASSISTANT = "assistant"
MESSAGE_ROLE_SYSTEM = "system"

# LLM Providers
LLM_PROVIDER_CLAUDE = "claude"
LLM_PROVIDER_OPENAI = "openai"
LLM_PROVIDER_YANDEX = "yandex"

# Default LLM settings
DEFAULT_MAX_TOKENS = 500
DEFAULT_TEMPERATURE = 0.7

# Conversation limits
MAX_CONVERSATION_HISTORY = 50
MAX_MESSAGE_LENGTH = 4000

# File upload limits
MAX_UPLOAD_SIZE_MB = 10
ALLOWED_DOCUMENT_TYPES = [".pdf", ".docx", ".txt", ".md", ".json"]

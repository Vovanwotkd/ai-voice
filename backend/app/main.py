"""
FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import logging

from app.config import settings
from app.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - runs on startup and shutdown
    """
    # Startup
    logger.info("🚀 Starting AI Voice Hostess Bot API...")
    logger.info(f"📊 LLM Provider: {settings.LLM_PROVIDER}")
    logger.info(f"🏪 Restaurant: {settings.RESTAURANT_NAME}")

    # Initialize database
    init_db()
    logger.info("✅ Database initialized")

    # Initialize default prompt
    from app.services.prompt_service import prompt_service
    await prompt_service.initialize_default_prompt()
    logger.info("✅ Default prompt initialized")

    yield

    # Shutdown
    logger.info("👋 Shutting down API...")


# Create FastAPI application
app = FastAPI(
    title="AI Voice Hostess Bot API",
    description="Backend API for AI-powered restaurant hostess bot with RAG",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create static directories if they don't exist
os.makedirs("static/audio", exist_ok=True)
os.makedirs("data/uploads", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
from app.api import health, chat, prompts

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(prompts.router, prefix="/api/prompts", tags=["Prompts"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Voice Hostess Bot API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

"""
Health check endpoints for monitoring application status
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis

from app.api.deps import get_db
from app.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    Returns 200 OK if the service is running.
    """
    return {
        "status": "healthy",
        "service": "AI Voice Hostess Bot API",
        "version": "1.0.0"
    }


@router.get("/health/db")
async def health_check_database(db: Session = Depends(get_db)):
    """
    Database health check.
    Returns 200 OK if database connection is working.
    """
    try:
        # Execute a simple query to test connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )


@router.get("/health/redis")
async def health_check_redis():
    """
    Redis health check.
    Returns 200 OK if Redis connection is working.
    """
    try:
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        r.ping()
        return {
            "status": "healthy",
            "redis": "connected"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis connection failed: {str(e)}"
        )


@router.get("/health/full")
async def full_health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check for all services.
    Checks database, Redis, and application status.
    """
    health_status = {
        "status": "healthy",
        "service": "AI Voice Hostess Bot API",
        "version": "1.0.0",
        "checks": {}
    }

    # Check database
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"

    # Check Redis
    try:
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        r.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"

    # Check LLM provider configuration
    try:
        settings.validate_llm_provider()
        health_status["checks"]["llm_provider"] = f"configured ({settings.LLM_PROVIDER})"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["llm_provider"] = f"misconfigured: {str(e)}"

    # Return appropriate status code
    if health_status["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )

    return health_status

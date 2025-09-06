"""Health check routes."""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from src.captcha.factory import get_captcha_provider
from src.config.settings import config
from src.database.connection import get_session

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "TGuard API"
    }


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with dependencies."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "TGuard API",
        "version": "1.0.0",
        "checks": {}
    }

    # Check database connection
    try:
        async with get_session() as session:
            await session.execute("SELECT 1")
        health_status["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"

    # Check captcha provider
    try:
        captcha_provider = get_captcha_provider()
        health_status["checks"]["captcha"] = {
            "status": "healthy",
            "provider": captcha_provider.provider_name
        }
    except Exception as e:
        logger.error(f"Captcha provider health check failed: {e}")
        health_status["checks"]["captcha"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"

    # Check configuration
    try:
        # Validate critical config values
        if not config.bot.token or config.bot.token == "YOUR_BOT_TOKEN_HERE":
            raise ValueError("Bot token not configured")

        captcha_config = getattr(config.captcha, config.captcha.provider)
        if not captcha_config.site_key or not captcha_config.secret_key:
            raise ValueError("Captcha keys not configured")

        health_status["checks"]["configuration"] = {"status": "healthy"}
    except Exception as e:
        logger.error(f"Configuration health check failed: {e}")
        health_status["checks"]["configuration"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"

    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)

    return health_status

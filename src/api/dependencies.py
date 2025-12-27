"""FastAPI dependencies for authentication and authorization."""

import logging

from fastapi import Header, HTTPException, status

from src.config.settings import config

logger = logging.getLogger(__name__)


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """
    Verify API Key from X-API-Key header.
    
    Args:
        x_api_key: API key from X-API-Key header
        
    Returns:
        The API key if valid
        
    Raises:
        HTTPException: If API is disabled or key is invalid
    """
    # Check if API is enabled
    if not config.api.enable:
        logger.warning("API access attempted but API is disabled")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API访问已禁用"
        )
    
    # Check if API key is configured
    if not config.api.api_key:
        logger.error("API is enabled but API key is not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API配置错误"
        )
    
    # Verify API key
    if x_api_key != config.api.api_key:
        logger.warning(f"Invalid API key attempted: {x_api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API密钥",
            headers={"WWW-Authenticate": "X-API-Key"},
        )
    
    return x_api_key

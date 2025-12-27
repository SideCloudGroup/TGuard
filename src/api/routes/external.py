"""External API routes for creating verification requests."""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.api.dependencies import verify_api_key
from src.config.settings import config
from src.database.operations import create_join_request, create_verification_session
from src.utils.crypto import generate_verification_token

logger = logging.getLogger(__name__)
router = APIRouter()


class CreateVerificationRequest(BaseModel):
    """Request model for creating verification."""
    user_id: int


class CreateVerificationResponse(BaseModel):
    """Response model for creating verification."""
    token: str
    verification_url: str
    expires_at: str


@router.post("/verification/create", response_model=CreateVerificationResponse)
async def create_verification(
    request: CreateVerificationRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Create a new verification request via external API.
    
    This endpoint allows external bots to create verification requests
    for Telegram users. Returns a token and verification URL.
    """
    try:
        user_id = request.user_id
        
        logger.info(f"Creating verification request via API for user {user_id}")
        
        # Generate verification token
        verification_token = generate_verification_token()
        
        # Set expiration time to 10 minutes
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Use 0 as chat_id for external API requests (not tied to a specific chat)
        chat_id = 0
        
        # Create join request record (with minimal data, marked as API type)
        db_join_request = await create_join_request(
            user_id=user_id,
            chat_id=chat_id,
            username=None,
            first_name="",
            last_name=None,
            verification_token=verification_token,
            request_type="api"
        )
        
        if not db_join_request:
            logger.error(f"Failed to create join request for user {user_id}")
            raise HTTPException(
                status_code=500,
                detail="创建验证请求失败"
            )
        
        # Create verification session
        verification_session = await create_verification_session(
            token=verification_token,
            user_id=user_id,
            chat_id=chat_id,
            expires_at=expires_at
        )
        
        if not verification_session:
            logger.error(f"Failed to create verification session for user {user_id}")
            raise HTTPException(
                status_code=500,
                detail="创建验证会话失败"
            )
        
        # Generate verification URL
        verification_url = f"{config.api.base_url}/verify?token={verification_token}"
        
        logger.info(f"Verification request created successfully for user {user_id}, token: {verification_token[:8]}...")
        
        return CreateVerificationResponse(
            token=verification_token,
            verification_url=verification_url,
            expires_at=expires_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating verification request: {e}")
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误"
        )

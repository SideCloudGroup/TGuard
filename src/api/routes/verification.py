"""Verification API routes."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel

from src.captcha.factory import get_captcha_provider
from src.database.operations import (
    get_verification_session,
    complete_verification,
    get_join_request_by_token,
    approve_join_request
)
from src.api.services.approval import auto_approve_user

logger = logging.getLogger(__name__)
router = APIRouter()


class VerificationRequest(BaseModel):
    """Verification request model."""
    token: str
    captcha_response: str


class VerificationResponse(BaseModel):
    """Verification response model."""
    success: bool
    message: str
    redirect_url: Optional[str] = None


def get_client_ip(request: Request) -> str:
    """Get client IP address."""
    # Check for forwarded headers (when behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host


@router.post("/verify", response_model=VerificationResponse)
async def verify_captcha(
    verification_req: VerificationRequest,
    request: Request
):
    """Verify captcha and process join request."""
    try:
        token = verification_req.token
        captcha_response = verification_req.captcha_response
        
        logger.info(f"Processing verification for token: {token}")
        
        # Get verification session
        session = await get_verification_session(token)
        if not session:
            logger.warning(f"Verification session not found: {token}")
            raise HTTPException(
                status_code=404,
                detail="验证会话不存在或已过期"
            )
        
        # Check if session is expired
        if session.is_expired:
            logger.warning(f"Verification session expired: {token}")
            raise HTTPException(
                status_code=400,
                detail="验证会话已过期，请重新申请"
            )
        
        # Check if already completed
        if session.captcha_completed:
            logger.warning(f"Verification already completed: {token}")
            raise HTTPException(
                status_code=400,
                detail="验证已完成，请勿重复提交"
            )
        
        # Get client info
        client_ip = get_client_ip(request)
        user_agent = request.headers.get("User-Agent")
        
        # Verify captcha
        captcha_provider = get_captcha_provider()
        verification_result = await captcha_provider.verify(
            response=captcha_response,
            remote_ip=client_ip,
            user_agent=user_agent
        )
        
        if not verification_result.success:
            logger.warning(f"Captcha verification failed: {verification_result.error_code}")
            raise HTTPException(
                status_code=400,
                detail=verification_result.error_message or "验证失败，请重试"
            )
        
        # Mark verification as completed
        success = await complete_verification(
            token=token,
            captcha_response=captcha_response,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        if not success:
            logger.error(f"Failed to complete verification: {token}")
            raise HTTPException(
                status_code=500,
                detail="服务器错误，请稍后重试"
            )
        
        # Auto-approve the user
        approval_result = await auto_approve_user(token)
        
        if approval_result.success:
            logger.info(f"User auto-approved successfully: {token}")
            return VerificationResponse(
                success=True,
                message="✅ 验证成功！您已被批准加入群组。",
                redirect_url="https://t.me"  # Redirect to Telegram
            )
        else:
            logger.warning(f"Auto-approval failed: {approval_result.error}")
            return VerificationResponse(
                success=True,
                message="✅ 验证成功！正在处理您的加群申请，请稍等。"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误"
        )


@router.get("/verification-status/{token}")
async def get_verification_status(token: str):
    """Get verification status for a token."""
    try:
        session = await get_verification_session(token)
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail="验证会话不存在"
            )
        
        join_request = await get_join_request_by_token(token)
        
        return {
            "token": token,
            "completed": session.captcha_completed,
            "expired": session.is_expired,
            "status": join_request.status if join_request else "unknown",
            "created_time": session.created_time.isoformat(),
            "expires_at": session.expires_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting verification status: {e}")
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误"
        )


@router.get("/captcha-config")
async def get_captcha_config():
    """Get captcha configuration for frontend."""
    try:
        captcha_provider = get_captcha_provider()
        config = captcha_provider.get_frontend_config()
        
        return {
            "captcha": config,
            "provider": captcha_provider.provider_name
        }
        
    except Exception as e:
        logger.error(f"Error getting captcha config: {e}")
        raise HTTPException(
            status_code=500,
            detail="无法获取验证配置"
        )

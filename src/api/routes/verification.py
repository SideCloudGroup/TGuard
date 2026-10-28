"""Verification API routes."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from src.api.services.approval import auto_approve_user
from src.captcha.factory import get_captcha_provider
from src.config.settings import config
from src.database.operations import (
    approve_join_request,
    get_verification_session,
    complete_verification,
    get_join_request_by_token
)
from src.utils.telegram import validate_init_data

logger = logging.getLogger(__name__)
router = APIRouter()


class VerificationRequest(BaseModel):
    """Verification request model."""
    token: str
    captcha_response: str
    user_id: Optional[int] = None
    init_data: Optional[str] = None


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

        logger.info(f"Processing verification for token: {token[:8]}...")

        # Get verification session
        session = await get_verification_session(token)
        if not session:
            logger.warning(f"Verification session not found: {token[:8]}...")
            raise HTTPException(
                status_code=404,
                detail="验证会话不存在或已过期"
            )

        # Check if session is expired
        if session.is_expired:
            logger.warning(f"Verification session expired: {token[:8]}...")
            raise HTTPException(
                status_code=400,
                detail="验证会话已过期，请重新申请"
            )

        # Check if already completed
        if session.captcha_completed:
            logger.warning(f"Verification already completed: {token[:8]}...")
            raise HTTPException(
                status_code=400,
                detail="验证已完成，请勿重复提交"
            )

        # Verify the submitter is the user this session was issued to
        join_request = await get_join_request_by_token(token)
        # chat_id=0 sessions can only be issued by the external API, regardless of the join request row
        is_api_request = session.chat_id == 0 or (
            join_request is not None and join_request.request_type == "api"
        )

        telegram_user = validate_init_data(verification_req.init_data or "", config.bot.token)
        if telegram_user:
            claimed_user_id = telegram_user["id"]
            identity_ok = claimed_user_id == session.user_id
        elif not is_api_request:
            # Telegram requests are opened via our own web_app button, so signed initData is mandatory
            claimed_user_id = None
            identity_ok = False
        else:
            # External API links may be opened outside Telegram or from another bot's web_app button,
            # whose initData is signed with a token we don't have; fall back to the client-reported ID
            claimed_user_id = verification_req.user_id
            identity_ok = claimed_user_id is None or claimed_user_id == session.user_id

        if not identity_ok:
            logger.warning(
                f"User identity check failed for token {token[:8]}...: "
                f"expected {session.user_id}, got {claimed_user_id}"
            )
            raise HTTPException(
                status_code=403,
                detail="用户身份验证失败"
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
            logger.error(f"Failed to complete verification: {token[:8]}...")
            raise HTTPException(
                status_code=500,
                detail="服务器错误，请稍后重试"
            )

        # API requests created without a chat (chat_id=0) have no Telegram join request to approve,
        # but the row must leave PENDING or it is reused by later requests and never purged
        if is_api_request and (join_request is None or join_request.chat_id == 0):
            if join_request is not None and not await approve_join_request(token):
                logger.warning(f"Failed to mark API request as approved: {token[:8]}...")
            logger.info(f"Verification completed for API request (no chat): {token[:8]}...")
            return VerificationResponse(success=True, message="✅ 验证成功！")

        approval_result = await auto_approve_user(token)
        if not approval_result.success:
            logger.warning(f"Auto-approval failed: {approval_result.error}")
            return VerificationResponse(success=True, message="✅ 验证成功！")

        logger.info(f"User auto-approved successfully: {token[:8]}...")
        return VerificationResponse(
            success=True,
            message="✅ 验证成功！",
            redirect_url="tg://"  # Deep link back to Telegram
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

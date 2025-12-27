"""Static file routes for Mini Web App."""

import logging

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.captcha.factory import get_captcha_provider
from src.config.settings import config
from src.database.operations import get_verification_session

logger = logging.getLogger(__name__)
router = APIRouter()

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")


@router.get("/verify", response_class=HTMLResponse)
async def verification_page(request: Request, token: str):
    """Serve verification page for Mini Web App."""
    try:
        # Validate token
        session = await get_verification_session(token)
        if not session:
            logger.warning(f"Invalid verification token: {token}")
            raise HTTPException(status_code=404, detail="验证链接无效或已过期")

        if session.is_expired:
            logger.warning(f"Expired verification token: {token}")
            return templates.TemplateResponse(
                "expired.html",
                {"request": request, "message": "验证链接已过期，请重新申请加群"}
            )

        if session.captcha_completed:
            logger.info(f"Verification already completed: {token}")
            return templates.TemplateResponse(
                "completed.html",
                {"request": request, "message": "您已完成验证，请等待管理员审核"}
            )

        # Pass expected user_id to template for client-side validation
        # The client will verify this matches the Telegram Web App user ID
        
        # Get captcha configuration
        captcha_provider = get_captcha_provider()
        captcha_config = captcha_provider.get_frontend_config()

        return templates.TemplateResponse(
            "verify.html",
            {
                "request": request,
                "token": token,
                "expected_user_id": session.user_id,
                "captcha_config": captcha_config,
                "api_base_url": config.api.base_url
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving verification page: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "页面加载失败，请稍后重试"}
        )


@router.get("/success", response_class=HTMLResponse)
async def success_page(request: Request):
    """Success page after verification."""
    return templates.TemplateResponse(
        "success.html",
        {"request": request}
    )


@router.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    """Index page with bot information."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

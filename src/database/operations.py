"""Database operations for TGuard bot."""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, update, func
from sqlalchemy.exc import SQLAlchemyError

from src.database.connection import get_session
from src.database.models import JoinRequest, VerificationSession, RequestStatus

logger = logging.getLogger(__name__)


async def create_join_request(
        user_id: int,
        chat_id: int,
        username: Optional[str],
        first_name: str,
        last_name: Optional[str],
        verification_token: str
) -> Optional[JoinRequest]:
    """Create a new join request."""
    try:
        async with get_session()() as session:
            # Check if there's already a pending request
            existing_request = await session.execute(
                select(JoinRequest).where(
                    JoinRequest.user_id == user_id,
                    JoinRequest.chat_id == chat_id,
                    JoinRequest.status == RequestStatus.PENDING
                )
            )
            existing = existing_request.scalar_one_or_none()

            if existing:
                # Update existing request with new token
                existing.verification_token = verification_token
                existing.request_time = datetime.utcnow()
                existing.verification_completed = False
                await session.commit()
                logger.info(f"Updated existing join request for user {user_id}")
                return existing

            # Create new request
            join_request = JoinRequest(
                user_id=user_id,
                chat_id=chat_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                verification_token=verification_token
            )

            session.add(join_request)
            await session.commit()
            await session.refresh(join_request)

            logger.info(f"Created join request for user {user_id}")
            return join_request

    except SQLAlchemyError as e:
        logger.error(f"Error creating join request: {e}")
        return None


async def create_verification_session(
        token: str,
        user_id: int,
        chat_id: int,
        expires_at: datetime
) -> Optional[VerificationSession]:
    """Create a new verification session."""
    try:
        async with get_session()() as session:
            # Delete any existing session with the same token
            await session.execute(
                update(VerificationSession)
                .where(VerificationSession.token == token)
                .values(expires_at=datetime.utcnow())  # Mark as expired
            )

            verification_session = VerificationSession(
                token=token,
                user_id=user_id,
                chat_id=chat_id,
                expires_at=expires_at
            )

            session.add(verification_session)
            await session.commit()
            await session.refresh(verification_session)

            logger.info(f"Created verification session for user {user_id}")
            return verification_session

    except SQLAlchemyError as e:
        logger.error(f"Error creating verification session: {e}")
        return None


async def get_verification_session(token: str) -> Optional[VerificationSession]:
    """Get verification session by token."""
    try:
        async with get_session()() as session:
            result = await session.execute(
                select(VerificationSession).where(VerificationSession.token == token)
            )
            return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error(f"Error getting verification session: {e}")
        return None


async def complete_verification(
        token: str,
        captcha_response: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
) -> bool:
    """Mark verification as completed."""
    try:
        async with get_session()() as session:
            # Update verification session
            await session.execute(
                update(VerificationSession)
                .where(VerificationSession.token == token)
                .values(
                    captcha_completed=True,
                    captcha_response=captcha_response,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    completed_time=datetime.utcnow()
                )
            )

            # Update join request
            await session.execute(
                update(JoinRequest)
                .where(JoinRequest.verification_token == token)
                .values(verification_completed=True)
            )

            await session.commit()
            logger.info(f"Verification completed for token {token}")
            return True

    except SQLAlchemyError as e:
        logger.error(f"Error completing verification: {e}")
        return False


async def approve_join_request(token: str, admin_id: Optional[int] = None) -> bool:
    """Approve a join request."""
    try:
        async with get_session()() as session:
            await session.execute(
                update(JoinRequest)
                .where(JoinRequest.verification_token == token)
                .values(
                    status=RequestStatus.APPROVED,
                    processed_time=datetime.utcnow(),
                    admin_id=admin_id
                )
            )

            await session.commit()
            logger.info(f"Join request approved for token {token}")
            return True

    except SQLAlchemyError as e:
        logger.error(f"Error approving join request: {e}")
        return False


async def get_join_request_by_token(token: str) -> Optional[JoinRequest]:
    """Get join request by verification token."""
    try:
        async with get_session()() as session:
            result = await session.execute(
                select(JoinRequest).where(JoinRequest.verification_token == token)
            )
            return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error(f"Error getting join request: {e}")
        return None


async def get_pending_requests(chat_id: int, limit: int = 50) -> List[JoinRequest]:
    """Get pending join requests for a chat."""
    try:
        async with get_session()() as session:
            result = await session.execute(
                select(JoinRequest)
                .where(
                    JoinRequest.chat_id == chat_id,
                    JoinRequest.status == RequestStatus.PENDING
                )
                .order_by(JoinRequest.request_time.desc())
                .limit(limit)
            )
            return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Error getting pending requests: {e}")
        return []


async def get_verification_stats(chat_id: int) -> Dict[str, Any]:
    """Get verification statistics for a chat."""
    try:
        async with get_session()() as session:
            # Get total counts by status
            result = await session.execute(
                select(
                    JoinRequest.status,
                    func.count(JoinRequest.id).label('count')
                )
                .where(JoinRequest.chat_id == chat_id)
                .group_by(JoinRequest.status)
            )

            counts = {row.status: row.count for row in result}

            total = sum(counts.values())
            approved = counts.get(RequestStatus.APPROVED, 0)

            stats = {
                'total_requests': total,
                'approved': approved,
                'rejected': counts.get(RequestStatus.REJECTED, 0),
                'pending': counts.get(RequestStatus.PENDING, 0),
                'expired': counts.get(RequestStatus.EXPIRED, 0),
                'approval_rate': (approved / total * 100) if total > 0 else 0
            }

            return stats

    except SQLAlchemyError as e:
        logger.error(f"Error getting verification stats: {e}")
        return {}


async def get_global_stats() -> Dict[str, Any]:
    """Get global verification statistics."""
    try:
        async with get_session()() as session:
            # Get total counts by status
            result = await session.execute(
                select(
                    JoinRequest.status,
                    func.count(JoinRequest.id).label('count')
                )
                .group_by(JoinRequest.status)
            )

            counts = {row.status: row.count for row in result}

            total = sum(counts.values())
            approved = counts.get(RequestStatus.APPROVED, 0)

            # Get today's stats
            today = datetime.utcnow().date()
            today_result = await session.execute(
                select(
                    JoinRequest.status,
                    func.count(JoinRequest.id).label('count')
                )
                .where(func.date(JoinRequest.request_time) == today)
                .group_by(JoinRequest.status)
            )

            today_counts = {row.status: row.count for row in today_result}
            today_total = sum(today_counts.values())
            today_approved = today_counts.get(RequestStatus.APPROVED, 0)

            stats = {
                'total_requests': total,
                'approved': approved,
                'rejected': counts.get(RequestStatus.REJECTED, 0),
                'pending': counts.get(RequestStatus.PENDING, 0),
                'expired': counts.get(RequestStatus.EXPIRED, 0),
                'approval_rate': (approved / total * 100) if total > 0 else 0,
                'today_total': today_total,
                'today_approved': today_approved,
                'today_approval_rate': (today_approved / today_total * 100) if today_total > 0 else 0
            }

            return stats

    except SQLAlchemyError as e:
        logger.error(f"Error getting global stats: {e}")
        return {}


async def cleanup_expired_sessions():
    """Clean up expired verification sessions and requests."""
    try:
        async with get_session()() as session:
            now = datetime.utcnow()

            # Mark expired verification sessions
            await session.execute(
                update(VerificationSession)
                .where(
                    VerificationSession.expires_at < now,
                    VerificationSession.captcha_completed == False
                )
                .values(expires_at=now)
            )

            # Mark corresponding join requests as expired
            expired_tokens = await session.execute(
                select(VerificationSession.token)
                .where(
                    VerificationSession.expires_at < now,
                    VerificationSession.captcha_completed == False
                )
            )

            for token_row in expired_tokens:
                await session.execute(
                    update(JoinRequest)
                    .where(
                        JoinRequest.verification_token == token_row.token,
                        JoinRequest.status == RequestStatus.PENDING
                    )
                    .values(status=RequestStatus.EXPIRED)
                )

            await session.commit()
            logger.info("Cleaned up expired sessions")

    except SQLAlchemyError as e:
        logger.error(f"Error cleaning up expired sessions: {e}")

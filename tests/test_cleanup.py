"""Tests for expired-session cleanup and stale-record purge."""

from datetime import datetime, timedelta

import pytest

from src.database.models import JoinRequest, RequestStatus, VerificationSession
from src.database.operations import cleanup_expired_sessions, purge_stale_records


async def _add(factory, *objects):
    async with factory() as session:
        session.add_all(objects)
        await session.commit()


@pytest.mark.asyncio
async def test_cleanup_expired_sessions_marks_pending_and_returns_dismiss_list(db_session):
    now = datetime.utcnow()
    await _add(
        db_session,
        VerificationSession(
            token="expired-tg",
            user_id=11,
            chat_id=-1001,
            captcha_completed=False,
            created_time=now - timedelta(minutes=10),
            expires_at=now - timedelta(minutes=1),
        ),
        JoinRequest(
            user_id=11,
            chat_id=-1001,
            first_name="A",
            verification_token="expired-tg",
            status=RequestStatus.PENDING,
            request_time=now - timedelta(minutes=10),
            request_type="telegram",
        ),
        VerificationSession(
            token="expired-api",
            user_id=22,
            chat_id=0,
            captcha_completed=False,
            created_time=now - timedelta(minutes=10),
            expires_at=now - timedelta(minutes=1),
        ),
        JoinRequest(
            user_id=22,
            chat_id=0,
            first_name="B",
            verification_token="expired-api",
            status=RequestStatus.PENDING,
            request_time=now - timedelta(minutes=10),
            request_type="api",
        ),
        VerificationSession(
            token="active",
            user_id=33,
            chat_id=-1002,
            captcha_completed=False,
            created_time=now,
            expires_at=now + timedelta(minutes=5),
        ),
        JoinRequest(
            user_id=33,
            chat_id=-1002,
            first_name="C",
            verification_token="active",
            status=RequestStatus.PENDING,
            request_time=now,
            request_type="telegram",
        ),
    )

    to_dismiss = await cleanup_expired_sessions()

    assert to_dismiss == [(-1001, 11)]

    async with db_session() as session:
        from sqlalchemy import select

        rows = (await session.execute(select(JoinRequest))).scalars().all()
        status_by_token = {row.verification_token: row.status for row in rows}

    assert status_by_token["expired-tg"] == RequestStatus.EXPIRED
    assert status_by_token["expired-api"] == RequestStatus.EXPIRED
    assert status_by_token["active"] == RequestStatus.PENDING


@pytest.mark.asyncio
async def test_purge_stale_records_deletes_only_old_data(db_session):
    now = datetime.utcnow()
    old = now - timedelta(days=40)
    recent = now - timedelta(days=3)

    await _add(
        db_session,
        VerificationSession(
            token="old-session",
            user_id=1,
            chat_id=-100,
            captcha_completed=True,
            created_time=old,
            expires_at=old + timedelta(minutes=10),
        ),
        VerificationSession(
            token="recent-session",
            user_id=2,
            chat_id=-100,
            captcha_completed=True,
            created_time=recent,
            expires_at=recent + timedelta(minutes=10),
        ),
        JoinRequest(
            user_id=1,
            chat_id=-100,
            first_name="Old",
            verification_token="old-approved",
            status=RequestStatus.APPROVED,
            request_time=old,
            request_type="telegram",
        ),
        JoinRequest(
            user_id=2,
            chat_id=-100,
            first_name="Recent",
            verification_token="recent-approved",
            status=RequestStatus.APPROVED,
            request_time=recent,
            request_type="telegram",
        ),
        JoinRequest(
            user_id=3,
            chat_id=-100,
            first_name="Pending",
            verification_token="old-pending",
            status=RequestStatus.PENDING,
            request_time=old,
            request_type="telegram",
        ),
    )

    deleted = await purge_stale_records(retention_days=30)

    assert deleted["sessions"] == 1
    assert deleted["join_requests"] == 2

    async with db_session() as session:
        from sqlalchemy import select

        sessions = (await session.execute(select(VerificationSession))).scalars().all()
        requests = (await session.execute(select(JoinRequest))).scalars().all()

    assert {item.token for item in sessions} == {"recent-session"}
    assert {item.verification_token for item in requests} == {"recent-approved"}


@pytest.mark.asyncio
async def test_purge_stale_records_respects_custom_retention(db_session):
    now = datetime.utcnow()
    await _add(
        db_session,
        VerificationSession(
            token="eight-days",
            user_id=1,
            chat_id=-100,
            created_time=now - timedelta(days=8),
            expires_at=now - timedelta(days=8),
        ),
        JoinRequest(
            user_id=1,
            chat_id=-100,
            first_name="Old",
            verification_token="eight-days",
            status=RequestStatus.EXPIRED,
            request_time=now - timedelta(days=8),
        ),
    )

    deleted = await purge_stale_records(retention_days=7)

    assert deleted == {"sessions": 1, "join_requests": 1}

"""Fix join requests left behind by older external API code."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .base import Migration


class FixStaleApiRequestsMigration(Migration):
    """Repair request_type and status of external API join requests."""

    def get_version(self) -> str:
        return "004"

    def get_description(self) -> str:
        return "Mark chat_id=0 join requests as api and approve completed ones stuck in pending"

    async def upgrade(self, session: AsyncSession) -> None:
        """Fix request_type and release completed API requests from pending."""
        # Only the external API creates chat_id=0 rows; the first API release stored them as 'telegram'
        await session.execute(text("""
            UPDATE join_requests
            SET request_type = 'api'
            WHERE chat_id = 0 AND request_type <> 'api'
        """))

        # Completed API requests without a chat never left pending, so they were reused and never purged
        await session.execute(text("""
            UPDATE join_requests
            SET status = 'approved',
                processed_time = COALESCE(processed_time, request_time)
            WHERE chat_id = 0 AND status = 'pending' AND verification_completed = TRUE
        """))

        await session.commit()

    async def downgrade(self, session: AsyncSession) -> None:
        """Data fix only; the original values are not worth restoring."""
        pass

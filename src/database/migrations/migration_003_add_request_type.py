"""Add request_type field to join_requests migration."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .base import Migration


class AddRequestTypeMigration(Migration):
    """Add request_type field to join_requests table."""
    
    def get_version(self) -> str:
        return "003"
    
    def get_description(self) -> str:
        return "Add request_type field to join_requests table to distinguish API and Telegram requests"
    
    async def upgrade(self, session: AsyncSession) -> None:
        """Add request_type column to join_requests table."""
        # Add request_type column with default value 'telegram' for existing records
        await session.execute(text("""
            ALTER TABLE join_requests 
            ADD COLUMN request_type VARCHAR(20) NOT NULL DEFAULT 'telegram'
        """))
        
        # Create index for request_type
        await session.execute(text("CREATE INDEX idx_join_requests_request_type ON join_requests(request_type)"))
        
        await session.commit()
    
    async def downgrade(self, session: AsyncSession) -> None:
        """Remove request_type column from join_requests table."""
        await session.execute(text("DROP INDEX IF EXISTS idx_join_requests_request_type"))
        await session.execute(text("ALTER TABLE join_requests DROP COLUMN IF EXISTS request_type"))
        await session.commit()


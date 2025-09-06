"""Add user statistics tracking migration."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .base import Migration


class AddUserStatsMigration(Migration):
    """Add user statistics tracking migration."""
    
    def get_version(self) -> str:
        return "002"
    
    def get_description(self) -> str:
        return "Add user statistics tracking table"
    
    async def upgrade(self, session: AsyncSession) -> None:
        """Add user_stats table."""
        await session.execute(text("""
            CREATE TABLE user_stats (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                total_requests INTEGER NOT NULL DEFAULT 0,
                successful_verifications INTEGER NOT NULL DEFAULT 0,
                failed_verifications INTEGER NOT NULL DEFAULT 0,
                last_verification_time TIMESTAMP,
                created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create unique index on user_id
        await session.execute(text("CREATE UNIQUE INDEX idx_user_stats_user_id ON user_stats(user_id)"))
        
        # Create trigger to update updated_time
        await session.execute(text("""
            CREATE OR REPLACE FUNCTION update_updated_time_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_time = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """))
        
        await session.execute(text("""
            CREATE TRIGGER update_user_stats_updated_time 
            BEFORE UPDATE ON user_stats 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_time_column();
        """))
        
        await session.commit()
    
    async def downgrade(self, session: AsyncSession) -> None:
        """Remove user_stats table."""
        await session.execute(text("DROP TRIGGER IF EXISTS update_user_stats_updated_time ON user_stats"))
        await session.execute(text("DROP FUNCTION IF EXISTS update_updated_time_column()"))
        await session.execute(text("DROP TABLE IF EXISTS user_stats"))
        await session.commit()

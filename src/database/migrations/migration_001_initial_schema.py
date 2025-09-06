"""Initial database schema migration."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .base import Migration


class InitialSchemaMigration(Migration):
    """Initial database schema migration."""
    
    def get_version(self) -> str:
        return "001"
    
    def get_description(self) -> str:
        return "Create initial database schema with join_requests and verification_sessions tables"
    
    async def upgrade(self, session: AsyncSession) -> None:
        """Create initial tables."""
        # Create join_requests table
        await session.execute(text("""
            CREATE TABLE join_requests (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                chat_id BIGINT NOT NULL,
                username VARCHAR(255),
                first_name VARCHAR(255) NOT NULL,
                last_name VARCHAR(255),
                verification_token VARCHAR(64) NOT NULL UNIQUE,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                request_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                processed_time TIMESTAMP,
                admin_id BIGINT,
                verification_completed BOOLEAN NOT NULL DEFAULT FALSE
            )
        """))
        
        # Create indexes for join_requests
        await session.execute(text("CREATE INDEX idx_join_requests_user_id ON join_requests(user_id)"))
        await session.execute(text("CREATE INDEX idx_join_requests_chat_id ON join_requests(chat_id)"))
        await session.execute(text("CREATE INDEX idx_join_requests_token ON join_requests(verification_token)"))
        await session.execute(text("CREATE INDEX idx_join_requests_status ON join_requests(status)"))
        
        # Create verification_sessions table
        await session.execute(text("""
            CREATE TABLE verification_sessions (
                id SERIAL PRIMARY KEY,
                token VARCHAR(64) NOT NULL UNIQUE,
                user_id BIGINT NOT NULL,
                chat_id BIGINT NOT NULL,
                captcha_completed BOOLEAN NOT NULL DEFAULT FALSE,
                captcha_response TEXT,
                ip_address VARCHAR(45),
                user_agent TEXT,
                created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_time TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """))
        
        # Create indexes for verification_sessions
        await session.execute(text("CREATE INDEX idx_verification_sessions_token ON verification_sessions(token)"))
        await session.execute(text("CREATE INDEX idx_verification_sessions_user_id ON verification_sessions(user_id)"))
        
        await session.commit()
    
    async def downgrade(self, session: AsyncSession) -> None:
        """Drop initial tables."""
        await session.execute(text("DROP TABLE IF EXISTS verification_sessions"))
        await session.execute(text("DROP TABLE IF EXISTS join_requests"))
        await session.commit()

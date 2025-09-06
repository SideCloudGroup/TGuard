"""Database connection management."""

import logging
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.config.settings import config
from src.database.models import Base
from src.database.migrations.manager import run_migrations

logger = logging.getLogger(__name__)

# Global database engine and session factory
engine: Optional[object] = None
async_session_factory: Optional[async_sessionmaker] = None


async def init_database():
    """Initialize database connection and create tables."""
    global engine, async_session_factory

    try:
        # Create async engine
        engine = create_async_engine(
            config.database.url,
            pool_size=config.database.min_size,
            max_overflow=config.database.max_size - config.database.min_size,
            echo=False,  # Set to True for SQL debugging
            future=True
        )

        # Create session factory
        async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # Run migrations instead of creating tables directly
        await run_migrations(async_session_factory)

        logger.info("Database initialized successfully")

    except SQLAlchemyError as e:
        logger.error(f"Database initialization error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {e}")
        raise


def get_session():
    """Get database session factory."""
    if async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")

    return async_session_factory


async def close_database():
    """Close database connections."""
    global engine

    if engine:
        await engine.dispose()
        logger.info("Database connections closed")

"""Database connection management."""

import asyncio
import logging
from typing import Optional

from sqlalchemy import event
from sqlalchemy.engine import ExceptionContext
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker

from src.config.settings import config
from src.database.migrations.manager import run_migrations

logger = logging.getLogger(__name__)

# Without these, a connection to a vanished server (e.g. a recreated container with a new IP)
# blocks until the kernel gives up on TCP retransmits, which takes ~15 minutes.
CONNECT_TIMEOUT_SECONDS = 10
COMMAND_TIMEOUT_SECONDS = 30
POOL_TIMEOUT_SECONDS = 10
POOL_RECYCLE_SECONDS = 30 * 60

# Global database engine and session factory
engine: Optional[AsyncEngine] = None
async_session_factory: Optional[async_sessionmaker] = None


def _invalidate_on_network_error(context: ExceptionContext) -> None:
    """Drop connections that hit a timeout or socket error instead of returning them to the pool.

    asyncpg raises these as plain Python exceptions, which SQLAlchemy does not recognise as disconnects.
    """
    if isinstance(context.original_exception, (asyncio.TimeoutError, OSError)):
        context.is_disconnect = True


async def init_database():
    """Initialize database connection and create tables."""
    global engine, async_session_factory

    try:
        # Create async engine
        engine = create_async_engine(
            config.database.url,
            pool_size=config.database.min_size,
            max_overflow=config.database.max_size - config.database.min_size,
            pool_pre_ping=True,
            pool_recycle=POOL_RECYCLE_SECONDS,
            pool_timeout=POOL_TIMEOUT_SECONDS,
            connect_args={
                "timeout": CONNECT_TIMEOUT_SECONDS,
                "command_timeout": COMMAND_TIMEOUT_SECONDS,
            },
            echo=False,  # Set to True for SQL debugging
            future=True
        )
        event.listen(engine.sync_engine, "handle_error", _invalidate_on_network_error)

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
        engine = None
        logger.info("Database connections closed")

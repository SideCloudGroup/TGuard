"""Base migration class."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class Migration(ABC):
    """Base migration class."""
    
    def __init__(self):
        self.version = self.get_version()
        self.description = self.get_description()
        self.created_at = datetime.utcnow()
    
    @abstractmethod
    def get_version(self) -> str:
        """Get migration version (e.g., '001', '002')."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get migration description."""
        pass
    
    @abstractmethod
    async def upgrade(self, session: AsyncSession) -> None:
        """Apply migration (upgrade)."""
        pass
    
    @abstractmethod
    async def downgrade(self, session: AsyncSession) -> None:
        """Revert migration (downgrade)."""
        pass


class MigrationManager:
    """Migration manager."""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.migrations: List[Migration] = []
    
    def register_migration(self, migration: Migration):
        """Register a migration."""
        self.migrations.append(migration)
        # Sort by version
        self.migrations.sort(key=lambda m: m.version)
    
    async def create_migrations_table(self, session: AsyncSession):
        """Create migrations table if it doesn't exist."""
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS migrations (
                version VARCHAR(10) PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await session.commit()
    
    async def get_applied_migrations(self, session: AsyncSession) -> List[str]:
        """Get list of applied migration versions."""
        result = await session.execute(text("SELECT version FROM migrations ORDER BY version"))
        return [row[0] for row in result.fetchall()]
    
    async def mark_migration_applied(self, session: AsyncSession, migration: Migration):
        """Mark migration as applied."""
        await session.execute(text("""
            INSERT INTO migrations (version, description, applied_at)
            VALUES (:version, :description, :applied_at)
        """), {
            "version": migration.version,
            "description": migration.description,
            "applied_at": migration.created_at
        })
        await session.commit()
    
    async def mark_migration_removed(self, session: AsyncSession, version: str):
        """Mark migration as removed."""
        await session.execute(text("DELETE FROM migrations WHERE version = :version"), {
            "version": version
        })
        await session.commit()
    
    async def run_migrations(self):
        """Run all pending migrations."""
        async with self.session_factory() as session:
            await self.create_migrations_table(session)
            applied_versions = await self.get_applied_migrations(session)
            
            for migration in self.migrations:
                if migration.version not in applied_versions:
                    logger.info(f"Applying migration {migration.version}: {migration.description}")
                    try:
                        await migration.upgrade(session)
                        await self.mark_migration_applied(session, migration)
                        logger.info(f"Migration {migration.version} applied successfully")
                    except Exception as e:
                        logger.error(f"Failed to apply migration {migration.version}: {e}")
                        raise
                else:
                    logger.debug(f"Migration {migration.version} already applied")
    
    async def rollback_migrations(self, target_version: Optional[str] = None):
        """Rollback migrations to target version."""
        async with self.session_factory() as session:
            applied_versions = await self.get_applied_migrations(session)
            
            # If no target version, rollback all
            if target_version is None:
                versions_to_rollback = applied_versions
            else:
                # Find migrations to rollback
                target_index = None
                for i, migration in enumerate(self.migrations):
                    if migration.version == target_version:
                        target_index = i
                        break
                
                if target_index is None:
                    raise ValueError(f"Target version {target_version} not found")
                
                versions_to_rollback = applied_versions[target_index:]
            
            # Rollback in reverse order
            for version in reversed(versions_to_rollback):
                migration = next((m for m in self.migrations if m.version == version), None)
                if migration:
                    logger.info(f"Rolling back migration {migration.version}: {migration.description}")
                    try:
                        await migration.downgrade(session)
                        await self.mark_migration_removed(session, version)
                        logger.info(f"Migration {migration.version} rolled back successfully")
                    except Exception as e:
                        logger.error(f"Failed to rollback migration {migration.version}: {e}")
                        raise

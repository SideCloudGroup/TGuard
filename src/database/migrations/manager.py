"""Migration manager for TGuard database."""

import logging
from typing import List

from .base import MigrationManager
from .migration_001_initial_schema import InitialSchemaMigration
from .migration_002_add_user_stats import AddUserStatsMigration
from .migration_003_add_request_type import AddRequestTypeMigration

logger = logging.getLogger(__name__)


def get_migration_manager(session_factory):
    """Get migration manager with all migrations registered."""
    manager = MigrationManager(session_factory)
    
    # Register all migrations
    manager.register_migration(InitialSchemaMigration())
    manager.register_migration(AddUserStatsMigration())
    manager.register_migration(AddRequestTypeMigration())
    
    return manager


async def run_migrations(session_factory):
    """Run all pending migrations."""
    manager = get_migration_manager(session_factory)
    await manager.run_migrations()


async def rollback_migrations(session_factory, target_version: str = None):
    """Rollback migrations to target version."""
    manager = get_migration_manager(session_factory)
    await manager.rollback_migrations(target_version)

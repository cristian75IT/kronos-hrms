"""KRONOS - Alembic Migration Environment.

Multi-schema support for microservices architecture.
Each service has its own schema in the same database.
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config, create_async_engine

from alembic import context

# Import all models so Alembic can detect them
from src.core.config import settings

# Import all models from all services
from src.services.auth.models import Base as AuthBase
from src.services.leaves.models import Base as LeavesBase
from src.services.expenses.models import Base as ExpensesBase
from src.services.config.models import Base as ConfigBase
from src.services.notifications.models import Base as NotificationsBase
from src.services.audit.models import Base as AuditBase
from src.services.leaves_wallet.models import Base as LeavesWalletBase
from src.services.expensive_wallet.models import Base as ExpensiveWalletBase

# Use a combined metadata
from src.core.database import Base

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata

# Override sqlalchemy.url from settings
config.set_main_option("sqlalchemy.url", settings.database_url.replace("+asyncpg", ""))

# List of schemas to include
SCHEMAS = ["auth", "leaves", "expenses", "config", "notifications", "audit", "wallet"]


def include_object(object, name, type_, reflected, compare_to):
    """Filter objects to include in migrations."""
    # Include objects from our schemas
    if type_ == "table":
        schema = getattr(object, "schema", None)
        if schema in SCHEMAS or schema is None:
            return True
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_object=include_object,
        version_table_schema="public",
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        include_object=include_object,
        version_table_schema="public",
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode."""
    # Create schemas first
    connectable = create_async_engine(
        settings.database_url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Create schemas if they don't exist
        for schema in SCHEMAS:
            await connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        await connection.commit()
        
        # Run migrations
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

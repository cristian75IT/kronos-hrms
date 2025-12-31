"""KRONOS Backend - Database Configuration."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from src.core.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
)

# Create session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session.
    
    Sets the search_path to the service's schema.
    
    Yields:
        AsyncSession: Database session with correct schema.
    """
    async with async_session_factory() as session:
        # Set schema for this session
        await session.execute(
            text(f"SET search_path TO {settings.database_schema}, public")
        )
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database session.
    
    Use this for non-FastAPI contexts (e.g., Celery tasks).
    
    Yields:
        AsyncSession: Database session with correct schema.
    """
    async with async_session_factory() as session:
        await session.execute(
            text(f"SET search_path TO {settings.database_schema}, public")
        )
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database connection and create tables.
    
    Called on application startup to verify connection and create tables.
    """
    async with engine.begin() as conn:
        # Verify connection
        await conn.execute(text("SELECT 1"))
        
        # Set schema for table creation
        await conn.execute(text(f"SET search_path TO {settings.database_schema}, public"))
        
        
        # Log schema
        result = await conn.execute(text("SHOW search_path"))
        search_path = result.scalar()
        print(f"Database connected. Schema: {settings.database_schema}, search_path: {search_path}")


async def close_db() -> None:
    """Close database connection.
    
    Called on application shutdown.
    """
    await engine.dispose()

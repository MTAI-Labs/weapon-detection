import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import text
from contextlib import asynccontextmanager

from app.core.config import settings

logger = logging.getLogger(__name__)

# Database engine with PostgreSQL optimizations (simplified for API-only)
engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    
    # PostgreSQL specific optimizations
    poolclass=QueuePool if settings.ENVIRONMENT == "production" else NullPool,
    
    # Echo SQL queries in development
    echo=settings.DEBUG,
    
    # Connection arguments for PostgreSQL optimization
    connect_args={
        "server_settings": {
            "application_name": f"{settings.PROJECT_NAME}_api",
        },
        "command_timeout": 60,
    }
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False
)


# Dependency to get database session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Health check for database connectivity
async def check_database_health() -> bool:
    """Check if database is accessible"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# Database initialization
async def init_db() -> None:
    """Initialize database tables"""
    async with engine.begin() as conn:
        # Import all models to ensure they are registered
        from app.models.base import Base
        from app.models import User, Item  # noqa
        
        # Create all tables
        def create_tables(connection):
            Base.metadata.create_all(bind=connection)
        
        await conn.run_sync(create_tables)
        logger.info("Database tables created successfully")


# Database cleanup
async def close_db() -> None:
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")


@asynccontextmanager
async def db_transaction():
    """Context manager for database transactions"""
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                yield session
        except Exception:
            await session.rollback()
            raise
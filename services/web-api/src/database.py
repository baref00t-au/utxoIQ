"""Database configuration and session management."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from typing import AsyncGenerator
import logging
import asyncpg
from google.cloud.sql.connector import Connector

from src.config import settings
from src.monitoring.database_monitor import get_database_monitor

logger = logging.getLogger(__name__)

# Initialize Cloud SQL Connector for Cloud Run
connector = None


async def get_connection() -> asyncpg.Connection:
    """Get database connection using Cloud SQL Connector."""
    global connector
    if connector is None:
        connector = Connector()
    
    conn: asyncpg.Connection = await connector.connect_async(
        settings.cloud_sql_connection_name,
        "asyncpg",
        user=settings.db_user,
        password=settings.db_password,
        db=settings.db_name,
    )
    return conn


# Create async engine with connection pooling
# Use Cloud SQL Connector only if connection name is explicitly set and not empty
if settings.cloud_sql_connection_name and settings.cloud_sql_connection_name.strip():
    logger.info(f"Using Cloud SQL Connector: {settings.cloud_sql_connection_name}")
    engine = create_async_engine(
        "postgresql+asyncpg://",
        async_creator=get_connection,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
        pool_pre_ping=True,
        echo=False,
    )
else:
    logger.info(f"Using direct PostgreSQL connection: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    engine = create_async_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
        pool_pre_ping=True,
        echo=False,
    )

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create declarative base for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database connection pool."""
    try:
        async with engine.begin() as conn:
            # Test connection
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection pool initialized successfully")
        
        # Set up monitoring
        monitor = get_database_monitor()
        monitor.setup_pool_listeners(engine)
        logger.info("Database monitoring configured")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db():
    """Close database connection pool."""
    global connector
    await engine.dispose()
    if connector:
        await connector.close_async()
    logger.info("Database connection pool closed")

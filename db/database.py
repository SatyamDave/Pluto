"""
Database configuration and connection management
"""

import logging
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData
from config import settings

logger = logging.getLogger(__name__)

# Database base
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()

# Database engine
engine = None
AsyncSessionLocal = None

# Redis connection
redis_client = None


async def init_db():
    """Initialize database connections"""
    global engine, AsyncSessionLocal, redis_client
    
    try:
        # Initialize PostgreSQL
        if engine is None:
            # Convert sync URL to async
            async_database_url = settings.DATABASE_URL.replace(
                "postgresql://", "postgresql+asyncpg://"
            )
            engine = create_async_engine(
                async_database_url,
                echo=settings.DEBUG,
                pool_pre_ping=True,
                pool_recycle=300
            )
            
            AsyncSessionLocal = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("PostgreSQL connection established")
        
        # Initialize Redis
        if redis_client is None:
            redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            await redis_client.ping()
            logger.info("Redis connection established")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def get_db() -> AsyncSession:
    """Get database session"""
    if AsyncSessionLocal is None:
        await init_db()
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def get_redis() -> redis.Redis:
    """Get Redis client"""
    if redis_client is None:
        await init_db()
    
    return redis_client


async def close_db():
    """Close database connections"""
    global engine, redis_client
    
    if engine:
        await engine.dispose()
        logger.info("PostgreSQL connection closed")
    
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")

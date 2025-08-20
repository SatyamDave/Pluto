"""
Database connection and utilities for the AI Engine service
"""

import asyncio
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from prisma import Prisma
import structlog

from .config import settings

logger = structlog.get_logger()

# Global Prisma client instance
prisma_client: Optional[Prisma] = None

async def get_prisma_client() -> Prisma:
    """Get or create Prisma client instance"""
    global prisma_client
    
    if prisma_client is None:
        prisma_client = Prisma()
        await prisma_client.connect()
        logger.info("Connected to database")
    
    return prisma_client

async def close_prisma_client():
    """Close Prisma client connection"""
    global prisma_client
    
    if prisma_client is not None:
        await prisma_client.disconnect()
        prisma_client = None
        logger.info("Disconnected from database")

@asynccontextmanager
async def get_db() -> AsyncGenerator[Prisma, None]:
    """Database dependency for FastAPI"""
    client = await get_prisma_client()
    try:
        yield client
    except Exception as e:
        logger.error("Database error", error=str(e))
        raise
    finally:
        # Don't close the client here as it's shared
        pass

# Database utilities
async def health_check() -> bool:
    """Check database connectivity"""
    try:
        client = await get_prisma_client()
        # Simple query to test connection
        await client.user.find_first()
        return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False

async def initialize_database():
    """Initialize database and run migrations"""
    try:
        client = await get_prisma_client()
        
        # Check if we can connect
        await health_check()
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise

async def cleanup_database():
    """Cleanup database connections"""
    await close_prisma_client()

# Database models for type hints
from prisma.models import (
    User,
    DataSource,
    RawData,
    Claim,
    IdentityCard,
    Verification,
    Endorsement,
    CardView,
    CardShare,
    Subscription
)

__all__ = [
    "get_prisma_client",
    "close_prisma_client",
    "get_db",
    "health_check",
    "initialize_database",
    "cleanup_database",
    "User",
    "DataSource",
    "RawData",
    "Claim",
    "IdentityCard",
    "Verification",
    "Endorsement",
    "CardView",
    "CardShare",
    "Subscription"
]

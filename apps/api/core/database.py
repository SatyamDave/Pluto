from __future__ import annotations
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

from prisma import Prisma

from .config import settings


_client: Optional[Prisma] = None


async def get_prisma_client() -> Prisma:
    global _client
    if _client is None:
        _client = Prisma()
        await _client.connect()
    return _client


@asynccontextmanager
async def get_db() -> AsyncGenerator[Prisma, None]:
    client = await get_prisma_client()
    try:
        yield client
    finally:
        pass


async def initialize_database() -> None:
    await get_prisma_client()


async def cleanup_database() -> None:
    global _client
    if _client is not None:
        await _client.disconnect()
        _client = None



from __future__ import annotations
from typing import Optional
from fastapi import Depends, HTTPException, Header
from pydantic import BaseModel

from .database import get_prisma_client


class CurrentUser(BaseModel):
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    username: Optional[str] = None


def create_access_token(data: dict) -> str:
    return "devtoken"


def verify_token(token: str) -> bool:
    return token == "devtoken"


async def get_current_user(x_user_id: Optional[str] = Header(default=None)) -> CurrentUser:
    db = await get_prisma_client()
    user_id = x_user_id or "demo-user"
    user = await db.user.find_unique(where={"id": user_id})
    if not user:
        user = await db.user.create(
            data={
                "id": user_id,
                "email": f"{user_id}@example.com",
                "handle": "demo",
                "name": "Demo User",
            }
        )
    return CurrentUser(id=user.id, email=user.email, name=user.name, username=user.handle)



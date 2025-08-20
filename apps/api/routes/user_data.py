from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO
import json
from datetime import datetime

from ..core.database import get_prisma_client
from ..core.auth import get_current_user

router = APIRouter(prefix="/user_data", tags=["user_data"])

@router.get("/export")
async def export_my_data(current_user = Depends(get_current_user)):
    db = await get_prisma_client()
    user = await db.user.find_unique(where={"id": current_user.id})
    claims = await db.claim.find_many(where={"userId": current_user.id})
    cards = await db.identitycard.find_many(where={"userId": current_user.id}, include={"claims": True})
    data = {
        "user": user,
        "claims": claims,
        "cards": cards,
        "exported_at": datetime.utcnow().isoformat(),
    }
    buf = BytesIO()
    buf.write(json.dumps(data, default=str).encode())
    buf.seek(0)
    return StreamingResponse(buf, media_type='application/zip', headers={'Content-Disposition': 'attachment; filename="export.json"'})

@router.delete("/")
async def delete_my_data(current_user = Depends(get_current_user)):
    db = await get_prisma_client()
    # Tombstone public slugs
    cards = await db.identitycard.find_many(where={"userId": current_user.id})
    for c in cards:
        if c.shareSlug:
            await db.identitycard.update(where={"id": c.id}, data={"shareSlug": f"tombstoned-{c.id[:6]}"})
    # Delete claims/cards/user
    await db.claim.delete_many(where={"userId": current_user.id})
    await db.identitycard.delete_many(where={"userId": current_user.id})
    await db.user.delete(where={"id": current_user.id})
    return {"status": "deleted"}

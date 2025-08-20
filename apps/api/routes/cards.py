from __future__ import annotations
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from hashlib import sha256

from ..core.database import get_db
from ..core.rate_limit import per_ip_allow, per_slug_allow
from ..utils.redaction import redact_text
from ..services.trust_score import TrustScoreService


router = APIRouter(prefix="", tags=["cards"])
trust = TrustScoreService()


class WorkCardCreate(BaseModel):
    headline: str
    location: Optional[str] = None
    availability: Optional[str] = None


@router.post("/cards/work")
async def create_work_card(payload: WorkCardCreate, db = Depends(get_db), current_user_id: Optional[str] = None):  # owner auth to be wired
    user_id = current_user_id or "demo-user"
    card = await db.card.create(
        data={
            "userId": user_id,
            "cardType": "WORK",
            "headline": payload.headline,
            "slug": sha256(f"{user_id}:{payload.headline}".encode()).hexdigest()[:10],
            "location": payload.location,
            "availability": payload.availability,
        }
    )
    return {"id": card.id, "slug": card.slug}


@router.get("/public/cards/{slug}")
async def get_public_card(slug: str, role: Optional[str] = None, request: Request = None, db = Depends(get_db)):
    ip = request.client.host if request and request.client else "0.0.0.0"
    if not per_ip_allow(ip) or not per_slug_allow(slug):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    card = await db.card.find_first(where={"slug": slug, "isPublic": True})
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    score, _ = await trust.compute_trust_score(card.userId)

    await db.publiccardview.create(
        data={
            "cardId": card.id,
            "ipHash": sha256(ip.encode()).hexdigest()[:32],
            "uaHash": sha256((request.headers.get("user-agent", "") if request else "").encode()).hexdigest()[:32],
        }
    )

    top_skills = [s.name for s in await db.skill.find_many(where={"userId": card.userId, "verified": True}, take=3)]
    highlights: list[str] = []
    verification_badges = ["github"] if top_skills else []
    projection = {
        "headline": redact_text(card.headline),
        "role_fit": role,
        "top_skills": top_skills,
        "trust_score": score,
        "availability": redact_text(card.availability or ""),
        "location": redact_text(card.location or ""),
        "highlights": highlights,
        "verification_badges": verification_badges,
        "share_assets": {"qr_url": f"/api/qr/{slug}"},
        "versions": {"current": 1},
    }
    return projection


@router.get("/public/cards/{slug}/meta")
async def get_public_card_meta(slug: str, db = Depends(get_db)):
    card = await db.card.find_first(where={"slug": slug, "isPublic": True})
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return {
        "title": f"{card.headline} — Work Identity Card",
        "description": f"Top skills and verified highlights for {card.headline}",
        "image": f"/api/og/card/{slug}.png",
    }


@router.post("/cards/{card_id}/publish")
async def publish_card(card_id: str, db = Depends(get_db)):
    card = await db.card.update(where={"id": card_id}, data={"isPublic": True})
    return {"id": card.id, "is_public": card.isPublic}


@router.get("/cards/{card_id}")
async def get_card_owner(card_id: str, db = Depends(get_db)):
    card = await db.card.find_unique(where={"id": card_id})
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card



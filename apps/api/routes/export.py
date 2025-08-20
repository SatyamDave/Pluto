from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Dict, Any
from datetime import datetime

from ..core.database import get_prisma_client
from ..services.trust_score import TrustScoreService
from ..utils.redaction import redact_dict

router = APIRouter(prefix="/export", tags=["export"])

trust = TrustScoreService()

async def build_resume_json(card) -> Dict[str, Any]:
    score, breakdown = await trust.compute_trust_score(card.userId)
    verified_claims = [c for c in card.claims if c.isVerified]
    skills = [
        {"name": c.title, "verified": True, "evidenceRefs": c.proofSources or []}
        for c in verified_claims if str(c.type) == "SKILL"
    ]
    experiences = [
        {"role": c.title, "org": None, "startDate": c.createdAt.isoformat(), "highlights": [c.description or ''], "verificationStatus": "verified", "evidenceRefs": c.proofSources or []}
        for c in verified_claims if str(c.type) == "EXPERIENCE"
    ]
    projects = [
        {"name": c.title, "summary": c.description or '', "links": [], "evidenceRefs": c.proofSources or []}
        for c in verified_claims if str(c.type) == "PROJECT"
    ]
    resume = {
        "person": {"name": card.user.name or card.user.username, "headline": card.title, "location": (card.settings or {}).get("location") if card.settings else None},
        "trust": {"score": score, "breakdown": {"verified": 1, "corroborated": 0, "self": 0}},
        "skills": skills,
        "experiences": experiences,
        "education": [],
        "projects": projects,
        "verifications": [],
        "links": {"publicCardUrl": f"/u/{card.shareSlug}", "smartLinks": {}},
        "meta": {"cardId": card.id, "version": "0", "generatedAt": datetime.utcnow().isoformat()},
    }
    return redact_dict(resume)

@router.get("/public/cards/{slug}/resume.json")
async def public_resume_json(slug: str, db = Depends(get_prisma_client)):
    card = await db.identitycard.find_first(where={"shareSlug": slug, "isPublic": True}, include={"claims": True, "user": True})
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    resume = await build_resume_json(card)
    return JSONResponse(content=resume)

@router.post("/cards/{card_id}/pdf")
async def export_pdf(card_id: str, db = Depends(get_prisma_client)):
    card = await db.identitycard.find_unique(where={"id": card_id}, include={"claims": True, "user": True})
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    resume = await build_resume_json(card)
    # lazy import to avoid heavy deps at import time
    from packages.pdf-maker.src.index import renderPdf  # type: ignore
    pdf = await renderPdf(resume)
    return StreamingResponse(iter([pdf]), media_type='application/pdf', headers={'Content-Disposition': f'attachment; filename="{card.shareSlug or card.id}.pdf"'})

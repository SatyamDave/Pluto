from __future__ import annotations
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
import math

from ..core.database import get_prisma_client

WEIGHT_VERIFIED = 1.0
WEIGHT_CORROBORATED = 0.6
WEIGHT_SELF = 0.2

SOURCE_REPUTATION = {
    "GITHUB": 1.0,
    "LINKEDIN": 0.8,
    "EMAIL": 0.7,
    "OTHER": 0.5,
}

RECENCY_HALFLIFE_DAYS = 180

class TrustScoreService:
    def __init__(self) -> None:
        pass

    async def compute_trust_score(self, user_id: str) -> Tuple[int, Dict[str, Any]]:
        db = await get_prisma_client()

        claims = await db.claim.find_many(where={"userId": user_id})

        now = datetime.utcnow()
        recency_weight = lambda dt: self._recency_weight(dt, now)

        total_score = 0.0
        max_score = 0.0
        breakdown_items: List[Dict[str, Any]] = []

        for claim in claims:
            # Determine verification tier
            if claim.isVerified:
                tier_weight = WEIGHT_VERIFIED
                tier = "verified"
            elif claim.confidence and claim.confidence >= 0.7:
                tier_weight = WEIGHT_CORROBORATED
                tier = "corroborated"
            else:
                tier_weight = WEIGHT_SELF
                tier = "self"

            # Source reputation (best-effort from proofSources)
            proof_sources = (claim.proofSources or []) if isinstance(claim.proofSources, list) else []
            source_weight = self._source_reputation(proof_sources)

            # Recency
            created_at = claim.createdAt or now
            r_weight = recency_weight(created_at)

            # Base claim strength from confidence and type
            base_strength = float(claim.confidence or 0.5)
            type_weight = self._type_weight(str(claim.type))

            claim_score = base_strength * tier_weight * source_weight * r_weight * type_weight
            total_score += claim_score
            max_score += 1.0  # normalized per-claim max

            breakdown_items.append({
                "claim_id": claim.id,
                "type": str(claim.type),
                "tier": tier,
                "base": round(base_strength, 3),
                "source": round(source_weight, 3),
                "recency": round(r_weight, 3),
                "type_weight": type_weight,
                "score": round(claim_score, 3),
            })

        normalized = 0 if max_score == 0 else total_score / max_score
        score_0_100 = int(round(min(100, max(0, normalized * 100))))
        breakdown = {
            "user_id": user_id,
            "normalized": round(normalized, 3),
            "items": breakdown_items,
            "weights": {
                "verified": WEIGHT_VERIFIED,
                "corroborated": WEIGHT_CORROBORATED,
                "self": WEIGHT_SELF,
                "recency_halflife_days": RECENCY_HALFLIFE_DAYS,
            },
        }
        return score_0_100, breakdown

    async def snapshot(self, user_id: str) -> Dict[str, Any]:
        score, breakdown = await self.compute_trust_score(user_id)
        db = await get_prisma_client()
        await db.trustscoresnapshot.create(data={
            "userId": user_id,
            "score": score,
            "breakdown": breakdown,
        })
        return {"score": score}

    def _recency_weight(self, created_at: datetime, now: datetime) -> float:
        days = max(0.0, (now - created_at).total_seconds() / 86400.0)
        halflife = float(RECENCY_HALFLIFE_DAYS)
        return 0.5 ** (days / halflife)

    def _source_reputation(self, sources: List[str]) -> float:
        if not sources:
            return SOURCE_REPUTATION["OTHER"]
        best = 0.0
        for src in sources:
            src_upper = src.upper()
            if "GITHUB" in src_upper:
                best = max(best, SOURCE_REPUTATION["GITHUB"])
            elif "LINKEDIN" in src_upper:
                best = max(best, SOURCE_REPUTATION["LINKEDIN"])
            elif "EMAIL" in src_upper or "DOMAIN" in src_upper:
                best = max(best, SOURCE_REPUTATION["EMAIL"])
            else:
                best = max(best, SOURCE_REPUTATION["OTHER"])
        return best or SOURCE_REPUTATION["OTHER"]

    def _type_weight(self, claim_type: str) -> float:
        claim_type = claim_type.upper()
        if "EXPERIENCE" in claim_type or "PROJECT" in claim_type:
            return 1.0
        if "SKILL" in claim_type:
            return 0.9
        if "EDUCATION" in claim_type:
            return 0.8
        if "ACHIEVEMENT" in claim_type:
            return 0.7
        return 0.6

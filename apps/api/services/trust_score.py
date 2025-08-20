from __future__ import annotations
from typing import Dict, Any, Tuple
from datetime import datetime, timedelta

from ..core.database import get_prisma_client


class TrustScoreService:
    async def compute_trust_score(self, user_id: str) -> Tuple[int, Dict[str, Any]]:
        db = await get_prisma_client()

        verified_skills_count = await db.skill.count(where={"userId": user_id, "verified": True})
        verified_experiences_count = await db.experience.count(
            where={"userId": user_id, "verificationStatus": "VERIFIED"}
        )

        # Recent activity: any project updated or created within 90 days
        cutoff = datetime.utcnow() - timedelta(days=90)
        recent_projects = await db.project.count(
            where={"userId": user_id, "OR": [{"createdAt": {"gte": cutoff}}, {"updatedAt": {"gte": cutoff}}]}
        )

        # base
        base = 40
        from_verified_skills = min(30, 3 * int(verified_skills_count))
        from_verified_experiences = min(20, 2 * int(verified_experiences_count))
        recent_activity_factor = 10 if recent_projects > 0 else 0
        from_recent_activity = min(10, round(recent_activity_factor))

        total = max(0, min(100, base + from_verified_skills + from_verified_experiences + from_recent_activity))
        breakdown = {
            "base": base,
            "verified_skills": from_verified_skills,
            "verified_experiences": from_verified_experiences,
            "recent_activity": from_recent_activity,
            "total": total,
        }
        return int(total), breakdown

    async def snapshot(self, user_id: str) -> Dict[str, Any]:
        score, breakdown = await self.compute_trust_score(user_id)
        db = await get_prisma_client()
        await db.trustscoresnapshot.create(
            data={"userId": user_id, "score": int(score), "breakdown": breakdown}
        )
        return {"score": int(score)}

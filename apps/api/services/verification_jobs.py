from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..core.database import get_prisma_client

class VerificationJobsService:
    async def create_job(self, user_id: str, job_type: str, card_id: Optional[str] = None, claim_id: Optional[str] = None, evidence: Optional[Dict[str, Any]] = None):
        db = await get_prisma_client()
        job = await db.verificationjob.create(data={
            "userId": user_id,
            "cardId": card_id,
            "claimId": claim_id,
            "type": job_type,
            "status": "PENDING",
            "evidence": evidence or {},
            "nextActionAt": datetime.utcnow() + timedelta(minutes=5),
        })
        return job

    async def list_jobs(self, user_id: str):
        db = await get_prisma_client()
        jobs = await db.verificationjob.find_many(where={"userId": user_id})
        return jobs

    async def mark_completed(self, job_id: str, success: bool, confidence: float, evidence: Optional[Dict[str, Any]] = None):
        db = await get_prisma_client()
        status = "COMPLETED" if success else "FAILED"
        job = await db.verificationjob.update(
            where={"id": job_id},
            data={"status": status, "confidence": confidence, "evidence": evidence or {}},
        )
        return job

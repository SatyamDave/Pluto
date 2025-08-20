from __future__ import annotations
from typing import Dict, Any, List

from ..core.database import get_prisma_client
from ..core.config import settings
from ..services.claim_processor import ClaimProcessor
from ..services.verification_service import VerificationService
from ..utils.redaction import redact_text, redact_dict  # to be created in ai-engine

REFUSAL = {
    "answer": "I can only answer based on verified facts shown on the card. I cannot share personal contact details or private information.",
    "citations": []
}

class CardChatAgent:
    def __init__(self) -> None:
        self.claim_processor = ClaimProcessor()
        self.verification_service = VerificationService()

    async def answer(self, user_id: str, card_id: str, question: str) -> Dict[str, Any]:
        # Redact input
        question = redact_text(question)

        # Load verified facts only
        db = await get_prisma_client()
        card = await db.identitycard.find_unique(where={"id": card_id}, include={"claims": True})
        if not card:
            return REFUSAL
        claims = [c for c in card.claims if c.isVerified]

        # Refusal policy: if question asks for contact, email, phone, addresses
        lower = question.lower()
        if any(k in lower for k in ["email", "phone", "address", "contact", "linkedin", "github username"]):
            return REFUSAL

        # Simple heuristic: check for skills
        wants_react = "react" in lower
        wants_aws = "aws" in lower

        citations: List[Dict[str, Any]] = []
        if wants_react:
            for c in claims:
                if str(c.type) == "SKILL" and "react" in c.title.lower():
                    citations.append({"type": "SKILL", "title": c.title})
                    break
        if wants_aws:
            for c in claims:
                if str(c.type) == "SKILL" and "aws" in c.title.lower():
                    citations.append({"type": "SKILL", "title": c.title})
                    break

        answer_text = "Based on verified skills, the candidate matches the requested technologies." if citations else "The skills requested are not in verified facts."
        return {"answer": answer_text, "citations": citations}

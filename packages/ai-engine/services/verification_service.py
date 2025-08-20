"""
Verification Service

Handles claim verification, background checks, and credibility analysis.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import structlog

from openai import AsyncOpenAI

from ..core.config import settings
from ..core.database import get_prisma_client, Verification, VerificationType, VerificationStatus, VerificationMethod

logger = structlog.get_logger()

class VerificationService:
    """Verification service for claims and identity cards"""
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.initialized = False
        
    async def initialize(self):
        """Initialize verification service"""
        if self.initialized:
            return
            
        logger.info("Initializing Verification Service")
        
        # Test OpenAI connection
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            logger.info("OpenAI connection successful for verification")
        except Exception as e:
            logger.error("Failed to connect to OpenAI for verification", error=str(e))
            raise
        
        self.initialized = True
        logger.info("Verification Service initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up Verification Service")
    
    async def verify_claim(self, claim_id: str, verification_type: str, 
                          data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Verify a specific claim"""
        try:
            logger.info("Starting claim verification", claim_id=claim_id, verification_type=verification_type)
            
            db = await get_prisma_client()
            
            # Get the claim
            claim = await db.claim.find_unique(where={"id": claim_id})
            if not claim:
                raise ValueError(f"Claim not found: {claim_id}")
            
            # Create verification record
            verification = await db.verification.create(
                data={
                    "userId": claim.userId,
                    "claimId": claim_id,
                    "type": verification_type.upper(),
                    "status": VerificationStatus.IN_PROGRESS,
                    "method": VerificationMethod.AI_AUTO,
                    "data": data or {},
                    "metadata": {
                        "started_at": datetime.utcnow().isoformat(),
                        "verification_type": verification_type
                    }
                }
            )
            
            # Start verification process in background
            asyncio.create_task(self._process_verification(verification.id, claim, verification_type, data))
            
            return {
                "id": verification.id,
                "status": verification.status,
                "confidence": None,
                "result": {}
            }
            
        except Exception as e:
            logger.error("Error starting claim verification", error=str(e), claim_id=claim_id)
            raise
    
    async def get_verification_status(self, verification_id: str) -> Dict[str, Any]:
        """Get verification status"""
        try:
            db = await get_prisma_client()
            
            verification = await db.verification.find_unique(where={"id": verification_id})
            if not verification:
                raise ValueError(f"Verification not found: {verification_id}")
            
            return {
                "id": verification.id,
                "status": verification.status,
                "confidence": verification.confidence,
                "result": verification.result or {},
                "notes": verification.notes,
                "created_at": verification.createdAt.isoformat(),
                "completed_at": verification.completedAt.isoformat() if verification.completedAt else None
            }
            
        except Exception as e:
            logger.error("Error getting verification status", error=str(e), verification_id=verification_id)
            raise
    
    async def verify_identity_card(self, card_id: str, verification_type: str = "BACKGROUND_CHECK") -> Dict[str, Any]:
        """Verify an entire identity card"""
        try:
            logger.info("Starting identity card verification", card_id=card_id)
            
            db = await get_prisma_client()
            
            # Get the card and its claims
            card = await db.identitycard.find_unique(
                where={"id": card_id},
                include={"claims": True}
            )
            
            if not card:
                raise ValueError(f"Identity card not found: {card_id}")
            
            # Create verification record for the card
            verification = await db.verification.create(
                data={
                    "userId": card.userId,
                    "cardId": card_id,
                    "type": verification_type.upper(),
                    "status": VerificationStatus.IN_PROGRESS,
                    "method": VerificationMethod.AI_AUTO,
                    "data": {
                        "claim_count": len(card.claims),
                        "card_type": card.type
                    },
                    "metadata": {
                        "started_at": datetime.utcnow().isoformat(),
                        "verification_type": verification_type
                    }
                }
            )
            
            # Start verification process in background
            asyncio.create_task(self._process_card_verification(verification.id, card, verification_type))
            
            return {
                "id": verification.id,
                "status": verification.status,
                "confidence": None,
                "result": {}
            }
            
        except Exception as e:
            logger.error("Error starting card verification", error=str(e), card_id=card_id)
            raise
    
    async def _process_verification(self, verification_id: str, claim, verification_type: str, 
                                  data: Optional[Dict[str, Any]] = None):
        """Process verification in background"""
        try:
            db = await get_prisma_client()
            
            # Update status to in progress
            await db.verification.update(
                where={"id": verification_id},
                data={"status": VerificationStatus.IN_PROGRESS}
            )
            
            result = {}
            confidence = 0.0
            
            # Perform verification based on type
            if verification_type.upper() == "BACKGROUND_CHECK":
                result, confidence = await self._perform_background_check(claim)
            elif verification_type.upper() == "SKILL_ASSESSMENT":
                result, confidence = await self._perform_skill_assessment(claim)
            elif verification_type.upper() == "EMPLOYMENT_VERIFICATION":
                result, confidence = await self._perform_employment_verification(claim)
            elif verification_type.upper() == "EDUCATION_VERIFICATION":
                result, confidence = await self._perform_education_verification(claim)
            else:
                result, confidence = await self._perform_general_verification(claim)
            
            # Determine final status
            status = VerificationStatus.APPROVED if confidence >= 0.7 else VerificationStatus.REJECTED
            
            # Update verification record
            await db.verification.update(
                where={"id": verification_id},
                data={
                    "status": status,
                    "confidence": confidence,
                    "result": result,
                    "completedAt": datetime.utcnow()
                }
            )
            
            # Update claim if verification was successful
            if status == VerificationStatus.APPROVED:
                await db.claim.update(
                    where={"id": claim.id},
                    data={
                        "isVerified": True,
                        "verifiedAt": datetime.utcnow(),
                        "verificationMethod": VerificationMethod.AI_AUTO
                    }
                )
            
            logger.info("Verification completed", verification_id=verification_id, status=status, confidence=confidence)
            
        except Exception as e:
            logger.error("Error processing verification", error=str(e), verification_id=verification_id)
            
            # Update verification record with error
            try:
                db = await get_prisma_client()
                await db.verification.update(
                    where={"id": verification_id},
                    data={
                        "status": VerificationStatus.REJECTED,
                        "confidence": 0.0,
                        "result": {"error": str(e)},
                        "notes": f"Verification failed: {str(e)}",
                        "completedAt": datetime.utcnow()
                    }
                )
            except Exception as update_error:
                logger.error("Error updating verification record", error=str(update_error))
    
    async def _process_card_verification(self, verification_id: str, card, verification_type: str):
        """Process identity card verification in background"""
        try:
            db = await get_prisma_client()
            
            # Update status to in progress
            await db.verification.update(
                where={"id": verification_id},
                data={"status": VerificationStatus.IN_PROGRESS}
            )
            
            # Verify each claim in the card
            claim_verifications = []
            total_confidence = 0.0
            
            for claim in card.claims:
                # Perform verification for each claim
                result, confidence = await self._perform_general_verification(claim)
                claim_verifications.append({
                    "claim_id": claim.id,
                    "claim_title": claim.title,
                    "confidence": confidence,
                    "result": result
                })
                total_confidence += confidence
            
            # Calculate overall confidence
            overall_confidence = total_confidence / len(card.claims) if card.claims else 0.0
            
            # Determine final status
            status = VerificationStatus.APPROVED if overall_confidence >= 0.7 else VerificationStatus.REJECTED
            
            # Update verification record
            await db.verification.update(
                where={"id": verification_id},
                data={
                    "status": status,
                    "confidence": overall_confidence,
                    "result": {
                        "claim_verifications": claim_verifications,
                        "overall_confidence": overall_confidence,
                        "verified_claims": len([c for c in claim_verifications if c["confidence"] >= 0.7])
                    },
                    "completedAt": datetime.utcnow()
                }
            )
            
            logger.info("Card verification completed", verification_id=verification_id, status=status, confidence=overall_confidence)
            
        except Exception as e:
            logger.error("Error processing card verification", error=str(e), verification_id=verification_id)
            
            # Update verification record with error
            try:
                db = await get_prisma_client()
                await db.verification.update(
                    where={"id": verification_id},
                    data={
                        "status": VerificationStatus.REJECTED,
                        "confidence": 0.0,
                        "result": {"error": str(e)},
                        "notes": f"Card verification failed: {str(e)}",
                        "completedAt": datetime.utcnow()
                    }
                )
            except Exception as update_error:
                logger.error("Error updating card verification record", error=str(update_error))
    
    async def _perform_background_check(self, claim) -> tuple[Dict[str, Any], float]:
        """Perform background check on a claim"""
        try:
            # Use AI to analyze claim credibility
            prompt = f"""
            Perform a background check on this claim. Analyze the credibility, consistency, and verifiability.
            
            Claim: {claim.title}
            Description: {claim.description}
            Content: {json.dumps(claim.content)}
            Proof Sources: {claim.proofSources}
            
            Return a JSON response with:
            - credibility_score (0-1)
            - consistency_check (pass/fail)
            - verification_methods (list of methods used)
            - risk_factors (list of potential issues)
            - recommendations (list of suggestions)
            """
            
            response = await self.openai_client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            confidence = result.get("credibility_score", 0.5)
            
            return result, confidence
            
        except Exception as e:
            logger.error("Error performing background check", error=str(e))
            return {"error": str(e)}, 0.0
    
    async def _perform_skill_assessment(self, claim) -> tuple[Dict[str, Any], float]:
        """Perform skill assessment on a claim"""
        try:
            # Use AI to assess skill level and evidence
            prompt = f"""
            Assess the skill level and evidence for this skill claim.
            
            Skill: {claim.title}
            Description: {claim.description}
            Content: {json.dumps(claim.content)}
            Proof Sources: {claim.proofSources}
            
            Return a JSON response with:
            - skill_level (beginner/intermediate/advanced/expert)
            - evidence_strength (0-1)
            - assessment_methods (list of methods used)
            - skill_validation (pass/fail)
            - confidence_score (0-1)
            """
            
            response = await self.openai_client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            confidence = result.get("confidence_score", 0.5)
            
            return result, confidence
            
        except Exception as e:
            logger.error("Error performing skill assessment", error=str(e))
            return {"error": str(e)}, 0.0
    
    async def _perform_employment_verification(self, claim) -> tuple[Dict[str, Any], float]:
        """Perform employment verification on a claim"""
        try:
            # Use AI to verify employment details
            prompt = f"""
            Verify the employment details in this claim.
            
            Employment: {claim.title}
            Description: {claim.description}
            Content: {json.dumps(claim.content)}
            Proof Sources: {claim.proofSources}
            
            Return a JSON response with:
            - employment_verified (true/false)
            - company_validation (pass/fail)
            - date_consistency (pass/fail)
            - role_verification (pass/fail)
            - confidence_score (0-1)
            """
            
            response = await self.openai_client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            confidence = result.get("confidence_score", 0.5)
            
            return result, confidence
            
        except Exception as e:
            logger.error("Error performing employment verification", error=str(e))
            return {"error": str(e)}, 0.0
    
    async def _perform_education_verification(self, claim) -> tuple[Dict[str, Any], float]:
        """Perform education verification on a claim"""
        try:
            # Use AI to verify education details
            prompt = f"""
            Verify the education details in this claim.
            
            Education: {claim.title}
            Description: {claim.description}
            Content: {json.dumps(claim.content)}
            Proof Sources: {claim.proofSources}
            
            Return a JSON response with:
            - education_verified (true/false)
            - institution_validation (pass/fail)
            - degree_verification (pass/fail)
            - date_consistency (pass/fail)
            - confidence_score (0-1)
            """
            
            response = await self.openai_client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            confidence = result.get("confidence_score", 0.5)
            
            return result, confidence
            
        except Exception as e:
            logger.error("Error performing education verification", error=str(e))
            return {"error": str(e)}, 0.0
    
    async def _perform_general_verification(self, claim) -> tuple[Dict[str, Any], float]:
        """Perform general verification on a claim"""
        try:
            # Use AI to perform general verification
            prompt = f"""
            Perform a general verification on this claim.
            
            Claim: {claim.title}
            Type: {claim.type}
            Description: {claim.description}
            Content: {json.dumps(claim.content)}
            Proof Sources: {claim.proofSources}
            
            Return a JSON response with:
            - claim_valid (true/false)
            - evidence_quality (0-1)
            - consistency_check (pass/fail)
            - verification_methods (list)
            - confidence_score (0-1)
            """
            
            response = await self.openai_client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            confidence = result.get("confidence_score", 0.5)
            
            return result, confidence
            
        except Exception as e:
            logger.error("Error performing general verification", error=str(e))
            return {"error": str(e)}, 0.0

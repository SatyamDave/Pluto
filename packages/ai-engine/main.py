"""
AI Identity Platform - AI Engine Service

This service handles AI processing, claim extraction, and verification
for the modular identity card system.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import structlog

from .core.config import settings
from .core.database import get_db
from .services.claim_processor import ClaimProcessor
from .services.verification_service import VerificationService
from .services.github_processor import GitHubProcessor
from .services.linkedin_processor import LinkedInProcessor

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="AI Identity Platform - AI Engine",
    description="AI processing and verification engine for modular identity cards",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
claim_processor = ClaimProcessor()
verification_service = VerificationService()
github_processor = GitHubProcessor()
linkedin_processor = LinkedInProcessor()

# =============================================================================
# Pydantic Models
# =============================================================================

class ProcessDataSourceRequest(BaseModel):
    """Request model for processing data sources"""
    user_id: str
    data_source_type: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class ProcessDataSourceResponse(BaseModel):
    """Response model for data source processing"""
    success: bool
    claims_generated: int
    claims: List[Dict[str, Any]]
    processing_time: float
    confidence_score: float

class VerifyClaimRequest(BaseModel):
    """Request model for claim verification"""
    claim_id: str
    verification_type: str
    data: Optional[Dict[str, Any]] = None

class VerifyClaimResponse(BaseModel):
    """Response model for claim verification"""
    success: bool
    verification_id: str
    status: str
    confidence: float
    result: Dict[str, Any]

class GenerateCardRequest(BaseModel):
    """Request model for card generation"""
    user_id: str
    card_type: str
    claim_ids: List[str]
    template: str = "default"
    settings: Optional[Dict[str, Any]] = None

class GenerateCardResponse(BaseModel):
    """Response model for card generation"""
    success: bool
    card_id: str
    share_url: str
    qr_code_url: Optional[str] = None
    preview_data: Dict[str, Any]

class RelevanceRequest(BaseModel):
    user_id: str
    card_id: str
    target_role: str

class RelevanceResponse(BaseModel):
    sections: List[Dict[str, Any]]

# =============================================================================
# Health Check
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "ai-engine",
        "version": "1.0.0"
    }

@app.get("/status")
async def status():
    try:
        return {
            "status": "ok",
            "service": "ai-engine",
            "build": os.getenv("GIT_SHA", "dev"),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e)}

# =============================================================================
# Data Source Processing
# =============================================================================

@app.post("/process/github", response_model=ProcessDataSourceResponse)
async def process_github_data(
    request: ProcessDataSourceRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """Process GitHub data and extract claims"""
    try:
        logger.info("Processing GitHub data", user_id=request.user_id)
        
        # Process GitHub data
        claims = await github_processor.process_user_data(
            user_id=request.user_id,
            github_data=request.data,
            metadata=request.metadata
        )
        
        # Store claims in background
        background_tasks.add_task(
            claim_processor.store_claims,
            user_id=request.user_id,
            claims=claims,
            source_type="github"
        )
        
        return ProcessDataSourceResponse(
            success=True,
            claims_generated=len(claims),
            claims=claims,
            processing_time=0.0,  # TODO: Add actual timing
            confidence_score=0.85  # TODO: Calculate actual confidence
        )
        
    except Exception as e:
        logger.error("Error processing GitHub data", error=str(e), user_id=request.user_id)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/linkedin", response_model=ProcessDataSourceResponse)
async def process_linkedin_data(
    request: ProcessDataSourceRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """Process LinkedIn data and extract claims"""
    try:
        logger.info("Processing LinkedIn data", user_id=request.user_id)
        
        # Process LinkedIn data
        claims = await linkedin_processor.process_user_data(
            user_id=request.user_id,
            linkedin_data=request.data,
            metadata=request.metadata
        )
        
        # Store claims in background
        background_tasks.add_task(
            claim_processor.store_claims,
            user_id=request.user_id,
            claims=claims,
            source_type="linkedin"
        )
        
        return ProcessDataSourceResponse(
            success=True,
            claims_generated=len(claims),
            claims=claims,
            processing_time=0.0,
            confidence_score=0.80
        )
        
    except Exception as e:
        logger.error("Error processing LinkedIn data", error=str(e), user_id=request.user_id)
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# Claim Verification
# =============================================================================

@app.post("/verify/claim", response_model=VerifyClaimResponse)
async def verify_claim(
    request: VerifyClaimRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """Verify a specific claim"""
    try:
        logger.info("Verifying claim", claim_id=request.claim_id)
        
        # Start verification process
        verification = await verification_service.verify_claim(
            claim_id=request.claim_id,
            verification_type=request.verification_type,
            data=request.data
        )
        
        return VerifyClaimResponse(
            success=True,
            verification_id=verification["id"],
            status=verification["status"],
            confidence=verification["confidence"],
            result=verification["result"]
        )
        
    except Exception as e:
        logger.error("Error verifying claim", error=str(e), claim_id=request.claim_id)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/verify/status/{verification_id}")
async def get_verification_status(
    verification_id: str,
    db = Depends(get_db)
):
    """Get verification status"""
    try:
        status = await verification_service.get_verification_status(verification_id)
        return status
        
    except Exception as e:
        logger.error("Error getting verification status", error=str(e), verification_id=verification_id)
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# Card Generation
# =============================================================================

@app.post("/generate/card", response_model=GenerateCardResponse)
async def generate_identity_card(
    request: GenerateCardRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """Generate an identity card from claims"""
    try:
        logger.info("Generating identity card", user_id=request.user_id, card_type=request.card_type)
        
        # Generate card
        card_data = await claim_processor.generate_card(
            user_id=request.user_id,
            card_type=request.card_type,
            claim_ids=request.claim_ids,
            template=request.template,
            settings=request.settings
        )
        
        return GenerateCardResponse(
            success=True,
            card_id=card_data["id"],
            share_url=card_data["share_url"],
            qr_code_url=card_data.get("qr_code_url"),
            preview_data=card_data["preview"]
        )
        
    except Exception as e:
        logger.error("Error generating card", error=str(e), user_id=request.user_id)
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# AI Processing
# =============================================================================

@app.post("/ai/extract-skills")
async def extract_skills_from_text(text: str):
    """Extract skills from text using AI"""
    try:
        skills = await claim_processor.extract_skills(text)
        return {"skills": skills}
        
    except Exception as e:
        logger.error("Error extracting skills", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/analyze-credibility")
async def analyze_credibility(claim_data: Dict[str, Any]):
    """Analyze credibility of a claim using AI"""
    try:
        credibility = await claim_processor.analyze_credibility(claim_data)
        return {"credibility_score": credibility}
        
    except Exception as e:
        logger.error("Error analyzing credibility", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/relevance", response_model=RelevanceResponse)
async def compute_relevance_view(req: RelevanceRequest):
    try:
        # Simple heuristic: prioritize sections based on target_role keywords
        role = req.target_role.lower()
        sections: List[Dict[str, Any]] = []
        # Fetch card/claims
        db = await get_db().__anext__()  # quick access to prisma client
        card = await db.identitycard.find_unique(where={"id": req.card_id}, include={"claims": True})
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        skills = [c for c in card.claims if str(c.type) == "SKILL"]
        projects = [c for c in card.claims if str(c.type) == "PROJECT"]
        experiences = [c for c in card.claims if str(c.type) == "EXPERIENCE"]

        def match_score(text: str) -> int:
            t = text.lower()
            score = 0
            for kw in role.split():
                if kw in t:
                    score += 1
            return score

        sections.append({
            "type": "skills",
            "items": sorted([{"title": s.title, "confidence": s.confidence} for s in skills], key=lambda x: -match_score(x["title"]))[:8],
        })
        sections.append({
            "type": "projects",
            "items": sorted([{"title": p.title, "confidence": p.confidence} for p in projects], key=lambda x: -match_score(x["title"]))[:5],
        })
        sections.append({
            "type": "experience",
            "items": sorted([{"title": e.title, "confidence": e.confidence} for e in experiences], key=lambda x: -match_score(x["title"]))[:5],
        })
        return {"sections": sections}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error computing relevance view", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# Analytics
# =============================================================================

@app.get("/analytics/processing-stats")
async def get_processing_stats(db = Depends(get_db)):
    """Get AI processing statistics"""
    try:
        stats = await claim_processor.get_processing_stats()
        return stats
        
    except Exception as e:
        logger.error("Error getting processing stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# Startup and Shutdown Events
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting AI Engine service")
    
    # Initialize AI models and services
    await claim_processor.initialize()
    await verification_service.initialize()
    
    logger.info("AI Engine service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down AI Engine service")
    
    # Cleanup resources
    await claim_processor.cleanup()
    await verification_service.cleanup()
    
    logger.info("AI Engine service shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

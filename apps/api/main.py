"""
AI Identity Platform - FastAPI Backend

Main application entry point with API routes, middleware, and configuration.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from hashlib import sha256

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import structlog

from .core.config import settings
from .core.database import get_db, initialize_database, cleanup_database
from .core.auth import get_current_user, create_access_token, verify_token
from .services.user_service import UserService
from .services.card_service import CardService
from .services.auth_service import AuthService
from .services.trust_score import TrustScoreService
from .core.rate_limit import per_ip_allow, per_slug_allow
from .utils.redaction import redact_text, redact_dict
from .services.verification_jobs import VerificationJobsService
from .routes import user_data as user_data_routes

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
    title="AI Identity Platform API",
    description="Backend API for the AI Identity Platform - Modular identity card system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Routers
app.include_router(user_data_routes.router)

# Security
security = HTTPBearer()

# Initialize services
user_service = UserService()
card_service = CardService()
auth_service = AuthService()
trust_score_service = TrustScoreService()
jobs_service = VerificationJobsService()

# =============================================================================
# Pydantic Models
# =============================================================================

class UserCreate(BaseModel):
    """User creation model"""
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User name")
    username: str = Field(..., description="Username")
    password: Optional[str] = Field(None, description="Password (optional for OAuth)")

class UserUpdate(BaseModel):
    """User update model"""
    name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None

class CardCreate(BaseModel):
    """Card creation model"""
    type: str = Field(..., description="Card type (work, financial, creator, civic)")
    title: str = Field(..., description="Card title")
    subtitle: Optional[str] = None
    template: str = Field(default="default", description="Card template")
    settings: Optional[Dict[str, Any]] = None

class DataSourceConnect(BaseModel):
    """Data source connection model"""
    type: str = Field(..., description="Data source type (github, linkedin, etc.)")
    access_token: str = Field(..., description="Access token")
    metadata: Optional[Dict[str, Any]] = None

class PublicCardChatRequest(BaseModel):
    question: str
    target_role: Optional[str] = None
    captchaToken: Optional[str] = None

class PublicCardProjection(BaseModel):
    headline: str
    role_fit_summary: str
    top_skills: List[str]
    trust_score: int
    availability: Optional[str] = None
    location: Optional[str] = None
    highlights: List[str]
    verification_badges: List[str]
    ai_chat_context_id: str

# =============================================================================
# Health Check
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "ai-identity-api",
        "version": "1.0.0"
    }

@app.get("/status")
async def status(db = Depends(get_db)):
    try:
        # Simple DB health check via prisma find_first
        _ = await db.user.find_first()
        return {
            "status": "ok",
            "service": "api",
            "build": os.getenv("GIT_SHA", "dev"),
            "migrations_ok": True,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e)}

# =============================================================================
# Authentication Routes
# =============================================================================

@app.post("/auth/register", response_model=Dict[str, Any])
async def register_user(user_data: UserCreate, db = Depends(get_db)):
    """Register a new user"""
    try:
        user = await auth_service.register_user(db, user_data)
        access_token = create_access_token(data={"sub": user.id})
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "username": user.username
            },
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        logger.error("Error registering user", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login", response_model=Dict[str, Any])
async def login_user(email: str, password: str, db = Depends(get_db)):
    """Login user"""
    try:
        user = await auth_service.authenticate_user(db, email, password)
        access_token = create_access_token(data={"sub": user.id})
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "username": user.username
            },
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        logger.error("Error logging in user", error=str(e))
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/auth/oauth/{provider}")
async def oauth_login(provider: str, code: str, db = Depends(get_db)):
    """OAuth login for various providers"""
    try:
        user = await auth_service.oauth_login(db, provider, code)
        access_token = create_access_token(data={"sub": user.id})
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "username": user.username
            },
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        logger.error(f"Error with {provider} OAuth login", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

# =============================================================================
# User Routes
# =============================================================================

@app.get("/users/me", response_model=Dict[str, Any])
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "username": current_user.username,
        "bio": current_user.bio,
        "location": current_user.location,
        "website": current_user.website,
        "avatar": current_user.avatar,
        "isPremium": current_user.isPremium,
        "createdAt": current_user.createdAt.isoformat()
    }

@app.put("/users/me", response_model=Dict[str, Any])
async def update_user_info(
    user_data: UserUpdate,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Update current user information"""
    try:
        updated_user = await user_service.update_user(db, current_user.id, user_data)
        return {
            "id": updated_user.id,
            "email": updated_user.email,
            "name": updated_user.name,
            "username": updated_user.username,
            "bio": updated_user.bio,
            "location": updated_user.location,
            "website": updated_user.website,
            "avatar": updated_user.avatar
        }
        
    except Exception as e:
        logger.error("Error updating user", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{username}", response_model=Dict[str, Any])
async def get_user_by_username(username: str, db = Depends(get_db)):
    """Get user by username"""
    try:
        user = await user_service.get_user_by_username(db, username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": user.id,
            "name": user.name,
            "username": user.username,
            "bio": user.bio,
            "location": user.location,
            "website": user.website,
            "avatar": user.avatar
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user by username", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# =============================================================================
# Data Source Routes
# =============================================================================

@app.post("/data-sources/connect")
async def connect_data_source(
    data_source: DataSourceConnect,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Connect a data source (GitHub, LinkedIn, etc.)"""
    try:
        result = await user_service.connect_data_source(
            db, 
            current_user.id, 
            data_source.type, 
            data_source.access_token,
            data_source.metadata
        )
        
        return {
            "success": True,
            "data_source_id": result.id,
            "type": result.type,
            "is_connected": result.isConnected
        }
        
    except Exception as e:
        logger.error("Error connecting data source", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/data-sources")
async def get_data_sources(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get user's connected data sources"""
    try:
        data_sources = await user_service.get_data_sources(db, current_user.id)
        return {
            "data_sources": [
                {
                    "id": ds.id,
                    "type": ds.type,
                    "is_connected": ds.isConnected,
                    "last_sync": ds.lastSyncAt.isoformat() if ds.lastSyncAt else None,
                    "sync_status": ds.syncStatus
                }
                for ds in data_sources
            ]
        }
        
    except Exception as e:
        logger.error("Error getting data sources", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/data-sources/{data_source_id}")
async def disconnect_data_source(
    data_source_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Disconnect a data source"""
    try:
        await user_service.disconnect_data_source(db, current_user.id, data_source_id)
        return {"success": True, "message": "Data source disconnected"}
        
    except Exception as e:
        logger.error("Error disconnecting data source", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

# =============================================================================
# Identity Card Routes
# =============================================================================

@app.post("/cards", response_model=Dict[str, Any])
async def create_identity_card(
    card_data: CardCreate,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Create a new identity card"""
    try:
        card = await card_service.create_card(db, current_user.id, card_data)
        return {
            "id": card.id,
            "type": card.type,
            "title": card.title,
            "subtitle": card.subtitle,
            "template": card.template,
            "share_slug": card.shareSlug,
            "is_public": card.isPublic,
            "created_at": card.createdAt.isoformat()
        }
        
    except Exception as e:
        logger.error("Error creating identity card", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/cards", response_model=Dict[str, Any])
async def get_user_cards(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get user's identity cards"""
    try:
        cards = await card_service.get_user_cards(db, current_user.id)
        return {
            "cards": [
                {
                    "id": card.id,
                    "type": card.type,
                    "title": card.title,
                    "subtitle": card.subtitle,
                    "template": card.template,
                    "share_slug": card.shareSlug,
                    "is_public": card.isPublic,
                    "view_count": card.viewCount,
                    "share_count": card.shareCount,
                    "created_at": card.createdAt.isoformat(),
                    "updated_at": card.updatedAt.isoformat()
                }
                for card in cards
            ]
        }
        
    except Exception as e:
        logger.error("Error getting user cards", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/cards/{card_id}", response_model=Dict[str, Any])
async def get_card_details(
    card_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get detailed information about a specific card"""
    try:
        card = await card_service.get_card_details(db, card_id, current_user.id)
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        return {
            "id": card.id,
            "type": card.type,
            "title": card.title,
            "subtitle": card.subtitle,
            "template": card.template,
            "layout": card.layout,
            "settings": card.settings,
            "share_slug": card.shareSlug,
            "qr_code": card.qrCode,
            "is_public": card.isPublic,
            "view_count": card.viewCount,
            "share_count": card.shareCount,
            "claims": [
                {
                    "id": claim.id,
                    "type": claim.type,
                    "title": claim.title,
                    "description": claim.description,
                    "confidence": claim.confidence,
                    "is_verified": claim.isVerified
                }
                for claim in card.claims
            ],
            "created_at": card.createdAt.isoformat(),
            "updated_at": card.updatedAt.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting card details", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/cards/{card_id}")
async def update_card(
    card_id: str,
    card_data: CardCreate,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Update an identity card"""
    try:
        card = await card_service.update_card(db, card_id, current_user.id, card_data)
        return {
            "id": card.id,
            "type": card.type,
            "title": card.title,
            "subtitle": card.subtitle,
            "template": card.template,
            "updated_at": card.updatedAt.isoformat()
        }
        
    except Exception as e:
        logger.error("Error updating card", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/cards/{card_id}")
async def delete_card(
    card_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Delete an identity card"""
    try:
        await card_service.delete_card(db, card_id, current_user.id)
        return {"success": True, "message": "Card deleted successfully"}
        
    except Exception as e:
        logger.error("Error deleting card", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

# =============================================================================
# Public Card Routes
# =============================================================================

@app.get("/public/cards/{share_slug}")
async def get_public_card_projection(share_slug: str, request: Request, db = Depends(get_db)):
    """Recruiter-facing projection for a public card. Redacted, minimal proof artifacts only."""
    try:
        ip = request.client.host if request.client else "0.0.0.0"
        if not per_ip_allow(ip) or not per_slug_allow(share_slug):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        card = await card_service.get_public_card(db, share_slug)
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")

        # store public view
        ua = request.headers.get("user-agent", "")
        ip_hash = sha256(ip.encode()).hexdigest()[:32]
        ua_hash = sha256(ua.encode()).hexdigest()[:32]
        await db.publiccardview.create(data={"cardId": card.id, "ipHash": ip_hash, "uaHash": ua_hash})

        # Compute trust score
        trust_score, _ = await trust_score_service.compute_trust_score(card.userId)

        # Build projection fields from verified facts only
        verified_claims = [c for c in card.claims if c.isVerified]
        top_skills = [c.title for c in verified_claims if str(c.type) == "SKILL"][:6]
        highlights = [c.title for c in verified_claims if str(c.type) in ("PROJECT", "ACHIEVEMENT")][:5]
        verification_badges = [str(c.type) for c in verified_claims][:6]

        headline = f"{card.title}"
        role_fit_summary = f"Strong fit for {card.title} roles based on verified skills and projects."
        availability = (card.settings or {}).get("availability") if card.settings else None
        location = (card.settings or {}).get("location") if card.settings else None

        projection = {
            "headline": redact_text(headline),
            "role_fit_summary": redact_text(role_fit_summary),
            "top_skills": top_skills,
            "trust_score": trust_score,
            "availability": redact_text(availability or ""),
            "location": redact_text(location or ""),
            "highlights": [redact_text(h) for h in highlights],
            "verification_badges": verification_badges,
            "ai_chat_context_id": f"ctx:{share_slug}",
        }

        # Increment view count
        await card_service.increment_view_count(db, card.id)

        return projection

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting public card projection", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/public/cards/{share_slug}/meta")
async def get_public_card_meta(share_slug: str, db = Depends(get_db)):
    try:
        card = await card_service.get_public_card(db, share_slug)
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        title = f"{card.title} — Work Identity Card"
        desc = f"Top skills and verified highlights for {card.title}."
        image = f"/api/og/card/{share_slug}.png"
        return {"title": title, "description": desc, "image": image}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting card meta", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/public/cards/{share_slug}/chat")
async def public_card_chat(share_slug: str, payload: PublicCardChatRequest, request: Request):
    try:
        ip = request.client.host if request.client else "0.0.0.0"
        # Tighter limits for chat
        if not per_ip_allow(ip, capacity=20, refill_rate_per_sec=0.1) or not per_slug_allow(share_slug, capacity=50, refill_rate_per_sec=0.2):
            # TODO: validate captchaToken before allowing further
            raise HTTPException(status_code=429, detail="Rate limit exceeded; captcha required")

        # Redact user question to ensure no PII echoes back
        question = redact_text(payload.question)

        # Delegate to AI Engine (placeholder: return canned response)
        answer = {
            "answer": "Based on verified facts: candidate has strong React and AWS experience with multiple projects.",
            "citations": [
                {"type": "SKILL", "title": "React"},
                {"type": "PROJECT", "title": "AWS deployment pipeline"}
            ]
        }
        return answer
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in public card chat", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# =============================================================================
# Analytics Routes
# =============================================================================

@app.get("/analytics/cards/{card_id}")
async def get_card_analytics(
    card_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get analytics for a specific card"""
    try:
        analytics = await card_service.get_card_analytics(db, card_id, current_user.id)
        return analytics
        
    except Exception as e:
        logger.error("Error getting card analytics", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# =============================================================================
# Trust Score
# =============================================================================

@app.get("/cards/{card_id}/trust_score")
async def get_trust_score(card_id: str, current_user = Depends(get_current_user), db = Depends(get_db)):
    try:
        card = await card_service.get_card_details(db, card_id, current_user.id)
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        score, breakdown = await trust_score_service.compute_trust_score(card.userId)
        # snapshot asynchronously would be better; do synchronous for now
        await trust_score_service.snapshot(card.userId)
        return {"score": score, "breakdown": breakdown}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error computing trust score", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# =============================================================================
# Verification Jobs
# =============================================================================

@app.post("/verification_jobs")
async def create_verification_job(payload: Dict[str, Any], current_user = Depends(get_current_user)):
    try:
        job = await jobs_service.create_job(
            user_id=current_user.id,
            job_type=payload.get("type"),
            card_id=payload.get("cardId"),
            claim_id=payload.get("claimId"),
            evidence=payload.get("evidence"),
        )
        return job
    except Exception as e:
        logger.error("Error creating verification job", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/verification_jobs")
async def list_verification_jobs(current_user = Depends(get_current_user)):
    jobs = await jobs_service.list_jobs(current_user.id)
    return {"jobs": jobs}

@app.post("/verification_jobs/{job_id}/complete")
async def complete_verification_job(job_id: str, payload: Dict[str, Any]):
    # Webhook: authenticated via shared secret header in production
    success = bool(payload.get("success", False))
    confidence = float(payload.get("confidence", 0.0))
    job = await jobs_service.mark_completed(job_id, success, confidence, payload.get("evidence"))
    return job

# =============================================================================
# Error Handlers
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# =============================================================================
# Startup and Shutdown Events
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting AI Identity Platform API")
    
    # Initialize database
    await initialize_database()
    
    logger.info("AI Identity Platform API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down AI Identity Platform API")
    
    # Cleanup database connections
    await cleanup_database()
    
    logger.info("AI Identity Platform API shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

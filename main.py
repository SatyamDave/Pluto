"""
Jarvis Phone - AI Personal Assistant
Main FastAPI application entry point
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from config import settings
from db.database import init_db
from api.routes import sms, voice, reminders, email, calendar, notes, health, outbound_calls, proactive, communication, oauth, audit, ai_management, telephony, slack, onboarding, digest
from ai_orchestrator import AIOrchestrator
from config import is_proactive_mode_enabled, is_daily_digest_enabled, settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Jarvis Phone AI Assistant...")
    await init_db()
    logger.info("Database initialized successfully")
    
    # Initialize AI orchestrator for proactive automation
    if is_proactive_mode_enabled():
        logger.info("Initializing proactive automation mode...")
        ai_orchestrator = AIOrchestrator()
        
        # Start proactive automation background task
        asyncio.create_task(run_proactive_automation(ai_orchestrator))
        logger.info("Proactive automation mode initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Jarvis Phone AI Assistant...")


# Create FastAPI app
app = FastAPI(
    title="Jarvis Phone - AI Personal Assistant",
    description="Phone-number-based AI assistant accessible via SMS and voice calls",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with logging"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include API routes
app.include_router(sms.router, prefix="/api/v1/sms", tags=["SMS"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice"])
app.include_router(reminders.router, prefix="/api/v1/reminders", tags=["Reminders"])
app.include_router(email.router, prefix="/api/v1/email", tags=["Email"])
app.include_router(calendar.router, prefix="/api/v1/calendar", tags=["Calendar"])
app.include_router(notes.router, prefix="/api/v1/notes", tags=["Notes"])
app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])
app.include_router(outbound_calls.router, prefix="/api/v1/outbound-calls", tags=["Outbound Calls"])
app.include_router(proactive.router, prefix="/api/v1/proactive", tags=["Proactive Automation"])
app.include_router(communication.router, prefix="/api/v1/communication", tags=["Communication Hub"])
app.include_router(oauth.router, prefix="/api/v1/oauth", tags=["OAuth Integration"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["Audit & Analytics"])
app.include_router(ai_management.router, prefix="/api/v1", tags=["AI Management"])
app.include_router(telephony.router, tags=["Telephony"])
app.include_router(slack.router, prefix="/api/v1/slack", tags=["Slack Integration"])
app.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["Onboarding"])
app.include_router(digest.router, prefix="/api/v1/digest", tags=["Digest Service"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Jarvis Phone - AI Personal Assistant",
        "version": "1.0.0",
        "status": "running",
        "description": "Your AI assistant accessible via phone number"
    }


async def run_proactive_automation(ai_orchestrator: AIOrchestrator):
    """Background task for running proactive automation"""
    try:
        while True:
            try:
                await ai_orchestrator.run_proactive_automation()
                
                # Wait for next cycle
                await asyncio.sleep(settings.PROACTIVE_CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in proactive automation cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
                
    except asyncio.CancelledError:
        logger.info("Proactive automation task cancelled")
    except Exception as e:
        logger.error(f"Fatal error in proactive automation: {e}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

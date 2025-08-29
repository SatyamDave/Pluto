"""
Digest API routes for Jarvis Phone AI Assistant
Handles morning and evening digest generation and delivery
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from services.digest_service import digest_service
from utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


class DigestRequest(BaseModel):
    """Digest request model"""
    user_id: int
    digest_type: str = "morning"  # morning, evening, or both


class DigestResponse(BaseModel):
    """Digest response model"""
    success: bool
    digest_type: str
    sent_to: str
    content_length: int
    message: str


@router.post("/send", response_model=DigestResponse)
async def send_digest(
    request: DigestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Send a digest to a user"""
    try:
        if request.digest_type not in ["morning", "evening"]:
            raise HTTPException(status_code=400, detail="Invalid digest type. Use 'morning' or 'evening'")
        
        # Send digest in background
        background_tasks.add_task(
            digest_service.send_manual_digest,
            request.user_id,
            request.digest_type
        )
        
        return DigestResponse(
            success=True,
            digest_type=request.digest_type,
            sent_to="Processing...",
            content_length=0,
            message=f"{request.digest_type.title()} digest queued for delivery"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending digest: {e}")
        raise HTTPException(status_code=500, detail="Failed to send digest")


@router.post("/send-both")
async def send_both_digests(
    request: DigestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Send both morning and evening digests to a user"""
    try:
        # Send both digests in background
        background_tasks.add_task(
            digest_service.send_manual_digest,
            request.user_id,
            "morning"
        )
        
        background_tasks.add_task(
            digest_service.send_manual_digest,
            request.user_id,
            "evening"
        )
        
        return {
            "success": True,
            "message": "Both digests queued for delivery",
            "morning": "queued",
            "evening": "queued"
        }
        
    except Exception as e:
        logger.error(f"Error sending both digests: {e}")
        raise HTTPException(status_code=500, detail="Failed to send digests")


@router.get("/status")
async def get_digest_status():
    """Get digest service status"""
    try:
        return {
            "status": "healthy",
            "scheduler_running": digest_service.scheduler.running,
            "next_morning_digest": "7:00 AM UTC",
            "next_evening_digest": "7:00 PM UTC",
            "message": "Digest service is active"
        }
        
    except Exception as e:
        logger.error(f"Error getting digest status: {e}")
        return {
            "status": "error",
            "message": f"Error: {str(e)}"
        }


@router.post("/start")
async def start_digest_service():
    """Start the digest scheduler"""
    try:
        digest_service.start()
        return {
            "success": True,
            "message": "Digest scheduler started",
            "status": "running"
        }
        
    except Exception as e:
        logger.error(f"Error starting digest service: {e}")
        raise HTTPException(status_code=500, detail="Failed to start digest service")


@router.post("/stop")
async def stop_digest_service():
    """Stop the digest scheduler"""
    try:
        digest_service.stop()
        return {
            "success": True,
            "message": "Digest scheduler stopped",
            "status": "stopped"
        }
        
    except Exception as e:
        logger.error(f"Error stopping digest service: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop digest service")


@router.get("/test/{user_id}")
async def test_digest_generation(
    user_id: int,
    digest_type: str = "morning",
    db: AsyncSession = Depends(get_db)
):
    """Test digest generation for a user (without sending)"""
    try:
        if digest_type == "morning":
            content = await digest_service._generate_morning_digest(user_id)
        elif digest_type == "evening":
            content = await digest_service._generate_evening_digest(user_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid digest type")
        
        return {
            "success": True,
            "digest_type": digest_type,
            "content": content,
            "content_length": len(content),
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing digest generation: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate test digest")

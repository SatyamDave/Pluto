"""
Proactive Automation Routes for Jarvis Phone AI Assistant
Handles API endpoints for proactive automation features
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ai_orchestrator import AIOrchestrator
from services.digest_service import DigestService
from config import is_proactive_mode_enabled, is_daily_digest_enabled

logger = logging.getLogger(__name__)
router = APIRouter()


class ProactiveTaskRequest(BaseModel):
    """Request model for running proactive tasks"""
    user_id: int
    task_type: str  # "email_check", "calendar_check", "digest", "all"


class ProactiveTaskResponse(BaseModel):
    """Response model for proactive task execution"""
    task_type: str
    status: str
    message: str
    details: Dict[str, Any] = None


@router.post("/run", response_model=ProactiveTaskResponse)
async def run_proactive_tasks(request: ProactiveTaskRequest):
    """Run proactive automation tasks for a specific user"""
    try:
        if not is_proactive_mode_enabled():
            raise HTTPException(status_code=400, detail="Proactive automation mode is not enabled")
        
        ai_orchestrator = AIOrchestrator()
        
        # Get user phone number (this would come from user context)
        # For now, we'll use a placeholder
        user_phone = "+1234567890"  # This should come from user context
        
        if request.task_type == "all":
            # Run all proactive tasks
            await ai_orchestrator._run_user_proactive_tasks(request.user_id, user_phone)
            
            return ProactiveTaskResponse(
                task_type="all",
                status="completed",
                message="All proactive tasks completed successfully",
                details={"tasks_run": ["email_check", "calendar_check", "digest"]}
            )
        
        elif request.task_type == "email_check":
            # Check for low-priority emails and auto-reply
            await ai_orchestrator._handle_low_priority_emails(request.user_id)
            
            return ProactiveTaskResponse(
                task_type="email_check",
                status="completed",
                message="Email check completed successfully",
                details={"emails_processed": "auto-replies sent for low-priority emails"}
            )
        
        elif request.task_type == "calendar_check":
            # Check for calendar conflicts
            await ai_orchestrator._handle_calendar_conflicts(request.user_id, user_phone)
            
            return ProactiveTaskResponse(
                task_type="calendar_check",
                status="completed",
                message="Calendar check completed successfully",
                details={"conflicts_checked": "calendar conflicts analyzed"}
            )
        
        elif request.task_type == "digest":
            # Send immediate digest
            if not is_daily_digest_enabled():
                raise HTTPException(status_code=400, detail="Daily digest is not enabled")
            
            digest_service = DigestService()
            success = await digest_service.send_immediate_digest(request.user_id, user_phone)
            
            if success:
                return ProactiveTaskResponse(
                    task_type="digest",
                    status="completed",
                    message="Daily digest sent successfully",
                    details={"digest_sent": True}
                )
            else:
                return ProactiveTaskResponse(
                    task_type="digest",
                    status="failed",
                    message="Failed to send daily digest",
                    details={"digest_sent": False}
                )
        
        else:
            raise HTTPException(status_code=400, detail=f"Invalid task type: {request.task_type}")
        
    except Exception as e:
        logger.error(f"Error running proactive tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_proactive_status():
    """Get status of proactive automation mode"""
    try:
        return {
            "proactive_mode_enabled": is_proactive_mode_enabled(),
            "daily_digest_enabled": is_daily_digest_enabled(),
            "features": {
                "email_auto_reply": True,  # This would come from settings
                "calendar_conflict_detection": True,  # This would come from settings
                "daily_digest": is_daily_digest_enabled()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting proactive status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/digest/statistics/{user_id}")
async def get_digest_statistics(user_id: int):
    """Get digest statistics for a specific user"""
    try:
        if not is_daily_digest_enabled():
            raise HTTPException(status_code=400, detail="Daily digest is not enabled")
        
        digest_service = DigestService()
        stats = await digest_service.get_digest_statistics(user_id)
        
        return {
            "user_id": user_id,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting digest statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/digest/schedule/{user_id}")
async def schedule_daily_digest(user_id: int):
    """Schedule daily digest for a specific user"""
    try:
        if not is_daily_digest_enabled():
            raise HTTPException(status_code=400, detail="Daily digest is not enabled")
        
        # Get user phone number (this would come from user context)
        user_phone = "+1234567890"  # This should come from user context
        
        digest_service = DigestService()
        success = await digest_service.schedule_daily_digest(user_id, user_phone)
        
        if success:
            return {"message": "Daily digest scheduled successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to schedule daily digest")
        
    except Exception as e:
        logger.error(f"Error scheduling daily digest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/digest/send/{user_id}")
async def send_immediate_digest(user_id: int):
    """Send immediate digest for a specific user"""
    try:
        if not is_daily_digest_enabled():
            raise HTTPException(status_code=400, detail="Daily digest is not enabled")
        
        # Get user phone number (this would come from user context)
        user_phone = "+1234567890"  # This should come from user context
        
        digest_service = DigestService()
        success = await digest_service.send_immediate_digest(user_id, user_phone)
        
        if success:
            return {"message": "Digest sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send digest")
        
    except Exception as e:
        logger.error(f"Error sending immediate digest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/automation/cycle")
async def get_automation_cycle_info():
    """Get information about the proactive automation cycle"""
    try:
        if not is_proactive_mode_enabled():
            raise HTTPException(status_code=400, detail="Proactive automation mode is not enabled")
        
        from config import settings
        
        return {
            "cycle_interval_seconds": settings.PROACTIVE_CHECK_INTERVAL,
            "cycle_interval_minutes": settings.PROACTIVE_CHECK_INTERVAL / 60,
            "features_enabled": {
                "email_auto_reply": settings.EMAIL_AUTO_REPLY_ENABLED,
                "calendar_conflict_detection": settings.CALENDAR_CONFLICT_DETECTION,
                "daily_digest": is_daily_digest_enabled()
            },
            "next_cycle_in": "Calculated based on last run time"
        }
        
    except Exception as e:
        logger.error(f"Error getting automation cycle info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

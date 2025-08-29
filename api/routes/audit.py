"""
Audit Routes for Jarvis Phone AI Assistant
Handles API endpoints for audit logging and daily summaries
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from datetime import date

from services.audit_service import AuditService, ActionType, ActionStatus

logger = logging.getLogger(__name__)
router = APIRouter()


class DailySummaryResponse(BaseModel):
    """Response model for daily summary"""
    user_id: int
    date: str
    total_actions: int
    successful_actions: int
    failed_actions: int
    action_breakdown: Dict[str, int]
    cost_estimate: float
    time_saved_minutes: int
    summary_text: str


class UserAnalyticsResponse(BaseModel):
    """Response model for user analytics"""
    period_days: int
    total_actions: int
    successful_actions: int
    failed_actions: int
    success_rate: float
    action_distribution: Dict[str, int]
    cost_analysis: Dict[str, float]
    time_saved_analysis: Dict[str, float]
    daily_averages: Dict[str, float]


@router.get("/summary/{user_id}", response_model=DailySummaryResponse)
async def get_daily_summary(
    user_id: int, 
    target_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")
):
    """Get daily summary of AI actions for a user"""
    try:
        audit_service = AuditService()
        
        # Parse date if provided
        parsed_date = None
        if target_date:
            try:
                parsed_date = date.fromisoformat(target_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Generate summary
        summary = await audit_service.generate_daily_summary(user_id, parsed_date)
        
        return DailySummaryResponse(
            user_id=summary.user_id,
            date=summary.date.isoformat(),
            total_actions=summary.total_actions,
            successful_actions=summary.successful_actions,
            failed_actions=summary.failed_actions,
            action_breakdown=summary.action_breakdown,
            cost_estimate=summary.cost_estimate,
            time_saved_minutes=summary.time_saved_minutes,
            summary_text=summary.summary_text
        )
        
    except Exception as e:
        logger.error(f"Error getting daily summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summary/{user_id}/send-sms")
async def send_daily_summary_sms(
    user_id: int, 
    user_phone: str,
    target_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")
):
    """Send daily summary via SMS"""
    try:
        audit_service = AuditService()
        
        # Parse date if provided
        parsed_date = None
        if target_date:
            try:
                parsed_date = date.fromisoformat(target_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Send summary SMS
        success = await audit_service.send_daily_summary_sms(user_id, user_phone, parsed_date)
        
        if success:
            return {
                "message": "Daily summary SMS sent successfully",
                "user_id": user_id,
                "date": target_date or "today"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send daily summary SMS")
        
    except Exception as e:
        logger.error(f"Error sending daily summary SMS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/{user_id}", response_model=UserAnalyticsResponse)
async def get_user_analytics(
    user_id: int, 
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365)
):
    """Get analytics for a user over a period of time"""
    try:
        audit_service = AuditService()
        
        # Get analytics
        analytics = await audit_service.get_user_analytics(user_id, days)
        
        if "error" in analytics:
            raise HTTPException(status_code=500, detail=analytics["error"])
        
        return UserAnalyticsResponse(**analytics)
        
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actions/{user_id}")
async def get_user_actions(
    user_id: int,
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    action_types: Optional[str] = Query(None, description="Comma-separated action types"),
    status: Optional[str] = Query(None, description="Action status filter")
):
    """Get audit log entries for a specific user"""
    try:
        audit_service = AuditService()
        
        # Parse dates if provided
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            try:
                parsed_start_date = date.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start date format. Use YYYY-MM-DD")
        
        if end_date:
            try:
                parsed_end_date = date.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end date format. Use YYYY-MM-DD")
        
        # Parse action types if provided
        parsed_action_types = None
        if action_types:
            try:
                parsed_action_types = [ActionType(action_type.strip()) for action_type in action_types.split(",")]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid action type: {e}")
        
        # Parse status if provided
        parsed_status = None
        if status:
            try:
                parsed_status = ActionStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        # Get actions
        actions = await audit_service.get_user_actions(
            user_id=user_id,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            action_types=parsed_action_types
        )
        
        # Filter by status if provided
        if parsed_status:
            actions = [action for action in actions if action.status == parsed_status]
        
        # Format response
        formatted_actions = []
        for action in actions:
            formatted_actions.append({
                "id": action.id,
                "action_type": action.action_type.value,
                "action_description": action.action_description,
                "status": action.status.value,
                "timestamp": action.timestamp.isoformat() if action.timestamp else None,
                "cost_estimate": action.cost_estimate,
                "ai_model_used": action.ai_model_used,
                "execution_time_ms": action.execution_time_ms,
                "details": action.details
            })
        
        return {
            "user_id": user_id,
            "total_actions": len(formatted_actions),
            "actions": formatted_actions,
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "action_types": action_types,
                "status": status
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actions/types")
async def get_action_types():
    """Get all available action types"""
    try:
        return {
            "action_types": [
                {
                    "id": action_type.value,
                    "name": action_type.value.replace("_", " ").title(),
                    "category": _get_action_category(action_type)
                }
                for action_type in ActionType
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting action types: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actions/statuses")
async def get_action_statuses():
    """Get all available action statuses"""
    try:
        return {
            "action_statuses": [
                {
                    "id": status.value,
                    "name": status.value.replace("_", " ").title(),
                    "description": _get_status_description(status)
                }
                for status in ActionStatus
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting action statuses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/log")
async def log_action(
    user_id: int,
    action_type: str,
    action_description: str,
    status: str = "success",
    details: Optional[Dict[str, Any]] = None,
    cost_estimate: Optional[float] = None,
    ai_model_used: Optional[str] = None,
    execution_time_ms: Optional[int] = None
):
    """Log an AI action for audit purposes"""
    try:
        audit_service = AuditService()
        
        # Validate action type
        try:
            parsed_action_type = ActionType(action_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid action type: {action_type}")
        
        # Validate status
        try:
            parsed_status = ActionStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        # Log action
        success = await audit_service.log_action(
            user_id=user_id,
            action_type=parsed_action_type,
            action_description=action_description,
            status=parsed_status,
            details=details,
            cost_estimate=cost_estimate,
            ai_model_used=ai_model_used,
            execution_time_ms=execution_time_ms
        )
        
        if success:
            return {
                "message": "Action logged successfully",
                "user_id": user_id,
                "action_type": action_type,
                "status": status
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to log action")
        
    except Exception as e:
        logger.error(f"Error logging action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup")
async def cleanup_old_logs(days_to_keep: int = Query(90, description="Number of days to keep", ge=1, le=1000)):
    """Clean up old audit logs"""
    try:
        audit_service = AuditService()
        
        # Clean up old logs
        await audit_service.cleanup_old_logs(days_to_keep)
        
        return {
            "message": f"Old audit logs cleaned up successfully",
            "days_to_keep": days_to_keep,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_action_category(action_type: ActionType) -> str:
    """Get category for an action type"""
    if action_type.value.startswith("sms") or action_type.value.startswith("email"):
        return "Communication"
    elif action_type.value.startswith("reminder") or action_type.value.startswith("wakeup"):
        return "Reminders & Calendar"
    elif action_type.value.startswith("outbound_call"):
        return "Outbound Calls"
    elif action_type.value.startswith("inbox") or action_type.value.startswith("low_priority"):
        return "Proactive Automation"
    elif action_type.value.startswith("note") or action_type.value.startswith("task"):
        return "Notes & Tasks"
    else:
        return "Other"


def _get_status_description(status: ActionStatus) -> str:
    """Get description for a status"""
    descriptions = {
        ActionStatus.SUCCESS: "Action completed successfully",
        ActionStatus.FAILED: "Action failed to complete",
        ActionStatus.PENDING: "Action is waiting to be processed",
        ActionStatus.CANCELLED: "Action was cancelled before completion"
    }
    return descriptions.get(status, "Unknown status")

"""
Reminders API routes for Jarvis Phone AI Assistant
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from reminders.reminder_service import ReminderService
from db.models import Reminder

logger = logging.getLogger(__name__)
router = APIRouter()


class ReminderCreate(BaseModel):
    """Create reminder request model"""
    title: str
    description: Optional[str] = None
    reminder_time: str
    reminder_type: str = "sms"


class ReminderUpdate(BaseModel):
    """Update reminder request model"""
    title: Optional[str] = None
    description: Optional[str] = None
    reminder_time: Optional[str] = None
    reminder_type: Optional[str] = None


class ReminderResponse(BaseModel):
    """Reminder response model"""
    id: int
    title: str
    description: Optional[str]
    reminder_time: str
    reminder_type: str
    is_completed: bool
    status: str
    created_at: str


@router.post("/", response_model=ReminderResponse)
async def create_reminder(
    reminder_data: ReminderCreate,
    user_id: int,  # In production, get from auth token
    db: AsyncSession = Depends(get_db)
):
    """Create a new reminder"""
    try:
        service = ReminderService()
        reminder = await service.create_reminder(
            user_id=user_id,
            title=reminder_data.title,
            reminder_time=reminder_data.reminder_time,
            description=reminder_data.description,
            reminder_type=reminder_data.reminder_type
        )
        
        return ReminderResponse(
            id=reminder.id,
            title=reminder.title,
            description=reminder.description,
            reminder_time=reminder.reminder_time.isoformat(),
            reminder_type=reminder.reminder_type,
            is_completed=reminder.is_completed,
            status=reminder.status,
            created_at=reminder.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error creating reminder: {e}")
        raise HTTPException(status_code=500, detail="Failed to create reminder")


@router.get("/", response_model=List[ReminderResponse])
async def get_user_reminders(
    user_id: int,  # In production, get from auth token
    include_completed: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Get all reminders for a user"""
    try:
        service = ReminderService()
        reminders = await service.get_user_reminders(
            user_id=user_id,
            include_completed=include_completed
        )
        
        return [
            ReminderResponse(
                id=reminder.id,
                title=reminder.title,
                description=reminder.description,
                reminder_time=reminder.reminder_time.isoformat(),
                reminder_type=reminder.reminder_type,
                is_completed=reminder.is_completed,
                status=reminder.status,
                created_at=reminder.created_at.isoformat()
            )
            for reminder in reminders
        ]
        
    except Exception as e:
        logger.error(f"Error getting reminders: {e}")
        raise HTTPException(status_code=500, detail="Failed to get reminders")


@router.get("/{reminder_id}", response_model=ReminderResponse)
async def get_reminder(
    reminder_id: int,
    user_id: int,  # In production, get from auth token
    db: AsyncSession = Depends(get_db)
):
    """Get a specific reminder"""
    try:
        # Get reminder from database
        query = "SELECT * FROM reminders WHERE id = :reminder_id AND user_id = :user_id"
        result = await db.execute(query, {
            "reminder_id": reminder_id,
            "user_id": user_id
        })
        
        reminder = result.fetchone()
        
        if not reminder:
            raise HTTPException(status_code=404, detail="Reminder not found")
        
        return ReminderResponse(
            id=reminder.id,
            title=reminder.title,
            description=reminder.description,
            reminder_time=reminder.reminder_time.isoformat(),
            reminder_type=reminder.reminder_type,
            is_completed=reminder.is_completed,
            status=reminder.status,
            created_at=reminder.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting reminder: {e}")
        raise HTTPException(status_code=500, detail="Failed to get reminder")


@router.put("/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: int,
    reminder_data: ReminderUpdate,
    user_id: int,  # In production, get from auth token
    db: AsyncSession = Depends(get_db)
):
    """Update a reminder"""
    try:
        service = ReminderService()
        
        # Prepare update data
        update_data = {}
        if reminder_data.title is not None:
            update_data['title'] = reminder_data.title
        if reminder_data.description is not None:
            update_data['description'] = reminder_data.description
        if reminder_data.reminder_time is not None:
            update_data['reminder_time'] = reminder_data.reminder_time
        if reminder_data.reminder_type is not None:
            update_data['reminder_type'] = reminder_data.reminder_type
        
        reminder = await service.update_reminder(
            reminder_id=reminder_id,
            user_id=user_id,
            **update_data
        )
        
        if not reminder:
            raise HTTPException(status_code=404, detail="Reminder not found")
        
        return ReminderResponse(
            id=reminder.id,
            title=reminder.title,
            description=reminder.description,
            reminder_time=reminder.reminder_time.isoformat(),
            reminder_type=reminder.reminder_type,
            is_completed=reminder.is_completed,
            status=reminder.status,
            created_at=reminder.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating reminder: {e}")
        raise HTTPException(status_code=500, detail="Failed to update reminder")


@router.delete("/{reminder_id}")
async def delete_reminder(
    reminder_id: int,
    user_id: int,  # In production, get from auth token
    db: AsyncSession = Depends(get_db)
):
    """Delete a reminder"""
    try:
        service = ReminderService()
        success = await service.delete_reminder(reminder_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Reminder not found")
        
        return {"message": "Reminder deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting reminder: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete reminder")


@router.post("/{reminder_id}/complete")
async def mark_reminder_completed(
    reminder_id: int,
    user_id: int,  # In production, get from auth token
    db: AsyncSession = Depends(get_db)
):
    """Mark a reminder as completed"""
    try:
        service = ReminderService()
        success = await service.mark_reminder_completed(reminder_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Reminder not found")
        
        return {"message": "Reminder marked as completed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking reminder completed: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark reminder completed")


@router.post("/{reminder_id}/snooze")
async def snooze_reminder(
    reminder_id: int,
    duration: str,  # "15m", "1h", "2d", etc.
    user_id: int,  # In production, get from auth token
    db: AsyncSession = Depends(get_db)
):
    """Snooze a reminder for a specified duration"""
    try:
        service = ReminderService()
        success = await service.snooze_reminder(reminder_id, user_id, duration)
        
        if not success:
            raise HTTPException(status_code=404, detail="Reminder not found")
        
        return {"message": f"Reminder snoozed for {duration}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error snoozing reminder: {e}")
        raise HTTPException(status_code=500, detail="Failed to snooze reminder")


@router.get("/status/pending")
async def get_pending_reminders(
    db: AsyncSession = Depends(get_db)
):
    """Get all pending reminders (admin endpoint)"""
    try:
        service = ReminderService()
        reminders = await service.get_pending_reminders()
        
        return {
            "pending_count": len(reminders),
            "reminders": [
                {
                    "id": reminder.id,
                    "title": reminder.title,
                    "user_id": reminder.user_id,
                    "reminder_time": reminder.reminder_time.isoformat(),
                    "status": reminder.status
                }
                for reminder in reminders
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting pending reminders: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pending reminders")

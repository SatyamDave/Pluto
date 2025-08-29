"""
Calendar API routes for Jarvis Phone AI Assistant
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from calendar_service.calendar_service import CalendarService

logger = logging.getLogger(__name__)
router = APIRouter()


class CalendarEventCreate(BaseModel):
    """Create calendar event request model"""
    title: str
    description: str = ""
    start_time: str
    end_time: str
    location: str = ""
    attendees: List[str] = []
    is_all_day: bool = False


class CalendarEventMove(BaseModel):
    """Move calendar event request model"""
    new_start_time: str
    new_end_time: str = None


class CalendarEvent(BaseModel):
    """Calendar event response model"""
    id: str
    title: str
    description: str
    start_time: str
    end_time: str
    location: str
    attendees: List[str]
    is_all_day: bool
    status: str


@router.get("/next-event/{user_id}")
async def get_next_event(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get the next upcoming calendar event"""
    try:
        service = CalendarService()
        event = await service.get_next_event(user_id)
        
        if not event:
            return {"message": "No upcoming events"}
        
        return event
        
    except Exception as e:
        logger.error(f"Error getting next event: {e}")
        raise HTTPException(status_code=500, detail="Failed to get next event")


@router.get("/today/{user_id}")
async def get_today_events(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all events for today"""
    try:
        service = CalendarService()
        events = await service.get_today_events(user_id)
        
        return {
            "user_id": user_id,
            "date": "today",
            "event_count": len(events),
            "events": events
        }
        
    except Exception as e:
        logger.error(f"Error getting today's events: {e}")
        raise HTTPException(status_code=500, detail="Failed to get today's events")


@router.get("/upcoming/{user_id}")
async def get_upcoming_events(
    user_id: int,
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """Get upcoming events for the next N days"""
    try:
        service = CalendarService()
        events = await service.get_upcoming_events(user_id, days)
        
        return {
            "user_id": user_id,
            "days_ahead": days,
            "event_count": len(events),
            "events": events
        }
        
    except Exception as e:
        logger.error(f"Error getting upcoming events: {e}")
        raise HTTPException(status_code=500, detail="Failed to get upcoming events")


@router.get("/analytics/{user_id}")
async def get_calendar_analytics(
    user_id: int,
    days: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """Get calendar analytics for a user"""
    try:
        service = CalendarService()
        analytics = await service.get_calendar_analytics(user_id, days)
        
        if "error" in analytics:
            raise HTTPException(status_code=400, detail=analytics["error"])
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting calendar analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get calendar analytics")


@router.post("/create")
async def create_calendar_event(
    event_data: CalendarEventCreate,
    user_id: int,  # In production, get from auth token
    db: AsyncSession = Depends(get_db)
):
    """Create a new calendar event"""
    try:
        service = CalendarService()
        event = await service.create_event(
            user_id=user_id,
            title=event_data.title,
            description=event_data.description,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            location=event_data.location,
            attendees=event_data.attendees,
            is_all_day=event_data.is_all_day
        )
        
        if "error" in event:
            raise HTTPException(status_code=400, detail=event["error"])
        
        return {
            "message": "Calendar event created successfully",
            "event": event
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating calendar event: {e}")
        raise HTTPException(status_code=500, detail="Failed to create calendar event")


@router.post("/{event_id}/move")
async def move_calendar_event(
    event_id: str,
    move_data: CalendarEventMove,
    user_id: int,  # In production, get from auth token
    db: AsyncSession = Depends(get_db)
):
    """Move/reschedule a calendar event"""
    try:
        service = CalendarService()
        result = await service.move_event(
            user_id=user_id,
            event_id=event_id,
            new_start_time=move_data.new_start_time,
            new_end_time=move_data.new_end_time
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "message": "Calendar event moved successfully",
            "event": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moving calendar event: {e}")
        raise HTTPException(status_code=500, detail="Failed to move calendar event")

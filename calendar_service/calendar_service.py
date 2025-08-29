"""
Calendar service for Jarvis Phone AI Assistant
Integrates with Google Calendar API
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from db.database import get_db
from db.models import CalendarEvent, User
from config import settings

logger = logging.getLogger(__name__)

# Google Calendar API scopes
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events'
]


class CalendarService:
    """Service for managing Google Calendar integration"""
    
    def __init__(self):
        self.service = None
        self.creds = None
    
    async def authenticate_user(self, user_id: int) -> bool:
        """Authenticate user with Google Calendar API"""
        try:
            db = await get_db()
            
            # Get user
            user_query = "SELECT * FROM users WHERE id = :user_id"
            result = await db.execute(user_query, {"user_id": user_id})
            user = result.fetchone()
            
            if not user:
                logger.error(f"User {user_id} not found")
                return False
            
            # Check if user has valid credentials
            if hasattr(user, 'calendar_credentials') and user.calendar_credentials:
                # Refresh credentials if needed
                self.creds = Credentials.from_authorized_user_info(
                    user.calendar_credentials, SCOPES
                )
                
                if self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                    
                    # Update stored credentials
                    await self._update_user_credentials(user_id, self.creds.to_json())
                
                self.service = build('calendar', 'v3', credentials=self.creds)
                return True
            
            else:
                logger.info(f"User {user_id} needs Calendar authentication")
                return False
                
        except Exception as e:
            logger.error(f"Error authenticating user {user_id}: {e}")
            return False
    
    async def get_next_event(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get the next upcoming calendar event"""
        try:
            if not await self.authenticate_user(user_id):
                return None
            
            now = datetime.utcnow().isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=1,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                return None
            
            event = events[0]
            return self._format_event(event)
            
        except HttpError as e:
            logger.error(f"Calendar API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting next event: {e}")
            return None
    
    async def get_today_events(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all events for today"""
        try:
            if not await self.authenticate_user(user_id):
                return []
            
            today = datetime.utcnow().date()
            start_time = datetime.combine(today, datetime.min.time()).isoformat() + 'Z'
            end_time = datetime.combine(today, datetime.max.time()).isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_time,
                timeMax=end_time,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            return [self._format_event(event) for event in events]
            
        except Exception as e:
            logger.error(f"Error getting today's events: {e}")
            return []
    
    async def get_upcoming_events(self, user_id: int, days: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming events for the next N days"""
        try:
            if not await self.authenticate_user(user_id):
                return []
            
            now = datetime.utcnow()
            end_time = (now + timedelta(days=days)).isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now.isoformat() + 'Z',
                timeMax=end_time,
                maxResults=20,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            return [self._format_event(event) for event in events]
            
        except Exception as e:
            logger.error(f"Error getting upcoming events: {e}")
            return []
    
    def _format_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Format calendar event for consistent output"""
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        
        return {
            'id': event['id'],
            'title': event.get('summary', 'No Title'),
            'description': event.get('description', ''),
            'start_time': start,
            'end_time': end,
            'location': event.get('location', ''),
            'attendees': [attendee['email'] for attendee in event.get('attendees', [])],
            'is_all_day': 'date' in event['start'],
            'status': event.get('status', 'confirmed')
        }
    
    async def _update_user_credentials(self, user_id: int, credentials_json: str):
        """Update user's Calendar credentials"""
        try:
            db = await get_db()
            
            update_query = "UPDATE users SET calendar_credentials = :creds WHERE id = :user_id"
            await db.execute(update_query, {
                "creds": credentials_json,
                "user_id": user_id
            })
            
            await db.commit()
            logger.info(f"Updated Calendar credentials for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating user credentials: {e}")
    
    async def get_calendar_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get calendar analytics for a user"""
        try:
            if not await self.authenticate_user(user_id):
                return {"error": "Authentication required"}
            
            now = datetime.utcnow()
            end_time = (now + timedelta(days=days)).isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now.isoformat() + 'Z',
                timeMax=end_time,
                maxResults=100,
                singleEvents=True
            ).execute()
            
            events = events_result.get('items', [])
            
            analytics = {
                "total_events": len(events),
                "meetings": 0,
                "all_day_events": 0,
                "busy_hours": {},
                "top_locations": {}
            }
            
            for event in events:
                # Count meeting types
                if 'meeting' in event.get('summary', '').lower():
                    analytics["meetings"] += 1
                
                # Count all-day events
                if 'date' in event['start']:
                    analytics["all_day_events"] += 1
                
                # Track busy hours
                if 'dateTime' in event['start']:
                    start_time = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
                    hour = start_time.hour
                    analytics["busy_hours"][hour] = analytics["busy_hours"].get(hour, 0) + 1
                
                # Track locations
                location = event.get('location', '')
                if location:
                    analytics["top_locations"][location] = analytics["top_locations"].get(location, 0) + 1
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting calendar analytics: {e}")
            return {"error": str(e)}
    
    async def create_event(
        self,
        user_id: int,
        title: str,
        description: str = "",
        start_time: str = None,
        end_time: str = None,
        location: str = "",
        attendees: List[str] = [],
        is_all_day: bool = False
    ) -> Dict[str, Any]:
        """Create a new calendar event"""
        try:
            if not await self.authenticate_user(user_id):
                return {"error": "Authentication required"}
            
            # Parse times
            if start_time and end_time:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            else:
                # Default to 1 hour from now
                start_dt = datetime.utcnow() + timedelta(hours=1)
                end_dt = start_dt + timedelta(hours=1)
            
            # Build event body
            event_body = {
                'summary': title,
                'description': description,
                'location': location,
                'start': {
                    'dateTime': start_dt.isoformat() + 'Z' if not is_all_day else start_dt.date().isoformat(),
                    'timeZone': 'UTC'
                },
                'end': {
                    'dateTime': end_dt.isoformat() + 'Z' if not is_all_day else end_dt.date().isoformat(),
                    'timeZone': 'UTC'
                }
            }
            
            # Add attendees if provided
            if attendees:
                event_body['attendees'] = [{'email': email} for email in attendees]
            
            # Create event in Google Calendar
            event = self.service.events().insert(
                calendarId='primary',
                body=event_body
            ).execute()
            
            # Store in database
            await self._store_calendar_event(user_id, event)
            
            logger.info(f"Created calendar event '{title}' for user {user_id}")
            
            return {
                "success": True,
                "event_id": event['id'],
                "title": event['summary'],
                "start_time": event['start'].get('dateTime', event['start'].get('date')),
                "end_time": event['end'].get('dateTime', event['end'].get('date')),
                "location": event.get('location', ''),
                "attendees": [attendee['email'] for attendee in event.get('attendees', [])]
            }
            
        except HttpError as e:
            logger.error(f"Calendar API error creating event: {e}")
            return {"error": f"Calendar API error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return {"error": str(e)}
    
    async def move_event(
        self,
        user_id: int,
        event_id: str,
        new_start_time: str,
        new_end_time: str = None
    ) -> Dict[str, Any]:
        """Move/reschedule a calendar event"""
        try:
            if not await self.authenticate_user(user_id):
                return {"error": "Authentication required"}
            
            # Get existing event
            existing_event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            if not existing_event:
                return {"error": "Event not found"}
            
            # Parse new times
            new_start_dt = datetime.fromisoformat(new_start_time.replace('Z', '+00:00'))
            if new_end_time:
                new_end_dt = datetime.fromisoformat(new_end_time.replace('Z', '+00:00'))
            else:
                # Keep same duration
                old_start = datetime.fromisoformat(existing_event['start'].get('dateTime', existing_event['start'].get('date')).replace('Z', '+00:00'))
                old_end = datetime.fromisoformat(existing_event['end'].get('dateTime', existing_event['end'].get('date')).replace('Z', '+00:00'))
                duration = old_end - old_start
                new_end_dt = new_start_dt + duration
            
            # Update event
            existing_event['start'] = {
                'dateTime': new_start_dt.isoformat() + 'Z',
                'timeZone': 'UTC'
            }
            existing_event['end'] = {
                'dateTime': new_end_dt.isoformat() + 'Z',
                'timeZone': 'UTC'
            }
            
            # Update in Google Calendar
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=existing_event
            ).execute()
            
            # Update database
            await self._update_calendar_event(user_id, event_id, updated_event)
            
            logger.info(f"Moved calendar event '{updated_event['summary']}' for user {user_id}")
            
            return {
                "success": True,
                "event_id": updated_event['id'],
                "title": updated_event['summary'],
                "start_time": updated_event['start'].get('dateTime'),
                "end_time": updated_event['end'].get('dateTime'),
                "location": updated_event.get('location', ''),
                "attendees": [attendee['email'] for attendee in updated_event.get('attendees', [])]
            }
            
        except HttpError as e:
            logger.error(f"Calendar API error moving event: {e}")
            return {"error": f"Calendar API error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error moving calendar event: {e}")
            return {"error": str(e)}
    
    async def _store_calendar_event(self, user_id: int, event: Dict[str, Any]):
        """Store calendar event in database"""
        try:
            db = await get_db()
            
            # Check if event already exists
            existing_query = "SELECT id FROM calendar_events WHERE event_id = :event_id AND user_id = :user_id"
            result = await db.execute(existing_query, {
                "event_id": event['id'],
                "user_id": user_id
            })
            
            if result.fetchone():
                return  # Event already stored
            
            # Create new event record
            calendar_event = CalendarEvent(
                user_id=user_id,
                event_id=event['id'],
                title=event.get('summary', 'No Title'),
                description=event.get('description', ''),
                start_time=event['start'].get('dateTime', event['start'].get('date')),
                end_time=event['end'].get('dateTime', event['end'].get('date')),
                location=event.get('location', ''),
                attendees=[attendee['email'] for email in event.get('attendees', [])],
                calendar_source='google'
            )
            
            db.add(calendar_event)
            await db.commit()
            
            logger.debug(f"Stored calendar event {event['id']} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing calendar event: {e}")
    
    async def _update_calendar_event(self, user_id: int, event_id: str, event: Dict[str, Any]):
        """Update calendar event in database"""
        try:
            db = await get_db()
            
            update_query = """
                UPDATE calendar_events 
                SET title = :title, description = :description, 
                    start_time = :start_time, end_time = :end_time,
                    location = :location, attendees = :attendees,
                    updated_at = NOW()
                WHERE event_id = :event_id AND user_id = :user_id
            """
            
            await db.execute(update_query, {
                "title": event.get('summary', 'No Title'),
                "description": event.get('description', ''),
                "start_time": event['start'].get('dateTime', event['start'].get('date')),
                "end_time": event['end'].get('dateTime', event['end'].get('date')),
                "location": event.get('location', ''),
                "attendees": [attendee['email'] for attendee in event.get('attendees', [])],
                "event_id": event_id,
                "user_id": user_id
            })
            
            await db.commit()
            
            logger.debug(f"Updated calendar event {event_id} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating calendar event: {e}")

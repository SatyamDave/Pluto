"""
Digest Service for Jarvis Phone AI Assistant
Handles morning and evening digests with timezone support
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, time, timedelta
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore

from db.database import get_db
from db.models import User, UserPreference, CalendarEvent, EmailMessage, Reminder
from services.memory_manager import memory_manager
from services.habit_engine import habit_engine
from services.proactive_agent import proactive_agent
from telephony.telephony_manager import telephony_manager
from utils.logging_config import get_logger

logger = get_logger(__name__)


class DigestService:
    """Service for generating and sending morning/evening digests"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(
            jobstores={'default': MemoryJobStore()},
            timezone='UTC'
        )
        self.logger = get_logger(__name__)
        self._setup_scheduler()
    
    def _setup_scheduler(self):
        """Setup the scheduler with default digest times"""
        try:
            # Morning digest at 7 AM UTC (will be adjusted per user timezone)
            self.scheduler.add_job(
                self._send_morning_digests,
                CronTrigger(hour=7, minute=0),
                id='morning_digests',
                name='Send morning digests to all users'
            )
            
            # Evening digest at 7 PM UTC (will be adjusted per user timezone)
            self.scheduler.add_job(
                self._send_evening_digests,
                CronTrigger(hour=19, minute=0),
                id='evening_digests',
                name='Send evening digests to all users'
            )
            
            self.logger.info("Digest scheduler configured")
            
        except Exception as e:
            self.logger.error(f"Error setting up digest scheduler: {e}")
    
    def start(self):
        """Start the digest scheduler"""
        try:
            if not self.scheduler.running:
                self.scheduler.start()
                self.logger.info("Digest scheduler started")
        except Exception as e:
            self.logger.error(f"Error starting digest scheduler: {e}")
    
    def stop(self):
        """Stop the digest scheduler"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                self.logger.info("Digest scheduler stopped")
        except Exception as e:
            self.logger.error(f"Error stopping digest scheduler: {e}")
    
    async def _send_morning_digests(self):
        """Send morning digests to all active users"""
        try:
            self.logger.info("Starting morning digest distribution")
            
            # Get all active users
            users = await self._get_active_users()
            
            for user in users:
                try:
                    await self._send_morning_digest(user['id'])
                    # Small delay to avoid overwhelming the system
                    await asyncio.sleep(1)
                except Exception as e:
                    self.logger.error(f"Error sending morning digest to user {user['id']}: {e}")
            
            self.logger.info(f"Morning digests sent to {len(users)} users")
            
        except Exception as e:
            self.logger.error(f"Error in morning digest distribution: {e}")
    
    async def _send_evening_digests(self):
        """Send evening digests to all active users"""
        try:
            self.logger.info("Starting evening digest distribution")
            
            # Get all active users
            users = await self._get_active_users()
            
            for user in users:
                try:
                    await self._send_evening_digest(user['id'])
                    # Small delay to avoid overwhelming the system
                    await asyncio.sleep(1)
                except Exception as e:
                    self.logger.error(f"Error sending evening digest to user {user['id']}: {e}")
            
            self.logger.info(f"Evening digests sent to {len(users)} users")
            
        except Exception as e:
            self.logger.error(f"Error in evening digest distribution: {e}")
    
    async def _get_active_users(self) -> List[Dict[str, Any]]:
        """Get all active users from database"""
        try:
            db = await get_db()
            
            query = """
                SELECT id, phone_number, name, timezone 
                FROM users 
                WHERE is_active = true 
                AND phone_number IS NOT NULL
            """
            
            result = await db.execute(query)
            users = [dict(row) for row in result.fetchall()]
            
            return users
            
        except Exception as e:
            self.logger.error(f"Error getting active users: {e}")
            return []
    
    async def _send_morning_digest(self, user_id: int):
        """Send morning digest to a specific user"""
        try:
            # Get user's timezone preference
            user_tz = await self._get_user_timezone(user_id)
            if not user_tz:
                user_tz = 'UTC'
            
            # Check if it's actually morning in user's timezone
            user_time = datetime.now(pytz.timezone(user_tz))
            if not (6 <= user_time.hour <= 9):  # Only send between 6-9 AM local time
                self.logger.info(f"Not morning in {user_tz} for user {user_id}")
                return
            
            # Generate morning digest content
            digest_content = await self._generate_morning_digest(user_id)
            
            # Send via SMS
            user_phone = await self._get_user_phone(user_id)
            if user_phone:
                await telephony_manager.send_sms(
                    to_phone=user_phone,
                    message=digest_content
                )
                
                # Log the digest
                await memory_manager.store_memory(
                    user_id=user_id,
                    memory_type="digest_sent",
                    content=f"Morning digest sent: {digest_content[:100]}...",
                    metadata={"digest_type": "morning", "sent_at": datetime.utcnow().isoformat()}
                )
                
                self.logger.info(f"Morning digest sent to user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Error sending morning digest to user {user_id}: {e}")
    
    async def _send_evening_digest(self, user_id: int):
        """Send evening digest to a specific user"""
        try:
            # Get user's timezone preference
            user_tz = await self._get_user_timezone(user_id)
            if not user_tz:
                user_tz = 'UTC'
            
            # Check if it's actually evening in user's timezone
            user_time = datetime.now(pytz.timezone(user_tz))
            if not (18 <= user_time.hour <= 21):  # Only send between 6-9 PM local time
                self.logger.info(f"Not evening in {user_tz} for user {user_id}")
                return
            
            # Generate evening digest content
            digest_content = await self._generate_evening_digest(user_id)
            
            # Send via SMS
            user_phone = await self._get_user_phone(user_id)
            if user_phone:
                await telephony_manager.send_sms(
                    to_phone=user_phone,
                    message=digest_content
                )
                
                # Log the digest
                await memory_manager.store_memory(
                    user_id=user_id,
                    memory_type="digest_sent",
                    content=f"Evening digest sent: {digest_content[:100]}...",
                    metadata={"digest_type": "evening", "sent_at": datetime.utcnow().isoformat()}
                )
                
                self.logger.info(f"Evening digest sent to user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Error sending evening digest to user {user_id}: {e}")
    
    async def _generate_morning_digest(self, user_id: int) -> str:
        """Generate morning digest content for a user"""
        try:
            # Get today's calendar events
            today_events = await self._get_today_events(user_id)
            
            # Get unread emails count
            unread_emails = await self._get_unread_emails_count(user_id)
            
            # Get pending reminders
            pending_reminders = await self._get_pending_reminders(user_id)
            
            # Get proactive suggestions
            proactive_suggestions = await proactive_agent.suggest_proactive_actions(user_id)
            
            # Build digest content
            digest_parts = []
            
            # Greeting
            digest_parts.append("🌅 Good morning! Here's your daily digest:")
            
            # Calendar events
            if today_events:
                digest_parts.append(f"📅 Today: {len(today_events)} events")
                for i, event in enumerate(today_events[:3], 1):  # Show first 3
                    time_str = self._format_event_time(event['start_time'])
                    digest_parts.append(f"{i}. {time_str} - {event['title']}")
                if len(today_events) > 3:
                    digest_parts.append(f"... and {len(today_events) - 3} more")
            else:
                digest_parts.append("📅 Today: No events scheduled")
            
            # Email summary
            if unread_emails > 0:
                digest_parts.append(f"📧 {unread_emails} unread emails")
            else:
                digest_parts.append("📧 Inbox is clean!")
            
            # Reminders
            if pending_reminders:
                digest_parts.append(f"⏰ {len(pending_reminders)} pending reminders")
                for i, reminder in enumerate(pending_reminders[:2], 1):  # Show first 2
                    digest_parts.append(f"{i}. {reminder['title']}")
            
            # Proactive suggestions
            if proactive_suggestions:
                digest_parts.append("💡 Suggestions:")
                for i, suggestion in enumerate(proactive_suggestions[:2], 1):
                    digest_parts.append(f"{i}. {suggestion['action']}")
            
            # Weather and commute (placeholder for future integration)
            digest_parts.append("🌤️ Weather: Check your weather app for today's forecast")
            
            # Sign off
            digest_parts.append("Have a great day! Reply with any questions.")
            
            return "\n".join(digest_parts)
            
        except Exception as e:
            self.logger.error(f"Error generating morning digest for user {user_id}: {e}")
            return "🌅 Good morning! I'm having trouble loading your digest right now. Reply with any questions!"
    
    async def _generate_evening_digest(self, user_id: int) -> str:
        """Generate evening digest content for a user"""
        try:
            # Get tomorrow's calendar events
            tomorrow_events = await self._get_tomorrow_events(user_id)
            
            # Get today's completed tasks
            completed_tasks = await self._get_completed_tasks_today(user_id)
            
            # Get pending items for tomorrow
            pending_tomorrow = await self._get_pending_tomorrow(user_id)
            
            # Build digest content
            digest_parts = []
            
            # Greeting
            digest_parts.append("🌙 Good evening! Here's your wrap-up:")
            
            # Tomorrow's schedule
            if tomorrow_events:
                digest_parts.append(f"📅 Tomorrow: {len(tomorrow_events)} events")
                for i, event in enumerate(tomorrow_events[:3], 1):
                    time_str = self._format_event_time(event['start_time'])
                    digest_parts.append(f"{i}. {time_str} - {event['title']}")
            else:
                digest_parts.append("📅 Tomorrow: No events scheduled")
            
            # Today's accomplishments
            if completed_tasks:
                digest_parts.append(f"✅ Completed today: {len(completed_tasks)} tasks")
                for i, task in enumerate(completed_tasks[:2], 1):
                    digest_parts.append(f"{i}. {task['title']}")
            
            # Tomorrow's preparation
            if pending_tomorrow:
                digest_parts.append(f"📋 Prepare for tomorrow: {len(pending_tomorrow)} items")
                for i, item in enumerate(pending_tomorrow[:2], 1):
                    digest_parts.append(f"{i}. {item['title']}")
            
            # Evening routine suggestions
            digest_parts.append("🌙 Evening routine:")
            digest_parts.append("1. Review tomorrow's schedule")
            digest_parts.append("2. Set out clothes/items needed")
            digest_parts.append("3. Wind down and relax")
            
            # Sign off
            digest_parts.append("Sleep well! I'll see you in the morning.")
            
            return "\n".join(digest_parts)
            
        except Exception as e:
            self.logger.error(f"Error generating evening digest for user {user_id}: {e}")
            return "🌙 Good evening! I'm having trouble loading your wrap-up right now. Have a good night!"
    
    async def _get_today_events(self, user_id: int) -> List[Dict[str, Any]]:
        """Get today's calendar events for a user"""
        try:
            db = await get_db()
            
            today = datetime.utcnow().date()
            start_time = datetime.combine(today, time.min)
            end_time = datetime.combine(today, time.max)
            
            query = """
                SELECT id, title, start_time, end_time, location
                FROM calendar_events 
                WHERE user_id = :user_id 
                AND start_time >= :start_time 
                AND start_time <= :end_time
                ORDER BY start_time
            """
            
            result = await db.execute(query, {
                "user_id": user_id,
                "start_time": start_time,
                "end_time": end_time
            })
            
            events = [dict(row) for row in result.fetchall()]
            return events
            
        except Exception as e:
            self.logger.error(f"Error getting today's events: {e}")
            return []
    
    async def _get_tomorrow_events(self, user_id: int) -> List[Dict[str, Any]]:
        """Get tomorrow's calendar events for a user"""
        try:
            db = await get_db()
            
            tomorrow = (datetime.utcnow() + timedelta(days=1)).date()
            start_time = datetime.combine(tomorrow, time.min)
            end_time = datetime.combine(tomorrow, time.max)
            
            query = """
                SELECT id, title, start_time, end_time, location
                FROM calendar_events 
                WHERE user_id = :user_id 
                AND start_time >= :start_time 
                AND start_time <= :end_time
                ORDER BY start_time
            """
            
            result = await db.execute(query, {
                "user_id": user_id,
                "start_time": start_time,
                "end_time": end_time
            })
            
            events = [dict(row) for row in result.fetchall()]
            return events
            
        except Exception as e:
            self.logger.error(f"Error getting tomorrow's events: {e}")
            return []
    
    async def _get_unread_emails_count(self, user_id: int) -> int:
        """Get count of unread emails for a user"""
        try:
            db = await get_db()
            
            query = """
                SELECT COUNT(*) as count
                FROM email_messages 
                WHERE user_id = :user_id AND is_read = false
            """
            
            result = await db.execute(query, {"user_id": user_id})
            row = result.fetchone()
            
            return row.count if row else 0
            
        except Exception as e:
            self.logger.error(f"Error getting unread emails count: {e}")
            return 0
    
    async def _get_pending_reminders(self, user_id: int) -> List[Dict[str, Any]]:
        """Get pending reminders for a user"""
        try:
            db = await get_db()
            
            query = """
                SELECT id, title, reminder_time
                FROM reminders 
                WHERE user_id = :user_id 
                AND is_completed = false 
                AND reminder_time >= :now
                ORDER BY reminder_time
                LIMIT 5
            """
            
            result = await db.execute(query, {
                "user_id": user_id,
                "now": datetime.utcnow()
            })
            
            reminders = [dict(row) for row in result.fetchall()]
            return reminders
            
        except Exception as e:
            self.logger.error(f"Error getting pending reminders: {e}")
            return []
    
    async def _get_completed_tasks_today(self, user_id: int) -> List[Dict[str, Any]]:
        """Get tasks completed today by a user"""
        try:
            db = await get_db()
            
            today = datetime.utcnow().date()
            start_time = datetime.combine(today, time.min)
            end_time = datetime.combine(today, time.max)
            
            query = """
                SELECT id, title, updated_at
                FROM reminders 
                WHERE user_id = :user_id 
                AND is_completed = true 
                AND updated_at >= :start_time 
                AND updated_at <= :end_time
                ORDER BY updated_at DESC
                LIMIT 5
            """
            
            result = await db.execute(query, {
                "user_id": user_id,
                "start_time": start_time,
                "end_time": end_time
            })
            
            tasks = [dict(row) for row in result.fetchall()]
            return tasks
            
        except Exception as e:
            self.logger.error(f"Error getting completed tasks: {e}")
            return []
    
    async def _get_pending_tomorrow(self, user_id: int) -> List[Dict[str, Any]]:
        """Get items pending for tomorrow"""
        try:
            db = await get_db()
            
            tomorrow = (datetime.utcnow() + timedelta(days=1)).date()
            start_time = datetime.combine(tomorrow, time.min)
            end_time = datetime.combine(tomorrow, time.max)
            
            query = """
                SELECT id, title, reminder_time
                FROM reminders 
                WHERE user_id = :user_id 
                AND is_completed = false 
                AND reminder_time >= :start_time 
                AND reminder_time <= :end_time
                ORDER BY reminder_time
                LIMIT 5
            """
            
            result = await db.execute(query, {
                "user_id": user_id,
                "start_time": start_time,
                "end_time": end_time
            })
            
            items = [dict(row) for row in result.fetchall()]
            return items
            
        except Exception as e:
            self.logger.error(f"Error getting pending tomorrow: {e}")
            return []
    
    async def _get_user_timezone(self, user_id: int) -> Optional[str]:
        """Get user's timezone preference"""
        try:
            db = await get_db()
            
            query = """
                SELECT preference_value 
                FROM user_preferences 
                WHERE user_id = :user_id AND preference_key = 'timezone'
            """
            
            result = await db.execute(query, {"user_id": user_id})
            row = result.fetchone()
            
            if row and row.preference_value:
                return row.preference_value
            
            # Default to UTC if no preference set
            return 'UTC'
            
        except Exception as e:
            self.logger.error(f"Error getting user timezone: {e}")
            return 'UTC'
    
    async def _get_user_phone(self, user_id: int) -> Optional[str]:
        """Get user's phone number"""
        try:
            db = await get_db()
            
            query = "SELECT phone_number FROM users WHERE id = :user_id"
            result = await db.execute(query, {"user_id": user_id})
            row = result.fetchone()
            
            return row.phone_number if row else None
            
        except Exception as e:
            self.logger.error(f"Error getting user phone: {e}")
            return None
    
    def _format_event_time(self, start_time_str: str) -> str:
        """Format event start time for display"""
        try:
            if isinstance(start_time_str, str):
                dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            else:
                dt = start_time_str
            
            return dt.strftime("%I:%M %p")
            
        except Exception as e:
            self.logger.error(f"Error formatting event time: {e}")
            return "TBD"
    
    async def send_manual_digest(self, user_id: int, digest_type: str = "morning") -> Dict[str, Any]:
        """Send a manual digest to a user (for testing or on-demand)"""
        try:
            if digest_type == "morning":
                content = await self._generate_morning_digest(user_id)
            elif digest_type == "evening":
                content = await self._generate_evening_digest(user_id)
            else:
                return {"error": "Invalid digest type. Use 'morning' or 'evening'"}
            
            # Send via SMS
            user_phone = await self._get_user_phone(user_id)
            if user_phone:
                await telephony_manager.send_sms(
                    to_phone=user_phone,
                    message=content
                )
                
                return {
                    "success": True,
                    "digest_type": digest_type,
                    "sent_to": user_phone,
                    "content_length": len(content)
                }
            else:
                return {"error": "User phone number not found"}
                
        except Exception as e:
            self.logger.error(f"Error sending manual digest: {e}")
            return {"error": str(e)}


# Global instance
digest_service = DigestService()

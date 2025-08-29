#!/usr/bin/env python3
"""
Pluto Proactive Agent
Handles scheduled tasks and proactive messaging with intelligent automation
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Optional
from collections import defaultdict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from services.memory_manager import memory_manager
from services.habit_engine import habit_engine
from services.style_engine import style_engine
from services.context_aggregator import context_aggregator
from services.user_manager import user_manager
from services.digest_service import DigestService
from services.communication_service import CommunicationService
from telephony.outbound_call_service import OutboundCallService
from utils.logging_config import get_logger
from utils.constants import PROACTIVE_THRESHOLD
from db.models import User, UserPreference, ProactiveTask
from sqlalchemy import select, and_

# Import get_db_session from memory_manager since it's already defined there
from services.memory_manager import get_db_session

logger = get_logger(__name__)


class ProactiveAgent:
    """Pluto's proactive agent - handles scheduled tasks and proactive messaging"""
    
    def __init__(self):
        self.is_running = False
        self.scheduler = AsyncIOScheduler()
        self.scheduled_tasks = {}
        self.user_preferences = {}
        self.proactive_thresholds = {
            'email_urgency': 0.8,
            'calendar_conflict': 0.7,
            'habit_reminder': 0.6,
            'overdue_reminder': 0.9
        }
        
        # Initialize services
        self.digest_service = DigestService()
        self.communication_service = CommunicationService()
        self.outbound_call_service = OutboundCallService()
        
        # Wake-up call tracking
        self.active_wakeup_calls = {}
        
    async def start(self):
        """Start the proactive agent with scheduler"""
        try:
            if not self.is_running:
                self.is_running = True
                
                # Start the scheduler
                self.scheduler.start()
                logger.info("Pluto Proactive Agent scheduler started")
                
                # Schedule recurring tasks
                await self._schedule_recurring_tasks()
                
                # Start background task for proactive monitoring
                asyncio.create_task(self._proactive_monitoring_loop())
                
                logger.info("Pluto Proactive Agent fully started")
                
        except Exception as e:
            logger.error(f"Error starting proactive agent: {e}")
            raise
    
    async def stop(self):
        """Stop the proactive agent"""
        try:
            self.is_running = False
            
            # Shutdown scheduler
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("Proactive agent scheduler stopped")
            
            logger.info("Pluto Proactive Agent stopped")
            
        except Exception as e:
            logger.error(f"Error stopping proactive agent: {e}")
    
    async def _schedule_recurring_tasks(self):
        """Schedule recurring proactive tasks for all users"""
        try:
            # Get all active users
            active_users = await user_manager.get_active_users()
            
            for user in active_users:
                user_id = user["id"]
                phone_number = user["phone_number"]
                
                # Get user preferences
                user_profile = await user_manager.get_user_by_id(user_id)
                preferences = user_profile.get("preferences", {})
                
                # Only schedule if proactive mode is enabled
                if preferences.get("proactive_mode", True):
                    await self._schedule_user_tasks(user_id, phone_number, preferences)
            
            logger.info(f"Scheduled recurring tasks for {len(active_users)} users")
            
        except Exception as e:
            logger.error(f"Error scheduling recurring tasks: {e}")
    
    async def _schedule_user_tasks(self, user_id: int, phone_number: str, preferences: Dict[str, Any]):
        """Schedule recurring tasks for a specific user"""
        try:
            # Schedule morning digest
            digest_time = preferences.get("morning_digest_time", "08:00")
            hour, minute = map(int, digest_time.split(":"))
            
            job_id = f"morning_digest_{user_id}"
            self.scheduler.add_job(
                func=self._send_morning_digest,
                trigger=CronTrigger(hour=hour, minute=minute),
                args=[user_id, phone_number],
                id=job_id,
                replace_existing=True,
                timezone="UTC"
            )
            
            # Schedule evening digest
            evening_time = preferences.get("evening_digest_time", "18:00")
            evening_hour, evening_minute = map(int, evening_time.split(":"))
            
            evening_job_id = f"evening_digest_{user_id}"
            self.scheduler.add_job(
                func=self._send_evening_digest,
                trigger=CronTrigger(hour=evening_hour, minute=evening_minute),
                args=[user_id, phone_number],
                id=evening_job_id,
                replace_existing=True,
                timezone="UTC"
            )
            
            # Schedule habit check (every 2 hours during active hours)
            habit_job_id = f"habit_check_{user_id}"
            self.scheduler.add_job(
                func=self._check_user_habits,
                trigger=IntervalTrigger(hours=2, start_date=datetime.utcnow()),
                args=[user_id, phone_number],
                id=habit_job_id,
                replace_existing=True
            )
            
            # Schedule email monitoring (every 15 minutes during business hours)
            email_job_id = f"email_monitor_{user_id}"
            self.scheduler.add_job(
                func=self._monitor_urgent_emails,
                trigger=IntervalTrigger(minutes=15, start_date=datetime.utcnow()),
                args=[user_id, phone_number],
                id=email_job_id,
                replace_existing=True
            )
            
            # Schedule calendar conflict check (every hour)
            calendar_job_id = f"calendar_check_{user_id}"
            self.scheduler.add_job(
                func=self._check_calendar_conflicts,
                trigger=IntervalTrigger(hours=1, start_date=datetime.utcnow()),
                args=[user_id, phone_number],
                id=calendar_job_id,
                replace_existing=True
            )
            
            logger.info(f"Scheduled tasks for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error scheduling tasks for user {user_id}: {e}")
    
    async def _send_morning_digest(self, user_id: int, phone_number: str):
        """Send morning digest to user"""
        try:
            logger.info(f"Sending morning digest to user {user_id}")
            
            # Check if user wants morning digest
            user_profile = await user_manager.get_user_by_id(user_id)
            preferences = user_profile.get("preferences", {})
            
            if not preferences.get("morning_digest_enabled", True):
                logger.info(f"Morning digest disabled for user {user_id}")
                return
            
            # Use the new daily digest method
            success = await self.send_daily_digest(user_id)
            
            if success:
                logger.info(f"Daily digest sent to user {user_id}")
            else:
                logger.error(f"Failed to send daily digest to user {user_id}")
                
        except Exception as e:
            logger.error(f"Error sending morning digest to user {user_id}: {e}")
    
    async def _send_evening_digest(self, user_id: int, phone_number: str):
        """Send evening digest to user with tomorrow's preview"""
        try:
            logger.info(f"Sending evening digest to user {user_id}")
            
            # Check if user wants evening digest
            user_profile = await user_manager.get_user_by_id(user_id)
            preferences = user_profile.get("preferences", {})
            
            if not preferences.get("evening_digest_enabled", True):
                logger.info(f"Evening digest disabled for user {user_id}")
                return
            
            # Get tomorrow's reminders and events
            db = await get_db_session()
            
            # Get tomorrow's reminders
            from reminders.reminder_service import ReminderService
            reminder_service = ReminderService()
            tomorrow_reminders = await reminder_service.get_user_reminders(user_id, include_completed=False)
            
            # Filter for tomorrow's reminders
            tomorrow = (datetime.now() + timedelta(days=1)).date()
            tomorrow_reminders = [
                r for r in tomorrow_reminders 
                if r.reminder_time.date() == tomorrow and r.status == "pending"
            ]
            
            # Get tomorrow's calendar events
            from calendar_service.calendar_service import CalendarService
            calendar_service = CalendarService()
            tomorrow_events = await calendar_service.get_user_events_for_date(user_id, tomorrow)
            
            # Build evening digest message
            message = "🌙 Evening Digest - Tomorrow's Preview:\n\n"
            
            # Add tomorrow's reminders
            if tomorrow_reminders:
                message += "⏰ Tomorrow's Reminders:\n"
                for i, reminder in enumerate(tomorrow_reminders[:3], 1):  # Limit to 3
                    time_str = reminder.reminder_time.strftime("%I:%M %p")
                    message += f"{i}) {reminder.title} at {time_str}\n"
                message += "\n"
            
            # Add tomorrow's events
            if tomorrow_events:
                message += "📅 Tomorrow's Events:\n"
                for i, event in enumerate(tomorrow_events[:3], 1):  # Limit to 3
                    time_str = event.start_time.strftime("%I:%M %p")
                    message += f"{i}) {event.title} at {time_str}\n"
                message += "\n"
            
            # Add action instructions
            if tomorrow_reminders or tomorrow_events:
                message += "💬 Reply with:\n"
                message += "• 'snooze #2 1h' to delay reminder #2\n"
                message += "• 'move #1 to 2pm' to reschedule event #1\n"
                message += "• 'cancel #3' to cancel item #3"
            else:
                message += "✨ No scheduled items for tomorrow!"
            
            # Send digest
            from telephony.telephony_manager import TelephonyManager
            telephony_manager = TelephonyManager({})
            await telephony_manager.send_sms(
                to=phone_number,
                body=message,
                user_id=user_id
            )
            
            logger.info(f"Evening digest sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending evening digest to user {user_id}: {e}")
            
            # Store proactive action
            await self.store_proactive_action(
                str(user_id), "morning_digest_sent", digest_message, {"phone": phone_number}
            )
            
        except Exception as e:
            logger.error(f"Error sending morning digest to user {user_id}: {e}")
    
    async def _check_user_habits(self, user_id: int, phone_number: str):
        """Check user habits and send proactive suggestions"""
        try:
            logger.info(f"Checking habits for user {user_id}")
            
            # Get user habits
            habits = await habit_engine.get_user_habits(str(user_id))
            
            # Check for habits that are due soon
            suggestions = []
            current_time = datetime.utcnow()
            
            for habit in habits:
                if habit.get("next_predicted"):
                    try:
                        next_time = datetime.fromisoformat(habit["next_predicted"])
                        time_until = (next_time - current_time).total_seconds() / 3600  # hours
                        
                        # If habit is due within 2 hours, suggest it
                        if 0 <= time_until <= 2:
                            suggestion = await self._generate_habit_suggestion(habit, time_until)
                            if suggestion:
                                suggestions.append(suggestion)
                    except (ValueError, TypeError):
                        continue
            
            # Send habit suggestions if any
            if suggestions:
                message = "🔄 Habit suggestions:\n" + "\n".join(suggestions[:3])  # Top 3
                
                if self.communication_service.sms_handler:
                    await self.communication_service.sms_handler.send_sms(
                        to_phone=phone_number,
                        message=message
                    )
                    logger.info(f"Habit suggestions sent to user {user_id}")
                
                # Store proactive action
                await self.store_proactive_action(
                    str(user_id), "habit_suggestions_sent", message, {"suggestions": suggestions}
                )
            
        except Exception as e:
            logger.error(f"Error checking habits for user {user_id}: {e}")
    
    async def _monitor_urgent_emails(self, user_id: int, phone_number: str):
        """Monitor for urgent emails and alert user"""
        try:
            logger.info(f"Monitoring emails for user {user_id}")
            
            # Get user context
            context = await context_aggregator.get_full_context(str(user_id))
            email_status = context.get('email_status', {})
            
            # Check for urgent emails
            urgent_count = email_status.get('urgent_count', 0)
            if urgent_count > 0:
                # Check user preferences for urgent alerts
                user_profile = await user_manager.get_user_by_id(user_id)
                preferences = user_profile.get("preferences", {})
                
                if preferences.get("urgent_email_alerts", True):
                    message = f"🚨 You have {urgent_count} urgent emails! Want me to summarize them?"
                    
                    if self.communication_service.sms_handler:
                        await self.communication_service.sms_handler.send_sms(
                            to_phone=phone_number,
                            message=message
                        )
                        logger.info(f"Urgent email alert sent to user {user_id}")
                    
                    # Store proactive action
                    await self.store_proactive_action(
                        str(user_id), "urgent_email_alert", message, {"urgent_count": urgent_count}
                    )
            
        except Exception as e:
            logger.error(f"Error monitoring emails for user {user_id}: {e}")
    
    async def _check_calendar_conflicts(self, user_id: int, phone_number: str):
        """Check for calendar conflicts and alert user"""
        try:
            logger.info(f"Checking calendar for user {user_id}")
            
            # Get user context
            context = await context_aggregator.get_full_context(str(user_id))
            calendar_status = context.get('calendar_status', {})
            
            # Check for conflicts
            conflict_count = calendar_status.get('conflict_count', 0)
            if conflict_count > 0:
                # Check user preferences for calendar alerts
                user_profile = await user_manager.get_user_by_id(user_id)
                preferences = user_profile.get("preferences", {})
                
                if preferences.get("calendar_alerts", True):
                    message = f"📅 Calendar conflict detected! You have {conflict_count} overlapping events. Need help resolving?"
                    
                    if self.communication_service.sms_handler:
                        await self.communication_service.sms_handler.send_sms(
                            to_phone=phone_number,
                            message=message
                        )
                        logger.info(f"Calendar conflict alert sent to user {user_id}")
                    
                    # Store proactive action
                    await self.store_proactive_action(
                        str(user_id), "calendar_conflict_alert", message, {"conflict_count": conflict_count}
                    )
            
        except Exception as e:
            logger.error(f"Error checking calendar for user {user_id}: {e}")
    
    async def schedule_wakeup_call(
        self, 
        user_id: int, 
        phone_number: str, 
        wakeup_time: datetime,
        message: str = "Good morning! Time to wake up!"
    ) -> bool:
        """Schedule a wake-up call for the user"""
        try:
            logger.info(f"Scheduling wake-up call for user {user_id} at {wakeup_time}")
            
            # Check if user wants wake-up calls
            user_profile = await user_manager.get_user_by_id(user_id)
            preferences = user_profile.get("preferences", {})
            
            if not preferences.get("wake_up_calls", True):
                logger.info(f"Wake-up calls disabled for user {user_id}")
                return False
            
            # Schedule the wake-up call
            job_id = f"wakeup_call_{user_id}_{wakeup_time.timestamp()}"
            self.scheduler.add_job(
                func=self._make_wakeup_call,
                trigger=CronTrigger(
                    hour=wakeup_time.hour,
                    minute=wakeup_time.minute,
                    second=wakeup_time.second
                ),
                args=[user_id, phone_number, message],
                id=job_id,
                replace_existing=True,
                timezone="UTC"
            )
            
            # Store the scheduled wake-up call
            self.active_wakeup_calls[job_id] = {
                "user_id": user_id,
                "phone_number": phone_number,
                "wakeup_time": wakeup_time,
                "message": message,
                "status": "scheduled"
            }
            
            logger.info(f"Wake-up call scheduled for user {user_id} at {wakeup_time}")
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling wake-up call for user {user_id}: {e}")
            return False
    
    async def _make_wakeup_call(self, user_id: int, phone_number: str, message: str):
        """Make the actual wake-up call"""
        try:
            logger.info(f"Making wake-up call to user {user_id}")
            
            # Update status
            job_id = f"wakeup_call_{user_id}_{datetime.utcnow().timestamp()}"
            if job_id in self.active_wakeup_calls:
                self.active_wakeup_calls[job_id]["status"] = "calling"
            
            # Make the call
            call_result = await self.outbound_call_service.initiate_wakeup_call(
                user_id=user_id,
                target_phone=phone_number,
                message=message
            )
            
            if call_result:
                logger.info(f"Wake-up call initiated for user {user_id}")
                
                # Store proactive action
                await self.store_proactive_action(
                    str(user_id), "wakeup_call_made", f"Wake-up call made to {phone_number}", 
                    {"call_result": call_result}
                )
            else:
                logger.error(f"Failed to make wake-up call to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error making wake-up call to user {user_id}: {e}")
    
    async def generate_morning_digest(self, user_id: int) -> str:
        """
        Generate personalized morning digest for user
        
        Args:
            user_id: User identifier
            
        Returns:
            Personalized morning digest message
        """
        try:
            # Get full context
            context = await context_aggregator.get_full_context(user_id)
            
            # Get user style profile
            style_profile = await style_engine.get_user_style_profile(user_id)
            
            # Generate digest content
            digest_parts = []
            
            # Email summary
            email_status = context.get('email_status', {})
            if email_status.get('total_unread', 0) > 0:
                digest_parts.append(f"📧 {email_status['total_unread']} unread emails")
                if email_status.get('urgent_count', 0) > 0:
                    digest_parts.append(f"🚨 {email_status['urgent_count']} urgent")
            
            # Calendar summary
            calendar_status = context.get('calendar_status', {})
            if calendar_status.get('today_count', 0) > 0:
                digest_parts.append(f"📅 {calendar_status['today_count']} events today")
                if calendar_status.get('next_event'):
                    next_event = calendar_status['next_event']
                    digest_parts.append(f"⏰ Next: {next_event.get('title', 'Event')} at {next_event.get('start_time', 'Unknown time')}")
            
            # Reminder summary
            reminder_status = context.get('reminder_status', {})
            if reminder_status.get('active_count', 0) > 0:
                digest_parts.append(f"⏰ {reminder_status['active_count']} active reminders")
            
            # Habit suggestions
            habit_status = context.get('habit_status', {})
            if habit_status.get('suggestions'):
                suggestions = habit_status['suggestions'][:2]  # Top 2 suggestions
                for suggestion in suggestions:
                    digest_parts.append(f"🔄 {suggestion.get('message', 'Habit suggestion')}")
            
            # Generate base digest
            if digest_parts:
                base_digest = "Good morning! " + " | ".join(digest_parts) + "."
            else:
                base_digest = "Good morning! All clear, ready for a great day!"
            
            # Style-match the response
            styled_digest = await style_engine.generate_style_matched_response(
                user_id, base_digest, {"intent": "morning_digest"}
            )
            
            # Store proactive action
            await self.store_proactive_action(
                user_id, "morning_digest", styled_digest, {"context": context}
            )
            
            return styled_digest
            
        except Exception as e:
            logger.error(f"Error generating morning digest: {e}")
            return "Good morning! Ready to help you today."
    
    async def suggest_proactive_actions(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get intelligent proactive suggestions for user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of proactive action suggestions
        """
        try:
            suggestions = []
            
            # Get user context
            context = await context_aggregator.get_full_context(user_id)
            
            # Get user habits
            habits = await habit_engine.get_user_habits(user_id)
            
            # Check for urgent items that need attention
            priority_alerts = context.get('priority_alerts', [])
            for alert in priority_alerts:
                if alert.get('priority') == 'high':
                    suggestions.append({
                        'type': 'urgent_alert',
                        'priority': 'high',
                        'message': alert.get('message', 'Urgent action needed'),
                        'action': alert.get('action', 'check_status'),
                        'confidence': 0.9
                    })
            
            # Check for habit-based suggestions
            for habit in habits:
                if habit.get('next_predicted'):
                    next_time = datetime.fromisoformat(habit['next_predicted'])
                    time_until = (next_time - datetime.utcnow()).total_seconds() / 3600  # hours
                    
                    if 0 <= time_until <= 2:  # Due within 2 hours
                        suggestion = await self._generate_habit_suggestion(habit, time_until)
                        if suggestion:
                            suggestions.append(suggestion)
            
            # Check for email-based suggestions
            email_status = context.get('email_status', {})
            if email_status.get('urgent_count', 0) > 0:
                suggestions.append({
                    'type': 'email_priority',
                    'priority': 'high',
                    'message': f"You have {email_status['urgent_count']} urgent emails. Want me to summarize them?",
                    'action': 'summarize_emails',
                    'confidence': 0.8
                })
            
            # Check for calendar-based suggestions
            calendar_status = context.get('calendar_status', {})
            if calendar_status.get('conflict_count', 0) > 0:
                suggestions.append({
                    'type': 'calendar_conflict',
                    'priority': 'high',
                    'message': f"Calendar conflict detected! Want me to help resolve it?",
                    'action': 'resolve_conflicts',
                    'confidence': 0.8
                })
            
            # Sort by priority and confidence
            suggestions.sort(key=lambda x: (x.get('priority') == 'high', x.get('confidence', 0)), reverse=True)
            
            return suggestions[:5]  # Return top 5 suggestions
            
        except Exception as e:
            logger.error(f"Error getting proactive suggestions: {e}")
            return []
    
    async def _generate_habit_suggestion(self, habit: Dict[str, Any], time_until: float) -> Optional[Dict[str, Any]]:
        """Generate a suggestion based on a user habit"""
        try:
            pattern_type = habit.get('pattern_type', 'unknown')
            pattern_data = habit.get('pattern_data', {})
            
            if pattern_type == 'time_based':
                # Time-based habit (e.g., wake-up time)
                if 'wake_up' in str(pattern_data).lower() or 'alarm' in str(pattern_data).lower():
                    return {
                        'type': 'habit_reminder',
                        'priority': 'medium',
                        'message': f"You usually set a {pattern_data.get('time', '7AM')} wake-up. Want me to call you tomorrow?",
                        'action': 'schedule_wakeup',
                        'confidence': habit.get('confidence', 0.5),
                        'habit_id': habit.get('id')
                    }
            
            elif pattern_type == 'frequency_based':
                # Frequency-based habit (e.g., daily check-ins)
                return {
                    'type': 'habit_reminder',
                    'priority': 'medium',
                    'message': f"Time for your {pattern_data.get('action', 'habit')}?",
                    'action': 'execute_habit',
                    'confidence': habit.get('confidence', 0.5),
                    'habit_id': habit.get('id')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating habit suggestion: {e}")
            return None
    
    async def execute_proactive_action(
        self, 
        user_id: str, 
        action_type: str, 
        action_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a proactive action on behalf of the user
        
        Args:
            user_id: User identifier
            action_type: Type of action to execute
            action_data: Action-specific data
            
        Returns:
            Action execution result
        """
        try:
            result = {"success": False, "message": "", "action_type": action_type}
            
            if action_type == "morning_digest":
                result["message"] = await self.generate_morning_digest(user_id)
                result["success"] = True
            
            elif action_type == "schedule_wakeup":
                # Schedule wake-up call
                user_profile = await user_manager.get_user_by_id(int(user_id))
                phone_number = user_profile.get("phone_number")
                
                if phone_number:
                    # Default to 7 AM tomorrow if no time specified
                    wakeup_time = action_data.get('wakeup_time')
                    if not wakeup_time:
                        tomorrow = datetime.utcnow() + timedelta(days=1)
                        wakeup_time = tomorrow.replace(hour=7, minute=0, second=0, microsecond=0)
                    
                    success = await self.schedule_wakeup_call(
                        user_id=int(user_id),
                        phone_number=phone_number,
                        wakeup_time=wakeup_time
                    )
                    
                    if success:
                        result["message"] = f"Wake-up call scheduled for {wakeup_time.strftime('%I:%M %p')} tomorrow!"
                        result["success"] = True
                    else:
                        result["message"] = "Failed to schedule wake-up call. Check your preferences."
                else:
                    result["message"] = "Phone number not found for wake-up call."
            
            elif action_type == "summarize_emails":
                result["message"] = await self._summarize_urgent_emails(user_id)
                result["success"] = True
            
            elif action_type == "resolve_conflicts":
                result["message"] = await self._resolve_calendar_conflicts(user_id)
                result["success"] = True
            
            elif action_type == "execute_habit":
                result["message"] = await self._execute_user_habit(user_id, action_data)
                result["success"] = True
            
            elif action_type == "check_reminders":
                result["message"] = await self._check_overdue_reminders(user_id)
                result["success"] = True
            
            else:
                result["message"] = f"Unknown action type: {action_type}"
            
            # Store the action result
            await self.store_proactive_action(
                user_id, f"executed_{action_type}", result["message"], result
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing proactive action {action_type}: {e}")
            return {
                "success": False,
                "message": f"Error executing {action_type}: {str(e)}",
                "action_type": action_type
            }
    
    async def send_proactive_message(
        self, 
        user_id: str, 
        message: str, 
        priority: str = "medium",
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a proactive message to the user
        
        Args:
            user_id: User identifier
            message: Message to send
            priority: Message priority
            context: Optional context for style matching
            
        Returns:
            Success status
        """
        try:
            # Style-match the message
            styled_message = await style_engine.generate_style_matched_response(
                user_id, message, context
            )
            
            # Store the proactive message
            await self.store_proactive_action(
                user_id, "proactive_message", styled_message, {
                    "priority": priority,
                    "context": context,
                    "message_type": "proactive"
                }
            )
            
            # Get user phone number
            user_profile = await user_manager.get_user_by_id(int(user_id))
            phone_number = user_profile.get("phone_number")
            
            if phone_number and self.communication_service.sms_handler:
                await self.communication_service.sms_handler.send_sms(
                    to_phone=phone_number,
                    message=styled_message
                )
                logger.info(f"Proactive message sent to user {user_id}: {styled_message}")
                return True
            else:
                logger.warning(f"No SMS handler or phone number for user {user_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error sending proactive message: {e}")
            return False
    
    async def store_proactive_action(
        self, 
        user_id: str, 
        action_type: str, 
        message: str, 
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Store a proactive action in memory"""
        try:
            await memory_manager.store_memory(
                user_id=user_id,
                memory_type="proactive_action",
                content=message,
                metadata=metadata or {"action_type": action_type},
                importance_score=0.5
            )
        except Exception as e:
            logger.error(f"Error storing proactive action: {e}")
    
    async def _proactive_monitoring_loop(self):
        """Background loop for proactive monitoring"""
        while self.is_running:
            try:
                # Check for proactive opportunities
                await self._check_proactive_opportunities()
                
                # Wait before next check
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in proactive monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _check_proactive_opportunities(self):
        """Check for proactive opportunities across all users"""
        try:
            # Get all active users
            active_users = await user_manager.get_active_users()
            
            for user in active_users:
                try:
                    await self._check_user_proactive_opportunities(user["id"])
                except Exception as e:
                    logger.error(f"Error checking proactive opportunities for user {user['id']}: {e}")
                    
        except Exception as e:
            logger.error(f"Error checking proactive opportunities: {e}")
    
    async def _check_user_proactive_opportunities(self, user_id: int):
        """Check for proactive opportunities for a specific user"""
        try:
            # Get user context
            context = await context_aggregator.get_full_context(str(user_id))
            
            # Check for urgent items
            priority_alerts = context.get('priority_alerts', [])
            for alert in priority_alerts:
                if alert.get('priority') == 'high':
                    await self.send_proactive_message(
                        str(user_id),
                        alert.get('message', 'Urgent action needed'),
                        priority="high",
                        context={"alert": alert}
                    )
            
            # Check for habit reminders
            habit_status = context.get('habit_status', {})
            if habit_status.get('due_soon_count', 0) > 0:
                await self.send_proactive_message(
                    str(user_id),
                    f"You have {habit_status['due_soon_count']} habits due soon. Need help?",
                    priority="medium",
                    context={"habits": habit_status.get('due_soon', [])}
                )
            
        except Exception as e:
            logger.error(f"Error checking user proactive opportunities: {e}")
    
    async def _summarize_urgent_emails(self, user_id: str) -> str:
        """Summarize urgent emails for the user"""
        try:
            context = await context_aggregator.get_full_context(user_id)
            email_status = context.get('email_status', {})
            
            if not email_status.get('urgent_count', 0):
                return "No urgent emails to summarize."
            
            urgent_emails = email_status.get('recent_urgent', [])
            summary_parts = [f"You have {len(urgent_emails)} urgent emails:"]
            
            for email in urgent_emails[:3]:  # Top 3 urgent emails
                sender = email.get('sender', 'Unknown')
                subject = email.get('subject', 'No subject')
                summary_parts.append(f"• From {sender}: {subject}")
            
            if len(urgent_emails) > 3:
                summary_parts.append(f"And {len(urgent_emails) - 3} more urgent emails")
            
            return " ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error summarizing urgent emails: {e}")
            return "Unable to summarize emails at this time."
    
    async def _resolve_calendar_conflicts(self, user_id: str) -> str:
        """Help resolve calendar conflicts"""
        try:
            context = await context_aggregator.get_full_context(user_id)
            calendar_status = context.get('calendar_status', {})
            
            if not calendar_status.get('conflict_count', 0):
                return "No calendar conflicts to resolve."
            
            conflicts = calendar_status.get('conflicts', [])
            return f"Found {len(conflicts)} calendar conflicts. I can help you reschedule them. Which one should we tackle first?"
            
        except Exception as e:
            logger.error(f"Error resolving calendar conflicts: {e}")
            return "Unable to resolve calendar conflicts at this time."
    
    async def _execute_user_habit(self, user_id: str, action_data: Dict[str, Any]) -> str:
        """Execute a user habit"""
        try:
            habit_id = action_data.get('habit_id')
            if not habit_id:
                return "No habit specified to execute."
            
            # Get habit details
            habits = await habit_engine.get_user_habits(user_id)
            habit = next((h for h in habits if h.get('id') == habit_id), None)
            
            if not habit:
                return "Habit not found."
            
            # Execute the habit (this would vary based on habit type)
            habit_action = habit.get('pattern_data', {}).get('action', 'habit')
            
            # Store habit execution
            await memory_manager.store_memory(
                user_id=user_id,
                memory_type="habit_executed",
                content=f"Executed habit: {habit_action}",
                metadata={"habit_id": habit_id, "habit_data": habit},
                importance_score=0.6
            )
            
            return f"✅ Executed your habit: {habit_action}"
            
        except Exception as e:
            logger.error(f"Error executing user habit: {e}")
            return "Unable to execute habit at this time."
    
    async def _check_overdue_reminders(self, user_id: str) -> str:
        """Check for overdue reminders"""
        try:
            context = await context_aggregator.get_full_context(user_id)
            reminder_status = context.get('reminder_status', {})
            
            if not reminder_status.get('overdue_count', 0):
                return "No overdue reminders to check."
            
            overdue = reminder_status.get('overdue', [])
            summary_parts = [f"You have {len(overdue)} overdue reminders:"]
            
            for reminder in overdue[:3]:
                title = reminder.get('title', 'Unknown reminder')
                summary_parts.append(f"• {title}")
            
            if len(overdue) > 3:
                summary_parts.append(f"And {len(overdue) - 3} more overdue reminders")
            
            return " ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error checking overdue reminders: {e}")
            return "Unable to check reminders at this time."
    
    async def get_user_proactive_tasks(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all proactive tasks for a specific user"""
        try:
            tasks = []
            
            # Get scheduled tasks for this user
            if user_id in self.scheduled_tasks:
                for task_id, task_info in self.scheduled_tasks[user_id].items():
                    tasks.append({
                        "task_type": task_info.get("type", "unknown"),
                        "description": task_info.get("description", "No description"),
                        "next_run": task_info.get("next_run", "Unknown"),
                        "status": task_info.get("status", "unknown"),
                        "priority": task_info.get("priority", 5)
                    })
            
            # Get active wake-up calls
            if user_id in self.active_wakeup_calls:
                wakeup_info = self.active_wakeup_calls[user_id]
                tasks.append({
                    "task_type": "wake_up_call",
                    "description": f"Wake-up call at {wakeup_info.get('scheduled_time', 'Unknown')}",
                    "next_run": wakeup_info.get('scheduled_time', 'Unknown'),
                    "status": "active",
                    "priority": 10
                })
            
            # Get scheduled digest tasks
            digest_time = await self._get_user_digest_time(user_id)
            if digest_time:
                tasks.append({
                    "task_type": "morning_digest",
                    "description": "Daily morning digest",
                    "next_run": digest_time,
                    "status": "scheduled",
                    "priority": 3
                })
            
            # Get habit-based proactive tasks
            habits = await habit_engine.get_user_habits(user_id)
            for habit in habits:
                if habit.get("confidence", 0) > 0.7:  # High confidence habits
                    tasks.append({
                        "task_type": "habit_reminder",
                        "description": f"Reminder for habit: {habit.get('description', 'Unknown habit')}",
                        "next_run": habit.get("next_predicted", "Unknown"),
                        "status": "scheduled",
                        "priority": 4
                    })
            
            # Sort by priority (higher priority first)
            tasks.sort(key=lambda x: x.get("priority", 5), reverse=True)
            
            logger.info(f"Retrieved {len(tasks)} proactive tasks for user {user_id}")
            return tasks
            
        except Exception as e:
            logger.error(f"Error getting user proactive tasks: {e}")
            return []
    
    async def schedule_memory_reminder(
        self, 
        user_id: int, 
        memory_id: int, 
        content: str, 
        hours_from_now: int, 
        urgency_level: str
    ):
        """
        Schedule a reminder for a specific memory
        
        Args:
            user_id: User identifier
            memory_id: Memory ID to remind about
            content: Memory content
            hours_from_now: Hours from now to send reminder
            urgency_level: Urgency level for prioritization
        """
        try:
            # Calculate reminder time
            from datetime import datetime, timedelta
            reminder_time = datetime.now() + timedelta(hours=hours_from_now)
            
            # Create reminder task
            reminder_task = {
                "type": "memory_reminder",
                "user_id": user_id,
                "memory_id": memory_id,
                "content": content,
                "urgency_level": urgency_level,
                "scheduled_time": reminder_time.isoformat(),
                "status": "scheduled"
            }
            
            # Store in database
            db = await get_db_session()
            task = ProactiveTask(
                user_id=user_id,
                task_type="memory_reminder",
                task_data=reminder_task,
                scheduled_time=reminder_time,
                priority=urgency_level
            )
            db.add(task)
            await db.commit()
            
            logger.info(f"Scheduled memory reminder for user {user_id} at {reminder_time}")
            
        except Exception as e:
            logger.error(f"Error scheduling memory reminder: {e}")

    async def _send_memory_reminder(self, user_id: int, memory_id: int, content: str, urgency_level: str):
        """
        Send a memory reminder to the user
        
        Args:
            user_id: User identifier
            memory_id: Memory ID being reminded about
            content: Memory content
            urgency_level: Urgency level for message tone
        """
        try:
            # Get user phone number
            db = await get_db_session()
            user = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user.scalar_one_or_none()
            
            if not user or not user.phone_number:
                logger.error(f"No phone number found for user {user_id}")
                return
            
            # Create reminder message based on urgency
            urgency_emojis = {
                "critical": "🚨",
                "high": "⚠️", 
                "medium": "📝",
                "low": "💡"
            }
            
            urgency_prefix = urgency_emojis.get(urgency_level, "📝")
            
            message = f"{urgency_prefix} Reminder: {content}"
            
            # Add urgency context
            if urgency_level == "critical":
                message += "\n\nThis is marked as urgent - please address soon!"
            elif urgency_level == "high":
                message += "\n\nThis is important - consider addressing today."
            
            # Send SMS reminder
            from telephony.telephony_manager import TelephonyManager
            telephony_manager = TelephonyManager({})
            await telephony_manager.send_sms(
                to=user.phone_number,
                body=message,
                user_id=user_id
            )
            
            logger.info(f"Sent memory reminder to user {user_id}: {content}")
            
        except Exception as e:
            logger.error(f"Error sending memory reminder: {e}")

    async def _process_memory_reminders(self):
        """Process and send scheduled memory reminders"""
        try:
            db = await get_db_session()
            
            # Get due memory reminders
            from datetime import datetime
            now = datetime.now()
            
            due_reminders = await db.execute(
                select(ProactiveTask).where(
                    and_(
                        ProactiveTask.task_type == "memory_reminder",
                        ProactiveTask.scheduled_time <= now,
                        ProactiveTask.status == "scheduled"
                    )
                )
            )
            due_reminders = due_reminders.scalars().all()
            
            for reminder in due_reminders:
                try:
                    task_data = reminder.task_data
                    user_id = task_data.get("user_id")
                    memory_id = task_data.get("memory_id")
                    content = task_data.get("content")
                    urgency_level = task_data.get("urgency_level", "medium")
                    
                    # Send the reminder
                    await self._send_memory_reminder(user_id, memory_id, content, urgency_level)
                    
                    # Mark as completed
                    reminder.status = "completed"
                    await db.commit()
                    
                    logger.info(f"Processed memory reminder for user {user_id}")
                    
                except Exception as e:
                    logger.error(f"Error processing memory reminder {reminder.id}: {e}")
                    # Mark as failed
                    reminder.status = "failed"
                    await db.commit()
                    
        except Exception as e:
            logger.error(f"Error processing memory reminders: {e}")

    async def _get_user_digest_time(self, user_id: int) -> Optional[str]:
        """Get user's preferred digest time"""
        try:
            preferences = await memory_manager.get_user_preferences(user_id)
            digest_time = preferences.get("digest_time", "08:00")
            return digest_time
        except Exception as e:
            logger.warning(f"Error getting user digest time: {e}")
            return "08:00"  # Default time
    
    async def send_daily_digest(self, user_id: int) -> bool:
        """Send daily digest to user with reminders and calendar events"""
        try:
            db = await get_db_session()
            
            # Get user
            user = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user.scalar_one_or_none()
            
            if not user or not user.phone_number:
                logger.error(f"No phone number found for user {user_id}")
                return False
            
            # Get today's reminders
            from reminders.reminder_service import ReminderService
            reminder_service = ReminderService()
            today_reminders = await reminder_service.get_user_reminders(user_id, include_completed=False)
            
            # Filter for today's reminders
            today = datetime.now().date()
            today_reminders = [
                r for r in today_reminders 
                if r.reminder_time.date() == today and r.status == "pending"
            ]
            
            # Get today's calendar events
            from calendar_service.calendar_service import CalendarService
            calendar_service = CalendarService()
            today_events = await calendar_service.get_user_events_for_date(user_id, today)
            
            # Build digest message
            message = "📅 Today's Plan:\n\n"
            
            # Add reminders
            if today_reminders:
                message += "⏰ Reminders:\n"
                for i, reminder in enumerate(today_reminders[:5], 1):  # Limit to 5
                    time_str = reminder.reminder_time.strftime("%I:%M %p")
                    message += f"{i}) {reminder.title} at {time_str}\n"
                message += "\n"
            
            # Add calendar events
            if today_events:
                message += "📅 Events:\n"
                for i, event in enumerate(today_events[:5], 1):  # Limit to 5
                    time_str = event.start_time.strftime("%I:%M %p")
                    message += f"{i}) {event.title} at {time_str}\n"
                message += "\n"
            
            # Add action instructions
            if today_reminders or today_events:
                message += "💬 Reply with:\n"
                message += "• '#2 snooze 30m' to snooze reminder #2\n"
                message += "• 'move #3 to 6pm' to reschedule event #3\n"
                message += "• 'complete #1' to mark reminder #1 done"
            else:
                message += "✨ No scheduled items for today!"
            
            # Send digest
            from telephony.telephony_manager import TelephonyManager
            telephony_manager = TelephonyManager({})
            await telephony_manager.send_sms(
                to=user.phone_number,
                body=message,
                user_id=user_id
            )
            
            logger.info(f"Sent daily digest to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending daily digest to user {user_id}: {e}")
            return False


# Global proactive agent instance
proactive_agent = ProactiveAgent()

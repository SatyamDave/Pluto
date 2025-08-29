#!/usr/bin/env python3
"""
Pluto Context Aggregator
Aggregates real-time context from all sources for comprehensive user awareness
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict

from services.memory_manager import memory_manager
from services.habit_engine import habit_engine
from email_service.email_service import EmailService
from calendar_service.calendar_service import CalendarService
from reminders.reminder_service import ReminderService
from utils.logging_config import get_logger
from utils.constants import CACHE_TTL

logger = get_logger(__name__)

class ContextAggregator:
    """Pluto's context aggregator - provides comprehensive real-time context"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.calendar_service = CalendarService()
        self.reminder_service = ReminderService()
        self.context_cache = {}  # Simple in-memory cache
        self.cache_ttl = CACHE_TTL
    
    async def get_full_context(
        self, 
        user_id: str, 
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get comprehensive context for user
        
        Args:
            user_id: User identifier
            force_refresh: Force refresh of cached context
            
        Returns:
            Comprehensive context dictionary
        """
        try:
            # Check cache first
            cache_key = f"context:{user_id}"
            if not force_refresh and cache_key in self.context_cache:
                cached_context, timestamp = self.context_cache[cache_key]
                if (datetime.utcnow() - timestamp).seconds < self.cache_ttl:
                    logger.info(f"Returning cached context for user {user_id}")
                    return cached_context
            
            # Build comprehensive context
            context = await self._build_context(user_id)
            
            # Cache the result
            self.context_cache[cache_key] = (context, datetime.utcnow())
            
            # Store context snapshot
            await self._store_context_snapshot(user_id, context)
            
            logger.info(f"Generated fresh context for user {user_id}")
            return context
            
        except Exception as e:
            logger.error(f"Error getting full context for user {user_id}: {e}")
            return self._get_fallback_context(user_id)
    
    async def update_context_stream(
        self, 
        user_id: str, 
        source: str, 
        data: Any,
        importance_score: float = 0.5
    ):
        """
        Update context when new data arrives from any source
        
        Args:
            user_id: User identifier
            source: Data source (email, calendar, etc.)
            data: New data
            importance_score: Importance of the update
        """
        try:
            # Store in memory
            memory_id = await memory_manager.store_memory(
                user_id=user_id,
                memory_type=f"context_update_{source}",
                content=f"Context update from {source}: {json.dumps(data, default=str)}",
                metadata={"source": source, "data": data},
                importance_score=importance_score
            )
            
            # Invalidate cache for this user
            cache_key = f"context:{user_id}"
            if cache_key in self.context_cache:
                del self.context_cache[cache_key]
            
            # Check if this triggers proactive actions
            await self._check_proactive_triggers(user_id, source, data)
            
            logger.info(f"Updated context stream for user {user_id} from {source}")
            
        except Exception as e:
            logger.error(f"Error updating context stream: {e}")
    
    async def detect_context_changes(
        self, 
        user_id: str, 
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Detect significant context changes that require attention
        
        Args:
            user_id: User identifier
            hours_back: Hours to look back for changes
            
        Returns:
            List of significant context changes
        """
        try:
            changes = []
            
            # Get recent context updates
            recent_updates = await memory_manager.recall_memory(
                user_id=user_id,
                memory_type="context_update",
                hours_back=hours_back,
                limit=50
            )
            
            # Analyze for significant changes
            for update in recent_updates:
                change = await self._analyze_context_change(update)
                if change and change.get('significance') > 0.7:
                    changes.append(change)
            
            # Sort by significance
            changes.sort(key=lambda x: x.get('significance', 0), reverse=True)
            
            return changes[:10]  # Return top 10 most significant changes
            
        except Exception as e:
            logger.error(f"Error detecting context changes: {e}")
            return []
    
    async def get_context_summary(
        self, 
        user_id: str, 
        summary_type: str = "daily"
    ) -> str:
        """
        Get human-readable context summary
        
        Args:
            user_id: User identifier
            summary_type: Type of summary (daily, weekly, event_based)
            
        Returns:
            Human-readable summary string
        """
        try:
            context = await self.get_full_context(user_id)
            
            if summary_type == "daily":
                return await self._generate_daily_summary(context)
            elif summary_type == "weekly":
                return await self._generate_weekly_summary(context)
            elif summary_type == "event_based":
                return await self._generate_event_summary(context)
            else:
                return await self._generate_general_summary(context)
                
        except Exception as e:
            logger.error(f"Error generating context summary: {e}")
            return "Unable to generate context summary at this time."
    
    async def _build_context(self, user_id: str) -> Dict[str, Any]:
        """Build comprehensive context from all sources"""
        try:
            context = {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "recent_conversations": [],
                "email_status": {},
                "calendar_status": {},
                "reminder_status": {},
                "habit_status": {},
                "relationship_context": {},
                "priority_alerts": []
            }
            
            # Get recent conversations
            context["recent_conversations"] = await self._get_recent_conversations(user_id)
            
            # Get email status
            context["email_status"] = await self._get_email_status(user_id)
            
            # Get calendar status
            context["calendar_status"] = await self._get_calendar_status(user_id)
            
            # Get reminder status
            context["reminder_status"] = await self._get_reminder_status(user_id)
            
            # Get habit status
            context["habit_status"] = await self._get_habit_status(user_id)
            
            # Get relationship context
            context["relationship_context"] = await self._get_relationship_context(user_id)
            
            # Generate priority alerts
            context["priority_alerts"] = await self._generate_priority_alerts(context)
            
            return context
            
        except Exception as e:
            logger.error(f"Error building context: {e}")
            return {"error": str(e)}
    
    async def _get_recent_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recent conversation context"""
        try:
            recent_memories = await memory_manager.recall_memory(
                user_id=user_id,
                memory_type="sms",
                hours_back=24,
                limit=10
            )
            
            conversations = []
            for memory in recent_memories:
                conversations.append({
                    "type": memory.get("type"),
                    "content": memory.get("content", "")[:100],  # Truncate
                    "timestamp": memory.get("timestamp"),
                    "importance": memory.get("importance_score", 0.5)
                })
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error getting recent conversations: {e}")
            return []
    
    async def _get_email_status(self, user_id: str) -> Dict[str, Any]:
        """Get current email status"""
        try:
            # Get unread emails
            unread_emails = await self.email_service.get_unread_emails(user_id)
            
            # Analyze email priorities
            urgent_emails = []
            important_emails = []
            low_priority_emails = []
            
            for email in unread_emails:
                if email.get('is_important'):
                    urgent_emails.append(email)
                elif email.get('priority') == 'high':
                    important_emails.append(email)
                else:
                    low_priority_emails.append(email)
            
            return {
                "total_unread": len(unread_emails),
                "urgent_count": len(urgent_emails),
                "important_count": len(important_emails),
                "low_priority_count": len(low_priority_emails),
                "recent_urgent": urgent_emails[:3],
                "recent_important": important_emails[:3]
            }
            
        except Exception as e:
            logger.error(f"Error getting email status: {e}")
            return {"error": str(e)}
    
    async def _get_calendar_status(self, user_id: str) -> Dict[str, Any]:
        """Get current calendar status"""
        try:
            # Get upcoming events
            upcoming_events = await self.calendar_service.get_upcoming_events(user_id, hours_ahead=24)
            
            # Get today's events
            today_events = await self.calendar_service.get_today_events(user_id)
            
            # Check for conflicts
            conflicts = await self._detect_calendar_conflicts(upcoming_events)
            
            return {
                "upcoming_count": len(upcoming_events),
                "today_count": len(today_events),
                "conflict_count": len(conflicts),
                "next_event": upcoming_events[0] if upcoming_events else None,
                "conflicts": conflicts[:3]
            }
            
        except Exception as e:
            logger.error(f"Error getting calendar status: {e}")
            return {"error": str(e)}
    
    async def _get_reminder_status(self, user_id: str) -> Dict[str, Any]:
        """Get current reminder status"""
        try:
            # Get active reminders
            active_reminders = await self.reminder_service.get_active_reminders(user_id)
            
            # Get overdue reminders
            overdue_reminders = await self.reminder_service.get_overdue_reminders(user_id)
            
            # Get upcoming reminders
            upcoming_reminders = await self.reminder_service.get_upcoming_reminders(user_id, hours_ahead=6)
            
            return {
                "active_count": len(active_reminders),
                "overdue_count": len(overdue_reminders),
                "upcoming_count": len(upcoming_reminders),
                "overdue": overdue_reminders[:3],
                "upcoming": upcoming_reminders[:3]
            }
            
        except Exception as e:
            logger.error(f"Error getting reminder status: {e}")
            return {"error": str(e)}
    
    async def _get_habit_status(self, user_id: str) -> Dict[str, Any]:
        """Get current habit status"""
        try:
            # Get user habits
            habits = await habit_engine.get_user_habits(user_id)
            
            # Get habits due soon
            due_soon_habits = []
            for habit in habits:
                if habit.get('next_predicted'):
                    next_time = datetime.fromisoformat(habit['next_predicted'])
                    if next_time <= datetime.utcnow() + timedelta(hours=2):
                        due_soon_habits.append(habit)
            
            # Get habit suggestions
            suggestions = await habit_engine.suggest_proactive_actions(user_id)
            
            return {
                "total_habits": len(habits),
                "due_soon_count": len(due_soon_habits),
                "due_soon": due_soon_habits[:3],
                "suggestions": suggestions[:3]
            }
            
        except Exception as e:
            logger.error(f"Error getting habit status: {e}")
            return {"error": str(e)}
    
    async def _get_relationship_context(self, user_id: str) -> Dict[str, Any]:
        """Get relationship context"""
        try:
            # Get recent interactions with contacts
            recent_contacts = await memory_manager.recall_memory(
                user_id=user_id,
                memory_type="contact_interaction",
                hours_back=24 * 7,  # Last week
                limit=20
            )
            
            # Group by contact
            contact_interactions = defaultdict(list)
            for interaction in recent_contacts:
                contact = interaction.get('context_data', {}).get('contact_name', 'Unknown')
                contact_interactions[contact].append(interaction)
            
            # Get top contacts
            top_contacts = sorted(
                contact_interactions.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:5]
            
            return {
                "recent_contacts": len(contact_interactions),
                "top_contacts": [
                    {
                        "name": contact,
                        "interaction_count": len(interactions),
                        "last_interaction": interactions[0].get('timestamp') if interactions else None
                    }
                    for contact, interactions in top_contacts
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting relationship context: {e}")
            return {"error": str(e)}
    
    async def _generate_priority_alerts(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate priority alerts based on context"""
        alerts = []
        
        try:
            # Email alerts
            email_status = context.get('email_status', {})
            if email_status.get('urgent_count', 0) > 0:
                alerts.append({
                    "type": "urgent_email",
                    "priority": "high",
                    "message": f"You have {email_status['urgent_count']} urgent emails",
                    "action": "check_inbox"
                })
            
            # Calendar alerts
            calendar_status = context.get('calendar_status', {})
            if calendar_status.get('conflict_count', 0) > 0:
                alerts.append({
                    "type": "calendar_conflict",
                    "priority": "high",
                    "message": f"Calendar conflict detected: {calendar_status['conflict_count']} overlapping events",
                    "action": "resolve_conflicts"
                })
            
            # Reminder alerts
            reminder_status = context.get('reminder_status', {})
            if reminder_status.get('overdue_count', 0) > 0:
                alerts.append({
                    "type": "overdue_reminder",
                    "priority": "medium",
                    "message": f"You have {reminder_status['overdue_count']} overdue reminders",
                    "action": "check_reminders"
                })
            
            # Habit alerts
            habit_status = context.get('habit_status', {})
            if habit_status.get('due_soon_count', 0) > 0:
                alerts.append({
                    "type": "habit_due",
                    "priority": "medium",
                    "message": f"{habit_status['due_soon_count']} habits due soon",
                    "action": "check_habits"
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating priority alerts: {e}")
            return []
    
    async def _detect_calendar_conflicts(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect calendar conflicts in events"""
        try:
            conflicts = []
            
            # Sort events by start time
            sorted_events = sorted(events, key=lambda x: x.get('start_time', datetime.min))
            
            for i in range(len(sorted_events) - 1):
                current_event = sorted_events[i]
                next_event = sorted_events[i + 1]
                
                current_end = current_event.get('end_time')
                next_start = next_event.get('start_time')
                
                if current_end and next_start and current_end > next_start:
                    conflicts.append({
                        'title': f"{current_event.get('title')} vs {next_event.get('title')}",
                        'start_time': next_start,
                        'conflict_type': 'overlap'
                    })
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Error detecting calendar conflicts: {e}")
            return []
    
    async def _check_proactive_triggers(
        self, 
        user_id: str, 
        source: str, 
        data: Any
    ):
        """Check if context update triggers proactive actions"""
        try:
            # Check for urgent emails
            if source == "email" and data.get('is_important'):
                await self._trigger_urgent_email_alert(user_id, data)
            
            # Check for calendar conflicts
            if source == "calendar" and data.get('conflict_detected'):
                await self._trigger_calendar_conflict_alert(user_id, data)
            
            # Check for overdue reminders
            if source == "reminder" and data.get('is_overdue'):
                await self._trigger_overdue_reminder_alert(user_id, data)
            
        except Exception as e:
            logger.error(f"Error checking proactive triggers: {e}")
    
    async def _trigger_urgent_email_alert(self, user_id: str, email_data: Dict[str, Any]):
        """Trigger alert for urgent email"""
        try:
            # Store proactive action
            await memory_manager.store_memory(
                user_id=user_id,
                memory_type="proactive_alert",
                content=f"Urgent email alert: {email_data.get('subject', 'No subject')}",
                metadata={
                    "alert_type": "urgent_email",
                    "email_data": email_data,
                    "action_required": True
                },
                importance_score=0.9
            )
            
            logger.info(f"Triggered urgent email alert for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error triggering urgent email alert: {e}")
    
    async def _trigger_calendar_conflict_alert(self, user_id: str, conflict_data: Dict[str, Any]):
        """Trigger alert for calendar conflict"""
        try:
            await memory_manager.store_memory(
                user_id=user_id,
                memory_type="proactive_alert",
                content=f"Calendar conflict detected: {conflict_data.get('title', 'Unknown conflict')}",
                metadata={
                    "alert_type": "calendar_conflict",
                    "conflict_data": conflict_data,
                    "action_required": True
                },
                importance_score=0.8
            )
            
            logger.info(f"Triggered calendar conflict alert for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error triggering calendar conflict alert: {e}")
    
    async def _trigger_overdue_reminder_alert(self, user_id: str, reminder_data: Dict[str, Any]):
        """Trigger alert for overdue reminder"""
        try:
            await memory_manager.store_memory(
                user_id=user_id,
                memory_type="proactive_alert",
                content=f"Overdue reminder: {reminder_data.get('title', 'Unknown reminder')}",
                metadata={
                    "alert_type": "overdue_reminder",
                    "reminder_data": reminder_data,
                    "action_required": True
                },
                importance_score=0.7
            )
            
            logger.info(f"Triggered overdue reminder alert for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error triggering overdue reminder alert: {e}")
    
    async def _analyze_context_change(self, update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze the significance of a context change"""
        try:
            content = update.get('content', '')
            metadata = update.get('context_data', {})
            
            # Calculate significance based on various factors
            significance = 0.5  # Base significance
            
            # Source importance
            source = metadata.get('source', '')
            if source in ['email', 'calendar']:
                significance += 0.2
            elif source in ['reminder', 'habit']:
                significance += 0.1
            
            # Data importance
            if metadata.get('is_important'):
                significance += 0.3
            if metadata.get('priority') == 'high':
                significance += 0.2
            
            # Content length (longer content might be more significant)
            if len(content) > 100:
                significance += 0.1
            
            return {
                "id": update.get('id'),
                "type": update.get('type'),
                "significance": min(1.0, significance),
                "source": source,
                "timestamp": update.get('timestamp'),
                "action_required": metadata.get('action_required', False)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing context change: {e}")
            return None
    
    async def _store_context_snapshot(self, user_id: str, context: Dict[str, Any]):
        """Store context snapshot for historical analysis"""
        try:
            # Generate summary
            summary = await self._generate_context_summary_text(context)
            
            # Store snapshot
            await memory_manager.store_memory(
                user_id=user_id,
                memory_type="context_snapshot",
                content=f"Context snapshot: {summary}",
                metadata={
                    "snapshot_type": "daily",
                    "context_summary": context,
                    "summary_text": summary
                },
                importance_score=0.4
            )
            
        except Exception as e:
            logger.error(f"Error storing context snapshot: {e}")
    
    async def _generate_context_summary_text(self, context: Dict[str, Any]) -> str:
        """Generate human-readable context summary"""
        try:
            summary_parts = []
            
            # Email summary
            email_status = context.get('email_status', {})
            if email_status.get('urgent_count', 0) > 0:
                summary_parts.append(f"{email_status['urgent_count']} urgent emails")
            
            # Calendar summary
            calendar_status = context.get('calendar_status', {})
            if calendar_status.get('upcoming_count', 0) > 0:
                summary_parts.append(f"{calendar_status['upcoming_count']} upcoming events")
            
            # Reminder summary
            reminder_status = context.get('reminder_status', {})
            if reminder_status.get('overdue_count', 0) > 0:
                summary_parts.append(f"{reminder_status['overdue_count']} overdue reminders")
            
            if summary_parts:
                return f"Context: {', '.join(summary_parts)}"
            else:
                return "Context: All clear, no urgent items"
                
        except Exception as e:
            logger.error(f"Error generating context summary text: {e}")
            return "Context summary unavailable"
    
    async def _generate_daily_summary(self, context: Dict[str, Any]) -> str:
        """Generate daily context summary"""
        try:
            summary_parts = []
            
            # Email summary
            email_status = context.get('email_status', {})
            if email_status.get('total_unread', 0) > 0:
                summary_parts.append(f"📧 {email_status['total_unread']} unread emails")
                if email_status.get('urgent_count', 0) > 0:
                    summary_parts.append(f"🚨 {email_status['urgent_count']} urgent")
            
            # Calendar summary
            calendar_status = context.get('calendar_status', {})
            if calendar_status.get('today_count', 0) > 0:
                summary_parts.append(f"📅 {calendar_status['today_count']} events today")
            
            # Reminder summary
            reminder_status = context.get('reminder_status', {})
            if reminder_status.get('active_count', 0) > 0:
                summary_parts.append(f"⏰ {reminder_status['active_count']} active reminders")
            
            if summary_parts:
                return "Daily Summary: " + " | ".join(summary_parts)
            else:
                return "Daily Summary: All clear, have a great day!"
                
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
            return "Unable to generate daily summary"
    
    async def _generate_weekly_summary(self, context: Dict[str, Any]) -> str:
        """Generate weekly context summary"""
        try:
            # This would aggregate data from the past week
            return "Weekly summary feature coming soon!"
        except Exception as e:
            logger.error(f"Error generating weekly summary: {e}")
            return "Unable to generate weekly summary"
    
    async def _generate_event_summary(self, context: Dict[str, Any]) -> str:
        """Generate event-based context summary"""
        try:
            # This would focus on specific events or time periods
            return "Event summary feature coming soon!"
        except Exception as e:
            logger.error(f"Error generating event summary: {e}")
            return "Unable to generate event summary"
    
    async def _generate_general_summary(self, context: Dict[str, Any]) -> str:
        """Generate general context summary"""
        try:
            return await self._generate_daily_summary(context)
        except Exception as e:
            logger.error(f"Error generating general summary: {e}")
            return "Unable to generate summary"
    
    def _get_fallback_context(self, user_id: str) -> Dict[str, Any]:
        """Get fallback context when main context generation fails"""
        return {
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "error": "Context generation failed, using fallback",
            "recent_conversations": [],
            "email_status": {"error": "Service unavailable"},
            "calendar_status": {"error": "Service unavailable"},
            "reminder_status": {"error": "Service unavailable"},
            "habit_status": {"error": "Service unavailable"},
            "relationship_context": {"error": "Service unavailable"},
            "priority_alerts": []
        }

# Global context aggregator instance
context_aggregator = ContextAggregator()

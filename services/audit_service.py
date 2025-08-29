"""
Audit Service for Jarvis Phone AI Assistant
Logs all AI actions and provides daily summaries for transparency
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, date
from dataclasses import dataclass
from enum import Enum

from config import settings
from telephony.twilio_handler import TwilioHandler
from telephony.telnyx_handler import TelnyxHandler
from config import get_telephony_provider, is_twilio_enabled, is_telnyx_enabled

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of AI actions"""
    # Communication
    SMS_SENT = "sms_sent"
    EMAIL_SENT = "email_sent"
    EMAIL_REPLY = "email_reply"
    AUTO_REPLY = "auto_reply"
    SLACK_MESSAGE = "slack_message"
    DISCORD_MESSAGE = "discord_message"
    
    # Reminders & Calendar
    REMINDER_CREATED = "reminder_created"
    REMINDER_SENT = "reminder_sent"
    WAKEUP_CALL = "wakeup_call"
    CALENDAR_CHECK = "calendar_check"
    CONFLICT_DETECTED = "conflict_detected"
    
    # Outbound Calls
    OUTBOUND_CALL_INITIATED = "outbound_call_initiated"
    OUTBOUND_CALL_COMPLETED = "outbound_call_completed"
    OUTBOUND_CALL_FAILED = "outbound_call_failed"
    
    # Proactive Actions
    INBOX_MONITORED = "inbox_monitored"
    LOW_PRIORITY_EMAILS = "low_priority_emails_processed"
    DAILY_DIGEST_SENT = "daily_digest_sent"
    
    # Notes & Tasks
    NOTE_CREATED = "note_created"
    NOTE_UPDATED = "note_updated"
    TASK_ADDED = "task_added"
    TASK_COMPLETED = "task_completed"


class ActionStatus(Enum):
    """Status of AI actions"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    CANCELLED = "cancelled"


@dataclass
class AuditLogEntry:
    """Individual audit log entry"""
    id: Optional[int] = None
    user_id: int = 0
    action_type: ActionType = ActionType.SMS_SENT
    action_description: str = ""
    status: ActionStatus = ActionStatus.SUCCESS
    details: Dict[str, Any] = None
    timestamp: datetime = None
    cost_estimate: Optional[float] = None
    ai_model_used: Optional[str] = None
    execution_time_ms: Optional[int] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.details is None:
            self.details = {}


@dataclass
class DailySummary:
    """Daily summary of AI actions for a user"""
    user_id: int
    date: date
    total_actions: int
    successful_actions: int
    failed_actions: int
    action_breakdown: Dict[str, int]
    cost_estimate: float
    time_saved_minutes: int
    summary_text: str


class AuditService:
    """Service for logging and auditing AI actions"""
    
    def __init__(self):
        self.telephony_provider = get_telephony_provider()
        
        # Initialize telephony handler for sending summaries
        if self.telephony_provider == "twilio" and is_twilio_enabled():
            self.sms_handler = TwilioHandler()
        elif self.telephony_provider == "telnyx" and is_telnyx_enabled():
            self.sms_handler = TelnyxHandler()
        else:
            logger.warning("No valid telephony provider configured for audit SMS")
            self.sms_handler = None
    
    async def log_action(
        self,
        user_id: int,
        action_type: ActionType,
        action_description: str,
        status: ActionStatus = ActionStatus.SUCCESS,
        details: Optional[Dict[str, Any]] = None,
        cost_estimate: Optional[float] = None,
        ai_model_used: Optional[str] = None,
        execution_time_ms: Optional[int] = None
    ) -> bool:
        """Log an AI action for audit purposes"""
        try:
            # Create audit log entry
            log_entry = AuditLogEntry(
                user_id=user_id,
                action_type=action_type,
                action_description=action_description,
                status=status,
                details=details or {},
                cost_estimate=cost_estimate,
                ai_model_used=ai_model_used,
                execution_time_ms=execution_time_ms
            )
            
            # Store in database (this would go to an audit_logs table)
            await self._store_audit_log(log_entry)
            
            # Log to application logs
            logger.info(f"AI Action Logged: User {user_id} - {action_type.value}: {action_description} - {status.value}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging audit action: {e}")
            return False
    
    async def get_user_actions(
        self, 
        user_id: int, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        action_types: Optional[List[ActionType]] = None
    ) -> List[AuditLogEntry]:
        """Get audit log entries for a specific user"""
        try:
            # This would query the audit_logs database table
            # For now, return a placeholder
            return []
            
        except Exception as e:
            logger.error(f"Error getting user actions: {e}")
            return []
    
    async def generate_daily_summary(self, user_id: int, target_date: Optional[date] = None) -> DailySummary:
        """Generate daily summary of AI actions for a user"""
        try:
            if target_date is None:
                target_date = date.today()
            
            # Get actions for the day
            actions = await self.get_user_actions(
                user_id=user_id,
                start_date=target_date,
                end_date=target_date
            )
            
            # Calculate summary statistics
            total_actions = len(actions)
            successful_actions = len([a for a in actions if a.status == ActionStatus.SUCCESS])
            failed_actions = len([a for a in actions if a.status == ActionStatus.FAILED])
            
            # Action breakdown by type
            action_breakdown = {}
            for action in actions:
                action_type = action.action_type.value
                action_breakdown[action_type] = action_breakdown.get(action_type, 0) + 1
            
            # Calculate cost estimate
            total_cost = sum(a.cost_estimate or 0 for a in actions)
            
            # Estimate time saved (based on action types)
            time_saved_minutes = self._estimate_time_saved(actions)
            
            # Generate summary text
            summary_text = self._generate_summary_text(actions, action_breakdown, time_saved_minutes)
            
            return DailySummary(
                user_id=user_id,
                date=target_date,
                total_actions=total_actions,
                successful_actions=successful_actions,
                failed_actions=failed_actions,
                action_breakdown=action_breakdown,
                cost_estimate=total_cost,
                time_saved_minutes=time_saved_minutes,
                summary_text=summary_text
            )
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
            # Return empty summary
            return DailySummary(
                user_id=user_id,
                date=target_date or date.today(),
                total_actions=0,
                successful_actions=0,
                failed_actions=0,
                action_breakdown={},
                cost_estimate=0.0,
                time_saved_minutes=0,
                summary_text="Unable to generate summary at this time."
            )
    
    async def send_daily_summary_sms(self, user_id: int, user_phone: str, target_date: Optional[date] = None) -> bool:
        """Send daily summary via SMS"""
        try:
            if not self.sms_handler:
                logger.error("No SMS handler available for sending daily summary")
                return False
            
            # Generate summary
            summary = await self.generate_daily_summary(user_id, target_date)
            
            # Format SMS message
            message = self._format_summary_sms(summary)
            
            # Send SMS
            await self.sms_handler.send_sms(user_phone, message)
            
            logger.info(f"Daily summary SMS sent to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending daily summary SMS: {e}")
            return False
    
    async def get_user_analytics(
        self, 
        user_id: int, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics for a user over a period of time"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # Get actions for the period
            actions = await self.get_user_actions(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Calculate analytics
            total_actions = len(actions)
            successful_actions = len([a for a in actions if a.status == ActionStatus.SUCCESS])
            failed_actions = len([a for a in actions if a.status == ActionStatus.FAILED])
            
            # Action type distribution
            action_distribution = {}
            for action in actions:
                action_type = action.action_type.value
                action_distribution[action_type] = action_distribution.get(action_type, 0) + 1
            
            # Cost analysis
            total_cost = sum(a.cost_estimate or 0 for a in actions)
            avg_cost_per_action = total_cost / total_actions if total_actions > 0 else 0
            
            # Time saved analysis
            total_time_saved = sum(self._estimate_time_saved([a]) for a in actions)
            
            # Daily averages
            daily_avg_actions = total_actions / days
            daily_avg_cost = total_cost / days
            daily_avg_time_saved = total_time_saved / days
            
            return {
                "period_days": days,
                "total_actions": total_actions,
                "successful_actions": successful_actions,
                "failed_actions": failed_actions,
                "success_rate": (successful_actions / total_actions * 100) if total_actions > 0 else 0,
                "action_distribution": action_distribution,
                "cost_analysis": {
                    "total_cost": total_cost,
                    "avg_cost_per_action": avg_cost_per_action,
                    "daily_avg_cost": daily_avg_cost
                },
                "time_saved_analysis": {
                    "total_time_saved_minutes": total_time_saved,
                    "daily_avg_time_saved": daily_avg_time_saved
                },
                "daily_averages": {
                    "actions": daily_avg_actions,
                    "cost": daily_avg_cost,
                    "time_saved": daily_avg_time_saved
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
            return {"error": str(e)}
    
    def _estimate_time_saved(self, actions: List[AuditLogEntry]) -> int:
        """Estimate time saved based on action types"""
        try:
            time_saved = 0
            
            for action in actions:
                action_type = action.action_type
                
                # Time savings estimates (in minutes)
                if action_type == ActionType.EMAIL_REPLY:
                    time_saved += 5  # 5 minutes to draft and send email
                elif action_type == ActionType.SMS_SENT:
                    time_saved += 2  # 2 minutes to send SMS
                elif action_type == ActionType.REMINDER_CREATED:
                    time_saved += 1  # 1 minute to set reminder
                elif action_type == ActionType.OUTBOUND_CALL_COMPLETED:
                    time_saved += 15  # 15 minutes for phone call
                elif action_type == ActionType.INBOX_MONITORED:
                    time_saved += 10  # 10 minutes to check inbox
                elif action_type == ActionType.AUTO_REPLY:
                    time_saved += 3   # 3 minutes to reply to email
                elif action_type == ActionType.CONFLICT_DETECTED:
                    time_saved += 8   # 8 minutes to resolve calendar conflict
            
            return time_saved
            
        except Exception as e:
            logger.error(f"Error estimating time saved: {e}")
            return 0
    
    def _generate_summary_text(
        self, 
        actions: List[AuditLogEntry], 
        action_breakdown: Dict[str, int],
        time_saved_minutes: int
    ) -> str:
        """Generate human-readable summary text"""
        try:
            if not actions:
                return "No AI actions taken today."
            
            summary_parts = []
            
            # Action count
            total_actions = len(actions)
            summary_parts.append(f"Today I completed {total_actions} tasks for you")
            
            # Highlight key actions
            if action_breakdown.get("email_reply", 0) > 0:
                summary_parts.append(f"replied to {action_breakdown['email_reply']} emails")
            
            if action_breakdown.get("sms_sent", 0) > 0:
                summary_parts.append(f"sent {action_breakdown['sms_sent']} text messages")
            
            if action_breakdown.get("reminder_sent", 0) > 0:
                summary_parts.append(f"sent {action_breakdown['reminder_sent']} reminders")
            
            if action_breakdown.get("outbound_call_completed", 0) > 0:
                summary_parts.append(f"completed {action_breakdown['outbound_call_completed']} phone calls")
            
            # Time saved
            if time_saved_minutes > 0:
                summary_parts.append(f"and saved you approximately {time_saved_minutes} minutes")
            
            # Join parts
            summary = ", ".join(summary_parts) + "."
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary text: {e}")
            return "Summary generated with some information."
    
    def _format_summary_sms(self, summary: DailySummary) -> str:
        """Format daily summary for SMS transmission"""
        try:
            message = f"📊 Daily AI Summary - {summary.date.strftime('%b %d')}\n\n"
            
            # Action summary
            message += f"✅ Completed: {summary.successful_actions} tasks\n"
            if summary.failed_actions > 0:
                message += f"❌ Failed: {summary.failed_actions} tasks\n"
            
            # Time saved
            if summary.time_saved_minutes > 0:
                message += f"⏰ Time saved: ~{summary.time_saved_minutes} minutes\n"
            
            # Cost estimate
            if summary.cost_estimate > 0:
                message += f"💰 Estimated cost: ${summary.cost_estimate:.2f}\n"
            
            # Key actions
            if summary.action_breakdown:
                message += "\n🔍 Key actions:\n"
                for action_type, count in list(summary.action_breakdown.items())[:3]:
                    action_name = action_type.replace("_", " ").title()
                    message += f"• {action_name}: {count}\n"
            
            # Footer
            message += "\nReply 'details' for full report or 'call me' to discuss."
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting summary SMS: {e}")
            return f"Daily Summary: {summary.summary_text}"
    
    async def _store_audit_log(self, log_entry: AuditLogEntry):
        """Store audit log entry in database"""
        try:
            # This would save to an audit_logs table
            # For now, just log it
            logger.debug(f"Storing audit log: {log_entry.action_type.value} for user {log_entry.user_id}")
            
        except Exception as e:
            logger.error(f"Error storing audit log: {e}")
    
    async def cleanup_old_logs(self, days_to_keep: int = 90):
        """Clean up old audit logs to save storage"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # This would delete old logs from the database
            # For now, just log the cleanup
            logger.info(f"Cleaning up audit logs older than {days_to_keep} days (before {cutoff_date})")
            
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")

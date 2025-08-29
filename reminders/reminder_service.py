"""
Reminder service for Jarvis Phone AI Assistant
Handles scheduling, storing, and sending reminders
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from db.database import get_db
from db.models import Reminder, User
from telephony.twilio_handler import TwilioHandler
from telephony.telnyx_handler import TelnyxHandler
from config import get_telephony_provider, is_twilio_enabled, is_telnyx_enabled, is_persistent_wakeup_enabled, settings

logger = logging.getLogger(__name__)


class ReminderService:
    """Service for managing reminders and wake-up calls"""
    
    def __init__(self):
        self.telephony_provider = get_telephony_provider()
    
    async def create_reminder(
        self,
        user_id: int,
        title: str,
        reminder_time: str,
        description: Optional[str] = None,
        reminder_type: str = "sms"
    ) -> Reminder:
        """Create a new reminder"""
        try:
            # Parse the reminder time
            if isinstance(reminder_time, str):
                reminder_datetime = datetime.fromisoformat(reminder_time.replace('Z', '+00:00'))
            else:
                reminder_datetime = reminder_time
            
            # Create reminder record
            reminder = Reminder(
                user_id=user_id,
                title=title,
                description=description,
                reminder_time=reminder_datetime,
                reminder_type=reminder_type,
                status="pending"
            )
            
            # Save to database
            db = await get_db()
            db.add(reminder)
            await db.commit()
            await db.refresh(reminder)
            
            logger.info(f"Created reminder '{title}' for user {user_id} at {reminder_datetime}")
            
            # Schedule the reminder
            await self._schedule_reminder(reminder)
            
            return reminder
            
        except Exception as e:
            logger.error(f"Error creating reminder: {e}")
            raise
    
    async def get_user_reminders(
        self, 
        user_id: int, 
        include_completed: bool = False
    ) -> List[Reminder]:
        """Get all reminders for a user"""
        try:
            db = await get_db()
            
            query = select(Reminder).where(Reminder.user_id == user_id)
            
            if not include_completed:
                query = query.where(Reminder.is_completed == False)
            
            query = query.order_by(Reminder.reminder_time)
            
            result = await db.execute(query)
            reminders = result.scalars().all()
            
            return reminders
            
        except Exception as e:
            logger.error(f"Error getting user reminders: {e}")
            raise
    
    async def get_pending_reminders(self) -> List[Reminder]:
        """Get all pending reminders that are due"""
        try:
            db = await get_db()
            
            now = datetime.utcnow()
            
            query = select(Reminder).where(
                and_(
                    Reminder.status == "pending",
                    Reminder.reminder_time <= now,
                    Reminder.is_completed == False
                )
            )
            
            result = await db.execute(query)
            reminders = result.scalars().all()
            
            return reminders
            
        except Exception as e:
            logger.error(f"Error getting pending reminders: {e}")
            raise
    
    async def mark_reminder_completed(self, reminder_id: int) -> bool:
        """Mark a reminder as completed"""
        try:
            db = await get_db()
            
            query = select(Reminder).where(Reminder.id == reminder_id)
            result = await db.execute(query)
            reminder = result.scalar_one_or_none()
            
            if reminder:
                reminder.is_completed = True
                reminder.status = "completed"
                await db.commit()
                
                logger.info(f"Marked reminder {reminder_id} as completed")
                return True
            else:
                logger.warning(f"Reminder {reminder_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Error marking reminder completed: {e}")
            raise
    
    async def _schedule_reminder(self, reminder: Reminder):
        """Schedule a reminder to be sent at the specified time"""
        try:
            # Calculate delay until reminder time
            now = datetime.utcnow()
            delay = (reminder.reminder_time - now).total_seconds()
            
            if delay > 0:
                # Schedule the reminder
                asyncio.create_task(
                    self._send_reminder_after_delay(reminder.id, delay)
                )
                logger.info(f"Scheduled reminder {reminder.id} for {delay} seconds from now")
            else:
                # Reminder is already due, send immediately
                await self._send_reminder(reminder.id)
                
        except Exception as e:
            logger.error(f"Error scheduling reminder: {e}")
            raise
    
    async def _send_reminder_after_delay(self, reminder_id: int, delay: float):
        """Send reminder after specified delay"""
        try:
            await asyncio.sleep(delay)
            await self._send_reminder(reminder_id)
        except Exception as e:
            logger.error(f"Error in delayed reminder {reminder_id}: {e}")
    
    async def _send_reminder(self, reminder_id: int):
        """Send a reminder via SMS and/or voice call"""
        try:
            db = await get_db()
            
            # Get reminder details
            query = select(Reminder).where(Reminder.id == reminder_id)
            result = await db.execute(query)
            reminder = result.scalar_one_or_none()
            
            if not reminder:
                logger.warning(f"Reminder {reminder_id} not found")
                return
            
            # Get user details
            user_query = select(User).where(User.id == reminder.user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"User {reminder.user_id} not found")
                return
            
            # Send reminder based on type
            success = False
            
            if reminder.reminder_type in ["sms", "both"]:
                success = await self._send_sms_reminder(user, reminder)
            
            if reminder.reminder_type in ["call", "both"]:
                success = await self._send_voice_reminder(user, reminder) or success
            
            # Update reminder status
            if success:
                reminder.status = "sent"
                reminder.retry_count += 1
            else:
                reminder.status = "failed"
                reminder.retry_count += 1
                
                # Retry logic
                if reminder.retry_count < reminder.max_retries:
                    # Schedule retry in 5 minutes
                    asyncio.create_task(
                        self._send_reminder_after_delay(reminder_id, 300)
                    )
                    reminder.status = "pending"
            
            await db.commit()
            
            logger.info(f"Reminder {reminder_id} sent with status: {reminder.status}")
            
        except Exception as e:
            logger.error(f"Error sending reminder {reminder_id}: {e}")
            raise
    
    async def _send_sms_reminder(self, user: User, reminder: Reminder) -> bool:
        """Send SMS reminder"""
        try:
            message = f"🔔 Reminder: {reminder.title}"
            if reminder.description:
                message += f"\n{reminder.description}"
            
            # Send SMS based on configured provider
            if self.telephony_provider == "twilio" and is_twilio_enabled():
                handler = TwilioHandler()
                await handler.send_sms(user.phone_number, message)
                return True
                
            elif self.telephony_provider == "telnyx" and is_telnyx_enabled():
                handler = TelnyxHandler()
                await handler.send_sms(user.phone_number, message)
                return True
                
            else:
                logger.warning("No valid telephony provider configured for SMS")
                return False
                
        except Exception as e:
            logger.error(f"Error sending SMS reminder: {e}")
            return False
    
    async def _send_voice_reminder(self, user: User, reminder: Reminder) -> bool:
        """Send voice reminder call"""
        try:
            message = f"Hello, this is your reminder: {reminder.title}"
            if reminder.description:
                message += f". {reminder.description}"
            
            # Check if this is a wake-up call that requires confirmation
            if "wake" in reminder.title.lower() or "wake" in reminder.description.lower():
                return await self._send_persistent_wakeup_call(user, reminder)
            
            # Make regular voice call based on configured provider
            if self.telephony_provider == "twilio" and is_twilio_enabled():
                handler = TwilioHandler()
                await handler.make_call(user.phone_number, message)
                return True
                
            elif self.telephony_provider == "telnyx" and is_telnyx_enabled():
                handler = TelnyxHandler()
                await handler.make_call(user.phone_number, message)
                return True
                
            else:
                logger.warning("No valid telephony provider configured for voice calls")
                return False
                
        except Exception as e:
            logger.error(f"Error sending voice reminder: {e}")
            return False
    
    async def _send_persistent_wakeup_call(self, user: User, reminder: Reminder) -> bool:
        """Send persistent wake-up call that continues until user confirms they're awake"""
        try:
            if not is_persistent_wakeup_enabled():
                logger.info("Persistent wake-up calls are disabled")
                return await self._send_regular_wakeup_call(user, reminder)
            
            logger.info(f"Starting persistent wake-up call sequence for user {user.id}")
            
            # Start the persistent wake-up sequence
            asyncio.create_task(
                self._persistent_wakeup_sequence(user, reminder)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting persistent wake-up call: {e}")
            return False
    
    async def _persistent_wakeup_sequence(self, user: User, reminder: Reminder):
        """Execute persistent wake-up call sequence"""
        try:
            retry_count = 0
            max_retries = settings.WAKEUP_CALL_RETRY_ATTEMPTS
            retry_delay = settings.WAKEUP_CALL_RETRY_DELAY
            
            while retry_count < max_retries:
                try:
                    logger.info(f"Wake-up call attempt {retry_count + 1} for user {user.id}")
                    
                    # Make the wake-up call
                    call_success = await self._make_wakeup_call_with_confirmation(user, reminder)
                    
                    if call_success:
                        logger.info(f"Wake-up call confirmed by user {user.id}")
                        return
                    
                    # If call wasn't confirmed, wait and retry
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.info(f"Wake-up call not confirmed, retrying in {retry_delay} seconds")
                        await asyncio.sleep(retry_delay)
                    
                except Exception as e:
                    logger.error(f"Error in wake-up call attempt {retry_count + 1}: {e}")
                    retry_count += 1
            
            # If all retries failed, send SMS fallback
            if settings.WAKEUP_SMS_FALLBACK:
                logger.info(f"All wake-up call attempts failed for user {user.id}, sending SMS fallback")
                await self._send_wakeup_sms_fallback(user, reminder)
            
        except Exception as e:
            logger.error(f"Error in persistent wake-up sequence: {e}")
    
    async def _make_wakeup_call_with_confirmation(self, user: User, reminder: Reminder) -> bool:
        """Make a wake-up call that requires user confirmation"""
        try:
            # Generate TwiML for wake-up call with confirmation
            twiml = self._generate_wakeup_twiml(reminder)
            
            # Make the call
            if self.telephony_provider == "twilio" and is_twilio_enabled():
                handler = TwilioHandler()
                call_sid = await handler.make_call_with_twiml(user.phone_number, twiml)
                
                # Wait for call completion and check if confirmed
                return await self._wait_for_wakeup_confirmation(call_sid, user.id)
                
            elif self.telephony_provider == "telnyx" and is_telnyx_enabled():
                handler = TelnyxHandler()
                call_id = await handler.make_call_with_instructions(user.phone_number, twiml)
                
                # Wait for call completion and check if confirmed
                return await self._wait_for_wakeup_confirmation(call_id, user.id)
                
            else:
                logger.warning("No valid telephony provider configured for wake-up calls")
                return False
                
        except Exception as e:
            logger.error(f"Error making wake-up call with confirmation: {e}")
            return False
    
    def _generate_wakeup_twiml(self, reminder: Reminder) -> str:
        """Generate TwiML for wake-up call with confirmation"""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Good morning! This is your wake-up call.</Say>
    <Pause length="1"/>
    <Say voice="alice">{reminder.title}</Say>
    <Pause length="2"/>
    <Say voice="alice">To confirm you're awake, please press 1 on your phone.</Say>
    <Pause length="1"/>
    
    <Gather input="dtmf" timeout="15" action="/api/v1/voice/wakeup-webhook" method="POST">
        <Say voice="alice">Press 1 to confirm you're awake, or I'll call you again in 5 minutes.</Say>
    </Gather>
    
    <Say voice="alice">No confirmation received. I'll call you again shortly.</Say>
    <Hangup/>
</Response>"""
    
    async def _wait_for_wakeup_confirmation(self, call_id: str, user_id: int) -> bool:
        """Wait for wake-up call confirmation"""
        try:
            # This would typically involve webhook handling and database state tracking
            # For now, we'll simulate a simple wait
            await asyncio.sleep(30)  # Wait 30 seconds for call completion
            
            # Check if user confirmed (this would come from webhook)
            # For now, return False to trigger retry
            return False
            
        except Exception as e:
            logger.error(f"Error waiting for wake-up confirmation: {e}")
            return False
    
    async def _send_wakeup_sms_fallback(self, user: User, reminder: Reminder):
        """Send SMS fallback when wake-up calls fail"""
        try:
            message = f"🔔 Wake-up reminder: {reminder.title}\n\n"
            message += "I tried calling you but couldn't reach you. "
            message += "Please reply 'awake' to confirm you're up, or I'll keep trying."
            
            if self.telephony_provider == "twilio" and is_twilio_enabled():
                handler = TwilioHandler()
                await handler.send_sms(user.phone_number, message)
                return True
                
            elif self.telephony_provider == "telnyx" and is_telnyx_enabled():
                handler = TelnyxHandler()
                await handler.send_sms(user.phone_number, message)
                return True
                
            else:
                logger.warning("No valid telephony provider configured for SMS fallback")
                return False
                
        except Exception as e:
            logger.error(f"Error sending wake-up SMS fallback: {e}")
            return False
    
    async def _send_regular_wakeup_call(self, user: User, reminder: Reminder) -> bool:
        """Send regular wake-up call without persistence"""
        try:
            message = f"Good morning! This is your wake-up call: {reminder.title}"
            if reminder.description:
                message += f". {reminder.description}"
            
            # Make voice call based on configured provider
            if self.telephony_provider == "twilio" and is_twilio_enabled():
                handler = TwilioHandler()
                await handler.make_call(user.phone_number, message)
                return True
                
            elif self.telephony_provider == "telnyx" and is_telnyx_enabled():
                handler = TelnyxHandler()
                await handler.make_call(user.phone_number, message)
                return True
                
            else:
                logger.warning("No valid telephony provider configured for voice calls")
                return False
                
        except Exception as e:
            logger.error(f"Error sending regular wake-up call: {e}")
            return False
    
    async def delete_reminder(self, reminder_id: int) -> bool:
        """Delete a reminder"""
        try:
            db = await get_db()
            
            query = select(Reminder).where(Reminder.id == reminder_id)
            result = await db.execute(query)
            reminder = result.scalar_one_or_none()
            
            if reminder:
                await db.delete(reminder)
                await db.commit()
                
                logger.info(f"Deleted reminder {reminder_id}")
                return True
            else:
                logger.warning(f"Reminder {reminder_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting reminder: {e}")
            raise
    
    async def update_reminder(
        self, 
        reminder_id: int, 
        **kwargs
    ) -> Optional[Reminder]:
        """Update reminder fields"""
        try:
            db = await get_db()
            
            query = select(Reminder).where(Reminder.id == reminder_id)
            result = await db.execute(query)
            reminder = result.scalar_one_or_none()
            
            if reminder:
                for key, value in kwargs.items():
                    if hasattr(reminder, key):
                        setattr(reminder, key, value)
                
                await db.commit()
                await db.refresh(reminder)
                
                logger.info(f"Updated reminder {reminder_id}")
                return reminder
            else:
                logger.warning(f"Reminder {reminder_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Error updating reminder: {e}")
            raise
    
    async def snooze_reminder(self, reminder_id: int, user_id: int, duration: str) -> bool:
        """Snooze a reminder for a specified duration"""
        try:
            db = await get_db()
            
            query = select(Reminder).where(
                and_(Reminder.id == reminder_id, Reminder.user_id == user_id)
            )
            result = await db.execute(query)
            reminder = result.scalar_one_or_none()
            
            if not reminder:
                logger.warning(f"Reminder {reminder_id} not found for user {user_id}")
                return False
            
            # Parse duration (e.g., "15m", "1h", "2d")
            new_time = self._parse_duration(duration)
            if not new_time:
                logger.error(f"Invalid duration format: {duration}")
                return False
            
            # Update reminder time
            reminder.reminder_time = new_time
            reminder.status = "pending"
            reminder.is_completed = False
            
            await db.commit()
            await db.refresh(reminder)
            
            # Reschedule the reminder
            await self._schedule_reminder(reminder)
            
            logger.info(f"Snoozed reminder {reminder_id} for {duration} to {new_time}")
            return True
            
        except Exception as e:
            logger.error(f"Error snoozing reminder: {e}")
            raise
    
    def _parse_duration(self, duration: str) -> Optional[datetime]:
        """Parse duration string into datetime"""
        try:
            now = datetime.utcnow()
            
            if duration.endswith('m'):  # minutes
                minutes = int(duration[:-1])
                return now + timedelta(minutes=minutes)
            elif duration.endswith('h'):  # hours
                hours = int(duration[:-1])
                return now + timedelta(hours=hours)
            elif duration.endswith('d'):  # days
                days = int(duration[:-1])
                return now + timedelta(days=days)
            else:
                # Try to parse as minutes if no suffix
                minutes = int(duration)
                return now + timedelta(minutes=minutes)
                
        except (ValueError, TypeError):
            logger.error(f"Invalid duration format: {duration}")
            return None

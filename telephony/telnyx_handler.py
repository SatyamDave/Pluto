"""
Telnyx handler for Jarvis Phone AI Assistant
Handles SMS and voice calls via Telnyx API
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import telnyx
from config import settings

logger = logging.getLogger(__name__)


class TelnyxHandler:
    """Handles Telnyx SMS and voice operations"""
    
    def __init__(self):
        if not is_telnyx_enabled():
            raise ValueError("Telnyx not properly configured")
        
        # Set Telnyx API key
        telnyx.api_key = settings.TELNYX_API_KEY
        self.from_number = settings.TELNYX_PHONE_NUMBER
    
    async def send_sms(self, to_phone: str, message: str) -> str:
        """Send SMS message via Telnyx"""
        try:
            logger.info(f"Sending SMS to {to_phone} via Telnyx")
            
            # Clean phone number
            clean_phone = self._clean_phone_number(to_phone)
            
            # Send SMS using Telnyx Messaging API
            message_obj = telnyx.Message.create(
                from_=self.from_number,
                to=clean_phone,
                text=message
            )
            
            logger.info(f"SMS sent successfully. ID: {message_obj.id}")
            return message_obj.id
            
        except Exception as e:
            logger.error(f"Telnyx SMS error: {e}")
            raise
    
    async def send_bulk_sms(self, to_phones: List[str], message: str) -> List[Dict[str, Any]]:
        """Send SMS to multiple phone numbers"""
        try:
            logger.info(f"Sending bulk SMS to {len(to_phones)} numbers via Telnyx")
            
            results = []
            for phone in to_phones:
                try:
                    message_id = await self.send_sms(phone, message)
                    results.append({"phone": phone, "success": True, "message_id": message_id})
                except Exception as e:
                    logger.error(f"Failed to send SMS to {phone}: {e}")
                    results.append({"phone": phone, "success": False, "error": str(e)})
            
            logger.info(f"Bulk SMS completed. {len([r for r in results if r['success']])} successful")
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk SMS: {e}")
            raise
    
    async def schedule_sms(self, to_phone: str, message: str, send_at: datetime) -> str:
        """Schedule an SMS to be sent at a specific time"""
        try:
            logger.info(f"Scheduling SMS to {to_phone} for {send_at} via Telnyx")
            
            # Clean phone number
            clean_phone = self._clean_phone_number(to_phone)
            
            # Format time for Telnyx (ISO 8601)
            send_at_str = send_at.isoformat()
            
            # Create scheduled message
            message_obj = telnyx.Message.create(
                from_=self.from_number,
                to=clean_phone,
                text=message,
                scheduled_at=send_at_str
            )
            
            logger.info(f"SMS scheduled successfully. ID: {message_obj.id}")
            return message_obj.id
            
        except Exception as e:
            logger.error(f"Telnyx scheduled SMS error: {e}")
            raise
    
    async def make_call(self, to_phone: str, message: str) -> str:
        """Make outbound voice call via Telnyx with text-to-speech"""
        try:
            logger.info(f"Making call to {to_phone} via Telnyx")
            
            # Clean phone number
            clean_phone = self._clean_phone_number(to_phone)
            
            # Create call using Telnyx Call Control API
            call = telnyx.Call.create(
                from_=self.from_number,
                to=clean_phone,
                webhook_url=f"{settings.BASE_URL}/api/v1/voice/webhook/outbound",
                webhook_failover_url=f"{settings.BASE_URL}/api/v1/voice/webhook/outbound-fallback"
            )
            
            logger.info(f"Call initiated successfully. ID: {call.id}")
            return call.id
            
        except Exception as e:
            logger.error(f"Telnyx call error: {e}")
            raise
    
    async def make_call_with_script(self, to_phone: str, call_script: Dict[str, Any]) -> str:
        """Make outbound voice call with custom call script"""
        try:
            logger.info(f"Making call with script to {to_phone} via Telnyx")
            
            # Clean phone number
            clean_phone = self._clean_phone_number(to_phone)
            
            # Create call with custom webhook for call control
            call = telnyx.Call.create(
                from_=self.from_number,
                to=clean_phone,
                webhook_url=f"{settings.BASE_URL}/api/v1/voice/webhook/outbound-script",
                webhook_failover_url=f"{settings.BASE_URL}/api/v1/voice/webhook/outbound-fallback"
            )
            
            # Store call script for later use (you'd implement this with Redis/database)
            await self._store_call_script(call.id, call_script)
            
            logger.info(f"Call with script initiated successfully. ID: {call.id}")
            return call.id
            
        except Exception as e:
            logger.error(f"Telnyx call with script error: {e}")
            raise
    
    async def make_wakeup_call(self, to_phone: str, reminder_text: str) -> str:
        """Make a wake-up call that requires user confirmation"""
        try:
            logger.info(f"Making wake-up call to {to_phone} via Telnyx")
            
            # Clean phone number
            clean_phone = self._clean_phone_number(to_phone)
            
            # Create wake-up call with specific webhook
            call = telnyx.Call.create(
                from_=self.from_number,
                to=clean_phone,
                webhook_url=f"{settings.BASE_URL}/api/v1/voice/webhook/wakeup",
                webhook_failover_url=f"{settings.BASE_URL}/api/v1/voice/webhook/wakeup-fallback"
            )
            
            # Store wake-up call context
            await self._store_wakeup_context(call.id, reminder_text)
            
            logger.info(f"Wake-up call initiated successfully. ID: {call.id}")
            return call.id
            
        except Exception as e:
            logger.error(f"Telnyx wake-up call error: {e}")
            raise
    
    async def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """Get SMS message delivery status"""
        try:
            message = telnyx.Message.retrieve(message_id)
            status = {
                "id": message.id,
                "status": message.status,
                "direction": message.direction,
                "from": message.from_,
                "to": message.to,
                "text": message.text,
                "created_at": message.created_at,
                "updated_at": message.updated_at,
                "sent_at": message.sent_at,
                "delivered_at": message.delivered_at,
                "error_code": getattr(message, 'error_code', None),
                "error_message": getattr(message, 'error_message', None)
            }
            return status
        except Exception as e:
            logger.error(f"Error getting message status: {e}")
            raise
    
    async def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """Get call status"""
        try:
            call = telnyx.Call.retrieve(call_id)
            status = {
                "id": call.id,
                "status": call.status,
                "direction": call.direction,
                "from": call.from_,
                "to": call.to,
                "started_at": call.started_at,
                "ended_at": call.ended_at,
                "duration": call.duration,
                "webhook_url": call.webhook_url,
                "webhook_failover_url": call.webhook_failover_url
            }
            return status
        except Exception as e:
            logger.error(f"Error getting call status: {e}")
            raise
    
    async def list_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent SMS messages"""
        try:
            messages = telnyx.Message.list(limit=limit)
            return [
                {
                    "id": msg.id,
                    "from": msg.from_,
                    "to": msg.to,
                    "text": msg.text,
                    "status": msg.status,
                    "created_at": msg.created_at
                }
                for msg in messages.data
            ]
        except Exception as e:
            logger.error(f"Error listing messages: {e}")
            raise
    
    async def list_recent_calls(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent voice calls"""
        try:
            calls = telnyx.Call.list(limit=limit)
            return [
                {
                    "id": call.id,
                    "from": call.from_,
                    "to": call.to,
                    "status": call.status,
                    "started_at": call.started_at,
                    "duration": call.duration
                }
                for call in calls.data
            ]
        except Exception as e:
            logger.error(f"Error listing calls: {e}")
            raise
    
    async def hangup_call(self, call_id: str) -> bool:
        """Hang up an active call"""
        try:
            call = telnyx.Call.retrieve(call_id)
            call.hangup()
            logger.info(f"Call {call_id} hung up successfully")
            return True
        except Exception as e:
            logger.error(f"Error hanging up call {call_id}: {e}")
            return False
    
    def _clean_phone_number(self, phone: str) -> str:
        """Clean and format phone number for Telnyx"""
        # Remove all non-digit characters
        clean = ''.join(filter(str.isdigit, phone))
        
        # Ensure it starts with country code
        if len(clean) == 10:
            clean = "1" + clean  # Assume US number
        elif len(clean) == 11 and clean.startswith("1"):
            pass  # Already has US country code
        else:
            # Add + prefix for international numbers
            clean = "+" + clean
        
        return clean
    
    async def _store_call_script(self, call_id: str, script: Dict[str, Any]):
        """Store call script for later use (implement with Redis/database)"""
        # This would typically store the script in Redis or database
        # For now, we'll just log it
        logger.info(f"Stored call script for call {call_id}: {script}")
    
    async def _store_wakeup_context(self, call_id: str, reminder_text: str):
        """Store wake-up call context (implement with Redis/database)"""
        # This would typically store the wake-up context in Redis or database
        # For now, we'll just log it
        logger.info(f"Stored wake-up context for call {call_id}: {reminder_text}")


def is_telnyx_enabled() -> bool:
    """Check if Telnyx is properly configured"""
    return all([
        settings.TELNYX_API_KEY,
        settings.TELNYX_PHONE_NUMBER
    ])

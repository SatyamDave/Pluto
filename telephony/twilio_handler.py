"""
Twilio handler for Jarvis Phone AI Assistant
Handles SMS and voice calls via Twilio API
"""

import logging
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from config import settings

logger = logging.getLogger(__name__)


class TwilioHandler:
    """Handles Twilio SMS and voice operations"""
    
    def __init__(self):
        if not is_twilio_enabled():
            raise ValueError("Twilio not properly configured")
        
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.from_number = settings.TWILIO_PHONE_NUMBER
    
    async def send_sms(self, to_phone: str, message: str) -> str:
        """Send SMS message via Twilio"""
        try:
            logger.info(f"Sending SMS to {to_phone} via Twilio")
            
            # Clean phone number
            clean_phone = self._clean_phone_number(to_phone)
            
            # Send SMS
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=clean_phone
            )
            
            logger.info(f"SMS sent successfully. SID: {message_obj.sid}")
            return message_obj.sid
            
        except TwilioException as e:
            logger.error(f"Twilio SMS error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending SMS: {e}")
            raise
    
    async def make_call(self, to_phone: str, message: str) -> str:
        """Make outbound voice call via Twilio with simple text-to-speech"""
        try:
            logger.info(f"Making call to {to_phone} via Twilio")
            
            # Clean phone number
            clean_phone = self._clean_phone_number(to_phone)
            
            # Create TwiML for the call
            twiml = self._generate_call_twiml(message)
            
            # Make the call
            call = self.client.calls.create(
                twiml=twiml,
                from_=self.from_number,
                to=clean_phone
            )
            
            logger.info(f"Call initiated successfully. SID: {call.sid}")
            return call.sid
            
        except TwilioException as e:
            logger.error(f"Twilio call error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error making call: {e}")
            raise
    
    async def make_call_with_twiml(self, to_phone: str, twiml: str) -> str:
        """Make outbound voice call with custom TwiML"""
        try:
            logger.info(f"Making call with custom TwiML to {to_phone} via Twilio")
            
            # Clean phone number
            clean_phone = self._clean_phone_number(to_phone)
            
            # Make the call with custom TwiML
            call = self.client.calls.create(
                twiml=twiml,
                from_=self.from_number,
                to=clean_phone
            )
            
            logger.info(f"Call with custom TwiML initiated successfully. SID: {call.sid}")
            return call.sid
            
        except TwilioException as e:
            logger.error(f"Twilio call error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error making call with custom TwiML: {e}")
            raise
    
    async def send_bulk_sms(self, to_phones: list, message: str) -> list:
        """Send SMS to multiple phone numbers"""
        try:
            logger.info(f"Sending bulk SMS to {len(to_phones)} numbers via Twilio")
            
            results = []
            for phone in to_phones:
                try:
                    message_sid = await self.send_sms(phone, message)
                    results.append({"phone": phone, "success": True, "message_sid": message_sid})
                except Exception as e:
                    logger.error(f"Failed to send SMS to {phone}: {e}")
                    results.append({"phone": phone, "success": False, "error": str(e)})
            
            logger.info(f"Bulk SMS completed. {len([r for r in results if r['success']])} successful")
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk SMS: {e}")
            raise
    
    async def schedule_sms(self, to_phone: str, message: str, send_at: str) -> str:
        """Schedule an SMS to be sent at a specific time"""
        try:
            logger.info(f"Scheduling SMS to {to_phone} for {send_at} via Twilio")
            
            # Clean phone number
            clean_phone = self._clean_phone_number(to_phone)
            
            # Schedule SMS
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=clean_phone,
                send_at=send_at,
                schedule_type="fixed"
            )
            
            logger.info(f"SMS scheduled successfully. SID: {message_obj.sid}")
            return message_obj.sid
            
        except TwilioException as e:
            logger.error(f"Twilio scheduled SMS error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error scheduling SMS: {e}")
            raise
    
    def _clean_phone_number(self, phone: str) -> str:
        """Clean and format phone number for Twilio"""
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
    
    def _generate_call_twiml(self, message: str) -> str:
        """Generate TwiML for outbound call"""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">{message}</Say>
    <Hangup/>
</Response>"""
    
    async def get_message_status(self, message_sid: str) -> dict:
        """Get SMS message delivery status"""
        try:
            message = self.client.messages(message_sid).fetch()
            return {
                "sid": message.sid,
                "status": message.status,
                "direction": message.direction,
                "from": message.from_,
                "to": message.to,
                "body": message.body,
                "date_sent": message.date_sent,
                "error_code": message.error_code,
                "error_message": message.error_message
            }
        except TwilioException as e:
            logger.error(f"Error getting message status: {e}")
            raise
    
    async def get_call_status(self, call_sid: str) -> dict:
        """Get call status"""
        try:
            call = self.client.calls(call_sid).fetch()
            return {
                "sid": call.sid,
                "status": call.status,
                "direction": call.direction,
                "from": call.from_,
                "to": call.to,
                "start_time": call.start_time,
                "end_time": call.end_time,
                "duration": call.duration,
                "price": call.price,
                "price_unit": call.price_unit
            }
        except TwilioException as e:
            logger.error(f"Error getting call status: {e}")
            raise


def is_twilio_enabled() -> bool:
    """Check if Twilio is properly configured"""
    return all([
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN,
        settings.TWILIO_PHONE_NUMBER
    ])

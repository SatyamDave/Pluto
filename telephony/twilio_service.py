"""
Twilio Telephony Service Implementation
Handles SMS and voice calls through Twilio API
"""

import json
import hmac
import hashlib
import time
from typing import Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlencode

from .base import (
    BaseTelephonyService, 
    CallRequest, 
    MessageRequest, 
    InboundCall, 
    InboundMessage,
    CallStatus,
    MessageStatus
)
from utils import get_logger

logger = get_logger(__name__)


class TwilioService(BaseTelephonyService):
    """Twilio telephony service implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Twilio service"""
        super().__init__(config)
        self.account_sid = config.get("twilio_account_sid")
        self.auth_token = config.get("twilio_auth_token")
        self.phone_number = config.get("twilio_phone_number")
        self.webhook_secret = config.get("twilio_webhook_secret")
        
        if not self.account_sid:
            logger.warning("Twilio Account SID not configured")
        if not self.auth_token:
            logger.warning("Twilio Auth Token not configured")
        if not self.webhook_secret:
            logger.warning("Twilio webhook secret not configured")
    
    async def send_sms(self, request: MessageRequest) -> Dict[str, Any]:
        """Send SMS via Twilio"""
        try:
            from twilio.rest import Client
            
            # Initialize Twilio client
            client = Client(self.account_sid, self.auth_token)
            
            # Send SMS via Twilio
            message = client.messages.create(
                body=request.body,
                from_=request.from_,
                to=request.to
            )
            
            logger.info(f"SMS sent successfully via Twilio to {request.to}: {message.sid}")
            
            return {
                "message_id": message.sid,
                "status": message.status,
                "provider": "twilio",
                "to": request.to,
                "from": request.from_,
                "body": request.body,
                "timestamp": datetime.utcnow().isoformat(),
                "price": getattr(message, 'price', None),
                "price_unit": getattr(message, 'price_unit', None)
            }
            
        except Exception as e:
            logger.error(f"Error sending SMS via Twilio: {e}")
            return {
                "error": str(e),
                "status": "failed",
                "provider": "twilio"
            }
    
    async def make_call(self, request: CallRequest) -> Dict[str, Any]:
        """Make outbound call via Twilio"""
        try:
            from twilio.rest import Client
            from twilio.twiml.voice_response import VoiceResponse
            
            # Initialize Twilio client
            client = Client(self.account_sid, self.auth_token)
            
            # Generate TwiML for the call
            twiml = VoiceResponse()
            twiml.say(request.script, voice="alice")
            twiml.hangup()
            
            # Make the call
            call = client.calls.create(
                twiml=str(twiml),
                from_=request.from_,
                to=request.to
            )
            
            logger.info(f"Call initiated successfully via Twilio to {request.to}: {call.sid}")
            
            return {
                "call_id": call.sid,
                "status": call.status,
                "provider": "twilio",
                "to": request.to,
                "from": request.from_,
                "script": request.script,
                "timestamp": datetime.utcnow().isoformat(),
                "price": getattr(call, 'price', None),
                "price_unit": getattr(call, 'price_unit', None)
            }
            
        except Exception as e:
            logger.error(f"Error making call via Twilio: {e}")
            return {
                "error": str(e),
                "status": "failed",
                "provider": "twilio"
            }
    
    async def handle_inbound_sms(self, payload: Dict[str, Any]) -> InboundMessage:
        """Process inbound SMS webhook from Twilio"""
        try:
            # Extract SMS data from Twilio webhook payload
            return InboundMessage(
                message_id=payload.get("MessageSid", ""),
                from_=payload.get("From", ""),
                to=payload.get("To", ""),
                body=payload.get("Body", ""),
                timestamp=payload.get("MessageTimestamp", ""),
                media_urls=payload.get("MediaUrl", [])
            )
            
        except Exception as e:
            logger.error(f"Error processing Twilio inbound SMS: {e}")
            raise
    
    async def handle_inbound_voice(self, payload: Dict[str, Any]) -> InboundCall:
        """Process inbound voice webhook from Twilio"""
        try:
            # Extract call data from Twilio webhook payload
            return InboundCall(
                call_id=payload.get("CallSid", ""),
                from_=payload.get("From", ""),
                to=payload.get("To", ""),
                timestamp=payload.get("CallTimestamp", ""),
                call_status=CallStatus.IN_PROGRESS,
                recording_url=payload.get("RecordingUrl"),
                duration=payload.get("CallDuration")
            )
            
        except Exception as e:
            logger.error(f"Error processing Twilio inbound voice: {e}")
            raise
    
    async def get_call_status(self, call_id: str) -> CallStatus:
        """Get call status from Twilio"""
        try:
            from twilio.rest import Client
            
            # Initialize Twilio client
            client = Client(self.account_sid, self.auth_token)
            
            # Get call details
            call = client.calls(call_id).fetch()
            
            # Map Twilio status to our enum
            status_mapping = {
                'queued': CallStatus.QUEUED,
                'ringing': CallStatus.RINGING,
                'in-progress': CallStatus.IN_PROGRESS,
                'completed': CallStatus.COMPLETED,
                'busy': CallStatus.BUSY,
                'failed': CallStatus.FAILED,
                'no-answer': CallStatus.NO_ANSWER,
                'canceled': CallStatus.CANCELED
            }
            
            return status_mapping.get(call.status, CallStatus.UNKNOWN)
            
        except Exception as e:
            logger.error(f"Error getting call status: {e}")
            return CallStatus.FAILED
    
    async def get_message_status(self, message_id: str) -> MessageStatus:
        """Get message status from Twilio"""
        try:
            from twilio.rest import Client
            
            # Initialize Twilio client
            client = Client(self.account_sid, self.auth_token)
            
            # Get message details
            message = client.messages(message_id).fetch()
            
            # Map Twilio status to our enum
            status_mapping = {
                'queued': MessageStatus.QUEUED,
                'sending': MessageStatus.SENDING,
                'sent': MessageStatus.SENT,
                'delivered': MessageStatus.DELIVERED,
                'undelivered': MessageStatus.UNDELIVERED,
                'failed': MessageStatus.FAILED
            }
            
            return status_mapping.get(message.status, MessageStatus.UNKNOWN)
            
        except Exception as e:
            logger.error(f"Error getting message status: {e}")
            return MessageStatus.FAILED
    
    async def hangup_call(self, call_id: str) -> bool:
        """Hang up call via Twilio"""
        try:
            from twilio.rest import Client
            
            # Initialize Twilio client
            client = Client(self.account_sid, self.auth_token)
            
            # Update call to hang up
            call = client.calls(call_id).update(status='completed')
            
            logger.info(f"Call {call_id} hung up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error hanging up call: {e}")
            return False
    
    async def validate_webhook_signature(self, payload: bytes, signature: str, timestamp: str) -> bool:
        """Validate Twilio webhook signature"""
        try:
            if not self.webhook_secret:
                logger.warning("No webhook secret configured for signature validation")
                return True  # Allow if no secret configured
            
            # Create expected signature (Twilio format)
            # Concatenate the URL and the request body
            from config import settings
            url = f"{settings.BASE_URL}{timestamp}"  # Use configured BASE_URL
            data = url + str(payload, 'utf-8')
            
            # Create expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                data.encode('utf-8'),
                hashlib.sha1
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error validating webhook signature: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get Twilio service health status"""
        base_status = super().get_health_status()
        base_status.update({
            "account_sid_configured": bool(self.account_sid),
            "auth_token_configured": bool(self.auth_token),
            "webhook_secret_configured": bool(self.webhook_secret),
            "phone_number": self.phone_number
        })
        return base_status

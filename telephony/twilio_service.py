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
            # TODO: Implement actual Twilio SMS API call
            # For now, return mock response
            logger.info(f"Sending SMS to {request.to}: {request.body}")
            
            return {
                "message_id": f"twilio_msg_{int(time.time())}",
                "status": "queued",
                "provider": "twilio",
                "to": request.to,
                "from": request.from_,
                "body": request.body,
                "timestamp": datetime.utcnow().isoformat()
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
            # TODO: Implement actual Twilio Voice API call
            # For now, return mock response
            logger.info(f"Making call to {request.to}: {request.script}")
            
            return {
                "call_id": f"twilio_call_{int(time.time())}",
                "status": "queued",
                "provider": "twilio",
                "to": request.to,
                "from": request.from_,
                "script": request.script,
                "timestamp": datetime.utcnow().isoformat()
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
            # TODO: Implement actual Twilio API call to get status
            # For now, return mock status
            logger.info(f"Getting call status for {call_id}")
            return CallStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Error getting call status: {e}")
            return CallStatus.FAILED
    
    async def get_message_status(self, message_id: str) -> MessageStatus:
        """Get message status from Twilio"""
        try:
            # TODO: Implement actual Twilio API call to get status
            # For now, return mock status
            logger.info(f"Getting message status for {message_id}")
            return MessageStatus.DELIVERED
            
        except Exception as e:
            logger.error(f"Error getting message status: {e}")
            return MessageStatus.FAILED
    
    async def hangup_call(self, call_id: str) -> bool:
        """Hang up call via Twilio"""
        try:
            # TODO: Implement actual Twilio API call to hang up
            logger.info(f"Hanging up call {call_id}")
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
            url = f"https://your-domain.com{timestamp}"  # This should be the actual webhook URL
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

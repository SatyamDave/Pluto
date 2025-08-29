"""
Telnyx Telephony Service Implementation
Handles SMS and voice calls through Telnyx API
"""

import json
import hmac
import hashlib
import time
from typing import Dict, Any, Optional
from datetime import datetime

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


class TelnyxService(BaseTelephonyService):
    """Telnyx telephony service implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Telnyx service"""
        super().__init__(config)
        self.api_key = config.get("telnyx_api_key")
        self.webhook_secret = config.get("telnyx_webhook_secret")
        self.phone_number = config.get("telnyx_phone_number")
        
        if not self.api_key:
            logger.warning("Telnyx API key not configured")
        if not self.webhook_secret:
            logger.warning("Telnyx webhook secret not configured")
    
    async def send_sms(self, request: MessageRequest) -> Dict[str, Any]:
        """Send SMS via Telnyx"""
        try:
            # TODO: Implement actual Telnyx SMS API call
            # For now, return mock response
            logger.info(f"Sending SMS to {request.to}: {request.body}")
            
            return {
                "message_id": f"telnyx_msg_{int(time.time())}",
                "status": "queued",
                "provider": "telnyx",
                "to": request.to,
                "from": request.from_,
                "body": request.body,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending SMS via Telnyx: {e}")
            return {
                "error": str(e),
                "status": "failed",
                "provider": "telnyx"
            }
    
    async def make_call(self, request: CallRequest) -> Dict[str, Any]:
        """Make outbound call via Telnyx"""
        try:
            # TODO: Implement actual Telnyx Voice API call
            # For now, return mock response
            logger.info(f"Making call to {request.to}: {request.script}")
            
            return {
                "call_id": f"telnyx_call_{int(time.time())}",
                "status": "queued",
                "provider": "telnyx",
                "to": request.to,
                "from": request.from_,
                "script": request.script,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error making call via Telnyx: {e}")
            return {
                "error": str(e),
                "status": "failed",
                "provider": "telnyx"
            }
    
    async def handle_inbound_sms(self, payload: Dict[str, Any]) -> InboundMessage:
        """Process inbound SMS webhook from Telnyx"""
        try:
            # Extract SMS data from Telnyx webhook payload
            data = payload.get("data", {})
            
            return InboundMessage(
                message_id=data.get("id", ""),
                from_=data.get("from", {}).get("phone_number", ""),
                to=data.get("to", {}).get("phone_number", ""),
                body=data.get("text", ""),
                timestamp=data.get("occurred_at", ""),
                media_urls=data.get("media", [])
            )
            
        except Exception as e:
            logger.error(f"Error processing Telnyx inbound SMS: {e}")
            raise
    
    async def handle_inbound_voice(self, payload: Dict[str, Any]) -> InboundCall:
        """Process inbound voice webhook from Telnyx"""
        try:
            # Extract call data from Telnyx webhook payload
            data = payload.get("data", {})
            
            return InboundCall(
                call_id=data.get("id", ""),
                from_=data.get("from", {}).get("phone_number", ""),
                to=data.get("to", {}).get("phone_number", ""),
                timestamp=data.get("occurred_at", ""),
                call_status=CallStatus.IN_PROGRESS,
                recording_url=data.get("recording_url"),
                duration=data.get("duration")
            )
            
        except Exception as e:
            logger.error(f"Error processing Telnyx inbound voice: {e}")
            raise
    
    async def get_call_status(self, call_id: str) -> CallStatus:
        """Get call status from Telnyx"""
        try:
            # TODO: Implement actual Telnyx API call to get status
            # For now, return mock status
            logger.info(f"Getting call status for {call_id}")
            return CallStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Error getting call status: {e}")
            return CallStatus.FAILED
    
    async def get_message_status(self, message_id: str) -> MessageStatus:
        """Get message status from Telnyx"""
        try:
            # TODO: Implement actual Telnyx API call to get status
            # For now, return mock status
            logger.info(f"Getting message status for {message_id}")
            return MessageStatus.DELIVERED
            
        except Exception as e:
            logger.error(f"Error getting message status: {e}")
            return MessageStatus.FAILED
    
    async def hangup_call(self, call_id: str) -> bool:
        """Hang up call via Telnyx"""
        try:
            # TODO: Implement actual Telnyx API call to hang up
            logger.info(f"Hanging up call {call_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error hanging up call: {e}")
            return False
    
    async def validate_webhook_signature(self, payload: bytes, signature: str, timestamp: str) -> bool:
        """Validate Telnyx webhook signature"""
        try:
            if not self.webhook_secret:
                logger.warning("No webhook secret configured for signature validation")
                return True  # Allow if no secret configured
            
            # Create expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error validating webhook signature: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get Telnyx service health status"""
        base_status = super().get_health_status()
        base_status.update({
            "api_key_configured": bool(self.api_key),
            "webhook_secret_configured": bool(self.webhook_secret),
            "phone_number": self.phone_number
        })
        return base_status

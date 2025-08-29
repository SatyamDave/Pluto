"""
Abstract Telephony Service Base Class
Defines the interface for all telephony providers (Telnyx, Twilio, etc.)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class CallStatus(Enum):
    """Call status enumeration"""
    RINGING = "ringing"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BUSY = "busy"
    NO_ANSWER = "no-answer"


class MessageStatus(Enum):
    """Message status enumeration"""
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    UNDELIVERED = "undelivered"


@dataclass
class CallRequest:
    """Call request data structure"""
    to: str
    from_: str
    script: str
    user_id: str
    call_type: str = "general"
    timeout: int = 30
    record: bool = False


@dataclass
class MessageRequest:
    """Message request data structure"""
    to: str
    from_: str
    body: str
    user_id: str
    media_urls: Optional[List[str]] = None


@dataclass
class InboundCall:
    """Inbound call data structure"""
    call_id: str
    from_: str
    to: str
    timestamp: str
    call_status: CallStatus
    recording_url: Optional[str] = None
    duration: Optional[int] = None


@dataclass
class InboundMessage:
    """Inbound message data structure"""
    message_id: str
    from_: str
    to: str
    body: str
    timestamp: str
    media_urls: Optional[List[str]] = None


class BaseTelephonyService(ABC):
    """Abstract base class for telephony services"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize telephony service with configuration"""
        self.config = config
        self.phone_number = config.get("phone_number")
        self.provider_name = self.__class__.__name__.lower()
    
    @abstractmethod
    async def send_sms(self, request: MessageRequest) -> Dict[str, Any]:
        """
        Send SMS message
        
        Args:
            request: Message request data
            
        Returns:
            Response with message_id and status
        """
        pass
    
    @abstractmethod
    async def make_call(self, request: CallRequest) -> Dict[str, Any]:
        """
        Make outbound call
        
        Args:
            request: Call request data
            
        Returns:
            Response with call_id and status
        """
        pass
    
    @abstractmethod
    async def handle_inbound_sms(self, payload: Dict[str, Any]) -> InboundMessage:
        """
        Process inbound SMS webhook payload
        
        Args:
            payload: Raw webhook payload from provider
            
        Returns:
            Structured inbound message data
        """
        pass
    
    @abstractmethod
    async def handle_inbound_voice(self, payload: Dict[str, Any]) -> InboundCall:
        """
        Process inbound voice webhook payload
        
        Args:
            payload: Raw webhook payload from provider
            
        Returns:
            Structured inbound call data
        """
        pass
    
    @abstractmethod
    async def get_call_status(self, call_id: str) -> CallStatus:
        """
        Get current status of a call
        
        Args:
            call_id: Call identifier
            
        Returns:
            Current call status
        """
        pass
    
    @abstractmethod
    async def get_message_status(self, message_id: str) -> MessageStatus:
        """
        Get current status of a message
        
        Args:
            message_id: Message identifier
            
        Returns:
            Current message status
        """
        pass
    
    @abstractmethod
    async def hangup_call(self, call_id: str) -> bool:
        """
        Hang up an active call
        
        Args:
            call_id: Call identifier
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def validate_webhook_signature(self, payload: bytes, signature: str, timestamp: str) -> bool:
        """
        Validate webhook signature for security
        
        Args:
            payload: Raw webhook payload
            signature: Signature header
            timestamp: Timestamp header
            
        Returns:
            True if signature is valid
        """
        pass
    
    def get_webhook_urls(self) -> Dict[str, str]:
        """Get webhook URLs for this service"""
        return {
            "sms": f"/api/v1/telephony/{self.provider_name}/sms",
            "voice": f"/api/v1/telephony/{self.provider_name}/voice",
            "status": f"/api/v1/telephony/{self.provider_name}/status"
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get service health status"""
        return {
            "provider": self.provider_name,
            "phone_number": self.phone_number,
            "status": "healthy",
            "capabilities": ["sms", "voice", "webhooks"]
        }

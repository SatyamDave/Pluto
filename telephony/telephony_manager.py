"""
Telephony Manager
Integrates telephony services with Pluto's AI orchestrator
"""

from typing import Dict, Any, Optional, List
from .base import (
    BaseTelephonyService, 
    CallRequest, 
    MessageRequest, 
    InboundCall, 
    InboundMessage
)
from .service_factory import TelephonyServiceFactory
from services.user_manager import UserManager
# from ai_orchestrator import AIOrchestrator  # Circular import - will import when needed
from utils import get_logger

logger = get_logger(__name__)


class TelephonyManager:
    """Manages telephony operations and integrates with Pluto's AI orchestrator"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize telephony manager"""
        self.config = config
        self.provider = config.get("PROVIDER", "telnyx").lower()
        self.phone_number = config.get("PHONE_NUMBER")
        
        # Create telephony service
        self.telephony_service = TelephonyServiceFactory.create_service(self.provider, config)
        if not self.telephony_service:
            raise ValueError(f"Failed to create telephony service for provider: {self.provider}")
        
        # Initialize other services
        self.user_manager = UserManager()
        self.orchestrator = None  # Will initialize when needed
        
        logger.info(f"Telephony Manager initialized with {self.provider}")
    
    async def handle_inbound_sms(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle inbound SMS webhook
        
        Args:
            payload: Raw webhook payload from telephony provider
            
        Returns:
            Response to send back to provider
        """
        try:
            # Process the webhook payload
            inbound_message = await self.telephony_service.handle_inbound_sms(payload)
            
            # Get or create user
            user = await self.user_manager.get_or_create_user(inbound_message.from_)
            user_id = user["id"]
            
            # Process message through AI orchestrator
            if self.orchestrator is None:
                from ai_orchestrator import AIOrchestrator
                self.orchestrator = AIOrchestrator()
            
            result = await self.orchestrator.process_message(
                user_id=user_id,
                message=inbound_message.body,
                message_type="sms"
            )
            
            # Send response back to user
            if "response" in result:
                response = await self.telephony_service.send_sms(
                    MessageRequest(
                        to=inbound_message.from_,
                        from_=self.phone_number,
                        body=result["response"],
                        user_id=user_id
                    )
                )
                
                logger.info(f"Sent SMS response to {inbound_message.from_}: {result['response']}")
                
                return {
                    "success": True,
                    "message": "SMS processed and response sent",
                    "response_id": response.get("message_id")
                }
            else:
                logger.error(f"No response generated for SMS from {inbound_message.from_}")
                return {
                    "success": False,
                    "error": "No response generated"
                }
                
        except Exception as e:
            logger.error(f"Error handling inbound SMS: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def handle_inbound_voice(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle inbound voice webhook
        
        Args:
            payload: Raw webhook payload from telephony provider
            
        Returns:
            Response to send back to provider
        """
        try:
            # Process the webhook payload
            inbound_call = await self.telephony_service.handle_inbound_voice(payload)
            
            # Get or create user
            user = await self.user_manager.get_or_create_user(inbound_call.from_)
            user_id = user["id"]
            
            # For voice calls, we'll need to implement TTS and voice response
            # For now, return a simple greeting
            greeting = "Hello! I'm Pluto, your AI assistant. I'm currently in development mode. Please send me a text message instead."
            
            logger.info(f"Received voice call from {inbound_call.from_}, playing greeting")
            
            return {
                "success": True,
                "message": "Voice call handled",
                "action": "play_greeting",
                "greeting": greeting
            }
            
        except Exception as e:
            logger.error(f"Error handling inbound voice: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_sms(self, to: str, body: str, user_id: int) -> Dict[str, Any]:
        """
        Send outbound SMS
        
        Args:
            to: Recipient phone number
            body: Message body
            user_id: Sender user ID
            
        Returns:
            Send result
        """
        try:
            request = MessageRequest(
                to=to,
                from_=self.phone_number,
                body=body,
                user_id=user_id
            )
            
            result = await self.telephony_service.send_sms(request)
            
            if "error" not in result:
                logger.info(f"SMS sent successfully to {to}")
            else:
                logger.error(f"Failed to send SMS to {to}: {result['error']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def make_call(self, to: str, script: str, user_id: int, call_type: str = "general") -> Dict[str, Any]:
        """
        Make outbound call
        
        Args:
            to: Recipient phone number
            script: Call script to read
            user_id: Caller user ID
            call_type: Type of call
            
        Returns:
            Call result
        """
        try:
            request = CallRequest(
                to=to,
                from_=self.phone_number,
                script=script,
                user_id=user_id,
                call_type=call_type
            )
            
            result = await self.telephony_service.make_call(request)
            
            if "error" not in result:
                logger.info(f"Call initiated successfully to {to}")
            else:
                logger.error(f"Failed to initiate call to {to}: {result['error']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error making call: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def get_telephony_status(self) -> Dict[str, Any]:
        """Get telephony service status"""
        try:
            telephony_status = self.telephony_service.get_health_status()
            
            return {
                "provider": self.provider,
                "phone_number": self.phone_number,
                "service_status": telephony_status,
                "webhook_urls": self.telephony_service.get_webhook_urls()
            }
            
        except Exception as e:
            logger.error(f"Error getting telephony status: {e}")
            return {
                "error": str(e),
                "provider": self.provider
            }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate telephony configuration"""
        return TelephonyServiceFactory.validate_config(self.provider, self.config)

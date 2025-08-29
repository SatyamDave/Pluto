"""
Telephony Service Factory
Creates and manages telephony service instances based on configuration
"""

from typing import Dict, Any, Optional
from .base import BaseTelephonyService
from .telnyx_service import TelnyxService
from .twilio_service import TwilioService
from utils import get_logger

logger = get_logger(__name__)


class TelephonyServiceFactory:
    """Factory for creating telephony service instances"""
    
    @staticmethod
    def create_service(provider: str, config: Dict[str, Any]) -> Optional[BaseTelephonyService]:
        """
        Create telephony service instance based on provider
        
        Args:
            provider: Service provider name (telnyx, twilio)
            config: Configuration dictionary
            
        Returns:
            Telephony service instance or None if provider not supported
        """
        try:
            if provider.lower() == "telnyx":
                return TelnyxService(config)
            elif provider.lower() == "twilio":
                return TwilioService(config)
            else:
                logger.error(f"Unsupported telephony provider: {provider}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating telephony service for {provider}: {e}")
            return None
    
    @staticmethod
    def get_supported_providers() -> list:
        """Get list of supported telephony providers"""
        return ["telnyx", "twilio"]
    
    @staticmethod
    def validate_config(provider: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration for a specific provider
        
        Args:
            provider: Service provider name
            config: Configuration dictionary
            
        Returns:
            Validation result with errors and warnings
        """
        errors = []
        warnings = []
        
        if provider.lower() == "telnyx":
            if not config.get("telnyx_api_key"):
                errors.append("telnyx_api_key is required")
            if not config.get("telnyx_phone_number"):
                errors.append("telnyx_phone_number is required")
            if not config.get("telnyx_webhook_secret"):
                warnings.append("telnyx_webhook_secret is recommended for security")
                
        elif provider.lower() == "twilio":
            if not config.get("twilio_account_sid"):
                errors.append("twilio_account_sid is required")
            if not config.get("twilio_auth_token"):
                errors.append("twilio_auth_token is required")
            if not config.get("twilio_phone_number"):
                errors.append("twilio_phone_number is required")
            if not config.get("twilio_webhook_secret"):
                warnings.append("twilio_webhook_secret is recommended for security")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

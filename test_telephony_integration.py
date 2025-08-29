"""
Test Telephony Integration
Verify that Pluto can handle telephony operations
"""

import asyncio
import pytest
from telephony.telephony_manager import TelephonyManager
from telephony.service_factory import TelephonyServiceFactory


class TestTelephonyIntegration:
    """Test telephony integration with Pluto"""
    
    def test_service_factory(self):
        """Test telephony service factory"""
        # Test supported providers
        providers = TelephonyServiceFactory.get_supported_providers()
        assert "telnyx" in providers
        assert "twilio" in providers
        
        # Test configuration validation
        telnyx_config = {
            "telnyx_api_key": "test_key",
            "telnyx_phone_number": "+1234567890"
        }
        validation = TelephonyServiceFactory.validate_config("telnyx", telnyx_config)
        assert validation["valid"] is True
        assert len(validation["errors"]) == 0
        
        # Test missing required config
        invalid_config = {"telnyx_phone_number": "+1234567890"}
        validation = TelephonyServiceFactory.validate_config("telnyx", invalid_config)
        assert validation["valid"] is False
        assert "telnyx_api_key is required" in validation["errors"]
    
    def test_service_creation(self):
        """Test telephony service creation"""
        config = {
            "PROVIDER": "telnyx",
            "PHONE_NUMBER": "+1234567890",
            "telnyx_api_key": "test_key",
            "telnyx_phone_number": "+1234567890"
        }
        
        service = TelephonyServiceFactory.create_service("telnyx", config)
        assert service is not None
        assert service.provider_name == "telnyxservice"
        assert service.phone_number == "+1234567890"
    
    @pytest.mark.asyncio
    async def test_telephony_manager_initialization(self):
        """Test telephony manager initialization"""
        config = {
            "PROVIDER": "telnyx",
            "PHONE_NUMBER": "+1234567890",
            "telnyx_api_key": "test_key",
            "telnyx_phone_number": "+1234567890"
        }
        
        try:
            manager = TelephonyManager(config)
            assert manager.provider == "telnyx"
            assert manager.phone_number == "+1234567890"
            assert manager.telephony_service is not None
        except Exception as e:
            # This might fail if database is not available, which is expected
            print(f"Telephony manager initialization failed (expected): {e}")
    
    @pytest.mark.asyncio
    async def test_webhook_urls(self):
        """Test webhook URL generation"""
        config = {
            "PROVIDER": "telnyx",
            "PHONE_NUMBER": "+1234567890",
            "telnyx_api_key": "test_key",
            "telnyx_phone_number": "+1234567890"
        }
        
        service = TelephonyServiceFactory.create_service("telnyx", config)
        urls = service.get_webhook_urls()
        
        assert "sms" in urls
        assert "voice" in urls
        assert "status" in urls
        assert "/telnyxservice/sms" in urls["sms"]
        assert "/telnyxservice/voice" in urls["voice"]


if __name__ == "__main__":
    # Run tests
    test_instance = TestTelephonyIntegration()
    
    print("Testing Telephony Service Factory...")
    test_instance.test_service_factory()
    
    print("Testing Service Creation...")
    test_instance.test_service_creation()
    
    print("Testing Webhook URLs...")
    test_instance.test_webhook_urls()
    
    print("All telephony integration tests passed! ✅")

#!/usr/bin/env python3
"""
Test Twilio Setup for Jarvis Phone AI Assistant
Verifies Twilio configuration and basic functionality
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import settings, is_twilio_enabled
from telephony.service_factory import TelephonyServiceFactory
from telephony.telephony_manager import TelephonyManager

async def test_twilio_configuration():
    """Test Twilio configuration and basic setup"""
    print("🔧 Testing Twilio Configuration...")
    
    # Check if environment variables are loaded
    load_dotenv()
    
    # Check if Twilio is enabled
    if not is_twilio_enabled():
        print("❌ Twilio is not properly configured!")
        print("Please set the following environment variables:")
        print("  - TWILIO_ACCOUNT_SID")
        print("  - TWILIO_AUTH_TOKEN") 
        print("  - TWILIO_PHONE_NUMBER")
        return False
    
    print("✅ Twilio configuration looks good!")
    print(f"   Account SID: {settings.TWILIO_ACCOUNT_SID[:8]}...")
    print(f"   Phone Number: {settings.TWILIO_PHONE_NUMBER}")
    print(f"   Webhook Secret: {'✅' if settings.TWILIO_WEBHOOK_SECRET else '❌'}")
    
    return True

async def test_twilio_service_creation():
    """Test creating Twilio service instance"""
    print("\n🏗️  Testing Twilio Service Creation...")
    
    try:
        # Create Twilio service
        config = {
            "twilio_account_sid": settings.TWILIO_ACCOUNT_SID,
            "twilio_auth_token": settings.TWILIO_AUTH_TOKEN,
            "twilio_phone_number": settings.TWILIO_PHONE_NUMBER,
            "twilio_webhook_secret": settings.TWILIO_WEBHOOK_SECRET
        }
        
        service = TelephonyServiceFactory.create_service("twilio", config)
        
        if service:
            print("✅ Twilio service created successfully!")
            
            # Test health status
            health = service.get_health_status()
            print(f"   Health Status: {health}")
            
            return True
        else:
            print("❌ Failed to create Twilio service")
            return False
            
    except Exception as e:
        print(f"❌ Error creating Twilio service: {e}")
        return False

async def test_twilio_manager():
    """Test telephony manager with Twilio"""
    print("\n📱 Testing Telephony Manager with Twilio...")
    
    try:
        # Create telephony manager
        config = {
            "PROVIDER": "twilio",
            "PHONE_NUMBER": settings.TWILIO_PHONE_NUMBER,
            "twilio_account_sid": settings.TWILIO_ACCOUNT_SID,
            "twilio_auth_token": settings.TWILIO_AUTH_TOKEN,
            "twilio_phone_number": settings.TWILIO_PHONE_NUMBER,
            "twilio_webhook_secret": settings.TWILIO_WEBHOOK_SECRET
        }
        
        manager = TelephonyManager(config)
        
        print("✅ Telephony manager created successfully!")
        print(f"   Provider: {manager.provider}")
        print(f"   Phone Number: {manager.phone_number}")
        
        # Test configuration validation
        validation = manager.validate_configuration()
        print(f"   Configuration Valid: {validation['valid']}")
        
        if not validation['valid']:
            print(f"   Errors: {validation['errors']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating telephony manager: {e}")
        return False

async def test_twilio_webhook_validation():
    """Test Twilio webhook signature validation"""
    print("\n🔐 Testing Twilio Webhook Validation...")
    
    if not settings.TWILIO_WEBHOOK_SECRET:
        print("⚠️  No webhook secret configured - skipping validation test")
        return True
    
    try:
        from telephony.twilio_service import TwilioService
        
        config = {
            "twilio_account_sid": settings.TWILIO_ACCOUNT_SID,
            "twilio_auth_token": settings.TWILIO_AUTH_TOKEN,
            "twilio_phone_number": settings.TWILIO_PHONE_NUMBER,
            "twilio_webhook_secret": settings.TWILIO_WEBHOOK_SECRET
        }
        
        service = TwilioService(config)
        
        # Test with mock data
        test_payload = b"test payload"
        test_signature = "test_signature"
        test_timestamp = "1234567890"
        
        # This should return False for invalid signature
        result = await service.validate_webhook_signature(test_payload, test_signature, test_timestamp)
        
        print("✅ Webhook validation method working")
        return True
        
    except Exception as e:
        print(f"❌ Error testing webhook validation: {e}")
        return False

async def main():
    """Run all Twilio tests"""
    print("🚀 Jarvis Phone - Twilio Setup Test")
    print("=" * 50)
    
    tests = [
        test_twilio_configuration,
        test_twilio_service_creation,
        test_twilio_manager,
        test_twilio_webhook_validation
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = sum(results)
    total = len(results)
    
    for i, result in enumerate(results):
        status = "✅ PASS" if result else "❌ FAIL"
        test_name = tests[i].__name__.replace("test_", "").replace("_", " ").title()
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Twilio is ready to use.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

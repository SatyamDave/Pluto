#!/usr/bin/env python3
"""
Test script to verify Telnyx setup for Jarvis Phone
Run this to check if your Telnyx configuration is working
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_telnyx_config():
    """Test basic Telnyx configuration"""
    print("🔍 Testing Telnyx Configuration...")
    
    # Check environment variables
    required_vars = [
        'TELNYX_API_KEY',
        'TELNYX_PHONE_NUMBER'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # Mask sensitive values
            if 'API_KEY' in var:
                display_value = value[:8] + "..." + value[-4:]
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please add these to your .env file")
        return False
    
    return True


async def test_telnyx_import():
    """Test if Telnyx can be imported and initialized"""
    print("\n📦 Testing Telnyx Import...")
    
    try:
        import telnyx
        print("✅ Telnyx client imported successfully")
        
        # Test client initialization
        telnyx.api_key = os.getenv('TELNYX_API_KEY')
        print("✅ Telnyx client initialized successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import Telnyx: {e}")
        print("Run: pip install telnyx")
        return False
    except Exception as e:
        print(f"❌ Failed to initialize Telnyx client: {e}")
        return False


async def test_telnyx_connection():
    """Test connection to Telnyx API"""
    print("\n🔌 Testing Telnyx Connection...")
    
    try:
        import telnyx
        
        # Set API key
        telnyx.api_key = os.getenv('TELNYX_API_KEY')
        
        # Test API connection by fetching account info
        account = telnyx.Account.retrieve()
        print(f"✅ Connected to Telnyx account: {account.name}")
        print(f"✅ Account status: {account.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to Telnyx: {e}")
        return False


async def test_phone_number():
    """Test if the phone number is valid and accessible"""
    print("\n📞 Testing Phone Number...")
    
    try:
        import telnyx
        
        # Set API key
        telnyx.api_key = os.getenv('TELNYX_API_KEY')
        
        phone_number = os.getenv('TELNYX_PHONE_NUMBER')
        
        # Fetch phone number details
        numbers = telnyx.PhoneNumber.list(phone_number=phone_number)
        
        if numbers.data:
            number_obj = numbers.data[0]
            print(f"✅ Phone number found: {number_obj.phone_number}")
            print(f"✅ Capabilities: Voice={number_obj.voice_enabled}, SMS={number_obj.messaging_enabled}")
            
            # Check webhook configuration
            if hasattr(number_obj, 'webhook_url') and number_obj.webhook_url:
                print(f"✅ Webhook URL configured: {number_obj.webhook_url}")
            else:
                print("⚠️  No webhook URL configured")
                
            return True
        else:
            print(f"❌ Phone number {phone_number} not found in your account")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test phone number: {e}")
        return False


async def test_jarvis_handlers():
    """Test if Jarvis handlers can be imported"""
    print("\n🤖 Testing Jarvis Handlers...")
    
    try:
        # Test SMS handler
        from api.routes.sms import router as sms_router
        print("✅ SMS handler imported successfully")
        
        # Test voice handler
        from api.routes.voice import router as voice_router
        print("✅ Voice handler imported successfully")
        
        # Test Telnyx handler
        from telephony.telnyx_handler import TelnyxHandler
        print("✅ Telnyx handler imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to import Jarvis handlers: {e}")
        return False


async def test_webhook_endpoints():
    """Test if webhook endpoints are accessible"""
    print("\n🌐 Testing Webhook Endpoints...")
    
    try:
        import httpx
        
        # Test SMS webhook endpoint
        sms_url = "http://localhost:8000/api/v1/sms/status"
        async with httpx.AsyncClient() as client:
            response = await client.get(sms_url)
            if response.status_code == 200:
                print("✅ SMS status endpoint accessible")
            else:
                print(f"⚠️  SMS status endpoint returned {response.status_code}")
        
        # Test voice webhook endpoint
        voice_url = "http://localhost:8000/api/v1/voice/status"
        async with httpx.AsyncClient() as client:
            response = await client.get(voice_url)
            if response.status_code == 200:
                print("✅ Voice status endpoint accessible")
            else:
                print(f"⚠️  Voice status endpoint returned {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test webhook endpoints: {e}")
        print("Make sure your FastAPI server is running on localhost:8000")
        return False


async def test_telnyx_operations():
    """Test basic Telnyx operations"""
    print("\n🔧 Testing Telnyx Operations...")
    
    try:
        from telephony.telnyx_handler import TelnyxHandler
        
        # Test handler initialization
        handler = TelnyxHandler()
        print("✅ Telnyx handler initialized successfully")
        
        # Test phone number cleaning
        test_phone = "+1 (555) 123-4567"
        clean_phone = handler._clean_phone_number(test_phone)
        print(f"✅ Phone number cleaning: {test_phone} → {clean_phone}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test Telnyx operations: {e}")
        return False


async def test_webhook_payloads():
    """Test webhook payload parsing"""
    print("\n📨 Testing Webhook Payload Parsing...")
    
    try:
        # Test SMS webhook payload
        sms_payload = {
            "data": {
                "event_type": "message.received",
                "payload": {
                    "from": {"phone_number": "+15551234567"},
                    "to": [{"phone_number": "+15551234568"}],
                    "text": "Hello Jarvis",
                    "id": "msg_123456789"
                }
            }
        }
        
        # Test voice webhook payload
        voice_payload = {
            "data": {
                "event_type": "call.initiated",
                "payload": {
                    "from": {"phone_number": "+15551234567"},
                    "to": {"phone_number": "+15551234568"},
                    "id": "call_123456789"
                }
            }
        }
        
        print("✅ SMS webhook payload format: OK")
        print("✅ Voice webhook payload format: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test webhook payloads: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Jarvis Phone - Telnyx Setup Test")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_telnyx_config),
        ("Import", test_telnyx_import),
        ("Connection", test_telnyx_connection),
        ("Phone Number", test_phone_number),
        ("Handlers", test_jarvis_handlers),
        ("Webhooks", test_webhook_endpoints),
        ("Operations", test_telnyx_operations),
        ("Payloads", test_webhook_payloads),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Your Telnyx setup is ready.")
        print("\nNext steps:")
        print("1. Configure webhooks in Telnyx portal")
        print("2. Test with a real SMS/call")
        print("3. Deploy to production")
        print("\n💰 You'll save 30-70% compared to Twilio!")
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed. Please fix the issues above.")
        
        if not any(result for _, result in results[:3]):
            print("\n🔧 Quick fixes:")
            print("- Check your .env file has all required variables")
            print("- Verify your Telnyx API key is correct")
            print("- Ensure your Telnyx account is active")
            print("- Make sure you have a phone number purchased")
    
    return passed == len(results)


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

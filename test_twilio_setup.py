#!/usr/bin/env python3
"""
Test script to verify Twilio setup for Jarvis Phone
Run this to check if your Twilio configuration is working
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_twilio_config():
    """Test basic Twilio configuration"""
    print("🔍 Testing Twilio Configuration...")
    
    # Check environment variables
    required_vars = [
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN', 
        'TWILIO_PHONE_NUMBER'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # Mask sensitive values
            if 'TOKEN' in var:
                display_value = value[:8] + "..." + value[-4:]
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please add these to your .env file")
        return False
    
    return True


async def test_twilio_import():
    """Test if Twilio can be imported and initialized"""
    print("\n📦 Testing Twilio Import...")
    
    try:
        from twilio.rest import Client
        print("✅ Twilio client imported successfully")
        
        # Test client initialization
        client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        print("✅ Twilio client initialized successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import Twilio: {e}")
        print("Run: pip install twilio")
        return False
    except Exception as e:
        print(f"❌ Failed to initialize Twilio client: {e}")
        return False


async def test_twilio_connection():
    """Test connection to Twilio API"""
    print("\n🔌 Testing Twilio Connection...")
    
    try:
        from twilio.rest import Client
        
        client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        
        # Test API connection by fetching account info
        account = client.api.accounts(os.getenv('TWILIO_ACCOUNT_SID')).fetch()
        print(f"✅ Connected to Twilio account: {account.friendly_name}")
        print(f"✅ Account status: {account.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to Twilio: {e}")
        return False


async def test_phone_number():
    """Test if the phone number is valid and accessible"""
    print("\n📞 Testing Phone Number...")
    
    try:
        from twilio.rest import Client
        
        client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        
        phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        # Fetch phone number details
        number = client.incoming_phone_numbers.list(phone_number=phone_number)
        
        if number:
            number_obj = number[0]
            print(f"✅ Phone number found: {number_obj.phone_number}")
            print(f"✅ Capabilities: Voice={number_obj.capabilities.get('voice', False)}, SMS={number_obj.capabilities.get('sms', False)}")
            
            # Check webhook configuration
            if number_obj.webhook_url:
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
        
        # Test Twilio handler
        from telephony.twilio_handler import TwilioHandler
        print("✅ Twilio handler imported successfully")
        
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


async def main():
    """Run all tests"""
    print("🚀 Jarvis Phone - Twilio Setup Test")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_twilio_config),
        ("Import", test_twilio_import),
        ("Connection", test_twilio_connection),
        ("Phone Number", test_phone_number),
        ("Handlers", test_jarvis_handlers),
        ("Webhooks", test_webhook_endpoints),
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
        print("\n🎉 All tests passed! Your Twilio setup is ready.")
        print("\nNext steps:")
        print("1. Configure webhooks in Twilio console")
        print("2. Test with a real SMS/call")
        print("3. Deploy to production")
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed. Please fix the issues above.")
        
        if not any(result for _, result in results[:3]):
            print("\n🔧 Quick fixes:")
            print("- Check your .env file has all required variables")
            print("- Verify your Twilio credentials are correct")
            print("- Ensure your Twilio account is active")
    
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

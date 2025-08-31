#!/usr/bin/env python3
"""
Demo Twilio Functionality for Jarvis Phone AI Assistant
Shows how to send SMS and make voice calls using the Twilio integration
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telephony.telephony_manager import TelephonyManager
from config import settings

async def demo_sms_functionality():
    """Demonstrate SMS functionality"""
    print("📱 SMS Functionality Demo")
    print("=" * 40)
    
    try:
        # Create telephony manager with Twilio
        config = {
            "PROVIDER": "twilio",
            "PHONE_NUMBER": settings.TWILIO_PHONE_NUMBER,
            "twilio_account_sid": settings.TWILIO_ACCOUNT_SID,
            "twilio_auth_token": settings.TWILIO_AUTH_TOKEN,
            "twilio_phone_number": settings.TWILIO_PHONE_NUMBER,
            "twilio_webhook_secret": settings.TWILIO_WEBHOOK_SECRET
        }
        
        manager = TelephonyManager(config)
        print(f"✅ Telephony manager initialized with {manager.provider}")
        
        # Example: Send a reminder SMS
        print("\n📤 Sending reminder SMS...")
        reminder_result = await manager.send_sms(
            to="+15551234567",  # Replace with actual number
            body="🔔 Reminder: Your meeting starts in 15 minutes!",
            user_id=1
        )
        
        if "error" not in reminder_result:
            print(f"✅ SMS sent successfully!")
            print(f"   Message ID: {reminder_result.get('message_id')}")
            print(f"   Status: {reminder_result.get('status')}")
        else:
            print(f"❌ SMS failed: {reminder_result.get('error')}")
        
        # Example: Send a daily digest
        print("\n📤 Sending daily digest SMS...")
        digest_result = await manager.send_sms(
            to="+15551234567",  # Replace with actual number
            body="🌅 Good morning! Here's your daily digest:\n• 3 unread emails\n• 2 meetings today\n• 1 reminder due",
            user_id=1
        )
        
        if "error" not in digest_result:
            print(f"✅ Daily digest sent successfully!")
            print(f"   Message ID: {digest_result.get('message_id')}")
        else:
            print(f"❌ Daily digest failed: {digest_result.get('error')}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error in SMS demo: {e}")
        return False

async def demo_voice_functionality():
    """Demonstrate voice call functionality"""
    print("\n🎯 Voice Call Functionality Demo")
    print("=" * 40)
    
    try:
        # Create telephony manager with Twilio
        config = {
            "PROVIDER": "twilio",
            "PHONE_NUMBER": settings.TWILIO_PHONE_NUMBER,
            "twilio_account_sid": settings.TWILIO_ACCOUNT_SID,
            "twilio_auth_token": settings.TWILIO_AUTH_TOKEN,
            "twilio_phone_number": settings.TWILIO_PHONE_NUMBER,
            "twilio_webhook_secret": settings.TWILIO_WEBHOOK_SECRET
        }
        
        manager = TelephonyManager(config)
        print(f"✅ Telephony manager initialized with {manager.provider}")
        
        # Example: Make a wake-up call
        print("\n📞 Making wake-up call...")
        wakeup_result = await manager.make_call(
            to="+15551234567",  # Replace with actual number
            script="Good morning! This is your wake-up call. Time to start your day!",
            user_id=1,
            call_type="wakeup"
        )
        
        if "error" not in wakeup_result:
            print(f"✅ Wake-up call initiated successfully!")
            print(f"   Call ID: {wakeup_result.get('call_id')}")
            print(f"   Status: {wakeup_result.get('status')}")
        else:
            print(f"❌ Wake-up call failed: {wakeup_result.get('error')}")
        
        # Example: Make a reminder call
        print("\n📞 Making reminder call...")
        reminder_result = await manager.make_call(
            to="+15551234567",  # Replace with actual number
            script="Hello! This is a reminder that your dentist appointment is in one hour. Please confirm you're still coming.",
            user_id=1,
            call_type="reminder"
        )
        
        if "error" not in reminder_result:
            print(f"✅ Reminder call initiated successfully!")
            print(f"   Call ID: {reminder_result.get('call_id')}")
        else:
            print(f"❌ Reminder call failed: {reminder_result.get('error')}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error in voice demo: {e}")
        return False

async def demo_ai_assistant_integration():
    """Demonstrate how Twilio integrates with the AI assistant"""
    print("\n🤖 AI Assistant Integration Demo")
    print("=" * 40)
    
    try:
        from ai_orchestrator import AIOrchestrator
        
        # Initialize AI orchestrator
        orchestrator = AIOrchestrator()
        print("✅ AI Orchestrator initialized")
        
        # Example: Process a user message (simulating SMS)
        print("\n💬 Processing user message through AI...")
        user_message = "Remind me to call mom tomorrow at 2pm"
        
        result = await orchestrator.process_message(
            user_id=1,
            message=user_message,
            message_type="sms"
        )
        
        print(f"✅ Message processed successfully!")
        print(f"   Intent: {result.get('intent')}")
        print(f"   Execution Mode: {result.get('exec_mode')}")
        print(f"   Response: {result.get('response')}")
        
        # Example: Process a proactive action
        print("\n🔄 Running proactive automation...")
        await orchestrator.run_proactive_automation()
        print("✅ Proactive automation completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in AI integration demo: {e}")
        return False

async def demo_webhook_handling():
    """Demonstrate webhook handling for inbound SMS/calls"""
    print("\n🌐 Webhook Handling Demo")
    print("=" * 40)
    
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
        
        # Simulate inbound SMS webhook
        print("📥 Simulating inbound SMS webhook...")
        mock_sms_payload = {
            "MessageSid": "SMxxxxxxxxxxxxxxxxxxxx",
            "From": "+15551234567",
            "To": settings.TWILIO_PHONE_NUMBER,
            "Body": "Hello Jarvis, what's on my calendar today?",
            "MessageTimestamp": "2024-01-01T12:00:00Z"
        }
        
        sms_result = await manager.handle_inbound_sms(mock_sms_payload)
        print(f"✅ SMS webhook handled: {sms_result.get('success')}")
        
        # Simulate inbound voice webhook
        print("📥 Simulating inbound voice webhook...")
        mock_voice_payload = {
            "CallSid": "CAxxxxxxxxxxxxxxxxxxxx",
            "From": "+15551234567",
            "To": settings.TWILIO_PHONE_NUMBER,
            "CallTimestamp": "2024-01-01T12:00:00Z"
        }
        
        voice_result = await manager.handle_inbound_voice(mock_voice_payload)
        print(f"✅ Voice webhook handled: {voice_result.get('success')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in webhook demo: {e}")
        return False

async def main():
    """Run all Twilio functionality demos"""
    print("🚀 Jarvis Phone - Twilio Functionality Demo")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Check if Twilio is configured
    if not settings.TWILIO_ACCOUNT_SID or settings.TWILIO_ACCOUNT_SID == "ACxxxxxxxxxxxxxxxxxxxx":
        print("⚠️  Twilio not configured with real credentials")
        print("Please update your .env file with actual Twilio credentials")
        print("This demo will show the structure but won't make real calls/SMS")
        print()
    
    demos = [
        ("SMS Functionality", demo_sms_functionality),
        ("Voice Functionality", demo_voice_functionality),
        ("AI Assistant Integration", demo_ai_assistant_integration),
        ("Webhook Handling", demo_webhook_handling)
    ]
    
    results = []
    for demo_name, demo_func in demos:
        try:
            print(f"\n🎬 Running {demo_name} Demo...")
            result = await demo_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {demo_name} demo failed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 Demo Results Summary:")
    
    passed = sum(results)
    total = len(results)
    
    for i, result in enumerate(results):
        status = "✅ PASS" if result else "❌ FAIL"
        demo_name = demos[i][0]
        print(f"   {demo_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} demos completed successfully")
    
    if passed == total:
        print("🎉 All demos completed! Twilio integration is working properly.")
        print("\nNext steps:")
        print("1. Configure real Twilio credentials in .env")
        print("2. Set up webhook URLs in Twilio Console")
        print("3. Test with real phone numbers")
        print("4. Deploy to production")
    else:
        print("⚠️  Some demos failed. Check the configuration and try again.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

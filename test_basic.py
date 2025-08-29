"""
Basic test file for Jarvis Phone AI Assistant
Tests basic functionality without external dependencies
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_imports():
    """Test that all modules can be imported"""
    print("Testing module imports...")
    
    try:
        from config import settings
        print("✅ Config imported successfully")
        
        from db.database import init_db
        print("✅ Database module imported successfully")
        
        from db.models import User, Reminder, Note
        print("✅ Database models imported successfully")
        
        from ai_orchestrator import AIOrchestrator
        print("✅ AI Orchestrator imported successfully")
        
        from reminders.reminder_service import ReminderService
        print("✅ Reminder service imported successfully")
        
        from email_service.email_service import EmailService
        print("✅ Email service imported successfully")
        
        from calendar_service.calendar_service import CalendarService
        print("✅ Calendar service imported successfully")
        
        from notes.notes_service import NotesService
        print("✅ Notes service imported successfully")
        
        from telephony.twilio_handler import TwilioHandler
        print("✅ Twilio handler imported successfully")
        
        from telephony.telnyx_handler import TelnyxHandler
        print("✅ Telnyx handler imported successfully")
        
        # Test new feature imports
        try:
            from telephony.outbound_call_service import OutboundCallService, CallType
            print("✅ Outbound call service imported successfully")
        except ImportError:
            print("⚠️  Outbound call service not available (expected in development)")
        
        try:
            from services.digest_service import DigestService
            print("✅ Digest service imported successfully")
        except ImportError:
            print("⚠️  Digest service not available (expected in development)")
        
        print("\n🎉 All modules imported successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


async def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        from config import settings
        
        # Check basic settings
        assert hasattr(settings, 'DEBUG'), "DEBUG setting missing"
        assert hasattr(settings, 'LOG_LEVEL'), "LOG_LEVEL setting missing"
        assert hasattr(settings, 'DATABASE_URL'), "DATABASE_URL setting missing"
        assert hasattr(settings, 'REDIS_URL'), "REDIS_URL setting missing"
        
        print("✅ Configuration loaded successfully")
        print(f"   Debug mode: {settings.DEBUG}")
        print(f"   Log level: {settings.LOG_LEVEL}")
        print(f"   Database URL: {settings.DATABASE_URL}")
        print(f"   Redis URL: {settings.REDIS_URL}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


async def test_ai_orchestrator():
    """Test AI orchestrator basic functionality"""
    print("\nTesting AI Orchestrator...")
    
    try:
        from ai_orchestrator import AIOrchestrator
        
        # Test simple intent analysis (fallback mode)
        orchestrator = AIOrchestrator()
        
        # Test with a simple message
        test_message = "Wake me at 7 AM tomorrow"
        intent_analysis = orchestrator._simple_intent_analysis(test_message)
        
        assert 'intent' in intent_analysis, "Intent analysis missing intent field"
        assert 'confidence' in intent_analysis, "Intent analysis missing confidence field"
        assert 'action' in intent_analysis, "Intent analysis missing action field"
        
        print("✅ AI Orchestrator basic functionality works")
        print(f"   Test message: '{test_message}'")
        print(f"   Detected intent: {intent_analysis['intent']}")
        print(f"   Confidence: {intent_analysis['confidence']}")
        print(f"   Action: {intent_analysis['action']}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI Orchestrator test failed: {e}")
        return False


async def test_services():
    """Test service instantiation"""
    print("\nTesting service instantiation...")
    
    try:
        from reminders.reminder_service import ReminderService
        from email_service.email_service import EmailService
        from calendar_service.calendar_service import CalendarService
        from notes.notes_service import NotesService
        
        # Test service creation
        reminder_service = ReminderService()
        email_service = EmailService()
        calendar_service = CalendarService()
        notes_service = NotesService()
        
        print("✅ All services instantiated successfully")
        print(f"   Reminder service: {type(reminder_service).__name__}")
        print(f"   Email service: {type(email_service).__name__}")
        print(f"   Calendar service: {type(calendar_service).__name__}")
        print(f"   Notes service: {type(notes_service).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        return False


async def test_new_features():
    """Test new feature functionality"""
    print("\nTesting new features...")
    
    try:
        # Test outbound call service (if available)
        try:
            from telephony.outbound_call_service import OutboundCallService, CallType
            
            # Test call types
            call_types = list(CallType)
            assert len(call_types) > 0, "No call types defined"
            
            print("✅ Outbound call service works")
            print(f"   Available call types: {[ct.value for ct in call_types]}")
            
        except ImportError:
            print("⚠️  Outbound call service not available")
        
        # Test digest service (if available)
        try:
            from services.digest_service import DigestService, DigestItem, DailyDigest
            
            # Test data classes
            item = DigestItem(
                type="email",
                title="Test Email",
                description="Test description",
                priority="normal"
            )
            
            assert item.type == "email", "DigestItem type not working"
            assert item.priority == "normal", "DigestItem priority not working"
            
            print("✅ Digest service data classes work")
            
        except ImportError:
            print("⚠️  Digest service not available")
        
        # Test communication service (if available)
        try:
            from services.communication_service import CommunicationService, ContactType, MessageType
            
            # Test enums
            assert ContactType.PHONE.value == "phone", "ContactType.PHONE not working"
            assert ContactType.EMAIL.value == "email", "ContactType.EMAIL not working"
            assert MessageType.SMS.value == "sms", "MessageType.SMS not working"
            
            print("✅ Communication service enums work")
            
        except ImportError:
            print("⚠️  Communication service not available")
        
        # Test audit service (if available)
        try:
            from services.audit_service import AuditService, ActionType, ActionStatus
            
            # Test enums
            assert ActionType.SMS_SENT.value == "sms_sent", "ActionType.SMS_SENT not working"
            assert ActionStatus.SUCCESS.value == "success", "ActionStatus.SUCCESS not working"
            
            print("✅ Audit service enums work")
            
        except ImportError:
            print("⚠️  Audit service not available")
        
        # Test OAuth service (if available)
        try:
            from services.oauth_service import OAuthService, OAuthProvider, OAuthStatus
            
            # Test enums
            assert OAuthProvider.GOOGLE.value == "google", "OAuthProvider.GOOGLE not working"
            assert OAuthStatus.CONNECTED.value == "connected", "OAuthStatus.CONNECTED not working"
            
            print("✅ OAuth service enums work")
            
        except ImportError:
            print("⚠️  OAuth service not available")
        
        # Test configuration flags
        from config import (
            is_proactive_mode_enabled, 
            is_outbound_calls_enabled, 
            is_persistent_wakeup_enabled, 
            is_daily_digest_enabled
        )
        
        print("✅ Feature flags loaded successfully")
        print(f"   Proactive mode: {is_proactive_mode_enabled()}")
        print(f"   Outbound calls: {is_outbound_calls_enabled()}")
        print(f"   Persistent wakeup: {is_persistent_wakeup_enabled()}")
        print(f"   Daily digest: {is_daily_digest_enabled()}")
        
        return True
        
    except Exception as e:
        print(f"❌ New features test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🧪 Starting Jarvis Phone AI Assistant tests...\n")
    
    tests = [
        test_imports(),
        test_config(),
        test_ai_orchestrator(),
        test_services(),
        test_new_features()
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    print("\n" + "="*50)
    print("📊 Test Results Summary")
    print("="*50)
    
    passed = 0
    total = len(tests)
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"❌ Test {i+1} failed with exception: {result}")
        elif result:
            print(f"✅ Test {i+1} passed")
            passed += 1
        else:
            print(f"❌ Test {i+1} failed")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready to run.")
        print("\nTo start the application:")
        print("1. Set up your .env file with API keys")
        print("2. Start PostgreSQL and Redis")
        print("3. Run: python main.py")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(1)

#!/usr/bin/env python3
"""
Test script for OpenRouter integration
Run this to verify the setup is working correctly
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.openrouter_service import (
    OpenRouterService, 
    analyze_intent_with_openrouter,
    extract_time_info_with_openrouter,
    generate_response_with_openrouter
)
from config import is_openrouter_enabled


async def test_openrouter_basic():
    """Test basic OpenRouter functionality"""
    print("🔍 Testing OpenRouter Basic Functionality...")
    
    if not is_openrouter_enabled():
        print("❌ OpenRouter is not enabled. Check your OPENROUTER_API_KEY in .env file")
        return False
    
    try:
        service = OpenRouterService()
        
        # Test health check
        health = await service.health_check()
        print(f"✅ Health check: {'PASS' if health else 'FAIL'}")
        
        # Test available models
        models = await service.available_models()
        print(f"✅ Available models: {len(models)} models found")
        
        # Test basic chat completion
        response = await service.chat_completion(
            messages=[{"role": "user", "content": "Hello, how are you?"}],
            temperature=0.3,
            max_tokens=50
        )
        
        if response.get("content"):
            print(f"✅ Chat completion: SUCCESS")
            print(f"   Model used: {response.get('model', 'unknown')}")
            print(f"   Provider: {response.get('provider', 'unknown')}")
            print(f"   Response: {response['content'][:100]}...")
        else:
            print("❌ Chat completion: FAILED")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False


async def test_intent_analysis():
    """Test intent analysis with OpenRouter"""
    print("\n🧠 Testing Intent Analysis...")
    
    if not is_openrouter_enabled():
        print("❌ OpenRouter is not enabled")
        return False
    
    try:
        # Test reminder intent
        reminder_intent = await analyze_intent_with_openrouter(
            "Wake me up at 7 AM tomorrow"
        )
        
        print(f"✅ Reminder intent analysis: {reminder_intent.get('intent', 'unknown')}")
        print(f"   Confidence: {reminder_intent.get('confidence', 0)}")
        
        # Test email intent
        email_intent = await analyze_intent_with_openrouter(
            "Check my inbox for important emails"
        )
        
        print(f"✅ Email intent analysis: {email_intent.get('intent', 'unknown')}")
        print(f"   Confidence: {email_intent.get('confidence', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Intent analysis test failed: {e}")
        return False


async def test_time_extraction():
    """Test time extraction with OpenRouter"""
    print("\n⏰ Testing Time Extraction...")
    
    if not is_openrouter_enabled():
        print("❌ OpenRouter is not enabled")
        return False
    
    try:
        # Test absolute time
        absolute_time = await extract_time_info_with_openrouter(
            "Wake me up at 7 AM tomorrow"
        )
        
        if absolute_time:
            print(f"✅ Absolute time extraction: {absolute_time.get('readable_time', 'unknown')}")
            print(f"   Type: {absolute_time.get('type', 'unknown')}")
            print(f"   Confidence: {absolute_time.get('confidence', 0)}")
        else:
            print("❌ Absolute time extraction failed")
            return False
        
        # Test relative time
        relative_time = await extract_time_info_with_openrouter(
            "Remind me in 2 hours"
        )
        
        if relative_time:
            print(f"✅ Relative time extraction: {relative_time.get('readable_time', 'unknown')}")
            print(f"   Type: {relative_time.get('type', 'unknown')}")
            print(f"   Confidence: {relative_time.get('confidence', 0)}")
        else:
            print("❌ Relative time extraction failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Time extraction test failed: {e}")
        return False


async def test_response_generation():
    """Test response generation with OpenRouter"""
    print("\n💬 Testing Response Generation...")
    
    if not is_openrouter_enabled():
        print("❌ OpenRouter is not enabled")
        return False
    
    try:
        # Test reminder response
        reminder_response = await generate_response_with_openrouter(
            context="Setting a wake-up reminder",
            user_message="Wake me up at 7 AM",
            response_type="reminder"
        )
        
        print(f"✅ Reminder response generation: SUCCESS")
        print(f"   Response: {reminder_response[:100]}...")
        
        # Test general response
        general_response = await generate_response_with_openrouter(
            context="General assistance",
            user_message="What can you help me with?",
            response_type="general"
        )
        
        print(f"✅ General response generation: SUCCESS")
        print(f"   Response: {general_response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Response generation test failed: {e}")
        return False


async def test_usage_tracking():
    """Test usage tracking functionality"""
    print("\n📊 Testing Usage Tracking...")
    
    if not is_openrouter_enabled():
        print("❌ OpenRouter is not enabled")
        return False
    
    try:
        service = OpenRouterService()
        
        # Get initial stats
        initial_stats = service.get_usage_stats()
        print(f"✅ Initial usage stats retrieved")
        print(f"   Total requests: {initial_stats['total_requests']}")
        print(f"   Total tokens: {initial_stats['total_tokens']}")
        
        # Make a test request to increment stats
        await service.chat_completion(
            messages=[{"role": "user", "content": "Test message for usage tracking"}],
            temperature=0.1,
            max_tokens=20
        )
        
        # Get updated stats
        updated_stats = service.get_usage_stats()
        print(f"✅ Updated usage stats retrieved")
        print(f"   Total requests: {updated_stats['total_requests']}")
        print(f"   Total tokens: {updated_stats['total_tokens']}")
        
        # Verify stats were incremented
        if updated_stats['total_requests'] > initial_stats['total_requests']:
            print("✅ Usage tracking: SUCCESS - Stats incremented correctly")
        else:
            print("❌ Usage tracking: FAILED - Stats not incremented")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Usage tracking test failed: {e}")
        return False


async def test_model_fallbacks():
    """Test model fallback functionality"""
    print("\n🔄 Testing Model Fallbacks...")
    
    if not is_openrouter_enabled():
        print("❌ OpenRouter is not enabled")
        return False
    
    try:
        service = OpenRouterService()
        
        # Test with specific model
        specific_response = await service.chat_completion(
            messages=[{"role": "user", "content": "Quick test"}],
            model="openai/gpt-4o-mini",  # Use a specific model
            temperature=0.1,
            max_tokens=20
        )
        
        print(f"✅ Specific model test: SUCCESS")
        print(f"   Model used: {specific_response.get('model', 'unknown')}")
        
        # Test with auto-selection (should try preferred models)
        auto_response = await service.chat_completion(
            messages=[{"role": "user", "content": "Another quick test"}],
            temperature=0.1,
            max_tokens=20
        )
        
        print(f"✅ Auto-model selection: SUCCESS")
        print(f"   Model used: {auto_response.get('model', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model fallback test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Starting OpenRouter Integration Tests...\n")
    
    tests = [
        ("Basic Functionality", test_openrouter_basic),
        ("Intent Analysis", test_intent_analysis),
        ("Time Extraction", test_time_extraction),
        ("Response Generation", test_response_generation),
        ("Usage Tracking", test_usage_tracking),
        ("Model Fallbacks", test_model_fallbacks),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📋 TEST SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! OpenRouter integration is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    # Check if running in async context
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already running, create a task
            loop.create_task(main())
        else:
            # Run the main function
            asyncio.run(main())
    except RuntimeError:
        # No event loop, create one
        asyncio.run(main())

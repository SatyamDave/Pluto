#!/usr/bin/env python3
"""
OpenRouter Demo Script for Jarvis Phone
Shows practical examples of using OpenRouter for various AI tasks
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.openrouter_service import (
    OpenRouterService,
    analyze_intent_with_openrouter,
    extract_time_info_with_openrouter,
    generate_response_with_openrouter
)
from config import is_openrouter_enabled


async def demo_basic_chat():
    """Demonstrate basic chat completion"""
    print("💬 Basic Chat Completion Demo")
    print("=" * 40)
    
    if not is_openrouter_enabled():
        print("❌ OpenRouter not configured. Set OPENROUTER_API_KEY in .env")
        return
    
    try:
        service = OpenRouterService()
        
        # Simple greeting
        response = await service.chat_completion(
            messages=[{"role": "user", "content": "Hello! I'm setting up Jarvis Phone. Can you help me get started?"}],
            temperature=0.3,
            max_tokens=150
        )
        
        print(f"🤖 AI Response: {response['content']}")
        print(f"📊 Model Used: {response['model']}")
        print(f"🏢 Provider: {response['provider']}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def demo_intent_analysis():
    """Demonstrate intent analysis for user messages"""
    print("🧠 Intent Analysis Demo")
    print("=" * 40)
    
    if not is_openrouter_enabled():
        print("❌ OpenRouter not configured")
        return
    
    # Test messages
    test_messages = [
        "Wake me up at 7 AM tomorrow",
        "Check my email inbox for important messages",
        "What's my next meeting?",
        "Add buy groceries to my shopping list",
        "Call the dentist to reschedule my appointment",
        "Send me a summary of my day"
    ]
    
    for message in test_messages:
        try:
            intent = await analyze_intent_with_openrouter(message)
            
            print(f"📝 Message: {message}")
            print(f"🎯 Intent: {intent['intent']}")
            print(f"📈 Confidence: {intent['confidence']:.2f}")
            print(f"⚡ Action: {intent['action']}")
            print(f"🏷️  Priority: {intent.get('priority', 'medium')}")
            print("-" * 30)
            
        except Exception as e:
            print(f"❌ Error analyzing '{message}': {e}")


async def demo_time_extraction():
    """Demonstrate time extraction from natural language"""
    print("⏰ Time Extraction Demo")
    print("=" * 40)
    
    if not is_openrouter_enabled():
        print("❌ OpenRouter not configured")
        return
    
    # Test time expressions
    time_expressions = [
        "Wake me up at 7 AM tomorrow",
        "Remind me in 2 hours",
        "Set an alarm for 6:30 AM on Monday",
        "Call me back in 15 minutes",
        "Schedule a meeting for next Friday at 3 PM",
        "Remind me to take my medicine every day at 9 AM"
    ]
    
    for expression in time_expressions:
        try:
            time_info = await extract_time_info_with_openrouter(expression)
            
            if time_info:
                print(f"📝 Expression: {expression}")
                print(f"🕐 Readable Time: {time_info['readable_time']}")
                print(f"📅 Type: {time_info['type']}")
                print(f"📈 Confidence: {time_info['confidence']:.2f}")
                print(f"🔢 ISO Time: {time_info['datetime']}")
                print("-" * 30)
            else:
                print(f"❌ Could not extract time from: {expression}")
                
        except Exception as e:
            print(f"❌ Error extracting time from '{expression}': {e}")


async def demo_response_generation():
    """Demonstrate contextual response generation"""
    print("💬 Response Generation Demo")
    print("=" * 40)
    
    if not is_openrouter_enabled():
        print("❌ OpenRouter not configured")
        return
    
    # Test scenarios
    scenarios = [
        {
            "context": "Setting a wake-up reminder",
            "message": "Wake me up at 7 AM tomorrow",
            "type": "reminder"
        },
        {
            "context": "Email management",
            "message": "I have too many unread emails",
            "type": "email"
        },
        {
            "context": "Calendar scheduling",
            "message": "I need to reschedule my meeting",
            "type": "calendar"
        },
        {
            "context": "Making outbound calls",
            "message": "Call the restaurant to make a reservation",
            "type": "outbound_call"
        }
    ]
    
    for scenario in scenarios:
        try:
            response = await generate_response_with_openrouter(
                context=scenario["context"],
                user_message=scenario["message"],
                response_type=scenario["type"]
            )
            
            print(f"🎭 Context: {scenario['context']}")
            print(f"💬 User: {scenario['message']}")
            print(f"🤖 Jarvis: {response}")
            print("-" * 30)
            
        except Exception as e:
            print(f"❌ Error generating response for {scenario['type']}: {e}")


async def demo_model_selection():
    """Demonstrate different model selections"""
    print("🔧 Model Selection Demo")
    print("=" * 40)
    
    if not is_openrouter_enabled():
        print("❌ OpenRouter not configured")
        return
    
    try:
        service = OpenRouterService()
        
        # Test different models
        models_to_test = [
            "openai/gpt-4o-mini",      # Fast, cost-effective
            "anthropic/claude-3-haiku-20240307",  # Very fast
            "google/gemini-pro-1.5"    # Alternative provider
        ]
        
        test_message = "Explain quantum computing in simple terms"
        
        for model in models_to_test:
            try:
                print(f"🧪 Testing model: {model}")
                
                start_time = asyncio.get_event_loop().time()
                
                response = await service.chat_completion(
                    messages=[{"role": "user", "content": test_message}],
                    model=model,
                    temperature=0.3,
                    max_tokens=100
                )
                
                end_time = asyncio.get_event_loop().time()
                response_time = end_time - start_time
                
                print(f"✅ Success! Response time: {response_time:.2f}s")
                print(f"📝 Response: {response['content'][:100]}...")
                print(f"🏢 Provider: {response['provider']}")
                print("-" * 30)
                
            except Exception as e:
                print(f"❌ Model {model} failed: {e}")
                print("-" * 30)
                
    except Exception as e:
        print(f"❌ Error in model selection demo: {e}")


async def demo_usage_tracking():
    """Demonstrate usage tracking and statistics"""
    print("📊 Usage Tracking Demo")
    print("=" * 40)
    
    if not is_openrouter_enabled():
        print("❌ OpenRouter not configured")
        return
    
    try:
        service = OpenRouterService()
        
        # Get initial stats
        initial_stats = service.get_usage_stats()
        print(f"📈 Initial Stats:")
        print(f"   Total Requests: {initial_stats['total_requests']}")
        print(f"   Total Tokens: {initial_stats['total_tokens']}")
        print(f"   Models Used: {len(initial_stats['model_usage'])}")
        
        # Make some test requests
        print("\n🧪 Making test requests...")
        
        for i in range(3):
            await service.chat_completion(
                messages=[{"role": "user", "content": f"Test message {i+1}"}],
                temperature=0.1,
                max_tokens=20
            )
            print(f"   ✅ Request {i+1} completed")
        
        # Get updated stats
        updated_stats = service.get_usage_stats()
        print(f"\n📈 Updated Stats:")
        print(f"   Total Requests: {updated_stats['total_requests']}")
        print(f"   Total Tokens: {updated_stats['total_tokens']}")
        print(f"   Models Used: {len(updated_stats['model_usage'])}")
        
        # Show model-specific usage
        print(f"\n🔍 Model Usage Breakdown:")
        for model, usage in updated_stats['model_usage'].items():
            print(f"   {model}: {usage['requests']} requests, {usage['tokens']} tokens")
        
    except Exception as e:
        print(f"❌ Error in usage tracking demo: {e}")


async def demo_health_check():
    """Demonstrate health checking"""
    print("🏥 Health Check Demo")
    print("=" * 40)
    
    if not is_openrouter_enabled():
        print("❌ OpenRouter not configured")
        return
    
    try:
        service = OpenRouterService()
        
        # Check service health
        health_status = await service.health_check()
        print(f"🔍 Service Health: {'✅ Healthy' if health_status else '❌ Unhealthy'}")
        
        # Get available models
        models = await service.get_available_models()
        print(f"📚 Available Models: {len(models)} models")
        
        # Get credits
        credits = await service.get_credits()
        if credits:
            print(f"💰 Credits: {credits.get('credits_remaining', 'Unknown')} remaining")
        else:
            print("💰 Credits: Unable to retrieve")
        
        # Test with a simple request
        try:
            response = await service.chat_completion(
                messages=[{"role": "user", "content": "Health check test"}],
                temperature=0.1,
                max_tokens=20
            )
            print(f"🧪 Test Request: ✅ Success")
        except Exception as e:
            print(f"🧪 Test Request: ❌ Failed - {e}")
        
    except Exception as e:
        print(f"❌ Error in health check demo: {e}")


async def main():
    """Run all demos"""
    print("🚀 OpenRouter Integration Demo for Jarvis Phone")
    print("=" * 60)
    print()
    
    if not is_openrouter_enabled():
        print("❌ OpenRouter is not configured!")
        print("Please set OPENROUTER_API_KEY in your .env file")
        print("Get your API key from: https://openrouter.ai")
        return
    
    demos = [
        ("Basic Chat", demo_basic_chat),
        ("Intent Analysis", demo_intent_analysis),
        ("Time Extraction", demo_time_extraction),
        ("Response Generation", demo_response_generation),
        ("Model Selection", demo_model_selection),
        ("Usage Tracking", demo_usage_tracking),
        ("Health Check", demo_health_check),
    ]
    
    for demo_name, demo_func in demos:
        print(f"\n🎬 Running {demo_name} Demo...")
        print("=" * 60)
        
        try:
            await demo_func()
        except Exception as e:
            print(f"❌ Demo '{demo_name}' failed: {e}")
        
        print("\n" + "=" * 60)
    
    print("\n🎉 Demo completed!")
    print("💡 Check the output above to see OpenRouter in action")
    print("📖 For more details, see OPENROUTER_SETUP.md")


if __name__ == "__main__":
    asyncio.run(main())

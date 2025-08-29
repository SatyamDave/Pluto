#!/usr/bin/env python3
"""
Simple test for Pluto AI Assistant
"""

import asyncio
from ai_orchestrator import AIOrchestrator

async def test_pluto():
    """Test basic Pluto functionality"""
    print("🧪 Testing Pluto AI Assistant...")
    
    try:
        # Create orchestrator
        orchestrator = AIOrchestrator()
        print("✅ AI Orchestrator created successfully")
        
        # Test message processing
        test_message = "remind me to call mom tomorrow at 2pm"
        print(f"📱 Testing message: '{test_message}'")
        
        result = await orchestrator.process_message(
            user_id=1,  # Test user
            message=test_message,
            message_type="sms"
        )
        
        print(f"🎯 Intent: {result.get('intent', {}).get('intent', 'unknown')}")
        print(f"🤖 Response: {result.get('response', 'No response')}")
        print(f"📊 Status: {result.get('status', 'unknown')}")
        
        print("✅ Pluto test completed successfully!")
        
    except Exception as e:
        print(f"❌ Pluto test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pluto())

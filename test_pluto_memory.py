#!/usr/bin/env python3
"""
Test Pluto's Memory and Habit Learning Features
"""

import asyncio
import logging
from datetime import datetime, timedelta

from services.memory_manager import memory_manager
from services.habit_engine import habit_engine
from services.proactive_agent import proactive_agent
from ai_orchestrator import AIOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_pluto_memory():
    """Test Pluto's memory capabilities"""
    print("🧠 Testing Pluto's Memory System")
    print("=" * 50)
    
    user_id = "test_user_1"
    
    # Test 1: Store memories
    print("\n1. Storing memories...")
    memory_ids = []
    
    memories_to_store = [
        ("reminder", "Wake me up at 7 AM tomorrow"),
        ("reminder", "Wake me up at 7 AM on Monday"),
        ("reminder", "Wake me up at 7 AM on Tuesday"),
        ("schedule", "Meeting with John at 3 PM"),
        ("schedule", "Meeting with Sarah at 2 PM"),
        ("habit", "Check email every 2 hours"),
        ("habit", "Check email every 2 hours"),
        ("habit", "Check email every 2 hours"),
        ("sms", "Hello Pluto, how are you?"),
        ("sms", "Pluto, remind me to call the dentist"),
        ("email", "New email from boss about project update"),
        ("email", "Urgent email from client about deadline")
    ]
    
    for memory_type, content in memories_to_store:
        memory_id = await memory_manager.store_memory(
            user_id=user_id,
            memory_type=memory_type,
            content=content
        )
        memory_ids.append(memory_id)
        print(f"   ✅ Stored {memory_type}: {content[:50]}...")
    
    # Test 2: Recall memories
    print("\n2. Recalling memories...")
    
    # Recent memories
    recent_memories = await memory_manager.recall_memory(
        user_id=user_id,
        limit=5
    )
    print(f"   📝 Recent memories: {len(recent_memories)} found")
    
    # Semantic search
    semantic_results = await memory_manager.recall_memory(
        user_id=user_id,
        query="wake up time",
        limit=3
    )
    print(f"   🔍 Semantic search for 'wake up time': {len(semantic_results)} results")
    
    # Test 3: User preferences
    print("\n3. Setting user preferences...")
    
    preferences = {
        "preferred_wake_time": "7:00 AM",
        "timezone": "PST",
        "notification_frequency": "high",
        "coffee_preference": "dark roast"
    }
    
    for key, value in preferences.items():
        await memory_manager.set_user_preference(user_id, key, value)
        print(f"   ⚙️ Set {key}: {value}")
    
    # Test 4: Get memory summary
    print("\n4. Memory summary...")
    summary = await memory_manager.get_memory_summary(user_id)
    print(f"   📊 Total memories: {summary['total_memories']}")
    print(f"   📈 Recent activity: {summary['recent_activity']}")
    print(f"   🏷️ Type counts: {summary['type_counts']}")

async def test_pluto_habits():
    """Test Pluto's habit learning capabilities"""
    print("\n🔄 Testing Pluto's Habit Learning")
    print("=" * 50)
    
    user_id = "test_user_1"
    
    # Test 1: Analyze habits
    print("\n1. Analyzing user habits...")
    habits = await habit_engine.analyze_user_habits(user_id)
    print(f"   🧠 Detected {len(habits)} habits")
    
    for habit in habits:
        pattern_type = habit["pattern_type"]
        confidence = habit["confidence"]
        observations = habit["observations"]
        print(f"   📊 {pattern_type}: {confidence:.2f} confidence ({observations} observations)")
    
    # Test 2: Get user habits
    print("\n2. Getting user habits...")
    user_habits = await habit_engine.get_user_habits(user_id)
    print(f"   📋 Stored {len(user_habits)} habits")
    
    for habit in user_habits:
        pattern_data = habit["pattern_data"]
        if habit["pattern_type"] == "time_based":
            time = pattern_data.get("time", "unknown")
            print(f"   ⏰ Time-based: {time}")
        elif habit["pattern_type"] == "frequency_based":
            frequency = pattern_data.get("frequency", "unknown")
            print(f"   🔄 Frequency-based: {frequency}")
    
    # Test 3: Proactive suggestions
    print("\n3. Generating proactive suggestions...")
    suggestions = await habit_engine.suggest_proactive_actions(user_id)
    print(f"   💡 Generated {len(suggestions)} suggestions")
    
    for suggestion in suggestions:
        print(f"   📢 {suggestion['title']}: {suggestion['message']}")

async def test_pluto_proactive():
    """Test Pluto's proactive capabilities"""
    print("\n🚀 Testing Pluto's Proactive Features")
    print("=" * 50)
    
    user_id = "test_user_1"
    
    # Test 1: Morning digest
    print("\n1. Generating morning digest...")
    digest = await proactive_agent.generate_morning_digest(user_id)
    print(f"   🌅 {digest}")
    
    # Test 2: Proactive suggestions
    print("\n2. Getting proactive suggestions...")
    suggestions = await proactive_agent.suggest_proactive_actions(user_id)
    print(f"   💭 {len(suggestions)} proactive suggestions available")
    
    # Test 3: Store proactive action
    print("\n3. Storing proactive action...")
    await proactive_agent.store_proactive_action(
        user_id=user_id,
        action_type="test_action",
        message="This is a test proactive action",
        metadata={"test": True}
    )
    print("   ✅ Proactive action stored")

async def test_pluto_orchestrator():
    """Test Pluto's AI orchestrator with memory"""
    print("\n🤖 Testing Pluto's AI Orchestrator with Memory")
    print("=" * 50)
    
    user_id = "test_user_1"
    orchestrator = AIOrchestrator()
    
    # Test 1: Process message with memory
    print("\n1. Processing message with memory context...")
    response = await orchestrator.process_message(
        user_id=user_id,
        message="What time do I usually wake up?",
        message_type="sms"
    )
    
    print(f"   💬 Response: {response['response']}")
    print(f"   🎯 Intent: {response['intent'].get('intent', 'unknown')}")
    print(f"   📊 Context used: {response['context_used']} recent interactions")
    print(f"   💡 Proactive suggestions: {len(response['proactive_suggestions'])}")
    
    # Test 2: Get memory summary
    print("\n2. Getting user memory summary...")
    summary = await orchestrator.get_user_memory_summary(user_id)
    
    if "error" not in summary:
        memory_info = summary["memory"]
        habits_info = summary["habits"]
        preferences_info = summary["preferences"]
        
        print(f"   🧠 Memory: {memory_info['total_memories']} total, {memory_info['recent_activity']} recent")
        print(f"   🔄 Habits: {habits_info['count']} detected, avg confidence: {habits_info['confidence_avg']:.2f}")
        print(f"   ⚙️ Preferences: {preferences_info['count']} stored")
    else:
        print(f"   ❌ Error: {summary['error']}")
    
    # Test 3: Set user preference
    print("\n3. Setting user preference...")
    success = await orchestrator.set_user_preference(
        user_id=user_id,
        key="test_preference",
        value="test_value"
    )
    print(f"   ✅ Preference set: {success}")
    
    # Test 4: Get morning digest
    print("\n4. Getting morning digest...")
    digest = await orchestrator.get_morning_digest(user_id)
    print(f"   🌅 {digest}")

async def main():
    """Run all Pluto tests"""
    print("🤖 PLUTO - AI PHONE ASSISTANT")
    print("Memory and Habit Learning Test Suite")
    print("=" * 60)
    
    try:
        # Test memory system
        await test_pluto_memory()
        
        # Test habit learning
        await test_pluto_habits()
        
        # Test proactive features
        await test_pluto_proactive()
        
        # Test AI orchestrator
        await test_pluto_orchestrator()
        
        print("\n" + "=" * 60)
        print("✅ All Pluto tests completed successfully!")
        print("🚀 Pluto is ready with memory, habit learning, and proactive features!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.error(f"Test error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())

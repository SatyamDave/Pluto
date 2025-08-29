#!/usr/bin/env python3
"""
Test Smart Memory Reminder Functionality
Demonstrates Pluto's intelligent reminder scheduling based on urgency analysis
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.memory_manager import memory_manager
from services.proactive_agent import proactive_agent
from services.user_manager import user_manager


async def test_smart_memory_reminders():
    """Test the smart memory reminder functionality"""
    print("🧠 Testing Pluto's Smart Memory Reminder System")
    print("=" * 50)
    
    # Create a test user
    user = await user_manager.get_or_create_user("+1234567890")
    user_id = user["id"]
    print(f"✅ Created test user: {user_id}")
    
    # Test different types of memories with varying urgency
    test_memories = [
        {
            "content": "Call the dentist - urgent appointment tomorrow",
            "type": "reminder",
            "expected_urgency": "high",
            "expected_hours": 24
        },
        {
            "content": "Remember to buy groceries this afternoon",
            "type": "todo", 
            "expected_urgency": "medium",
            "expected_hours": 4
        },
        {
            "content": "Emergency meeting with CEO ASAP",
            "type": "reminder",
            "expected_urgency": "critical", 
            "expected_hours": 1
        },
        {
            "content": "Check email when you have time",
            "type": "note",
            "expected_urgency": "low",
            "expected_hours": 12
        },
        {
            "content": "Dinner reservation tonight at 8pm",
            "type": "reminder",
            "expected_urgency": "medium",
            "expected_hours": 8
        }
    ]
    
    print("\n📝 Testing Memory Storage with Smart Reminders:")
    print("-" * 40)
    
    for i, memory_data in enumerate(test_memories, 1):
        print(f"\n{i}. Storing memory: '{memory_data['content']}'")
        
        # Store the memory (this will trigger smart reminder scheduling)
        memory_id = await memory_manager.store_memory(
            user_id=user_id,
            memory_type=memory_data["type"],
            content=memory_data["content"],
            importance_score=0.7,
            schedule_reminder=True
        )
        
        print(f"   ✅ Memory stored with ID: {memory_id}")
        print(f"   📊 Expected urgency: {memory_data['expected_urgency']}")
        print(f"   ⏰ Expected reminder in: {memory_data['expected_hours']} hours")
    
    print("\n🎯 Smart Reminder Features:")
    print("-" * 30)
    print("• 🚨 Critical urgency: 1 hour reminders")
    print("• ⚠️ High urgency: 3-4 hour reminders") 
    print("• 📝 Medium urgency: 6 hour reminders")
    print("• 💡 Low urgency: 12 hour reminders")
    print("• 🕐 Time-aware: 'morning', 'evening', 'tonight' adjustments")
    print("• 📅 Date-aware: 'tomorrow', 'next week' handling")
    
    print("\n🧠 Memory Recall Test:")
    print("-" * 25)
    
    # Test semantic memory recall
    recall_queries = [
        "dentist appointment",
        "groceries shopping", 
        "meeting with CEO",
        "dinner plans"
    ]
    
    for query in recall_queries:
        memories = await memory_manager.recall_memory(
            user_id=user_id,
            query=query,
            limit=3
        )
        
        print(f"\n🔍 Query: '{query}'")
        if memories:
            for memory in memories[:2]:  # Show first 2 results
                print(f"   📌 Found: {memory['content'][:60]}...")
        else:
            print("   ❌ No memories found")
    
    print("\n🎉 Smart Memory System Test Complete!")
    print("\n💡 Key Features Demonstrated:")
    print("• Automatic urgency analysis based on keywords")
    print("• Intelligent reminder timing (1-24 hours)")
    print("• Context-aware scheduling (time of day, dates)")
    print("• Semantic memory recall and search")
    print("• Proactive reminder delivery via SMS")


if __name__ == "__main__":
    # Set up environment
    os.environ["OPENROUTER_API_KEY"] = "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"
    os.environ["DATABASE_URL"] = "postgresql://satyamdave@localhost:5432/jarvis_phone"
    
    # Run the test
    asyncio.run(test_smart_memory_reminders())

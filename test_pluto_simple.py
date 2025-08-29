#!/usr/bin/env python3
"""
Simple Pluto Test - Demonstrates Pluto's capabilities without external dependencies
"""

import asyncio
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimplePlutoMemory:
    """Simple in-memory implementation for testing"""
    
    def __init__(self):
        self.memories = {}
        self.preferences = {}
        self.habits = []
    
    async def store_memory(self, user_id: str, memory_type: str, content: str, metadata=None):
        """Store a memory"""
        if user_id not in self.memories:
            self.memories[user_id] = []
        
        memory = {
            "id": len(self.memories[user_id]) + 1,
            "type": memory_type,
            "content": content,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        }
        self.memories[user_id].append(memory)
        print(f"🧠 Stored memory: {memory_type} - {content[:50]}...")
        return memory["id"]
    
    async def recall_memory(self, user_id: str, query=None, memory_type=None, limit=10):
        """Recall memories"""
        if user_id not in self.memories:
            return []
        
        memories = self.memories[user_id]
        
        if memory_type:
            memories = [m for m in memories if m["type"] == memory_type]
        
        if query:
            # Simple keyword search
            memories = [m for m in memories if query.lower() in m["content"].lower()]
        
        return memories[-limit:] if memories else []
    
    async def set_preference(self, user_id: str, key: str, value):
        """Set user preference"""
        if user_id not in self.preferences:
            self.preferences[user_id] = {}
        
        self.preferences[user_id][key] = value
        print(f"⚙️ Set preference: {key} = {value}")
    
    async def get_preferences(self, user_id: str):
        """Get user preferences"""
        return self.preferences.get(user_id, {})

class SimpleHabitEngine:
    """Simple habit detection for testing"""
    
    def __init__(self, memory):
        self.memory = memory
        self.habits = {}
    
    async def analyze_habits(self, user_id: str):
        """Analyze user habits"""
        memories = await self.memory.recall_memory(user_id, limit=100)
        
        # Simple pattern detection
        time_patterns = {}
        frequency_patterns = {}
        
        for memory in memories:
            content = memory["content"].lower()
            
            # Time-based patterns
            if "wake up" in content or "alarm" in content:
                time_match = self._extract_time(content)
                if time_match:
                    if time_match not in time_patterns:
                        time_patterns[time_match] = 0
                    time_patterns[time_match] += 1
            
            # Frequency patterns
            memory_type = memory["type"]
            if memory_type not in frequency_patterns:
                frequency_patterns[memory_type] = 0
            frequency_patterns[memory_type] += 1
        
        # Store detected habits
        habits = []
        
        for time, count in time_patterns.items():
            if count >= 2:  # At least 2 occurrences
                habits.append({
                    "pattern_type": "time_based",
                    "pattern_data": {"time": time, "frequency": count},
                    "confidence": min(0.9, count / 5.0),
                    "observations": count
                })
        
        for memory_type, count in frequency_patterns.items():
            if count >= 3:  # At least 3 occurrences
                habits.append({
                    "pattern_type": "frequency_based",
                    "pattern_data": {"memory_type": memory_type, "frequency": count},
                    "confidence": min(0.8, count / 10.0),
                    "observations": count
                })
        
        self.habits[user_id] = habits
        print(f"🔄 Detected {len(habits)} habits for user {user_id}")
        return habits
    
    def _extract_time(self, content: str):
        """Extract time from content"""
        import re
        time_patterns = [
            r"(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)?",
            r"(\d{1,2})\s*(am|pm|AM|PM)",
            r"wake\s+up\s+at\s+(\d{1,2})",
            r"alarm\s+at\s+(\d{1,2})"
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, content)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2)) if match.group(2) else 0
                
                # Handle AM/PM
                if match.group(3):
                    if match.group(3).lower() == "pm" and hour != 12:
                        hour += 12
                    elif match.group(3).lower() == "am" and hour == 12:
                        hour = 0
                
                return f"{hour:02d}:{minute:02d}"
        
        return None
    
    async def get_habits(self, user_id: str):
        """Get user habits"""
        return self.habits.get(user_id, [])
    
    async def suggest_actions(self, user_id: str):
        """Generate proactive suggestions"""
        habits = await self.get_habits(user_id)
        suggestions = []
        
        for habit in habits:
            if habit["confidence"] >= 0.6:
                if habit["pattern_type"] == "time_based":
                    time = habit["pattern_data"]["time"]
                    suggestions.append({
                        "type": "habit_reminder",
                        "title": "Habit Reminder",
                        "message": f"It's {time} - time for your usual activity!",
                        "priority": "medium"
                    })
                elif habit["pattern_type"] == "frequency_based":
                    memory_type = habit["pattern_data"]["memory_type"]
                    suggestions.append({
                        "type": "frequency_reminder",
                        "title": "Regular Activity",
                        "message": f"Time for your regular {memory_type} activity",
                        "priority": "low"
                    })
        
        return suggestions

class SimplePlutoOrchestrator:
    """Simple Pluto orchestrator for testing"""
    
    def __init__(self):
        self.memory = SimplePlutoMemory()
        self.habit_engine = SimpleHabitEngine(self.memory)
    
    async def process_message(self, user_id: str, message: str, message_type="sms"):
        """Process a user message"""
        print(f"\n💬 Processing: {message}")
        
        # Store the message
        await self.memory.store_memory(user_id, message_type, message)
        
        # Get recent context
        recent_memories = await self.memory.recall_memory(user_id, limit=3)
        preferences = await self.memory.get_preferences(user_id)
        
        # Analyze intent (simple keyword matching)
        intent = self._analyze_intent(message)
        
        # Get proactive suggestions
        suggestions = await self.habit_engine.suggest_actions(user_id)
        
        # Generate response
        response = self._generate_response(message, intent, recent_memories, preferences, suggestions)
        
        # Store response
        await self.memory.store_memory(user_id, "response", response)
        
        # Analyze habits periodically
        if len(recent_memories) % 5 == 0:
            await self.habit_engine.analyze_habits(user_id)
        
        return {
            "response": response,
            "intent": intent,
            "proactive_suggestions": suggestions,
            "context_used": len(recent_memories)
        }
    
    def _analyze_intent(self, message: str):
        """Simple intent analysis"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["wake", "alarm", "remind"]):
            return {"intent": "reminder", "confidence": 0.8}
        elif any(word in message_lower for word in ["email", "mail"]):
            return {"intent": "email", "confidence": 0.7}
        elif any(word in message_lower for word in ["schedule", "meeting", "calendar"]):
            return {"intent": "calendar", "confidence": 0.7}
        elif any(word in message_lower for word in ["what", "when", "how"]):
            return {"intent": "question", "confidence": 0.6}
        else:
            return {"intent": "general", "confidence": 0.5}
    
    def _generate_response(self, message: str, intent: dict, recent_memories: list, preferences: dict, suggestions: list):
        """Generate contextual response"""
        intent_type = intent.get("intent", "general")
        
        # Check for wake-up patterns
        if "wake" in message.lower() or "alarm" in message.lower():
            # Look for existing wake-up patterns
            wake_memories = [m for m in recent_memories if "wake" in m["content"].lower()]
            if wake_memories:
                return "I'll set that alarm for you! I notice you often wake up around the same time - I'll remember this pattern for future mornings."
            else:
                return "I'll set that alarm for you! I'll start learning your wake-up patterns to help you in the future."
        
        # Check for questions about patterns
        if "usually" in message.lower() or "pattern" in message.lower():
            if recent_memories:
                return f"I remember our recent interactions! I'm learning your patterns to provide better assistance. You have {len(recent_memories)} recent activities I'm tracking."
            else:
                return "I'm here to learn your patterns and preferences! The more we interact, the better I'll get at anticipating your needs."
        
        # Default responses based on intent
        if intent_type == "reminder":
            return "I'll set that reminder for you! I'm learning your reminder patterns to be more proactive."
        elif intent_type == "email":
            return "I can help you with email! I'll remember your email checking patterns to suggest when to check next."
        elif intent_type == "calendar":
            return "I can help you with your schedule! I'm learning your calendar patterns to provide better suggestions."
        elif intent_type == "question":
            return "I'm here to help! I'm learning from our conversations to provide more personalized assistance."
        else:
            return "I'm Pluto, your personal AI assistant! I remember everything and learn your patterns to help you better."

async def test_pluto_simple():
    """Test Pluto's simple implementation"""
    print("🤖 PLUTO - AI PHONE ASSISTANT")
    print("Simple Memory and Learning Test")
    print("=" * 50)
    
    orchestrator = SimplePlutoOrchestrator()
    user_id = "test_user_1"
    
    # Test 1: Basic interactions
    print("\n1. Basic Interactions")
    print("-" * 30)
    
    messages = [
        "Wake me up at 7 AM tomorrow",
        "Set an alarm for 7 AM on Monday",
        "Remind me to wake up at 7 AM on Tuesday",
        "What time do I usually wake up?",
        "Check my email",
        "How are you learning my patterns?"
    ]
    
    for message in messages:
        response = await orchestrator.process_message(user_id, message)
        print(f"User: {message}")
        print(f"Pluto: {response['response']}")
        print(f"Intent: {response['intent']['intent']}")
        print(f"Suggestions: {len(response['proactive_suggestions'])}")
        print()
    
    # Test 2: Memory recall
    print("\n2. Memory Recall")
    print("-" * 30)
    
    # Get all memories
    all_memories = await orchestrator.memory.recall_memory(user_id, limit=20)
    print(f"Total memories stored: {len(all_memories)}")
    
    # Get wake-up related memories
    wake_memories = await orchestrator.memory.recall_memory(user_id, query="wake", limit=5)
    print(f"Wake-up related memories: {len(wake_memories)}")
    
    # Test 3: Habit analysis
    print("\n3. Habit Analysis")
    print("-" * 30)
    
    habits = await orchestrator.habit_engine.analyze_habits(user_id)
    print(f"Detected habits: {len(habits)}")
    
    for habit in habits:
        pattern_type = habit["pattern_type"]
        confidence = habit["confidence"]
        observations = habit["observations"]
        pattern_data = habit["pattern_data"]
        
        if pattern_type == "time_based":
            time = pattern_data.get("time", "unknown")
            print(f"⏰ Time-based habit: {time} ({confidence:.2f} confidence, {observations} observations)")
        elif pattern_type == "frequency_based":
            memory_type = pattern_data.get("memory_type", "unknown")
            print(f"🔄 Frequency-based habit: {memory_type} ({confidence:.2f} confidence, {observations} observations)")
    
    # Test 4: Proactive suggestions
    print("\n4. Proactive Suggestions")
    print("-" * 30)
    
    suggestions = await orchestrator.habit_engine.suggest_actions(user_id)
    print(f"Proactive suggestions: {len(suggestions)}")
    
    for suggestion in suggestions:
        print(f"💡 {suggestion['title']}: {suggestion['message']}")
    
    # Test 5: User preferences
    print("\n5. User Preferences")
    print("-" * 30)
    
    preferences = {
        "preferred_wake_time": "7:00 AM",
        "timezone": "PST",
        "notification_frequency": "high"
    }
    
    for key, value in preferences.items():
        await orchestrator.memory.set_preference(user_id, key, value)
    
    stored_preferences = await orchestrator.memory.get_preferences(user_id)
    print(f"Stored preferences: {len(stored_preferences)}")
    for key, value in stored_preferences.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 50)
    print("✅ Pluto Simple Test Completed!")
    print("🚀 Pluto demonstrates:")
    print("   🧠 Memory storage and recall")
    print("   🔄 Pattern detection and habit learning")
    print("   💡 Proactive suggestions")
    print("   ⚙️ User preference management")
    print("   🤖 Contextual responses")

if __name__ == "__main__":
    asyncio.run(test_pluto_simple())

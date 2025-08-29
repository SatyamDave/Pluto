#!/usr/bin/env python3
"""
Interactive Chat with Jarvis Phone
Test all the features in a conversational way
"""

import asyncio
import json
import requests
from datetime import datetime

# Configuration
JARVIS_URL = "http://localhost:8003"

class JarvisMemory:
    """Jarvis's memory system - remembers user preferences and context"""
    
    def __init__(self):
        self.user_preferences = {
            "name": "User",
            "timezone": "local",
            "work_hours": "9 AM - 5 PM",
            "preferred_wake_time": "7 AM",
            "important_contacts": {},
            "frequent_tasks": [],
            "reminder_preferences": "aggressive"
        }
        self.conversation_history = []
        self.active_reminders = []
        self.scheduled_tasks = []
        self.user_context = {}
    
    def remember(self, key, value):
        """Remember something about the user"""
        self.user_context[key] = value
        print(f"🧠 Jarvis remembers: {key} = {value}")
    
    def recall(self, key):
        """Recall something about the user"""
        return self.user_context.get(key, "I don't remember that yet.")
    
    def add_to_history(self, user_message, jarvis_response, intent=None):
        """Add conversation to memory"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "jarvis": jarvis_response,
            "intent": intent
        }
        self.conversation_history.append(entry)
    
    def get_context_summary(self):
        """Get a summary of what Jarvis knows about the user"""
        return {
            "preferences": self.user_preferences,
            "context": self.user_context,
            "conversation_count": len(self.conversation_history),
            "active_reminders": len(self.active_reminders)
        }

def print_banner():
    """Print Jarvis Phone banner"""
    print("=" * 60)
    print("🤖 JARVIS PHONE - YOUR PERSONAL AI ASSISTANT")
    print("=" * 60)
    print("🚀 Powered by OpenRouter with 300+ AI models")
    print("💬 Chat naturally - Jarvis remembers everything")
    print("⏰ Set reminders and manage your schedule")
    print("📧 Handle emails and communications")
    print("📅 Manage calendar and appointments")
    print("📝 Create notes and to-do lists")
    print("📞 Make calls on your behalf")
    print("🧠 Has memory and learns your preferences")
    print("🔒 NEVER goes away - always in your messages")
    print("=" * 60)
    print("Type 'help' for commands, 'quit' to exit")
    print("Type 'memory' to see what Jarvis remembers")
    print("=" * 60)

def check_server():
    """Check if Jarvis server is running"""
    try:
        response = requests.get(f"{JARVIS_URL}/health")
        if response.status_code == 200:
            data = response.json()
            if data.get("openrouter_available"):
                print("✅ Jarvis Phone server is running and ready!")
                return True
            else:
                print("❌ OpenRouter not available")
                return False
        else:
            print("❌ Server not responding")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Jarvis Phone server")
        print(f"   Make sure it's running on {JARVIS_URL}")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False

def chat_with_jarvis(message, model=None):
    """Send a message to Jarvis and get response"""
    try:
        payload = {
            "message": message,
            "max_tokens": 400
        }
        if model:
            payload["model"] = model
        
        response = requests.post(
            f"{JARVIS_URL}/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return {
                    "response": data["response"],
                    "model": data.get("model_used", "unknown"),
                    "provider": data.get("provider", "unknown")
                }
            else:
                return {"error": data.get("error", "Unknown error")}
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"error": f"Request failed: {e}"}

def analyze_intent(message):
    """Analyze user message intent"""
    try:
        response = requests.post(
            f"{JARVIS_URL}/intent",
            json={"message": message},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data["intent"]
            else:
                return {"error": data.get("error", "Unknown error")}
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"error": f"Request failed: {e}"}

def extract_time(message):
    """Extract time information from message"""
    try:
        response = requests.post(
            f"{JARVIS_URL}/extract-time",
            json={"message": message},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data["time_info"]
            else:
                return {"error": data.get("error", "Unknown error")}
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"error": f"Request failed: {e}"}

def generate_response(context, user_message, response_type="general"):
    """Generate contextual response"""
    try:
        response = requests.post(
            f"{JARVIS_URL}/generate-response",
            json={
                "context": context,
                "user_message": user_message,
                "response_type": response_type
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data["response"]
            else:
                return {"error": data.get("error", "Unknown error")}
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"error": f"Request failed: {e}"}

def get_usage():
    """Get current usage statistics"""
    try:
        response = requests.get(f"{JARVIS_URL}/usage")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data["usage"]
            else:
                return {"error": data.get("error", "Unknown error")}
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"error": f"Request failed: {e}"}

def get_models():
    """Get available AI models"""
    try:
        response = requests.get(f"{JARVIS_URL}/models")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data["models"]
            else:
                return {"error": data.get("error", "Unknown error")}
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"error": f"Request failed: {e}"}

def show_help():
    """Show available commands"""
    print("\n📚 JARVIS PHONE COMMANDS:")
    print("=" * 40)
    print("💬 Just type naturally - Jarvis understands!")
    print("🔒 Jarvis NEVER goes away - always in your messages")
    print("")
    print("🔧 Special Commands:")
    print("  help          - Show this help")
    print("  memory        - Show what Jarvis remembers")
    print("  intent        - Analyze your last message")
    print("  time          - Extract time from your last message")
    print("  models        - Show available AI models")
    print("  usage         - Show usage statistics")
    print("  reminder      - Test reminder functionality")
    print("  email         - Test email functionality")
    print("  calendar      - Test calendar functionality")
    print("  call          - Test outbound call functionality")
    print("  quit          - Exit chat")
    print("")
    print("💡 Examples:")
    print("  'Wake me up at 7 AM tomorrow'")
    print("  'Check my email inbox'")
    print("  'What meetings do I have today?'")
    print("  'Call the restaurant to make a reservation'")
    print("  'Add buy groceries to my shopping list'")
    print("  'Remember I prefer coffee over tea'")
    print("  'What do you remember about me?'")
    print("  'Jarvis, are you still there?'")
    print("=" * 40)

def test_reminder():
    """Test reminder functionality"""
    print("\n⏰ TESTING REMINDER FUNCTIONALITY:")
    print("-" * 40)
    
    test_messages = [
        "Wake me up at 7 AM tomorrow",
        "Remind me to call the dentist at 2 PM on Friday",
        "Set an alarm for 6:30 AM on Monday",
        "Remind me in 2 hours to take my medicine"
    ]
    
    for message in test_messages:
        print(f"\n📝 Testing: '{message}'")
        
        # Analyze intent
        intent = analyze_intent(message)
        if "error" not in intent:
            print(f"🎯 Intent: {intent.get('intent', 'unknown')}")
            print(f"📈 Confidence: {intent.get('confidence', 0)}")
            print(f"⚡ Action: {intent.get('action_needed', 'unknown')}")
            print(f"🏷️  Priority: {intent.get('priority', 'unknown')}")
        else:
            print(f"❌ Intent analysis failed: {intent['error']}")
        
        # Extract time
        time_info = extract_time(message)
        if "error" not in time_info and time_info:
            print(f"🕐 Time: {time_info.get('readable_time', 'unknown')}")
            print(f"📅 Type: {time_info.get('type', 'unknown')}")
            print(f"📈 Confidence: {time_info.get('confidence', 0)}")
        else:
            print(f"❌ Time extraction failed: {time_info.get('error', 'No time found')}")
        
        print("-" * 30)

def test_email():
    """Test email functionality"""
    print("\n📧 TESTING EMAIL FUNCTIONALITY:")
    print("-" * 40)
    
    test_messages = [
        "Check my email inbox for important messages",
        "Summarize my unread emails",
        "Draft a reply to John about the meeting",
        "Send an email to the team about the project update"
    ]
    
    for message in test_messages:
        print(f"\n📝 Testing: '{message}'")
        
        # Analyze intent
        intent = analyze_intent(message)
        if "error" not in intent:
            print(f"🎯 Intent: {intent.get('intent', 'unknown')}")
            print(f"📈 Confidence: {intent.get('confidence', 0)}")
            print(f"⚡ Action: {intent.get('action_needed', 'unknown')}")
        else:
            print(f"❌ Intent analysis failed: {intent['error']}")
        
        # Generate response
        response = generate_response("Email management", message, "email")
        if "error" not in response:
            print(f"🤖 Response: {response}")
        else:
            print(f"❌ Response generation failed: {response['error']}")
        
        print("-" * 30)

def test_calendar():
    """Test calendar functionality"""
    print("\n📅 TESTING CALENDAR FUNCTIONALITY:")
    print("-" * 40)
    
    test_messages = [
        "What meetings do I have today?",
        "Schedule a meeting with John tomorrow at 3 PM",
        "Check my calendar for next week",
        "Reschedule my dentist appointment to Friday"
    ]
    
    for message in test_messages:
        print(f"\n📝 Testing: '{message}'")
        
        # Analyze intent
        intent = analyze_intent(message)
        if "error" not in intent:
            print(f"🎯 Intent: {intent.get('intent', 'unknown')}")
            print(f"📈 Confidence: {intent.get('confidence', 0)}")
            print(f"⚡ Action: {intent.get('action_needed', 'unknown')}")
        else:
            print(f"❌ Intent analysis failed: {intent['error']}")
        
        # Generate response
        response = generate_response("Calendar management", message, "calendar")
        if "error" not in response:
            print(f"🤖 Response: {response}")
        else:
            print(f"❌ Response generation failed: {response['error']}")
        
        print("-" * 30)

def test_outbound_calls():
    """Test outbound call functionality"""
    print("\n📞 TESTING OUTBOUND CALL FUNCTIONALITY:")
    print("-" * 40)
    
    test_messages = [
        "Call the restaurant to make a dinner reservation for 7 PM",
        "Phone the dentist to reschedule my appointment to Friday afternoon",
        "Call the delivery service to check on my package",
        "Phone the hotel to confirm my booking for next week"
    ]
    
    for message in test_messages:
        print(f"\n📝 Testing: '{message}'")
        
        # Analyze intent
        intent = analyze_intent(message)
        if "error" not in intent:
            print(f"🎯 Intent: {intent.get('intent', 'unknown')}")
            print(f"📈 Confidence: {intent.get('confidence', 0)}")
            print(f"⚡ Action: {intent.get('action_needed', 'unknown')}")
        else:
            print(f"❌ Intent analysis failed: {intent['error']}")
        
        # Generate response
        response = generate_response("Making outbound calls", message, "outbound_call")
        if "error" not in response:
            print(f"🤖 Response: {response}")
        else:
            print(f"❌ Response generation failed: {response['error']}")
        
        print("-" * 30)

def main():
    """Main chat loop"""
    print_banner()
    
    if not check_server():
        print("\n❌ Please start the Jarvis Phone server first:")
        print("   python3 test_server.py")
        return
    
    # Initialize Jarvis's memory
    jarvis_memory = JarvisMemory()
    
    print("\n�� Jarvis is ready! I'm always here in your messages...")
    print("💡 Try saying: 'Remember I prefer coffee over tea' or 'What do you remember about me?'")
    print("🔒 I never go away - I'm always listening and ready to help!")
    
    last_message = ""
    
    while True:
        try:
            # Get user input
            user_input = input("\n💬 You: ").strip()
            
            if not user_input:
                continue
            
            # Handle special commands
            if user_input.lower() == 'quit':
                print("\n👋 Goodbye! But remember - Jarvis is always here in your messages when you need help.")
                break
            elif user_input.lower() == 'help':
                show_help()
                continue
            elif user_input.lower() == 'memory':
                print("\n🧠 JARVIS'S MEMORY:")
                print("=" * 40)
                context = jarvis_memory.get_context_summary()
                print(f"📊 Conversation history: {context['conversation_count']} messages")
                print(f"⏰ Active reminders: {context['active_reminders']}")
                print(f"🔑 User preferences: {len(context['preferences'])} items")
                print(f"📝 Context items: {len(context['context'])}")
                
                if context['context']:
                    print("\n📋 What I remember about you:")
                    for key, value in context['context'].items():
                        print(f"   • {key}: {value}")
                
                if context['preferences']:
                    print("\n⚙️ Your preferences:")
                    for key, value in context['preferences'].items():
                        print(f"   • {key}: {value}")
                continue
            elif user_input.lower() == 'intent':
                if last_message:
                    print(f"\n🧠 Analyzing intent for: '{last_message}'")
                    intent = analyze_intent(last_message)
                    if "error" not in intent:
                        print(json.dumps(intent, indent=2))
                    else:
                        print(f"❌ {intent['error']}")
                else:
                    print("❌ No previous message to analyze. Say something first!")
                continue
            elif user_input.lower() == 'time':
                if last_message:
                    print(f"\n⏰ Extracting time from: '{last_message}'")
                    time_info = extract_time(last_message)
                    if "error" not in time_info and time_info:
                        print(json.dumps(time_info, indent=2))
                    else:
                        print(f"❌ {time_info.get('error', 'No time found')}")
                else:
                    print("❌ No previous message to analyze. Say something first!")
                continue
            elif user_input.lower() == 'models':
                print("\n🤖 Available AI Models:")
                models = get_models()
                if "error" not in models:
                    for i, model in enumerate(models[:10]):  # Show first 10
                        print(f"  {i+1}. {model['id']} - {model['name']}")
                    print(f"  ... and {len(models)-10} more models")
                else:
                    print(f"❌ {models['error']}")
                continue
            elif user_input.lower() == 'usage':
                print("\n📊 Usage Statistics:")
                usage = get_usage()
                if "error" not in usage:
                    print(json.dumps(usage, indent=2))
                else:
                    print(f"❌ {usage['error']}")
                continue
            elif user_input.lower() == 'reminder':
                test_reminder()
                continue
            elif user_input.lower() == 'email':
                test_email()
                continue
            elif user_input.lower() == 'calendar':
                test_calendar()
                continue
            elif user_input.lower() == 'call':
                test_outbound_calls()
                continue
            
            # Store message for analysis
            last_message = user_input
            
            # Check for presence/availability questions
            if any(phrase in user_input.lower() for phrase in ['are you there', 'still there', 'jarvis are you', 'you there']):
                print("\n🤖 Jarvis: Always here! I never go away - I live in your messages and I'm always listening. What do you need?")
                jarvis_memory.add_to_history(user_input, "Always here! I never go away - I live in your messages and I'm always listening.")
                continue
            
            # Check for memory commands
            if user_input.lower().startswith('remember'):
                # Extract what to remember
                memory_item = user_input[8:].strip()  # Remove "remember"
                if 'that' in memory_item.lower():
                    memory_item = memory_item.split('that', 1)[1].strip()
                
                # Try to parse key-value pairs
                if '=' in memory_item:
                    key, value = memory_item.split('=', 1)
                    jarvis_memory.remember(key.strip(), value.strip())
                elif 'is' in memory_item:
                    parts = memory_item.split('is', 1)
                    if len(parts) == 2:
                        jarvis_memory.remember(parts[0].strip(), parts[1].strip())
                else:
                    # Just remember the whole thing
                    jarvis_memory.remember("fact", memory_item)
                
                print("✅ Got it! I'll remember that.")
                continue
            
            elif user_input.lower().startswith('what do you remember'):
                print("\n🧠 Let me check my memory...")
                context = jarvis_memory.get_context_summary()
                
                if context['context']:
                    print("📋 Here's what I remember about you:")
                    for key, value in context['context'].items():
                        print(f"   • {key}: {value}")
                else:
                    print("🤔 I don't have any specific memories yet. Tell me something about yourself!")
                continue
            
            # Chat with Jarvis
            print("\n🤖 Jarvis is thinking...")
            result = chat_with_jarvis(user_input)
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"\n🤖 Jarvis: {result['response']}")
                print(f"   🧠 Model: {result['model']} | 🏢 Provider: {result['provider']}")
                
                # Store in memory
                jarvis_memory.add_to_history(user_input, result['response'])
                
                # Auto-analyze intent for certain types of messages
                if any(word in user_input.lower() for word in ['remind', 'wake', 'alarm', 'schedule', 'meeting', 'appointment']):
                    print(f"\n🔍 Auto-analysis:")
                    intent = analyze_intent(user_input)
                    if "error" not in intent:
                        print(f"   🎯 Intent: {intent.get('intent', 'unknown')}")
                        print(f"   📈 Confidence: {intent.get('confidence', 0)}")
                        print(f"   ⚡ Action: {intent.get('action_needed', 'unknown')}")
                        
                        # Remember important details
                        if intent.get('entities'):
                            entities = intent['entities']
                            if 'time' in entities:
                                jarvis_memory.remember("last_reminder_time", entities['time'])
                            if 'date' in entities:
                                jarvis_memory.remember("last_reminder_date", entities['date'])
                            if 'task' in entities:
                                jarvis_memory.remember("last_reminder_task", entities['task'])
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! But remember - Jarvis is always here in your messages when you need help.")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()

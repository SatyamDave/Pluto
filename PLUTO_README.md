# 🤖 Pluto - AI Phone Assistant

**Pluto** is your personal AI assistant that lives in your phone and **never forgets**. With long-term memory, habit learning, and proactive behavior, Pluto becomes more helpful and personalized over time.

## 🚀 Key Features

### 🧠 **Long-Term Memory**
- **Never forgets** - Stores every interaction, preference, and pattern
- **Semantic search** - Find memories by meaning, not just keywords
- **Context awareness** - Remembers your habits, preferences, and history
- **Fast recall** - Redis for recent context, Postgres for long-term storage

### 🔄 **Habit Learning**
- **Pattern detection** - Learns your daily routines and preferences
- **Time-based habits** - "You usually wake up at 7 AM on weekdays"
- **Frequency patterns** - "You check email every 2 hours"
- **Context sequences** - "You always check email after meetings"
- **Proactive suggestions** - Suggests actions before you ask

### 🚀 **Proactive Behavior**
- **Morning digests** - Daily summaries of your schedule and priorities
- **Habit reminders** - "It's 7 AM, time for your usual wake-up routine"
- **Smart notifications** - Only interrupts when it matters
- **Predictive assistance** - Anticipates your needs based on patterns

### 📞 **Phone Integration**
- **SMS interface** - Text Pluto naturally
- **Voice calls** - Talk to Pluto like a real assistant
- **Outbound calls** - Pluto can call others on your behalf (with permission)
- **Always available** - No app downloads, just use your phone number

## 🏗️ Architecture

### Core Components

```
Pluto/
├── 🧠 Memory Manager (Postgres + Redis)
├── 🔄 Habit Engine (Pattern Detection)
├── 🚀 Proactive Agent (Scheduled Tasks)
├── 🤖 AI Orchestrator (OpenRouter + Fallbacks)
├── 📞 Telephony (Twilio/Telnyx)
├── 📧 Email Service (Gmail API)
├── 📅 Calendar Service (Google Calendar)
└── 🔐 Security & Permissions
```

### Data Flow

1. **User sends message** → SMS/Voice
2. **Memory lookup** → Recent context + preferences
3. **Intent analysis** → What does the user want?
4. **Habit check** → Any proactive suggestions?
5. **Response generation** → Contextual, personalized response
6. **Memory storage** → Learn from this interaction
7. **Proactive actions** → Schedule future reminders/suggestions

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- OpenRouter API key (or OpenAI/Anthropic)

### Quick Start

1. **Clone and setup**
```bash
git clone <repository>
cd ai-market-terminal
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp env.example .env
# Edit .env with your API keys and settings
```

3. **Database setup**
```bash
# Create PostgreSQL database
createdb pluto_assistant

# Run migrations
alembic upgrade head
```

4. **Start Pluto**
```bash
python main.py
```

## 📋 Configuration

### Environment Variables

```bash
# AI Providers
OPENROUTER_API_KEY=sk-or-...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Database
DATABASE_URL=postgresql://user:pass@localhost/pluto_assistant

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Telephony
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TELNYX_API_KEY=KEY...

# Pluto Settings
PLUTO_MEMORY_ENABLED=true
PLUTO_HABIT_LEARNING_ENABLED=true
PLUTO_PROACTIVE_ENABLED=true
PLUTO_CAN_CALL_EXTERNAL=false
PLUTO_REQUIRES_CONFIRMATION=true
```

## 🧪 Testing

### Run Pluto Tests
```bash
python test_pluto_memory.py
```

### Test Memory System
```bash
# Store memories
curl -X POST http://localhost:8000/api/v1/memory/store \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user1", "type": "reminder", "content": "Wake up at 7 AM"}'

# Recall memories
curl -X GET "http://localhost:8000/api/v1/memory/recall?user_id=user1&query=wake%20up"
```

### Test Habit Learning
```bash
# Analyze habits
curl -X POST http://localhost:8000/api/v1/habits/analyze \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user1"}'

# Get suggestions
curl -X GET "http://localhost:8000/api/v1/habits/suggestions?user_id=user1"
```

## 📱 Usage Examples

### Basic Interactions

**User:** "Wake me up at 7 AM tomorrow"
**Pluto:** "✅ Set alarm for 7 AM tomorrow. I'll remember this for future mornings!"

**User:** "What time do I usually wake up?"
**Pluto:** "Based on your patterns, you usually wake up at 7 AM on weekdays. Want me to set that for tomorrow?"

**User:** "Check my email"
**Pluto:** "📧 You have 3 new emails. One from your boss marked urgent. Want me to summarize them?"

### Proactive Behavior

**Pluto (10 PM):** "It's getting late! You usually set a 7 AM alarm on weekdays. Want me to set that for tomorrow?"

**Pluto (Morning):** "Good morning! Today you have 2 meetings, 3 new emails, and 1 reminder. Your first meeting is at 10 AM."

**Pluto (After meeting):** "Meeting with John completed. You usually check email after meetings. Want me to check for new messages?"

### External Interactions

**User:** "Call the restaurant to make a reservation for 7 PM"
**Pluto:** "I'll call the restaurant for you. Just to confirm: Make a dinner reservation for 7 PM tonight? (Yes/No)"

**User:** "Yes"
**Pluto:** "📞 Calling restaurant... Reservation confirmed for 7 PM. I've added it to your calendar."

## 🔧 API Endpoints

### Memory Management
- `POST /api/v1/memory/store` - Store new memory
- `GET /api/v1/memory/recall` - Recall memories (semantic search)
- `GET /api/v1/memory/summary` - Get memory summary
- `DELETE /api/v1/memory/{id}` - Forget specific memory

### Habit Learning
- `POST /api/v1/habits/analyze` - Analyze user habits
- `GET /api/v1/habits` - Get user habits
- `GET /api/v1/habits/suggestions` - Get proactive suggestions

### Proactive Features
- `GET /api/v1/proactive/digest` - Get morning digest
- `POST /api/v1/proactive/schedule` - Schedule proactive task
- `GET /api/v1/proactive/suggestions` - Get current suggestions

### User Preferences
- `GET /api/v1/preferences` - Get user preferences
- `POST /api/v1/preferences` - Set user preference
- `DELETE /api/v1/preferences/{key}` - Remove preference

## 🔐 Security & Privacy

### Data Protection
- **Encrypted storage** - All sensitive data encrypted at rest
- **Access controls** - User-specific data isolation
- **Audit logging** - Track all data access and modifications
- **Data retention** - Configurable memory retention periods

### User Permissions
- **External actions** - Require explicit confirmation
- **Granular controls** - Choose what Pluto can do
- **Opt-out options** - "Forget this" commands
- **Data export** - Download your data anytime

### Privacy Features
- **Local processing** - Sensitive data processed locally when possible
- **Anonymized analytics** - Usage patterns without personal data
- **Transparent AI** - Explain why Pluto makes suggestions
- **User control** - Full control over what Pluto remembers

## 🚀 Advanced Features

### Voice Integration
- **Natural speech** - Talk to Pluto like a real person
- **Voice synthesis** - Pluto speaks with natural, friendly voice
- **Call handling** - Pluto can answer and make calls
- **Voice commands** - "Pluto, wake me up" works over phone

### Smart Integrations
- **Email management** - Read, summarize, and reply to emails
- **Calendar sync** - Schedule and manage appointments
- **Contact management** - Remember important people and relationships
- **Task automation** - Execute complex workflows

### Learning Capabilities
- **Conversation memory** - Remembers entire conversations
- **Preference learning** - Learns your communication style
- **Context awareness** - Understands conversation context
- **Adaptive responses** - Adjusts tone and style to match you

## 🔄 Development

### Adding New Features

1. **Create service** - Add new functionality as a service
2. **Update memory** - Store relevant data in memory system
3. **Add habits** - Detect patterns in new feature usage
4. **Proactive integration** - Suggest new feature when relevant
5. **Test thoroughly** - Ensure privacy and security

### Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit pull request

## 📊 Performance

### Scalability
- **Horizontal scaling** - Multiple Pluto instances
- **Database optimization** - Efficient queries and indexing
- **Caching strategy** - Redis for fast access
- **Async processing** - Non-blocking operations

### Monitoring
- **Health checks** - System status monitoring
- **Performance metrics** - Response times and throughput
- **Error tracking** - Comprehensive error logging
- **Usage analytics** - Feature usage and patterns

## 🎯 Roadmap

### Phase 1 (Current)
- ✅ Long-term memory system
- ✅ Habit learning engine
- ✅ Proactive suggestions
- ✅ Basic phone integration

### Phase 2 (Next)
- 🔄 Advanced voice capabilities
- 🔄 Email and calendar integration
- 🔄 External contact management
- 🔄 Advanced habit detection

### Phase 3 (Future)
- 📅 Multi-modal interactions
- 📅 Advanced AI reasoning
- 📅 Predictive assistance
- 📅 Ecosystem integrations

## 🤝 Support

### Documentation
- [API Reference](docs/api.md)
- [Deployment Guide](docs/deployment.md)
- [Security Guide](docs/security.md)
- [Contributing Guide](docs/contributing.md)

### Community
- [Discord Server](https://discord.gg/pluto)
- [GitHub Issues](https://github.com/pluto-ai/issues)
- [Feature Requests](https://github.com/pluto-ai/discussions)

### Enterprise
- [Enterprise Support](mailto:enterprise@pluto.ai)
- [Custom Integrations](mailto:integrations@pluto.ai)
- [Security Audits](mailto:security@pluto.ai)

---

**Pluto** - Your AI assistant that never forgets and always learns. 🚀

# Jarvis Phone - AI Personal Assistant

> "Why talk to everyone to get work done? Just talk to one."

Jarvis Phone is a **phone-number-based AI personal assistant** accessible via SMS and voice calls. No app download required - just text or call a number to interact with your AI assistant.

## 🚀 Features

### Core Capabilities
- **SMS & Voice Interface**: Interact via text messages or voice calls
- **AI-Powered**: GPT-4o and Claude integration for intelligent responses
- **Proactive Actions**: AI can act autonomously, not just respond
- **Wake-up Calls**: Persistent reminders with SMS + voice until confirmed
- **AI Calling Humans**: AI makes calls to businesses/people on your behalf
- **Daily Digest**: Automated summaries of emails, calendar, and reminders

### Integrations
- **Gmail**: Summarize inbox, auto-replies, email management
- **Google Calendar**: Meeting alerts, schedule management, proactive notifications
- **Notes & Lists**: To-do management, shopping lists, personal notes
- **Reminders**: Smart scheduling with multiple notification types
- **OpenRouter**: Unified AI access with automatic fallbacks and cost optimization

### Current Features (V1)
- **AI Calling Humans**: Schedule appointments, make bookings on your behalf
- **Proactive Mode**: Auto-replies, conflict resolution, smart suggestions
- **Daily Digest**: Automated daily summaries sent via SMS
- **Persistent Wake-up**: Calls continue until you confirm you're awake

### 🆕 New Features (Beta)
- **Communication Hub**: Text on behalf, forward notes, Slack/Discord integration
- **Audit & Transparency**: Daily summaries of all AI actions taken
- **OAuth Integration**: Secure Gmail and Calendar setup
- **Enhanced Email**: Draft, send, and auto-reply capabilities

## 🛠️ Tech Stack

- **Backend**: Python FastAPI (async, modular)
- **Database**: PostgreSQL (user state) + Redis (job scheduling)
- **Telephony**: Twilio or Telnyx (SMS + voice calls)
- **AI**: OpenRouter (primary with 100+ models), OpenAI GPT-4o (fallback), Anthropic Claude (fallback)
- **Integrations**: Gmail API, Google Calendar API
- **Orchestration**: Custom AI agent planner

## 📁 Project Structure

```
jarvis-phone/
├── main.py                 # FastAPI app entry point
├── config.py              # Configuration and settings
├── ai_orchestrator.py     # Core AI brain and routing
├── api/                   # API routes
│   ├── routes/
│   │   ├── sms.py        # SMS webhook handler
│   │   ├── voice.py      # Voice call handler
│   │   ├── reminders.py  # Reminder management
│   │   ├── email.py      # Email operations
│   │   ├── calendar.py   # Calendar operations
│   │   ├── notes.py      # Notes and todos
│   │   └── health.py     # Health checks
├── db/                    # Database layer
│   ├── database.py       # Connection management
│   └── models.py         # SQLAlchemy models
├── telephony/             # Telephony providers
│   ├── twilio_handler.py # Twilio integration
│   ├── telnyx_handler.py # Telnyx integration
│   └── outbound_call_service.py # AI calling humans
├── reminders/             # Reminder service
│   └── reminder_service.py
├── email_service/         # Email service
│   └── email_service.py
├── calendar_service/      # Calendar service
│   └── calendar_service.py
├── notes/                 # Notes service
│   └── notes_service.py
├── services/              # Additional services
│   ├── digest_service.py # Daily digest generation
│   ├── communication_service.py # Communication hub
│   ├── audit_service.py  # Audit logging & analytics
│   ├── oauth_service.py  # OAuth integration
│   └── openrouter_service.py # OpenRouter AI integration
├── requirements.txt       # Python dependencies
└── env.example           # Environment variables template
```

## 🚀 Quick Start

### Option 1: Docker (Recommended)

#### Prerequisites
- Docker and Docker Compose
- Twilio or Telnyx account
- OpenRouter API key (primary AI provider)
- OpenAI API key (fallback)
- Anthropic API key (fallback)

#### Installation

```bash
# Clone the repository
git clone <repository-url>
cd jarvis-phone

# Copy environment template
cp env.example .env

# Edit .env with your credentials
# DATABASE_URL, REDIS_URL, API keys, etc.

# Start all services
docker-compose up -d

# Access the application
# Pluto AI: http://localhost:8000
# pgAdmin: http://localhost:5050 (admin@pluto.ai / admin123)
# Redis Commander: http://localhost:8081
```

### Option 2: Local Development

#### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Twilio or Telnyx account
- OpenRouter API key (primary AI provider)
- OpenAI API key (fallback)
- Anthropic API key (fallback)

#### Installation

```bash
# Clone the repository
git clone <repository-url>
cd jarvis-phone

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### 3. Configuration

```bash
# Copy environment template
cp env.example .env

# Edit .env with your credentials
DATABASE_URL=postgresql://user:password@localhost:5432/jarvis_phone
REDIS_URL=redis://localhost:6379/0
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
OPENAI_API_KEY=your_openai_api_key
```

### 4. Database Setup

```bash
# Create PostgreSQL database
createdb jarvis_phone

# Run database migrations (when implemented)
# alembic upgrade head
```

### 5. Run the Application

```bash
# Start the server
python main.py

# Or with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## 📱 Usage Examples

### SMS Commands
```
"Wake me at 7 AM tomorrow"
"Check my inbox"
"What's my next meeting?"
"Add buy groceries to my list"
"Remind me to call mom in 2 hours"
"Call the dentist to reschedule my appointment to Friday"
"Send me a digest of my day"
```

### AI Calling Humans
```
"Call the restaurant to make a dinner reservation for 7 PM"
"Phone the dentist to reschedule my appointment to Friday afternoon"
"Call the delivery service to check on my package"
"Phone the hotel to confirm my booking for next week"
```

### Voice Commands
```
"Set a reminder for my dentist appointment"
"Read my unread emails"
"Schedule a meeting with John tomorrow at 3 PM"
"Create a shopping list with milk, bread, and eggs"
```

## 🔧 API Endpoints

### Core Endpoints
- `GET /` - Service status
- `GET /api/v1/health` - Health checks
- `POST /api/v1/sms/webhook` - SMS webhook (Twilio/Telnyx)
- `POST /api/v1/voice/webhook/incoming` - Voice webhook

### Admin Endpoints
- `GET /admin/users/{id}/context` - User context view (HTML)
- `GET /admin/users/{id}/context.json` - User context (JSON)
- `GET /admin/users` - List all users
- `GET /admin/system/status` - System health status

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html --cov-fail-under=85

# Run specific test categories
pytest test_functionality.py::TestSMSFlow
pytest test_functionality.py::TestActionExecutionLayer
```

### Test Coverage
- **Target**: 85%+ coverage
- **Current**: 80%+ coverage
- **Test Categories**: SMS, Voice, Memory, Proactive, Action Layer, Admin

## 🚀 CI/CD Pipeline

### GitHub Actions
- **Automated Testing**: Runs on every push/PR
- **Code Quality**: Black + isort + flake8 linting
- **Coverage Check**: Fails if coverage < 85%
- **Security**: Bandit + Safety security checks
- **Docker**: Automated builds and pushes
- **Deployment**: Staging (develop) and Production (main)

### Docker Support
- **Multi-service**: FastAPI + PostgreSQL + Redis
- **Development**: Hot-reload with volume mounts
- **Management**: pgAdmin + Redis Commander included
- **Production**: Optimized for deployment

### Service Endpoints
- `GET /api/v1/reminders/` - Get user reminders
- `GET /api/v1/email/unread/{user_id}` - Get unread emails
- `GET /api/v1/calendar/next-event/{user_id}` - Get next meeting
- `GET /api/v1/notes/{user_id}` - Get user notes

### New Feature Endpoints
- `POST /api/v1/outbound-calls/initiate` - Initiate AI calling humans
- `GET /api/v1/outbound-calls/{call_id}/status` - Get call status and transcript
- `POST /api/v1/proactive/run` - Run proactive automation tasks
- `POST /api/v1/proactive/digest/send/{user_id}` - Send immediate digest
- `POST /api/v1/voice/webhook/wakeup` - Handle wake-up call confirmations

#### Communication Hub
- `POST /api/v1/communication/text-on-behalf` - Send SMS on behalf
- `POST /api/v1/communication/forward-notes` - Forward notes to contacts
- `POST /api/v1/communication/slack/send` - Send to Slack channels
- `POST /api/v1/communication/discord/send` - Send to Discord channels
- `POST /api/v1/communication/contacts/add` - Add new contacts
- `GET /api/v1/communication/contacts/{user_id}` - Get user contacts

#### OAuth Integration
- `POST /api/v1/oauth/initiate` - Start OAuth flow
- `POST /api/v1/oauth/callback` - Handle OAuth callback
- `GET /api/v1/oauth/status/{user_id}` - Get integration status
- `POST /api/v1/oauth/refresh/{user_id}` - Refresh tokens
- `DELETE /api/v1/oauth/revoke/{user_id}` - Revoke integration

#### Audit & Analytics
- `GET /api/v1/audit/summary/{user_id}` - Get daily summary
- `POST /api/v1/audit/summary/{user_id}/send-sms` - Send summary SMS
- `GET /api/v1/audit/analytics/{user_id}` - Get user analytics
- `GET /api/v1/audit/actions/{user_id}` - Get action history
- `POST /api/v1/audit/log` - Log custom actions

#### AI Management
- `GET /api/v1/ai/health` - AI services health check
- `GET /api/v1/ai/models` - List available AI models
- `GET /api/v1/ai/models/{model_id}` - Get model information
- `GET /api/v1/ai/usage` - Get AI usage statistics
- `POST /api/v1/ai/test` - Test AI completion
- `GET /api/v1/ai/credits` - Get OpenRouter credits
- `GET /api/v1/ai/status` - Comprehensive AI status

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_reminders.py

# Test OpenRouter integration
python test_openrouter.py
```

## 🤖 OpenRouter AI Integration

Jarvis Phone uses **OpenRouter** as the primary AI provider, giving you access to 100+ AI models through a single API key with automatic fallbacks and cost optimization.

### Key Benefits
- **Unified Access**: Single API key for OpenAI, Anthropic, Google, Meta, and more
- **Automatic Fallbacks**: Seamlessly switches between models if one fails
- **Cost Optimization**: Automatically selects cost-effective models
- **Provider Diversity**: Access to the best models from multiple providers

### Quick Setup
1. Get your API key from [OpenRouter.ai](https://openrouter.ai)
2. Add to `.env`: `OPENROUTER_API_KEY=sk-or-your-key-here`
3. Run `python test_openrouter.py` to verify setup

### Available Models
- **GPT-4o** - Best performance, higher cost
- **GPT-4o-mini** - Good performance, moderate cost
- **Claude 3.5 Sonnet** - Alternative provider
- **Claude 3 Haiku** - Fast, cost-effective
- **Llama 3.1** - Local fallback option
- **Gemini Pro 1.5** - Google's offering

📖 **Full Setup Guide**: [OPENROUTER_SETUP.md](OPENROUTER_SETUP.md)

## 📊 Monitoring

- **Health Checks**: `/api/v1/health/detailed`
- **Logging**: Comprehensive logging for all external API calls
- **Metrics**: Database performance, API response times
- **Alerts**: Failed reminders, API errors, service degradation

## 🔒 Security

- **OAuth 2.0**: Gmail and Calendar integration
- **Secure Storage**: Encrypted credential storage
- **Rate Limiting**: API request throttling
- **Input Validation**: All user inputs sanitized
- **No Token Logging**: Sensitive data never logged

## 🚀 Deployment

### Docker (Recommended)
```bash
# Build image
docker build -t jarvis-phone .

# Run container
docker run -p 8000:8000 --env-file .env jarvis-phone
```

### Production Considerations
- Use production-grade PostgreSQL and Redis
- Implement proper SSL/TLS
- Set up monitoring and alerting
- Configure backup strategies
- Use environment-specific configurations

## 💰 Monetization Strategy

### Subscription Tiers
- **Free**: Basic reminders, limited features
- **Pro ($20-30/month)**: Full feature access, priority support
- **Executive ($50-100/month)**: AI calling humans, premium integrations

### Additional Revenue Streams
- **Affiliate Commissions**: Travel, restaurant bookings
- **Enterprise Licensing**: White-label solutions
- **API Access**: Third-party integrations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is proprietary software. All rights reserved.

## 🆘 Support

- **Documentation**: [API Docs](http://localhost:8000/docs)
- **Issues**: GitHub Issues
- **Email**: support@jarvisphone.com

## 🆕 New Features

### AI Calling Humans
- **What it does**: AI makes phone calls to businesses and people on your behalf
- **Use cases**: Reschedule appointments, make reservations, check delivery status
- **How it works**: Text "Call the dentist to reschedule my appointment" and AI handles the entire call
- **Compliance**: Always starts with "Hi, this is an AI assistant calling for a client"
- **Transcripts**: Full conversation logs available for review

### Proactive Automation Mode
- **Email Management**: Automatically replies to low-priority emails
- **Calendar Monitoring**: Detects conflicts and suggests reschedules
- **Daily Digest**: Automated SMS summaries of your day
- **Smart Notifications**: Proactive alerts for important events

### Persistent Wake-up Calls
- **How it works**: When you say "Wake me at 2 AM", AI calls repeatedly until you confirm
- **Confirmation**: Press "1" on your phone to confirm you're awake
- **Fallback**: SMS notifications if calls fail
- **Reliability**: Won't stop until you're confirmed awake

## 🔮 Roadmap

### MVP (Current)
- ✅ SMS/voice interface
- ✅ Basic reminders
- ✅ Gmail integration
- ✅ Calendar integration
- ✅ Notes management

### V1 (Current)
- ✅ AI calling humans
- ✅ Proactive automation
- ✅ Daily digest summaries
- ✅ Persistent wake-up calls

### V2 (12+ months)
- 🔮 Multi-language support
- 🔮 Enterprise features
- 🔮 Advanced AI capabilities
- 🔮 Mobile app companion

---

**Jarvis Phone** - Your AI personal assistant, accessible anywhere via phone.

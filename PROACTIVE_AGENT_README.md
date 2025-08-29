# Pluto Proactive Agent - Complete Guide

This document describes Pluto's Proactive Agent system that makes Pluto truly proactive and helpful without being prompted.

## 🎯 Overview

The Proactive Agent transforms Pluto from a reactive assistant to a proactive one that:
- **Schedules recurring tasks** (morning digests, habit checks, email monitoring)
- **Sends urgent alerts** (important emails, calendar conflicts)
- **Makes outbound calls** (wake-up calls, reminders)
- **Suggests proactive actions** based on user habits and context
- **Respects user preferences** for all proactive features

## 🏗️ Architecture

### Core Components

1. **`ProactiveAgent`** (`services/proactive_agent.py`)
   - Main proactive service with APScheduler integration
   - Manages all scheduled tasks and proactive actions
   - Coordinates with other services for context and actions

2. **APScheduler Integration**
   - **CronTrigger**: For time-based tasks (morning digest at 8AM)
   - **IntervalTrigger**: For recurring checks (email monitoring every 15 minutes)
   - **Job Management**: Automatic job scheduling, replacement, and cleanup

3. **Service Integration**
   - **UserManager**: Gets user preferences and phone numbers
   - **DigestService**: Generates morning summaries
   - **CommunicationService**: Sends SMS messages
   - **OutboundCallService**: Makes wake-up calls
   - **HabitEngine**: Analyzes user behavior patterns
   - **ContextAggregator**: Provides user context for decisions

## 🚀 Proactive Features

### 1. Morning Digest System

**What it does**: Sends personalized daily summaries at user's preferred time
**Default time**: 8:00 AM
**Content includes**:
- 📧 Unread email count and urgent emails
- 📅 Today's calendar events and next meeting
- ⏰ Active reminders and overdue items
- 🔄 Habit suggestions and proactive tips

**Example message**:
```
Good morning! 📧 5 unread emails (2 urgent) | 📅 3 events today | ⏰ Next: Team meeting at 10:00 AM | 🔄 Time for your morning routine
```

**User preferences**:
- `morning_digest_enabled`: Enable/disable feature
- `morning_digest_time`: Customize delivery time (e.g., "07:30")

### 2. Urgent Email Alerts

**What it does**: Monitors inbox every 15 minutes for urgent emails
**Alert threshold**: Emails marked as urgent or high priority
**Response time**: Within 15 minutes of arrival
**User control**: `urgent_email_alerts` preference

**Example alert**:
```
🚨 You have 2 urgent emails! Want me to summarize them?
```

### 3. Calendar Conflict Detection

**What it does**: Checks calendar every hour for scheduling conflicts
**Detection**: Overlapping events, double-bookings, impossible schedules
**User control**: `calendar_alerts` preference

**Example alert**:
```
📅 Calendar conflict detected! You have 1 overlapping events. Need help resolving?
```

### 4. Habit-Based Suggestions

**What it does**: Analyzes user behavior patterns and suggests proactive actions
**Frequency**: Every 2 hours during active periods
**Pattern types**:
- **Time-based**: "You usually set a 7AM wake-up. Want me to call you tomorrow?"
- **Frequency-based**: "Time for your daily check-in?"

**Example suggestions**:
```
🔄 Habit suggestions:
You usually set a 7AM wake-up. Want me to call you tomorrow?
Time for your daily check-in?
```

### 5. Wake-up Call System

**What it does**: Makes outbound calls to wake users at scheduled times
**Scheduling**: Can be scheduled manually or suggested by habit analysis
**Persistence**: Calls until user confirms they're awake
**User control**: `wake_up_calls` preference

**Example flow**:
1. User: "Wake me up at 7AM tomorrow"
2. Pluto: "I'll call you at 7:00 AM tomorrow to wake you up!"
3. Next day at 7AM: Pluto calls with "Good morning! Time to wake up!"
4. User confirms: "I'm awake" → Call ends

## ⚙️ User Preferences

### Core Proactive Settings

```python
{
    "proactive_mode": True,              # Master switch for all proactive features
    "morning_digest_enabled": True,      # Daily morning summaries
    "morning_digest_time": "08:00",      # Custom digest time
    "wake_up_calls": True,               # Allow wake-up calls
    "urgent_email_alerts": True,         # Urgent email notifications
    "calendar_alerts": True,             # Calendar conflict alerts
    "habit_reminders": True,             # Habit-based suggestions
    "proactive_suggestions": True        # General proactive tips
}
```

### Preference Management

```python
from services.user_manager import user_manager

# Update user preference
await user_manager.update_user_preference(
    user_id=1, 
    key="morning_digest_time", 
    value="07:30"
)

# Disable proactive mode
await user_manager.update_user_preference(
    user_id=1, 
    key="proactive_mode", 
    value=False
)
```

## 📅 Task Scheduling

### Automatic Scheduling

When a user activates proactive mode, the system automatically schedules:

1. **Morning Digest**: Daily at user's preferred time
2. **Email Monitoring**: Every 15 minutes during business hours
3. **Calendar Checks**: Every hour for conflicts
4. **Habit Analysis**: Every 2 hours for suggestions

### Manual Scheduling

```python
from services.proactive_agent import proactive_agent

# Schedule wake-up call
await proactive_agent.schedule_wakeup_call(
    user_id=1,
    phone_number="+15551234567",
    wakeup_time=datetime(2024, 1, 15, 7, 0),  # 7 AM tomorrow
    message="Good morning! Time to wake up!"
)

# Schedule custom proactive task
await proactive_agent.scheduler.add_job(
    func=proactive_agent.send_proactive_message,
    trigger=CronTrigger(hour=18, minute=0),  # 6 PM daily
    args=["1", "Time to review your day!"],
    id="daily_review_1"
)
```

## 🔄 Proactive Actions

### Available Actions

1. **`morning_digest`**: Generate and send daily summary
2. **`schedule_wakeup`**: Schedule wake-up call
3. **`summarize_emails`**: Summarize urgent emails
4. **`resolve_conflicts`**: Help with calendar conflicts
5. **`execute_habit`**: Execute user habit
6. **`check_reminders`**: Check overdue reminders

### Action Execution

```python
# Execute proactive action
result = await proactive_agent.execute_proactive_action(
    user_id="1",
    action_type="schedule_wakeup",
    action_data={"wakeup_time": "07:00"}
)

if result["success"]:
    print(f"Action completed: {result['message']}")
else:
    print(f"Action failed: {result['message']}")
```

## 📱 Communication Channels

### SMS Messages

- **Morning digests** sent via SMS
- **Urgent alerts** delivered immediately
- **Habit suggestions** sent proactively
- **Calendar conflict notifications**

### Voice Calls

- **Wake-up calls** with TTS messages
- **Reminder calls** for important items
- **Confirmation calls** for critical actions

### Message Styling

All proactive messages are styled using the user's style profile:
- **Emoji usage** based on user preference
- **Formality level** matching user's style
- **Message length** adapted to user preference
- **Tone consistency** across all communications

## 🧪 Testing

### Basic Tests

```bash
# Run simple functionality test
python3 test_proactive_agent_simple.py

# Run full test suite (requires pytest)
pytest test_proactive_agent.py -v
```

### Test Coverage

- ✅ **Initialization**: Agent creation and service loading
- ✅ **Scheduling**: Task scheduling and management
- ✅ **Morning Digest**: Digest generation and sending
- ✅ **Habit Suggestions**: Pattern recognition and suggestions
- ✅ **Wake-up Calls**: Call scheduling and execution
- ✅ **User Preferences**: Preference respect and control
- ✅ **Error Handling**: Graceful failure handling

### Manual Testing

1. **Enable proactive mode** for a test user
2. **Set morning digest time** to 1-2 minutes from now
3. **Create test habits** with the habit engine
4. **Schedule test wake-up call** for 1-2 minutes from now
5. **Monitor logs** for proactive actions

## 🔧 Configuration

### Environment Variables

```bash
# Proactive agent settings
PROACTIVE_MODE_ENABLED=true
DEFAULT_DIGEST_TIME=08:00
EMAIL_MONITORING_INTERVAL=15  # minutes
CALENDAR_CHECK_INTERVAL=60    # minutes
HABIT_CHECK_INTERVAL=120      # minutes
```

### Service Dependencies

```python
# Required services for full functionality
services = {
    "user_manager": "User profiles and preferences",
    "digest_service": "Morning digest generation",
    "communication_service": "SMS sending",
    "outbound_call_service": "Voice calls",
    "habit_engine": "Behavior pattern analysis",
    "context_aggregator": "User context data",
    "style_engine": "Message styling"
}
```

## 🚨 Troubleshooting

### Common Issues

1. **Scheduler not starting**
   - Check APScheduler installation: `pip install apscheduler`
   - Verify scheduler permissions and timezone settings

2. **Tasks not executing**
   - Check user preferences (`proactive_mode` enabled)
   - Verify service dependencies are running
   - Check scheduler logs for job errors

3. **Messages not sending**
   - Verify telephony service configuration
   - Check user phone number format
   - Ensure SMS handler is properly initialized

4. **Wake-up calls failing**
   - Check outbound call service configuration
   - Verify user has `wake_up_calls` enabled
   - Check telephony provider settings

### Debug Mode

Enable detailed logging:

```python
import logging
logging.getLogger("services.proactive_agent").setLevel(logging.DEBUG)
logging.getLogger("apscheduler").setLevel(logging.DEBUG)
```

### Health Checks

```python
# Check proactive agent status
agent = proactive_agent
print(f"Running: {agent.is_running}")
print(f"Scheduler running: {agent.scheduler.running}")
print(f"Active jobs: {len(agent.scheduler.get_jobs())}")
print(f"Active wake-up calls: {len(agent.active_wakeup_calls)}")
```

## 🚀 Future Enhancements

### Planned Features

1. **Smart Timing**: AI-powered optimal timing for proactive messages
2. **Multi-channel**: Slack, Discord, email integration
3. **Advanced Habits**: Complex pattern recognition and prediction
4. **Contextual Suggestions**: Proactive actions based on external events
5. **Learning System**: Improve suggestions based on user responses

### Scalability Improvements

1. **Redis Job Store**: Persistent job storage across restarts
2. **Distributed Scheduling**: Multi-instance job coordination
3. **Rate Limiting**: Intelligent throttling based on user preferences
4. **Batch Processing**: Efficient bulk proactive actions

## 📊 Performance Metrics

### Key Indicators

- **Task Execution Rate**: >95% successful execution
- **Response Time**: Proactive messages within 15 minutes
- **User Engagement**: 70%+ users respond to proactive messages
- **System Reliability**: 99.9% uptime for proactive features

### Monitoring

```python
# Monitor proactive agent performance
metrics = {
    "scheduled_jobs": len(proactive_agent.scheduler.get_jobs()),
    "active_wakeup_calls": len(proactive_agent.active_wakeup_calls),
    "last_digest_sent": last_digest_timestamp,
    "user_engagement_rate": engagement_percentage
}
```

## 📞 Support

For issues with the proactive agent:

1. **Check logs** for detailed error information
2. **Verify configuration** and service dependencies
3. **Test basic functionality** with simple test script
4. **Review user preferences** and proactive mode settings
5. **Check scheduler status** and job execution

---

**Note**: The Proactive Agent makes Pluto feel alive and helpful by anticipating user needs and taking action without being prompted. It's the key to transforming Pluto from a reactive tool into a proactive personal assistant! 🎉

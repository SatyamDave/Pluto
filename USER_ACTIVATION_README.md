# User Activation & Identity Management System

This document describes the user activation and identity management system implemented for Pluto AI Phone Assistant.

## 🎯 Overview

The system automatically creates and manages user profiles when someone texts or calls Pluto for the first time. Each user is identified by their phone number and gets a complete profile with preferences, style settings, and memory tracking.

## 🏗️ Architecture

### Core Components

1. **`UserManager`** (`services/user_manager.py`)
   - Main service for user operations
   - Handles user creation, retrieval, and profile management
   - Provides phone number cleaning and validation

2. **Updated SMS Handler** (`api/routes/sms.py`)
   - Integrates with UserManager for user activation
   - Links all messages to user profiles
   - Maintains conversation history

3. **Updated Voice Handler** (`api/routes/voice.py`)
   - Similar integration for voice calls
   - Tracks call sessions and user context

4. **Enhanced AI Orchestrator** (`ai_orchestrator.py`)
   - Uses UserManager for proactive tasks
   - Accesses user preferences and style profiles

## 🚀 User Activation Flow

### First Contact
1. User texts/calls Pluto from a new phone number
2. `UserManager.get_or_create_user()` is called
3. New user profile is created with:
   - Unique phone number as identifier
   - Default style profile (casual, friendly, emoji-enabled)
   - Default preferences (proactive mode, morning digests, etc.)
   - Empty memory and habit tracking

### Subsequent Contacts
1. Existing user is retrieved by phone number
2. `last_seen` timestamp is updated
3. Full user profile is loaded (preferences, style, memory, habits)
4. AI orchestrator uses this context for personalized responses

## 📊 User Profile Structure

```python
{
    "id": 1,
    "phone_number": "15551234567",
    "name": "John Doe",  # Optional
    "email": "john@example.com",  # Optional
    "is_active": True,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "last_seen": "2024-01-01T12:00:00Z",
    "style_profile": {
        "emoji_usage": True,
        "formality_level": "casual",
        "avg_message_length": "medium",
        "signature_phrases": ["on it", "got it"],
        "tone_preferences": {"humor": 0.5, "formality": 0.3},
        "communication_style": "friendly"
    },
    "preferences": {
        "auto_confirm_family": True,
        "auto_confirm_work": False,
        "morning_digest_enabled": True,
        "proactive_mode": True,
        "wake_up_calls": True,
        "email_summaries": True,
        "calendar_alerts": True
    },
    "stats": {
        "memory_count": 25,
        "habit_count": 3
    }
}
```

## ⚙️ User Preferences

### Core Preferences
- **`auto_confirm_family`**: Automatically confirm appointments with family contacts
- **`auto_confirm_work`**: Always confirm with work contacts
- **`morning_digest_enabled`**: Send daily morning summaries
- **`proactive_mode`**: Enable proactive suggestions and actions
- **`wake_up_calls`**: Allow wake-up call scheduling
- **`email_summaries`**: Provide email inbox summaries
- **`calendar_alerts`**: Send calendar event reminders

### Style Preferences
- **`emoji_usage`**: Whether to use emojis in responses
- **`formality_level`**: casual, formal, or mixed
- **`avg_message_length`**: short, medium, or long
- **`communication_style`**: friendly, direct, or professional

## 🔄 Memory & Context Management

### User Memory
- All interactions stored with `user_id` linkage
- Memory includes type, content, context data, and importance scores
- Supports embedding vectors for semantic search

### Habit Tracking
- Automatic pattern recognition from user behavior
- Confidence scoring for habit predictions
- Proactive suggestion generation based on habits

### Context Snapshots
- Periodic context captures for long-term memory
- Daily, weekly, and event-based summaries
- Relationship graph tracking between entities

## 🗄️ Database Schema

### Core Tables
- **`users`**: Basic user information and timestamps
- **`user_style_profiles`**: Communication style preferences
- **`user_preferences`**: Key-value preference storage
- **`user_memory`**: Long-term memory with embeddings
- **`user_habits`**: Behavioral pattern tracking
- **`proactive_tasks`**: Scheduled proactive actions
- **`external_contacts`**: People Pluto can interact with
- **`relationship_graph`**: Entity relationship mapping
- **`context_snapshots`**: Context state captures

### Key Relationships
- All user-related tables reference `users.id`
- Foreign key constraints ensure data integrity
- Indexes optimize query performance

## 🧪 Testing

### Basic Tests
```bash
# Run simple functionality test
python test_user_activation_simple.py

# Run full test suite (requires pytest)
pytest test_user_activation.py
```

### Test Coverage
- Phone number cleaning and validation
- User creation and retrieval
- Profile management operations
- Preference and style updates
- Error handling and edge cases

## 🚀 Usage Examples

### Creating/Retrieving Users
```python
from services.user_manager import user_manager

# Get or create user by phone number
user_profile = await user_manager.get_or_create_user("+1-555-123-4567")

# Get existing user
existing_user = await user_manager.get_user_by_phone("+1-555-123-4567")

# Update user preference
await user_manager.update_user_preference(user_id=1, key="morning_digest_enabled", value=False)
```

### Style Profile Updates
```python
# Update communication style
await user_manager.update_style_profile(
    user_id=1, 
    style_updates={"formality_level": "formal", "emoji_usage": False}
)
```

### Proactive Operations
```python
# Get all active users for proactive tasks
active_users = await user_manager.get_active_users()

# Each user has phone_number for outbound communication
for user in active_users:
    await send_morning_digest(user["phone_number"])
```

## 🔒 Security & Privacy

### Data Protection
- Phone numbers are cleaned and standardized
- No sensitive data logged in plain text
- User preferences stored as JSONB for flexibility
- Soft deletion support for data retention

### Access Control
- User isolation by phone number
- No cross-user data access
- Database-level foreign key constraints
- Session-based database access

## 🚧 Future Enhancements

### Planned Features
- **Multi-channel Support**: Email, Slack, Discord integration
- **Contact Management**: Family/work contact categorization
- **Advanced Preferences**: Timezone, language, accessibility settings
- **Privacy Controls**: Granular permission management
- **Data Export**: User data portability

### Scalability Considerations
- Redis caching for frequently accessed profiles
- Database connection pooling
- Async operations for concurrent user management
- Horizontal scaling support

## 📝 Migration Guide

### Database Setup
1. Run the migration script:
   ```bash
   psql -d your_database -f db/migrations/001_create_users_table.sql
   ```

2. Verify table creation:
   ```sql
   \dt user_*
   ```

3. Check foreign key constraints:
   ```sql
   SELECT * FROM information_schema.table_constraints 
   WHERE constraint_type = 'FOREIGN KEY';
   ```

### Code Integration
1. Import UserManager in your handlers
2. Replace manual user creation with `user_manager.get_or_create_user()`
3. Update AI orchestrator to use user context
4. Test with new phone numbers to verify activation

## 🆘 Troubleshooting

### Common Issues
- **Phone Number Format**: Ensure proper country code handling
- **Database Connections**: Check async session management
- **Foreign Key Errors**: Verify table creation order
- **Memory Issues**: Monitor user profile size and cleanup

### Debug Mode
Enable detailed logging in `utils/logging_config.py`:
```python
logging.getLogger("services.user_manager").setLevel(logging.DEBUG)
```

## 📞 Support

For issues or questions about the user activation system:
1. Check the test files for usage examples
2. Review database migration logs
3. Enable debug logging for detailed error information
4. Verify database schema matches models.py

---

**Note**: This system ensures Pluto recognizes users from their first interaction and maintains personalized context across all communications.

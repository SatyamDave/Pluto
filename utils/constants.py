"""
Constants for Jarvis Phone AI Assistant
"""

import os
from typing import Dict, Any

# Execution modes for AI orchestrator
EXECUTION_MODES = {
    "cloud": "Server-side execution via APIs",
    "deeplink": "Generate deep link for user to tap",
    "device_bridge": "Send signed command to device automation",
    "hybrid": "Combination of cloud + deeplink",
    "fallback": "Fallback when intent is unclear"
}

# Device capabilities by platform
DEVICE_CAPABILITIES = {
    "ios": {
        "deeplinks": True,
        "shortcuts": True,
        "device_bridge": False,  # iOS limitations
        "supported_actions": [
            "call", "sms", "maps", "alarm", "calendar", "messages",
            "slack", "notion", "twitter", "uber", "lyft", "doordash",
            "camera", "photos", "settings", "wifi", "dnd"
        ],
        "automation": "Shortcuts",
        "limitations": [
            "No background automation",
            "Limited system settings access",
            "Requires user interaction for most actions"
        ]
    },
    "android": {
        "deeplinks": True,
        "shortcuts": False,
        "device_bridge": True,  # Tasker support
        "supported_actions": [
            "call", "sms", "maps", "alarm", "calendar", "messages",
            "slack", "notion", "twitter", "uber", "lyft", "doordash",
            "camera", "photos", "settings", "wifi", "dnd"
        ],
        "automation": "Tasker",
        "limitations": [
            "Requires Tasker setup",
            "Some actions need root access",
            "Varies by manufacturer"
        ]
    },
    "unknown": {
        "deeplinks": True,
        "shortcuts": False,
        "device_bridge": False,
        "supported_actions": [
            "call", "sms", "maps", "alarm", "calendar", "messages"
        ],
        "automation": "None",
        "limitations": [
            "Generic deep links only",
            "No device automation",
            "Fallback to web alternatives"
        ]
    }
}

# Memory management constants
MAX_MEMORY_RECALL = 100
MAX_CONTEXT_ITEMS = 50
CACHE_TTL = 86400  # 24 hours in seconds

# Proactive automation constants
PROACTIVE_THRESHOLD = 0.6
DEFAULT_DIGEST_TIME = "08:00"
DEFAULT_PROACTIVE_INTERVAL = 300  # 5 minutes
HABIT_CONFIDENCE_THRESHOLD = 0.6

# Contact resolution constants
MAX_CONTACT_AMBIGUITY = 3
CONTACT_SEARCH_LIMIT = 10

# Security constants
HMAC_ALGORITHM = "sha256"
COMMAND_SIGNATURE_LENGTH = 64

# Deep link constants
MAX_DEEPLINK_LENGTH = 2048
SUPPORTED_URL_SCHEMES = [
    "tel:", "sms:", "smsto:", "geo:", "camera://", "photos://",
    "shortcuts://", "tasker://", "slack://", "notion://", "twitter://",
    "uber://", "lyft://", "doordash://", "maps://", "calendar://"
]

# Intent confidence thresholds
HIGH_CONFIDENCE = 0.8
MEDIUM_CONFIDENCE = 0.6
LOW_CONFIDENCE = 0.4

# Response formatting constants
MAX_RESPONSE_LENGTH = 160  # SMS character limit
MAX_DEEPLINKS_PER_RESPONSE = 3

# Device bridge constants
PLUTO_COMMAND_PREFIX = "PLUTO://cmd/"
COMMAND_EXPIRY_SECONDS = 300  # 5 minutes
MAX_RETRY_ATTEMPTS = 3

# Calendar integration constants
DEFAULT_CALENDAR_REMINDER_MINUTES = 15
MAX_CALENDAR_EVENTS_PER_DAY = 50
CALENDAR_SYNC_INTERVAL = 300  # 5 minutes

# Email integration constants
MAX_EMAIL_SUMMARY_LENGTH = 500
EMAIL_AUTO_REPLY_THRESHOLD = 0.7
EMAIL_SYNC_INTERVAL = 600  # 10 minutes

# Slack integration constants
MAX_SLACK_MESSAGE_LENGTH = 3000
SLACK_CHANNEL_CACHE_TTL = 3600  # 1 hour
SLACK_RATE_LIMIT_DELAY = 1  # 1 second between messages

# Maps integration constants
MAX_DESTINATION_LENGTH = 200
DEFAULT_MAPS_PROVIDER = "google"
SUPPORTED_MAPS_PROVIDERS = ["google", "apple", "bing"]

# Ride-sharing constants
MAX_PICKUP_DESTINATION_LENGTH = 100
SUPPORTED_RIDE_SERVICES = ["uber", "lyft"]
DEFAULT_RIDE_TYPE = "uberx"

# Food delivery constants
MAX_RESTAURANT_NAME_LENGTH = 100
SUPPORTED_FOOD_SERVICES = ["doordash", "ubereats", "grubhub"]

# System settings constants
SUPPORTED_SYSTEM_ACTIONS = [
    "wifi", "bluetooth", "dnd", "airplane_mode", "brightness",
    "volume", "ringer", "vibration", "location", "camera"
]

# User preference defaults
DEFAULT_USER_PREFERENCES = {
    "device_type": "unknown",
    "device_bridge_enabled": False,
    "timezone": "UTC",
    "language": "en",
    "morning_digest_time": "08:00",
    "evening_digest_time": "18:00",
    "proactive_mode": True,
    "urgent_email_alerts": True,
    "calendar_alerts": True,
    "wake_up_calls": True,
    "emoji_usage": True,
    "formality_level": "casual",
    "communication_style": "friendly"
}

# Audit log constants
AUDIT_LOG_RETENTION_DAYS = 90
AUDIT_LOG_MAX_ENTRIES = 10000
AUDIT_LOG_BATCH_SIZE = 100

# Error handling constants
MAX_ERROR_RETRIES = 3
ERROR_BACKOFF_SECONDS = 60
FATAL_ERROR_THRESHOLD = 10

# Performance constants
MAX_CONCURRENT_REQUESTS = 10
REQUEST_TIMEOUT_SECONDS = 30
MEMORY_CLEANUP_INTERVAL = 3600  # 1 hour

# Integration limits
MAX_OAUTH_INTEGRATIONS = 5
MAX_EXTERNAL_CONTACTS = 100
MAX_USER_MEMORIES = 10000
MAX_HABIT_PATTERNS = 50

# Security and privacy constants
PII_MASKING_ENABLED = True
ENCRYPTION_AT_REST = True
AUDIT_TRAIL_ENABLED = True
USER_CONSENT_REQUIRED = True

# Feature flags
FEATURES = {
    "proactive_mode": True,
    "device_bridge": True,
    "deep_links": True,
    "calendar_integration": True,
    "email_integration": True,
    "slack_integration": True,
    "maps_integration": True,
    "ride_sharing": True,
    "food_delivery": True,
    "system_settings": True,
    "ai_memory": True,
    "habit_learning": True,
    "audit_logging": True
}

# Environment-specific overrides
if os.getenv("ENVIRONMENT") == "production":
    # Production settings
    AUDIT_LOG_RETENTION_DAYS = 365
    MAX_CONCURRENT_REQUESTS = 50
    REQUEST_TIMEOUT_SECONDS = 60
    PII_MASKING_ENABLED = True
    ENCRYPTION_AT_REST = True
elif os.getenv("ENVIRONMENT") == "staging":
    # Staging settings
    AUDIT_LOG_RETENTION_DAYS = 30
    MAX_CONCURRENT_REQUESTS = 20
    REQUEST_TIMEOUT_SECONDS = 45
    PII_MASKING_ENABLED = True
    ENCRYPTION_AT_REST = False
else:
    # Development settings
    AUDIT_LOG_RETENTION_DAYS = 7
    MAX_CONCURRENT_REQUESTS = 5
    REQUEST_TIMEOUT_SECONDS = 30
    PII_MASKING_ENABLED = False
    ENCRYPTION_AT_REST = False

# Additional constants for backward compatibility
STYLE_LEVELS = {
    "formality": ["casual", "mixed", "formal"],
    "message_length": ["short", "medium", "long"],
    "communication_style": ["friendly", "direct", "professional"]
}

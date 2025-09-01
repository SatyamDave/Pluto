"""
Configuration settings for Jarvis Phone AI Assistant
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str = Field(default="postgresql://user:password@localhost:5432/jarvis_phone")
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    
    # Twilio (Primary telephony provider)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    TWILIO_WEBHOOK_SECRET: Optional[str] = None
    
    # AI Providers
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = Field(default="gpt-4o")
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = Field(default="claude-3-sonnet-20240229")
    
    # OpenRouter (Primary AI provider with fallbacks)
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_PREFERRED_MODEL: str = Field(default="openai/gpt-4o", description="Preferred OpenRouter model")
    OPENROUTER_FALLBACK_ENABLED: bool = Field(default=True, description="Enable automatic model fallbacks")
    OPENROUTER_COST_OPTIMIZATION: bool = Field(default=True, description="Enable cost optimization")
    
    # Google APIs
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = Field(default="http://localhost:8000/auth/google/callback")
    
    # Application
    SECRET_KEY: str = Field(default="your_secret_key_here")
    DEBUG: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="INFO")
    BASE_URL: str = Field(default="http://localhost:8000", description="Base URL for webhooks")
    
    # External Services
    SLACK_BOT_TOKEN: Optional[str] = None
    DISCORD_BOT_TOKEN: Optional[str] = None
    
    # Telephony Provider (Twilio only)
    PROVIDER: str = Field(default="twilio", description="Primary telephony provider")
    PHONE_NUMBER: Optional[str] = Field(default=None, description="Primary phone number for the service")
    
    # Feature Flags
    ENABLE_PROACTIVE_MODE: bool = Field(default=True, description="Enable proactive automation mode")
    ENABLE_OUTBOUND_CALLS: bool = Field(default=True, description="Enable AI calling humans")
    ENABLE_PERSISTENT_WAKEUP: bool = Field(default=True, description="Enable persistent wake-up calls")
    ENABLE_DAILY_DIGEST: bool = Field(default=True, description="Enable daily digest SMS")
    
    # Proactive Mode Settings
    PROACTIVE_CHECK_INTERVAL: int = Field(default=300, description="Seconds between proactive checks")
    EMAIL_AUTO_REPLY_ENABLED: bool = Field(default=True, description="Enable automatic email replies")
    CALENDAR_CONFLICT_DETECTION: bool = Field(default=True, description="Enable calendar conflict detection")
    
    # Outbound Call Settings
    MAX_CALL_DURATION: int = Field(default=600, description="Maximum call duration in seconds")
    CALL_RETRY_ATTEMPTS: int = Field(default=3, description="Number of call retry attempts")
    CALL_RETRY_DELAY: int = Field(default=60, description="Delay between call retries in seconds")
    
    # Wake-up Call Settings
    WAKEUP_CALL_RETRY_ATTEMPTS: int = Field(default=5, description="Number of wake-up call retries")
    WAKEUP_CALL_RETRY_DELAY: int = Field(default=300, description="Delay between wake-up call retries in seconds")
    WAKEUP_SMS_FALLBACK: bool = Field(default=True, description="Enable SMS fallback for wake-up calls")
    
    # Digest Settings
    DIGEST_SEND_TIME: str = Field(default="08:00", description="Time to send daily digest (24h format)")
    DIGEST_MAX_EMAILS: int = Field(default=5, description="Maximum emails to include in digest")
    DIGEST_MAX_EVENTS: int = Field(default=3, description="Maximum calendar events to include in digest")
    
    # Audit & Analytics Settings
    AUDIT_LOG_RETENTION_DAYS: int = Field(default=90, description="Days to keep audit logs")
    ENABLE_COST_TRACKING: bool = Field(default=True, description="Enable cost tracking for actions")
    ENABLE_TIME_SAVINGS_TRACKING: bool = Field(default=True, description="Enable time savings tracking")
    
    # Pluto Memory and Learning Settings
    PLUTO_MEMORY_ENABLED: bool = Field(default=True, description="Enable Pluto's long-term memory")
    PLUTO_HABIT_LEARNING_ENABLED: bool = Field(default=True, description="Enable habit learning and pattern detection")
    PLUTO_PROACTIVE_ENABLED: bool = Field(default=True, description="Enable proactive messaging and suggestions")
    PLUTO_MEMORY_RETENTION_DAYS: int = Field(default=365, description="Days to keep memories")
    PLUTO_HABIT_CONFIDENCE_THRESHOLD: float = Field(default=0.6, description="Minimum confidence for habit suggestions")
    PLUTO_PROACTIVE_FREQUENCY_HOURS: int = Field(default=6, description="Hours between proactive checks")
    
    # Redis Settings (for fast context recall)
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    
    # External Contact Permissions
    PLUTO_CAN_CALL_EXTERNAL: bool = Field(default=False, description="Allow Pluto to call external contacts")
    PLUTO_CAN_TEXT_EXTERNAL: bool = Field(default=False, description="Allow Pluto to text external contacts")
    PLUTO_CAN_EMAIL_EXTERNAL: bool = Field(default=False, description="Allow Pluto to email external contacts")
    PLUTO_REQUIRES_CONFIRMATION: bool = Field(default=True, description="Require user confirmation for external actions")
    
    # Admin Settings
    ADMIN_TOKEN: Optional[str] = Field(default=None, description="Admin access token for debugging and management")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields in .env file


# Create global settings instance
settings = Settings()


def get_telephony_provider() -> str:
    """Get the configured telephony provider (Twilio only)"""
    return "twilio"


def is_twilio_enabled() -> bool:
    """Check if Twilio is properly configured"""
    return all([
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN,
        settings.TWILIO_PHONE_NUMBER
    ])


def is_proactive_mode_enabled() -> bool:
    """Check if proactive automation mode is enabled"""
    return settings.ENABLE_PROACTIVE_MODE


def is_outbound_calls_enabled() -> bool:
    """Check if AI calling humans is enabled"""
    return settings.ENABLE_OUTBOUND_CALLS


def is_persistent_wakeup_enabled() -> bool:
    """Check if persistent wake-up calls are enabled"""
    return settings.ENABLE_PERSISTENT_WAKEUP


def is_daily_digest_enabled() -> bool:
    """Check if daily digest is enabled"""
    return settings.ENABLE_DAILY_DIGEST


def is_openrouter_enabled() -> bool:
    """Check if OpenRouter is properly configured (primary AI provider)"""
    return bool(settings.OPENROUTER_API_KEY)


def get_openrouter_preferred_model() -> str:
    """Get the preferred OpenRouter model"""
    return settings.OPENROUTER_PREFERRED_MODEL


def is_openrouter_fallback_enabled() -> bool:
    """Check if OpenRouter fallbacks are enabled"""
    return settings.OPENROUTER_FALLBACK_ENABLED


def is_openrouter_cost_optimization_enabled() -> bool:
    """Check if OpenRouter cost optimization is enabled"""
    return settings.OPENROUTER_COST_OPTIMIZATION


def get_webhook_base_url() -> str:
    """Get the base URL for webhooks"""
    return settings.BASE_URL.rstrip('/')


def is_pluto_memory_enabled() -> bool:
    """Check if Pluto memory is enabled"""
    return settings.PLUTO_MEMORY_ENABLED

def is_pluto_habit_learning_enabled() -> bool:
    """Check if Pluto habit learning is enabled"""
    return settings.PLUTO_HABIT_LEARNING_ENABLED

def is_pluto_proactive_enabled() -> bool:
    """Check if Pluto proactive features are enabled"""
    return settings.PLUTO_PROACTIVE_ENABLED

def get_pluto_memory_retention_days() -> int:
    """Get Pluto memory retention period in days"""
    return settings.PLUTO_MEMORY_RETENTION_DAYS

def get_pluto_habit_confidence_threshold() -> float:
    """Get Pluto habit confidence threshold"""
    return settings.PLUTO_HABIT_CONFIDENCE_THRESHOLD

def get_pluto_proactive_frequency_hours() -> int:
    """Get Pluto proactive check frequency in hours"""
    return settings.PLUTO_PROACTIVE_FREQUENCY_HOURS

def is_pluto_external_calls_allowed() -> bool:
    """Check if Pluto can call external contacts"""
    return settings.PLUTO_CAN_CALL_EXTERNAL

def is_pluto_external_texts_allowed() -> bool:
    """Check if Pluto can text external contacts"""
    return settings.PLUTO_CAN_TEXT_EXTERNAL

def is_pluto_external_emails_allowed() -> bool:
    """Check if Pluto can email external contacts"""
    return settings.PLUTO_CAN_EMAIL_EXTERNAL

def is_pluto_confirmation_required() -> bool:
    """Check if Pluto requires confirmation for external actions"""
    return settings.PLUTO_REQUIRES_CONFIRMATION

"""
Configuration settings for the AI Engine service
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "AI Identity Platform - AI Engine"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # AI & LLM
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    AI_MODEL: str = Field(default="gpt-4", env="AI_MODEL")
    
    # External APIs
    GITHUB_ACCESS_TOKEN: Optional[str] = Field(None, env="GITHUB_ACCESS_TOKEN")
    LINKEDIN_ACCESS_TOKEN: Optional[str] = Field(None, env="LINKEDIN_ACCESS_TOKEN")
    
    # Security
    JWT_SECRET: str = Field(..., env="JWT_SECRET")
    JWT_EXPIRES_IN: str = Field(default="7d", env="JWT_EXPIRES_IN")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    
    # Rate Limiting
    RATE_LIMIT_WINDOW: str = Field(default="15m", env="RATE_LIMIT_WINDOW")
    RATE_LIMIT_MAX_REQUESTS: int = Field(default=100, env="RATE_LIMIT_MAX_REQUESTS")
    
    # File Storage
    AWS_ACCESS_KEY_ID: Optional[str] = Field(None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(None, env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    AWS_S3_BUCKET: Optional[str] = Field(None, env="AWS_S3_BUCKET")
    
    # Monitoring
    SENTRY_DSN: Optional[str] = Field(None, env="SENTRY_DSN")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Feature Flags
    ENABLE_FINANCIAL_CARD: bool = Field(default=False, env="ENABLE_FINANCIAL_CARD")
    ENABLE_CREATOR_CARD: bool = Field(default=False, env="ENABLE_CREATOR_CARD")
    ENABLE_CIVIC_CARD: bool = Field(default=False, env="ENABLE_CIVIC_CARD")
    ENABLE_BLOCKCHAIN_VERIFICATION: bool = Field(default=False, env="ENABLE_BLOCKCHAIN_VERIFICATION")
    
    # AI Processing
    MAX_TOKENS_PER_REQUEST: int = Field(default=4000, env="MAX_TOKENS_PER_REQUEST")
    AI_PROCESSING_TIMEOUT: int = Field(default=30, env="AI_PROCESSING_TIMEOUT")
    
    # Verification
    VERIFICATION_TIMEOUT: int = Field(default=300, env="VERIFICATION_TIMEOUT")  # 5 minutes
    MAX_VERIFICATION_ATTEMPTS: int = Field(default=3, env="MAX_VERIFICATION_ATTEMPTS")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Validate required settings
def validate_settings():
    """Validate that all required settings are present"""
    required_settings = [
        "DATABASE_URL",
        "OPENAI_API_KEY",
        "JWT_SECRET"
    ]
    
    missing_settings = []
    for setting in required_settings:
        if not getattr(settings, setting, None):
            missing_settings.append(setting)
    
    if missing_settings:
        raise ValueError(f"Missing required settings: {', '.join(missing_settings)}")

# Validate on import
validate_settings()

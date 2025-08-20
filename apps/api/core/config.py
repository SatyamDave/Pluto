import os
from typing import List, Optional


class Settings:
    def __init__(self) -> None:
        # Web
        self.NEXT_PUBLIC_APP_URL: str = os.getenv("NEXT_PUBLIC_APP_URL", "http://localhost:3000")

        # API
        self.API_URL: str = os.getenv("API_URL", "http://localhost:8000")
        self.API_JWT_SECRET: str = os.getenv("API_JWT_SECRET", "devjwtsecret")
        self.OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.RATE_LIMIT_PUBLIC_CHAT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PUBLIC_CHAT_PER_MINUTE", "6"))

        # DB & Cache
        self.POSTGRES_URL: str = os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@db:5432/workid")
        self.REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

        # Signing keys
        self.SIGNING_KEY_ROTATE_DAYS: int = int(os.getenv("SIGNING_KEY_ROTATE_DAYS", "30"))

        # CORS
        self.ALLOWED_ORIGINS: List[str] = [self.NEXT_PUBLIC_APP_URL]
        self.ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]


settings = Settings()



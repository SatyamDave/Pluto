#!/usr/bin/env python3
"""
Simple startup script for Pluto
"""

import asyncio
import uvicorn
from main import app

if __name__ == "__main__":
    print("🚀 Starting Pluto AI Assistant...")
    print("📱 SMS Webhook: http://localhost:8000/api/v1/sms/webhook")
    print("🏥 Health Check: http://localhost:8000/api/v1/health")
    print("📊 API Docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

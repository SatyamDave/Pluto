#!/usr/bin/env python3
"""
Simple Pluto startup - works without database setup
"""

import asyncio
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Pluto AI Assistant", version="1.0.0")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Pluto AI Assistant is running!", "status": "ready"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "pluto"}

@app.post("/api/v1/sms/webhook")
async def handle_sms_webhook(request: Request):
    """Handle incoming SMS webhook"""
    try:
        # Parse webhook data
        webhook_data = await request.json()
        logger.info(f"Received webhook: {webhook_data}")
        
        # Extract SMS data (Telnyx format)
        sms_data = webhook_data.get("data", {})
        event_type = sms_data.get("event_type")
        
        if event_type != "message.received":
            return Response(content="OK", status_code=200)
        
        # Extract message details
        payload = sms_data.get("payload", {})
        from_phone = payload.get("from", {}).get("phone_number", "")
        body = payload.get("text", "")
        
        logger.info(f"Received SMS from {from_phone}: {body}")
        
        # Simple AI response (no database required)
        ai_response = await generate_simple_response(body)
        
        # Log the interaction
        logger.info(f"AI Response: {ai_response}")
        
        # Return success (in production, you'd send SMS back via Telnyx)
        return Response(content="OK", status_code=200)
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return Response(content="Error", status_code=500)

async def generate_simple_response(message: str) -> str:
    """Generate a simple AI response without external dependencies"""
    message_lower = message.lower()
    
    # Simple intent recognition
    if any(word in message_lower for word in ["remind", "reminder", "remember"]):
        if "mom" in message_lower or "call" in message_lower:
            return "I'll remind you to call mom tomorrow at 2pm! 📞"
        else:
            return "I'll set that reminder for you! ⏰"
    
    elif any(word in message_lower for word in ["wake", "alarm", "morning"]):
        return "I'll set your alarm! 🌅"
    
    elif any(word in message_lower for word in ["email", "mail", "inbox"]):
        return "I can help you with email! 📧"
    
    elif any(word in message_lower for word in ["schedule", "meeting", "calendar"]):
        return "I can help you with your schedule! 📅"
    
    elif any(word in message_lower for word in ["hello", "hi", "hey"]):
        return "Hello! I'm Pluto, your AI assistant. How can I help you today? 🤖"
    
    else:
        return "I'm here to help! I can set reminders, check email, manage your calendar, and more. What would you like me to do? 💬"

@app.get("/api/v1/sms/status")
async def sms_status():
    """Check SMS service status"""
    return {
        "status": "operational",
        "provider": "telnyx",
        "webhook_endpoint": "/api/v1/sms/webhook",
        "message": "Ready to receive SMS webhooks!"
    }

if __name__ == "__main__":
    print("🚀 Starting Pluto AI Assistant (Simple Mode)...")
    print("📱 SMS Webhook: http://localhost:8000/api/v1/sms/webhook")
    print("🏥 Health Check: http://localhost:8000/health")
    print("📊 API Docs: http://localhost:8000/docs")
    print("💡 This is a simple version that works without database setup")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

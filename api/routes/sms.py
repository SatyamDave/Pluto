"""
SMS handler for Jarvis Phone AI Assistant
Handles incoming SMS messages via Telnyx webhooks and routes them to the AI orchestrator
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import json

from db.database import get_db
from db.models import User, Conversation
from ai_orchestrator import AIOrchestrator
from telephony.telnyx_handler import TelnyxHandler
from config import get_telephony_provider, is_telnyx_enabled
from services.user_manager import user_manager

logger = logging.getLogger(__name__)
router = APIRouter()


class TelnyxSMSWebhook(BaseModel):
    """Telnyx SMS webhook payload"""
    data: dict


class SMSResponse(BaseModel):
    """SMS response model"""
    message: str
    success: bool


@router.post("/webhook", response_class=Response)
async def handle_sms_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle incoming SMS webhook from Telnyx"""
    try:
        # Parse JSON payload from Telnyx webhook
        webhook_data = await request.json()
        
        # Extract SMS data from Telnyx webhook format
        sms_data = webhook_data.get("data", {})
        event_type = sms_data.get("event_type")
        
        # Only process SMS received events
        if event_type != "message.received":
            logger.info(f"Ignoring non-SMS event: {event_type}")
            return Response(content="OK", status_code=200)
        
        # Extract SMS details
        payload = sms_data.get("payload", {})
        from_phone = payload.get("from", {}).get("phone_number", "")
        to_phone = payload.get("to", [{}])[0].get("phone_number", "")
        body = payload.get("text", "")
        message_id = payload.get("id", "")
        
        logger.info(f"Received SMS from {from_phone}: {body}")
        
        # Get or create user using user_manager
        user_profile = await user_manager.get_or_create_user(from_phone, db)
        
        # Check if this is a first-time user (first message)
        is_first_message = user_profile.get("message_count", 0) == 0
        
        # Create conversation record
        conversation = Conversation(
            user_id=user_profile["id"],
            session_id=message_id or "unknown",
            message_type="sms",
            user_message=body,
            ai_response="",  # Will be filled by orchestrator
            intent="",
            action_taken=""
        )
        
        # Handle first-time user onboarding
        if is_first_message:
            onboarding_message = (
                "I'm Pluto—your AI in Messages. I can remind, schedule, text people, and summarize email. "
                "Reply YES to set up. (STOP to opt out)"
            )
            
            # Update conversation
            conversation.ai_response = onboarding_message
            conversation.intent = "onboarding_welcome"
            conversation.action_taken = "onboarding_triggered"
            
            # Send onboarding message
            if is_telnyx_enabled():
                try:
                    handler = TelnyxHandler()
                    await handler.send_sms(
                        to_phone=from_phone,
                        message=onboarding_message
                    )
                    logger.info(f"Onboarding message sent to {from_phone}")
                except Exception as e:
                    logger.error(f"Failed to send onboarding message: {e}")
            
            # Update user message count
            await user_manager.increment_message_count(user_profile["id"])
            
            db.add(conversation)
            await db.commit()
            
            return Response(content="OK", status_code=200)
        
        # Process message with AI orchestrator for existing users
        orchestrator = AIOrchestrator()
        response = await orchestrator.process_message(
            user_id=str(user_profile["id"]),
            message=body,
            message_type="sms"
        )
        
        # Update conversation with AI response
        conversation.ai_response = response.get("response", "")
        conversation.intent = response.get("intent", {}).get("intent", "")
        conversation.action_taken = response.get("intent", {}).get("action", "")
        
        db.add(conversation)
        await db.commit()
        
        # Send SMS response via Telnyx
        if is_telnyx_enabled():
            try:
                handler = TelnyxHandler()
                await handler.send_sms(
                    to_phone=from_phone,
                    message=response.get("message", "I'm sorry, I couldn't process your request.")
                )
                logger.info(f"SMS response sent to {from_phone}")
            except Exception as e:
                logger.error(f"Failed to send SMS response: {e}")
        else:
            logger.warning("Telnyx not enabled, cannot send SMS response")
        
        # Return success response to Telnyx
        return Response(content="OK", status_code=200)
        
    except Exception as e:
        logger.error(f"Error processing SMS: {e}", exc_info=True)
        
        # Return error response to Telnyx
        return Response(content="Error", status_code=500)





@router.get("/status")
async def sms_status():
    """Check SMS service status"""
    provider = get_telephony_provider()
    
    return {
        "status": "operational",
        "provider": provider,
        "telnyx_enabled": is_telnyx_enabled(),
        "webhook_endpoint": "/api/v1/sms/webhook"
    }


@router.post("/send")
async def send_sms(
    to_phone: str,
    message: str,
    db: AsyncSession = Depends(get_db)
):
    """Send outbound SMS via Telnyx"""
    try:
        if not is_telnyx_enabled():
            raise HTTPException(status_code=500, detail="Telnyx not enabled")
        
        handler = TelnyxHandler()
        message_id = await handler.send_sms(to_phone, message)
        
        return {
            "message": "SMS sent successfully",
            "message_id": message_id,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        raise HTTPException(status_code=500, detail="Failed to send SMS")


@router.post("/send-bulk")
async def send_bulk_sms(
    phone_numbers: list,
    message: str,
    db: AsyncSession = Depends(get_db)
):
    """Send bulk SMS via Telnyx"""
    try:
        if not is_telnyx_enabled():
            raise HTTPException(status_code=500, detail="Telnyx not enabled")
        
        handler = TelnyxHandler()
        results = await handler.send_bulk_sms(phone_numbers, message)
        
        return {
            "message": "Bulk SMS completed",
            "results": results,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Failed to send bulk SMS: {e}")
        raise HTTPException(status_code=500, detail="Failed to send bulk SMS")

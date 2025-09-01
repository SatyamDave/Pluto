"""
SMS handler for Jarvis Phone AI Assistant
Handles incoming SMS messages via Telnyx webhooks and routes them to the AI orchestrator
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import json

from db.database import get_db
from db.models import Conversation
from ai_orchestrator import AIOrchestrator
from telephony.twilio_handler import TwilioHandler
from config import get_telephony_provider, is_twilio_enabled
from services.user_manager import user_manager

logger = logging.getLogger(__name__)
router = APIRouter()


class TwilioSMSWebhook(BaseModel):
    """Twilio SMS webhook payload"""
    Body: str
    From: str
    To: str


class SMSResponse(BaseModel):
    """SMS response model"""
    message: str
    success: bool


@router.post("/webhook", response_class=Response)
async def handle_sms_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle incoming SMS webhook from Twilio"""
    try:
        # Get raw body first for debugging
        body = await request.body()
        logger.info(f"Raw webhook body: {body}")
        
        # Check if body is empty
        if not body:
            logger.warning("Received empty webhook body")
            return Response(content="OK", status_code=200)
        
        # Parse form data from Twilio
        try:
            form_data = await request.form()
            webhook_data = dict(form_data)
            logger.info("Parsed Twilio form data")
        except Exception as e:
            logger.error(f"Failed to parse webhook form data: {e}, body: {body}")
            return Response(content="Invalid format", status_code=400)
        
        # Log the full webhook payload for debugging
        logger.info(f"Received Twilio webhook: {json.dumps(webhook_data, indent=2)}")
        
        # Parse Twilio format (including WhatsApp)
        from_phone_raw = webhook_data.get("From", "")
        from_phone = from_phone_raw.replace("whatsapp:", "")
        body_text = webhook_data.get("Body", "")
        message_id = webhook_data.get("SmsMessageSid", "")
        
        # Check if it's a received message
        if webhook_data.get("SmsStatus") != "received":
            logger.info(f"Ignoring non-received Twilio message: {webhook_data.get('SmsStatus')}")
            return Response(content="OK", status_code=200)
            
        logger.info(f"Received Twilio/WhatsApp message from {from_phone}: {body_text}")
        
        # Get or create user using user_manager
        user_profile = await user_manager.get_or_create_user(from_phone, db)
        
        # Check if this is a first-time user (first message)
        is_first_message = user_profile.get("message_count", 0) == 0
        
        # Increment message count for this user
        await user_manager.increment_message_count(user_profile["id"], db)
        
        # Create conversation record
        conversation = Conversation(
            user_id=user_profile["id"],
            session_id=message_id or "unknown",
            message_type="sms",
            user_message=body_text,
            ai_response="",  # Will be filled by orchestrator
            intent="",
            action_taken=""
        )
        print("is_first_message:", is_first_message)
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
            
            # Send onboarding message via Twilio
            if is_twilio_enabled():
                try:
                    handler = TwilioHandler()
                    await handler.send_sms(
                        to_phone=from_phone_raw,
                        message=onboarding_message
                    )
                    
                    # Save conversation
                    db.add(conversation)
                    await db.commit()
                    
                    return Response(content="OK", status_code=200)
                    
                except Exception as e:
                    logger.error(f"Failed to send onboarding SMS: {e}")
                    return Response(content="Error", status_code=500)
            else:
                logger.error("Twilio not enabled")
                return Response(content="Service unavailable", status_code=503)
        
        # Process regular message through AI orchestrator
        orchestrator = AIOrchestrator()
        result = await orchestrator.process_message(
            user_id=user_profile["id"],
            message=body_text,
            message_type="sms"
        )
        
        # Extract AI response
        ai_response = result.get("response", "I'm having trouble processing that right now.")
        
        # Update conversation with AI response
        conversation.ai_response = ai_response
        conversation.intent = result.get("intent", {}).get("intent", "unknown")
        conversation.action_taken = result.get("result", {}).get("action", "none")
        
        # Save conversation
        db.add(conversation)
        await db.commit()
        
        # Send AI response back to user
        if is_twilio_enabled():
            try:
                handler = TwilioHandler()
                await handler.send_sms(
                    to_phone=from_phone_raw,
                    message=ai_response
                )
                
                logger.info(f"Sent AI response to {from_phone}: {ai_response}")
                
            except Exception as e:
                logger.error(f"Failed to send AI response SMS: {e}")
                return Response(content="Error sending response", status_code=500)
        else:
            logger.error("Twilio not enabled")
            return Response(content="Service unavailable", status_code=503)
        
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
        "twilio_enabled": is_twilio_enabled(),
        "webhook_endpoint": "/api/v1/sms/webhook"
    }


@router.post("/send")
async def send_sms(
    to_phone: str,
    message: str
):
    """Send outbound SMS via Twilio"""
    try:
        if not is_twilio_enabled():
            raise HTTPException(status_code=500, detail="Twilio not enabled")
        
        handler = TwilioHandler()
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
    phone_numbers: List[str],
    message: str
):
    """Send bulk SMS via Twilio"""
    try:
        if not is_twilio_enabled():
            raise HTTPException(status_code=500, detail="Twilio not enabled")
        
        handler = TwilioHandler()
        results = await handler.send_bulk_sms(phone_numbers, message)
        
        return {
            "message": "Bulk SMS completed",
            "results": results,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Failed to send bulk SMS: {e}")
        raise HTTPException(status_code=500, detail="Failed to send bulk SMS")

"""
Voice handler for Jarvis Phone AI Assistant
Handles incoming voice calls via Telnyx webhooks and outbound calls with text-to-speech
"""

import logging
from typing import Optional, Dict, Any
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


class TelnyxVoiceWebhook(BaseModel):
    """Telnyx voice webhook payload"""
    data: dict


class VoiceResponse(BaseModel):
    """Voice response model"""
    message: str
    success: bool


@router.post("/webhook/incoming", response_class=Response)
async def handle_incoming_call(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle incoming voice call webhook from Telnyx"""
    try:
        # Parse JSON payload from Telnyx webhook
        webhook_data = await request.json()
        
        # Extract call data from Telnyx webhook format
        call_data = webhook_data.get("data", {})
        event_type = call_data.get("event_type")
        
        # Only process call initiated events
        if event_type != "call.initiated":
            logger.info(f"Ignoring non-call event: {event_type}")
            return Response(content="OK", status_code=200)
        
        # Extract call details
        payload = call_data.get("payload", {})
        from_phone = payload.get("from", {}).get("phone_number", "")
        to_phone = payload.get("to", {}).get("phone_number", "")
        call_id = payload.get("id", "")
        
        logger.info(f"Received incoming call from {from_phone}")
        
        # Get or create user using user_manager
        user_profile = await user_manager.get_or_create_user(from_phone, db)
        
        # Create conversation record
        conversation = Conversation(
            user_id=user_profile["id"],
            session_id=call_id or "unknown",
            message_type="voice",
            user_message="Incoming call",
            ai_response="",
            intent="",
            action_taken=""
        )
        
        db.add(conversation)
        await db.commit()
        
        # Return Telnyx Call Control response
        call_control_response = generate_welcome_call_control()
        
        return Response(
            content=json.dumps(call_control_response),
            media_type="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error handling incoming call: {e}", exc_info=True)
        
        # Return error response to Telnyx
        return Response(content="Error", status_code=500)


async def get_user_style_profile(db: AsyncSession, user_id: int) -> Dict[str, Any]:
    """Get user style profile from style engine"""
    try:
        return await style_engine.get_user_style_profile(str(user_id))
    except Exception as e:
        logger.warning(f"Error getting user style profile: {e}")
        return {}


async def get_user_preferences(db: AsyncSession, user_id: int) -> Dict[str, Any]:
    """Get user preferences from memory manager"""
    try:
        return await memory_manager.get_user_preferences(str(user_id))
    except Exception as e:
        logger.warning(f"Error getting user preferences: {e}")
        return {}


async def get_user_stats(db: AsyncSession, user_id: int) -> Dict[str, Any]:
    """Get user statistics from memory manager"""
    try:
        memory_summary = await memory_manager.get_memory_summary(str(user_id))
        habits = await habit_engine.get_user_habits(str(user_id))
        
        return {
            "memory_count": memory_summary.get("total_count", 0),
            "habit_count": len(habits) if habits else 0
        }
    except Exception as e:
        logger.warning(f"Error getting user stats: {e}")
        return {"memory_count": 0, "habit_count": 0}


@router.post("/webhook/speech", response_class=Response)
async def handle_speech_input(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle speech-to-text input from voice call"""
    try:
        # Parse JSON payload from Telnyx webhook
        webhook_data = await request.json()
        
        # Extract speech data from Telnyx webhook format
        speech_data = webhook_data.get("data", {})
        event_type = speech_data.get("event_type")
        
        # Only process speech events
        if event_type != "call.speech.gathered":
            logger.info(f"Ignoring non-speech event: {event_type}")
            return Response(content="OK", status_code=200)
        
        # Extract speech details
        payload = speech_data.get("payload", {})
        call_id = payload.get("call_control_id", "")
        speech_result = payload.get("result", "")
        
        if not speech_result:
            # No speech detected, ask again
            call_control_response = generate_no_speech_call_control()
            return Response(
                content=json.dumps(call_control_response),
                media_type="application/json"
            )
        
        logger.info(f"Received speech: {speech_result}")
        
        # Get user from call context (this would need call tracking)
        # For now, we'll use a placeholder - in production this should track active calls
        user_profile = await get_user_by_call_id(db, call_id)
        
        # Process speech with AI orchestrator
        orchestrator = AIOrchestrator()
        response = await orchestrator.process_message(
            user_id=str(user_profile["id"]),
            message=speech_result,
            message_type="voice"
        )
        
        # Update conversation
        conversation = Conversation(
            user_id=user_profile["id"],
            session_id=call_id or "unknown",
            message_type="voice",
            user_message=speech_result,
            ai_response=response.get("response", ""),
            intent=response.get("intent", {}).get("intent", ""),
            action_taken=response.get("intent", {}).get("action", "")
        )
        
        db.add(conversation)
        await db.commit()
        
        # Return Telnyx Call Control response with AI response
        call_control_response = generate_speech_response_call_control(response.get("message", ""))
        
        return Response(
            content=json.dumps(call_control_response),
            media_type="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error processing speech: {e}", exc_info=True)
        
        # Return error response to Telnyx
        return Response(content="Error", status_code=500)


@router.post("/call/outbound")
async def make_outbound_call(
    to_phone: str,
    message: str,
    db: AsyncSession = Depends(get_db)
):
    """Make outbound voice call with text-to-speech via Telnyx"""
    try:
        if not is_telnyx_enabled():
            raise HTTPException(status_code=500, detail="Telnyx not enabled")
        
        logger.info(f"Making outbound call to {to_phone}")
        
        handler = TelnyxHandler()
        call_id = await handler.make_call(to_phone, message)
        
        return {
            "message": "Outbound call initiated",
            "call_id": call_id,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Failed to make outbound call: {e}")
        raise HTTPException(status_code=500, detail="Failed to make outbound call")


def generate_welcome_call_control() -> dict:
    """Generate Telnyx Call Control response for welcome message"""
    return {
        "commands": [
            {
                "command": "answer",
                "payload": {}
            },
            {
                "command": "speak",
                "payload": {
                    "text": "Welcome to Jarvis Phone, your AI personal assistant. How can I help you today?",
                    "voice": "female",
                    "language": "en-US"
                }
            },
            {
                "command": "gather",
                "payload": {
                    "type": "speech",
                    "timeout": 10,
                    "speech": {
                        "language": "en-US",
                        "model": "default"
                    },
                    "on_gather": {
                        "webhook_url": "/api/v1/voice/webhook/speech",
                        "webhook_method": "POST"
                    }
                }
            }
        ]
    }


def generate_speech_response_call_control(response_message: str) -> dict:
    """Generate Telnyx Call Control response for AI response"""
    return {
        "commands": [
            {
                "command": "speak",
                "payload": {
                    "text": response_message,
                    "voice": "female",
                    "language": "en-US"
                }
            },
            {
                "command": "gather",
                "payload": {
                    "type": "speech",
                    "timeout": 10,
                    "speech": {
                        "language": "en-US",
                        "model": "default"
                    },
                    "on_gather": {
                        "webhook_url": "/api/v1/voice/webhook/speech",
                        "webhook_method": "POST"
                    }
                }
            },
            {
                "command": "speak",
                "payload": {
                    "text": "Thank you for using Jarvis Phone. Goodbye!",
                    "voice": "female",
                    "language": "en-US"
                }
            },
            {
                "command": "hangup",
                "payload": {}
            }
        ]
    }


def generate_no_speech_call_control() -> dict:
    """Generate Telnyx Call Control response when no speech is detected"""
    return {
        "commands": [
            {
                "command": "speak",
                "payload": {
                    "text": "I didn't hear anything. Please try speaking your request again.",
                    "voice": "female",
                    "language": "en-US"
                }
            },
            {
                "command": "gather",
                "payload": {
                    "type": "speech",
                    "timeout": 10,
                    "speech": {
                        "language": "en-US",
                        "model": "default"
                    },
                    "on_gather": {
                        "webhook_url": "/api/v1/voice/webhook/speech",
                        "webhook_method": "POST"
                    }
                }
            },
            {
                "command": "speak",
                "payload": {
                    "text": "I still didn't hear anything. Please call back and try again.",
                    "voice": "female",
                    "language": "en-US"
                }
            },
            {
                "command": "hangup",
                "payload": {}
            }
        ]
    }


def generate_error_call_control() -> dict:
    """Generate Telnyx Call Control response for error handling"""
    return {
        "commands": [
            {
                "command": "speak",
                "payload": {
                    "text": "I'm sorry, I encountered an error. Please try calling back later.",
                    "voice": "female",
                    "language": "en-US"
                }
            },
            {
                "command": "hangup",
                "payload": {}
            }
        ]
    }





async def get_user_by_call_id(db: AsyncSession, call_id: str) -> Dict[str, Any]:
    """Get user by call ID from conversation history"""
    try:
        # Query the database for active calls with this call ID
        # This would typically be stored in a call_sessions table
        # For now, we'll implement a basic lookup system
        
        # Check if we have a call session record
        call_query = """
            SELECT user_id, phone_number, created_at 
            FROM call_sessions 
            WHERE call_id = :call_id 
            AND status = 'active'
            ORDER BY created_at DESC 
            LIMIT 1
        """
        
        try:
            result = await db.execute(call_query, {"call_id": call_id})
            call_session = result.fetchone()
            
            if call_session:
                # Get user details from the call session
                user_query = """
                    SELECT id, phone_number, name, email, is_active, 
                           created_at, updated_at, last_seen
                    FROM users 
                    WHERE id = :user_id
                """
                
                user_result = await db.execute(user_query, {"user_id": call_session.user_id})
                user = user_result.fetchone()
                
                if user:
                    return {
                        "id": user.id,
                        "phone_number": user.phone_number,
                        "name": user.name,
                        "email": user.email,
                        "is_active": user.is_active,
                        "created_at": user.created_at,
                        "updated_at": user.updated_at,
                        "last_seen": user.last_seen,
                        "style_profile": await get_user_style_profile(db, user.id),
                        "preferences": await get_user_preferences(db, user.id),
                        "stats": await get_user_stats(db, user.id)
                    }
        except Exception as e:
            logger.warning(f"Error looking up call session: {e}")
        
        # Fallback: try to find user by recent call history
        # This is a simplified approach for when call_sessions table doesn't exist
        logger.info(f"No active call session found for call_id: {call_id}, using fallback lookup")
        
        # Return a default user profile for now
        # In production, you'd want to implement proper call tracking
        return {
            "id": 1,  # Default ID
            "phone_number": "unknown",
            "name": None,
            "email": None,
            "is_active": True,
            "created_at": None,
            "updated_at": None,
            "last_seen": None,
            "style_profile": {},
            "preferences": {},
            "stats": {"memory_count": 0, "habit_count": 0}
        }
        
    except Exception as e:
        logger.error(f"Error getting user by call ID: {e}")
        # Return safe default values
        return {
            "id": 1,
            "phone_number": "unknown",
            "name": None,
            "email": None,
            "is_active": True,
            "created_at": None,
            "updated_at": None,
            "last_seen": None,
            "style_profile": {},
            "preferences": {},
            "stats": {"memory_count": 0, "habit_count": 0}
        }


@router.get("/status")
async def voice_status():
    """Check voice service status"""
    provider = get_telephony_provider()
    
    return {
        "status": "operational",
        "provider": provider,
        "telnyx_enabled": is_telnyx_enabled(),
        "webhook_endpoint": "/api/v1/voice/webhook/incoming"
    }


@router.post("/webhook/wakeup")
async def handle_wakeup_confirmation(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle wake-up call confirmation webhook"""
    try:
        # Parse JSON payload from Telnyx webhook
        webhook_data = await request.json()
        
        # Extract DTMF data from Telnyx webhook format
        dtmf_data = webhook_data.get("data", {})
        event_type = dtmf_data.get("event_type")
        
        if event_type != "call.dtmf.gathered":
            return Response(content="OK", status_code=200)
        
        # Extract DTMF digits
        payload = dtmf_data.get("payload", {})
        digits = payload.get("digits", "")
        call_id = payload.get("call_control_id", "")
        
        logger.info(f"Wake-up confirmation received: digits={digits}, call_id={call_id}")
        
        if digits == "1":
            # User confirmed they're awake
            logger.info(f"User confirmed wake-up for call {call_id}")
            
            # Return Call Control confirming wake-up
            call_control_response = {
                "commands": [
                    {
                        "command": "speak",
                        "payload": {
                            "text": "Great! You're awake. Have a wonderful day!",
                            "voice": "female",
                            "language": "en-US"
                        }
                    },
                    {
                        "command": "hangup",
                        "payload": {}
                    }
                ]
            }
            
            return Response(
                content=json.dumps(call_control_response),
                media_type="application/json"
            )
        
        else:
            # Invalid input, ask again
            call_control_response = {
                "commands": [
                    {
                        "command": "speak",
                        "payload": {
                            "text": "I didn't understand that input. Please press 1 to confirm you're awake.",
                            "voice": "female",
                            "language": "en-US"
                        }
                    },
                    {
                        "command": "gather",
                        "payload": {
                            "type": "dtmf",
                            "timeout": 15,
                            "on_gather": {
                                "webhook_url": "/api/v1/voice/webhook/wakeup",
                                "webhook_method": "POST"
                            }
                        }
                    },
                    {
                        "command": "speak",
                        "payload": {
                            "text": "Press 1 to confirm you're awake.",
                            "voice": "female",
                            "language": "en-US"
                        }
                    }
                ]
            }
            
            return Response(
                content=json.dumps(call_control_response),
                media_type="application/json"
            )
        
    except Exception as e:
        logger.error(f"Error handling wake-up confirmation: {e}", exc_info=True)
        return Response(content="Error", status_code=500)

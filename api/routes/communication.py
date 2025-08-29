"""
Communication Routes for Jarvis Phone AI Assistant
Handles API endpoints for communication hub features
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from services.communication_service import CommunicationService, ContactType
from services.audit_service import AuditService

logger = logging.getLogger(__name__)
router = APIRouter()


class TextOnBehalfRequest(BaseModel):
    """Request model for texting on behalf"""
    user_id: int
    recipient_name: str
    message: str


class ForwardNotesRequest(BaseModel):
    """Request model for forwarding notes"""
    user_id: int
    recipient_name: str
    note_query: str = "latest"


class SlackMessageRequest(BaseModel):
    """Request model for sending Slack messages"""
    user_id: int
    channel: str
    message: str


class DiscordMessageRequest(BaseModel):
    """Request model for sending Discord messages"""
    user_id: int
    channel: str
    message: str


class AddContactRequest(BaseModel):
    """Request model for adding contacts"""
    user_id: int
    name: str
    contact_type: str
    value: str


class MessageResult(BaseModel):
    """Response model for message operations"""
    success: bool
    message: str
    message_id: Optional[str] = None
    error_message: Optional[str] = None


@router.post("/text-on-behalf", response_model=MessageResult)
async def text_on_behalf(request: TextOnBehalfRequest):
    """Send SMS on behalf of user"""
    try:
        communication_service = CommunicationService()
        
        # Validate contact type
        try:
            contact_type = ContactType(request.contact_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid contact type: {request.contact_type}")
        
        # Send SMS
        result = await communication_service.text_on_behalf(
            user_id=request.user_id,
            recipient_name=request.recipient_name,
            message=request.message
        )
        
        if result.success:
            return MessageResult(
                success=True,
                message=f"Message sent to {request.recipient_name} successfully",
                message_id=result.message_id
            )
        else:
            return MessageResult(
                success=False,
                message="Failed to send message",
                error_message=result.error_message
            )
        
    except Exception as e:
        logger.error(f"Error sending SMS on behalf: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forward-notes", response_model=MessageResult)
async def forward_notes(request: ForwardNotesRequest):
    """Forward notes to a contact"""
    try:
        communication_service = CommunicationService()
        
        # Forward notes
        result = await communication_service.forward_notes(
            user_id=request.user_id,
            recipient_name=request.recipient_name,
            note_query=request.note_query
        )
        
        if result.success:
            return MessageResult(
                success=True,
                message=f"Notes forwarded to {request.recipient_name} successfully",
                message_id=result.message_id
            )
        else:
            return MessageResult(
                success=False,
                message="Failed to forward notes",
                error_message=result.error_message
            )
        
    except Exception as e:
        logger.error(f"Error forwarding notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/slack/send", response_model=MessageResult)
async def send_slack_message(request: SlackMessageRequest):
    """Send message to Slack channel"""
    try:
        communication_service = CommunicationService()
        
        # Send to Slack
        result = await communication_service.send_to_slack(
            user_id=request.user_id,
            channel=request.channel,
            message=request.message
        )
        
        if result.success:
            return MessageResult(
                success=True,
                message=f"Message sent to Slack #{request.channel} successfully",
                message_id=result.message_id
            )
        else:
            return MessageResult(
                success=False,
                message="Failed to send Slack message",
                error_message=result.error_message
            )
        
    except Exception as e:
        logger.error(f"Error sending Slack message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/discord/send", response_model=MessageResult)
async def send_discord_message(request: DiscordMessageRequest):
    """Send message to Discord channel"""
    try:
        communication_service = CommunicationService()
        
        # Send to Discord
        result = await communication_service.send_to_discord(
            user_id=request.user_id,
            channel=request.channel,
            message=request.message
        )
        
        if result.success:
            return MessageResult(
                success=True,
                message=f"Message sent to Discord #{request.channel} successfully",
                message_id=result.message_id
            )
        else:
            return MessageResult(
                success=False,
                message="Failed to send Discord message",
                error_message=result.error_message
            )
        
    except Exception as e:
        logger.error(f"Error sending Discord message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contacts/add")
async def add_contact(request: AddContactRequest):
    """Add a new contact for a user"""
    try:
        communication_service = CommunicationService()
        
        # Validate contact type
        try:
            contact_type = ContactType(request.contact_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid contact type: {request.contact_type}")
        
        # Add contact
        success = await communication_service.add_contact(
            user_id=request.user_id,
            name=request.name,
            contact_type=contact_type,
            value=request.value
        )
        
        if success:
            return {
                "message": f"Contact {request.name} added successfully",
                "contact_type": request.contact_type,
                "value": request.value
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add contact")
        
    except Exception as e:
        logger.error(f"Error adding contact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contacts/{user_id}")
async def get_user_contacts(user_id: int):
    """Get all contacts for a user"""
    try:
        communication_service = CommunicationService()
        
        contacts = await communication_service.get_user_contacts(user_id)
        
        return {
            "user_id": user_id,
            "contacts": [
                {
                    "name": contact.name,
                    "contact_type": contact.contact_type.value,
                    "value": contact.value,
                    "is_verified": contact.is_verified
                }
                for contact in contacts
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting user contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{user_id}")
async def get_communication_summary(user_id: int, date: str = None):
    """Get communication summary for a user"""
    try:
        communication_service = CommunicationService()
        
        # Parse date if provided
        target_date = None
        if date:
            from datetime import datetime
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        summary = await communication_service.get_communication_summary(user_id, target_date)
        
        return {
            "user_id": user_id,
            "date": target_date.isoformat() if target_date else "today",
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting communication summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def communication_status():
    """Get communication service status"""
    try:
        from config import settings
        
        return {
            "status": "operational",
            "features": {
                "sms": True,
                "email": True,
                "slack": bool(settings.SLACK_BOT_TOKEN),
                "discord": bool(settings.DISCORD_BOT_TOKEN)
            },
            "telephony_provider": "twilio" if settings.TWILIO_ACCOUNT_SID else "telnyx" if settings.TELNYX_API_KEY else "none"
        }
        
    except Exception as e:
        logger.error(f"Error getting communication status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

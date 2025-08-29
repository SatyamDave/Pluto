"""
Onboarding API routes for Jarvis Phone AI Assistant
Handles user activation and contact permissions
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from services.user_manager import user_manager
from services.communication_service import CommunicationService
from services.audit_service import AuditService

logger = logging.getLogger(__name__)
router = APIRouter()


class OnboardingRequest(BaseModel):
    """Onboarding request model"""
    phone_number: str
    name: str
    timezone: str = "UTC"
    language: str = "en"


class ContactPermissionRequest(BaseModel):
    """Contact permission request model"""
    contact_name: str
    contact_phone: str
    permission_type: str = "always"  # "always", "once", "never"


class OnboardingResponse(BaseModel):
    """Onboarding response model"""
    user_id: int
    status: str
    message: str
    next_steps: list[str]


@router.post("/activate", response_model=OnboardingResponse)
async def activate_user(
    request: OnboardingRequest,
    db: AsyncSession = Depends(get_db)
):
    """Activate a new user"""
    try:
        # Check if user already exists
        existing_user = await user_manager.get_user_by_phone(request.phone_number)
        if existing_user:
            return OnboardingResponse(
                user_id=existing_user["id"],
                status="existing",
                message="Welcome back! You're already activated.",
                next_steps=["Text me anything to get started"]
            )
        
        # Create new user
        user_data = {
            "phone_number": request.phone_number,
            "name": request.name,
            "timezone": request.timezone,
            "language": request.language,
            "preferences": {
                "proactive_mode": True,
                "morning_digest_time": "08:00",
                "evening_digest_time": "18:00",
                "device_type": "unknown",
                "device_bridge_enabled": False
            }
        }
        
        new_user = await user_manager.create_user(user_data)
        
        if not new_user:
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        # Send welcome message
        welcome_message = (
            f"Welcome to Pluto, {request.name}! 🎉\n\n"
            "I'm your AI assistant in Messages. I can:\n"
            "• Set reminders and manage your calendar\n"
            "• Send texts and emails on your behalf\n"
            "• Summarize your inbox and Slack\n"
            "• Give directions and open apps\n\n"
            "Just text me what you need. Try:\n"
            "• 'remind me to call mom at 6pm'\n"
            "• 'what's on my calendar today?'\n"
            "• 'text Jon I'm running 10 min late'"
        )
        
        # Send welcome SMS
        communication_service = CommunicationService()
        await communication_service.send_sms(
            to=request.phone_number,
            body=welcome_message,
            user_id=new_user["id"]
        )
        
        # Log activation
        audit_service = AuditService()
        await audit_service.log_action(
            user_id=new_user["id"],
            action_type="user_activation",
            details={
                "phone_number": request.phone_number,
                "name": request.name,
                "timezone": request.timezone,
                "language": request.language
            }
        )
        
        logger.info(f"User activated: {request.phone_number} ({request.name})")
        
        return OnboardingResponse(
            user_id=new_user["id"],
            status="activated",
            message="Welcome to Pluto! You're all set up.",
            next_steps=[
                "Text me anything to get started",
                "Try 'remind me to call mom at 6pm'",
                "Ask 'what's on my calendar today?'"
            ]
        )
        
    except Exception as e:
        logger.error(f"Error activating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate user")


@router.post("/contact-permission")
async def request_contact_permission(
    request: ContactPermissionRequest,
    user_id: int,  # In production, get from auth token
    db: AsyncSession = Depends(get_db)
):
    """Request permission to text a new contact"""
    try:
        # Check if contact already exists and has permissions
        communication_service = CommunicationService()
        existing_contact = await communication_service.get_contact_by_phone(
            user_id, request.contact_phone
        )
        
        if existing_contact:
            permission = existing_contact.get("permission", "never")
            if permission == "always":
                return {
                    "status": "permitted",
                    "message": f"Already have permission to text {request.contact_name}",
                    "contact_id": existing_contact["id"]
                }
            elif permission == "never":
                return {
                    "status": "denied",
                    "message": f"Permission denied to text {request.contact_name}",
                    "contact_id": existing_contact["id"]
                }
        
        # Create permission request
        permission_request = await communication_service.create_contact_permission_request(
            user_id=user_id,
            contact_name=request.contact_name,
            contact_phone=request.contact_phone,
            permission_type=request.permission_type
        )
        
        # Send permission request SMS to user
        permission_message = (
            f"📱 Contact Permission Request\n\n"
            f"Contact: {request.contact_name} ({request.contact_phone})\n\n"
            f"Reply with:\n"
            f"• 'yes' - Allow this time only\n"
            f"• 'always' - Always allow texting {request.contact_name}\n"
            f"• 'no' - Never allow texting {request.contact_name}"
        )
        
        user_profile = await user_manager.get_user_by_id(user_id)
        if user_profile and user_profile.get("phone_number"):
            await communication_service.send_sms(
                to=user_profile["phone_number"],
                body=permission_message,
                user_id=user_id
            )
        
        return {
            "status": "pending",
            "message": f"Permission request sent for {request.contact_name}",
            "request_id": permission_request["id"]
        }
        
    except Exception as e:
        logger.error(f"Error requesting contact permission: {e}")
        raise HTTPException(status_code=500, detail="Failed to request contact permission")


@router.post("/contact-permission/{request_id}/respond")
async def respond_to_contact_permission(
    request_id: int,
    response: str,  # "yes", "always", "no"
    user_id: int,  # In production, get from auth token
    db: AsyncSession = Depends(get_db)
):
    """Respond to a contact permission request"""
    try:
        communication_service = CommunicationService()
        
        # Get the permission request
        permission_request = await communication_service.get_contact_permission_request(request_id)
        if not permission_request or permission_request["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Permission request not found")
        
        # Process the response
        if response.lower() in ["yes", "always"]:
            permission_type = "always" if response.lower() == "always" else "once"
            
            # Update contact permissions
            await communication_service.update_contact_permission(
                user_id=user_id,
                contact_phone=permission_request["contact_phone"],
                permission=permission_type
            )
            
            # Mark request as approved
            await communication_service.update_permission_request_status(
                request_id, "approved"
            )
            
            message = f"✅ Permission granted to text {permission_request['contact_name']}"
            
        elif response.lower() == "no":
            # Update contact permissions to denied
            await communication_service.update_contact_permission(
                user_id=user_id,
                contact_phone=permission_request["contact_phone"],
                permission="never"
            )
            
            # Mark request as denied
            await communication_service.update_permission_request_status(
                request_id, "denied"
            )
            
            message = f"❌ Permission denied to text {permission_request['contact_name']}"
            
        else:
            raise HTTPException(status_code=400, detail="Invalid response. Use 'yes', 'always', or 'no'")
        
        # Log the response
        audit_service = AuditService()
        await audit_service.log_action(
            user_id=user_id,
            action_type="contact_permission_response",
            details={
                "request_id": request_id,
                "response": response,
                "contact_name": permission_request["contact_name"],
                "contact_phone": permission_request["contact_phone"]
            }
        )
        
        return {
            "status": "processed",
            "message": message,
            "permission": permission_type if response.lower() in ["yes", "always"] else "denied"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error responding to contact permission: {e}")
        raise HTTPException(status_code=500, detail="Failed to process permission response")


@router.get("/status/{user_id}")
async def get_onboarding_status(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get user's onboarding status and progress"""
    try:
        user_profile = await user_manager.get_user_by_id(user_id)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's contacts and permissions
        communication_service = CommunicationService()
        contacts = await communication_service.get_user_contacts(user_id)
        
        # Calculate onboarding progress
        progress_items = [
            "account_created",
            "first_reminder_set" if user_profile.get("first_reminder_at") else None,
            "calendar_linked" if user_profile.get("calendar_linked") else None,
            "email_linked" if user_profile.get("email_linked") else None,
            "slack_linked" if user_profile.get("slack_linked") else None
        ]
        
        progress_items = [item for item in progress_items if item]
        progress_percentage = (len(progress_items) / 5) * 100
        
        return {
            "user_id": user_id,
            "status": "active" if user_profile.get("activated_at") else "pending",
            "progress_percentage": progress_percentage,
            "completed_items": progress_items,
            "total_contacts": len(contacts),
            "contacts_with_permission": len([c for c in contacts if c.get("permission") in ["always", "once"]]),
            "next_steps": [
                "Set your first reminder",
                "Link your calendar",
                "Connect your email",
                "Add Slack integration"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting onboarding status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get onboarding status")

"""
Email API routes for Jarvis Phone AI Assistant
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from email_service.email_service import EmailService

logger = logging.getLogger(__name__)
router = APIRouter()


class EmailCompose(BaseModel):
    """Email compose request model"""
    to: str
    subject: str
    body: str
    reply_to_message_id: str = None


class EmailSend(BaseModel):
    """Email send confirmation model"""
    draft_id: str
    confirm: bool  # True to send, False to cancel


class EmailSummary(BaseModel):
    """Email summary response model"""
    total_emails: int
    unread_count: int
    recent_emails: int
    top_senders: List[dict]
    period_days: int


@router.get("/unread/{user_id}")
async def get_unread_emails(
    user_id: int,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get unread emails for a user"""
    try:
        service = EmailService()
        emails = await service.get_unread_emails(user_id, limit)
        
        return {
            "user_id": user_id,
            "unread_count": len(emails),
            "emails": emails
        }
        
    except Exception as e:
        logger.error(f"Error getting unread emails: {e}")
        raise HTTPException(status_code=500, detail="Failed to get unread emails")


@router.get("/summary/{user_id}", response_model=EmailSummary)
async def get_email_summary(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get email summary for a user"""
    try:
        service = EmailService()
        summary = await service.get_email_summary(user_id)
        
        if "error" in summary:
            raise HTTPException(status_code=400, detail=summary["error"])
        
        return EmailSummary(**summary)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get email summary")


@router.get("/analytics/{user_id}")
async def get_email_analytics(
    user_id: int,
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """Get email analytics for a user"""
    try:
        service = EmailService()
        analytics = await service.get_email_analytics(user_id, days)
        
        if "error" in analytics:
            raise HTTPException(status_code=400, detail=analytics["error"])
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get email analytics")


@router.post("/mark-read/{user_id}")
async def mark_email_read(
    user_id: int,
    message_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Mark an email as read"""
    try:
        service = EmailService()
        success = await service.mark_email_read(user_id, message_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to mark email as read")
        
        return {"message": "Email marked as read successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking email as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark email as read")


@router.post("/compose")
async def compose_email(
    email_data: EmailCompose,
    user_id: int,  # In production, get from auth token
    db: AsyncSession = Depends(get_db)
):
    """Compose a new email (creates draft)"""
    try:
        service = EmailService()
        draft = await service.compose_email(
            user_id=user_id,
            to=email_data.to,
            subject=email_data.subject,
            body=email_data.body,
            reply_to_message_id=email_data.reply_to_message_id
        )
        
        if "error" in draft:
            raise HTTPException(status_code=400, detail=draft["error"])
        
        return {
            "message": "Email draft created successfully",
            "draft_id": draft["draft_id"],
            "preview": f"Drafted to {email_data.to}: '{email_data.subject}'",
            "body_preview": email_data.body[:100] + "..." if len(email_data.body) > 100 else email_data.body
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error composing email: {e}")
        raise HTTPException(status_code=500, detail="Failed to compose email")


@router.post("/send")
async def send_email(
    send_data: EmailSend,
    user_id: int,  # In production, get from auth token
    db: AsyncSession = Depends(get_db)
):
    """Send a composed email draft"""
    try:
        service = EmailService()
        
        if not send_data.confirm:
            # Cancel the draft
            success = await service.cancel_draft(user_id, send_data.draft_id)
            return {"message": "Email draft cancelled"}
        
        # Send the email
        result = await service.send_draft(
            user_id=user_id,
            draft_id=send_data.draft_id
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "message": "Email sent successfully",
            "message_id": result.get("message_id"),
            "sent_to": result.get("to")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email")

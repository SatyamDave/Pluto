"""
Slack API routes for Jarvis Phone AI Assistant
Handles incoming Slack events and reactions
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from services.communication_service import CommunicationService
from services.audit_service import AuditService

logger = logging.getLogger(__name__)
router = APIRouter()


class SlackEvent(BaseModel):
    """Slack event model"""
    type: str
    user: str = None
    channel: str = None
    text: str = None
    ts: str = None
    reaction: str = None
    item: Dict[str, Any] = None


class SlackEventChallenge(BaseModel):
    """Slack URL verification challenge"""
    challenge: str
    token: str
    type: str


@router.post("/events")
async def handle_slack_events(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle incoming Slack events"""
    try:
        # Parse the request body
        body = await request.json()
        
        # Handle URL verification challenge
        if body.get("type") == "url_verification":
            challenge = SlackEventChallenge(**body)
            logger.info("Slack URL verification challenge received")
            return {"challenge": challenge.challenge}
        
        # Handle actual events
        if body.get("type") == "event_callback":
            event = body.get("event", {})
            event_type = event.get("type")
            
            logger.info(f"Received Slack event: {event_type}")
            
            if event_type == "reaction_added":
                await _handle_slack_reaction(event, body.get("team_id"))
            elif event_type == "message":
                await _handle_slack_message(event, body.get("team_id"))
            elif event_type == "app_mention":
                await _handle_app_mention(event, body.get("team_id"))
            
            return {"status": "ok"}
        
        return {"status": "ignored"}
        
    except Exception as e:
        logger.error(f"Error handling Slack event: {e}")
        raise HTTPException(status_code=500, detail="Failed to process Slack event")


async def _handle_slack_reaction(event: Dict[str, Any], team_id: str):
    """Handle Slack reaction events (e.g., ✅ to mark task complete)"""
    try:
        reaction = event.get("reaction")
        user = event.get("user")
        item = event.get("item", {})
        
        # Check if it's a ✅ reaction on a message
        if reaction == "white_check_mark" and item.get("type") == "message":
            message_ts = item.get("ts")
            channel = item.get("channel")
            
            logger.info(f"Task completion reaction from {user} in {channel}")
            
            # Get the message content to identify the task
            message_content = await _get_slack_message(channel, message_ts, team_id)
            
            if message_content:
                # Parse the message to identify the task
                task_info = await _parse_task_from_message(message_content)
                
                if task_info:
                    # Mark task as complete
                    await _mark_task_complete(user, task_info, team_id)
                    
                    # Send confirmation
                    await _send_task_completion_confirmation(channel, user, task_info)
            
            # Log the completion
            await _log_task_completion(user, channel, message_ts, team_id)
            
    except Exception as e:
        logger.error(f"Error handling Slack reaction: {e}")


async def _handle_slack_message(event: Dict[str, Any], team_id: str):
    """Handle Slack message events"""
    try:
        user = event.get("user")
        channel = event.get("channel")
        text = event.get("text")
        ts = event.get("ts")
        
        # Log the message for audit purposes
        await _log_slack_message(user, channel, text, ts, team_id)
        
    except Exception as e:
        logger.error(f"Error handling Slack message: {e}")


async def _handle_app_mention(event: Dict[str, Any], team_id: str):
    """Handle Slack app mentions"""
    try:
        user = event.get("user")
        channel = event.get("channel")
        text = event.get("text")
        ts = event.get("ts")
        
        logger.info(f"App mention from {user} in {channel}: {text}")
        
        # Parse the mention and respond
        # This could trigger actions like creating reminders, etc.
        
    except Exception as e:
        logger.error(f"Error handling Slack app mention: {e}")


async def _log_task_completion(user: str, channel: str, message_ts: str, team_id: str):
    """Log task completion for audit purposes"""
    try:
        audit_service = AuditService()
        await audit_service.log_action(
            user_id=None,  # Slack user ID
            action_type="slack_task_completion",
            details={
                "slack_user": user,
                "channel": channel,
                "message_ts": message_ts,
                "team_id": team_id,
                "reaction": "white_check_mark"
            }
        )
        
        logger.info(f"Logged Slack task completion from {user} in {channel}")
        
    except Exception as e:
        logger.error(f"Error logging Slack task completion: {e}")


async def _log_slack_message(user: str, channel: str, text: str, ts: str, team_id: str):
    """Log Slack message for audit purposes"""
    try:
        audit_service = AuditService()
        await audit_service.log_action(
            user_id=None,  # Slack user ID
            action_type="slack_message",
            details={
                "slack_user": user,
                "channel": channel,
                "text": text[:100] if text else "",  # Truncate long messages
                "message_ts": ts,
                "team_id": team_id
            }
        )
        
    except Exception as e:
        logger.error(f"Error logging Slack message: {e}")


@router.get("/health")
async def slack_health_check():
    """Health check for Slack integration"""
    try:
        # Check if Slack bot token is configured
        from config import settings
        if settings.SLACK_BOT_TOKEN:
            return {
                "status": "healthy",
                "slack_configured": True,
                "message": "Slack integration is active"
            }
        else:
            return {
                "status": "unconfigured",
                "slack_configured": False,
                "message": "Slack bot token not configured"
            }
            
    except Exception as e:
        logger.error(f"Error checking Slack health: {e}")
        return {
            "status": "error",
            "slack_configured": False,
            "message": f"Error: {str(e)}"
        }


async def _get_slack_message(channel: str, message_ts: str, team_id: str) -> Optional[str]:
    """Get Slack message content from API"""
    try:
        from config import settings
        
        if not settings.SLACK_BOT_TOKEN:
            logger.warning("Slack bot token not configured")
            return None
        
        # This would use Slack Web API to fetch message
        # For now, return placeholder
        logger.info(f"Would fetch message {message_ts} from channel {channel}")
        return "Sample task message"
        
    except Exception as e:
        logger.error(f"Error getting Slack message: {e}")
        return None


async def _parse_task_from_message(message: str) -> Optional[Dict[str, Any]]:
    """Parse task information from Slack message"""
    try:
        # Simple task parsing logic
        # Look for common task patterns
        task_patterns = [
            r"task:\s*(.+)",
            r"todo:\s*(.+)",
            r"reminder:\s*(.+)",
            r"follow up:\s*(.+)"
        ]
        
        for pattern in task_patterns:
            import re
            match = re.search(pattern, message.lower())
            if match:
                return {
                    "type": "task",
                    "description": match.group(1).strip(),
                    "source": "slack",
                    "message": message
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Error parsing task from message: {e}")
        return None


async def _mark_task_complete(user: str, task_info: Dict[str, Any], team_id: str):
    """Mark task as complete in the system"""
    try:
        # This would integrate with the reminder/task system
        # For now, just log it
        logger.info(f"Task marked complete by {user}: {task_info}")
        
        # TODO: Integrate with reminder service to mark tasks complete
        
    except Exception as e:
        logger.error(f"Error marking task complete: {e}")


async def _send_task_completion_confirmation(channel: str, user: str, task_info: Dict[str, Any]):
    """Send confirmation message to Slack channel"""
    try:
        # This would use Slack Web API to send message
        # For now, just log it
        confirmation = f"✅ Task completed by <@{user}>: {task_info.get('description', 'Unknown task')}"
        logger.info(f"Would send confirmation to {channel}: {confirmation}")
        
        # TODO: Use Slack Web API to send confirmation
        
    except Exception as e:
        logger.error(f"Error sending task completion confirmation: {e}")

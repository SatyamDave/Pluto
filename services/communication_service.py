"""
Communication Service for Jarvis Phone AI Assistant
Handles texting on behalf, forwarding notes, and cross-platform messaging
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from config import settings
from telephony.twilio_handler import TwilioHandler
from telephony.telnyx_handler import TelnyxHandler
from config import get_telephony_provider, is_twilio_enabled, is_telnyx_enabled
from notes.notes_service import NotesService
from email_service.email_service import EmailService

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Type of message to send"""
    SMS = "sms"
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"


class ContactType(Enum):
    """Type of contact"""
    PHONE = "phone"
    EMAIL = "email"
    SLACK_CHANNEL = "slack_channel"
    DISCORD_CHANNEL = "discord_channel"


@dataclass
class Contact:
    """Contact information"""
    name: str
    contact_type: ContactType
    value: str  # phone number, email, or channel
    user_id: int
    is_verified: bool = False


@dataclass
class MessageRequest:
    """Request to send a message"""
    user_id: int
    recipient: str  # name or identifier
    message: str
    message_type: MessageType
    urgency: str = "normal"  # low, normal, high, urgent


@dataclass
class MessageResult:
    """Result of sending a message"""
    success: bool
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivery_status: Optional[str] = None


class CommunicationService:
    """Service for managing cross-platform communication"""
    
    def __init__(self):
        self.telephony_provider = get_telephony_provider()
        self.notes_service = NotesService()
        self.email_service = EmailService()
        
        # Initialize telephony handler for SMS
        if self.telephony_provider == "twilio" and is_twilio_enabled():
            self.sms_handler = TwilioHandler()
        elif self.telephony_provider == "telnyx" and is_telnyx_enabled():
            self.sms_handler = TelnyxHandler()
        else:
            logger.warning("No valid telephony provider configured for SMS")
            self.sms_handler = None
        
        # Initialize external platform handlers
        self.slack_handler = None
        self.discord_handler = None
        
        if settings.SLACK_BOT_TOKEN:
            try:
                from integrations.slack_handler import SlackHandler
                self.slack_handler = SlackHandler()
            except ImportError:
                logger.warning("Slack handler not available")
        
        if settings.DISCORD_BOT_TOKEN:
            try:
                from integrations.discord_handler import DiscordHandler
                self.discord_handler = DiscordHandler()
            except ImportError:
                logger.warning("Discord handler not available")
    
    async def text_on_behalf(
        self, 
        user_id: int, 
        recipient_name: str, 
        message: str
    ) -> MessageResult:
        """Send SMS on behalf of user to a contact"""
        try:
            logger.info(f"User {user_id} requesting to text {recipient_name}: {message}")
            
            # Find contact by name
            contact = await self._find_contact_by_name(user_id, recipient_name)
            
            if not contact:
                return MessageResult(
                    success=False,
                    error_message=f"Contact '{recipient_name}' not found. Please add them first."
                )
            
            if contact.contact_type != ContactType.PHONE:
                return MessageResult(
                    success=False,
                    error_message=f"'{recipient_name}' is not a phone contact. They're registered as {contact.contact_type.value}."
                )
            
            # Send SMS
            if self.sms_handler:
                message_id = await self.sms_handler.send_sms(contact.value, message)
                
                # Log the action
                await self._log_communication_action(
                    user_id, "sms_sent", recipient_name, message, message_id
                )
                
                return MessageResult(
                    success=True,
                    message_id=message_id,
                    sent_at=datetime.utcnow(),
                    delivery_status="sent"
                )
            else:
                return MessageResult(
                    success=False,
                    error_message="SMS service not available"
                )
                
        except Exception as e:
            logger.error(f"Error sending SMS on behalf: {e}")
            return MessageResult(
                success=False,
                error_message=str(e)
            )
    
    async def forward_notes(
        self, 
        user_id: int, 
        recipient_name: str, 
        note_query: str = "latest"
    ) -> MessageResult:
        """Forward notes to a contact"""
        try:
            logger.info(f"User {user_id} requesting to forward notes to {recipient_name}")
            
            # Find contact
            contact = await self._find_contact_by_name(user_id, recipient_name)
            
            if not contact:
                return MessageResult(
                    success=False,
                    error_message=f"Contact '{recipient_name}' not found"
                )
            
            # Get notes based on query
            notes = await self._get_notes_for_forwarding(user_id, note_query)
            
            if not notes:
                return MessageResult(
                    success=False,
                    error_message="No notes found to forward"
                )
            
            # Format notes for forwarding
            formatted_notes = self._format_notes_for_forwarding(notes)
            
            # Send based on contact type
            if contact.contact_type == ContactType.EMAIL:
                return await self._send_notes_via_email(
                    user_id, contact, formatted_notes
                )
            elif contact.contact_type == ContactType.PHONE:
                return await self._send_notes_via_sms(
                    user_id, contact, formatted_notes
                )
            else:
                return MessageResult(
                    success=False,
                    error_message=f"Cannot forward notes to {contact.contact_type.value} contact"
                )
                
        except Exception as e:
            logger.error(f"Error forwarding notes: {e}")
            return MessageResult(
                success=False,
                error_message=str(e)
            )
    
    async def send_to_slack(
        self, 
        user_id: int, 
        channel: str, 
        message: str
    ) -> MessageResult:
        """Send message to Slack channel"""
        try:
            if not self.slack_handler:
                return MessageResult(
                    success=False,
                    error_message="Slack integration not available"
                )
            
            # Clean channel name (remove # if present)
            clean_channel = channel.lstrip('#')
            
            # Send to Slack
            result = await self.slack_handler.send_message(clean_channel, message)
            
            if result.get('success'):
                # Log the action
                await self._log_communication_action(
                    user_id, "slack_message_sent", f"#{clean_channel}", message, result.get('message_id')
                )
                
                return MessageResult(
                    success=True,
                    message_id=result.get('message_id'),
                    sent_at=datetime.utcnow(),
                    delivery_status="sent"
                )
            else:
                return MessageResult(
                    success=False,
                    error_message=result.get('error', 'Unknown Slack error')
                )
                
        except Exception as e:
            logger.error(f"Error sending to Slack: {e}")
            return MessageResult(
                success=False,
                error_message=str(e)
            )
    
    async def send_to_discord(
        self, 
        user_id: int, 
        channel: str, 
        message: str
    ) -> MessageResult:
        """Send message to Discord channel"""
        try:
            if not self.discord_handler:
                return MessageResult(
                    success=False,
                    error_message="Discord integration not available"
                )
            
            # Clean channel name (remove # if present)
            clean_channel = channel.lstrip('#')
            
            # Send to Discord
            result = await self.discord_handler.send_message(clean_channel, message)
            
            if result.get('success'):
                # Log the action
                await self._log_communication_action(
                    user_id, "discord_message_sent", f"#{clean_channel}", message, result.get('message_id')
                )
                
                return MessageResult(
                    success=True,
                    message_id=result.get('message_id'),
                    sent_at=datetime.utcnow(),
                    delivery_status="sent"
                )
            else:
                return MessageResult(
                    success=False,
                    error_message=result.get('error', 'Unknown Discord error')
                )
                
        except Exception as e:
            logger.error(f"Error sending to Discord: {e}")
            return MessageResult(
                success=False,
                error_message=str(e)
            )
    
    async def add_contact(
        self, 
        user_id: int, 
        name: str, 
        contact_type: ContactType, 
        value: str
    ) -> bool:
        """Add a new contact for the user"""
        try:
            # This would typically save to a contacts database
            # For now, we'll use a simple in-memory store
            contact = Contact(
                name=name,
                contact_type=contact_type,
                value=value,
                user_id=user_id,
                is_verified=True  # In production, you'd want verification
            )
            
            # Save contact (this would go to database)
            logger.info(f"Added contact {name} ({contact_type.value}: {value}) for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding contact: {e}")
            return False
    
    async def get_user_contacts(self, user_id: int) -> List[Contact]:
        """Get all contacts for a user"""
        try:
            # This would typically query a contacts database
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error getting user contacts: {e}")
            return []
    
    async def _find_contact_by_name(self, user_id: int, name: str) -> Optional[Contact]:
        """Find contact by name for a specific user"""
        try:
            contacts = await self.get_user_contacts(user_id)
            
            # Case-insensitive search
            for contact in contacts:
                if contact.name.lower() == name.lower():
                    return contact
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding contact: {e}")
            return None
    
    async def _get_notes_for_forwarding(self, user_id: int, query: str) -> List[Dict[str, Any]]:
        """Get notes to forward based on query"""
        try:
            if query.lower() == "latest":
                # Get most recent notes
                notes = await self.notes_service.get_user_notes(user_id)
                return notes[:5]  # Last 5 notes
            elif query.lower() == "today":
                # Get today's notes
                today = datetime.utcnow().date()
                notes = await self.notes_service.get_user_notes(user_id)
                # Filter by date (this would need date field in notes)
                return notes[:3]
            else:
                # Search notes by content
                notes = await self.notes_service.search_notes(user_id, query)
                return notes[:3]
                
        except Exception as e:
            logger.error(f"Error getting notes for forwarding: {e}")
            return []
    
    def _format_notes_for_forwarding(self, notes: List[Dict[str, Any]]) -> str:
        """Format notes for forwarding"""
        try:
            if not notes:
                return "No notes to forward."
            
            formatted = f"📝 Notes from Jarvis Phone:\n\n"
            
            for i, note in enumerate(notes, 1):
                title = note.get('title', 'Untitled')
                content = note.get('content', '')
                created_at = note.get('created_at', '')
                
                formatted += f"{i}. {title}\n"
                if content:
                    formatted += f"   {content[:100]}{'...' if len(content) > 100 else ''}\n"
                if created_at:
                    formatted += f"   Created: {created_at}\n"
                formatted += "\n"
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting notes: {e}")
            return "Error formatting notes for forwarding."
    
    async def _send_notes_via_email(
        self, 
        user_id: int, 
        contact: Contact, 
        notes_content: str
    ) -> MessageResult:
        """Send notes via email"""
        try:
            # Send email with notes
            email_result = await self.email_service.send_email(
                user_id=user_id,
                to_email=contact.value,
                subject="Notes from Jarvis Phone",
                body=notes_content
            )
            
            if email_result.get('success'):
                return MessageResult(
                    success=True,
                    message_id=email_result.get('message_id'),
                    sent_at=datetime.utcnow(),
                    delivery_status="sent"
                )
            else:
                return MessageResult(
                    success=False,
                    error_message=email_result.get('error', 'Email send failed')
                )
                
        except Exception as e:
            logger.error(f"Error sending notes via email: {e}")
            return MessageResult(
                success=False,
                error_message=str(e)
            )
    
    async def _send_notes_via_sms(
        self, 
        user_id: int, 
        contact: Contact, 
        notes_content: str
    ) -> MessageResult:
        """Send notes via SMS"""
        try:
            if not self.sms_handler:
                return MessageResult(
                    success=False,
                    error_message="SMS service not available"
                )
            
            # Truncate notes if too long for SMS
            if len(notes_content) > 1600:  # Leave room for multiple SMS
                notes_content = notes_content[:1600] + "...\n\n(Notes truncated for SMS)"
            
            # Send SMS
            message_id = await self.sms_handler.send_sms(contact.value, notes_content)
            
            return MessageResult(
                success=True,
                message_id=message_id,
                sent_at=datetime.utcnow(),
                delivery_status="sent"
            )
            
        except Exception as e:
            logger.error(f"Error sending notes via SMS: {e}")
            return MessageResult(
                success=False,
                error_message=str(e)
            )
    
    async def _log_communication_action(
        self, 
        user_id: int, 
        action_type: str, 
        recipient: str, 
        message: str, 
        message_id: Optional[str] = None
    ):
        """Log communication actions for audit purposes"""
        try:
            # This would typically save to an audit log database
            log_entry = {
                "user_id": user_id,
                "action_type": action_type,
                "recipient": recipient,
                "message_preview": message[:100] + "..." if len(message) > 100 else message,
                "message_id": message_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Communication action logged: {log_entry}")
            
        except Exception as e:
            logger.error(f"Error logging communication action: {e}")
    
    async def get_communication_summary(self, user_id: int, date: datetime.date) -> Dict[str, Any]:
        """Get summary of communication actions for a user on a specific date"""
        try:
            # This would typically query an audit log database
            # For now, return a placeholder
            return {
                "date": date.isoformat(),
                "total_actions": 0,
                "sms_sent": 0,
                "emails_sent": 0,
                "slack_messages": 0,
                "discord_messages": 0,
                "notes_forwarded": 0
            }
            
        except Exception as e:
            logger.error(f"Error getting communication summary: {e}")
            return {}

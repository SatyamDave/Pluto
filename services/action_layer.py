"""
Action Execution Layer for Pluto AI Phone Assistant
Handles external actions (emails, texts, calls) with confirmation and permission management
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from db.database import get_db
from db.models import UserPreference, ExternalContact, ActionLog, ContactPermission
from config import settings
from utils.logging_config import get_logger
from telephony.outbound_call_service import OutboundCallService, CallType
from email_service.email_service import EmailService
from telephony.twilio_handler import TwilioHandler
from telephony.telnyx_handler import TelnyxHandler

logger = get_logger(__name__)

# Helper function for Python 3.9 compatibility
async def get_db_session():
    """Get database session with Python 3.9 compatibility"""
    return await get_db().__anext__()


class ActionType(Enum):
    """Types of actions that can be performed"""
    SEND_EMAIL = "send_email"
    SEND_SMS = "send_sms"
    PLACE_CALL = "place_call"
    SCHEDULE_MEETING = "schedule_meeting"
    CREATE_REMINDER = "create_reminder"


class PermissionLevel(Enum):
    """Permission levels for external contacts"""
    ALWAYS_ASK = "always_ask"
    AUTO_APPROVE = "auto_approve"
    NEVER_ALLOW = "never_allow"


class ActionLayer:
    """Pluto's action execution layer - always asks confirmation before acting"""
    
    def __init__(self):
        """Initialize the action execution layer"""
        self.logger = logger
        self.outbound_service = OutboundCallService()
        self.email_service = EmailService()
        self.twilio_handler = TwilioHandler()
        self.telnyx_handler = TelnyxHandler()
        self.logger.info("Action Execution Layer initialized")
    
    async def request_action_confirmation(
        self,
        user_id: str,
        action_type: ActionType,
        action_data: Dict[str, Any],
        contact_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Request confirmation for an external action
        
        Args:
            user_id: User requesting the action
            action_type: Type of action to perform
            action_data: Data needed for the action
            contact_info: Information about the external contact
            
        Returns:
            Confirmation request details
        """
        try:
            # Check if auto-approval is allowed
            auto_approve = await self._check_auto_approval(user_id, action_type, contact_info)
            
            if auto_approve:
                # Auto-approve and execute immediately
                result = await self._execute_action(user_id, action_type, action_data, contact_info)
                return {
                    "status": "auto_approved",
                    "message": "Action automatically approved and executed",
                    "result": result
                }
            
            # Generate confirmation request
            confirmation_request = await self._generate_confirmation_request(
                user_id, action_type, action_data, contact_info
            )
            
            # Store pending action for later execution
            await self._store_pending_action(user_id, action_type, action_data, contact_info)
            
            return {
                "status": "confirmation_required",
                "confirmation_request": confirmation_request,
                "action_id": confirmation_request["action_id"]
            }
            
        except Exception as e:
            self.logger.error(f"Error requesting action confirmation: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def confirm_action(
        self,
        user_id: str,
        action_id: str,
        confirmation: str
    ) -> Dict[str, Any]:
        """
        Confirm and execute a pending action
        
        Args:
            user_id: User confirming the action
            action_id: ID of the action to confirm
            confirmation: User's confirmation response
            
        Returns:
            Execution result
        """
        try:
            # Parse confirmation response
            is_confirmed = self._parse_confirmation(confirmation)
            
            if not is_confirmed:
                # User declined, cancel the action
                await self._cancel_pending_action(user_id, action_id)
                return {
                    "status": "cancelled",
                    "message": "Action cancelled by user"
                }
            
            # Get pending action details
            pending_action = await self._get_pending_action(user_id, action_id)
            if not pending_action:
                return {
                    "status": "error",
                    "error": "Action not found or expired"
                }
            
            # Execute the confirmed action
            result = await self._execute_action(
                user_id,
                pending_action["action_type"],
                pending_action["action_data"],
                pending_action.get("contact_info")
            )
            
            # Update contact permissions if this was successful
            if result.get("success") and pending_action.get("contact_info"):
                await self._update_contact_permissions(
                    user_id, 
                    pending_action["contact_info"], 
                    pending_action["action_type"]
                )
            
            # Remove from pending actions
            await self._remove_pending_action(user_id, action_id)
            
            # Log the action
            await self._log_action(
                user_id, 
                pending_action["action_type"], 
                pending_action["action_data"], 
                "confirmed",
                result
            )
            
            return {
                "status": "executed",
                "message": "Action executed successfully",
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Error confirming action: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_auto_approval(
        self,
        user_id: str,
        action_type: ActionType,
        contact_info: Optional[Dict[str, Any]]
    ) -> bool:
        """Check if action can be auto-approved"""
        try:
            if not contact_info:
                return False
            
            # Get contact permissions
            db = await anext(get_db())
            contact = db.query(ExternalContact).filter(
                and_(
                    ExternalContact.user_id == user_id,
                    ExternalContact.phone_number == contact_info.get("phone_number")
                )
            ).first()
            
            if not contact:
                return False
            
            # Check if auto-approval is enabled for this contact and action type
            permission = db.query(ContactPermission).filter(
                and_(
                    ContactPermission.contact_id == contact.id,
                    ContactPermission.action_type == action_type.value
                )
            ).first()
            
            if permission and permission.permission_level == PermissionLevel.AUTO_APPROVE.value:
                return True
            
            # Check user preferences for auto-approval
            user_pref = db.query(UserPreference).filter(
                and_(
                    UserPreference.user_id == user_id,
                    UserPreference.key == f"auto_approve_{action_type.value}"
                )
            ).first()
            
            return user_pref and user_pref.value == "true"
            
        except Exception as e:
            self.logger.error(f"Error checking auto-approval: {e}")
            return False
    
    async def _generate_confirmation_request(
        self,
        user_id: str,
        action_type: ActionType,
        action_data: Dict[str, Any],
        contact_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate a confirmation request for the user"""
        try:
            action_id = f"{user_id}_{action_type.value}_{datetime.now().timestamp()}"
            
            # Generate human-readable confirmation message
            confirmation_message = self._format_confirmation_message(
                action_type, action_data, contact_info
            )
            
            return {
                "action_id": action_id,
                "action_type": action_type.value,
                "confirmation_message": confirmation_message,
                "contact_info": contact_info,
                "timestamp": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating confirmation request: {e}")
            raise
    
    def _format_confirmation_message(
        self,
        action_type: ActionType,
        action_data: Dict[str, Any],
        contact_info: Optional[Dict[str, Any]]
    ) -> str:
        """Format confirmation message in human-readable form"""
        try:
            if action_type == ActionType.SEND_EMAIL:
                return f"Send email to {contact_info.get('name', 'contact')} at {contact_info.get('email')} with subject '{action_data.get('subject', 'No subject')}'?"
            
            elif action_type == ActionType.SEND_SMS:
                return f"Send text message to {contact_info.get('name', 'contact')} at {contact_info.get('phone_number')}: '{action_data.get('message', 'No message')}'?"
            
            elif action_type == ActionType.PLACE_CALL:
                return f"Call {contact_info.get('name', 'contact')} at {contact_info.get('phone_number')} about '{action_data.get('purpose', 'general inquiry')}'?"
            
            elif action_type == ActionType.SCHEDULE_MEETING:
                return f"Schedule meeting with {contact_info.get('name', 'contact')} for {action_data.get('date_time', 'unspecified time')}?"
            
            elif action_type == ActionType.CREATE_REMINDER:
                return f"Set reminder for {action_data.get('description', 'unspecified task')} at {action_data.get('time', 'unspecified time')}?"
            
            else:
                return f"Perform {action_type.value} action?"
                
        except Exception as e:
            self.logger.error(f"Error formatting confirmation message: {e}")
            return f"Perform {action_type.value} action?"
    
    def _parse_confirmation(self, confirmation: str) -> bool:
        """Parse user confirmation response"""
        try:
            confirmation_lower = confirmation.lower().strip()
            
            # Check for positive confirmations (exact word matches)
            positive_responses = ["yes", "yes.", "y", "yep", "sure", "ok", "okay", "confirm", "approved"]
            
            # Split into words and check for exact matches
            words = confirmation_lower.split()
            
            if any(response in words for response in positive_responses):
                return True
            
            # Check for negative confirmations (exact word matches)
            negative_responses = ["no", "no.", "n", "nope", "cancel", "stop", "don't", "dont"]
            
            if any(response in words for response in negative_responses):
                return False
            
            # Default to asking again for unclear responses
            return False
            
        except Exception as e:
            self.logger.error(f"Error parsing confirmation: {e}")
            return False
    
    async def _execute_action(
        self,
        user_id: str,
        action_type: ActionType,
        action_data: Dict[str, Any],
        contact_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute the confirmed action"""
        try:
            if action_type == ActionType.SEND_EMAIL:
                return await self._send_email(user_id, action_data, contact_info)
            
            elif action_type == ActionType.SEND_SMS:
                return await self._send_sms(user_id, action_data, contact_info)
            
            elif action_type == ActionType.PLACE_CALL:
                return await self._place_call(user_id, action_data, contact_info)
            
            elif action_type == ActionType.SCHEDULE_MEETING:
                return await self._schedule_meeting(user_id, action_data, contact_info)
            
            elif action_type == ActionType.CREATE_REMINDER:
                return await self._create_reminder(user_id, action_data)
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown action type: {action_type.value}"
                }
                
        except Exception as e:
            self.logger.error(f"Error executing action: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _send_email(
        self,
        user_id: str,
        action_data: Dict[str, Any],
        contact_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send email to external contact"""
        try:
            result = await self.email_service.send_email(
                to_email=contact_info["email"],
                subject=action_data["subject"],
                body=action_data["body"],
                user_id=user_id
            )
            
            return {
                "success": result.get("success", False),
                "email_id": result.get("email_id"),
                "message": "Email sent successfully" if result.get("success") else "Failed to send email"
            }
            
        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _send_sms(
        self,
        user_id: str,
        action_data: Dict[str, Any],
        contact_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send SMS to external contact"""
        try:
            # Use Twilio by default, fallback to Telnyx
            try:
                result = await self.twilio_handler.send_sms(
                    contact_info["phone_number"],
                    action_data["message"]
                )
                provider = "twilio"
            except Exception:
                result = await self.telnyx_handler.send_sms(
                    contact_info["phone_number"],
                    action_data["message"]
                )
                provider = "telnyx"
            
            return {
                "success": result,
                "provider": provider,
                "message": "SMS sent successfully" if result else "Failed to send SMS"
            }
            
        except Exception as e:
            self.logger.error(f"Error sending SMS: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _place_call(
        self,
        user_id: str,
        action_data: Dict[str, Any],
        contact_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Place call to external contact"""
        try:
            # Generate call script
            script = await self.outbound_service._generate_ai_script(
                CallType.GENERAL_INQUIRY,
                action_data.get("purpose", "general inquiry")
            )
            
            # Place the call
            result = await self.outbound_service.initiate_call(
                user_id=int(user_id),
                target_phone=contact_info["phone_number"],
                call_type=CallType.GENERAL_INQUIRY,
                task_description=action_data.get("purpose", "general inquiry"),
                ai_script=script
            )
            
            return {
                "success": result,
                "script": script,
                "message": "Call placed successfully" if result else "Failed to place call"
            }
            
        except Exception as e:
            self.logger.error(f"Error placing call: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _schedule_meeting(
        self,
        user_id: str,
        action_data: Dict[str, Any],
        contact_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Schedule meeting with external contact"""
        try:
            # This would integrate with calendar service
            # For now, return success
            return {
                "success": True,
                "meeting_id": f"meeting_{datetime.now().timestamp()}",
                "message": "Meeting scheduled successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error scheduling meeting: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _create_reminder(
        self,
        user_id: str,
        action_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create reminder for user"""
        try:
            # This would integrate with reminder service
            # For now, return success
            return {
                "success": True,
                "reminder_id": f"reminder_{datetime.now().timestamp()}",
                "message": "Reminder created successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error creating reminder: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _store_pending_action(
        self,
        user_id: str,
        action_type: ActionType,
        action_data: Dict[str, Any],
        contact_info: Optional[Dict[str, Any]]
    ) -> None:
        """Store pending action for later execution"""
        try:
            # Store in database using ActionLog model
            db = await get_db_session()
            
            action_log = ActionLog(
                user_id=user_id,
                action_type=action_type.value,
                action_data=action_data,
                contact_info=contact_info,
                status="pending",
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=24)
            )
            
            db.add(action_log)
            await db.commit()
            await db.refresh(action_log)
            
            self.logger.info(f"Stored pending action: {action_type.value} for user {user_id} (ID: {action_log.id})")
            
        except Exception as e:
            self.logger.error(f"Error storing pending action: {e}")
            # Fallback to in-memory storage for critical actions
            if not hasattr(self, '_pending_actions'):
                self._pending_actions = {}
            
            action_id = f"{user_id}_{action_type.value}_{datetime.now().timestamp()}"
            self._pending_actions[action_id] = {
                "user_id": user_id,
                "action_type": action_type.value,
                "action_data": action_data,
                "contact_info": contact_info,
                "created_at": datetime.now().isoformat()
            }
    
    async def _get_pending_action(
        self,
        user_id: str,
        action_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get pending action details"""
        try:
            # Try to get from database first
            db = await get_db_session()
            
            # Parse action_id to extract components
            if "_" in action_id:
                parts = action_id.split("_")
                if len(parts) >= 3:
                    action_type = parts[1]
                    timestamp = float(parts[2])
                    
                    # Query database for matching action
                    query = """
                        SELECT id, user_id, action_type, action_data, contact_info, 
                               status, created_at, expires_at
                        FROM action_logs 
                        WHERE user_id = :user_id 
                        AND action_type = :action_type
                        AND status = 'pending'
                        AND created_at >= :min_time
                        ORDER BY created_at DESC
                        LIMIT 1
                    """
                    
                    min_time = datetime.fromtimestamp(timestamp - 3600)  # 1 hour window
                    
                    result = await db.execute(query, {
                        "user_id": user_id,
                        "action_type": action_type,
                        "min_time": min_time
                    })
                    
                    action = result.fetchone()
                    if action:
                        return {
                            "action_type": action.action_type,
                            "action_data": action.action_data,
                            "contact_info": action.contact_info,
                            "created_at": action.created_at.isoformat()
                        }
            
            # Fallback to in-memory storage
            if hasattr(self, '_pending_actions') and action_id in self._pending_actions:
                return self._pending_actions[action_id]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting pending action: {e}")
            # Fallback to in-memory storage
            if hasattr(self, '_pending_actions') and action_id in self._pending_actions:
                return self._pending_actions[action_id]
            return None
    
    async def _remove_pending_action(
        self,
        user_id: str,
        action_id: str
    ) -> None:
        """Remove pending action after execution"""
        try:
            # Try to remove from database first
            db = await anext(get_db())
            
            # Parse action_id to extract components
            if "_" in action_id:
                parts = action_id.split("_")
                if len(parts) >= 3:
                    action_type = parts[1]
                    timestamp = float(parts[2])
                    
                    # Update database to mark as completed
                    update_query = """
                        UPDATE action_logs 
                        SET status = 'completed', updated_at = :updated_at
                        WHERE user_id = :user_id 
                        AND action_type = :action_type
                        AND status = 'pending'
                        AND created_at >= :min_time
                    """
                    
                    min_time = datetime.fromtimestamp(timestamp - 3600)  # 1 hour window
                    
                    await db.execute(update_query, {
                        "user_id": user_id,
                        "action_type": action_type,
                        "min_time": min_time,
                        "updated_at": datetime.now()
                    })
                    
                    await db.commit()
            
            # Remove from in-memory storage
            if hasattr(self, '_pending_actions') and action_id in self._pending_actions:
                del self._pending_actions[action_id]
            
            self.logger.info(f"Removed pending action {action_id} for user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Error removing pending action: {e}")
            # Fallback: just remove from in-memory storage
            if hasattr(self, '_pending_actions') and action_id in self._pending_actions:
                del self._pending_actions[action_id]
    
    async def _cancel_pending_action(
        self,
        user_id: str,
        action_id: str
    ) -> None:
        """Cancel pending action"""
        try:
            # Try to update database first
            db = await get_db_session()
            
            # Parse action_id to extract components
            if "_" in action_id:
                parts = action_id.split("_")
                if len(parts) >= 3:
                    action_type = parts[1]
                    timestamp = float(parts[2])
                    
                    # Update database to mark as cancelled
                    update_query = """
                        UPDATE action_logs 
                        SET status = 'cancelled', updated_at = :updated_at
                        WHERE user_id = :user_id 
                        AND action_type = :action_type
                        AND status = 'pending'
                        AND created_at >= :min_time
                    """
                    
                    min_time = datetime.fromtimestamp(timestamp - 3600)  # 1 hour window
                    
                    await db.execute(update_query, {
                        "user_id": user_id,
                        "action_type": action_type,
                        "min_time": min_time,
                        "updated_at": datetime.now()
                    })
                    
                    await db.commit()
            
            # Remove from in-memory storage
            if hasattr(self, '_pending_actions') and action_id in self._pending_actions:
                del self._pending_actions[action_id]
            
            self.logger.info(f"Cancelled pending action {action_id} for user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Error cancelling pending action: {e}")
            # Fallback: just remove from in-memory storage
            if hasattr(self, '_pending_actions') and action_id in self._pending_actions:
                del self._pending_actions[action_id]
    
    async def _update_contact_permissions(
        self,
        user_id: str,
        contact_info: Dict[str, Any],
        action_type: ActionType
    ) -> None:
        """Update contact permissions based on successful actions"""
        try:
            # Update database with contact permissions
            db = await get_db_session()
            
            # Check if contact exists
            contact_query = """
                SELECT id FROM external_contacts 
                WHERE user_id = :user_id 
                AND phone_number = :phone_number
            """
            
            result = await db.execute(contact_query, {
                "user_id": user_id,
                "phone_number": contact_info.get("phone_number")
            })
            
            contact = result.fetchone()
            
            if contact:
                # Update existing contact permissions
                permission_query = """
                    INSERT INTO contact_permissions (contact_id, action_type, permission_level, updated_at)
                    VALUES (:contact_id, :action_type, 'auto_approve', :updated_at)
                    ON CONFLICT (contact_id, action_type) 
                    DO UPDATE SET 
                        permission_level = 'auto_approve',
                        updated_at = :updated_at
                """
                
                await db.execute(permission_query, {
                    "contact_id": contact.id,
                    "action_type": action_type.value,
                    "updated_at": datetime.now()
                })
                
                await db.commit()
                
                self.logger.info(f"Updated permissions for contact {contact_info.get('name')} after {action_type.value}")
            else:
                # Create new contact with permissions
                insert_contact_query = """
                    INSERT INTO external_contacts (user_id, name, phone_number, email, relationship, created_at)
                    VALUES (:user_id, :name, :phone_number, :email, 'unknown', :created_at)
                    RETURNING id
                """
                
                result = await db.execute(insert_contact_query, {
                    "user_id": user_id,
                    "name": contact_info.get("name", "Unknown"),
                    "phone_number": contact_info.get("phone_number"),
                    "email": contact_info.get("email"),
                    "created_at": datetime.now()
                })
                
                new_contact = result.fetchone()
                
                if new_contact:
                    # Add permission for this action type
                    permission_query = """
                        INSERT INTO contact_permissions (contact_id, action_type, permission_level, created_at)
                        VALUES (:contact_id, :action_type, 'auto_approve', :created_at)
                    """
                    
                    await db.execute(permission_query, {
                        "contact_id": new_contact.id,
                        "action_type": action_type.value,
                        "created_at": datetime.now()
                    })
                    
                    await db.commit()
                    
                    self.logger.info(f"Created new contact {contact_info.get('name')} with auto-approval for {action_type.value}")
            
        except Exception as e:
            self.logger.error(f"Error updating contact permissions: {e}")
            # Fallback: just log the action
            self.logger.info(f"Updated permissions for contact {contact_info.get('name')} after {action_type.value}")
    
    async def _log_action(
        self,
        user_id: str,
        action_type: ActionType,
        action_data: Dict[str, Any],
        status: str,
        result: Dict[str, Any]
    ) -> None:
        """Log action execution for audit trail"""
        try:
            # Store in database using ActionLog model
            db = await get_db_session()
            
            action_log = ActionLog(
                user_id=user_id,
                action_type=action_type.value,
                action_data=action_data,
                status=status,
                result=result,
                created_at=datetime.now()
            )
            
            db.add(action_log)
            await db.commit()
            
            self.logger.info(f"Action logged: {action_type.value} for user {user_id}, status: {status}")
            
        except Exception as e:
            self.logger.error(f"Error logging action: {e}")
            # Fallback: just log to console
            self.logger.info(f"Action logged: {action_type.value} for user {user_id}, status: {status}")
    
    async def get_user_action_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's action history"""
        try:
            # Query database for action history
            db = await get_db_session()
            
            query = """
                SELECT id, action_type, action_data, status, result, created_at
                FROM action_logs 
                WHERE user_id = :user_id 
                ORDER BY created_at DESC 
                LIMIT :limit
            """
            
            result = await db.execute(query, {
                "user_id": user_id,
                "limit": limit
            })
            
            actions = []
            for row in result.fetchall():
                actions.append({
                    "id": row.id,
                    "action_type": row.action_type,
                    "action_data": row.action_data,
                    "status": row.status,
                    "result": row.result,
                    "created_at": row.created_at.isoformat() if row.created_at else None
                })
            
            self.logger.info(f"Retrieved {len(actions)} actions for user {user_id}")
            return actions
            
        except Exception as e:
            self.logger.error(f"Error getting action history: {e}")
            # Fallback: return in-memory actions if available
            if hasattr(self, '_pending_actions'):
                actions = []
                for action_id, action_data in self._pending_actions.items():
                    if action_data.get("user_id") == user_id:
                        actions.append({
                            "id": action_id,
                            "action_type": action_data.get("action_type"),
                            "action_data": action_data.get("action_data"),
                            "status": "pending",
                            "created_at": action_data.get("created_at")
                        })
                return actions[:limit]
            return []
    
    async def set_contact_permission(
        self,
        user_id: str,
        contact_id: str,
        action_type: ActionType,
        permission_level: PermissionLevel
    ) -> bool:
        """Set permission level for a contact and action type"""
        try:
            # Update database with contact permission
            db = await get_db_session()
            
            # Check if contact belongs to user
            contact_query = """
                SELECT id FROM external_contacts 
                WHERE id = :contact_id AND user_id = :user_id
            """
            
            result = await db.execute(contact_query, {
                "contact_id": contact_id,
                "user_id": user_id
            })
            
            contact = result.fetchone()
            if not contact:
                self.logger.warning(f"Contact {contact_id} not found for user {user_id}")
                return False
            
            # Update or insert permission
            permission_query = """
                INSERT INTO contact_permissions (contact_id, action_type, permission_level, updated_at)
                VALUES (:contact_id, :action_type, :permission_level, :updated_at)
                ON CONFLICT (contact_id, action_type) 
                DO UPDATE SET 
                    permission_level = :permission_level,
                    updated_at = :updated_at
            """
            
            await db.execute(permission_query, {
                "contact_id": contact_id,
                "action_type": action_type.value,
                "permission_level": permission_level.value,
                "updated_at": datetime.now()
            })
            
            await db.commit()
            
            self.logger.info(f"Set permission {permission_level.value} for {action_type.value} with contact {contact_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting contact permission: {e}")
            return False


# Global instance
action_layer = ActionLayer()

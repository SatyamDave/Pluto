"""
Email service for Jarvis Phone AI Assistant
Integrates with Gmail API for email management
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from db.database import get_db
from db.models import EmailMessage, User
from config import settings

logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]


class EmailService:
    """Service for managing Gmail integration"""
    
    def __init__(self):
        self.service = None
        self.creds = None
    
    async def authenticate_user(self, user_id: int) -> bool:
        """Authenticate user with Gmail API"""
        try:
            db = await get_db()
            
            # Get user
            user_query = "SELECT * FROM users WHERE id = :user_id"
            result = await db.execute(user_query, {"user_id": user_id})
            user = result.fetchone()
            
            if not user:
                logger.error(f"User {user_id} not found")
                return False
            
            # Check if user has valid credentials
            if hasattr(user, 'gmail_credentials') and user.gmail_credentials:
                # Refresh credentials if needed
                self.creds = Credentials.from_authorized_user_info(
                    user.gmail_credentials, SCOPES
                )
                
                if self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                    
                    # Update stored credentials
                    # Note: In production, you'd want to store credentials securely
                    await self._update_user_credentials(user_id, self.creds.to_json())
                
                self.service = build('gmail', 'v1', credentials=self.creds)
                return True
            
            else:
                logger.info(f"User {user_id} needs Gmail authentication")
                return False
                
        except Exception as e:
            logger.error(f"Error authenticating user {user_id}: {e}")
            return False
    
    async def get_unread_emails(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get unread emails for a user"""
        try:
            # Authenticate user
            if not await self.authenticate_user(user_id):
                return []
            
            # Get unread emails from Gmail
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['UNREAD'],
                maxResults=limit
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                email_data = await self._get_email_details(message['id'])
                if email_data:
                    emails.append(email_data)
                    
                    # Store in database
                    await self._store_email(user_id, email_data)
            
            logger.info(f"Retrieved {len(emails)} unread emails for user {user_id}")
            return emails
            
        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting unread emails: {e}")
            return []
    
    async def get_email_summary(self, user_id: int) -> Dict[str, Any]:
        """Get a summary of user's email activity"""
        try:
            # Get recent emails (both read and unread)
            if not await self.authenticate_user(user_id):
                return {"error": "Authentication required"}
            
            # Get recent messages
            results = self.service.users().messages().list(
                userId='me',
                maxResults=20
            ).execute()
            
            messages = results.get('messages', [])
            
            # Analyze email patterns
            summary = {
                "total_recent": len(messages),
                "unread_count": 0,
                "senders": {},
                "subjects": [],
                "last_email_time": None
            }
            
            for message in messages[:10]:  # Analyze first 10
                email_data = await self._get_email_details(message['id'])
                if email_data:
                    # Count unread
                    if 'UNREAD' in email_data.get('labels', []):
                        summary["unread_count"] += 1
                    
                    # Track senders
                    sender = email_data.get('sender', 'Unknown')
                    summary["senders"][sender] = summary["senders"].get(sender, 0) + 1
                    
                    # Track subjects
                    subject = email_data.get('subject', 'No Subject')
                    summary["subjects"].append(subject)
                    
                    # Track last email time
                    if not summary["last_email_time"]:
                        summary["last_email_time"] = email_data.get('received_at')
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting email summary: {e}")
            return {"error": str(e)}
    
    async def _get_email_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific email"""
        try:
            message = self.service.users().messages().get(
                userId='me', 
                id=message_id,
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date', 'To']
            ).execute()
            
            headers = message['payload']['headers']
            
            # Extract email details
            email_data = {
                'message_id': message_id,
                'sender': self._extract_header(headers, 'From'),
                'subject': self._extract_header(headers, 'Subject'),
                'recipients': self._extract_header(headers, 'To'),
                'received_at': self._parse_date(self._extract_header(headers, 'Date')),
                'labels': message.get('labelIds', []),
                'snippet': message.get('snippet', '')
            }
            
            return email_data
            
        except Exception as e:
            logger.error(f"Error getting email details: {e}")
            return None
    
    def _extract_header(self, headers: List[Dict[str, str]], name: str) -> str:
        """Extract header value by name"""
        for header in headers:
            if header['name'] == name:
                return header['value']
        return ''
    
    def _parse_date(self, date_string: str) -> Optional[datetime]:
        """Parse email date string"""
        try:
            # Handle various date formats
            import email.utils
            parsed_date = email.utils.parsedate_to_datetime(date_string)
            return parsed_date
        except Exception as e:
            logger.warning(f"Could not parse date '{date_string}': {e}")
            return None
    
    async def _store_email(self, user_id: int, email_data: Dict[str, Any]):
        """Store email in database"""
        try:
            db = await get_db()
            
            # Check if email already exists
            existing_query = "SELECT id FROM email_messages WHERE message_id = :message_id AND user_id = :user_id"
            result = await db.execute(existing_query, {
                "message_id": email_data['message_id'],
                "user_id": user_id
            })
            
            if result.fetchone():
                return  # Email already stored
            
            # Create new email record
            email_message = EmailMessage(
                user_id=user_id,
                message_id=email_data['message_id'],
                subject=email_data['subject'],
                sender=email_data['sender'],
                recipients=[email_data['recipients']] if email_data['recipients'] else [],
                content=email_data.get('snippet', ''),
                is_read='UNREAD' not in email_data.get('labels', []),
                email_source='gmail',
                received_at=email_data['received_at'] or datetime.utcnow()
            )
            
            db.add(email_message)
            await db.commit()
            
            logger.debug(f"Stored email {email_data['message_id']} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing email: {e}")
    
    async def _update_user_credentials(self, user_id: int, credentials_json: str):
        """Update user's Gmail credentials"""
        try:
            db = await get_db()
            
            # In production, you'd want to encrypt these credentials
            update_query = "UPDATE users SET gmail_credentials = :creds WHERE id = :user_id"
            await db.execute(update_query, {
                "creds": credentials_json,
                "user_id": user_id
            })
            
            await db.commit()
            logger.info(f"Updated Gmail credentials for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating user credentials: {e}")
    
    async def mark_email_read(self, user_id: int, message_id: str) -> bool:
        """Mark an email as read"""
        try:
            if not await self.authenticate_user(user_id):
                return False
            
            # Update Gmail labels
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            # Update database
            db = await get_db()
            update_query = "UPDATE email_messages SET is_read = true WHERE message_id = :message_id AND user_id = :user_id"
            await db.execute(update_query, {
                "message_id": message_id,
                "user_id": user_id
            })
            
            await db.commit()
            
            logger.info(f"Marked email {message_id} as read for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking email as read: {e}")
            return False
    
    async def get_email_analytics(self, user_id: int, days: int = 7) -> Dict[str, Any]:
        """Get email analytics for a user"""
        try:
            db = await get_db()
            
            # Get email statistics from database
            since_date = datetime.utcnow() - timedelta(days=days)
            
            stats_query = """
                SELECT 
                    COUNT(*) as total_emails,
                    COUNT(CASE WHEN is_read = false THEN 1 END) as unread_emails,
                    COUNT(CASE WHEN received_at >= :since_date THEN 1 END) as recent_emails
                FROM email_messages 
                WHERE user_id = :user_id
            """
            
            result = await db.execute(stats_query, {
                "user_id": user_id,
                "since_date": since_date
            })
            
            stats = result.fetchone()
            
            # Get top senders
            senders_query = """
                SELECT sender, COUNT(*) as count
                FROM email_messages 
                WHERE user_id = :user_id AND received_at >= :since_date
                GROUP BY sender 
                ORDER BY count DESC 
                LIMIT 5
            """
            
            senders_result = await db.execute(senders_query, {
                "user_id": user_id,
                "since_date": since_date
            })
            
            top_senders = [{"sender": row.sender, "count": row.count} for row in senders_result.fetchall()]
            
            return {
                "total_emails": stats.total_emails,
                "unread_emails": stats.unread_emails,
                "recent_emails": stats.recent_emails,
                "top_senders": top_senders,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting email analytics: {e}")
            return {"error": str(e)}
    
    async def draft_email(
        self, 
        user_id: int, 
        to_email: str, 
        subject: str, 
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Draft an email for the user"""
        try:
            if not await self.authenticate_user(user_id):
                return {"error": "Authentication required"}
            
            # Create email draft
            message = self._create_email_message(to_email, subject, body, cc, bcc)
            
            # Create draft in Gmail
            draft = self.service.users().drafts().create(
                userId='me',
                body={'message': message}
            ).execute()
            
            # Store draft in database
            await self._store_draft(user_id, draft, to_email, subject, body)
            
            logger.info(f"Created email draft for user {user_id} to {to_email}")
            
            return {
                "success": True,
                "draft_id": draft['id'],
                "message": "Email draft created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error drafting email: {e}")
            return {"error": str(e)}
    
    async def send_email(
        self, 
        user_id: int, 
        to_email: str, 
        subject: str, 
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send an email immediately"""
        try:
            if not await self.authenticate_user(user_id):
                return {"error": "Authentication required"}
            
            # Create email message
            message = self._create_email_message(to_email, subject, body, cc, bcc)
            
            # Send email via Gmail
            sent_message = self.service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            # Store sent email in database
            await self._store_sent_email(user_id, sent_message, to_email, subject, body)
            
            # Log the action for audit
            await self._log_email_action(user_id, "email_sent", to_email, subject)
            
            logger.info(f"Sent email for user {user_id} to {to_email}")
            
            return {
                "success": True,
                "message_id": sent_message['id'],
                "message": "Email sent successfully"
            }
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {"error": str(e)}
    
    async def send_email_reply(
        self, 
        user_id: int, 
        original_message_id: str, 
        reply_body: str
    ) -> Dict[str, Any]:
        """Send a reply to an existing email"""
        try:
            if not await self.authenticate_user(user_id):
                return {"error": "Authentication required"}
            
            # Get original message details
            original_message = self.service.users().messages().get(
                userId='me', 
                id=original_message_id,
                format='metadata',
                metadataHeaders=['From', 'Subject', 'To']
            ).execute()
            
            headers = original_message['payload']['headers']
            original_sender = self._extract_header(headers, 'From')
            original_subject = self._extract_header(headers, 'Subject')
            
            # Create reply subject
            if not original_subject.startswith('Re:'):
                reply_subject = f"Re: {original_subject}"
            else:
                reply_subject = original_subject
            
            # Send reply
            result = await self.send_email(
                user_id=user_id,
                to_email=original_sender,
                subject=reply_subject,
                body=reply_body
            )
            
            if result.get('success'):
                # Mark original as replied
                await self._mark_as_replied(user_id, original_message_id)
                
                return {
                    "success": True,
                    "message": "Reply sent successfully",
                    "original_message_id": original_message_id
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error sending email reply: {e}")
            return {"error": str(e)}
    
    async def auto_reply_to_email(
        self, 
        user_id: int, 
        message_id: str, 
        auto_reply_text: str = "Got it, thanks!"
    ) -> Dict[str, Any]:
        """Automatically reply to an email with a predefined message"""
        try:
            logger.info(f"Auto-replying to email {message_id} for user {user_id}")
            
            result = await self.send_email_reply(
                user_id=user_id,
                original_message_id=message_id,
                reply_body=auto_reply_text
            )
            
            if result.get('success'):
                # Log auto-reply action
                await self._log_email_action(user_id, "auto_reply_sent", "auto", auto_reply_text)
                
                return {
                    "success": True,
                    "message": "Auto-reply sent successfully",
                    "auto_reply_text": auto_reply_text
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error sending auto-reply: {e}")
            return {"error": str(e)}
    
    async def get_emails_in_timerange(
        self, 
        user_id: int, 
        start_date: datetime.date, 
        end_date: datetime.date
    ) -> List[Dict[str, Any]]:
        """Get emails within a specific time range"""
        try:
            if not await self.authenticate_user(user_id):
                return []
            
            # Convert dates to datetime
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            # Query Gmail for messages in date range
            query = f"after:{start_datetime.strftime('%Y/%m/%d')} before:{end_datetime.strftime('%Y/%m/%d')}"
            
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=100
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages[:50]:  # Limit to 50 emails
                email_data = await self._get_email_details(message['id'])
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error getting emails in timerange: {e}")
            return []
    
    async def compose_email(
        self,
        user_id: int,
        to: str,
        subject: str,
        body: str,
        reply_to_message_id: str = None
    ) -> Dict[str, Any]:
        """Compose an email (creates draft)"""
        try:
            if not await self.authenticate_user(user_id):
                return {"error": "Authentication required"}
            
            # Create email draft
            message = self._create_email_message(to, subject, body)
            
            # Create draft in Gmail
            draft = self.service.users().drafts().create(
                userId='me',
                body={'message': message}
            ).execute()
            
            # Store draft in database
            await self._store_draft(user_id, draft, to, subject, body)
            
            logger.info(f"Created email draft for user {user_id} to {to}")
            
            return {
                "success": True,
                "draft_id": draft['id'],
                "message": "Email draft created successfully",
                "to": to,
                "subject": subject,
                "body_preview": body[:100] + "..." if len(body) > 100 else body
            }
            
        except Exception as e:
            logger.error(f"Error composing email: {e}")
            return {"error": str(e)}
    
    async def send_draft(
        self,
        user_id: int,
        draft_id: str
    ) -> Dict[str, Any]:
        """Send a composed email draft"""
        try:
            if not await self.authenticate_user(user_id):
                return {"error": "Authentication required"}
            
            # Send the draft
            sent_message = self.service.users().drafts().send(
                userId='me',
                body={'id': draft_id}
            ).execute()
            
            # Store sent email in database
            await self._store_sent_email(user_id, sent_message, sent_message.get('to', ''), sent_message.get('subject', ''), '')
            
            # Log the action for audit
            await self._log_email_action(user_id, "email_sent", sent_message.get('to', ''), sent_message.get('subject', ''))
            
            logger.info(f"Sent email draft {draft_id} for user {user_id}")
            
            return {
                "success": True,
                "message_id": sent_message['id'],
                "message": "Email sent successfully"
            }
            
        except Exception as e:
            logger.error(f"Error sending email draft: {e}")
            return {"error": str(e)}
    
    async def cancel_draft(
        self,
        user_id: int,
        draft_id: str
    ) -> bool:
        """Cancel/delete an email draft"""
        try:
            if not await self.authenticate_user(user_id):
                return False
            
            # Delete the draft
            self.service.users().drafts().delete(
                userId='me',
                id=draft_id
            ).execute()
            
            logger.info(f"Cancelled email draft {draft_id} for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling email draft: {e}")
            return False
    
    def _create_email_message(
        self, 
        to_email: str, 
        subject: str, 
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create Gmail API message format"""
        import base64
        import email.mime.text
        import email.mime.multipart
        
        # Create MIME message
        msg = email.mime.multipart.MIMEMultipart()
        msg['to'] = to_email
        msg['subject'] = subject
        
        if cc:
            msg['cc'] = ', '.join(cc)
        if bcc:
            msg['bcc'] = ', '.join(bcc)
        
        # Add body
        text_part = email.mime.text.MIMEText(body, 'plain')
        msg.attach(text_part)
        
        # Encode for Gmail API
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
        
        return {'raw': raw_message}
    
    async def _store_draft(
        self, 
        user_id: int, 
        draft: Dict[str, Any], 
        to_email: str, 
        subject: str, 
        body: str
    ):
        """Store email draft in database"""
        try:
            db = await get_db()
            
            # This would store draft information
            # For now, just log it
            logger.debug(f"Storing draft {draft['id']} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing draft: {e}")
    
    async def _store_sent_email(
        self, 
        user_id: int, 
        sent_message: Dict[str, Any], 
        to_email: str, 
        subject: str, 
        body: str
    ):
        """Store sent email in database"""
        try:
            db = await get_db()
            
            # This would store sent email information
            # For now, just log it
            logger.debug(f"Storing sent email {sent_message['id']} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing sent email: {e}")
    
    async def _mark_as_replied(self, user_id: int, message_id: str):
        """Mark email as replied in database"""
        try:
            db = await get_db()
            
            # This would update the email status
            # For now, just log it
            logger.debug(f"Marking email {message_id} as replied for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error marking email as replied: {e}")
    
    async def _log_email_action(
        self, 
        user_id: int, 
        action_type: str, 
        recipient: str, 
        subject: str
    ):
        """Log email actions for audit purposes"""
        try:
            # This would save to an audit log database
            log_entry = {
                "user_id": user_id,
                "action_type": action_type,
                "recipient": recipient,
                "subject": subject,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Email action logged: {log_entry}")
            
        except Exception as e:
            logger.error(f"Error logging email action: {e}")

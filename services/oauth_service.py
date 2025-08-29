"""
OAuth Service for Jarvis Phone AI Assistant
Handles Gmail and Calendar OAuth integration setup
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from config import settings
from telephony.twilio_handler import TwilioHandler
from telephony.telnyx_handler import TelnyxHandler
from config import get_telephony_provider, is_twilio_enabled, is_telnyx_enabled

logger = logging.getLogger(__name__)


class OAuthProvider(Enum):
    """OAuth providers"""
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    SLACK = "slack"
    DISCORD = "discord"


class OAuthStatus(Enum):
    """OAuth integration status"""
    NOT_CONNECTED = "not_connected"
    PENDING = "pending"
    CONNECTED = "connected"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass
class OAuthIntegration:
    """OAuth integration details"""
    id: Optional[int] = None
    user_id: int = 0
    provider: OAuthProvider = OAuthProvider.GOOGLE
    status: OAuthStatus = OAuthStatus.NOT_CONNECTED
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    scopes: List[str] = None
    user_email: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.scopes is None:
            self.scopes = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


class OAuthService:
    """Service for managing OAuth integrations"""
    
    def __init__(self):
        self.telephony_provider = get_telephony_provider()
        
        # Initialize telephony handler for sending OAuth instructions
        if self.telephony_provider == "twilio" and is_twilio_enabled():
            self.sms_handler = TwilioHandler()
        elif self.telephony_provider == "telnyx" and is_telnyx_enabled():
            self.sms_handler = TelnyxHandler()
        else:
            logger.warning("No valid telephony provider configured for OAuth SMS")
            self.sms_handler = None
    
    async def initiate_google_oauth(self, user_id: int, user_phone: str) -> Dict[str, Any]:
        """Initiate Google OAuth flow for Gmail and Calendar"""
        try:
            logger.info(f"Initiating Google OAuth for user {user_id}")
            
            # Generate OAuth URL
            oauth_url = self._generate_google_oauth_url(user_id)
            
            # Send SMS with OAuth instructions
            if self.sms_handler:
                message = self._format_oauth_instructions("Google", oauth_url)
                await self.sms_handler.send_sms(user_phone, message)
                
                # Create pending OAuth integration
                integration = OAuthIntegration(
                    user_id=user_id,
                    provider=OAuthProvider.GOOGLE,
                    status=OAuthStatus.PENDING,
                    scopes=[
                        'https://www.googleapis.com/auth/gmail.readonly',
                        'https://www.googleapis.com/auth/gmail.send',
                        'https://www.googleapis.com/auth/gmail.modify',
                        'https://www.googleapis.com/auth/calendar.readonly',
                        'https://www.googleapis.com/auth/calendar.events'
                    ]
                )
                
                # Store integration (this would go to database)
                await self._store_oauth_integration(integration)
                
                logger.info(f"Google OAuth initiated for user {user_id}")
                
                return {
                    "success": True,
                    "oauth_url": oauth_url,
                    "message": "OAuth instructions sent via SMS"
                }
            else:
                return {
                    "success": False,
                    "error": "SMS service not available"
                }
                
        except Exception as e:
            logger.error(f"Error initiating Google OAuth: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def handle_google_oauth_callback(
        self, 
        user_id: int, 
        authorization_code: str
    ) -> Dict[str, Any]:
        """Handle Google OAuth callback and exchange code for tokens"""
        try:
            logger.info(f"Handling Google OAuth callback for user {user_id}")
            
            # Exchange authorization code for access token
            token_response = await self._exchange_google_code(authorization_code)
            
            if not token_response.get('success'):
                return token_response
            
            # Get user info from Google
            user_info = await self._get_google_user_info(token_response['access_token'])
            
            if not user_info.get('success'):
                return user_info
            
            # Update OAuth integration
            integration = await self._get_oauth_integration(user_id, OAuthProvider.GOOGLE)
            
            if integration:
                integration.status = OAuthStatus.CONNECTED
                integration.access_token = token_response['access_token']
                integration.refresh_token = token_response.get('refresh_token')
                integration.expires_at = datetime.utcnow() + timedelta(seconds=token_response['expires_in'])
                integration.user_email = user_info['email']
                integration.updated_at = datetime.utcnow()
                
                # Store updated integration
                await self._store_oauth_integration(integration)
                
                logger.info(f"Google OAuth completed for user {user_id} ({user_info['email']})")
                
                return {
                    "success": True,
                    "message": "Google OAuth completed successfully",
                    "user_email": user_info['email']
                }
            else:
                return {
                    "success": False,
                    "error": "OAuth integration not found"
                }
                
        except Exception as e:
            logger.error(f"Error handling Google OAuth callback: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def refresh_google_tokens(self, user_id: int) -> Dict[str, Any]:
        """Refresh expired Google access tokens"""
        try:
            integration = await self._get_oauth_integration(user_id, OAuthProvider.GOOGLE)
            
            if not integration or not integration.refresh_token:
                return {
                    "success": False,
                    "error": "No refresh token available"
                }
            
            # Refresh tokens using Google API
            token_response = await self._refresh_google_tokens(integration.refresh_token)
            
            if not token_response.get('success'):
                return token_response
            
            # Update integration with new tokens
            integration.access_token = token_response['access_token']
            integration.expires_at = datetime.utcnow() + timedelta(seconds=token_response['expires_in'])
            integration.updated_at = datetime.utcnow()
            
            # Store updated integration
            await self._store_oauth_integration(integration)
            
            logger.info(f"Google tokens refreshed for user {user_id}")
            
            return {
                "success": True,
                "message": "Tokens refreshed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error refreshing Google tokens: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_oauth_status(self, user_id: int) -> Dict[str, Any]:
        """Get OAuth integration status for a user"""
        try:
            integrations = await self._get_user_oauth_integrations(user_id)
            
            status_summary = {}
            
            for provider in OAuthProvider:
                integration = next(
                    (i for i in integrations if i.provider == provider), 
                    None
                )
                
                if integration:
                    # Check if token is expired
                    if (integration.expires_at and 
                        integration.expires_at < datetime.utcnow() and 
                        integration.status == OAuthStatus.CONNECTED):
                        integration.status = OAuthStatus.EXPIRED
                        await self._store_oauth_integration(integration)
                    
                    status_summary[provider.value] = {
                        "status": integration.status.value,
                        "connected": integration.status == OAuthStatus.CONNECTED,
                        "expires_at": integration.expires_at.isoformat() if integration.expires_at else None,
                        "user_email": integration.user_email
                    }
                else:
                    status_summary[provider.value] = {
                        "status": OAuthStatus.NOT_CONNECTED.value,
                        "connected": False,
                        "expires_at": None,
                        "user_email": None
                    }
            
            return {
                "user_id": user_id,
                "integrations": status_summary
            }
            
        except Exception as e:
            logger.error(f"Error getting OAuth status: {e}")
            return {"error": str(e)}
    
    async def revoke_oauth_integration(
        self, 
        user_id: int, 
        provider: OAuthProvider
    ) -> Dict[str, Any]:
        """Revoke OAuth integration for a user"""
        try:
            integration = await self._get_oauth_integration(user_id, provider)
            
            if not integration:
                return {
                    "success": False,
                    "error": "OAuth integration not found"
                }
            
            # Revoke tokens with provider
            if provider == OAuthProvider.GOOGLE:
                await self._revoke_google_tokens(integration.access_token)
            
            # Update integration status
            integration.status = OAuthStatus.REVOKED
            integration.access_token = None
            integration.refresh_token = None
            integration.expires_at = None
            integration.updated_at = datetime.utcnow()
            
            # Store updated integration
            await self._store_oauth_integration(integration)
            
            logger.info(f"OAuth integration revoked for user {user_id}, provider {provider.value}")
            
            return {
                "success": True,
                "message": f"{provider.value.title()} integration revoked successfully"
            }
            
        except Exception as e:
            logger.error(f"Error revoking OAuth integration: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_google_oauth_url(self, user_id: int) -> str:
        """Generate Google OAuth URL"""
        try:
            # Google OAuth 2.0 parameters
            params = {
                'client_id': settings.GOOGLE_CLIENT_ID,
                'redirect_uri': settings.GOOGLE_REDIRECT_URI,
                'scope': ' '.join([
                    'https://www.googleapis.com/auth/gmail.readonly',
                    'https://www.googleapis.com/auth/gmail.send',
                    'https://www.googleapis.com/auth/gmail.modify',
                    'https://www.googleapis.com/auth/calendar.readonly',
                    'https://www.googleapis.com/auth/calendar.events'
                ]),
                'response_type': 'code',
                'access_type': 'offline',
                'prompt': 'consent',
                'state': f"user_{user_id}"  # Include user ID for security
            }
            
            # Build query string
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            
            oauth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"
            
            return oauth_url
            
        except Exception as e:
            logger.error(f"Error generating Google OAuth URL: {e}")
            return ""
    
    def _format_oauth_instructions(self, provider: str, oauth_url: str) -> str:
        """Format OAuth instructions for SMS"""
        try:
            message = f"🔐 {provider} Integration Setup\n\n"
            message += "To connect your {provider} account:\n\n"
            message += "1. Click this link:\n"
            message += f"{oauth_url}\n\n"
            message += "2. Sign in and authorize access\n"
            message += "3. You'll be redirected back\n\n"
            message += "Reply 'connected' once you've completed the setup."
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting OAuth instructions: {e}")
            return f"Please visit {oauth_url} to connect your {provider} account."
    
    async def _exchange_google_code(self, authorization_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access tokens"""
        try:
            import httpx
            
            # Token exchange endpoint
            token_url = "https://oauth2.googleapis.com/token"
            
            # Request data
            data = {
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'code': authorization_code,
                'grant_type': 'authorization_code',
                'redirect_uri': settings.GOOGLE_REDIRECT_URI
            }
            
            # Make request
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
                
                if response.status_code == 200:
                    token_data = response.json()
                    
                    return {
                        "success": True,
                        "access_token": token_data['access_token'],
                        "refresh_token": token_data.get('refresh_token'),
                        "expires_in": token_data.get('expires_in', 3600)
                    }
                else:
                    logger.error(f"Google token exchange failed: {response.text}")
                    return {
                        "success": False,
                        "error": "Token exchange failed"
                    }
                    
        except Exception as e:
            logger.error(f"Error exchanging Google code: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_google_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Google"""
        try:
            import httpx
            
            # User info endpoint
            userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            
            headers = {'Authorization': f'Bearer {access_token}'}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(userinfo_url, headers=headers)
                
                if response.status_code == 200:
                    user_data = response.json()
                    
                    return {
                        "success": True,
                        "email": user_data.get('email'),
                        "name": user_data.get('name'),
                        "picture": user_data.get('picture')
                    }
                else:
                    logger.error(f"Google user info failed: {response.text}")
                    return {
                        "success": False,
                        "error": "Failed to get user info"
                    }
                    
        except Exception as e:
            logger.error(f"Error getting Google user info: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _refresh_google_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh Google access tokens"""
        try:
            import httpx
            
            # Token refresh endpoint
            token_url = "https://oauth2.googleapis.com/token"
            
            # Request data
            data = {
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
            
            # Make request
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
                
                if response.status_code == 200:
                    token_data = response.json()
                    
                    return {
                        "success": True,
                        "access_token": token_data['access_token'],
                        "expires_in": token_data.get('expires_in', 3600)
                    }
                else:
                    logger.error(f"Google token refresh failed: {response.text}")
                    return {
                        "success": False,
                        "error": "Token refresh failed"
                    }
                    
        except Exception as e:
            logger.error(f"Error refreshing Google tokens: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _revoke_google_tokens(self, access_token: str):
        """Revoke Google access tokens"""
        try:
            import httpx
            
            # Token revocation endpoint
            revoke_url = "https://oauth2.googleapis.com/revoke"
            
            data = {'token': access_token}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(revoke_url, data=data)
                
                if response.status_code == 200:
                    logger.info("Google tokens revoked successfully")
                else:
                    logger.warning(f"Google token revocation failed: {response.text}")
                    
        except Exception as e:
            logger.error(f"Error revoking Google tokens: {e}")
    
    async def _store_oauth_integration(self, integration: OAuthIntegration):
        """Store OAuth integration in database"""
        try:
            # This would save to an oauth_integrations table
            # For now, just log it
            logger.debug(f"Storing OAuth integration: {integration.provider.value} for user {integration.user_id}")
            
        except Exception as e:
            logger.error(f"Error storing OAuth integration: {e}")
    
    async def _get_oauth_integration(
        self, 
        user_id: int, 
        provider: OAuthProvider
    ) -> Optional[OAuthIntegration]:
        """Get OAuth integration for a user and provider"""
        try:
            # This would query the oauth_integrations table
            # For now, return None
            return None
            
        except Exception as e:
            logger.error(f"Error getting OAuth integration: {e}")
            return None
    
    async def _get_user_oauth_integrations(self, user_id: int) -> List[OAuthIntegration]:
        """Get all OAuth integrations for a user"""
        try:
            # This would query the oauth_integrations table
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error getting user OAuth integrations: {e}")
            return []

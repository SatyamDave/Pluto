"""
OAuth Routes for Jarvis Phone AI Assistant
Handles API endpoints for OAuth integration setup
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from services.oauth_service import OAuthService, OAuthProvider

logger = logging.getLogger(__name__)
router = APIRouter()


class OAuthInitiateRequest(BaseModel):
    """Request model for initiating OAuth"""
    user_id: int
    user_phone: str
    provider: str


class OAuthCallbackRequest(BaseModel):
    """Request model for OAuth callback"""
    user_id: int
    authorization_code: str
    state: Optional[str] = None


class OAuthStatusResponse(BaseModel):
    """Response model for OAuth status"""
    user_id: int
    integrations: Dict[str, Dict[str, Any]]


@router.post("/initiate")
async def initiate_oauth(request: OAuthInitiateRequest):
    """Initiate OAuth flow for a provider"""
    try:
        oauth_service = OAuthService()
        
        # Validate provider
        try:
            provider = OAuthProvider(request.provider)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid provider: {request.provider}")
        
        # Initiate OAuth based on provider
        if provider == OAuthProvider.GOOGLE:
            result = await oauth_service.initiate_google_oauth(
                user_id=request.user_id,
                user_phone=request.user_phone
            )
        else:
            raise HTTPException(status_code=400, detail=f"Provider {provider.value} not yet supported")
        
        if result.get('success'):
            return {
                "message": "OAuth initiated successfully",
                "provider": provider.value,
                "oauth_url": result.get('oauth_url'),
                "instructions_sent": True
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'OAuth initiation failed'))
        
    except Exception as e:
        logger.error(f"Error initiating OAuth: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/callback")
async def handle_oauth_callback(request: OAuthCallbackRequest):
    """Handle OAuth callback and exchange code for tokens"""
    try:
        oauth_service = OAuthService()
        
        # Handle callback based on state (which contains provider info)
        # For now, we'll assume Google OAuth
        result = await oauth_service.handle_google_oauth_callback(
            user_id=request.user_id,
            authorization_code=request.authorization_code
        )
        
        if result.get('success'):
            return {
                "message": "OAuth completed successfully",
                "provider": "google",
                "user_email": result.get('user_email'),
                "status": "connected"
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'OAuth callback failed'))
        
    except Exception as e:
        logger.error(f"Error handling OAuth callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{user_id}", response_model=OAuthStatusResponse)
async def get_oauth_status(user_id: int):
    """Get OAuth integration status for a user"""
    try:
        oauth_service = OAuthService()
        
        status = await oauth_service.get_oauth_status(user_id)
        
        if "error" in status:
            raise HTTPException(status_code=500, detail=status["error"])
        
        return OAuthStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"Error getting OAuth status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh/{user_id}")
async def refresh_oauth_tokens(user_id: int, provider: str = Query(..., description="OAuth provider")):
    """Refresh expired OAuth tokens"""
    try:
        oauth_service = OAuthService()
        
        # Validate provider
        try:
            oauth_provider = OAuthProvider(provider)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
        
        # Refresh tokens based on provider
        if oauth_provider == OAuthProvider.GOOGLE:
            result = await oauth_service.refresh_google_tokens(user_id)
        else:
            raise HTTPException(status_code=400, detail=f"Provider {provider} not yet supported")
        
        if result.get('success'):
            return {
                "message": "Tokens refreshed successfully",
                "provider": provider,
                "status": "refreshed"
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Token refresh failed'))
        
    except Exception as e:
        logger.error(f"Error refreshing OAuth tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/revoke/{user_id}")
async def revoke_oauth_integration(user_id: int, provider: str = Query(..., description="OAuth provider")):
    """Revoke OAuth integration for a user"""
    try:
        oauth_service = OAuthService()
        
        # Validate provider
        try:
            oauth_provider = OAuthProvider(provider)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
        
        # Revoke integration
        result = await oauth_service.revoke_oauth_integration(user_id, oauth_provider)
        
        if result.get('success'):
            return {
                "message": result.get('message', 'OAuth integration revoked successfully'),
                "provider": provider,
                "status": "revoked"
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'OAuth revocation failed'))
        
    except Exception as e:
        logger.error(f"Error revoking OAuth integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def get_available_providers():
    """Get list of available OAuth providers"""
    try:
        return {
            "providers": [
                {
                    "id": provider.value,
                    "name": provider.value.title(),
                    "supported": provider in [OAuthProvider.GOOGLE],  # Add more as implemented
                    "scopes": {
                        "google": [
                            "Gmail (read, send, modify)",
                            "Google Calendar (read, events)"
                        ]
                    }.get(provider.value, [])
                }
                for provider in OAuthProvider
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting OAuth providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/setup-instructions/{provider}")
async def get_setup_instructions(provider: str):
    """Get setup instructions for a specific OAuth provider"""
    try:
        # Validate provider
        try:
            oauth_provider = OAuthProvider(provider)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
        
        instructions = {
            "google": {
                "name": "Google (Gmail + Calendar)",
                "description": "Connect your Google account to access Gmail and Google Calendar",
                "scopes": [
                    "Read and send emails",
                    "Manage calendar events",
                    "Access to Gmail and Calendar APIs"
                ],
                "setup_steps": [
                    "1. Click 'Connect Google Account'",
                    "2. Sign in to your Google account",
                    "3. Grant permission to access Gmail and Calendar",
                    "4. You'll receive a confirmation SMS"
                ],
                "benefits": [
                    "Auto-reply to low-priority emails",
                    "Calendar conflict detection",
                    "Email summarization",
                    "Schedule management"
                ]
            }
        }
        
        if provider not in instructions:
            raise HTTPException(status_code=400, detail=f"Provider {provider} not yet supported")
        
        return {
            "provider": provider,
            "instructions": instructions[provider]
        }
        
    except Exception as e:
        logger.error(f"Error getting setup instructions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

"""
Beta Management API
Handles waitlist, invite codes, and beta user onboarding
"""

import os
import secrets
import string
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr
import redis
import posthog
from sqlalchemy.orm import Session

# Initialize Redis for waitlist management
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

# Initialize PostHog
posthog.api_key = os.getenv("POSTHOG_API_KEY")
posthog.host = os.getenv("POSTHOG_HOST", "https://app.posthog.com")

router = APIRouter(prefix="/beta", tags=["beta"])

# Pydantic models
class WaitlistSignup(BaseModel):
    email: EmailStr
    source: Optional[str] = None
    referral_code: Optional[str] = None

class InviteCodeRequest(BaseModel):
    email: EmailStr
    reason: Optional[str] = None

class InviteCodeResponse(BaseModel):
    invite_code: str
    expires_at: datetime
    max_uses: int
    current_uses: int

class BetaStats(BaseModel):
    total_waitlist: int
    total_invites_sent: int
    total_beta_users: int
    conversion_rate: float
    avg_waitlist_position: float

class ReferralStats(BaseModel):
    user_id: str
    total_referrals: int
    successful_referrals: int
    referral_rewards: List[Dict[str, Any]]

def generate_invite_code(length: int = 8) -> str:
    """Generate a secure invite code"""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def get_waitlist_position(email: str) -> int:
    """Get user's position in waitlist"""
    position = redis_client.zrank("beta_waitlist", email)
    return int(position) + 1 if position is not None else -1

def add_to_waitlist(email: str, source: str = None, referral_code: str = None):
    """Add user to waitlist"""
    timestamp = datetime.now().timestamp()
    redis_client.zadd("beta_waitlist", {email: timestamp})
    
    # Store additional info
    waitlist_data = {
        "email": email,
        "joined_at": timestamp,
        "source": source,
        "referral_code": referral_code
    }
    redis_client.hset(f"waitlist_user:{email}", mapping=waitlist_data)

@router.post("/waitlist")
async def join_waitlist(signup: WaitlistSignup):
    """Join the beta waitlist"""
    try:
        # Check if already on waitlist
        if redis_client.zrank("beta_waitlist", signup.email) is not None:
            position = get_waitlist_position(signup.email)
            return {
                "message": "Already on waitlist",
                "position": position,
                "status": "existing"
            }
        
        # Check waitlist limit
        waitlist_size = redis_client.zcard("beta_waitlist")
        max_waitlist = 1000  # Allow 1000 people on waitlist
        
        if waitlist_size >= max_waitlist:
            raise HTTPException(
                status_code=429, 
                detail="Waitlist is full. Please try again later."
            )
        
        # Add to waitlist
        add_to_waitlist(signup.email, signup.source, signup.referral_code)
        position = get_waitlist_position(signup.email)
        
        # Track in PostHog
        posthog.capture(signup.email, "waitlist_signup", {
            "email": signup.email,
            "position": position,
            "source": signup.source,
            "referral_code": signup.referral_code,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "message": "Successfully joined waitlist",
            "position": position,
            "status": "new"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/waitlist/position/{email}")
async def get_waitlist_position_endpoint(email: str):
    """Get user's waitlist position"""
    position = get_waitlist_position(email)
    if position == -1:
        raise HTTPException(status_code=404, detail="Email not found on waitlist")
    
    return {"position": position}

@router.get("/waitlist/stats")
async def get_waitlist_stats():
    """Get waitlist statistics"""
    total_waitlist = redis_client.zcard("beta_waitlist")
    total_invites_sent = redis_client.get("total_invites_sent") or 0
    total_beta_users = redis_client.get("total_beta_users") or 0
    
    # Calculate conversion rate
    conversion_rate = 0
    if total_invites_sent > 0:
        conversion_rate = (int(total_beta_users) / int(total_invites_sent)) * 100
    
    return BetaStats(
        total_waitlist=total_waitlist,
        total_invites_sent=int(total_invites_sent),
        total_beta_users=int(total_beta_users),
        conversion_rate=conversion_rate,
        avg_waitlist_position=total_waitlist / 2 if total_waitlist > 0 else 0
    )

@router.post("/invite/generate")
async def generate_invite_code_endpoint(request: InviteCodeRequest):
    """Generate an invite code for a specific user"""
    try:
        # Check if user is on waitlist
        position = get_waitlist_position(request.email)
        if position == -1:
            raise HTTPException(
                status_code=404, 
                detail="Email not found on waitlist"
            )
        
        # Generate invite code
        invite_code = generate_invite_code()
        expires_at = datetime.now() + timedelta(days=7)
        
        # Store invite code
        invite_data = {
            "email": request.email,
            "code": invite_code,
            "expires_at": expires_at.isoformat(),
            "max_uses": 1,
            "current_uses": 0,
            "reason": request.reason,
            "created_at": datetime.now().isoformat()
        }
        
        redis_client.hset(f"invite_code:{invite_code}", mapping=invite_data)
        redis_client.expire(f"invite_code:{invite_code}", 7 * 24 * 60 * 60)  # 7 days
        
        # Remove from waitlist
        redis_client.zrem("beta_waitlist", request.email)
        
        # Update stats
        redis_client.incr("total_invites_sent")
        
        # Track in PostHog
        posthog.capture(request.email, "invite_code_generated", {
            "email": request.email,
            "invite_code": invite_code,
            "waitlist_position": position,
            "reason": request.reason
        })
        
        return InviteCodeResponse(
            invite_code=invite_code,
            expires_at=expires_at,
            max_uses=1,
            current_uses=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/invite/validate")
async def validate_invite_code(invite_code: str):
    """Validate an invite code"""
    try:
        # Get invite code data
        invite_data = redis_client.hgetall(f"invite_code:{invite_code}")
        if not invite_data:
            raise HTTPException(status_code=404, detail="Invalid invite code")
        
        # Check if expired
        expires_at = datetime.fromisoformat(invite_data[b"expires_at"].decode())
        if datetime.now() > expires_at:
            raise HTTPException(status_code=410, detail="Invite code expired")
        
        # Check usage limit
        current_uses = int(invite_data[b"current_uses"].decode())
        max_uses = int(invite_data[b"max_uses"].decode())
        
        if current_uses >= max_uses:
            raise HTTPException(status_code=410, detail="Invite code already used")
        
        return {
            "valid": True,
            "email": invite_data[b"email"].decode(),
            "expires_at": expires_at,
            "max_uses": max_uses,
            "current_uses": current_uses
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/invite/use")
async def use_invite_code(invite_code: str, user_email: str):
    """Use an invite code to create a beta account"""
    try:
        # Validate invite code
        invite_data = redis_client.hgetall(f"invite_code:{invite_code}")
        if not invite_data:
            raise HTTPException(status_code=404, detail="Invalid invite code")
        
        # Check if expired
        expires_at = datetime.fromisoformat(invite_data[b"expires_at"].decode())
        if datetime.now() > expires_at:
            raise HTTPException(status_code=410, detail="Invite code expired")
        
        # Check usage limit
        current_uses = int(invite_data[b"current_uses"].decode())
        max_uses = int(invite_data[b"max_uses"].decode())
        
        if current_uses >= max_uses:
            raise HTTPException(status_code=410, detail="Invite code already used")
        
        # Check if email matches
        expected_email = invite_data[b"email"].decode()
        if user_email != expected_email:
            raise HTTPException(
                status_code=400, 
                detail="Invite code is for a different email"
            )
        
        # Mark invite code as used
        redis_client.hincrby(f"invite_code:{invite_code}", "current_uses", 1)
        
        # Update stats
        redis_client.incr("total_beta_users")
        
        # Track in PostHog
        posthog.capture(user_email, "invite_code_used", {
            "email": user_email,
            "invite_code": invite_code,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "message": "Invite code used successfully",
            "user_email": user_email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/referral/stats/{user_id}")
async def get_referral_stats(user_id: str):
    """Get user's referral statistics"""
    try:
        # Get referral data from Redis
        total_referrals = redis_client.get(f"referrals:{user_id}:total") or 0
        successful_referrals = redis_client.get(f"referrals:{user_id}:successful") or 0
        
        # Get referral rewards
        rewards = []
        reward_keys = redis_client.keys(f"referral_rewards:{user_id}:*")
        for key in reward_keys:
            reward_data = redis_client.hgetall(key)
            if reward_data:
                rewards.append({
                    "type": reward_data[b"type"].decode(),
                    "amount": reward_data[b"amount"].decode(),
                    "earned_at": reward_data[b"earned_at"].decode()
                })
        
        return ReferralStats(
            user_id=user_id,
            total_referrals=int(total_referrals),
            successful_referrals=int(successful_referrals),
            referral_rewards=rewards
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/referral/track")
async def track_referral(referrer_id: str, referred_email: str):
    """Track a referral"""
    try:
        # Increment referral count
        redis_client.incr(f"referrals:{referrer_id}:total")
        
        # Store referral data
        referral_data = {
            "referrer_id": referrer_id,
            "referred_email": referred_email,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        redis_client.hset(f"referral:{referrer_id}:{referred_email}", mapping=referral_data)
        
        # Track in PostHog
        posthog.capture(referrer_id, "referral_tracked", {
            "referrer_id": referrer_id,
            "referred_email": referred_email,
            "timestamp": datetime.now().isoformat()
        })
        
        return {"message": "Referral tracked successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/referral/complete")
async def complete_referral(referrer_id: str, referred_email: str):
    """Mark a referral as completed"""
    try:
        # Update referral status
        redis_client.hset(f"referral:{referrer_id}:{referred_email}", "status", "completed")
        
        # Increment successful referrals
        redis_client.incr(f"referrals:{referrer_id}:successful")
        
        # Award referral bonus (e.g., 30-day Pro trial)
        reward_data = {
            "type": "pro_trial_extension",
            "amount": "30",
            "earned_at": datetime.now().isoformat()
        }
        redis_client.hset(f"referral_rewards:{referrer_id}:{datetime.now().timestamp()}", mapping=reward_data)
        
        # Track in PostHog
        posthog.capture(referrer_id, "referral_completed", {
            "referrer_id": referrer_id,
            "referred_email": referred_email,
            "reward": "pro_trial_extension",
            "timestamp": datetime.now().isoformat()
        })
        
        return {"message": "Referral completed successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Background task to send invite codes
async def send_invite_email(email: str, invite_code: str, background_tasks: BackgroundTasks):
    """Send invite code email"""
    # This would integrate with your email service
    # For now, just log the action
    print(f"Sending invite code {invite_code} to {email}")
    
    # Track email sent
    posthog.capture(email, "invite_email_sent", {
        "email": email,
        "invite_code": invite_code,
        "timestamp": datetime.now().isoformat()
    })

@router.post("/invite/send")
async def send_invite_code(request: InviteCodeRequest, background_tasks: BackgroundTasks):
    """Generate and send invite code via email"""
    try:
        # Generate invite code
        invite_response = await generate_invite_code_endpoint(request)
        
        # Send email in background
        background_tasks.add_task(
            send_invite_email, 
            request.email, 
            invite_response.invite_code
        )
        
        return {
            "message": "Invite code sent successfully",
            "invite_code": invite_response.invite_code
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""
User Manager for Pluto AI Phone Assistant
Handles user activation, identity management, and user context retrieval
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from db.database import get_db
from db.models import User, UserStyleProfile, UserPreference, UserMemory, UserHabit
from utils import get_logger

logger = get_logger(__name__)


class UserManager:
    """Manages user activation, identity, and context for Pluto"""
    
    def __init__(self):
        """Initialize the User Manager"""
        self.logger = logger
        self.logger.info("User Manager initialized")
    
    async def get_or_create_user(self, phone_number: str, db: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """
        Get existing user or create new one with full initialization
        
        Args:
            phone_number: User's phone number
            db: Optional database session (will create one if not provided)
            
        Returns:
            User data dictionary with all profile information
        """
        try:
            # Clean phone number
            clean_phone = self._clean_phone_number(phone_number)
            
            # Use provided session or create new one
            if db is None:
                async for session in get_db():
                    return await self._get_or_create_user_internal(clean_phone, session)
            else:
                return await self._get_or_create_user_internal(clean_phone, db)
                
        except Exception as e:
            self.logger.error(f"Error in get_or_create_user: {e}")
            raise
    
    async def _get_or_create_user_internal(self, clean_phone: str, db: AsyncSession) -> Dict[str, Any]:
        """Internal method to get or create user"""
        try:
            # Try to find existing user
            stmt = select(User).where(User.phone_number == clean_phone)
            result = await db.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                # Update last_seen timestamp
                await self._update_last_seen(existing_user.id, db)
                
                # Get full user profile
                user_profile = await self._get_full_user_profile(existing_user.id, db)
                self.logger.info(f"Retrieved existing user: {clean_phone}")
                return user_profile
            else:
                # Create new user with full initialization
                new_user = await self._create_new_user(clean_phone, db)
                self.logger.info(f"Created new user: {clean_phone}")
                return new_user
                
        except Exception as e:
            self.logger.error(f"Error in _get_or_create_user_internal: {e}")
            await db.rollback()
            raise
    
    async def _create_new_user(self, phone_number: str, db: AsyncSession) -> Dict[str, Any]:
        """Create a new user with full profile initialization"""
        try:
            # Create base user
            new_user = User(
                phone_number=phone_number,
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
            db.add(new_user)
            await db.flush()  # Get the ID without committing
            
            # Create style profile
            style_profile = UserStyleProfile(
                user_id=new_user.id,
                emoji_usage=True,
                formality_level='casual',
                avg_message_length='medium',
                signature_phrases=[],
                tone_preferences={"humor": 0.5, "formality": 0.3},
                communication_style='friendly'
            )
            db.add(style_profile)
            
            # Create default preferences
            default_preferences = [
                ("auto_confirm_family", True),
                ("auto_confirm_work", False),
                ("morning_digest_enabled", True),
                ("morning_digest_time", "08:00"),
                ("proactive_mode", True),
                ("wake_up_calls", True),
                ("email_summaries", True),
                ("calendar_alerts", True),
                ("urgent_email_alerts", True),
                ("habit_reminders", True),
                ("proactive_suggestions", True)
            ]
            
            for key, value in default_preferences:
                preference = UserPreference(
                    user_id=new_user.id,
                    preference_key=key,
                    preference_value=value
                )
                db.add(preference)
            
            # Commit all changes
            await db.commit()
            await db.refresh(new_user)
            
            # Return full profile
            return await self._get_full_user_profile(new_user.id, db)
            
        except Exception as e:
            self.logger.error(f"Error creating new user: {e}")
            await db.rollback()
            raise
    
    async def _get_full_user_profile(self, user_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Get complete user profile with all related data"""
        try:
            # Get user with relationships
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one()
            
            if not user:
                raise ValueError(f"User not found: {user_id}")
            
            # Get style profile
            style_stmt = select(UserStyleProfile).where(UserStyleProfile.user_id == user_id)
            style_result = await db.execute(style_stmt)
            style_profile = style_result.scalar_one_or_none()
            
            # Get user preferences
            prefs_stmt = select(UserPreference).where(UserPreference.user_id == user_id)
            prefs_result = await db.execute(prefs_stmt)
            preferences = {pref.preference_key: pref.preference_value for pref in prefs_result.scalars()}
            
            # Get recent memory count
            memory_stmt = select(UserMemory).where(UserMemory.user_id == user_id)
            memory_result = await db.execute(memory_stmt)
            memory_count = len(memory_result.scalars().all())
            
            # Get habit count
            habit_stmt = select(UserHabit).where(UserHabit.user_id == user_id)
            habit_result = await db.execute(habit_stmt)
            habit_count = len(habit_result.scalars().all())
            
            return {
                "id": user.id,
                "phone_number": user.phone_number,
                "name": user.name,
                "email": user.email,
                "is_active": user.is_active,
                "message_count": getattr(user, 'message_count', 0),
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "last_seen": getattr(user, 'last_seen', None),
                "style_profile": {
                    "emoji_usage": style_profile.emoji_usage if style_profile else True,
                    "formality_level": style_profile.formality_level if style_profile else 'casual',
                    "avg_message_length": style_profile.avg_message_length if style_profile else 'medium',
                    "signature_phrases": style_profile.signature_phrases if style_profile else [],
                    "tone_preferences": style_profile.tone_preferences if style_profile else {},
                    "communication_style": style_profile.communication_style if style_profile else 'friendly'
                } if style_profile else {},
                "preferences": preferences,
                "stats": {
                    "memory_count": memory_count,
                    "habit_count": habit_count
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting full user profile: {e}")
            raise
    
    async def _update_last_seen(self, user_id: int, db: AsyncSession) -> None:
        """Update user's last_seen timestamp"""
        try:
            stmt = update(User).where(User.id == user_id).values(
                last_seen=datetime.now(timezone.utc)
            )
            await db.execute(stmt)
            await db.commit()
        except Exception as e:
            self.logger.error(f"Error updating last_seen: {e}")
            await db.rollback()
    
    async def get_user_by_id(self, user_id: int, db: Optional[AsyncSession] = None) -> Optional[Dict[str, Any]]:
        """Get user profile by ID"""
        try:
            if db is None:
                async for session in get_db():
                    return await self._get_full_user_profile(user_id, session)
            else:
                return await self._get_full_user_profile(user_id, db)
        except Exception as e:
            self.logger.error(f"Error getting user by ID: {e}")
            return None
    
    async def get_user_by_phone(self, phone_number: str, db: Optional[AsyncSession] = None) -> Optional[Dict[str, Any]]:
        """Get user profile by phone number"""
        try:
            clean_phone = self._clean_phone_number(phone_number)
            
            if db is None:
                async for session in get_db():
                    return await self._get_user_by_phone_internal(clean_phone, session)
            else:
                return await self._get_user_by_phone_internal(clean_phone, db)
                
        except Exception as e:
            self.logger.error(f"Error getting user by phone: {e}")
            return None
    
    async def _get_user_by_phone_internal(self, clean_phone: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
        """Internal method to get user by phone number"""
        try:
            stmt = select(User).where(User.phone_number == clean_phone)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                return await self._get_full_user_profile(user.id, db)
            return None
            
        except Exception as e:
            self.logger.error(f"Error in _get_user_by_phone_internal: {e}")
            return None
    
    async def update_user_preference(self, user_id: int, key: str, value: Any, db: Optional[AsyncSession] = None) -> bool:
        """Update a user preference"""
        try:
            if db is None:
                async for session in get_db():
                    return await self._update_user_preference_internal(user_id, key, value, session)
            else:
                return await self._update_user_preference_internal(user_id, key, value, db)
                
        except Exception as e:
            self.logger.error(f"Error updating user preference: {e}")
            return False
    
    async def _update_user_preference_internal(self, user_id: int, key: str, value: Any, db: AsyncSession) -> bool:
        """Internal method to update user preference"""
        try:
            # Try to update existing preference
            stmt = update(UserPreference).where(
                UserPreference.user_id == user_id,
                UserPreference.preference_key == key
            ).values(preference_value=value)
            
            result = await db.execute(stmt)
            
            if result.rowcount == 0:
                # Create new preference
                new_pref = UserPreference(
                    user_id=user_id,
                    preference_key=key,
                    preference_value=value
                )
                db.add(new_pref)
            
            await db.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error in _update_user_preference_internal: {e}")
            await db.rollback()
            return False
    
    async def update_style_profile(self, user_id: int, style_updates: Dict[str, Any], db: Optional[AsyncSession] = None) -> bool:
        """Update user's style profile"""
        try:
            if db is None:
                async for session in get_db():
                    return await self._update_style_profile_internal(user_id, style_updates, session)
            else:
                return await self._update_style_profile_internal(user_id, style_updates, db)
                
        except Exception as e:
            self.logger.error(f"Error updating style profile: {e}")
            return False
    
    async def _update_style_profile_internal(self, user_id: int, style_updates: Dict[str, Any], db: AsyncSession) -> bool:
        """Internal method to update style profile"""
        try:
            stmt = update(UserStyleProfile).where(
                UserStyleProfile.user_id == user_id
            ).values(**style_updates)
            
            await db.execute(stmt)
            await db.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error in _update_style_profile_internal: {e}")
            await db.rollback()
            return False
    
    async def get_active_users(self, db: Optional[AsyncSession] = None) -> List[Dict[str, Any]]:
        """Get all active users for proactive tasks"""
        try:
            if db is None:
                async for session in get_db():
                    return await self._get_active_users_internal(session)
            else:
                return await self._get_active_users_internal(db)
                
        except Exception as e:
            self.logger.error(f"Error getting active users: {e}")
            return []
    
    async def _get_active_users_internal(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Internal method to get active users"""
        try:
            stmt = select(User).where(User.is_active == True)
            result = await db.execute(stmt)
            users = result.scalars().all()
            
            active_users = []
            for user in users:
                # Get minimal user info for proactive tasks
                active_users.append({
                    "id": user.id,
                    "phone_number": user.phone_number,
                    "name": user.name
                })
            
            return active_users
            
        except Exception as e:
            self.logger.error(f"Error in _get_active_users_internal: {e}")
            return []
    
    async def increment_message_count(self, user_id: int, db: Optional[AsyncSession] = None) -> bool:
        """Increment user's message count"""
        try:
            if db is None:
                async for session in get_db():
                    return await self._increment_message_count_internal(user_id, session)
            else:
                return await self._increment_message_count_internal(user_id, db)
                
        except Exception as e:
            self.logger.error(f"Error incrementing message count: {e}")
            return False
    
    async def _increment_message_count_internal(self, user_id: int, db: AsyncSession) -> bool:
        """Internal method to increment message count"""
        try:
            stmt = update(User).where(User.id == user_id).values(
                message_count=User.message_count + 1
            )
            await db.execute(stmt)
            await db.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error in _increment_message_count_internal: {e}")
            await db.rollback()
            return False
    
    def _clean_phone_number(self, phone_number: str) -> str:
        """Clean phone number to standard format"""
        # Remove all non-digit characters
        clean = ''.join(filter(str.isdigit, phone_number))
        
        # Ensure it starts with country code if not present
        if len(clean) == 10:
            clean = "1" + clean  # Assume US number
        elif len(clean) == 11 and clean.startswith("1"):
            pass  # Already has US country code
        elif len(clean) < 10:
            raise ValueError(f"Invalid phone number: {phone_number}")
        
        return clean


# Global instance
user_manager = UserManager()

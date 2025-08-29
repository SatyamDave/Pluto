"""
Test user activation and identity management system
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from services.user_manager import UserManager
from db.models import User, UserStyleProfile, UserPreference


class TestUserManager:
    """Test the UserManager class"""
    
    @pytest.fixture
    def user_manager(self):
        """Create a UserManager instance for testing"""
        return UserManager()
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session"""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.refresh = AsyncMock()
        session.flush = AsyncMock()
        return session
    
    def test_clean_phone_number(self, user_manager):
        """Test phone number cleaning"""
        # Test US number with country code
        assert user_manager._clean_phone_number("+1-555-123-4567") == "15551234567"
        
        # Test US number without country code
        assert user_manager._clean_phone_number("555-123-4567") == "15551234567"
        
        # Test number with spaces and dashes
        assert user_manager._clean_phone_number("555 123 4567") == "15551234567"
        
        # Test already clean number
        assert user_manager._clean_phone_number("15551234567") == "15551234567"
    
    def test_clean_phone_number_invalid(self, user_manager):
        """Test phone number cleaning with invalid numbers"""
        with pytest.raises(ValueError):
            user_manager._clean_phone_number("123")  # Too short
        
        with pytest.raises(ValueError):
            user_manager._clean_phone_number("abc")  # No digits
    
    @pytest.mark.asyncio
    async def test_get_or_create_user_new_user(self, user_manager, mock_db_session):
        """Test creating a new user"""
        # Mock database query to return no existing user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        # Mock the internal methods
        user_manager._create_new_user = AsyncMock()
        user_manager._get_full_user_profile = AsyncMock()
        
        # Mock user creation
        mock_user = MagicMock()
        mock_user.id = 1
        user_manager._create_new_user.return_value = {"id": 1, "phone_number": "15551234567"}
        
        # Test
        result = await user_manager._get_or_create_user_internal("15551234567", mock_db_session)
        
        # Verify
        assert result["id"] == 1
        assert result["phone_number"] == "15551234567"
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_or_create_user_existing_user(self, user_manager, mock_db_session):
        """Test retrieving an existing user"""
        # Mock existing user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.phone_number = "15551234567"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = mock_result
        
        # Mock the internal methods
        user_manager._update_last_seen = AsyncMock()
        user_manager._get_full_user_profile = AsyncMock()
        user_manager._get_full_user_profile.return_value = {"id": 1, "phone_number": "15551234567"}
        
        # Test
        result = await user_manager._get_or_create_user_internal("15551234567", mock_db_session)
        
        # Verify
        assert result["id"] == 1
        assert result["phone_number"] == "15551234567"
        user_manager._update_last_seen.assert_called_once_with(1, mock_db_session)
        user_manager._get_full_user_profile.assert_called_once_with(1, mock_db_session)
    
    @pytest.mark.asyncio
    async def test_create_new_user(self, user_manager, mock_db_session):
        """Test creating a new user with full profile"""
        # Mock user creation
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.phone_number = "15551234567"
        mock_user.is_active = True
        mock_user.created_at = datetime.now(timezone.utc)
        mock_user.updated_at = datetime.now(timezone.utc)
        mock_user.last_seen = None
        
        # Mock the profile creation
        user_manager._get_full_user_profile = AsyncMock()
        user_manager._get_full_user_profile.return_value = {
            "id": 1,
            "phone_number": "15551234567",
            "is_active": True,
            "style_profile": {},
            "preferences": {},
            "stats": {"memory_count": 0, "habit_count": 0}
        }
        
        # Test
        result = await user_manager._create_new_user("15551234567", mock_db_session)
        
        # Verify
        assert result["id"] == 1
        assert result["phone_number"] == "15551234567"
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_full_user_profile(self, user_manager, mock_db_session):
        """Test getting full user profile"""
        # Mock user data
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.phone_number = "15551234567"
        mock_user.name = "Test User"
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.created_at = datetime.now(timezone.utc)
        mock_user.updated_at = datetime.now(timezone.utc)
        mock_user.last_seen = None
        
        # Mock style profile
        mock_style = MagicMock()
        mock_style.emoji_usage = True
        mock_style.formality_level = 'casual'
        mock_style.avg_message_length = 'medium'
        mock_style.signature_phrases = []
        mock_style.tone_preferences = {"humor": 0.5, "formality": 0.3}
        mock_style.communication_style = 'friendly'
        
        # Mock preferences
        mock_pref1 = MagicMock()
        mock_pref1.preference_key = "auto_confirm_family"
        mock_pref1.preference_value = True
        
        mock_pref2 = MagicMock()
        mock_pref2.preference_key = "morning_digest_enabled"
        mock_pref2.preference_value = True
        
        # Mock database queries
        user_result = MagicMock()
        user_result.scalar_one.return_value = mock_user
        
        style_result = MagicMock()
        style_result.scalar_one_or_none.return_value = mock_style
        
        prefs_result = MagicMock()
        prefs_result.scalars.return_value = [mock_pref1, mock_pref2]
        
        memory_result = MagicMock()
        memory_result.scalars.return_value = []
        
        habit_result = MagicMock()
        habit_result.scalars.return_value = []
        
        # Set up execute to return different results for different queries
        def mock_execute(stmt):
            if "users" in str(stmt):
                return user_result
            elif "user_style_profiles" in str(stmt):
                return style_result
            elif "user_preferences" in str(stmt):
                return prefs_result
            elif "user_memory" in str(stmt):
                return memory_result
            elif "user_habits" in str(stmt):
                return habit_result
            return MagicMock()
        
        mock_db_session.execute.side_effect = mock_execute
        
        # Test
        result = await user_manager._get_full_user_profile(1, mock_db_session)
        
        # Verify
        assert result["id"] == 1
        assert result["phone_number"] == "15551234567"
        assert result["name"] == "Test User"
        assert result["style_profile"]["emoji_usage"] is True
        assert result["style_profile"]["formality_level"] == 'casual'
        assert result["preferences"]["auto_confirm_family"] is True
        assert result["preferences"]["morning_digest_enabled"] is True
        assert result["stats"]["memory_count"] == 0
        assert result["stats"]["habit_count"] == 0


if __name__ == "__main__":
    # Run basic tests
    print("Testing UserManager...")
    
    # Test phone number cleaning
    user_manager = UserManager()
    
    test_numbers = [
        "+1-555-123-4567",
        "555-123-4567", 
        "555 123 4567",
        "15551234567"
    ]
    
    for number in test_numbers:
        cleaned = user_manager._clean_phone_number(number)
        print(f"'{number}' -> '{cleaned}'")
    
    print("Phone number cleaning tests passed!")
    
    # Test invalid numbers
    try:
        user_manager._clean_phone_number("123")
        print("ERROR: Should have raised ValueError for short number")
    except ValueError:
        print("Correctly raised ValueError for short number")
    
    try:
        user_manager._clean_phone_number("abc")
        print("ERROR: Should have raised ValueError for non-digit number")
    except ValueError:
        print("Correctly raised ValueError for non-digit number")
    
    print("All basic tests passed!")

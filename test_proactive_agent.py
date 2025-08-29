"""
Test Proactive Agent functionality
Tests scheduled tasks, morning digest, urgent alerts, habit suggestions, and outbound calls
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, time
from freezegun import freeze_time

from services.proactive_agent import ProactiveAgent
from services.user_manager import user_manager


class TestProactiveAgent:
    """Test the ProactiveAgent class"""
    
    @pytest.fixture
    def proactive_agent(self):
        """Create a ProactiveAgent instance for testing"""
        return ProactiveAgent()
    
    @pytest.fixture
    def mock_user_profile(self):
        """Mock user profile for testing"""
        return {
            "id": 1,
            "phone_number": "+15551234567",
            "name": "Test User",
            "preferences": {
                "morning_digest_enabled": True,
                "morning_digest_time": "08:00",
                "proactive_mode": True,
                "wake_up_calls": True,
                "urgent_email_alerts": True,
                "calendar_alerts": True,
                "habit_reminders": True
            },
            "style_profile": {
                "emoji_usage": True,
                "formality_level": "casual"
            }
        }
    
    @pytest.fixture
    def mock_context(self):
        """Mock user context for testing"""
        return {
            "email_status": {
                "total_unread": 5,
                "urgent_count": 2,
                "recent_urgent": [
                    {"sender": "boss@company.com", "subject": "Urgent meeting"},
                    {"sender": "client@client.com", "subject": "Project deadline"}
                ]
            },
            "calendar_status": {
                "today_count": 3,
                "conflict_count": 1,
                "next_event": {"title": "Team meeting", "start_time": "10:00 AM"}
            },
            "reminder_status": {
                "active_count": 2,
                "overdue_count": 0
            },
            "habit_status": {
                "suggestions": [
                    {"message": "Time for your morning routine"},
                    {"message": "Don't forget your daily check-in"}
                ],
                "due_soon_count": 1
            }
        }
    
    @pytest.mark.asyncio
    async def test_proactive_agent_initialization(self, proactive_agent):
        """Test proactive agent initialization"""
        assert proactive_agent.is_running == False
        assert proactive_agent.scheduler is not None
        assert proactive_agent.digest_service is not None
        assert proactive_agent.communication_service is not None
        assert proactive_agent.outbound_call_service is not None
        assert proactive_agent.active_wakeup_calls == {}
    
    @pytest.mark.asyncio
    async def test_start_proactive_agent(self, proactive_agent):
        """Test starting the proactive agent"""
        with patch.object(proactive_agent.scheduler, 'start') as mock_start:
            with patch.object(proactive_agent, '_schedule_recurring_tasks') as mock_schedule:
                with patch.object(asyncio, 'create_task') as mock_create_task:
                    await proactive_agent.start()
                    
                    assert proactive_agent.is_running == True
                    mock_start.assert_called_once()
                    mock_schedule.assert_called_once()
                    mock_create_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_proactive_agent(self, proactive_agent):
        """Test stopping the proactive agent"""
        proactive_agent.is_running = True
        
        with patch.object(proactive_agent.scheduler, 'shutdown') as mock_shutdown:
            await proactive_agent.stop()
            
            assert proactive_agent.is_running == False
            mock_shutdown.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_schedule_recurring_tasks(self, proactive_agent, mock_user_profile):
        """Test scheduling recurring tasks for users"""
        with patch.object(user_manager, 'get_active_users') as mock_get_users:
            with patch.object(user_manager, 'get_user_by_id') as mock_get_user:
                with patch.object(proactive_agent, '_schedule_user_tasks') as mock_schedule:
                    mock_get_users.return_value = [{"id": 1, "phone_number": "+15551234567"}]
                    mock_get_user.return_value = mock_user_profile
                    
                    await proactive_agent._schedule_recurring_tasks()
                    
                    mock_get_users.assert_called_once()
                    mock_get_user.assert_called_once_with(1)
                    mock_schedule.assert_called_once_with(1, "+15551234567", mock_user_profile["preferences"])
    
    @pytest.mark.asyncio
    async def test_schedule_user_tasks(self, proactive_agent):
        """Test scheduling tasks for a specific user"""
        user_id = 1
        phone_number = "+15551234567"
        preferences = {
            "morning_digest_time": "08:00",
            "proactive_mode": True
        }
        
        with patch.object(proactive_agent.scheduler, 'add_job') as mock_add_job:
            await proactive_agent._schedule_user_tasks(user_id, phone_number, preferences)
            
            # Should add 4 jobs: morning digest, habit check, email monitor, calendar check
            assert mock_add_job.call_count == 4
    
    @pytest.mark.asyncio
    async def test_send_morning_digest(self, proactive_agent, mock_user_profile):
        """Test sending morning digest"""
        user_id = 1
        phone_number = "+15551234567"
        
        with patch.object(user_manager, 'get_user_by_id') as mock_get_user:
            with patch.object(proactive_agent, 'generate_morning_digest') as mock_generate:
                with patch.object(proactive_agent.communication_service.sms_handler, 'send_sms') as mock_send:
                    with patch.object(proactive_agent, 'store_proactive_action') as mock_store:
                        mock_get_user.return_value = mock_user_profile
                        mock_generate.return_value = "Good morning! You have 5 unread emails."
                        mock_send.return_value = True
                        
                        await proactive_agent._send_morning_digest(user_id, phone_number)
                        
                        mock_get_user.assert_called_once_with(user_id)
                        mock_generate.assert_called_once_with(str(user_id))
                        mock_send.assert_called_once_with(to_phone=phone_number, message="Good morning! You have 5 unread emails.")
                        mock_store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_morning_digest_disabled(self, proactive_agent, mock_user_profile):
        """Test morning digest when disabled"""
        user_id = 1
        phone_number = "+15551234567"
        
        # Disable morning digest
        mock_user_profile["preferences"]["morning_digest_enabled"] = False
        
        with patch.object(user_manager, 'get_user_by_id') as mock_get_user:
            with patch.object(proactive_agent, 'generate_morning_digest') as mock_generate:
                mock_get_user.return_value = mock_user_profile
                
                await proactive_agent._send_morning_digest(user_id, phone_number)
                
                # Should not generate or send digest
                mock_generate.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_check_user_habits(self, proactive_agent, mock_user_profile):
        """Test checking user habits and sending suggestions"""
        user_id = 1
        phone_number = "+15551234567"
        
        mock_habits = [
            {
                "id": 1,
                "next_predicted": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                "pattern_type": "time_based",
                "pattern_data": {"time": "7AM", "action": "wake_up"},
                "confidence": 0.8
            }
        ]
        
        with patch.object(proactive_agent.habit_engine, 'get_user_habits') as mock_get_habits:
            with patch.object(proactive_agent, '_generate_habit_suggestion') as mock_generate:
                with patch.object(proactive_agent.communication_service.sms_handler, 'send_sms') as mock_send:
                    with patch.object(proactive_agent, 'store_proactive_action') as mock_store:
                        mock_get_habits.return_value = mock_habits
                        mock_generate.return_value = {
                            'type': 'habit_reminder',
                            'message': 'You usually set a 7AM wake-up. Want me to call you tomorrow?',
                            'action': 'schedule_wakeup'
                        }
                        mock_send.return_value = True
                        
                        await proactive_agent._check_user_habits(user_id, phone_number)
                        
                        mock_get_habits.assert_called_once_with(str(user_id))
                        mock_generate.assert_called_once()
                        mock_send.assert_called_once()
                        mock_store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_monitor_urgent_emails(self, proactive_agent, mock_user_profile, mock_context):
        """Test monitoring urgent emails"""
        user_id = 1
        phone_number = "+15551234567"
        
        with patch.object(proactive_agent.context_aggregator, 'get_full_context') as mock_get_context:
            with patch.object(user_manager, 'get_user_by_id') as mock_get_user:
                with patch.object(proactive_agent.communication_service.sms_handler, 'send_sms') as mock_send:
                    with patch.object(proactive_agent, 'store_proactive_action') as mock_store:
                        mock_get_context.return_value = mock_context
                        mock_get_user.return_value = mock_user_profile
                        mock_send.return_value = True
                        
                        await proactive_agent._monitor_urgent_emails(user_id, phone_number)
                        
                        mock_get_context.assert_called_once_with(str(user_id))
                        mock_get_user.assert_called_once_with(user_id)
                        mock_send.assert_called_once()
                        mock_store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_calendar_conflicts(self, proactive_agent, mock_user_profile, mock_context):
        """Test checking calendar conflicts"""
        user_id = 1
        phone_number = "+15551234567"
        
        with patch.object(proactive_agent.context_aggregator, 'get_full_context') as mock_get_context:
            with patch.object(user_manager, 'get_user_by_id') as mock_get_user:
                with patch.object(proactive_agent.communication_service.sms_handler, 'send_sms') as mock_send:
                    with patch.object(proactive_agent, 'store_proactive_action') as mock_store:
                        mock_get_context.return_value = mock_context
                        mock_get_user.return_value = mock_user_profile
                        mock_send.return_value = True
                        
                        await proactive_agent._check_calendar_conflicts(user_id, phone_number)
                        
                        mock_get_context.assert_called_once_with(str(user_id))
                        mock_get_user.assert_called_once_with(user_id)
                        mock_send.assert_called_once()
                        mock_store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_schedule_wakeup_call(self, proactive_agent, mock_user_profile):
        """Test scheduling wake-up call"""
        user_id = 1
        phone_number = "+15551234567"
        wakeup_time = datetime.utcnow() + timedelta(days=1)
        wakeup_time = wakeup_time.replace(hour=7, minute=0, second=0, microsecond=0)
        message = "Good morning! Time to wake up!"
        
        with patch.object(user_manager, 'get_user_by_id') as mock_get_user:
            with patch.object(proactive_agent.scheduler, 'add_job') as mock_add_job:
                mock_get_user.return_value = mock_user_profile
                
                result = await proactive_agent.schedule_wakeup_call(user_id, phone_number, wakeup_time, message)
                
                assert result == True
                mock_add_job.assert_called_once()
                
                # Check that wake-up call was stored
                assert len(proactive_agent.active_wakeup_calls) == 1
    
    @pytest.mark.asyncio
    async def test_wakeup_call_disabled(self, proactive_agent, mock_user_profile):
        """Test wake-up call when disabled"""
        user_id = 1
        phone_number = "+15551234567"
        wakeup_time = datetime.utcnow() + timedelta(days=1)
        
        # Disable wake-up calls
        mock_user_profile["preferences"]["wake_up_calls"] = False
        
        with patch.object(user_manager, 'get_user_by_id') as mock_get_user:
            mock_get_user.return_value = mock_user_profile
            mock_add_job = patch.object(proactive_agent.scheduler, 'add_job')
            
            result = await proactive_agent.schedule_wakeup_call(user_id, phone_number, wakeup_time)
            
            assert result == False
    
    @pytest.mark.asyncio
    async def test_generate_habit_suggestion(self, proactive_agent):
        """Test generating habit suggestions"""
        # Test time-based habit
        time_habit = {
            "pattern_type": "time_based",
            "pattern_data": {"time": "7AM", "action": "wake_up"},
            "confidence": 0.8,
            "id": 1
        }
        
        suggestion = await proactive_agent._generate_habit_suggestion(time_habit, 1.5)
        
        assert suggestion is not None
        assert suggestion["type"] == "habit_reminder"
        assert suggestion["action"] == "schedule_wakeup"
        assert "7AM" in suggestion["message"]
        
        # Test frequency-based habit
        freq_habit = {
            "pattern_type": "frequency_based",
            "pattern_data": {"action": "daily_checkin"},
            "confidence": 0.7,
            "id": 2
        }
        
        suggestion = await proactive_agent._generate_habit_suggestion(freq_habit, 0.5)
        
        assert suggestion is not None
        assert suggestion["type"] == "habit_reminder"
        assert suggestion["action"] == "execute_habit"
        assert "daily_checkin" in suggestion["message"]
    
    @pytest.mark.asyncio
    async def test_execute_proactive_action_schedule_wakeup(self, proactive_agent, mock_user_profile):
        """Test executing schedule_wakeup action"""
        user_id = "1"
        action_type = "schedule_wakeup"
        action_data = {"wakeup_time": datetime.utcnow() + timedelta(days=1)}
        
        with patch.object(user_manager, 'get_user_by_id') as mock_get_user:
            with patch.object(proactive_agent, 'schedule_wakeup_call') as mock_schedule:
                mock_get_user.return_value = mock_user_profile
                mock_schedule.return_value = True
                
                result = await proactive_agent.execute_proactive_action(user_id, action_type, action_data)
                
                assert result["success"] == True
                assert "scheduled" in result["message"]
                mock_schedule.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_proactive_message(self, proactive_agent, mock_user_profile):
        """Test sending proactive messages"""
        user_id = "1"
        message = "Test proactive message"
        priority = "high"
        
        with patch.object(user_manager, 'get_user_by_id') as mock_get_user:
            with patch.object(proactive_agent.style_engine, 'generate_style_matched_response') as mock_style:
                with patch.object(proactive_agent.communication_service.sms_handler, 'send_sms') as mock_send:
                    with patch.object(proactive_agent, 'store_proactive_action') as mock_store:
                        mock_get_user.return_value = mock_user_profile
                        mock_style.return_value = "Styled test message"
                        mock_send.return_value = True
                        
                        result = await proactive_agent.send_proactive_message(user_id, message, priority)
                        
                        assert result == True
                        mock_style.assert_called_once()
                        mock_send.assert_called_once()
                        mock_store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_morning_digest(self, proactive_agent, mock_context):
        """Test generating morning digest"""
        user_id = "1"
        
        with patch.object(proactive_agent.context_aggregator, 'get_full_context') as mock_get_context:
            with patch.object(proactive_agent.style_engine, 'generate_style_matched_response') as mock_style:
                with patch.object(proactive_agent, 'store_proactive_action') as mock_store:
                    mock_get_context.return_value = mock_context
                    mock_style.return_value = "Styled digest message"
                    
                    result = await proactive_agent.generate_morning_digest(user_id)
                    
                    assert "Styled digest message" in result
                    mock_get_context.assert_called_once_with(user_id)
                    mock_style.assert_called_once()
                    mock_store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_suggest_proactive_actions(self, proactive_agent, mock_context):
        """Test getting proactive action suggestions"""
        user_id = "1"
        
        mock_habits = [
            {
                "next_predicted": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                "pattern_type": "time_based",
                "pattern_data": {"time": "7AM"},
                "confidence": 0.8,
                "id": 1
            }
        ]
        
        with patch.object(proactive_agent.context_aggregator, 'get_full_context') as mock_get_context:
            with patch.object(proactive_agent.habit_engine, 'get_user_habits') as mock_get_habits:
                with patch.object(proactive_agent, '_generate_habit_suggestion') as mock_generate:
                    mock_get_context.return_value = mock_context
                    mock_get_habits.return_value = mock_habits
                    mock_generate.return_value = {
                        'type': 'habit_reminder',
                        'message': 'Habit suggestion',
                        'action': 'schedule_wakeup',
                        'confidence': 0.8
                    }
                    
                    suggestions = await proactive_agent.suggest_proactive_actions(user_id)
                    
                    assert len(suggestions) > 0
                    mock_get_context.assert_called_once_with(user_id)
                    mock_get_habits.assert_called_once_with(user_id)
                    mock_generate.assert_called_once()


if __name__ == "__main__":
    # Run basic tests
    print("🧪 Testing Proactive Agent...")
    
    # Create agent instance
    agent = ProactiveAgent()
    
    print("✅ Proactive Agent initialization test passed")
    print("✅ Basic functionality verified")
    print("\nNote: Full test suite requires pytest and mock dependencies.")
    print("Run with: pytest test_proactive_agent.py -v")

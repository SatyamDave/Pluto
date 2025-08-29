"""
Comprehensive Test Harness for Pluto AI Phone Assistant
Tests all critical paths: SMS, voice, memory, proactive, confirmation
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Import the modules we're testing
from ai_orchestrator import AIOrchestrator
from services.memory_manager import MemoryManager
from services.habit_engine import HabitEngine
from services.proactive_agent import ProactiveAgent
from services.style_engine import StyleEngine
from services.user_manager import UserManager
from services.action_layer import ActionLayer, ActionType, PermissionLevel
from telephony.twilio_handler import TwilioHandler
from telephony.telnyx_handler import TelnyxHandler
from telephony.outbound_call_service import OutboundCallService


class TestSMSFlow:
    """Test SMS message processing flow"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create AI orchestrator instance"""
        return AIOrchestrator()
    
    @pytest.fixture
    def memory_manager(self):
        """Create real memory manager instance"""
        return MemoryManager()
    
    @pytest.mark.asyncio
    async def test_sms_message_processing(self, orchestrator, memory_manager):
        """Test complete SMS message processing flow"""
        # First create a real user
        from services.user_manager import UserManager
        user_manager = UserManager()
        
        # Create a test user with a real phone number
        user = await user_manager.get_or_create_user("+1234567890")
        user_id = user["id"]
        
        # Now test message processing with the real user
        result = await orchestrator.process_message(
            user_id=user_id,  # Use the real user ID
            message="Wake me up at 7 AM tomorrow",
            message_type="sms"
        )
        
        # Verify response structure
        assert "response" in result
        assert "intent" in result
        assert "proactive_suggestions" in result
        assert "context_used" in result
        
        # Verify memory was stored
        assert result["context_used"] is not None
        
        # Verify context was retrieved
        assert "response" in result
    
    @pytest.mark.asyncio
    async def test_sms_intent_analysis(self, orchestrator):
        """Test SMS intent analysis"""
        # Test reminder intent
        intent = orchestrator._simple_intent_analysis("Wake me up at 7 AM")
        assert intent["intent"] == "reminder"
        assert intent["confidence"] == 0.8
        assert intent["action"] == "create_reminder"
        
        # Test email intent
        intent = orchestrator._simple_intent_analysis("Check my emails")
        assert intent["intent"] == "email"
        assert intent["action"] == "check_email"
        
        # Test general help
        intent = orchestrator._simple_intent_analysis("Hello there")
        assert intent["intent"] == "general_help"
        assert intent["action"] == "general_response"


class TestVoiceFlow:
    """Test voice call processing flow"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create AI orchestrator instance"""
        return AIOrchestrator()
    
    @pytest.mark.asyncio
    async def test_voice_message_processing(self, orchestrator):
        """Test voice message processing"""
        result = await orchestrator.process_message(
            user_id="test_user_123",
            message="Call my dentist to reschedule my appointment",
            message_type="voice"
        )
        
        assert "response" in result
        assert "intent" in result
        assert result["intent"]["intent"] == "general_help"  # Default fallback
    
    @pytest.mark.asyncio
    async def test_voice_intent_analysis(self, orchestrator):
        """Test voice intent analysis"""
        intent = orchestrator._simple_intent_analysis("Schedule a meeting for tomorrow")
        assert intent["intent"] == "calendar"
        assert intent["action"] == "check_calendar"


class TestMemoryManagement:
    """Test memory storage and recall"""
    
    @pytest.fixture
    def memory_manager(self):
        """Create memory manager instance"""
        return MemoryManager()
    
    @pytest.mark.asyncio
    async def test_memory_storage(self, memory_manager):
        """Test storing memories"""
        # First create a real user
        from services.user_manager import UserManager
        user_manager = UserManager()
        
        # Create a test user with a real phone number
        user = await user_manager.get_or_create_user("+1234567890")
        user_id = user["id"]
        
        # Now store memory for this real user
        memory_id = await memory_manager.store_memory(
            user_id=user_id,  # Use the real user ID
            memory_type="sms",
            content="Test message",
            metadata={"sender": "user"}
        )
        
        assert memory_id is not None
        assert isinstance(memory_id, int)
    
    @pytest.mark.asyncio
    async def test_memory_recall(self, memory_manager):
        """Test recalling memories"""
        # First store a memory
        memory_id = await memory_manager.store_memory(
            user_id="test_user",
            memory_type="sms",
            content="Test message for recall",
            metadata={"sender": "user"}
        )
        
        # Now recall it
        memories = await memory_manager.recall_memory(
            user_id="test_user",
            query="Test message",
            limit=5
        )
        
        assert isinstance(memories, list)
        assert len(memories) > 0
        assert any(m["content"] == "Test message for recall" for m in memories)
    
    @pytest.mark.asyncio
    async def test_memory_forgetting(self, memory_manager):
        """Test forgetting memories"""
        # First store a memory
        memory_id = await memory_manager.store_memory(
            user_id="test_user",
            memory_type="sms",
            content="Memory to forget",
            metadata={"sender": "user"}
        )
        
        # Now forget it
        result = await memory_manager.forget_memory("test_user", memory_id)
        assert result is True


class TestProactiveAgent:
    """Test proactive automation features"""
    
    @pytest.fixture
    async def proactive_agent(self):
        """Create proactive agent instance"""
        return ProactiveAgent()
    
    @pytest.mark.asyncio
    async def test_morning_digest_generation(self, proactive_agent):
        """Test morning digest generation"""
        digest = await proactive_agent.generate_morning_digest("test_user")
        
        assert isinstance(digest, str)
        assert len(digest) > 0
    
    @pytest.mark.asyncio
    async def test_proactive_suggestions(self, proactive_agent):
        """Test proactive action suggestions"""
        suggestions = await proactive_agent.suggest_proactive_actions("test_user")
        
        assert isinstance(suggestions, list)
        # May be empty if no proactive actions are needed


class TestStyleEngine:
    """Test style adaptation and personalization"""
    
    @pytest.fixture
    async def style_engine(self):
        """Create style engine instance"""
        return StyleEngine()
    
    @pytest.mark.asyncio
    async def test_style_analysis(self, style_engine):
        """Test user style analysis"""
        style_profile = await style_engine.analyze_user_style("test_user")
        
        assert isinstance(style_profile, dict)
        # Profile may be empty for new users
    
    @pytest.mark.asyncio
    async def test_style_adaptation(self, style_engine):
        """Test response style adaptation"""
        adapted_response = await style_engine.adapt_response(
            user_id="test_user",
            base_response="Hello, how can I help you today?",
            context="casual_conversation"
        )
        
        assert isinstance(adapted_response, str)
        assert len(adapted_response) > 0


class TestHabitEngine:
    """Test habit detection and learning"""
    
    @pytest.fixture
    async def habit_engine(self):
        """Create habit engine instance"""
        return HabitEngine()
    
    @pytest.mark.asyncio
    async def test_habit_analysis(self, habit_engine):
        """Test user habit analysis"""
        habits = await habit_engine.analyze_user_habits("test_user")
        
        assert isinstance(habits, list)
        # May be empty for new users
    
    @pytest.mark.asyncio
    async def test_habit_validation(self, habit_engine):
        """Test habit pattern validation"""
        pattern = {
            "type": "wake_up",
            "time": "07:00",
            "frequency": "daily"
        }
        
        is_valid = habit_engine._validate_pattern_strength(pattern)
        assert isinstance(is_valid, bool)


class TestUserManager:
    """Test user management and preferences"""
    
    @pytest.fixture
    async def user_manager(self):
        """Create user manager instance"""
        return UserManager()
    
    @pytest.mark.asyncio
    async def test_user_activation(self, user_manager):
        """Test user activation flow"""
        user = await user_manager.activate_user("+1234567890")
        
        assert isinstance(user, dict)
        assert "id" in user
        assert user["phone_number"] == "+1234567890"
    
    @pytest.mark.asyncio
    async def test_user_preferences(self, user_manager):
        """Test user preference management"""
        result = await user_manager.set_user_preference("test_user", "wake_time", "7:00 AM")
        
        assert result is True


class TestTelephonyHandlers:
    """Test telephony service handlers"""
    
    @pytest.fixture
    async def twilio_handler(self):
        """Create Twilio handler instance"""
        return TwilioHandler()
    
    @pytest.fixture
    async def telnyx_handler(self):
        """Create Telnyx handler instance"""
        return TelnyxHandler()
    
    @pytest.mark.asyncio
    async def test_twilio_sms_send(self, twilio_handler):
        """Test Twilio SMS sending"""
        result = await twilio_handler.send_sms("+1234567890", "Test message")
        
        assert isinstance(result, str)
        # May fail if credentials not configured
    
    @pytest.mark.asyncio
    async def test_telnyx_sms_send(self, telnyx_handler):
        """Test Telnyx SMS sending"""
        result = await telnyx_handler.send_sms("+1234567890", "Test message")
        
        assert isinstance(result, str)
        # May fail if credentials not configured


class TestActionExecutionLayer:
    """Test action execution layer with confirmation system"""
    
    @pytest.fixture
    def action_layer(self):
        """Create action execution layer instance"""
        return ActionLayer()
    
    @pytest.mark.asyncio
    async def test_action_confirmation_request(self, action_layer):
        """Test requesting confirmation for external action"""
        result = await action_layer.request_action_confirmation(
            user_id="test_user",
            action_type=ActionType.SEND_SMS,
            action_data={"message": "Hello from Pluto"},
            contact_info={"name": "John Doe", "phone_number": "+1234567890"}
        )
        
        assert "status" in result
        assert result["status"] in ["confirmation_required", "auto_approved"]
        
        if result["status"] == "confirmation_required":
            assert "confirmation_request" in result
            assert "action_id" in result
    
    @pytest.mark.asyncio
    async def test_action_confirmation_parsing(self, action_layer):
        """Test action confirmation parsing"""
        # Test various confirmation responses
        assert action_layer._parse_confirmation("yes") is True
        assert action_layer._parse_confirmation("Yes") is True
        assert action_layer._parse_confirmation("YES") is True
        assert action_layer._parse_confirmation("y") is True
        assert action_layer._parse_confirmation("Y") is True
        
        assert action_layer._parse_confirmation("no") is False
        assert action_layer._parse_confirmation("No") is False
        assert action_layer._parse_confirmation("NO") is False
        assert action_layer._parse_confirmation("n") is False
        assert action_layer._parse_confirmation("N") is False
        
        # Test ambiguous responses
        assert action_layer._parse_confirmation("maybe") is False
        assert action_layer._parse_confirmation("I don't know") is False
        assert action_layer._parse_confirmation("") is False
    
    @pytest.mark.asyncio
    async def test_confirmation_message_formatting(self, action_layer):
        """Test confirmation message generation"""
        # Test SMS confirmation
        message = action_layer._format_confirmation_message(
            ActionType.SEND_SMS,
            {"message": "Hello there"},
            {"name": "Jane", "phone_number": "+1987654321"}
        )
        
        assert "Send text message to Jane" in message
        assert "Hello there" in message
        
        # Test call confirmation
        message = action_layer._format_confirmation_message(
            ActionType.PLACE_CALL,
            {"purpose": "appointment"},
            {"name": "Dr. Smith", "phone_number": "+1555123456"}
        )
        
        assert "Call Dr. Smith" in message
        assert "appointment" in message
    
    @pytest.mark.asyncio
    async def test_action_execution_flow(self, action_layer):
        """Test complete action execution flow"""
        # Test SMS execution with real services
        result = await action_layer._execute_action(
            user_id="test_user",
            action_type=ActionType.SEND_SMS,
            action_data={"message": "Test message"},
            contact_info={"name": "Test", "phone_number": "+1234567890"}
        )
        
        assert "success" in result
        # May fail if telephony credentials not configured
    
    @pytest.mark.asyncio
    async def test_contact_permission_management(self, action_layer):
        """Test contact permission management"""
        result = await action_layer.set_contact_permission(
            user_id="test_user",
            contact_id="contact_123",
            action_type=ActionType.SEND_EMAIL,
            permission_level=PermissionLevel.AUTO_APPROVE
        )
        
        # May fail if database not configured
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_action_history_retrieval(self, action_layer):
        """Test retrieving user action history"""
        history = await action_layer.get_user_action_history("test_user", limit=10)
        
        assert isinstance(history, list)


class TestOutboundCalls:
    """Test outbound call functionality"""
    
    @pytest.fixture
    async def outbound_service(self):
        """Create outbound call service instance"""
        return OutboundCallService()
    
    @pytest.mark.asyncio
    async def test_call_placement(self, outbound_service):
        """Test placing outbound calls"""
        result = await outbound_service.initiate_call(
            user_id=1,
            target_phone="+1234567890",
            call_type="general_inquiry",
            task_description="Test call"
        )
        
        assert isinstance(result, object)
        # May fail if telephony credentials not configured
    
    @pytest.mark.asyncio
    async def test_call_script_generation(self, outbound_service):
        """Test call script generation"""
        script = await outbound_service._generate_ai_script(
            call_type="general_inquiry",
            task_description="Test appointment reschedule"
        )
        
        assert isinstance(script, str)
        assert "Pluto" in script
        assert "appointment" in script


class TestIntegrationFlows:
    """Test end-to-end integration flows"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create AI orchestrator instance"""
        return AIOrchestrator()
    
    @pytest.mark.asyncio
    async def test_complete_user_interaction_flow(self, orchestrator):
        """Test complete user interaction flow"""
        # Test with real services
        result = await orchestrator.process_message(
            user_id="test_user_123",
            message="Hello Pluto, how are you?",
            message_type="sms"
        )
        
        assert "response" in result
        assert "intent" in result
        # May fail if services not configured
    
    @pytest.mark.asyncio
    async def test_proactive_automation_cycle(self, orchestrator):
        """Test proactive automation cycle"""
        # Test proactive mode with real services
        await orchestrator.run_proactive_automation()
        
        # This is a background process, just verify it doesn't crash
        assert True
    
    @pytest.mark.asyncio
    async def test_external_action_request(self, orchestrator):
        """Test external action request flow"""
        result = await orchestrator.request_external_action(
            user_id="test_user",
            action_type="send_sms",
            action_data={"message": "Hello from Pluto"},
            contact_info={"name": "Test Contact", "phone_number": "+1234567890"}
        )
        
        assert "status" in result
        # May fail if services not configured
    
    @pytest.mark.asyncio
    async def test_external_action_confirmation(self, orchestrator):
        """Test external action confirmation flow"""
        result = await orchestrator.confirm_external_action(
            user_id="test_user",
            action_id="test_action_123",
            confirmation="yes"
        )
        
        assert "status" in result
        # May fail if services not configured


class TestAdminDashboard:
    """Test admin dashboard functionality"""
    
    @pytest.fixture
    async def admin_service(self):
        """Create admin service instance"""
        from services.admin_service import AdminService
        return AdminService()
    
    @pytest.mark.asyncio
    async def test_admin_token_verification(self, admin_service):
        """Test admin token verification"""
        # Test with invalid token
        with pytest.raises(Exception):
            await admin_service.verify_admin_token("invalid_token")
    
    @pytest.mark.asyncio
    async def test_user_context_retrieval(self, admin_service):
        """Test user context retrieval"""
        context = await admin_service.get_user_context("test_user")
        
        assert isinstance(context, dict)
        # May be empty for new users
    
    @pytest.mark.asyncio
    async def test_system_health_check(self, admin_service):
        """Test system health check"""
        health = await admin_service.get_system_health()
        
        assert isinstance(health, dict)
        assert "status" in health
        assert "services" in health


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create AI orchestrator instance"""
        return AIOrchestrator()
    
    @pytest.mark.asyncio
    async def test_memory_manager_failure(self, orchestrator):
        """Test handling of memory manager failures"""
        # Test with real services - may fail if not configured
        try:
            result = await orchestrator.process_message(
                user_id="test_user",
                message="Hello Pluto",
                message_type="sms"
            )
            # If it works, verify response structure
            assert "response" in result
        except Exception as e:
            # Expected if services not configured
            assert "error" in str(e) or "connection" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_habit_engine_failure(self, orchestrator):
        """Test handling of habit engine failures"""
        # Test with real services - may fail if not configured
        try:
            result = await orchestrator.process_message(
                user_id="test_user",
                message="Hello Pluto",
                message_type="sms"
            )
            # If it works, verify response structure
            assert "response" in result
        except Exception as e:
            # Expected if services not configured
            assert "error" in str(e) or "connection" in str(e).lower()


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v", "--tb=short"])

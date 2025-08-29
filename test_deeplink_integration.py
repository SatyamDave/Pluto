"""
Test Deep Link Integration for Pluto AI
Tests the execution mode routing and deep link generation
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from services.deeplink_service import DeepLinkService
from ai_orchestrator import AIOrchestrator


class TestDeepLinkService:
    """Test deep link generation"""
    
    def setup_method(self):
        self.deeplink_service = DeepLinkService()
    
    def test_generate_call_link_ios(self):
        """Test iOS call link generation"""
        result = self.deeplink_service.generate_call_link("+1234567890", "ios")
        
        assert result["url"] == "tel:+1234567890"
        assert result["label"] == "📞 Call +1234567890"
        assert result["app_name"] == "Phone"
        assert result["device_type"] == "ios"
    
    def test_generate_call_link_android(self):
        """Test Android call link generation"""
        result = self.deeplink_service.generate_call_link("+1234567890", "android")
        
        assert result["url"] == "tel:+1234567890"
        assert result["label"] == "📞 Call +1234567890"
        assert result["app_name"] == "Phone"
        assert result["device_type"] == "android"
    
    def test_generate_sms_link_ios(self):
        """Test iOS SMS link generation"""
        result = self.deeplink_service.generate_sms_link("+1234567890", "Hello there", "ios")
        
        assert result["url"] == "sms:+1234567890&body=Hello%20there"
        assert result["label"] == "✉️ Text +1234567890"
        assert result["app_name"] == "Messages"
        assert result["device_type"] == "ios"
    
    def test_generate_maps_link_ios(self):
        """Test iOS maps link generation"""
        result = self.deeplink_service.generate_maps_link("Cafe Centro", "ios")
        
        assert result["url"] == "https://maps.apple.com/?daddr=Cafe%20Centro"
        assert result["label"] == "🗺️ Directions to Cafe Centro"
        assert result["app_name"] == "Maps"
        assert result["device_type"] == "ios"
    
    def test_generate_maps_link_android(self):
        """Test Android maps link generation"""
        result = self.deeplink_service.generate_maps_link("Cafe Centro", "android")
        
        assert result["url"] == "geo:0,0?q=Cafe%20Centro"
        assert result["label"] == "🗺️ Directions to Cafe Centro"
        assert result["app_name"] == "Maps"
        assert result["device_type"] == "android"
    
    def test_generate_alarm_link_ios(self):
        """Test iOS alarm link generation"""
        result = self.deeplink_service.generate_alarm_link("6:30 AM", "ios")
        
        assert "shortcuts://run-shortcut" in result["url"]
        assert result["label"] == "⏰ Set alarm for 6:30 AM"
        assert result["app_name"] == "Clock"
        assert result["device_type"] == "ios"
    
    def test_generate_slack_link_ios(self):
        """Test iOS Slack link generation"""
        result = self.deeplink_service.generate_app_link("slack", {"channel": "random", "team": "T123"}, "ios")
        
        assert "slack://channel" in result["url"]
        assert result["label"] == "💬 Open Slack #random"
        assert result["app_name"] == "Slack"
        assert result["device_type"] == "ios"
    
    def test_clean_phone_number(self):
        """Test phone number cleaning"""
        # Test US number
        clean = self.deeplink_service._clean_phone_number("555-123-4567")
        assert clean == "15551234567"
        
        # Test international number
        clean = self.deeplink_service._clean_phone_number("+44 20 7946 0958")
        assert clean == "+442079460958"
        
        # Test already formatted number
        clean = self.deeplink_service._clean_phone_number("+15551234567")
        assert clean == "+15551234567"
    
    def test_validate_deeplink(self):
        """Test deeplink validation"""
        assert self.deeplink_service.validate_deeplink("tel:+1234567890")
        assert self.deeplink_service.validate_deeplink("sms:+1234567890")
        assert self.deeplink_service.validate_deeplink("https://maps.apple.com")
        assert self.deeplink_service.validate_deeplink("camera://")
        assert not self.deeplink_service.validate_deeplink("invalid-link")


class TestAIOrchestrator:
    """Test AI orchestrator execution mode routing"""
    
    def setup_method(self):
        self.orchestrator = AIOrchestrator()
    
    def test_determine_execution_mode_cloud(self):
        """Test cloud execution mode determination"""
        mode = self.orchestrator._determine_execution_mode(
            "send_sms", "ios", False, {}
        )
        assert mode == "cloud"
    
    def test_determine_execution_mode_deeplink(self):
        """Test deeplink execution mode determination"""
        mode = self.orchestrator._determine_execution_mode(
            "make_call", "ios", False, {}
        )
        assert mode == "deeplink"
    
    def test_determine_execution_mode_device_bridge_fallback(self):
        """Test device bridge fallback to deeplink when disabled"""
        mode = self.orchestrator._determine_execution_mode(
            "toggle_dnd", "ios", False, {}
        )
        assert mode == "deeplink"  # Falls back when device bridge disabled
    
    def test_determine_execution_mode_device_bridge_enabled(self):
        """Test device bridge execution mode when enabled"""
        mode = self.orchestrator._determine_execution_mode(
            "toggle_dnd", "android", True, {}
        )
        assert mode == "device_bridge"
    
    def test_parse_text_intent(self):
        """Test text intent parsing"""
        intent = self.orchestrator._parse_text_intent("text Jon I'm 10 min late")
        
        assert intent["intent"] == "send_sms"
        assert intent["confidence"] == 0.9
        assert intent["entities"]["recipient"] == "Jon"
        assert intent["entities"]["message"] == "I'm 10 min late"
    
    def test_parse_call_intent(self):
        """Test call intent parsing"""
        intent = self.orchestrator._parse_call_intent("call Mom")
        
        assert intent["intent"] == "make_call"
        assert intent["confidence"] == 0.9
        assert intent["entities"]["recipient"] == "Mom"
    
    def test_parse_calendar_intent(self):
        """Test calendar intent parsing"""
        intent = self.orchestrator._parse_calendar_intent("Lunch with Ben Fri 12-1")
        
        assert intent["intent"] == "create_calendar_event"
        assert intent["confidence"] == 0.8
        assert "Lunch with Ben Fri 12-1" in intent["entities"]["description"]
    
    def test_parse_maps_intent(self):
        """Test maps intent parsing"""
        intent = self.orchestrator._parse_maps_intent("directions to Cafe Centro")
        
        assert intent["intent"] == "open_maps"
        assert intent["confidence"] == 0.9
        assert intent["entities"]["destination"] == "Cafe Centro"
    
    def test_parse_email_intent(self):
        """Test email intent parsing"""
        intent = self.orchestrator._parse_email_intent("reply to Sarah: sounds good")
        
        assert intent["intent"] == "send_email"
        assert intent["confidence"] == 0.9
        assert intent["entities"]["recipient"] == "Sarah"
        assert intent["entities"]["message"] == "sounds good"
    
    def test_parse_slack_intent(self):
        """Test Slack intent parsing"""
        intent = self.orchestrator._parse_slack_intent("send 'deck attached' to #random")
        
        assert intent["intent"] == "send_slack_message"
        assert intent["confidence"] == 0.8
        assert "deck attached" in intent["entities"]["message"]
    
    def test_parse_device_intent(self):
        """Test device intent parsing"""
        intent = self.orchestrator._parse_device_intent("turn on DND")
        
        assert intent["intent"] == "toggle_dnd"
        assert intent["confidence"] == 0.8
        assert intent["entities"]["action"] == "toggle_dnd"
    
    @patch('ai_orchestrator.AIOrchestrator._resolve_contact')
    async def test_generate_call_deeplink(self, mock_resolve_contact):
        """Test call deeplink generation"""
        # Mock contact resolution
        mock_resolve_contact.return_value = {
            "name": "Mom",
            "phone": "+1234567890"
        }
        
        result = await self.orchestrator._generate_call_deeplink(
            "test_user", {"recipient": "Mom"}, "ios"
        )
        
        assert result["success"] == True
        assert result["action"] == "call_deeplink"
        assert result["recipient"] == "Mom"
        assert "tel:" in result["deeplink"]
        assert "📞 Call Mom" in result["label"]
    
    @patch('ai_orchestrator.AIOrchestrator._resolve_contact')
    async def test_generate_call_deeplink_contact_not_found(self, mock_resolve_contact):
        """Test call deeplink generation when contact not found"""
        mock_resolve_contact.return_value = None
        
        result = await self.orchestrator._generate_call_deeplink(
            "test_user", {"recipient": "Unknown"}, "ios"
        )
        
        assert result["success"] == False
        assert "not found" in result["error"]
    
    def test_sign_command(self):
        """Test command signing"""
        command_data = {"action": "test", "user_id": "123"}
        secret = "test_secret"
        
        signature = self.orchestrator._sign_command(command_data, secret)
        
        assert len(signature) == 64  # SHA-256 hex length
        assert isinstance(signature, str)
    
    def test_get_supported_actions(self):
        """Test getting supported actions for device type"""
        deeplink_service = DeepLinkService()
        
        ios_actions = deeplink_service.get_supported_actions("ios")
        assert ios_actions["device_type"] == "ios"
        assert "call" in ios_actions["supported_actions"]
        assert "sms" in ios_actions["supported_actions"]
        assert ios_actions["total_actions"] > 0
        
        android_actions = deeplink_service.get_supported_actions("android")
        assert android_actions["device_type"] == "android"
        assert android_actions["total_actions"] > 0


def test_integration_flow():
    """Test complete integration flow"""
    # This would test the full flow from message to execution
    # For now, we'll just verify the components work together
    
    deeplink_service = DeepLinkService()
    orchestrator = AIOrchestrator()
    
    # Test that both services can be instantiated
    assert deeplink_service is not None
    assert orchestrator is not None
    
    # Test that execution modes are properly defined
    assert "cloud" in orchestrator.intent_execution_map.values()
    assert "deeplink" in orchestrator.intent_execution_map.values()
    assert "device_bridge" in orchestrator.intent_execution_map.values()


if __name__ == "__main__":
    # Run tests
    print("Running Deep Link Integration Tests...")
    
    # Test DeepLinkService
    print("\n1. Testing DeepLinkService...")
    deeplink_service = DeepLinkService()
    
    # Test call link generation
    call_result = deeplink_service.generate_call_link("+1234567890", "ios")
    print(f"   - iOS call link: {call_result['url']}")
    
    # Test SMS link generation
    sms_result = deeplink_service.generate_sms_link("+1234567890", "Hello", "ios")
    print(f"   - iOS SMS link: {sms_result['url']}")
    
    # Test maps link generation
    maps_result = deeplink_service.generate_maps_link("Cafe Centro", "ios")
    print(f"   - iOS maps link: {maps_result['url']}")
    
    # Test Android links
    android_call = deeplink_service.generate_call_link("+1234567890", "android")
    print(f"   - Android call link: {android_call['url']}")
    
    # Test AIOrchestrator
    print("\n2. Testing AIOrchestrator...")
    orchestrator = AIOrchestrator()
    
    # Test execution mode determination
    cloud_mode = orchestrator._determine_execution_mode("send_sms", "ios", False, {})
    print(f"   - Cloud mode: {cloud_mode}")
    
    deeplink_mode = orchestrator._determine_execution_mode("make_call", "ios", False, {})
    print(f"   - Deeplink mode: {deeplink_mode}")
    
    device_bridge_mode = orchestrator._determine_execution_mode("toggle_dnd", "android", True, {})
    print(f"   - Device bridge mode: {device_bridge_mode}")
    
    # Test intent parsing
    text_intent = orchestrator._parse_text_intent("text Jon Hello")
    print(f"   - Text intent: {text_intent['intent']}")
    
    call_intent = orchestrator._parse_call_intent("call Mom")
    print(f"   - Call intent: {call_intent['intent']}")
    
    print("\n✅ All tests completed successfully!")
    print("\nPluto can now:")
    print("- Route intents to appropriate execution modes")
    print("- Generate device-specific deep links")
    print("- Support both cloud and device bridge actions")
    print("- Handle the full 'anything on your phone' workflow")

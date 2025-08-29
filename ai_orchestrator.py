"""
Jarvis Phone - AI Personal Assistant
Core AI brain and routing with execution mode support
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import json

from services.memory_manager import memory_manager
from services.habit_engine import habit_engine
from services.style_engine import style_engine
from services.context_aggregator import context_aggregator
from services.user_manager import user_manager
from services.action_layer import ActionLayer, ActionType, PermissionLevel
from services.deeplink_service import DeepLinkService
from services.communication_service import CommunicationService
from telephony.outbound_call_service import OutboundCallService
from utils.logging_config import get_logger
from utils.constants import EXECUTION_MODES, DEVICE_CAPABILITIES
from services.proactive_agent import proactive_agent

logger = get_logger(__name__)


class AIOrchestrator:
    """Pluto's AI Orchestrator - coordinates all AI interactions with memory and habit learning"""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.deeplinks = DeepLinkService()
        self.logger.info("AI Orchestrator initialized")

    async def process_message(
        self,
        user_id: int,
        message: str,
        message_type: str = "sms",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process a user message with memory, habits, and routing to execution mode."""
        try:
            await memory_manager.store_memory(
                user_id=user_id,
                memory_type=message_type,
                content=message,
                metadata=context or {},
            )

            recent_context = await memory_manager.get_recent_context(user_id, limit=5)
            user_preferences = await memory_manager.get_user_preferences(user_id)

            intent = await self._analyze_intent_with_context(message, recent_context, user_preferences)
            intent, exec_mode = self._decide_execution_mode(intent, user_preferences)

            # Proactive suggestions (not blocking)
            proactive_suggestions = await proactive_agent.suggest_proactive_actions(user_id)

            # Route to action layer or deep link
            routed = await self._route_intent(user_id, intent, exec_mode, user_preferences)

            # Store the response
            await memory_manager.store_memory(
                user_id=user_id,
                memory_type="response",
                content=routed.get("user_text", ""),
                metadata={"intent": intent, "exec_mode": exec_mode, "proactive_count": len(proactive_suggestions)},
            )

            if len(recent_context) % 10 == 0:
                await habit_engine.analyze_user_habits(user_id)

            return {
                "status": "ok",
                "intent": intent,
                "exec_mode": exec_mode,
                "result": routed,
                "response": routed.get("user_text", "I'm not sure how to help with that yet."),
                "proactive_suggestions": proactive_suggestions,
                "context_used": len(recent_context),
            }
        except Exception as e:
            self.logger.error(f"Error processing message: {e}", exc_info=True)
            return {"status": "error", "response": "I'm having trouble processing that right now."}

    async def _analyze_intent_with_context(
        self,
        message: str,
        recent_context: List[Dict[str, Any]],
        user_preferences: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze intent with recent context and user preferences."""
        try:
            # Use OpenRouter for real AI intent analysis
            from services.openrouter_service import analyze_intent_with_openrouter
            
            # Build context for the AI
            context_parts = []
            if recent_context:
                context_parts.append("Recent messages:")
                for ctx in recent_context[-3:]:  # Last 3 messages
                    context_parts.append(f"- {ctx.get('content', '')[:100]}...")
            
            if user_preferences:
                context_parts.append(f"User preferences: {user_preferences}")
            
            context_str = "\n".join(context_parts) if context_parts else "No recent context"
            
            # Analyze with AI
            intent_result = await analyze_intent_with_openrouter(message, context_str)
            
            if intent_result and "intent" in intent_result:
                return intent_result
            else:
                # Fallback to simple rules if AI fails
                self.logger.warning("AI intent analysis failed, using fallback")
                return self._simple_intent_analysis(message)
                
        except Exception as e:
            self.logger.error(f"Error analyzing intent with context: {e}", exc_info=True)
            # Fallback to simple rules
            return self._simple_intent_analysis(message)

    def _decide_execution_mode(self, intent: Dict[str, Any], prefs: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """Choose cloud vs deeplink vs device_bridge based on action + device prefs."""
        device = (prefs or {}).get("device", "unknown")  # ios|android|unknown
        itype = intent.get("intent", "general_help")

        # Cloud-capable intents first
        cloud_intents = {"reminder.create", "reminder.snooze", "calendar.read", "calendar.create",
                         "calendar.move", "email.summarize", "email.reply", "slack.post"}

        # Deeplink-only examples (phone dialer, maps, app schemes)
        deeplink_intents = {"phone.call", "maps.directions", "app.open"}

        if itype in cloud_intents:
            return (intent, "cloud")
        if itype in deeplink_intents:
            return (intent, "deeplink")

        # Device-bridge if enabled
        if (prefs or {}).get("device_bridge_enabled"):
            return (intent, "device_bridge")

        # Default to cloud where possible
        return (intent, "cloud")

    async def _route_intent(
        self,
        user_id: int,
        intent: Dict[str, Any],
        exec_mode: str,
        prefs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute intent via selected mode."""
        itype = intent.get("intent")

        # CLOUD
        if exec_mode == "cloud":
            if itype == "reminder.create":
                return await ActionLayer.create_reminder(user_id, intent)
            if itype == "reminder.snooze":
                return await ActionLayer.snooze_reminder(user_id, intent)
            if itype == "calendar.read":
                return await ActionLayer.calendar_list(user_id, intent)
            if itype == "calendar.create":
                return await ActionLayer.calendar_create(user_id, intent)
            if itype == "calendar.move":
                return await ActionLayer.calendar_move(user_id, intent)
            if itype == "email.summarize":
                return await ActionLayer.email_summarize(user_id, intent)
            if itype == "email.reply":
                return await ActionLayer.email_reply(user_id, intent)
            if itype == "slack.post":
                return await ActionLayer.slack_post(user_id, intent)
            # Fallback
            return {"user_text": "I can set reminders, manage calendar, text people, and summarize email. What next?"}

        # DEEPLINK
        if exec_mode == "deeplink":
            if itype == "phone.call":
                link = self.deeplinks.tel_link(intent.get("phone"))
                return {"user_text": f"📞 Call {intent.get('name','contact')}", "deeplink": link}
            if itype == "maps.directions":
                link = self.deeplinks.maps_link(intent.get("destination"), device=prefs.get("device", "unknown"))
                return {"user_text": "🗺️ Open directions", "deeplink": link}
            if itype == "app.open":
                link = self.deeplinks.app_link(intent.get("app"), intent.get("params", {}), device=prefs.get("device", "unknown"))
                return {"user_text": f"🔗 Open {intent.get('app')}", "deeplink": link}
            return {"user_text": "Here's a link to complete that on your phone.", "deeplink": None}

        # DEVICE BRIDGE (Android Tasker / iOS Shortcuts)
        if exec_mode == "device_bridge":
            payload = ActionLayer.build_device_command(user_id, intent)
            return {"user_text": "📲 Executing on your device…", "device_command": payload}

        return {"user_text": "Not sure how to run that yet—try a reminder, calendar, email, or maps."}

    async def get_user_memory_summary(self, user_id: int) -> Dict[str, Any]:
        try:
            memory_summary = await memory_manager.get_memory_summary(user_id)
            habits = await habit_engine.get_user_habits(user_id)
            preferences = await memory_manager.get_user_preferences(user_id)
            return {
                "memory": memory_summary,
                "habits": {
                    "count": len(habits),
                    "types": list({h["pattern_type"] for h in habits}) if habits else [],
                    "confidence_avg": (sum(h["confidence"] for h in habits) / len(habits)) if habits else 0.0,
                },
                "preferences": {"count": len(preferences), "keys": list(preferences.keys())},
            }
        except Exception as e:
            self.logger.error(f"Error getting memory summary: {e}", exc_info=True)
            return {"error": str(e)}

    async def request_external_action(self, user_id: int, action_type: ActionType,
                                      action_data: Dict[str, Any], contact_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            await memory_manager.store_memory(
                user_id=user_id,
                memory_type="action_request",
                content=f"Requested {action_type.value} action",
                metadata={"action_type": action_type.value, "action_data": action_data, "contact_info": contact_info},
            )
            result = await ActionLayer.request_action_confirmation(user_id, action_type, action_data, contact_info)
            await memory_manager.store_memory(
                user_id=user_id,
                memory_type="action_response",
                content=f"Action {action_type.value} {result.get('status')}",
                metadata={"result": result},
            )
            return result
        except Exception as e:
            self.logger.error(f"Error requesting external action: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    async def confirm_external_action(self, user_id: int, action_id: str, confirmation: str) -> Dict[str, Any]:
        try:
            result = await ActionLayer.confirm_action(user_id, action_id, confirmation)
            await memory_manager.store_memory(
                user_id=user_id,
                memory_type="action_response",
                content=f"Action confirmed: {result.get('status')}",
                metadata={"result": result},
            )
            return result
        except Exception as e:
            self.logger.error(f"Error confirming external action: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    async def get_morning_digest(self, user_id: int) -> str:
        try:
            return await proactive_agent.generate_morning_digest(user_id)
        except Exception as e:
            self.logger.error(f"Error generating morning digest: {e}", exc_info=True)
            return "Good morning! Ready to help you today."

    # ---- Simple fallback NLU ----
    def _simple_intent_analysis(self, message: str) -> Dict[str, Any]:
        m = message.lower()
        # Extremely minimal keyword routing; your LLM can override.
        if any(w in m for w in ["remind", "snooze", "todo", "to-do"]):
            return {"intent": "reminder.create" if "remind" in m else "reminder.snooze", "confidence": 0.7}
        if any(w in m for w in ["calendar", "meeting", "event", "what's today", "what's today", "today", "this week"]):
            if "move" in m or "resched" in m:
                return {"intent": "calendar.move", "confidence": 0.7}
            if any(w in m for w in ["add", "schedule", "create"]):
                return {"intent": "calendar.create", "confidence": 0.7}
            return {"intent": "calendar.read", "confidence": 0.7}
        if any(w in m for w in ["email", "inbox", "reply", "gmail"]):
            return {"intent": "email.reply" if "reply" in m else "email.summarize", "confidence": 0.7}
        if any(w in m for w in ["slack", "#"]):
            return {"intent": "slack.post", "confidence": 0.7}
        if any(w in m for w in ["call", "dial"]):
            return {"intent": "phone.call", "confidence": 0.7, "phone": None}
        if any(w in m for w in ["directions", "navigate", "route"]):
            return {"intent": "maps.directions", "confidence": 0.7, "destination": None}
        if any(w in m for w in ["open", "launch"]):
            return {"intent": "app.open", "confidence": 0.6, "app": None, "params": {}}
        return {"intent": "general_help", "confidence": 0.4}

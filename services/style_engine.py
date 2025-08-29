#!/usr/bin/env python3
"""
Pluto Style Engine
Learns and applies user's personal style and personality
"""

import json
import logging
import re
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from services.memory_manager import memory_manager
from utils.logging_config import get_logger
from utils.constants import STYLE_LEVELS

logger = get_logger(__name__)

class StyleEngine:
    """Pluto's style engine - learns and applies user's personal style"""
    
    def __init__(self):
        self.style_patterns = {
            'emoji_usage': self._analyze_emoji_usage,
            'formality': self._analyze_formality,
            'message_length': self._analyze_message_length,
            'tone': self._analyze_tone,
            'signature_phrases': self._analyze_signature_phrases,
            'communication_style': self._analyze_communication_style
        }
    
    async def analyze_message_style(
        self, 
        user_id: str, 
        message: str, 
        message_type: str = "sms"
    ) -> Dict[str, Any]:
        """
        Analyze a message to learn user's style
        
        Args:
            user_id: User identifier
            message: Message content to analyze
            message_type: Type of message (sms, email, etc.)
            
        Returns:
            Style analysis dictionary
        """
        try:
            style_analysis = {}
            
            # Analyze each style aspect
            for pattern_name, analyzer in self.style_patterns.items():
                style_analysis[pattern_name] = analyzer(message)
            
            # Add metadata
            style_analysis.update({
                'timestamp': datetime.utcnow().isoformat(),
                'message_type': message_type,
                'message_length': len(message)
            })
            
            # Update user's style profile
            await self._update_style_profile(user_id, style_analysis)
            
            # Store style analysis in memory
            await memory_manager.store_memory(
                user_id=user_id,
                memory_type="style_analysis",
                content=f"Style analysis: {json.dumps(style_analysis, indent=2)}",
                metadata=style_analysis,
                importance_score=0.3
            )
            
            logger.info(f"Analyzed style for user {user_id}: {style_analysis}")
            return style_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing message style: {e}")
            return {}
    
    async def generate_style_matched_response(
        self, 
        user_id: str, 
        base_response: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Modify response to match user's style
        
        Args:
            user_id: User identifier
            base_response: Base response to style-match
            context: Optional context for style decisions
            
        Returns:
            Style-matched response
        """
        try:
            # Get user's current style profile
            user_prefs = await memory_manager.get_user_preferences(user_id)
            style_profile = user_prefs.get('style_profile', {})
            
            if not style_profile:
                # No style profile yet, return base response
                return base_response
            
            # Apply style modifications
            styled_response = base_response
            
            # Emoji usage
            if style_profile.get('emoji_usage', True):
                styled_response = self._add_appropriate_emojis(styled_response, context)
            
            # Formality level
            formality_level = style_profile.get('formality_level', 'casual')
            styled_response = self._adjust_formality(styled_response, formality_level)
            
            # Message length
            avg_length = style_profile.get('avg_message_length', 'medium')
            styled_response = self._adjust_message_length(styled_response, avg_length)
            
            # Signature phrases
            signature_phrases = style_profile.get('signature_phrases', [])
            if signature_phrases and self._should_add_signature(context):
                styled_response = self._add_signature_phrase(styled_response, signature_phrases)
            
            # Tone adjustment
            tone_prefs = style_profile.get('tone_preferences', {})
            styled_response = self._adjust_tone(styled_response, tone_prefs)
            
            logger.info(f"Style-matched response for user {user_id}: {len(base_response)} -> {len(styled_response)} chars")
            return styled_response
            
        except Exception as e:
            logger.error(f"Error generating style-matched response: {e}")
            return base_response
    
    async def get_user_style_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user's current style profile"""
        try:
            user_prefs = await memory_manager.get_user_preferences(user_id)
            return user_prefs.get('style_profile', {})
        except Exception as e:
            logger.error(f"Error getting user style profile: {e}")
            return {}
    
    async def update_style_preference(
        self, 
        user_id: str, 
        preference_key: str, 
        value: Any
    ) -> bool:
        """Update a specific style preference"""
        try:
            # Get current style profile
            current_profile = await self.get_user_style_profile(user_id)
            
            # Update the preference
            current_profile[preference_key] = value
            
            # Save updated profile
            return await memory_manager.update_style_profile(user_id, current_profile)
            
        except Exception as e:
            logger.error(f"Error updating style preference: {e}")
            return False
    
    async def get_style_recommendations(self, user_id: str) -> List[str]:
        """Get recommendations for improving style matching"""
        try:
            style_profile = await self.get_user_style_profile(user_id)
            recommendations = []
            
            # Check for missing style data
            if not style_profile.get('emoji_usage'):
                recommendations.append("I'm still learning your emoji preferences. Send me a few more messages!")
            
            if not style_profile.get('signature_phrases'):
                recommendations.append("I haven't learned your signature phrases yet. Keep chatting naturally!")
            
            if not style_profile.get('tone_preferences'):
                recommendations.append("I'm still understanding your tone preferences. More messages will help!")
            
            # Check for style consistency
            if style_profile.get('formality_level') == 'mixed':
                recommendations.append("I notice you use both casual and formal language. This helps me adapt!")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting style recommendations: {e}")
            return []
    
    def _analyze_emoji_usage(self, message: str) -> bool:
        """Analyze if user uses emojis"""
        emoji_pattern = r'[😀-🙏🌀-🗿]'
        return bool(re.findall(emoji_pattern, message))
    
    def _analyze_formality(self, message: str) -> str:
        """Analyze formality level of message"""
        # Formal indicators
        formal_indicators = [
            'please', 'thank you', 'would you', 'could you', 'may i',
            'i would appreciate', 'i am writing to', 'regards', 'sincerely'
        ]
        
        # Casual indicators
        casual_indicators = [
            'hey', 'hi', 'yo', 'whatsup', 'cool', 'awesome', 'yeah', 'yep',
            'gonna', 'wanna', 'gotta', 'lemme', 'imma'
        ]
        
        message_lower = message.lower()
        formal_count = sum(1 for indicator in formal_indicators if indicator in message_lower)
        casual_count = sum(1 for indicator in casual_indicators if indicator in message_lower)
        
        if formal_count > casual_count:
            return 'formal'
        elif casual_count > formal_count:
            return 'casual'
        else:
            return 'mixed'
    
    def _analyze_message_length(self, message: str) -> str:
        """Analyze average message length"""
        word_count = len(message.split())
        
        if word_count <= 5:
            return 'short'
        elif word_count <= 20:
            return 'medium'
        else:
            return 'long'
    
    def _analyze_tone(self, message: str) -> Dict[str, float]:
        """Analyze tone of message"""
        tone_scores = {
            'humor': 0.0,
            'formality': 0.0,
            'enthusiasm': 0.0,
            'urgency': 0.0
        }
        
        message_lower = message.lower()
        
        # Humor indicators
        humor_words = ['haha', 'lol', 'funny', 'joke', 'hilarious', '😄', '😂']
        humor_count = sum(1 for word in humor_words if word in message_lower)
        tone_scores['humor'] = min(1.0, humor_count * 0.3)
        
        # Formality indicators
        formal_words = ['please', 'thank you', 'would you', 'could you']
        formal_count = sum(1 for word in formal_words if word in message_lower)
        tone_scores['formality'] = min(1.0, formal_count * 0.25)
        
        # Enthusiasm indicators
        enthusiasm_words = ['awesome', 'amazing', 'great', 'excellent', 'love', '❤️', '🔥']
        enthusiasm_count = sum(1 for word in enthusiasm_words if word in message_lower)
        tone_scores['enthusiasm'] = min(1.0, enthusiasm_count * 0.3)
        
        # Urgency indicators
        urgency_words = ['urgent', 'asap', 'now', 'quick', 'hurry', '⚡', '🚨']
        urgency_count = sum(1 for word in urgency_words if word in message_lower)
        tone_scores['urgency'] = min(1.0, urgency_count * 0.3)
        
        return tone_scores
    
    def _analyze_signature_phrases(self, message: str) -> List[str]:
        """Analyze signature phrases in message"""
        # Common signature phrases
        signature_patterns = [
            r'\b(on it|yep|got it|sure thing|no problem|absolutely)\b',
            r'\b(thanks|thx|ty|appreciate it)\b',
            r'\b(ok|okay|k|alright|alrighty)\b',
            r'\b(see you|cya|talk to you later|ttul)\b'
        ]
        
        found_phrases = []
        for pattern in signature_patterns:
            matches = re.findall(pattern, message.lower())
            found_phrases.extend(matches)
        
        return list(set(found_phrases))
    
    def _analyze_communication_style(self, message: str) -> str:
        """Analyze overall communication style"""
        # Count different indicators
        indicators = {
            'friendly': ['hi', 'hello', 'hey', 'thanks', 'please', '😊', '🙂'],
            'direct': ['yes', 'no', 'ok', 'sure', 'done', 'got it'],
            'professional': ['regards', 'sincerely', 'best', 'kind regards', 'thank you']
        }
        
        message_lower = message.lower()
        scores = {}
        
        for style, words in indicators.items():
            scores[style] = sum(1 for word in words if word in message_lower)
        
        # Return dominant style
        if scores['professional'] > scores['friendly'] and scores['professional'] > scores['direct']:
            return 'professional'
        elif scores['friendly'] > scores['direct']:
            return 'friendly'
        else:
            return 'direct'
    
    async def _update_style_profile(self, user_id: str, style_analysis: Dict[str, Any]):
        """Update user's style profile with new analysis"""
        try:
            # Get current profile
            current_profile = await self.get_user_style_profile(user_id)
            
            # Update with new analysis
            for key, value in style_analysis.items():
                if key in ['emoji_usage', 'formality_level', 'message_length', 'communication_style']:
                    # Direct values
                    current_profile[key] = value
                elif key == 'tone':
                    # Merge tone preferences
                    if 'tone_preferences' not in current_profile:
                        current_profile['tone_preferences'] = {}
                    
                    for tone_key, tone_value in value.items():
                        if tone_key in current_profile['tone_preferences']:
                            # Average with existing value
                            current = current_profile['tone_preferences'][tone_key]
                            current_profile['tone_preferences'][tone_key] = (current + tone_value) / 2
                        else:
                            current_profile['tone_preferences'][tone_key] = tone_value
                elif key == 'signature_phrases':
                    # Merge signature phrases
                    if 'signature_phrases' not in current_profile:
                        current_profile['signature_phrases'] = []
                    
                    existing_phrases = set(current_profile['signature_phrases'])
                    new_phrases = set(value)
                    current_profile['signature_phrases'] = list(existing_phrases.union(new_phrases))
            
            # Save updated profile
            await memory_manager.update_style_profile(user_id, current_profile)
            
        except Exception as e:
            logger.error(f"Error updating style profile: {e}")
    
    def _add_appropriate_emojis(self, response: str, context: Optional[Dict[str, Any]]) -> str:
        """Add appropriate emojis based on context and response content"""
        emoji_map = {
            'reminder': '⏰',
            'calendar': '📅',
            'email': '📧',
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'question': '❓',
            'exclamation': '❗',
            'heart': '❤️',
            'thumbs_up': '👍',
            'thumbs_down': '👎'
        }
        
        # Add context-appropriate emoji at the end
        if context and context.get('intent'):
            intent = context['intent']
            if intent in emoji_map:
                response += f" {emoji_map[intent]}"
        
        return response
    
    def _adjust_formality(self, response: str, formality_level: str) -> str:
        """Adjust response formality level"""
        if formality_level == 'casual':
            # Make more casual
            replacements = [
                ('I will', "I'll"),
                ('cannot', "can't"),
                ('do not', "don't"),
                ('will not', "won't"),
                ('I am', "I'm"),
                ('you are', "you're")
            ]
            
            for formal, casual in replacements:
                response = response.replace(formal, casual)
        
        elif formality_level == 'formal':
            # Make more formal
            replacements = [
                ("I'll", 'I will'),
                ("can't", 'cannot'),
                ("don't", 'do not'),
                ("won't", 'will not'),
                ("I'm", 'I am'),
                ("you're", 'you are')
            ]
            
            for casual, formal in replacements:
                response = response.replace(casual, formal)
        
        return response
    
    def _adjust_message_length(self, response: str, avg_length: str) -> str:
        """Adjust response length to match user preference"""
        if avg_length == 'short':
            # Keep it concise
            sentences = response.split('.')
            if len(sentences) > 2:
                response = '. '.join(sentences[:2]) + '.'
        
        elif avg_length == 'long':
            # Add more detail if possible
            if len(response.split()) < 20:
                response += " Let me know if you need anything else!"
        
        return response
    
    def _should_add_signature(self, context: Optional[Dict[str, Any]]) -> bool:
        """Determine if we should add a signature phrase"""
        if not context:
            return False
        
        # Add signature for certain intents
        signature_intents = ['reminder', 'calendar', 'email', 'success']
        return context.get('intent') in signature_intents
    
    def _add_signature_phrase(self, response: str, signature_phrases: List[str]) -> str:
        """Add a signature phrase to the response"""
        if not signature_phrases:
            return response
        
        # Choose a random signature phrase
        signature = random.choice(signature_phrases)
        
        # Add with appropriate punctuation
        if response.endswith('.'):
            response = response[:-1] + f", {signature}."
        else:
            response += f" {signature}."
        
        return response
    
    def _adjust_tone(self, response: str, tone_prefs: Dict[str, float]) -> str:
        """Adjust response tone based on user preferences"""
        # Adjust enthusiasm level
        enthusiasm = tone_prefs.get('humor', 0.5)
        if enthusiasm > 0.7:
            # Add some enthusiasm
            if '!' not in response:
                response = response.replace('.', '!', 1)
        
        # Adjust formality based on tone preferences
        formality = tone_prefs.get('formality', 0.5)
        if formality > 0.7:
            response = self._adjust_formality(response, 'formal')
        elif formality < 0.3:
            response = self._adjust_formality(response, 'casual')
        
        return response

# Global style engine instance
style_engine = StyleEngine()

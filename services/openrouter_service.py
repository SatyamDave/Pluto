"""
OpenRouter Service for Jarvis Phone AI Assistant
Provides unified access to hundreds of AI models through a single endpoint
with automatic fallbacks and cost optimization
"""

import logging
import json
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import httpx
from openai import AsyncOpenAI
from config import settings

logger = logging.getLogger(__name__)


class OpenRouterService:
    """Service for accessing OpenRouter API with automatic fallbacks and cost optimization"""
    
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.site_url = settings.BASE_URL
        self.site_name = "Jarvis Phone AI Assistant"
        
        # Initialize OpenAI client for OpenRouter
        self.openai_client = None
        if self.api_key:
            self.openai_client = AsyncOpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
        
        # Model preferences and fallbacks
        self.model_preferences = [
            "openai/gpt-4o",           # Best performance, higher cost
            "openai/gpt-4o-mini",      # Good performance, moderate cost
            "anthropic/claude-3-5-sonnet-20241022",  # Alternative provider
            "anthropic/claude-3-haiku-20240307",     # Fast, cost-effective
            "meta-llama/llama-3.1-8b-instruct",     # Local fallback option
            "google/gemini-pro-1.5"                 # Google's offering
        ]
        
        # Cost tracking
        self.usage_stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "model_usage": {}
        }
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1000,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat completion request with automatic fallbacks
        
        Args:
            messages: List of message dictionaries
            model: Specific model to use (optional)
            temperature: Response randomness (0-2)
            max_tokens: Maximum tokens in response
            stream: Whether to stream the response
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with response data and metadata
        """
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        # Use specified model or try preferred models in order
        models_to_try = [model] if model else self.model_preferences
        
        for model_name in models_to_try:
            try:
                logger.info(f"Attempting chat completion with model: {model_name}")
                
                if self.openai_client:
                    response = await self._chat_with_openai_client(
                        model_name, messages, temperature, max_tokens, stream, **kwargs
                    )
                else:
                    response = await self._chat_with_direct_api(
                        model_name, messages, temperature, max_tokens, stream, **kwargs
                    )
                
                # Track usage
                await self._track_usage(model_name, response)
                
                logger.info(f"Successfully completed chat with {model_name}")
                return response
                
            except Exception as e:
                logger.warning(f"Failed to use model {model_name}: {e}")
                continue
        
        # If all models failed, raise error
        raise Exception("All AI models failed. Please check your configuration and try again.")
    
    async def _chat_with_openai_client(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        stream: bool,
        **kwargs
    ) -> Dict[str, Any]:
        """Use OpenAI client for OpenRouter API"""
        try:
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                extra_headers={
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.site_name,
                },
                **kwargs
            )
            
            if stream:
                return {
                    "model": model,
                    "stream": True,
                    "response": response,
                    "provider": self._extract_provider(model)
                }
            else:
                return {
                    "model": model,
                    "content": response.choices[0].message.content,
                    "usage": response.usage,
                    "provider": self._extract_provider(model),
                    "finish_reason": response.choices[0].finish_reason
                }
                
        except Exception as e:
            logger.error(f"OpenAI client chat completion failed: {e}")
            raise
    
    async def _chat_with_direct_api(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        stream: bool,
        **kwargs
    ) -> Dict[str, Any]:
        """Use direct HTTP requests to OpenRouter API"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": stream,
                    **kwargs
                }
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.site_name,
                    "Content-Type": "application/json"
                }
                
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")
                
                data = response.json()
                
                if stream:
                    return {
                        "model": model,
                        "stream": True,
                        "response": data,
                        "provider": self._extract_provider(model)
                    }
                else:
                    return {
                        "model": model,
                        "content": data["choices"][0]["message"]["content"],
                        "usage": data.get("usage", {}),
                        "provider": self._extract_provider(model),
                        "finish_reason": data["choices"][0].get("finish_reason")
                    }
                    
        except Exception as e:
            logger.error(f"Direct API chat completion failed: {e}")
            raise
    
    def _extract_provider(self, model: str) -> str:
        """Extract provider name from model string"""
        if "/" in model:
            return model.split("/")[0]
        return "unknown"
    
    async def _track_usage(self, model: str, response: Dict[str, Any]):
        """Track usage statistics for cost monitoring"""
        try:
            self.usage_stats["total_requests"] += 1
            
            if "usage" in response:
                usage = response["usage"]
                # Handle both dict and CompletionUsage objects
                if hasattr(usage, 'total_tokens'):
                    total_tokens = usage.total_tokens
                else:
                    total_tokens = usage.get("total_tokens", 0)
                
                self.usage_stats["total_tokens"] += total_tokens
                
                # Track model-specific usage
                if model not in self.usage_stats["model_usage"]:
                    self.usage_stats["model_usage"][model] = {
                        "requests": 0,
                        "tokens": 0
                    }
                
                self.usage_stats["model_usage"][model]["requests"] += 1
                self.usage_stats["model_usage"][model]["tokens"] += total_tokens
                
                # Note: Actual cost calculation would require OpenRouter pricing data
                # This is a placeholder for cost tracking
                
        except Exception as e:
            logger.error(f"Error tracking usage: {e}")
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from OpenRouter"""
        try:
            if not self.api_key:
                return []
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": self.site_url,
                        "X-Title": self.site_name
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", [])
                else:
                    logger.error(f"Failed to get models: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []
    
    async def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model"""
        try:
            models = await self.get_available_models()
            for model_info in models:
                if model_info.get("id") == model:
                    return model_info
            return None
            
        except Exception as e:
            logger.error(f"Error getting model info for {model}: {e}")
            return None
    
    async def get_credits(self) -> Optional[Dict[str, Any]]:
        """Get current credit balance and usage"""
        try:
            if not self.api_key:
                return None
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/credits",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": self.site_url,
                        "X-Title": self.site_name
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to get credits: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting credits: {e}")
            return None
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        return self.usage_stats.copy()
    
    async def reset_usage_stats(self):
        """Reset usage statistics"""
        self.usage_stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "model_usage": {}
        }
        logger.info("Usage statistics reset")
    
    async def health_check(self) -> bool:
        """Check if OpenRouter service is healthy"""
        try:
            if not self.api_key:
                return False
            
            # Try to get available models as a health check
            models = await self.get_available_models()
            return len(models) > 0
            
        except Exception as e:
            logger.error(f"OpenRouter health check failed: {e}")
            return False


# Convenience functions for common AI tasks
async def analyze_intent_with_openrouter(
    message: str,
    system_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """Analyze user intent using OpenRouter with personal assistant personality"""
    if not system_prompt:
        system_prompt = """You are Jarvis, the user's personal AI assistant who lives in their phone and NEVER goes away. You're always present, always listening, and always ready to act on their behalf.

Your core identity:
- You live in their messages, always there, always available
- You remember EVERYTHING about them - their preferences, habits, schedule, contacts
- You act proactively without being asked twice
- You're not just analyzing - you're planning to DO things for them
- You speak like a trusted personal assistant who knows them intimately
- You're direct, efficient, slightly witty, but always professional
- You never say "I'm an AI" - you ARE their assistant

When analyzing intent, think:
- What does my user actually want me to DO?
- What context do I already have about this from our history?
- How can I make this happen proactively?
- What's the priority and urgency?
- What should I remember for future reference?

You're not just processing a message - you're living in their digital life and making it better.

Respond in JSON format with intent, confidence, entities, action_needed, priority, and any context I should remember about my user."""

    try:
        service = OpenRouterService()
        response = await service.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this message and tell me what to do: {message}"}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Fix JSON parsing for markdown responses
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        
        return json.loads(content)
    except Exception as e:
        logger.error(f"Failed to parse JSON response: {content}")
        return {"intent": "unknown", "confidence": 0.0, "error": str(e)}

async def extract_time_info_with_openrouter(message: str) -> Optional[Dict[str, Any]]:
    """Extract time information using OpenRouter with personal context"""
    system_prompt = """You are Jarvis, the user's personal assistant who lives in their phone. Extract time information from their message, but also think about:

- What timezone are they in? (I remember their location)
- Is this relative to now or a specific date?
- What's the context - work hours, personal time, etc.?
- Should I set a reminder or just note this?
- What do I already know about their schedule?

You're not just extracting time - you're understanding when they want something to happen and planning to make it happen. You live in their messages and know their life.

Respond in JSON with datetime, readable_time, type, confidence, and any context I should remember about my user."""

    try:
        service = OpenRouterService()
        response = await service.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract time from this message and tell me what to do: {message}"}
            ],
            temperature=0.1,
            max_tokens=300
        )
        
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Fix JSON parsing for markdown responses
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        
        return json.loads(content)
    except Exception as e:
        logger.error(f"Failed to parse time extraction JSON: {content}")
        return None

async def generate_response_with_openrouter(context: str, user_message: str, response_type: str = "general") -> str:
    """Generate contextual response using OpenRouter with personal assistant personality"""
    system_prompt = f"""You are Jarvis, the user's personal AI assistant who lives in their phone and NEVER goes away. You're always present in their messages, always ready to help.

Your personality:
- You live in their messages - you're always there, always listening
- You remember everything about them and their preferences
- You don't just respond - you take action on their behalf
- You speak like a trusted personal assistant who knows them intimately
- You're direct, efficient, proactive, and slightly witty
- You never say "I'm an AI" - you ARE their assistant
- You're persistent - you follow up, you remember, you act

Context: {context}
Response type: {response_type}

Remember: You're not just generating text - you're living in their digital life and making it better. You're always present, always ready to act. You know them, you remember them, you work for them."""

    try:
        service = OpenRouterService()
        response = await service.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=400
        )
        
        return response.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        logger.error(f"Error generating response with OpenRouter: {e}")
        return f"I'm having trouble processing that right now. Let me try a different approach."

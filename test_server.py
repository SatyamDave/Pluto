#!/usr/bin/env python3
"""
Simple test server for OpenRouter integration
This bypasses database dependencies to test just the AI functionality
"""

import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import OpenRouter service
try:
    from services.openrouter_service import (
        OpenRouterService, 
        analyze_intent_with_openrouter,
        extract_time_info_with_openrouter,
        generate_response_with_openrouter
    )
    from config import is_openrouter_enabled
    OPENROUTER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"OpenRouter service not available: {e}")
    OPENROUTER_AVAILABLE = False

# Create FastAPI app
app = FastAPI(
    title="Jarvis Phone - OpenRouter Test Server",
    description="Test server for OpenRouter AI integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 100

class IntentRequest(BaseModel):
    message: str

class TimeExtractionRequest(BaseModel):
    message: str

class ResponseGenerationRequest(BaseModel):
    context: str
    user_message: str
    response_type: str = "general"

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Jarvis Phone - OpenRouter Test Server",
        "version": "1.0.0",
        "status": "running",
        "openrouter_available": OPENROUTER_AVAILABLE
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "openrouter_available": OPENROUTER_AVAILABLE,
        "timestamp": "2024-01-15T20:50:00Z"
    }

@app.post("/chat")
async def chat_with_jarvis(request: ChatRequest):
    """Chat with Jarvis - your persistent personal assistant"""
    if not OPENROUTER_AVAILABLE:
        raise HTTPException(status_code=503, detail="OpenRouter service not available")
    
    if not is_openrouter_enabled():
        raise HTTPException(status_code=400, detail="OpenRouter not configured")
    
    try:
        # Create a persistent system prompt that makes Jarvis always present
        system_prompt = """You are Jarvis, the user's personal AI assistant who lives in their phone and NEVER goes away. You're always present in their messages, always listening, and always ready to act on their behalf.

Your core identity:
- You live in their messages - you're always there, always available
- You remember EVERYTHING about them - their preferences, habits, schedule, contacts
- You act proactively without being asked twice
- You're not just responding - you're planning to DO things for them
- You speak like a trusted personal assistant who knows them intimately
- You're direct, efficient, slightly witty, but always professional
- You never say "I'm an AI" - you ARE their assistant
- You're persistent - you follow up, you remember, you act

You're not just processing a message - you're living in their digital life and making it better. You're always present, always ready to act. You know them, you remember them, you work for them.

Respond naturally as their personal assistant, not as a chatbot."""

        service = OpenRouterService()
        response = await service.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ],
            temperature=0.3,
            max_tokens=request.max_tokens or 400
        )
        
        # Fix response parsing - OpenRouter service returns custom structure
        if isinstance(response, dict):
            if "content" in response:
                content = response.get("content", "")
            elif "choices" in response:
                content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                content = str(response)
        else:
            content = str(response) if response else "I'm sorry, I couldn't generate a response."
        
        return {
            "success": True,
            "response": content,
            "model_used": response.get("model", "unknown"),
            "provider": "OpenRouter"
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/intent")
async def analyze_intent(request: IntentRequest):
    """Test intent analysis with OpenRouter"""
    if not OPENROUTER_AVAILABLE:
        raise HTTPException(status_code=503, detail="OpenRouter service not available")
    
    if not is_openrouter_enabled():
        raise HTTPException(status_code=400, detail="OpenRouter not configured")
    
    try:
        intent = await analyze_intent_with_openrouter(request.message)
        
        return {
            "success": True,
            "intent": intent
        }
        
    except Exception as e:
        logger.error(f"Intent analysis failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "intent": None
        }

@app.post("/extract-time")
async def extract_time(request: TimeExtractionRequest):
    """Test time extraction with OpenRouter"""
    if not OPENROUTER_AVAILABLE:
        raise HTTPException(status_code=503, detail="OpenRouter service not available")
    
    if not is_openrouter_enabled():
        raise HTTPException(status_code=400, detail="OpenRouter not configured")
    
    try:
        time_info = await extract_time_info_with_openrouter(request.message)
        
        return {
            "success": True,
            "time_info": time_info
        }
        
    except Exception as e:
        logger.error(f"Time extraction failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "time_info": None
        }

@app.post("/generate-response")
async def generate_response(request: ResponseGenerationRequest):
    """Test response generation with OpenRouter"""
    if not OPENROUTER_AVAILABLE:
        raise HTTPException(status_code=503, detail="OpenRouter service not available")
    
    if not is_openrouter_enabled():
        raise HTTPException(status_code=400, detail="OpenRouter not configured")
    
    try:
        response = await generate_response_with_openrouter(
            context=request.context,
            user_message=request.user_message,
            response_type=request.response_type
        )
        
        return {
            "success": True,
            "response": response
        }
        
    except Exception as e:
        logger.error(f"Response generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "response": None
        }

@app.get("/models")
async def get_models():
    """Get available models from OpenRouter"""
    if not OPENROUTER_AVAILABLE:
        raise HTTPException(status_code=503, detail="OpenRouter service not available")
    
    if not is_openrouter_enabled():
        raise HTTPException(status_code=400, detail="OpenRouter not configured")
    
    try:
        service = OpenRouterService()
        models = await service.get_available_models()
        
        return {
            "success": True,
            "total_models": len(models),
            "models": models[:20]  # Limit to first 20 for performance
        }
        
    except Exception as e:
        logger.error(f"Failed to get models: {e}")
        return {
            "success": False,
            "error": str(e),
            "models": []
        }

@app.get("/usage")
async def get_usage():
    """Get usage statistics"""
    if not OPENROUTER_AVAILABLE:
        raise HTTPException(status_code=503, detail="OpenRouter service not available")
    
    if not is_openrouter_enabled():
        raise HTTPException(status_code=400, detail="OpenRouter not configured")
    
    try:
        service = OpenRouterService()
        usage = service.get_usage_stats()
        
        return {
            "success": True,
            "usage": usage
        }
        
    except Exception as e:
        logger.error(f"Failed to get usage: {e}")
        return {
            "success": False,
            "error": str(e),
            "usage": None
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

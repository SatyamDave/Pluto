"""
AI Management API routes for OpenRouter integration
Provides endpoints for monitoring AI usage, managing models, and health checks
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from services.openrouter_service import OpenRouterService
from config import is_openrouter_enabled

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI Management"])


@router.get("/health")
async def ai_health_check() -> Dict[str, Any]:
    """Check the health of all AI services"""
    try:
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "services": {}
        }
        
        # Check OpenRouter
        if is_openrouter_enabled():
            try:
                openrouter_service = OpenRouterService()
                openrouter_healthy = await openrouter_service.health_check()
                health_status["services"]["openrouter"] = {
                    "status": "healthy" if openrouter_healthy else "unhealthy",
                    "enabled": True
                }
                
                if not openrouter_healthy:
                    health_status["overall_status"] = "degraded"
                    
            except Exception as e:
                logger.error(f"OpenRouter health check failed: {e}")
                health_status["services"]["openrouter"] = {
                    "status": "unhealthy",
                    "enabled": True,
                    "error": str(e)
                }
                health_status["overall_status"] = "degraded"
        else:
            health_status["services"]["openrouter"] = {
                "status": "disabled",
                "enabled": False
            }
        
        return health_status
        
    except Exception as e:
        logger.error(f"AI health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/models")
async def get_available_models() -> Dict[str, Any]:
    """Get list of available AI models from OpenRouter"""
    try:
        if not is_openrouter_enabled():
            raise HTTPException(status_code=400, detail="OpenRouter is not enabled")
        
        openrouter_service = OpenRouterService()
        models = await openrouter_service.get_available_models()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_models": len(models),
            "models": models[:50]  # Limit to first 50 models for performance
        }
        
    except Exception as e:
        logger.error(f"Failed to get available models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")


@router.get("/models/{model_id}")
async def get_model_info(model_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific model"""
    try:
        if not is_openrouter_enabled():
            raise HTTPException(status_code=400, detail="OpenRouter is not enabled")
        
        openrouter_service = OpenRouterService()
        model_info = await openrouter_service.get_model_info(model_id)
        
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "model": model_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model info for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")


@router.get("/usage")
async def get_usage_stats() -> Dict[str, Any]:
    """Get current AI usage statistics"""
    try:
        if not is_openrouter_enabled():
            raise HTTPException(status_code=400, detail="OpenRouter is not enabled")
        
        openrouter_service = OpenRouterService()
        usage_stats = openrouter_service.get_usage_stats()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "usage": usage_stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get usage stats: {str(e)}")


@router.post("/usage/reset")
async def reset_usage_stats(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Reset usage statistics (runs in background)"""
    try:
        if not is_openrouter_enabled():
            raise HTTPException(status_code=400, detail="OpenRouter is not enabled")
        
        openrouter_service = OpenRouterService()
        
        # Reset stats in background
        background_tasks.add_task(openrouter_service.reset_usage_stats)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Usage statistics reset initiated",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Failed to reset usage stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset usage stats: {str(e)}")


@router.get("/credits")
async def get_credits() -> Dict[str, Any]:
    """Get current credit balance and usage from OpenRouter"""
    try:
        if not is_openrouter_enabled():
            raise HTTPException(status_code=400, detail="OpenRouter is not enabled")
        
        openrouter_service = OpenRouterService()
        credits = await openrouter_service.get_credits()
        
        if not credits:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Unable to retrieve credit information",
                "credits": None
            }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "credits": credits
        }
        
    except Exception as e:
        logger.error(f"Failed to get credits: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get credits: {str(e)}")


@router.post("/test")
async def test_ai_completion(
    message: str,
    model: Optional[str] = None
) -> Dict[str, Any]:
    """Test AI completion with a simple message"""
    try:
        if not is_openrouter_enabled():
            raise HTTPException(status_code=400, detail="OpenRouter is not enabled")
        
        openrouter_service = OpenRouterService()
        
        # Simple test prompt
        test_messages = [
            {"role": "system", "content": "You are Jarvis, a helpful AI assistant. Respond briefly and clearly."},
            {"role": "user", "content": message}
        ]
        
        response = await openrouter_service.chat_completion(
            messages=test_messages,
            model=model,
            temperature=0.3,
            max_tokens=100
        )
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "test_message": message,
            "model_used": response.get("model", "unknown"),
            "response": response.get("content", "No response generated"),
            "provider": response.get("provider", "unknown"),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"AI test completion failed: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "test_message": message,
            "error": str(e),
            "success": False
        }


@router.get("/status")
async def get_ai_status() -> Dict[str, Any]:
    """Get comprehensive AI service status"""
    try:
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "openrouter": {
                "enabled": is_openrouter_enabled(),
                "configured": bool(is_openrouter_enabled())
            }
        }
        
        # Add health check results
        if is_openrouter_enabled():
            try:
                openrouter_service = OpenRouterService()
                health_status = await openrouter_service.health_check()
                status["openrouter"]["healthy"] = health_status
                
                # Get available models count
                models = await openrouter_service.get_available_models()
                status["openrouter"]["available_models"] = len(models)
                
            except Exception as e:
                status["openrouter"]["healthy"] = False
                status["openrouter"]["error"] = str(e)
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get AI status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get AI status: {str(e)}")

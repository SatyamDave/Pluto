"""
Health check routes for Jarvis Phone AI Assistant
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from db.database import get_db, get_redis
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "Jarvis Phone AI Assistant",
        "version": "1.0.0"
    }


@router.get("/detailed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_db)
):
    """Detailed health check with database and service status"""
    try:
        health_status = {
            "status": "healthy",
            "service": "Jarvis Phone AI Assistant",
            "version": "1.0.0",
            "checks": {
                "database": "unknown",
                "redis": "unknown",
                "telephony": "unknown",
                "ai_services": "unknown"
            }
        }
        
        # Check database connection
        try:
            # Simple query to test database
            result = await db.execute("SELECT 1")
            result.fetchone()
            health_status["checks"]["database"] = "healthy"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health_status["checks"]["database"] = "unhealthy"
            health_status["status"] = "degraded"
        
        # Check Redis connection
        try:
            redis_client = await get_redis()
            await redis_client.ping()
            health_status["checks"]["redis"] = "healthy"
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            health_status["checks"]["redis"] = "unhealthy"
            health_status["status"] = "degraded"
        
        # Check telephony services
        try:
            from config import is_twilio_enabled, is_telnyx_enabled
            
            twilio_status = "enabled" if is_twilio_enabled() else "disabled"
            telnyx_status = "enabled" if is_telnyx_enabled() else "disabled"
            
            if is_twilio_enabled() or is_telnyx_enabled():
                health_status["checks"]["telephony"] = "healthy"
            else:
                health_status["checks"]["telephony"] = "unhealthy"
                health_status["status"] = "degraded"
                
        except Exception as e:
            logger.error(f"Telephony health check failed: {e}")
            health_status["checks"]["telephony"] = "unknown"
        
        # Check AI services
        try:
            ai_status = "unknown"
            if settings.OPENAI_API_KEY:
                ai_status = "healthy"
            elif settings.ANTHROPIC_API_KEY:
                ai_status = "healthy"
            else:
                ai_status = "unhealthy"
                health_status["status"] = "degraded"
            
            health_status["checks"]["ai_services"] = ai_status
            
        except Exception as e:
            logger.error(f"AI services health check failed: {e}")
            health_status["checks"]["ai_services"] = "unknown"
        
        # Determine overall status
        unhealthy_checks = [check for check in health_status["checks"].values() if check == "unhealthy"]
        if unhealthy_checks:
            health_status["status"] = "unhealthy"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "Jarvis Phone AI Assistant",
            "version": "1.0.0",
            "error": str(e)
        }


@router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes/load balancer health checks"""
    return {
        "status": "ready",
        "service": "Jarvis Phone AI Assistant"
    }


@router.get("/live")
async def liveness_check():
    """Liveness check for Kubernetes health checks"""
    return {
        "status": "alive",
        "service": "Jarvis Phone AI Assistant"
    }

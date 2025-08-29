"""
Outbound Call Routes for Jarvis Phone AI Assistant
Handles API endpoints for AI calling humans
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from telephony.outbound_call_service import OutboundCallService, CallType
from config import is_outbound_calls_enabled

logger = logging.getLogger(__name__)
router = APIRouter()


class OutboundCallRequest(BaseModel):
    """Request model for initiating outbound calls"""
    user_id: int
    target_phone: str
    call_type: str
    task_description: str
    ai_script: str = None


class CallStatusResponse(BaseModel):
    """Response model for call status"""
    call_id: str
    status: str
    message: str
    transcript: list = None


@router.post("/initiate", response_model=CallStatusResponse)
async def initiate_outbound_call(request: OutboundCallRequest):
    """Initiate an outbound call to a human"""
    try:
        if not is_outbound_calls_enabled():
            raise HTTPException(status_code=400, detail="Outbound calls are not enabled")
        
        # Validate call type
        try:
            call_type = CallType(request.call_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid call type: {request.call_type}")
        
        # Initialize outbound call service
        outbound_service = OutboundCallService()
        
        # Initiate the call
        call = await outbound_service.initiate_call(
            user_id=request.user_id,
            target_phone=request.target_phone,
            call_type=call_type,
            task_description=request.task_description,
            ai_script=request.ai_script
        )
        
        logger.info(f"Outbound call initiated: {call.call_id}")
        
        return CallStatusResponse(
            call_id=call.call_id,
            status=call.status.value,
            message=f"Call initiated to {request.target_phone}",
            transcript=[]
        )
        
    except Exception as e:
        logger.error(f"Error initiating outbound call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{call_id}/status", response_model=CallStatusResponse)
async def get_call_status(call_id: str):
    """Get status of a specific outbound call"""
    try:
        if not is_outbound_calls_enabled():
            raise HTTPException(status_code=400, detail="Outbound calls are not enabled")
        
        outbound_service = OutboundCallService()
        call = await outbound_service.get_call_status(call_id)
        
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        # Get transcript
        transcript = await outbound_service.get_call_transcript(call_id)
        
        return CallStatusResponse(
            call_id=call.call_id,
            status=call.status.value,
            message=f"Call {call.status.value}",
            transcript=transcript
        )
        
    except Exception as e:
        logger.error(f"Error getting call status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{call_id}/end")
async def end_call(call_id: str, result: str = None):
    """End an active outbound call"""
    try:
        if not is_outbound_calls_enabled():
            raise HTTPException(status_code=400, detail="Outbound calls are not enabled")
        
        outbound_service = OutboundCallService()
        success = await outbound_service.end_call(call_id, result)
        
        if not success:
            raise HTTPException(status_code=404, detail="Call not found or already ended")
        
        logger.info(f"Call {call_id} ended successfully")
        return {"message": "Call ended successfully"}
        
    except Exception as e:
        logger.error(f"Error ending call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{call_id}/retry")
async def retry_failed_call(call_id: str):
    """Retry a failed outbound call"""
    try:
        if not is_outbound_calls_enabled():
            raise HTTPException(status_code=400, detail="Outbound calls are not enabled")
        
        outbound_service = OutboundCallService()
        success = await outbound_service.retry_failed_call(call_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Call cannot be retried")
        
        logger.info(f"Call {call_id} retry initiated")
        return {"message": "Call retry initiated successfully"}
        
    except Exception as e:
        logger.error(f"Error retrying call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_calls():
    """Get all active outbound calls"""
    try:
        if not is_outbound_calls_enabled():
            raise HTTPException(status_code=400, detail="Outbound calls are not enabled")
        
        outbound_service = OutboundCallService()
        active_calls = await outbound_service.get_active_calls()
        
        return {
            "active_calls": len(active_calls),
            "calls": [
                {
                    "call_id": call.call_id,
                    "user_id": call.user_id,
                    "target_phone": call.target_phone,
                    "call_type": call.call_type.value,
                    "status": call.status.value,
                    "initiated_at": call.initiated_at.isoformat()
                }
                for call in active_calls
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting active calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def get_call_types():
    """Get available call types"""
    try:
        return {
            "call_types": [
                {
                    "value": call_type.value,
                    "description": call_type.name.replace("_", " ").title()
                }
                for call_type in CallType
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting call types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

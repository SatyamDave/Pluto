"""
Telephony API Routes
Handle inbound SMS and voice webhooks from telephony providers
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
import json

from telephony.telephony_manager import TelephonyManager
from config import settings
from utils import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/telephony", tags=["telephony"])

# Initialize telephony manager
telephony_manager = TelephonyManager({
    "PROVIDER": settings.PROVIDER,
    "PHONE_NUMBER": settings.PHONE_NUMBER,
    "telnyx_api_key": settings.TELNYX_API_KEY,
    "telnyx_webhook_secret": settings.TELNYX_WEBHOOK_SECRET,
    "telnyx_phone_number": settings.TELNYX_PHONE_NUMBER,
    "twilio_account_sid": settings.TWILIO_ACCOUNT_SID,
    "twilio_auth_token": settings.TWILIO_AUTH_TOKEN,
    "twilio_phone_number": settings.TWILIO_PHONE_NUMBER,
    "twilio_webhook_secret": settings.TWILIO_WEBHOOK_SECRET,
})


@router.post("/telnyx/sms")
async def telnyx_sms_webhook(request: Request):
    """Handle inbound SMS webhook from Telnyx"""
    try:
        # Get raw payload
        payload = await request.json()
        
        # Validate webhook signature if secret is configured
        if settings.TELNYX_WEBHOOK_SECRET:
            signature = request.headers.get("telnyx-signature-ed25519", "")
            timestamp = request.headers.get("telnyx-timestamp", "")
            
            if not await telephony_manager.telephony_service.validate_webhook_signature(
                await request.body(), signature, timestamp
            ):
                logger.warning("Invalid Telnyx webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Process the webhook
        result = await telephony_manager.handle_inbound_sms(payload)
        
        logger.info(f"Telnyx SMS webhook processed: {result}")
        
        if result.get("success"):
            return JSONResponse(content=result, status_code=200)
        else:
            return JSONResponse(content=result, status_code=500)
            
    except Exception as e:
        logger.error(f"Error processing Telnyx SMS webhook: {e}")
        return JSONResponse(
            content={"error": str(e)}, 
            status_code=500
        )


@router.post("/telnyx/voice")
async def telnyx_voice_webhook(request: Request):
    """Handle inbound voice webhook from Telnyx"""
    try:
        # Get raw payload
        payload = await request.json()
        
        # Validate webhook signature if secret is configured
        if settings.TELNYX_WEBHOOK_SECRET:
            signature = request.headers.get("telnyx-signature-ed25519", "")
            timestamp = request.headers.get("telnyx-timestamp", "")
            
            if not await telephony_manager.telephony_service.validate_webhook_signature(
                await request.body(), signature, timestamp
            ):
                logger.warning("Invalid Telnyx webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Process the webhook
        result = await telephony_manager.handle_inbound_voice(payload)
        
        logger.info(f"Telnyx voice webhook processed: {result}")
        
        if result.get("success"):
            return JSONResponse(content=result, status_code=200)
        else:
            return JSONResponse(content=result, status_code=500)
            
    except Exception as e:
        logger.error(f"Error processing Telnyx voice webhook: {e}")
        return JSONResponse(
            content={"error": str(e)}, 
            status_code=500
        )


@router.post("/twilio/sms")
async def twilio_sms_webhook(request: Request):
    """Handle inbound SMS webhook from Twilio"""
    try:
        # Get form data from Twilio
        form_data = await request.form()
        payload = dict(form_data)
        
        # Validate webhook signature if secret is configured
        if settings.TWILIO_WEBHOOK_SECRET:
            signature = request.headers.get("x-twilio-signature", "")
            url = str(request.url)
            timestamp = request.headers.get("x-twilio-timestamp", "")
            
            if not await telephony_manager.telephony_service.validate_webhook_signature(
                await request.body(), signature, timestamp
            ):
                logger.warning("Invalid Twilio webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Process the webhook
        result = await telephony_manager.handle_inbound_sms(payload)
        
        logger.info(f"Twilio SMS webhook processed: {result}")
        
        if result.get("success"):
            return JSONResponse(content=result, status_code=200)
        else:
            return JSONResponse(content=result, status_code=500)
            
    except Exception as e:
        logger.error(f"Error processing Twilio SMS webhook: {e}")
        return JSONResponse(
            content={"error": str(e)}, 
            status_code=500
        )


@router.post("/twilio/voice")
async def twilio_voice_webhook(request: Request):
    """Handle inbound voice webhook from Twilio"""
    try:
        # Get form data from Twilio
        form_data = await request.form()
        payload = dict(form_data)
        
        # Validate webhook signature if secret is configured
        if settings.TWILIO_WEBHOOK_SECRET:
            signature = request.headers.get("x-twilio-signature", "")
            url = str(request.url)
            timestamp = request.headers.get("x-twilio-timestamp", "")
            
            if not await telephony_manager.telephony_service.validate_webhook_signature(
                await request.body(), signature, timestamp
            ):
                logger.warning("Invalid Twilio webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Process the webhook
        result = await telephony_manager.handle_inbound_voice(payload)
        
        logger.info(f"Twilio voice webhook processed: {result}")
        
        if result.get("success"):
            return JSONResponse(content=result, status_code=200)
        else:
            return JSONResponse(content=result, status_code=500)
            
    except Exception as e:
        logger.error(f"Error processing Twilio voice webhook: {e}")
        return JSONResponse(
            content={"error": str(e)}, 
            status_code=500
        )


@router.get("/status")
async def get_telephony_status():
    """Get telephony service status"""
    try:
        status = await telephony_manager.get_telephony_status()
        return JSONResponse(content=status, status_code=200)
    except Exception as e:
        logger.error(f"Error getting telephony status: {e}")
        return JSONResponse(
            content={"error": str(e)}, 
            status_code=500
        )


@router.post("/send-sms")
async def send_sms(request: Request):
    """Send outbound SMS"""
    try:
        data = await request.json()
        to = data.get("to")
        body = data.get("body")
        user_id = data.get("user_id")
        
        if not all([to, body, user_id]):
            return JSONResponse(
                content={"error": "Missing required fields: to, body, user_id"}, 
                status_code=400
            )
        
        result = await telephony_manager.send_sms(to, body, user_id)
        
        if "error" not in result:
            return JSONResponse(content=result, status_code=200)
        else:
            return JSONResponse(content=result, status_code=500)
            
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        return JSONResponse(
            content={"error": str(e)}, 
            status_code=500
        )


@router.post("/make-call")
async def make_call(request: Request):
    """Make outbound call"""
    try:
        data = await request.json()
        to = data.get("to")
        script = data.get("script")
        user_id = data.get("user_id")
        call_type = data.get("call_type", "general")
        
        if not all([to, script, user_id]):
            return JSONResponse(
                content={"error": "Missing required fields: to, script, user_id"}, 
                status_code=400
            )
        
        result = await telephony_manager.make_call(to, script, user_id, call_type)
        
        if "error" not in result:
            return JSONResponse(content=result, status_code=200)
        else:
            return JSONResponse(content=result, status_code=500)
            
    except Exception as e:
        logger.error(f"Error making call: {e}")
        return JSONResponse(
            content={"error": str(e)}, 
            status_code=500
        )


@router.get("/webhook-urls")
async def get_webhook_urls():
    """Get webhook URLs for configuration"""
    try:
        urls = telephony_manager.telephony_service.get_webhook_urls()
        return JSONResponse(content=urls, status_code=200)
    except Exception as e:
        logger.error(f"Error getting webhook URLs: {e}")
        return JSONResponse(
            content={"error": str(e)}, 
            status_code=500
        )

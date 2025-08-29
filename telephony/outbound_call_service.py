"""
Outbound Call Service for Jarvis Phone AI Assistant
Handles AI calling humans to perform tasks like rescheduling appointments
"""

import logging
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from config import settings, is_outbound_calls_enabled
from telephony.twilio_handler import TwilioHandler
from telephony.telnyx_handler import TelnyxHandler
from config import get_telephony_provider, is_twilio_enabled, is_telnyx_enabled

logger = logging.getLogger(__name__)


class CallStatus(Enum):
    """Status of an outbound call"""
    INITIATED = "initiated"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no_answer"
    BUSY = "busy"


class CallType(Enum):
    """Type of outbound call"""
    APPOINTMENT_RESCHEDULE = "appointment_reschedule"
    RESTAURANT_BOOKING = "restaurant_booking"
    DELIVERY_UPDATE = "delivery_update"
    GENERAL_TASK = "general_task"


@dataclass
class CallTranscript:
    """Transcript of a call conversation"""
    call_id: str
    timestamp: datetime
    speaker: str  # "ai" or "human"
    message: str
    message_type: str  # "speech" or "dtmf"


@dataclass
class OutboundCall:
    """Represents an outbound call"""
    call_id: str
    user_id: int
    target_phone: str
    call_type: CallType
    task_description: str
    status: CallStatus
    initiated_at: datetime
    completed_at: Optional[datetime] = None
    transcript: List[CallTranscript] = None
    result: Optional[str] = None
    error_message: Optional[str] = None


class OutboundCallService:
    """Service for managing AI outbound calls to humans"""
    
    def __init__(self):
        if not is_outbound_calls_enabled():
            raise ValueError("Outbound calls are not enabled")
        
        self.telephony_provider = get_telephony_provider()
        self.active_calls: Dict[str, OutboundCall] = {}
        
        # Initialize telephony handler
        if self.telephony_provider == "twilio" and is_twilio_enabled():
            self.handler = TwilioHandler()
        elif self.telephony_provider == "telnyx" and is_telnyx_enabled():
            self.handler = TelnyxHandler()
        else:
            raise ValueError("No valid telephony provider configured")
    
    async def initiate_wakeup_call(
        self,
        user_id: int,
        target_phone: str,
        message: str = "Good morning! Time to wake up!"
    ) -> bool:
        """Initiate a wake-up call to the user"""
        try:
            logger.info(f"Initiating wake-up call to {target_phone} for user {user_id}")
            
            # Generate call ID
            call_id = f"wakeup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{user_id}"
            
            # Create call record
            wakeup_call = OutboundCall(
                call_id=call_id,
                user_id=user_id,
                target_phone=target_phone,
                call_type=CallType.GENERAL_TASK,
                task_description=f"Wake-up call: {message}",
                status=CallStatus.INITIATED,
                initiated_at=datetime.utcnow()
            )
            
            self.active_calls[call_id] = wakeup_call
            
            # Make the actual call using the telephony handler
            try:
                # Use TTS to convert message to speech
                # For now, we'll use a simple approach - in production you'd use ElevenLabs/Amazon Polly
                call_result = await self.handler.make_call(
                    to_phone=target_phone,
                    message=message
                )
                
                if call_result:
                    wakeup_call.status = CallStatus.IN_PROGRESS
                    logger.info(f"Wake-up call initiated successfully: {call_id}")
                    return True
                else:
                    wakeup_call.status = CallStatus.FAILED
                    wakeup_call.error_message = "Failed to initiate call"
                    logger.error(f"Failed to initiate wake-up call: {call_id}")
                    return False
                    
            except Exception as e:
                wakeup_call.status = CallStatus.FAILED
                wakeup_call.error_message = str(e)
                logger.error(f"Error making wake-up call: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error initiating wake-up call: {e}")
            return False
    
    async def initiate_call(
        self,
        user_id: int,
        target_phone: str,
        call_type: CallType,
        task_description: str,
        ai_script: Optional[str] = None
    ) -> OutboundCall:
        """Initiate an outbound call to a human"""
        try:
            logger.info(f"Initiating {call_type.value} call to {target_phone} for user {user_id}")
            
            # Generate call ID
            call_id = f"call_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{user_id}"
            
            # Create call record
            call = OutboundCall(
                call_id=call_id,
                user_id=user_id,
                target_phone=target_phone,
                call_type=call_type,
                task_description=task_description,
                status=CallStatus.INITIATED,
                initiated_at=datetime.utcnow(),
                transcript=[]
            )
            
            # Store call record
            self.active_calls[call_id] = call
            
            # Generate AI script if not provided
            if not ai_script:
                ai_script = await self._generate_ai_script(call_type, task_description)
            
            # Make the call
            if self.telephony_provider == "twilio":
                await self._initiate_twilio_call(call, ai_script)
            elif self.telephony_provider == "telnyx":
                await self._initiate_telnyx_call(call, ai_script)
            
            logger.info(f"Call {call_id} initiated successfully")
            return call
            
        except Exception as e:
            logger.error(f"Error initiating call: {e}")
            raise
    
    async def _generate_ai_script(
        self, 
        call_type: CallType, 
        task_description: str
    ) -> str:
        """Generate AI script for the call based on type and task"""
        try:
            # This would typically use the AI orchestrator to generate dynamic scripts
            # For now, we'll use predefined templates
            
            base_script = f"""Hi, this is an AI assistant calling for a client. I'm calling to {task_description.lower()}.
            
I need to {task_description.lower()}. Could you help me with that?

If you need to speak with the client directly, please let me know and I can arrange that."""
            
            if call_type == CallType.APPOINTMENT_RESCHEDULE:
                base_script += "\n\nThis is regarding rescheduling an appointment. What times do you have available?"
            elif call_type == CallType.RESTAURANT_BOOKING:
                base_script += "\n\nI'm looking to make a reservation. What's your availability?"
            elif call_type == CallType.DELIVERY_UPDATE:
                base_script += "\n\nI need to check on a delivery status. Can you help me track that?"
            
            return base_script
            
        except Exception as e:
            logger.error(f"Error generating AI script: {e}")
            return f"Hi, this is an AI assistant calling for a client. I need to {task_description.lower()}."
    
    async def _initiate_twilio_call(self, call: OutboundCall, ai_script: str):
        """Initiate call using Twilio"""
        try:
            # Generate TwiML with Gather for interactive conversation
            twiml = self._generate_interactive_twiml(ai_script, call.call_id)
            
            # Make the call
            call_sid = await self.handler.make_call(call.target_phone, twiml)
            
            # Update call record
            call.status = CallStatus.RINGING
            
            logger.info(f"Twilio call initiated with SID: {call_sid}")
            
        except Exception as e:
            logger.error(f"Error initiating Twilio call: {e}")
            call.status = CallStatus.FAILED
            call.error_message = str(e)
            raise
    
    async def _initiate_telnyx_call(self, call: OutboundCall, ai_script: str):
        """Initiate call using Telnyx"""
        try:
            # Generate Telnyx-specific call instructions
            call_instructions = self._generate_telnyx_instructions(ai_script, call.call_id)
            
            # Make the call
            call_id = await self.handler.make_call(call.target_phone, call_instructions)
            
            # Update call record
            call.status = CallStatus.RINGING
            
            logger.info(f"Telnyx call initiated with ID: {call_id}")
            
        except Exception as e:
            logger.error(f"Error initiating Telnyx call: {e}")
            call.status = CallStatus.FAILED
            call.error_message = str(e)
            raise
    
    def _generate_interactive_twiml(self, ai_script: str, call_id: str) -> str:
        """Generate TwiML for interactive conversation"""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hi, this is an AI assistant calling for a client.</Say>
    <Pause length="1"/>
    <Say voice="alice">{ai_script}</Say>
    <Pause length="2"/>
    
    <Gather input="speech" timeout="10" action="/api/v1/voice/call-webhook/{call_id}" method="POST">
        <Say voice="alice">Please respond to my request. I'm listening.</Say>
    </Gather>
    
    <Say voice="alice">Thank you for your time. Goodbye.</Say>
    <Hangup/>
</Response>"""
    
    def _generate_telnyx_instructions(self, ai_script: str, call_id: str) -> str:
        """Generate Telnyx call instructions"""
        # Telnyx uses different format - this would be implemented based on Telnyx API
        return f"Call script: {ai_script} | Call ID: {call_id}"
    
    async def handle_call_webhook(
        self, 
        call_id: str, 
        webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle webhook from telephony provider during call"""
        try:
            if call_id not in self.active_calls:
                logger.warning(f"Call {call_id} not found in active calls")
                return {"error": "Call not found"}
            
            call = self.active_calls[call_id]
            
            # Extract speech or DTMF input
            speech_result = webhook_data.get("SpeechResult")
            dtmf_digits = webhook_data.get("Digits")
            
            if speech_result:
                # Add human response to transcript
                transcript_entry = CallTranscript(
                    call_id=call_id,
                    timestamp=datetime.utcnow(),
                    speaker="human",
                    message=speech_result,
                    message_type="speech"
                )
                call.transcript.append(transcript_entry)
                
                # Generate AI response
                ai_response = await self._generate_ai_response(call, speech_result)
                
                # Add AI response to transcript
                ai_transcript = CallTranscript(
                    call_id=call_id,
                    timestamp=datetime.utcnow(),
                    speaker="ai",
                    message=ai_response,
                    message_type="speech"
                )
                call.transcript.append(ai_transcript)
                
                # Return TwiML for AI response
                return {
                    "twiml": self._generate_response_twiml(ai_response, call_id),
                    "transcript": speech_result,
                    "ai_response": ai_response
                }
            
            elif dtmf_digits:
                # Handle DTMF input (keypress)
                transcript_entry = CallTranscript(
                    call_id=call_id,
                    timestamp=datetime.utcnow(),
                    speaker="human",
                    message=dtmf_digits,
                    message_type="dtmf"
                )
                call.transcript.append(transcript_entry)
                
                return {
                    "twiml": self._generate_dtmf_response_twiml(dtmf_digits, call_id),
                    "transcript": f"Pressed {dtmf_digits}",
                    "ai_response": None
                }
            
            else:
                logger.warning(f"No speech or DTMF input in webhook for call {call_id}")
                return {"error": "No input received"}
                
        except Exception as e:
            logger.error(f"Error handling call webhook: {e}")
            return {"error": str(e)}
    
    async def _generate_ai_response(self, call: OutboundCall, human_input: str) -> str:
        """Generate AI response based on human input and call context"""
        try:
            # This would typically use the AI orchestrator to generate contextual responses
            # For now, we'll use simple response logic
            
            human_input_lower = human_input.lower()
            
            if call.call_type == CallType.APPOINTMENT_RESCHEDULE:
                if any(word in human_input_lower for word in ["available", "time", "slot"]):
                    return "Great! What times do you have available? I'm looking for something in the afternoon if possible."
                elif any(word in human_input_lower for word in ["confirm", "yes", "okay"]):
                    return "Perfect! I'll confirm that appointment time with my client. Thank you for your help."
                else:
                    return "I understand. Could you please let me know what times you have available for rescheduling?"
            
            elif call.call_type == CallType.RESTAURANT_BOOKING:
                if any(word in human_input_lower for word in ["reservation", "booking", "table"]):
                    return "Yes, I'd like to make a reservation. What's your availability for this evening?"
                else:
                    return "I'm looking to make a dinner reservation. What times do you have available?"
            
            else:
                return "Thank you for that information. Is there anything else I should know?"
                
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I'm sorry, I didn't catch that. Could you please repeat?"
    
    def _generate_response_twiml(self, ai_response: str, call_id: str) -> str:
        """Generate TwiML for AI response"""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">{ai_response}</Say>
    <Pause length="1"/>
    
    <Gather input="speech" timeout="10" action="/api/v1/voice/call-webhook/{call_id}" method="POST">
        <Say voice="alice">I'm listening for your response.</Say>
    </Gather>
    
    <Say voice="alice">Thank you. Goodbye.</Say>
    <Hangup/>
</Response>"""
    
    def _generate_dtmf_response_twiml(self, dtmf_digits: str, call_id: str) -> str:
        """Generate TwiML for DTMF response"""
        if dtmf_digits == "1":
            return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Thank you for confirming. I'll proceed with that.</Say>
    <Hangup/>
</Response>"""
        else:
            return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">I didn't understand that input. Please try again.</Say>
    <Gather input="dtmf" timeout="10" action="/api/v1/voice/call-webhook/{call_id}" method="POST">
        <Say voice="alice">Press 1 to confirm, or speak your response.</Say>
    </Gather>
</Response>"""
    
    async def end_call(self, call_id: str, result: Optional[str] = None) -> bool:
        """End an active call"""
        try:
            if call_id not in self.active_calls:
                logger.warning(f"Call {call_id} not found")
                return False
            
            call = self.active_calls[call_id]
            call.status = CallStatus.COMPLETED
            call.completed_at = datetime.utcnow()
            call.result = result
            
            # Remove from active calls
            del self.active_calls[call_id]
            
            logger.info(f"Call {call_id} ended successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error ending call {call_id}: {e}")
            return False
    
    async def get_call_status(self, call_id: str) -> Optional[OutboundCall]:
        """Get status of a specific call"""
        return self.active_calls.get(call_id)
    
    async def get_active_calls(self) -> List[OutboundCall]:
        """Get all active calls"""
        return list(self.active_calls.values())
    
    async def get_call_transcript(self, call_id: str) -> List[CallTranscript]:
        """Get transcript of a specific call"""
        call = await self.get_call_status(call_id)
        if call:
            return call.transcript
        return []
    
    async def retry_failed_call(self, call_id: str) -> bool:
        """Retry a failed call"""
        try:
            if call_id not in self.active_calls:
                logger.warning(f"Call {call_id} not found for retry")
                return False
            
            call = self.active_calls[call_id]
            
            if call.status != CallStatus.FAILED:
                logger.warning(f"Call {call_id} is not in failed state")
                return False
            
            # Reset call status and retry
            call.status = CallStatus.INITIATED
            call.error_message = None
            
            # Regenerate AI script and retry
            ai_script = await self._generate_ai_script(call.call_type, call.task_description)
            
            if self.telephony_provider == "twilio":
                await self._initiate_twilio_call(call, ai_script)
            elif self.telephony_provider == "telnyx":
                await self._initiate_telnyx_call(call, ai_script)
            
            logger.info(f"Call {call_id} retry initiated")
            return True
            
        except Exception as e:
            logger.error(f"Error retrying call {call_id}: {e}")
            return False

"""
Twilio Usage Examples for Jarvis Phone AI Assistant
Demonstrates how to send SMS, make calls, and handle webhooks
"""

import asyncio
import os
from datetime import datetime, timedelta
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.twiml.messaging_response import MessagingResponse

# Example environment variables
# TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxx
# TWILIO_AUTH_TOKEN=yyyyyyyyyyyyyyyyyyyy
# TWILIO_PHONE_NUMBER=+15551234567

class TwilioExamples:
    """Examples of Twilio operations for Jarvis Phone"""
    
    def __init__(self):
        # Initialize Twilio client
        self.client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        self.from_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    async def send_simple_sms(self, to_phone: str, message: str):
        """Send a simple SMS message"""
        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_phone
            )
            print(f"SMS sent successfully! SID: {message_obj.sid}")
            return message_obj.sid
        except Exception as e:
            print(f"Error sending SMS: {e}")
            return None
    
    async def send_scheduled_sms(self, to_phone: str, message: str, send_time: datetime):
        """Schedule an SMS to be sent at a specific time"""
        try:
            # Format time for Twilio (ISO 8601)
            send_at = send_time.isoformat()
            
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_phone,
                send_at=send_at,
                schedule_type="fixed"
            )
            print(f"SMS scheduled for {send_at}! SID: {message_obj.sid}")
            return message_obj.sid
        except Exception as e:
            print(f"Error scheduling SMS: {e}")
            return None
    
    async def send_bulk_sms(self, phone_numbers: list, message: str):
        """Send SMS to multiple phone numbers"""
        results = []
        for phone in phone_numbers:
            try:
                message_sid = await self.send_simple_sms(phone, message)
                results.append({"phone": phone, "success": True, "message_sid": message_sid})
            except Exception as e:
                results.append({"phone": phone, "success": False, "error": str(e)})
        
        successful = len([r for r in results if r['success']])
        print(f"Bulk SMS completed: {successful}/{len(phone_numbers)} successful")
        return results
    
    async def make_simple_call(self, to_phone: str, message: str):
        """Make a simple voice call with text-to-speech"""
        try:
            # Generate TwiML for the call
            twiml = VoiceResponse()
            twiml.say(message, voice="alice")
            twiml.hangup()
            
            # Make the call
            call = self.client.calls.create(
                twiml=str(twiml),
                from_=self.from_number,
                to=to_phone
            )
            print(f"Call initiated successfully! SID: {call.sid}")
            return call.sid
        except Exception as e:
            print(f"Error making call: {e}")
            return None
    
    async def make_interactive_call(self, to_phone: str, greeting: str):
        """Make an interactive call that can gather user input"""
        try:
            # Generate interactive TwiML
            twiml = VoiceResponse()
            twiml.say(greeting, voice="alice")
            
            # Add Gather verb to collect user input
            gather = Gather(
                input="speech",
                action="/api/v1/voice/webhook/speech",
                method="POST",
                speech_timeout="auto",
                language="en-US"
            )
            gather.say("Please speak your request after the beep.", voice="alice")
            twiml.append(gather)
            
            # Fallback if no input
            twiml.say("I didn't hear anything. Please call back and try again.", voice="alice")
            
            # Make the call
            call = self.client.calls.create(
                twiml=str(twiml),
                from_=self.from_number,
                to=to_phone
            )
            print(f"Interactive call initiated! SID: {call.sid}")
            return call.sid
        except Exception as e:
            print(f"Error making interactive call: {e}")
            return None
    
    async def make_wakeup_call(self, to_phone: str, reminder_text: str):
        """Make a wake-up call that requires user confirmation"""
        try:
            # Generate wake-up call TwiML
            twiml = VoiceResponse()
            twiml.say("Good morning! This is your wake-up call.", voice="alice")
            twiml.pause(length=1)
            twiml.say(reminder_text, voice="alice")
            twiml.pause(length=2)
            twiml.say("To confirm you're awake, please press 1 on your phone.", voice="alice")
            
            # Add DTMF gathering
            gather = Gather(
                input="dtmf",
                timeout=15,
                action="/api/v1/voice/webhook/wakeup",
                method="POST"
            )
            gather.say("Press 1 to confirm you're awake, or I'll call you again in 5 minutes.", voice="alice")
            twiml.append(gather)
            
            # Fallback message
            twiml.say("No confirmation received. I'll call you again shortly.", voice="alice")
            twiml.hangup()
            
            # Make the call
            call = self.client.calls.create(
                twiml=str(twiml),
                from_=self.from_number,
                to=to_phone
            )
            print(f"Wake-up call initiated! SID: {call.sid}")
            return call.sid
        except Exception as e:
            print(f"Error making wake-up call: {e}")
            return None
    
    async def get_message_status(self, message_sid: str):
        """Get the delivery status of an SMS message"""
        try:
            message = self.client.messages(message_sid).fetch()
            status = {
                "sid": message.sid,
                "status": message.status,
                "direction": message.direction,
                "from": message.from_,
                "to": message.to,
                "body": message.body,
                "date_sent": message.date_sent,
                "error_code": message.error_code,
                "error_message": message.error_message
            }
            print(f"Message status: {status}")
            return status
        except Exception as e:
            print(f"Error getting message status: {e}")
            return None
    
    async def get_call_status(self, call_sid: str):
        """Get the status of a voice call"""
        try:
            call = self.client.calls(call_sid).fetch()
            status = {
                "sid": call.sid,
                "status": call.status,
                "direction": call.direction,
                "from": call.from_,
                "to": call.to,
                "start_time": call.start_time,
                "end_time": call.end_time,
                "duration": call.duration,
                "price": call.price,
                "price_unit": call.price_unit
            }
            print(f"Call status: {status}")
            return status
        except Exception as e:
            print(f"Error getting call status: {e}")
            return None
    
    async def list_recent_messages(self, limit: int = 10):
        """List recent SMS messages"""
        try:
            messages = self.client.messages.list(limit=limit)
            for msg in messages:
                print(f"Message {msg.sid}: {msg.from_} -> {msg.to} | {msg.body[:50]}...")
            return messages
        except Exception as e:
            print(f"Error listing messages: {e}")
            return None
    
    async def list_recent_calls(self, limit: int = 10):
        """List recent voice calls"""
        try:
            calls = self.client.calls.list(limit=limit)
            for call in calls:
                print(f"Call {call.sid}: {call.from_} -> {call.to} | Status: {call.status}")
            return calls
        except Exception as e:
            print(f"Error listing calls: {e}")
            return None


# Example usage functions
async def example_sms_workflow():
    """Example SMS workflow for Jarvis Phone"""
    print("=== SMS Workflow Examples ===")
    
    examples = TwilioExamples()
    
    # Send immediate SMS
    await examples.send_simple_sms(
        "+15551234567",
        "🔔 Reminder: Your meeting starts in 15 minutes!"
    )
    
    # Schedule SMS for tomorrow morning
    tomorrow_8am = datetime.now() + timedelta(days=1)
    tomorrow_8am = tomorrow_8am.replace(hour=8, minute=0, second=0, microsecond=0)
    
    await examples.send_scheduled_sms(
        "+15551234567",
        "🌅 Good morning! Here's your daily digest:\n• 3 unread emails\n• 2 meetings today\n• 1 reminder due",
        tomorrow_8am
    )
    
    # Send bulk SMS to team
    team_numbers = ["+15551234567", "+15551234568", "+15551234569"]
    await examples.send_bulk_sms(
        team_numbers,
        "📢 Team meeting in 30 minutes. Don't forget to prepare your updates!"
    )


async def example_voice_workflow():
    """Example voice workflow for Jarvis Phone"""
    print("\n=== Voice Workflow Examples ===")
    
    examples = TwilioExamples()
    
    # Make simple reminder call
    await examples.make_simple_call(
        "+15551234567",
        "Hello! This is your reminder that your dentist appointment is in one hour. Please confirm you're still coming."
    )
    
    # Make interactive call
    await examples.make_interactive_call(
        "+15551234567",
        "Welcome to Jarvis Phone! I'm here to help you manage your schedule and tasks."
    )
    
    # Make wake-up call
    await examples.make_wakeup_call(
        "+15551234567",
        "Time to wake up! You have a meeting at 9 AM and 3 unread emails to review."
    )


async def example_monitoring():
    """Example monitoring and status checking"""
    print("\n=== Monitoring Examples ===")
    
    examples = TwilioExamples()
    
    # List recent messages and calls
    await examples.list_recent_messages(5)
    await examples.list_recent_calls(5)
    
    # Check specific message status (you'd need a real message SID)
    # await examples.get_message_status("SMxxxxxxxxxxxxxxxxxxxx")
    
    # Check specific call status (you'd need a real call SID)
    # await examples.get_call_status("CAxxxxxxxxxxxxxxxxxxxx")


if __name__ == "__main__":
    # Run examples
    asyncio.run(example_sms_workflow())
    asyncio.run(example_voice_workflow())
    asyncio.run(example_monitoring())

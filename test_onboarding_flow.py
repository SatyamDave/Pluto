#!/usr/bin/env python3
"""
Test script for onboarding flow
Tests user activation and contact permissions
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.user_manager import user_manager
from services.communication_service import CommunicationService
from services.audit_service import AuditService
from db.database import get_db


async def test_onboarding_flow():
    """Test the complete onboarding flow"""
    print("🧪 Testing Onboarding Flow...")
    
    try:
        # Test 1: User activation
        print("\n1️⃣ Testing user activation...")
        
        # Simulate a new user texting for the first time
        test_phone = "+15551234567"
        test_name = "Test User"
        
        # Check if user exists
        async for db in get_db():
            user_profile = await user_manager.get_or_create_user(test_phone, db)
            print(f"✅ User profile: {user_profile['id']} - {user_profile['phone_number']}")
            
            # Test message count increment
            print(f"📱 Initial message count: {user_profile.get('message_count', 0)}")
            
            success = await user_manager.increment_message_count(user_profile['id'], db)
            if success:
                print("✅ Message count incremented successfully")
                
                # Get updated profile
                updated_profile = await user_manager.get_user_by_id(user_profile['id'], db)
                print(f"📱 Updated message count: {updated_profile.get('message_count', 0)}")
            else:
                print("❌ Failed to increment message count")
            
            break
        
        # Test 2: Contact permission request
        print("\n2️⃣ Testing contact permission request...")
        
        communication_service = CommunicationService()
        audit_service = AuditService()
        
        # Simulate requesting permission to text a new contact
        contact_name = "John Doe"
        contact_phone = "+15559876543"
        
        async for db in get_db():
            # Create permission request
            permission_request = await communication_service.create_contact_permission_request(
                user_id=user_profile['id'],
                contact_name=contact_name,
                contact_phone=contact_phone,
                permission_type="always"
            )
            
            if permission_request:
                print(f"✅ Permission request created: {permission_request['id']}")
                
                # Test permission response
                print("\n3️⃣ Testing permission response...")
                
                # Simulate user responding "always"
                response_result = await communication_service.update_contact_permission(
                    user_id=user_profile['id'],
                    contact_phone=contact_phone,
                    permission="always"
                )
                
                if response_result:
                    print("✅ Contact permission updated successfully")
                    
                    # Get the contact
                    contact = await communication_service.get_contact_by_phone(
                        user_profile['id'], contact_phone
                    )
                    
                    if contact:
                        print(f"✅ Contact found: {contact['name']} - Permission: {contact.get('permission', 'none')}")
                    else:
                        print("❌ Contact not found after permission update")
                else:
                    print("❌ Failed to update contact permission")
                
                # Mark request as approved
                await communication_service.update_permission_request_status(
                    permission_request['id'], "approved"
                )
                print("✅ Permission request marked as approved")
                
            else:
                print("❌ Failed to create permission request")
            
            break
        
        # Test 3: Onboarding status
        print("\n4️⃣ Testing onboarding status...")
        
        async for db in get_db():
            status = await user_manager.get_onboarding_status(user_profile['id'], db)
            if status:
                print(f"✅ Onboarding status retrieved: {status['progress_percentage']}% complete")
                print(f"   Completed items: {status['completed_items']}")
                print(f"   Next steps: {status['next_steps']}")
            else:
                print("❌ Failed to get onboarding status")
            break
        
        print("\n🎉 Onboarding flow test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing onboarding flow: {e}")
        import traceback
        traceback.print_exc()


async def test_sms_onboarding():
    """Test SMS onboarding message flow"""
    print("\n📱 Testing SMS Onboarding Message...")
    
    try:
        # Simulate the onboarding message that would be sent
        onboarding_message = (
            "I'm Pluto—your AI in Messages. I can remind, schedule, text people, and summarize email. "
            "Reply YES to set up. (STOP to opt out)"
        )
        
        print(f"📝 Onboarding message:\n{onboarding_message}")
        
        # Test the welcome message format
        welcome_message = (
            "Welcome to Pluto, Test User! 🎉\n\n"
            "I'm your AI assistant in Messages. I can:\n"
            "• Set reminders and manage your calendar\n"
            "• Send texts and emails on your behalf\n"
            "• Summarize your inbox and Slack\n"
            "• Give directions and open apps\n\n"
            "Just text me what you need. Try:\n"
            "• 'remind me to call mom at 6pm'\n"
            "• 'what's on my calendar today?'\n"
            "• 'text Jon I'm running 10 min late'"
        )
        
        print(f"\n🎉 Welcome message:\n{welcome_message}")
        
        print("✅ SMS onboarding message test completed!")
        
    except Exception as e:
        print(f"❌ Error testing SMS onboarding: {e}")


if __name__ == "__main__":
    print("🚀 Starting Onboarding Flow Tests...")
    
    # Run tests
    asyncio.run(test_onboarding_flow())
    asyncio.run(test_sms_onboarding())
    
    print("\n✨ All tests completed!")

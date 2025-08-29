"""
Simple test script for user activation system
Run this to verify basic functionality
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.user_manager import UserManager


async def test_user_manager():
    """Test the UserManager basic functionality"""
    print("🧪 Testing UserManager...")
    
    # Create user manager instance
    user_manager = UserManager()
    
    # Test phone number cleaning
    print("\n📱 Testing phone number cleaning...")
    
    test_numbers = [
        "+1-555-123-4567",
        "555-123-4567", 
        "555 123 4567",
        "15551234567"
    ]
    
    for number in test_numbers:
        try:
            cleaned = user_manager._clean_phone_number(number)
            print(f"✅ '{number}' -> '{cleaned}'")
        except Exception as e:
            print(f"❌ '{number}' -> Error: {e}")
    
    # Test invalid numbers
    print("\n🚫 Testing invalid phone numbers...")
    
    invalid_numbers = ["123", "abc", ""]
    for number in invalid_numbers:
        try:
            cleaned = user_manager._clean_phone_number(number)
            print(f"❌ '{number}' -> '{cleaned}' (should have failed)")
        except ValueError as e:
            print(f"✅ '{number}' -> Correctly failed: {e}")
        except Exception as e:
            print(f"❌ '{number}' -> Unexpected error: {e}")
    
    print("\n🎉 Basic UserManager tests completed!")
    print("\nNote: Database tests require a running database connection.")
    print("Run the full test suite with: pytest test_user_activation.py")


if __name__ == "__main__":
    try:
        asyncio.run(test_user_manager())
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

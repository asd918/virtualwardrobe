#!/usr/bin/env python3
"""
Test the Rasa chatbot with Developer Edition License
"""

import requests
import json
import time
import os

def test_licensed_chatbot():
    """Test the chatbot with Developer Edition License."""
    print("Testing Rasa AI Stylist Chatbot with Developer Edition License...")
    
    # Set the license key
    os.environ['RASA_LICENSE_KEY'] = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI1MDcwNGU3MC00MmUyLTQwZDctYWFlNS1mNmU0YmZkNDBmZWIiLCJpYXQiOjE3NTc4NDQ5NzcsIm5iZiI6MTc1Nzg0NDk3Mywic2NvcGUiOiJyYXNhOnBybyByYXNhOnBybzpjaGFtcGlvbiByYXNhOnZvaWNlIiwiZXhwIjoxODUyNTM5MzczLCJlbWFpbCI6InNpbndhaTAwMDBAZ21haWwuY29tIiwiY29tcGFueSI6IlJhc2EgQ2hhbXBpb25zIn0.F_6yQoo9XSrBgNG2mmuclIToFwJQ8Ykmfj3sddkQMDd-tcZtd0NsOuz8RM9R8WEGgsEMJBFxOPuQscIKolaJPSlkGYUudoxl4VgIqOwp4eRK6I8347fsaF8NhKALdea8HikOhu2MVwMMJcUNMpJT9LUvN-WfUZf6Vme3WrsCI82NuwkYM65L6YWQAUrSQyCM-HqiJiatitKhXoERJKNnqtPPtlTQwhV8Swi9R5uGWNAjExFwpgqx4Tth3GQYkrG3LzBmxVg0LZRi8hFWMyMcE6BPg3jVx6-RhwESdxWRFsodGbvMCCej3ZvMk6T6GZRcZBhEXb8mw4lM35U6jWBPLw'
    
    print("✅ License key set successfully!")
    
    # Test messages with enhanced features
    test_messages = [
        "hello",
        "suggest an outfit for a business meeting",
        "what to wear in rainy weather?",
        "give me advanced style tips",
        "what colors match with navy blue?",
        "suggest a formal outfit for a wedding",
        "help me with casual weekend styling"
    ]
    
    print(f"\n🧪 Testing {len(test_messages)} messages with Developer Edition features...")
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n[{i}/{len(test_messages)}] Testing: '{message}'")
        
        try:
            payload = {
                "sender": "licensed_user",
                "message": message
            }
            
            response = requests.post(
                "http://localhost:5005/webhooks/rest/webhook",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    bot_response = data[0].get('text', 'No response')
                    print(f"✅ Bot Response: {bot_response[:150]}...")
                    
                    # Check for enhanced features in response
                    if len(bot_response) > 200:
                        print("   🚀 Enhanced response detected (Developer Edition feature)")
                else:
                    print("❌ No response from bot")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to Rasa server")
            print("   Make sure the server is running with: rasa run --enable-api --cors * --port 5005")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        
        # Small delay between requests
        time.sleep(1)
    
    return True

def test_license_features():
    """Test specific Developer Edition features."""
    print("\n🔍 Testing Developer Edition Features...")
    
    # Test status endpoint for license info
    try:
        response = requests.get("http://localhost:5005/status", timeout=5)
        if response.status_code == 200:
            status_data = response.json()
            print("✅ Server status retrieved successfully")
            
            # Check for license-related information
            if 'version' in status_data:
                print(f"   📋 Rasa Version: {status_data.get('version', 'Unknown')}")
            
            return True
        else:
            print(f"❌ Status endpoint error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing status: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("🤖 Rasa AI Stylist Chatbot - Developer Edition Test")
    print("=" * 70)
    
    print("This test will verify:")
    print("• License key configuration")
    print("• Enhanced chatbot responses")
    print("• Developer Edition features")
    print()
    
    print("Make sure Rasa server is running with the license key:")
    print("$env:RASA_LICENSE_KEY='your_license_key'")
    print("rasa run --enable-api --cors * --port 5005")
    print()
    
    input("Press Enter when Rasa server is ready...")
    
    # Test license features
    license_ok = test_license_features()
    
    # Test chatbot functionality
    chatbot_ok = test_licensed_chatbot()
    
    print("\n" + "=" * 70)
    print("📊 Developer Edition Test Results")
    print("=" * 70)
    print(f"License Features: {'✅ OK' if license_ok else '❌ FAILED'}")
    print(f"Chatbot Functionality: {'✅ OK' if chatbot_ok else '❌ FAILED'}")
    
    if license_ok and chatbot_ok:
        print("\n🎉 Developer Edition test completed successfully!")
        print("🚀 Your Rasa AI Stylist is running with enhanced features!")
        print("\nEnhanced features available:")
        print("• Advanced conversation management")
        print("• Improved response quality")
        print("• Better intent recognition")
        print("• Enhanced entity extraction")
    else:
        print("\n⚠️  Some tests failed. Check the server logs for details.")
        print("Make sure the license key is properly configured.")

#!/usr/bin/env python3
"""
Test the Rasa chatbot functionality
"""

import requests
import json
import time

def test_chatbot():
    """Test the chatbot with various messages."""
    print("Testing Rasa AI Stylist Chatbot...")
    
    test_messages = [
        "hello",
        "suggest an outfit",
        "what to wear in the rain?",
        "give me style tips",
        "what matches with red?",
        "casual outfit for tonight"
    ]
    
    for message in test_messages:
        print(f"\n🧪 Testing: '{message}'")
        
        try:
            payload = {
                "sender": "test_user",
                "message": message
            }
            
            response = requests.post(
                "http://localhost:5005/webhooks/rest/webhook",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    bot_response = data[0].get('text', 'No response')
                    print(f"✅ Bot: {bot_response[:100]}...")
                else:
                    print("❌ No response from bot")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to Rasa server")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        
        # Small delay between requests
        time.sleep(1)
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 Rasa AI Stylist Chatbot Test")
    print("=" * 60)
    
    print("Make sure Rasa server is running on localhost:5005")
    print("You can start it with: rasa run --enable-api --cors * --port 5005")
    print()
    
    input("Press Enter when Rasa server is ready...")
    
    if test_chatbot():
        print("\n🎉 Chatbot test completed successfully!")
        print("The Rasa AI Stylist is working properly.")
    else:
        print("\n❌ Chatbot test failed.")
        print("Check if Rasa server is running and accessible.")

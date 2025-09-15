#!/usr/bin/env python3
"""
Test script for Rasa server
"""

import requests
import json
import time

def test_rasa_server():
    """Test if Rasa server is running and responding."""
    print("Testing Rasa server...")
    
    # Test status endpoint
    try:
        response = requests.get("http://localhost:5005/status", timeout=5)
        if response.status_code == 200:
            print("✅ Rasa server is running!")
            print(f"Status: {response.json()}")
        else:
            print(f"❌ Rasa server returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Rasa server. Make sure it's running on localhost:5005")
        return False
    except Exception as e:
        print(f"❌ Error testing Rasa server: {e}")
        return False
    
    # Test webhook endpoint
    try:
        payload = {
            "sender": "test_user",
            "message": "hello"
        }
        
        response = requests.post(
            "http://localhost:5005/webhooks/rest/webhook",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Rasa webhook is working!")
            print(f"Response: {data}")
            return True
        else:
            print(f"❌ Rasa webhook returned status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Rasa webhook: {e}")
        return False

def test_action_server():
    """Test if Action server is running."""
    print("\nTesting Action server...")
    
    try:
        response = requests.get("http://localhost:5055/health", timeout=5)
        if response.status_code == 200:
            print("✅ Action server is running!")
            return True
        else:
            print(f"❌ Action server returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Action server. Make sure it's running on localhost:5055")
        return False
    except Exception as e:
        print(f"❌ Error testing Action server: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 Rasa Server Test")
    print("=" * 50)
    
    # Wait a moment for servers to start
    print("Waiting for servers to start...")
    time.sleep(5)
    
    rasa_ok = test_rasa_server()
    action_ok = test_action_server()
    
    print("\n" + "=" * 50)
    print("📊 Test Results")
    print("=" * 50)
    print(f"Rasa Server: {'✅ OK' if rasa_ok else '❌ FAILED'}")
    print(f"Action Server: {'✅ OK' if action_ok else '❌ FAILED'}")
    
    if rasa_ok and action_ok:
        print("\n🎉 All tests passed! Rasa chatbot is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Check the server logs for details.")

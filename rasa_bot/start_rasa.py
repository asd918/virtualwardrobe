#!/usr/bin/env python3
"""
Rasa AI Stylist Chatbot Startup Script

This script starts both the Rasa server and action server for the AI Stylist chatbot.
"""

import subprocess
import time
import sys
import os

def start_rasa_server():
    """Start the Rasa server with HTTP API enabled."""
    print("🚀 Starting Rasa Server on port 5005...")
    try:
        # Start Rasa server with HTTP API and CORS enabled
        rasa_cmd = [
            "rasa", "run",
            "--enable-api",
            "--cors", "*",
            "--port", "5005"
        ]
        
        # Start in background
        subprocess.Popen(rasa_cmd, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE)
        
        print("✅ Rasa Server started successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to start Rasa Server: {e}")
        return False

def start_action_server():
    """Start the Rasa action server."""
    print("🔧 Starting Action Server on port 5055...")
    try:
        # Start action server
        action_cmd = [
            "rasa", "run", "actions",
            "--port", "5055"
        ]
        
        # Start in background
        subprocess.Popen(action_cmd, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE)
        
        print("✅ Action Server started successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to start Action Server: {e}")
        return False

def check_rasa_installation():
    """Check if Rasa is installed and available."""
    try:
        result = subprocess.run(["rasa", "--version"], 
                              capture_output=True, 
                              text=True)
        if result.returncode == 0:
            print(f"✅ Rasa version: {result.stdout.strip()}")
            return True
        else:
            print("❌ Rasa is not properly installed")
            return False
    except FileNotFoundError:
        print("❌ Rasa is not installed. Please install it first:")
        print("   pip install rasa==3.6.15")
        return False

def main():
    """Main startup function."""
    print("=" * 50)
    print("🎭 Rasa AI Stylist Chatbot Startup")
    print("=" * 50)
    print()
    
    # Check Rasa installation
    if not check_rasa_installation():
        sys.exit(1)
    
    print("📋 Prerequisites check passed!")
    print()
    
    # Start Rasa server
    if not start_rasa_server():
        sys.exit(1)
    
    # Wait a moment for server to start
    print("⏳ Waiting for Rasa server to initialize...")
    time.sleep(3)
    
    # Start action server
    if not start_action_server():
        print("⚠️  Action server failed to start, but Rasa server is running")
        print("   You can still use basic responses, but custom actions won't work")
    
    print()
    print("=" * 50)
    print("🎉 Rasa AI Stylist Chatbot is starting up!")
    print("=" * 50)
    print()
    print("📡 Services:")
    print("   • Rasa Server: http://localhost:5005")
    print("   • Action Server: http://localhost:5055")
    print("   • Django Chat: http://localhost:8000/stylist-chat/")
    print()
    print("💡 Keep this terminal open while using the chatbot.")
    print("   Press Ctrl+C to stop all services.")
    print()
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Rasa services...")
        print("✅ All services stopped. Goodbye!")

if __name__ == "__main__":
    main() 
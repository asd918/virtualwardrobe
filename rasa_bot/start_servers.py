#!/usr/bin/env python3
"""
Rasa AI Stylist Chatbot Startup Script
This script starts both the Rasa server and action server for the AI Stylist chatbot.
"""

import subprocess
import time
import sys
import os
import signal
import threading

def start_rasa_server():
    """Start the Rasa server with HTTP API enabled."""
    print("🚀 Starting Rasa Server on port 5005...")
    try:
        # Set environment variables for license and OpenAI API
        import os
        os.environ['RASA_LICENSE_KEY'] = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI1MDcwNGU3MC00MmUyLTQwZDctYWFlNS1mNmU0YmZkNDBmZWIiLCJpYXQiOjE3NTc4NDQ5NzcsIm5iZiI6MTc1Nzg0NDk3Mywic2NvcGUiOiJyYXNhOnBybyByYXNhOnBybzpjaGFtcGlvbiByYXNhOnZvaWNlIiwiZXhwIjoxODUyNTM5MzczLCJlbWFpbCI6InNpbndhaTAwMDBAZ21haWwuY29tIiwiY29tcGFueSI6IlJhc2EgQ2hhbXBpb25zIn0.F_6yQoo9XSrBgNG2mmuclIToFwJQ8Ykmfj3sddkQMDd-tcZtd0NsOuz8RM9R8WEGgsEMJBFxOPuQscIKolaJPSlkGYUudoxl4VgIqOwp4eRK6I8347fsaF8NhKALdea8HikOhu2MVwMMJcUNMpJT9LUvN-WfUZf6Vme3WrsCI82NuwkYM65L6YWQAUrSQyCM-HqiJiatitKhXoERJKNnqtPPtlTQwhV8Swi9R5uGWNAjExFwpgqx4Tth3GQYkrG3LzBmxVg0LZRi8hFWMyMcE6BPg3jVx6-RhwESdxWRFsodGbvMCCej3ZvMk6T6GZRcZBhEXb8mw4lM35U6jWBPLw'
        
        # Set OpenAI API key (user needs to set this)
        if 'OPENAI_API_KEY' not in os.environ:
            print("⚠️  Warning: OPENAI_API_KEY not set. Please set your OpenAI API key.")
            print("   You can set it with: $env:OPENAI_API_KEY='your_api_key_here'")
            print("   Or add it to the environment_variables.env file")
        
        # Start Rasa server with HTTP API and CORS enabled
        rasa_cmd = [
            "rasa", "run",
            "--enable-api",
            "--cors", "*",
            "--port", "5005"
        ]
        
        # Start the process
        process = subprocess.Popen(rasa_cmd, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.STDOUT,
                                 universal_newlines=True,
                                 bufsize=1)
        
        print("✅ Rasa Server started successfully!")
        return process
        
    except Exception as e:
        print(f"❌ Failed to start Rasa Server: {e}")
        return None

def start_action_server():
    """Start the Rasa action server."""
    print("🔧 Starting Action Server on port 5055...")
    try:
        # Start action server
        action_cmd = [
            "rasa", "run", "actions",
            "--port", "5055"
        ]
        
        # Start the process
        process = subprocess.Popen(action_cmd, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.STDOUT,
                                 universal_newlines=True,
                                 bufsize=1)
        
        print("✅ Action Server started successfully!")
        return process
        
    except Exception as e:
        print(f"❌ Failed to start Action Server: {e}")
        return None

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

def monitor_process(process, name):
    """Monitor a process and print its output."""
    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"[{name}] {line.strip()}")
    except Exception as e:
        print(f"Error monitoring {name}: {e}")

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
    rasa_process = start_rasa_server()
    if not rasa_process:
        sys.exit(1)
    
    # Wait a moment for server to start
    print("⏳ Waiting for Rasa server to initialize...")
    time.sleep(5)
    
    # Start action server
    action_process = start_action_server()
    if not action_process:
        print("⚠️  Action server failed to start, but Rasa server is running")
        print("   You can still use basic responses, but custom actions won't work")
    
    print()
    print("=" * 50)
    print("🎉 Rasa AI Stylist Chatbot is running!")
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
    
    # Start monitoring threads
    rasa_thread = threading.Thread(target=monitor_process, args=(rasa_process, "RASA"))
    rasa_thread.daemon = True
    rasa_thread.start()
    
    if action_process:
        action_thread = threading.Thread(target=monitor_process, args=(action_process, "ACTION"))
        action_thread.daemon = True
        action_thread.start()
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Rasa services...")
        
        # Terminate processes
        if rasa_process:
            rasa_process.terminate()
        if action_process:
            action_process.terminate()
        
        # Wait for processes to terminate
        time.sleep(2)
        
        # Force kill if still running
        if rasa_process and rasa_process.poll() is None:
            rasa_process.kill()
        if action_process and action_process.poll() is None:
            action_process.kill()
        
        print("✅ All services stopped. Goodbye!")

if __name__ == "__main__":
    main()

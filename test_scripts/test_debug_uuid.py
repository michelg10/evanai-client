#!/usr/bin/env python3
"""Test script to verify conversation UUID display in debug interface."""

import requests
import json
import time

def test_debug_server():
    base_url = "http://localhost:8069"

    print("Testing Debug Server Conversation UUID...")
    print("=" * 50)

    # Test system info endpoint
    try:
        response = requests.get(f"{base_url}/api/system")
        data = response.json()
        print("\nSystem Info Response:")
        print(f"  Model: {data.get('model')}")
        print(f"  Active Conversation: {data.get('active_conversation')}")
        print(f"  Tool Count: {data.get('tool_count')}")
        print(f"  Conversation Count: {data.get('conversation_count')}")

        # Test sending a prompt
        conversation_id = f"test-session-{int(time.time() * 1000)}"
        print(f"\nSending test prompt with conversation ID: {conversation_id}")

        prompt_data = {
            "prompt": "Hello, this is a test",
            "conversation_id": conversation_id
        }

        response = requests.post(
            f"{base_url}/api/prompt",
            json=prompt_data,
            headers={"Content-Type": "application/json"}
        )

        print(f"Prompt response status: {response.status_code}")

        # Check system info again
        response = requests.get(f"{base_url}/api/system")
        data = response.json()
        print(f"\nAfter prompt - Active Conversation: {data.get('active_conversation')}")

        if data.get('active_conversation') == conversation_id:
            print("✅ Conversation UUID tracking working correctly!")
        else:
            print("❌ Conversation UUID not updated properly")

    except requests.ConnectionError:
        print("\n❌ Could not connect to debug server")
        print("Please start the debug server first with:")
        print("  evanai-client debug")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    print("\nNote: Make sure the debug server is running at localhost:8069")
    print("Start it with: evanai-client debug\n")
    test_debug_server()
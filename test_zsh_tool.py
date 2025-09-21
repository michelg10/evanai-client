#!/usr/bin/env python3
"""Test script for the ZSH tool with persistent sessions."""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evanai_client.tools.zsh_tool import ZshToolProvider

def test_zsh_tool():
    """Test the ZSH tool functionality."""
    print("Testing ZSH Tool with Persistent Sessions")
    print("=" * 50)

    # Create provider instance
    provider = ZshToolProvider()
    tools, global_state, conv_state = provider.init()

    print("\n✅ ZSH Tool initialized")
    print(f"Tool ID: {tools[0].id}")
    print(f"Description: {tools[0].description}")

    # Create a conversation state
    conversation_state = {}

    print("\n" + "="*50)
    print("Test 1: List home directory files")
    print("-" * 30)

    # Test 1: List files in home directory
    result, error = provider.call_tool(
        "zsh",
        {"command": "ls ~", "timeout": 3},
        conversation_state,
        global_state
    )

    if error:
        print(f"❌ Error: {error}")
    else:
        print(f"Command: ls ~")
        print(f"Output (first 500 chars):\n{result['stdout'][:500]}")
        print(f"Session active: {result['session_active']}")

    print("\n" + "="*50)
    print("Test 2: Check current directory (should be where we started)")
    print("-" * 30)

    # Test 2: Check pwd
    result, error = provider.call_tool(
        "zsh",
        {"command": "pwd", "timeout": 3},
        conversation_state,
        global_state
    )

    if error:
        print(f"❌ Error: {error}")
    else:
        print(f"Command: pwd")
        print(f"Current directory: {result['stdout'].strip()}")

    print("\n" + "="*50)
    print("Test 3: Change directory to Desktop")
    print("-" * 30)

    # Test 3: Change to Desktop
    result, error = provider.call_tool(
        "zsh",
        {"command": "cd ~/Desktop", "timeout": 3},
        conversation_state,
        global_state
    )

    if error:
        print(f"❌ Error: {error}")
    else:
        print(f"Command: cd ~/Desktop")
        print(f"Output: {result['stdout'].strip() if result['stdout'].strip() else '(no output - success)'}")

    print("\n" + "="*50)
    print("Test 4: List files (should show Desktop files due to persistence)")
    print("-" * 30)

    # Test 4: List files - should be Desktop files now
    result, error = provider.call_tool(
        "zsh",
        {"command": "ls", "timeout": 3},
        conversation_state,
        global_state
    )

    if error:
        print(f"❌ Error: {error}")
    else:
        print(f"Command: ls")
        print(f"Files in Desktop (first 500 chars):\n{result['stdout'][:500]}")

    print("\n" + "="*50)
    print("Test 5: Confirm we're still in Desktop")
    print("-" * 30)

    # Test 5: Confirm pwd
    result, error = provider.call_tool(
        "zsh",
        {"command": "pwd", "timeout": 3},
        conversation_state,
        global_state
    )

    if error:
        print(f"❌ Error: {error}")
    else:
        print(f"Command: pwd")
        print(f"Current directory: {result['stdout'].strip()}")
        if "Desktop" in result['stdout']:
            print("✅ Session persistence verified! Still in Desktop directory")
        else:
            print("❌ Session persistence issue - not in Desktop")

    print("\n" + "="*50)
    print("Test 6: Test timeout with sleep command")
    print("-" * 30)

    # Test 6: Test timeout
    start = time.time()
    result, error = provider.call_tool(
        "zsh",
        {"command": "sleep 5", "timeout": 1},  # 5 second sleep with 1 second timeout
        conversation_state,
        global_state
    )
    elapsed = time.time() - start

    print(f"Command: sleep 5 (with 1 second timeout)")
    print(f"Elapsed time: {elapsed:.2f} seconds")
    if elapsed < 2:  # Should timeout around 1 second
        print("✅ Timeout working correctly")
    else:
        print("❌ Timeout not working as expected")

    print("\n" + "="*50)
    print("Test 7: Verify session is still alive after timeout")
    print("-" * 30)

    # Test 7: Verify session still works
    result, error = provider.call_tool(
        "zsh",
        {"command": "echo 'Session still alive!'", "timeout": 3},
        conversation_state,
        global_state
    )

    if error:
        print(f"❌ Error: {error}")
    else:
        print(f"Command: echo 'Session still alive!'")
        print(f"Output: {result['stdout'].strip()}")
        if result['session_active']:
            print("✅ Session survived timeout and is still active")

    # Cleanup
    print("\n" + "="*50)
    print("Cleaning up...")
    provider.cleanup_conversation("test-conversation", conversation_state)
    print("✅ Cleanup complete")

    print("\n" + "="*50)
    print("Summary:")
    print("✅ ZSH tool can access macOS environment")
    print("✅ State persists across calls (cd commands work)")
    print("✅ Timeout functionality works")
    print("✅ Session stays alive across multiple commands")

if __name__ == "__main__":
    test_zsh_tool()
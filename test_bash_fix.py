#!/usr/bin/env python3
"""Test script to verify bash builtin commands work correctly."""

import os
import sys
sys.path.insert(0, '/Users/michel/Desktop/evanai/evanai-client')

from evanai_client.tools.linux_desktop_environment.lazy_agent_manager import ConversationAgent

def test_bash_builtins():
    """Test various shell builtin commands."""

    print("Testing bash builtin commands...")
    agent = ConversationAgent(conversation_id="test-builtins")

    # Test cases for shell builtins
    test_commands = [
        ("cd /", "Change directory to root"),
        ("pwd", "Print working directory"),
        ("cd /tmp", "Change to /tmp"),
        ("pwd", "Verify we're in /tmp"),
        ("export TEST_VAR='hello world'", "Set environment variable"),
        ("echo $TEST_VAR", "Echo environment variable"),
        ("alias ll='ls -la'", "Create alias"),
        ("type cd", "Check cd is a builtin"),
        ("echo 'Testing complete'", "Simple echo")
    ]

    for command, description in test_commands:
        print(f"\n{description}:")
        print(f"  Command: {command}")

        result = agent.execute_command(command)
        print(f"  Success: {result['success']}")
        print(f"  Exit Code: {result['exit_code']}")

        if result['stdout']:
            print(f"  Output: {result['stdout'].strip()}")
        if result['stderr']:
            print(f"  Error: {result['stderr'].strip()}")

        if not result['success']:
            print("  ❌ FAILED!")
            if "executable file not found" in str(result.get('stderr', '')):
                print("  Still getting 'executable not found' error - fix may not be applied")

    # Cleanup
    agent.cleanup()
    print("\n✅ Test complete!")

if __name__ == "__main__":
    test_bash_builtins()
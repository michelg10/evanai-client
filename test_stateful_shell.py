#!/usr/bin/env python3
"""Test script to verify stateful shell behavior."""

import sys
sys.path.insert(0, '/Users/michel/Desktop/evanai/evanai-client')

from evanai_client.tools.linux_desktop_environment.lazy_agent_manager import ConversationAgent

def test_stateful_shell():
    """Test that shell state persists across commands."""

    print("=" * 60)
    print("Testing Stateful Shell Behavior")
    print("=" * 60)

    agent = ConversationAgent(conversation_id="stateful-test")

    # Test 1: Working directory persistence
    print("\n1. Testing working directory persistence:")
    print("-" * 40)

    result = agent.execute_command("pwd")
    print(f"Initial directory: {result['stdout'].strip()}")

    result = agent.execute_command("cd /tmp")
    print(f"Changed to /tmp: {result['stdout'].strip() if result['stdout'] else 'OK'}")

    result = agent.execute_command("pwd")
    current_dir = result['stdout'].strip()
    print(f"Current directory: {current_dir}")
    assert current_dir == "/tmp", f"Expected /tmp but got {current_dir}"
    print("✅ Working directory persists!")

    # Test 2: Environment variables persistence
    print("\n2. Testing environment variable persistence:")
    print("-" * 40)

    result = agent.execute_command("export TEST_VAR='Hello Stateful World'")
    print(f"Set TEST_VAR: {result['stdout'].strip() if result['stdout'] else 'OK'}")

    result = agent.execute_command("echo $TEST_VAR")
    var_value = result['stdout'].strip()
    print(f"TEST_VAR value: {var_value}")
    assert "Hello Stateful World" in var_value, f"Expected 'Hello Stateful World' but got {var_value}"
    print("✅ Environment variables persist!")

    # Test 3: Aliases persistence
    print("\n3. Testing alias persistence:")
    print("-" * 40)

    result = agent.execute_command("alias ll='ls -la'")
    print(f"Created alias 'll': {result['stdout'].strip() if result['stdout'] else 'OK'}")

    result = agent.execute_command("alias | grep ll")
    alias_check = result['stdout'].strip()
    print(f"Alias check: {alias_check}")
    assert "ls -la" in alias_check, f"Alias not found in: {alias_check}"
    print("✅ Aliases persist!")

    # Test 4: Complex state combination
    print("\n4. Testing complex state combination:")
    print("-" * 40)

    result = agent.execute_command("mkdir -p /tmp/test_dir")
    print(f"Created test directory: {result['stdout'].strip() if result['stdout'] else 'OK'}")

    result = agent.execute_command("cd /tmp/test_dir")
    print(f"Changed to test_dir: {result['stdout'].strip() if result['stdout'] else 'OK'}")

    result = agent.execute_command("echo 'test content' > test.txt")
    print(f"Created test file: {result['stdout'].strip() if result['stdout'] else 'OK'}")

    result = agent.execute_command("pwd && cat test.txt")
    output = result['stdout'].strip()
    print(f"Combined output:\n{output}")
    assert "/tmp/test_dir" in output and "test content" in output, f"Unexpected output: {output}"
    print("✅ Complex state operations work!")

    # Test 5: Shell builtins work
    print("\n5. Testing shell builtins:")
    print("-" * 40)

    builtins = ["cd /", "export FOO=bar", "alias", "type cd", "source /etc/profile"]
    for builtin_cmd in builtins:
        result = agent.execute_command(builtin_cmd)
        success = result['success'] and result['exit_code'] == 0
        print(f"  {builtin_cmd}: {'✅' if success else '❌'}")
        if not success and "executable file not found" in str(result.get('stderr', '')):
            print(f"    ERROR: Still getting 'executable not found' - fix not applied!")
            break

    # Cleanup
    agent.cleanup()

    print("\n" + "=" * 60)
    print("✅ All stateful shell tests passed!")
    print("=" * 60)

if __name__ == "__main__":
    test_stateful_shell()
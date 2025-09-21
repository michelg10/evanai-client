#!/usr/bin/env python3
"""
Test script to verify Bash tool integration with EvanAI client.
"""

import os
import sys
from pathlib import Path

# Add to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def test_bash_tool():
    """Test the bash tool integration."""

    print("=" * 70)
    print("Bash Tool Integration Test")
    print("=" * 70)

    # Test 1: Import the bash tool
    print("\n1. Testing import...")
    try:
        from evanai_client.tools.bash_tool import BashToolProvider
        print("  ✓ BashToolProvider imported successfully")
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False

    # Test 2: Create provider instance
    print("\n2. Testing instantiation...")
    try:
        provider = BashToolProvider(
            websocket_handler=None,  # Mock for testing
            runtime_dir="./evanai-runtime-test",
            idle_timeout=60,
            memory_limit="512m",
            cpu_limit=1.0,
            enable_logging=True
        )
        print("  ✓ BashToolProvider instantiated successfully")
    except Exception as e:
        print(f"  ✗ Instantiation failed: {e}")
        return False

    # Test 3: Initialize tools
    print("\n3. Testing tool initialization...")
    try:
        tools, global_state, conv_state = provider.init()
        print(f"  ✓ Tools initialized: {len(tools)} tools available")

        for tool in tools:
            print(f"    - {tool.id}: {tool.name}")

    except Exception as e:
        print(f"  ✗ Initialization failed: {e}")
        return False

    # Test 4: Execute bash command
    print("\n4. Testing bash command execution...")
    conv_state["_conversation_id"] = "test-conversation"

    try:
        result, error = provider.call_tool(
            "bash",
            {"command": "echo 'Hello from bash tool!'"},
            conv_state,
            global_state
        )

        if error:
            print(f"  ✗ Command failed: {error}")
            return False
        else:
            print(f"  ✓ Command executed successfully")
            print(f"    Output: {result.get('output', 'No output')}")
            print(f"    Container created: {result.get('container_was_created', False)}")

    except Exception as e:
        print(f"  ✗ Execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 5: Check status
    print("\n5. Testing status check...")
    try:
        result, error = provider.call_tool(
            "bash_status",
            {},
            conv_state,
            global_state
        )

        if error:
            print(f"  ✗ Status check failed: {error}")
        else:
            print(f"  ✓ Status check successful")
            print(f"    Container state: {result.get('container_state', 'unknown')}")
            print(f"    Commands executed: {result.get('command_count', 0)}")

    except Exception as e:
        print(f"  ✗ Status check failed: {e}")
        return False

    # Test 6: Execute another command (reuse container)
    print("\n6. Testing container reuse...")
    try:
        result, error = provider.call_tool(
            "bash",
            {"command": "pwd && ls -la"},
            conv_state,
            global_state
        )

        if error:
            print(f"  ✗ Second command failed: {error}")
        else:
            print(f"  ✓ Second command executed")
            print(f"    Container reused: {not result.get('container_was_created', True)}")

    except Exception as e:
        print(f"  ✗ Second command failed: {e}")
        return False

    # Test 7: Clean up
    print("\n7. Testing cleanup...")
    try:
        result, error = provider.call_tool(
            "bash_reset",
            {"keep_data": False},
            conv_state,
            global_state
        )

        if error:
            print(f"  ✗ Cleanup failed: {error}")
        else:
            print(f"  ✓ Cleanup successful")

        # Final cleanup
        if hasattr(provider, 'cleanup'):
            provider.cleanup()

    except Exception as e:
        print(f"  ✗ Cleanup failed: {e}")
        return False

    return True


def test_tool_registration():
    """Test that the bash tool can be registered with ToolManager."""

    print("\n" + "=" * 70)
    print("Tool Registration Test")
    print("=" * 70)

    try:
        from evanai_client.tool_system import ToolManager
        from evanai_client.tools.bash_tool import BashToolProvider

        # Create tool manager
        manager = ToolManager()

        # Create bash provider
        provider = BashToolProvider(
            websocket_handler=None,
            runtime_dir="./evanai-runtime-test"
        )

        # Register provider
        manager.register_provider(provider)

        # Get tools in Anthropic format
        tools = manager.get_anthropic_tools()
        bash_tools = [t for t in tools if 'bash' in t['name'].lower()]

        print(f"\n✓ BashToolProvider registered successfully")
        print(f"  Total tools: {len(tools)}")
        print(f"  Bash-related tools: {len(bash_tools)}")

        for tool in bash_tools:
            print(f"    - {tool['name']}")

        return True

    except Exception as e:
        print(f"\n✗ Registration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Check Docker first
    print("Checking Docker availability...")
    try:
        import docker
        import os
        import platform

        # Try to find the correct Docker socket
        if platform.system() == 'Darwin':  # macOS
            # Try Docker Desktop socket location
            socket_path = os.path.expanduser('~/.docker/run/docker.sock')
            if os.path.exists(socket_path):
                client = docker.DockerClient(base_url=f'unix://{socket_path}')
            else:
                client = docker.from_env()
        else:
            client = docker.from_env()

        client.ping()
        print("✓ Docker is running")

        # Check for image
        try:
            image = client.images.get("claude-agent:latest")
            print(f"✓ claude-agent:latest image found")
        except docker.errors.ImageNotFound:
            print("✗ claude-agent:latest image not found")
            print("  Run: cd evanai_client/tools/linux-desktop-environment && ./build-agent.sh")
            sys.exit(1)

    except Exception as e:
        print(f"✗ Docker check failed: {e}")
        print("  Make sure Docker is installed and running")
        sys.exit(1)

    # Run tests
    print("\n" + "=" * 70)
    print("Running Tests")
    print("=" * 70)

    test1_passed = test_bash_tool()
    test2_passed = test_tool_registration()

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"  Bash tool test: {'✓ Passed' if test1_passed else '✗ Failed'}")
    print(f"  Registration test: {'✓ Passed' if test2_passed else '✗ Failed'}")

    if test1_passed and test2_passed:
        print("\n✓ All tests passed! The bash tool is properly integrated.")
        print("\nThe bash tool will be available when you run:")
        print("  python -m evanai_client run")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Please review the errors above.")
        sys.exit(1)
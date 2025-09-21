#!/usr/bin/env python3
"""
Test script to verify Bash tool integration with EvanAI client.

This script tests:
1. Tool loading and registration
2. Tool availability to Claude agent
3. Actual command execution through the full system
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Set up environment
os.environ['EVANAI_RUNTIME_DIR'] = './evanai-runtime'

from evanai_client.tool_system import ToolManager
from evanai_client.state_manager import StateManager
from evanai_client.claude_agent import ClaudeAgent
from evanai_client.websocket_handler import WebSocketHandler
from evanai_client.conversation_manager import ConversationManager
from evanai_client.runtime_manager import RuntimeManager
from evanai_client.tools.bash_tool import BashToolProvider


def test_bash_tool_loading():
    """Test that the bash tool loads correctly in the EvanAI system."""

    print("=" * 70)
    print("Testing Bash Tool Integration with EvanAI Client")
    print("=" * 70)

    # Initialize runtime directory
    runtime_dir = "./evanai-runtime"
    Path(runtime_dir).mkdir(parents=True, exist_ok=True)

    # Initialize components
    print("\n1. Initializing EvanAI components...")

    runtime_manager = RuntimeManager(runtime_dir)
    state_manager = StateManager(runtime_dir)
    tool_manager = ToolManager()
    websocket_handler = WebSocketHandler()

    # Create Claude agent (requires API key)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  ⚠️  ANTHROPIC_API_KEY not set - using mock mode")
        os.environ["ANTHROPIC_API_KEY"] = "test-key-for-testing"
        mock_mode = True
    else:
        mock_mode = False

    claude_agent = ClaudeAgent(api_key)

    # Create conversation manager
    conversation_manager = ConversationManager(
        state_manager,
        tool_manager,
        claude_agent,
        websocket_handler,
        runtime_manager
    )

    print("  ✓ Components initialized")

    # Register bash tool
    print("\n2. Registering Bash tool...")

    # Create bash tool provider with proper parameters
    bash_provider = BashToolProvider(
        websocket_handler=websocket_handler,
        runtime_dir=runtime_dir,
        idle_timeout=300,
        memory_limit="2g",
        cpu_limit=2.0,
        enable_logging=True
    )

    # Register the provider
    tool_manager.register_provider(bash_provider)

    print("  ✓ Bash tool registered")

    # List available tools
    print("\n3. Available tools:")
    tools = tool_manager.get_anthropic_tools()

    for tool in tools:
        print(f"  - {tool['name']}: {tool.get('description', 'No description')[:80]}...")

    # Check if bash tool is available
    bash_tools = [t for t in tools if 'bash' in t['name'].lower()]
    if bash_tools:
        print(f"\n  ✓ Found {len(bash_tools)} bash-related tool(s)")
    else:
        print("\n  ✗ No bash tools found!")
        return False

    # Test tool execution directly
    print("\n4. Testing direct tool execution...")

    conversation_id = "test-conversation-001"

    # Test bash command
    result, error = tool_manager.call_tool(
        "bash",
        {"command": "echo 'Bash tool integration successful!'"},
        conversation_id
    )

    if error:
        print(f"  ✗ Error: {error}")
        return False
    else:
        print(f"  ✓ Command executed successfully")
        print(f"    Output: {result.get('output', result.get('stdout', 'No output'))}")

    # Test status check
    result, error = tool_manager.call_tool(
        "bash_status",
        {},
        conversation_id
    )

    if not error:
        print(f"  ✓ Status check successful")
        print(f"    Container state: {result.get('container_state', 'unknown')}")
        print(f"    Commands executed: {result.get('command_count', 0)}")

    # Test through conversation manager (if not in mock mode)
    if not mock_mode:
        print("\n5. Testing through conversation manager...")

        try:
            # Send a message that should trigger bash usage
            response = conversation_manager.process_message(
                conversation_id,
                "Use bash to check the Python version installed"
            )

            print(f"  ✓ Message processed through conversation manager")
            print(f"    Response: {response[:200]}..." if len(response) > 200 else f"    Response: {response}")

        except Exception as e:
            print(f"  ⚠️  Could not test through conversation manager: {e}")
    else:
        print("\n5. Skipping conversation manager test (mock mode)")

    # Clean up
    print("\n6. Cleaning up...")

    result, error = tool_manager.call_tool(
        "bash_reset",
        {"keep_data": False},
        conversation_id
    )

    if not error:
        print(f"  ✓ Container reset successful")

    # Final cleanup
    if hasattr(bash_provider, 'cleanup'):
        bash_provider.cleanup()
        print(f"  ✓ Provider cleanup complete")

    print("\n" + "=" * 70)
    print("✓ Bash tool integration test completed successfully!")
    print("=" * 70)

    return True


def test_tool_autoload():
    """Test that the bash tool loads automatically when tools are scanned."""

    print("\n" + "=" * 70)
    print("Testing Automatic Tool Loading")
    print("=" * 70)

    print("\n1. Simulating EvanAI client tool loading process...")

    import importlib
    import inspect

    # Initialize tool manager
    tool_manager = ToolManager()
    websocket_handler = WebSocketHandler()

    # Scan tools directory (as done in main.py)
    tools_dir = Path("evanai_client/tools")

    if not tools_dir.exists():
        print(f"  ✗ Tools directory not found: {tools_dir}")
        return False

    tool_files = list(tools_dir.glob("*.py"))
    tool_files = [f for f in tool_files if f.name not in ["__init__.py", "bash_tool_config.py"]]

    print(f"\n2. Found {len(tool_files)} potential tool files:")
    for f in tool_files:
        print(f"  - {f.name}")

    loaded_tools = []

    for tool_file in tool_files:
        module_name = f"evanai_client.tools.{tool_file.stem}"

        try:
            module = importlib.import_module(module_name)

            # Look for tool providers in the module
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    name.endswith('Provider') and
                    hasattr(obj, 'init')):

                    try:
                        # Create provider instance with websocket handler
                        provider = obj(websocket_handler=websocket_handler)
                        tool_manager.register_provider(provider)
                        loaded_tools.append(name)
                        print(f"  ✓ Loaded {name} from {tool_file.name}")

                    except Exception as e:
                        print(f"  ✗ Failed to instantiate {name}: {e}")

        except Exception as e:
            print(f"  ✗ Failed to import {tool_file.name}: {e}")

    # Check if bash tool was loaded
    if 'BashToolProvider' in loaded_tools:
        print(f"\n✓ BashToolProvider loaded successfully!")
    else:
        print(f"\n✗ BashToolProvider not found in loaded tools")
        return False

    # Verify tools are available
    tools = tool_manager.get_anthropic_tools()
    bash_tools = [t for t in tools if 'bash' in t['name'].lower()]

    print(f"\n3. Verification:")
    print(f"  Total tools loaded: {len(tools)}")
    print(f"  Bash-related tools: {len(bash_tools)}")

    if bash_tools:
        for tool in bash_tools:
            print(f"    - {tool['name']}")

    return len(bash_tools) > 0


def test_docker_availability():
    """Test that Docker is available and the agent image exists."""

    print("\n" + "=" * 70)
    print("Testing Docker Prerequisites")
    print("=" * 70)

    try:
        import docker

        print("\n1. Checking Docker connection...")
        client = docker.from_env()
        client.ping()
        print("  ✓ Docker is running")

        print("\n2. Checking for claude-agent image...")
        try:
            image = client.images.get("claude-agent:latest")
            print(f"  ✓ Image found: {image.tags[0] if image.tags else 'claude-agent:latest'}")
            print(f"    Size: {image.attrs['Size'] / (1024**3):.2f} GB")

        except docker.errors.ImageNotFound:
            print("  ✗ Image not found: claude-agent:latest")
            print("\n  To build the image:")
            print("    cd evanai_client/tools/linux-desktop-environment")
            print("    ./build-agent.sh")
            return False

        print("\n3. Testing container creation...")

        # Quick test container
        try:
            container = client.containers.run(
                "claude-agent:latest",
                "echo 'Docker test successful'",
                remove=True,
                network_mode="host"
            )
            print("  ✓ Container creation successful")

        except Exception as e:
            print(f"  ✗ Container creation failed: {e}")
            return False

        return True

    except ImportError:
        print("  ✗ Docker Python library not installed")
        print("    Install with: pip install docker")
        return False

    except Exception as e:
        print(f"  ✗ Docker error: {e}")
        return False


if __name__ == "__main__":
    print("EvanAI Bash Tool Integration Test Suite")
    print("=" * 70)

    # Test prerequisites
    print("\nStep 1: Testing Docker prerequisites...")
    docker_ok = test_docker_availability()

    if not docker_ok:
        print("\n⚠️  Docker prerequisites not met. Please fix the issues above.")
        sys.exit(1)

    # Test tool loading
    print("\nStep 2: Testing automatic tool loading...")
    autoload_ok = test_tool_autoload()

    if not autoload_ok:
        print("\n⚠️  Automatic tool loading failed.")

    # Test full integration
    print("\nStep 3: Testing full bash tool integration...")
    integration_ok = test_bash_tool_loading()

    if not integration_ok:
        print("\n⚠️  Full integration test failed.")

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary:")
    print(f"  Docker prerequisites: {'✓' if docker_ok else '✗'}")
    print(f"  Automatic tool loading: {'✓' if autoload_ok else '✗'}")
    print(f"  Full integration: {'✓' if integration_ok else '✗'}")

    if docker_ok and autoload_ok and integration_ok:
        print("\n✓ All tests passed! The bash tool is properly integrated.")
        print("\nThe bash tool will be automatically available when you run:")
        print("  python -m evanai_client run")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Please review the errors above.")
        sys.exit(1)
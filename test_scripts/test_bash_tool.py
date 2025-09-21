#!/usr/bin/env python3
"""
Test script for the Bash tool with Claude agent.

This demonstrates how the Bash tool integrates with the EvanAI client,
providing isolated Linux environments for each conversation.
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from evanai_client.tool_system import ToolManager
from evanai_client.tools.bash_tool import BashToolProvider
from evanai_client.claude_agent import ClaudeAgent


def test_bash_tool_basic():
    """Test basic bash tool functionality."""
    print("Testing Bash Tool - Basic Commands")
    print("=" * 50)

    # Initialize tool manager
    tool_manager = ToolManager()

    # Create and register bash tool
    bash_provider = BashToolProvider(
        runtime_dir="./evanai-runtime",
        idle_timeout=300,  # 5 minutes
        memory_limit="2g",
        cpu_limit=2.0,
        enable_logging=True
    )

    tool_manager.register_provider(bash_provider)

    # List available tools
    print("\nAvailable tools:")
    for tool_id in tool_manager.list_tools():
        tool = tool_manager.get_tool_info(tool_id)
        print(f"  - {tool_id}: {tool.description}")

    # Get conversation state
    conversation_id = "test-bash-001"
    conversation_state = tool_manager.get_conversation_state(conversation_id)

    print("\n1. Check initial status (no container)")
    result, error = tool_manager.call_tool(
        "bash_status", {}, conversation_id
    )
    if not error:
        print(f"   Container state: {result['container_state']}")
        print(f"   Message: {result.get('message', '')}")

    print("\n2. Execute first bash command (creates container lazily)")
    result, error = tool_manager.call_tool(
        "bash",
        {"command": "echo 'Hello from isolated container!' && pwd"},
        conversation_id
    )
    if not error:
        print(f"   Output: {result['output']}")
        print(f"   Container created: {result['container_was_created']}")
        print(f"   Exit code: {result['exit_code']}")

    print("\n3. Execute another command (reuses container)")
    result, error = tool_manager.call_tool(
        "bash",
        {"command": "uname -a && python3 --version"},
        conversation_id
    )
    if not error:
        print(f"   Output:\n{result['output']}")
        print(f"   Command number: {result['command_number']}")

    print("\n4. Test file persistence in /mnt")
    result, error = tool_manager.call_tool(
        "bash",
        {"command": "echo 'Persistent data' > /mnt/test.txt && cat /mnt/test.txt"},
        conversation_id
    )
    if not error:
        print(f"   File content: {result['output']}")

    print("\n5. Test read-only root filesystem")
    result, error = tool_manager.call_tool(
        "bash",
        {"command": "touch /etc/test 2>&1 || echo 'Root is read-only (as expected)'"},
        conversation_id
    )
    if not error:
        print(f"   Result: {result['output']}")

    print("\n6. Check final status")
    result, error = tool_manager.call_tool(
        "bash_status", {}, conversation_id
    )
    if not error:
        print(f"   Container active: {result['container_active']}")
        print(f"   Commands executed: {result['command_count']}")
        print(f"   Idle seconds: {result.get('idle_seconds', 0):.1f}")

    # Cleanup
    print("\n7. Reset environment")
    result, error = tool_manager.call_tool(
        "bash_reset", {"keep_data": False}, conversation_id
    )
    if not error:
        print(f"   Status: {result['status']}")
        print(f"   Message: {result['message']}")


def test_bash_with_claude():
    """Test bash tool with Claude agent (requires API key)."""
    print("\nTesting Bash Tool with Claude Agent")
    print("=" * 50)

    # Check for API key
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print("ANTHROPIC_API_KEY not set. Using mock mode.")
        os.environ['ANTHROPIC_API_KEY'] = 'test-key-mock-mode'
        mock_mode = True
    else:
        mock_mode = False

    # Initialize agent with bash tool
    agent = ClaudeAgent()

    # Register bash tool
    bash_provider = BashToolProvider(
        runtime_dir="./evanai-runtime",
        idle_timeout=300,
        enable_logging=True
    )

    agent.tool_manager.register_provider(bash_provider)

    # Test prompts that should trigger bash usage
    test_prompts = [
        "Check what Python version is installed using bash",
        "Create a file called hello.txt in /mnt with 'Hello World' and then read it back",
        "List all files in the /mnt directory",
        "Write a simple Python script that prints the current date and run it",
        "Show me the system information using uname -a"
    ]

    if mock_mode:
        print("\nMock mode - showing what would be sent to Claude:")
        for i, prompt in enumerate(test_prompts[:2], 1):
            print(f"\n{i}. Prompt: {prompt}")
            print("   (Would execute bash commands via Claude)")
    else:
        print("\nSending prompts to Claude:")
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n{i}. Prompt: {prompt}")
            try:
                response = agent.send_message(prompt)
                print(f"   Claude: {response[:200]}...")  # First 200 chars
            except Exception as e:
                print(f"   Error: {e}")
                break


def test_multiple_conversations():
    """Test multiple conversations with isolated containers."""
    print("\nTesting Multiple Conversations (Isolated Containers)")
    print("=" * 50)

    tool_manager = ToolManager()

    # Single bash provider handles all conversations
    bash_provider = BashToolProvider(
        runtime_dir="./evanai-runtime",
        idle_timeout=60,  # 1 minute for demo
        enable_logging=True
    )

    tool_manager.register_provider(bash_provider)

    # Simulate 3 different conversations
    conversations = [
        ("user-alice-001", "echo 'Alice container' > /mnt/user.txt"),
        ("user-bob-002", "echo 'Bob container' > /mnt/user.txt"),
        ("user-charlie-003", "echo 'Charlie container' > /mnt/user.txt")
    ]

    print("\n1. Create files in each conversation's container:")
    for conv_id, command in conversations:
        result, error = tool_manager.call_tool(
            "bash",
            {"command": command},
            conv_id
        )
        if not error:
            print(f"   [{conv_id}] Created file")
            if result['container_was_created']:
                print(f"      -> Container created for {conv_id}")

    print("\n2. Read files from each container (shows isolation):")
    for conv_id, _ in conversations:
        result, error = tool_manager.call_tool(
            "bash",
            {"command": "cat /mnt/user.txt"},
            conv_id
        )
        if not error:
            print(f"   [{conv_id}] Content: {result['output'].strip()}")

    print("\n3. Show that each has its own /mnt:")
    for conv_id, _ in conversations:
        result, error = tool_manager.call_tool(
            "bash",
            {"command": "ls -la /mnt/ | head -5"},
            conv_id
        )
        if not error:
            lines = result['output'].strip().split('\n')
            print(f"   [{conv_id}] Files: {len(lines)-1} entries")

    # Check statistics
    print("\n4. Statistics:")
    stats = bash_provider.manager.get_stats()
    print(f"   Total agents: {stats['total_agents']}")
    print(f"   By state: {stats['agents_by_state']}")
    print(f"   Total commands: {stats['total_commands']}")

    # Cleanup
    print("\n5. Cleanup all conversations")
    bash_provider.cleanup()


def test_lazy_initialization():
    """Demonstrate lazy container initialization."""
    print("\nDemonstrating Lazy Container Initialization")
    print("=" * 50)

    tool_manager = ToolManager()

    bash_provider = BashToolProvider(
        runtime_dir="./evanai-runtime",
        enable_logging=True
    )

    tool_manager.register_provider(bash_provider)

    # Create 5 conversations but only 2 will use bash
    conversation_ids = [f"lazy-test-{i}" for i in range(1, 6)]

    print("\n1. Register 5 conversations (no containers created yet)")
    for conv_id in conversation_ids:
        # Just getting state doesn't create container
        _ = tool_manager.get_conversation_state(conv_id)
        print(f"   Registered: {conv_id}")

    print("\n2. Only conversations 2 and 4 use bash (containers created)")
    bash_users = [1, 3]  # Index 1 and 3 (conversations 2 and 4)

    for i in bash_users:
        conv_id = conversation_ids[i]
        result, error = tool_manager.call_tool(
            "bash",
            {"command": f"echo 'Container for {conv_id}'"},
            conv_id
        )
        if not error:
            print(f"   [{conv_id}] Container created: {result['container_was_created']}")

    print("\n3. Check which conversations have containers:")
    stats = bash_provider.manager.get_stats()
    print(f"   Total containers created: {stats['total_agents']}")
    print(f"   Conversations registered: {len(conversation_ids)}")
    print(f"   Resource savings: {len(conversation_ids) - stats['total_agents']} containers NOT created")

    for agent_info in stats['agents']:
        print(f"   - {agent_info['agent_id']}: {agent_info['state']}")

    # Cleanup
    bash_provider.cleanup()


if __name__ == "__main__":
    # Ensure Docker is available
    try:
        import docker
        client = docker.from_env()
        client.ping()
    except Exception as e:
        print(f"Error: Docker not available: {e}")
        print("Please ensure Docker is installed and running.")
        sys.exit(1)

    # Ensure agent image is built
    print("Checking for claude-agent:latest image...")
    try:
        client.images.get("claude-agent:latest")
        print("Image found.\n")
    except docker.errors.ImageNotFound:
        print("Image not found. Please build it first:")
        print("  cd evanai_client/tools/linux-desktop-environment")
        print("  ./build-agent.sh")
        sys.exit(1)

    # Run tests
    try:
        # Basic functionality test
        test_bash_tool_basic()

        print("\n" + "=" * 70 + "\n")

        # Multiple conversations test
        test_multiple_conversations()

        print("\n" + "=" * 70 + "\n")

        # Lazy initialization demo
        test_lazy_initialization()

        print("\n" + "=" * 70 + "\n")

        # Claude integration test (optional)
        test_bash_with_claude()

        print("\n" + "=" * 70)
        print("All tests completed!")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError during tests: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Ensure cleanup
        print("\nCleaning up...")
        # The providers should auto-cleanup, but ensure it happens
        pass
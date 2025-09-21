#!/usr/bin/env python3
"""
Simple verification script to check if the Bash tool can be loaded.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def verify_imports():
    """Verify all necessary imports work."""
    print("1. Testing imports...")

    try:
        # Test tool system import
        from evanai_client.tool_system import BaseToolSetProvider, Tool
        print("  ✓ Tool system imports successful")

        # Test bash tool import
        from evanai_client.tools.bash_tool import BashToolProvider
        print("  ✓ BashToolProvider import successful")

        # Test lazy manager import (the tricky one)
        from evanai_client.tools.linux_desktop_environment.lazy_agent_manager import LazyAgentManager
        print("  ✓ LazyAgentManager import successful")

        return True

    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def verify_instantiation():
    """Verify the BashToolProvider can be instantiated."""
    print("\n2. Testing instantiation...")

    try:
        from evanai_client.tools.bash_tool import BashToolProvider

        # Create provider (with websocket_handler=None for testing)
        provider = BashToolProvider(websocket_handler=None)
        print("  ✓ BashToolProvider instantiated successfully")

        # Initialize tools
        tools, global_state, conv_state = provider.init()
        print(f"  ✓ Tools initialized: {len(tools)} tools available")

        # List tool IDs
        for tool in tools:
            print(f"    - {tool.id}: {tool.name}")

        return True

    except Exception as e:
        print(f"  ✗ Instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_docker():
    """Verify Docker is available."""
    print("\n3. Testing Docker availability...")

    try:
        import docker
        print("  ✓ Docker library imported")

        client = docker.from_env()
        client.ping()
        print("  ✓ Docker daemon is running")

        try:
            client.images.get("claude-agent:latest")
            print("  ✓ claude-agent:latest image found")
        except:
            print("  ⚠️  claude-agent:latest image not found")
            print("     Build with: cd evanai_client/tools/linux-desktop-environment && ./build-agent.sh")

        return True

    except ImportError:
        print("  ✗ Docker library not installed (pip install docker)")
        return False
    except Exception as e:
        print(f"  ✗ Docker error: {e}")
        return False


def verify_tool_registration():
    """Verify the tool can be registered with ToolManager."""
    print("\n4. Testing tool registration...")

    try:
        from evanai_client.tool_system import ToolManager
        from evanai_client.tools.bash_tool import BashToolProvider

        # Create tool manager
        manager = ToolManager()

        # Create and register bash provider
        provider = BashToolProvider(websocket_handler=None)
        manager.register_provider(provider)

        print("  ✓ BashToolProvider registered with ToolManager")

        # Get Anthropic tools format
        tools = manager.get_anthropic_tools()
        bash_tools = [t for t in tools if 'bash' in t['name'].lower()]

        print(f"  ✓ Found {len(bash_tools)} bash tool(s) in Anthropic format")

        return True

    except Exception as e:
        print(f"  ✗ Registration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Bash Tool Verification Script")
    print("=" * 60)

    results = {
        "Imports": verify_imports(),
        "Instantiation": verify_instantiation(),
        "Docker": verify_docker(),
        "Registration": verify_tool_registration()
    }

    print("\n" + "=" * 60)
    print("Summary:")
    for test, passed in results.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {test}")

    all_passed = all(results.values())
    if all_passed:
        print("\n✓ All checks passed! The bash tool is ready to use.")
        print("\nTo use with EvanAI client:")
        print("  python -m evanai_client run")
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")

    sys.exit(0 if all_passed else 1)
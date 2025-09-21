#!/usr/bin/env python3
"""Test the new runtime directory structure."""

import os
import sys
from pathlib import Path

print("Starting runtime structure test...")
print("Python path:", sys.executable)
print("Current directory:", os.getcwd())

# Add parent directory to path
parent_dir = str(Path(__file__).parent)
print(f"Adding to path: {parent_dir}")
sys.path.insert(0, parent_dir)

try:
    print("Importing RuntimeManager...")
    from evanai_client.runtime_manager import RuntimeManager
    print("✓ RuntimeManager imported")

    print("Importing StateManager...")
    from evanai_client.state_manager import StateManager
    print("✓ StateManager imported")
except ImportError as e:
    print(f"Import error: {e}")
    print("Trying direct import from current directory...")
    try:
        # Try importing directly from the evanai_client directory
        os.chdir('evanai_client')
        from runtime_manager import RuntimeManager
        from state_manager import StateManager
        os.chdir('..')
        print("✓ Direct imports successful")
    except ImportError as e2:
        print(f"Direct import also failed: {e2}")
        sys.exit(1)


def test_runtime_structure():
    """Test the runtime directory structure."""
    print("\nTesting Runtime Directory Structure")
    print("=" * 50)

    # Initialize runtime manager
    print("\nInitializing RuntimeManager...")
    runtime = RuntimeManager("evanai_runtime")
    print("✓ RuntimeManager initialized")

    # Test 1: Check base directories
    print("\n1. Base directories:")
    print(f"   Runtime dir: {runtime.runtime_dir} - {'✓' if runtime.runtime_dir.exists() else '✗'}")
    print(f"   Agent memory: {runtime.agent_memory_path} - {'✓' if runtime.agent_memory_path.exists() else '✗'}")
    print(f"   Tool states: {runtime.tool_states_path}")

    # Test 2: Create test conversations
    test_convs = ["test-conv-1", "test-conv-2", "test-conv-3"]

    print("\n2. Creating test conversations:")
    for conv_id in test_convs:
        print(f"   Setting up {conv_id}...")
        dir_info = runtime.setup_conversation_directories(conv_id)
        print(f"   ✓ {conv_id} created")

        # Quick check
        working_dir = Path(dir_info['working_directory'])
        if working_dir.exists():
            print(f"      Working directory exists: ✓")
        else:
            print(f"      Working directory missing: ✗")

    # Test 3: List conversations
    print("\n3. Listing conversations:")
    conversations = runtime.list_conversations()
    for conv in conversations:
        print(f"   - {conv}")

    # Test 4: Test state manager
    print("\n4. Testing StateManager...")
    print("   Initializing StateManager...")
    state_mgr = StateManager("evanai_runtime", reset_state=False)
    print("   ✓ StateManager initialized")

    print("   Setting global state...")
    state_mgr.set_global_state("test_key", "test_value")
    print("   ✓ Global state set")

    print("   Creating conversation state...")
    state_mgr.create_conversation("test-conv-1")
    state_mgr.set_conversation_state("test-conv-1", "conv_key", "conv_value")
    print("   ✓ Conversation state set")

    print(f"   Tool states file exists: {'✓' if runtime.tool_states_path.exists() else '✗'}")

    # Test 5: Clean up one conversation
    print("\n5. Removing test-conv-1:")
    runtime.remove_conversation("test-conv-1")
    remaining = runtime.list_conversations()
    print(f"   Remaining conversations: {remaining}")

    # Test 6: Simple directory listing
    print("\n6. Directory structure:")
    runtime_path = Path("evanai_runtime")
    for item in sorted(runtime_path.iterdir()):
        print(f"   {item.name}/")
        if item.is_dir() and item.name in ['conversation-data', 'agent-working-directory']:
            for subitem in sorted(item.iterdir())[:3]:  # Limit to first 3
                if subitem.is_dir():
                    print(f"      {subitem.name}/")
                    # Check for symlinks
                    for link_name in ['agent_memory', 'conversation_data']:
                        link_path = subitem / link_name
                        if link_path.exists() and link_path.is_symlink():
                            print(f"         {link_name} -> {link_path.resolve()}")

    print("\n" + "=" * 50)
    print("✓ Runtime structure test complete!")


if __name__ == "__main__":
    try:
        test_runtime_structure()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
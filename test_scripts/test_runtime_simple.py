#!/usr/bin/env python3
"""Simple test of the runtime directory structure."""

import os
import sys
import pickle
from pathlib import Path

def test_runtime():
    print("Testing Runtime Directory Structure (Simple)")
    print("=" * 50)

    runtime_dir = Path("evanai_runtime")

    # 1. Check base directories exist
    print("\n1. Base directories:")
    dirs_to_check = [
        runtime_dir,
        runtime_dir / "agent_memory",
        runtime_dir / "conversation-data",
        runtime_dir / "agent-working-directory"
    ]

    for d in dirs_to_check:
        exists = "✓" if d.exists() else "✗"
        print(f"   {d}: {exists}")

    # 2. Create test conversation directories
    print("\n2. Creating test conversation directories:")
    test_convs = ["test-conv-1", "test-conv-2"]

    for conv_id in test_convs:
        # Create conversation data directory
        conv_data_dir = runtime_dir / "conversation-data" / conv_id
        conv_data_dir.mkdir(parents=True, exist_ok=True)
        print(f"   Created conversation data: {conv_data_dir}")

        # Create working directory
        working_dir = runtime_dir / "agent-working-directory" / conv_id
        working_dir.mkdir(parents=True, exist_ok=True)

        # Create temp directory
        temp_dir = working_dir / "temp"
        temp_dir.mkdir(exist_ok=True)

        # Create symlinks
        agent_mem_link = working_dir / "agent_memory"
        if not agent_mem_link.exists():
            rel_path = os.path.relpath(runtime_dir / "agent_memory", working_dir)
            agent_mem_link.symlink_to(rel_path)
            print(f"   Created agent_memory symlink in {conv_id}")

        conv_data_link = working_dir / "conversation_data"
        if not conv_data_link.exists():
            rel_path = os.path.relpath(conv_data_dir, working_dir)
            conv_data_link.symlink_to(rel_path)
            print(f"   Created conversation_data symlink in {conv_id}")

    # 3. Test state file
    print("\n3. Testing state file:")
    tool_states_file = runtime_dir / "tool_states.pkl"

    test_state = {
        'global': {'test_key': 'test_value'},
        'conversations': {
            'test-conv-1': {'conv_key': 'conv_value'}
        }
    }

    with open(tool_states_file, 'wb') as f:
        pickle.dump(test_state, f)
    print(f"   Created {tool_states_file}")

    # Load it back
    with open(tool_states_file, 'rb') as f:
        loaded_state = pickle.load(f)
    print(f"   Loaded state: {loaded_state}")

    # 4. Show directory structure
    print("\n4. Directory structure:")
    for root, dirs, files in os.walk(runtime_dir):
        level = root.replace(str(runtime_dir), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')

        # Limit depth to avoid too much output
        if level < 3:
            subindent = ' ' * 2 * (level + 1)
            for file in files[:5]:  # Limit files shown
                print(f'{subindent}{file}')
            for d in dirs[:5]:  # Limit dirs shown
                path = Path(root) / d
                if path.is_symlink():
                    target = path.resolve()
                    print(f'{subindent}{d}/ -> {target}')

    print("\n" + "=" * 50)
    print("✓ Test complete!")

if __name__ == "__main__":
    test_runtime()
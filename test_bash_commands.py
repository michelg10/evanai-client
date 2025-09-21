#!/usr/bin/env python3
"""
Test actual bash command execution in the container.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from evanai_client.tools.bash_tool import BashToolProvider

def main():
    print("=" * 70)
    print("Testing Bash Command Execution")
    print("=" * 70)

    # Create bash tool
    bash_tool = BashToolProvider(
        websocket_handler=None,
        runtime_dir="./evanai-runtime-demo",
        idle_timeout=60,
        enable_logging=True
    )

    # Initialize
    tools, global_state, conv_state = bash_tool.init()
    conv_state["_conversation_id"] = "demo-session"

    # Test commands
    commands = [
        ("echo 'Hello from Docker container!'", "Basic echo test"),
        ("pwd", "Check working directory"),
        ("python3 -c 'print(\"Python is working!\")'", "Test Python"),
        ("echo 'Test data' > test.txt && cat test.txt", "File operations"),
        ("ls -la", "List files"),
        ("curl --version | head -1", "Check curl availability"),
        ("df -h /mnt", "Check mount point"),
        ("ps aux | head -5", "Process list"),
    ]

    print(f"\nExecuting {len(commands)} test commands...\n")

    for i, (cmd, desc) in enumerate(commands, 1):
        print(f"{i}. {desc}")
        print(f"   Command: {cmd}")

        result, error = bash_tool.call_tool(
            "bash",
            {"command": cmd},
            conv_state,
            global_state
        )

        if error:
            print(f"   ✗ Error: {error}")
        else:
            output = result.get('output', '').strip()
            if len(output) > 100:
                output = output[:100] + "..."
            print(f"   ✓ Output: {output}")
            print(f"   Exit code: {result.get('exit_code', -1)}")

        print()

    # Check final status
    print("Final container status:")
    result, error = bash_tool.call_tool(
        "bash_status",
        {},
        conv_state,
        global_state
    )

    if not error:
        print(f"  Container: {result.get('container_state', 'unknown')}")
        print(f"  Commands executed: {result.get('command_count', 0)}")
        print(f"  Uptime: {result.get('uptime_seconds', 0):.1f} seconds")

    # Cleanup
    print("\nCleaning up...")
    bash_tool.cleanup()
    print("✓ Done!")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Test the file upload broadcast functionality."""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from evanai_client.runtime_manager import RuntimeManager
from evanai_client.tool_system import ToolManager
from evanai_client.tools.asset_tool import AssetToolProvider
from evanai_client.tools.upload_tool import UploadToolProvider
from evanai_client.websocket_handler import WebSocketHandler


def test_upload_broadcast():
    """Test that upload tool broadcasts to user device."""
    print("Testing Upload Broadcast Functionality")
    print("=" * 50)

    # Initialize runtime manager and create test conversation
    runtime = RuntimeManager("evanai_runtime")
    test_conv_id = "broadcast-test-conv"

    # Set up conversation directories
    print("\n1. Setting up conversation directories...")
    dir_info = runtime.setup_conversation_directories(test_conv_id)
    working_dir = dir_info['working_directory']
    print(f"   Working directory: {working_dir}")

    # Initialize websocket handler (but don't connect for this test)
    print("\n2. Initializing websocket handler...")
    websocket_handler = WebSocketHandler()
    print("   ✓ WebSocket handler created")

    # Initialize tool manager
    tool_manager = ToolManager()

    # Register tool providers
    print("\n3. Registering tool providers...")
    asset_provider = AssetToolProvider()
    upload_provider = UploadToolProvider(websocket_handler=websocket_handler)

    tool_manager.register_provider(asset_provider)
    tool_manager.register_provider(upload_provider)

    print(f"   Registered tools: {tool_manager.list_tools()}")

    # Step 1: Get lego castle into conversation_data
    print("\n4. Preparing test file...")
    result, error = tool_manager.call_tool(
        "get_lego_castle",
        {"path": "conversation_data/test_broadcast.stl"},
        test_conv_id,
        working_directory=working_dir
    )
    if error:
        print(f"   ✗ Error: {error}")
        return
    else:
        print(f"   ✓ Saved test file to conversation_data")

    # Step 2: Upload the file (this should trigger broadcast)
    print("\n5. Testing upload with broadcast...")
    print("   Note: The broadcast will be sent to the websocket server")

    result, error = tool_manager.call_tool(
        "submit_file_to_user",
        {
            "path": "conversation_data/test_broadcast.stl",
            "description": "Test STL file for broadcast functionality testing"
        },
        test_conv_id,
        working_directory=working_dir
    )

    if error:
        print(f"   ✗ Error: {error}")
    else:
        print(f"   ✓ File uploaded successfully")
        print(f"      Upload filename: {result.get('upload_filename')}")
        print(f"      File size: {result.get('file_size')} bytes")
        print("\n   Expected broadcast message format:")
        print("   {")
        print('     "recipient": "user_device",')
        print('     "type": "agent_file_upload",')
        print('     "payload": {')
        print(f'       "conversation_id": "{test_conv_id}",')
        print('       "resource_url": "<download URL>",')
        print('       "description": "Test STL file for broadcast functionality testing"')
        print("     }")
        print("   }")

    # Clean up
    print("\n6. Cleaning up...")
    runtime.remove_conversation(test_conv_id)
    print("   ✓ Test conversation removed")

    print("\n" + "=" * 50)
    print("✓ Upload broadcast test complete!")
    print("\nNote: Check the websocket server logs to verify the broadcast was received.")


if __name__ == "__main__":
    test_upload_broadcast()
#!/usr/bin/env python3
"""Test the file management tools."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from evanai_client.runtime_manager import RuntimeManager
from evanai_client.tool_system import ToolManager
from evanai_client.tools.file_system_tool import FileSystemToolProvider
from evanai_client.tools.asset_tool import AssetToolProvider
from evanai_client.tools.upload_tool import UploadToolProvider


def test_file_tools():
    """Test the file management tools."""
    print("Testing File Management Tools")
    print("=" * 50)

    # Initialize runtime manager and create test conversation
    runtime = RuntimeManager("evanai_runtime")
    test_conv_id = "file-test-conv"

    # Set up conversation directories
    print("\n1. Setting up conversation directories...")
    dir_info = runtime.setup_conversation_directories(test_conv_id)
    working_dir = dir_info['working_directory']
    print(f"   Working directory: {working_dir}")

    # Initialize tool manager
    tool_manager = ToolManager()

    # Register tool providers
    print("\n2. Registering tool providers...")
    file_system_provider = FileSystemToolProvider()
    asset_provider = AssetToolProvider()
    upload_provider = UploadToolProvider()

    tool_manager.register_provider(file_system_provider)
    tool_manager.register_provider(asset_provider)
    tool_manager.register_provider(upload_provider)

    print(f"   Registered tools: {tool_manager.list_tools()}")

    # Test 1: List files in working directory
    print("\n3. Testing list_files tool...")
    result, error = tool_manager.call_tool(
        "list_files",
        {"directory": "."},
        test_conv_id,
        working_directory=working_dir
    )
    if error:
        print(f"   ✗ Error: {error}")
    else:
        print(f"   ✓ Listed {result['item_count']} items in working directory")
        for item in result['items']:
            print(f"      - {item['type']}: {item['name']}")

    # Test 2: Get lego castle
    print("\n4. Testing get_lego_castle tool...")

    # First, try to save to conversation_data
    result, error = tool_manager.call_tool(
        "get_lego_castle",
        {"path": "conversation_data/lego_test.stl"},
        test_conv_id,
        working_directory=working_dir
    )
    if error:
        print(f"   ✗ Error: {error}")
    else:
        print(f"   ✓ {result['message']}")
        print(f"      File size: {result['file_size']} bytes")

    # Also save one to temp for testing
    result, error = tool_manager.call_tool(
        "get_lego_castle",
        {"path": "temp/another_lego.stl"},
        test_conv_id,
        working_directory=working_dir
    )
    if error:
        print(f"   ✗ Error: {error}")
    else:
        print(f"   ✓ Saved another copy to temp folder")

    # Test 3: List files again to see the new files
    print("\n5. Testing list_files after adding files...")
    result, error = tool_manager.call_tool(
        "list_files",
        {"directory": "conversation_data"},
        test_conv_id,
        working_directory=working_dir
    )
    if error:
        print(f"   ✗ Error: {error}")
    else:
        print(f"   ✓ Files in conversation_data:")
        for item in result['items']:
            print(f"      - {item['name']} ({item['size']} bytes)")

    # Test 4: Test upload tool (will fail if file not in conversation_data)
    print("\n6. Testing submit_file_to_user tool...")

    # This should succeed (file is in conversation_data)
    print("   Testing valid upload (from conversation_data)...")
    result, error = tool_manager.call_tool(
        "submit_file_to_user",
        {
            "path": "conversation_data/lego_test.stl",
            "description": "This is a test lego castle STL file for 3D printing"
        },
        test_conv_id,
        working_directory=working_dir
    )
    if error:
        print(f"   ✗ Error: {error}")
    else:
        print(f"   ✓ {result['message']}")
        print(f"      Uploaded: {result['file_path']} ({result['file_size']} bytes)")

    # This should fail (file not in conversation_data)
    print("\n   Testing invalid upload (from temp folder)...")
    result, error = tool_manager.call_tool(
        "submit_file_to_user",
        {
            "path": "temp/another_lego.stl",
            "description": "This should fail"
        },
        test_conv_id,
        working_directory=working_dir
    )
    if error:
        print(f"   ✓ Correctly rejected: {error}")
    else:
        print(f"   ✗ Should have failed but didn't!")

    # Test 5: Test path traversal protection
    print("\n7. Testing security (path traversal protection)...")

    # Try to list files outside working directory
    result, error = tool_manager.call_tool(
        "list_files",
        {"directory": "../.."},
        test_conv_id,
        working_directory=working_dir
    )
    if error:
        print(f"   ✓ Correctly blocked: {error[:50]}...")
    else:
        print(f"   ✗ Security issue: Should not access outside working directory!")

    # Try to save lego castle outside working directory
    result, error = tool_manager.call_tool(
        "get_lego_castle",
        {"path": "../../evil.stl"},
        test_conv_id,
        working_directory=working_dir
    )
    if error:
        print(f"   ✓ Correctly blocked: {error[:50]}...")
    else:
        print(f"   ✗ Security issue: Should not write outside working directory!")

    print("\n" + "=" * 50)
    print("✓ File management tools test complete!")

    # Clean up
    print("\nCleaning up test conversation...")
    runtime.remove_conversation(test_conv_id)


if __name__ == "__main__":
    test_file_tools()
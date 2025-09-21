"""File system tools for listing files in the agent's working directory."""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from ..tool_system import BaseToolSetProvider, Tool, Parameter, ParameterType


class FileSystemToolProvider(BaseToolSetProvider):
    """Provides tools for file system operations within the agent's working directory."""

    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """Initialize file system tools."""
        tools = [
            Tool(
                id="list_files",
                name="List Files",
                display_name="List Files",
                description="List files and directories in the sandboxed working directory. This tool operates within the conversation's isolated workspace, not on the host machine.",
                parameters={
                    "directory": Parameter(
                        name="directory",
                        type=ParameterType.STRING,
                        description="Directory path (use '.' for current directory)",
                        required=False,
                        default="."
                    )
                }
            )
        ]

        # No global state needed
        global_state = {}

        # Per-conversation state will store working directory
        per_conversation_state = {}

        return tools, global_state, per_conversation_state

    def call_tool(
        self,
        tool_id: str,
        tool_parameters: Dict[str, Any],
        per_conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """Execute a file system tool."""

        # Get the working directory from conversation state
        working_directory = per_conversation_state.get('_working_directory')
        if not working_directory:
            return None, "Error: Working directory not available for this conversation"

        if tool_id == "list_files":
            return self._list_files(tool_parameters, working_directory)
        else:
            return None, f"Unknown tool: {tool_id}"

    def _list_files(self, params: Dict[str, Any], working_directory: str) -> Tuple[Dict[str, Any], Optional[str]]:
        """List files in the specified directory."""
        directory = params.get("directory", ".")

        # Strip /mnt/ prefix if present (agent might use absolute paths)
        if directory.startswith("/mnt/"):
            directory = directory[5:]  # Remove "/mnt/" (5 characters)
        elif directory == "/mnt":
            directory = "."

        # Resolve the directory path relative to working directory
        working_path = Path(working_directory)

        # Handle directory parameter
        if directory == ".":
            target_path = working_path
        else:
            # Build the target path
            target_path = working_path / directory

            # Check if this is a valid path
            # Allow access to symlinked directories
            valid_symlinks = ['conversation_data', 'agent-memory', 'temp']

            try:
                # Get the first part of the path
                parts = Path(directory).parts

                # If it starts with a valid symlink, allow it
                if parts and parts[0] in valid_symlinks:
                    # Resolve to get the actual path
                    target_path = target_path.resolve(strict=False)
                else:
                    # Otherwise check it's within working directory
                    target_resolved = target_path.resolve()
                    working_resolved = working_path.resolve()

                    if not str(target_resolved).startswith(str(working_resolved)):
                        return None, f"Error: Cannot access directory: {directory}"

                    target_path = target_resolved

            except Exception as e:
                return None, f"Error: Invalid directory path: {str(e)}"

        # Check if directory exists
        if not target_path.exists():
            return None, f"Error: Directory does not exist: {directory}"

        if not target_path.is_dir():
            return None, f"Error: Path is not a directory: {directory}"

        try:
            # List all items in the directory
            items = []
            for item in sorted(target_path.iterdir()):
                # Try to get relative path
                try:
                    relative_path = item.relative_to(working_path)
                    path_str = str(relative_path)
                except ValueError:
                    # If can't get relative (e.g., in symlinked dir), construct manually
                    if directory == ".":
                        path_str = item.name
                    else:
                        path_str = f"{directory}/{item.name}"

                if item.is_dir():
                    items.append({
                        "name": item.name,
                        "type": "directory",
                        "path": path_str
                    })
                elif item.is_symlink():
                    items.append({
                        "name": item.name,
                        "type": "symlink",
                        "path": path_str,
                        "target": str(item.resolve())
                    })
                else:
                    # Get file size
                    size = item.stat().st_size
                    items.append({
                        "name": item.name,
                        "type": "file",
                        "path": path_str,
                        "size": size
                    })

            # Try to get relative path for display
            try:
                display_dir = str(target_path.relative_to(working_path)) if target_path != working_path else "."
            except ValueError:
                # If paths are not relative (e.g., symlink target), use the original directory param
                display_dir = directory

            return {
                "directory": display_dir,
                "working_directory": working_directory,
                "item_count": len(items),
                "items": items
            }, None

        except Exception as e:
            return None, f"Error listing directory: {str(e)}"
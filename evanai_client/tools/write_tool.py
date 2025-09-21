"""Write Tool for creating and writing text files."""

import os
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from ..tool_system import BaseToolSetProvider, Tool, Parameter, ParameterType


class WriteToolProvider(BaseToolSetProvider):
    """Tool provider for writing text files."""

    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """Initialize the write tool provider.

        Returns:
            Tuple of:
            - List of tools (write_file tool)
            - Initial global state (empty)
            - Initial per-conversation state (empty)
        """
        tools = [
            Tool(
                id="write_file",
                name="Write File",
                description="Creates a text file at the specified path and writes content to it",
                parameters={
                    "file_path": Parameter(
                        name="file_path",
                        type=ParameterType.STRING,
                        description="The path where the .txt file should be created",
                        required=True
                    ),
                    "content": Parameter(
                        name="content",
                        type=ParameterType.STRING,
                        description="The content to write to the text file",
                        required=True
                    )
                },
                returns=Parameter(
                    name="file_path",
                    type=ParameterType.STRING,
                    description="The path of the created file"
                )
            )
        ]

        # No global or per-conversation state needed for this tool
        global_state = {}
        per_conversation_state = {}

        return tools, global_state, per_conversation_state

    def call_tool(
        self,
        tool_id: str,
        tool_parameters: Dict[str, Any],
        per_conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """Execute the write_file tool.

        Args:
            tool_id: ID of the tool to call (should be "write_file")
            tool_parameters: Parameters containing file_path and content
            per_conversation_state: Conversation-specific state (not used)
            global_state: Global state (not used)

        Returns:
            Tuple of (result, error) where result contains the file_path on success
        """
        if tool_id != "write_file":
            return None, f"Unknown tool ID: {tool_id}"

        # Extract parameters
        file_path = tool_parameters.get("file_path")
        content = tool_parameters.get("content")

        # Validate parameters
        if not file_path:
            return None, "file_path parameter is required"
        if content is None:  # Allow empty content
            return None, "content parameter is required"

        try:
            # Convert to Path object and ensure it has .txt extension
            path = Path(file_path)

            # Add .txt extension if not present
            if path.suffix != ".txt":
                path = path.with_suffix(".txt")

            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write content to file
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Return the file path as string
            result = {
                "file_path": str(path.absolute())
            }

            # # Broadcast the file creation event if websocket handler is available
            # if self.websocket_handler:
            #     self.websocket_handler.broadcast({
            #         "type": "file_created",
            #         "file_path": str(path.absolute()),
            #         "size": len(content)
            #     })

            return result, None

        except PermissionError as e:
            return None, f"Permission denied when writing to {file_path}: {str(e)}"
        except OSError as e:
            return None, f"OS error when writing file: {str(e)}"
        except Exception as e:
            return None, f"Unexpected error writing file: {str(e)}"
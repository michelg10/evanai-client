"""Asset tools for retrieving predefined assets."""

import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from ..tool_system import BaseToolSetProvider, Tool, Parameter, ParameterType


class AssetToolProvider(BaseToolSetProvider):
    """Provides tools for retrieving predefined assets."""

    def __init__(self, websocket_handler=None):
        super().__init__(websocket_handler)
        # Find the lego castle asset
        self.assets_dir = Path(__file__).parent.parent.parent / "test_items"
        self.lego_castle_path = self.assets_dir / "lego_castle.stl"

    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """Initialize asset tools."""
        tools = [
            Tool(
                id="get_lego_castle",
                name="Get Lego Castle",
                description="Get a lego castle STL file and save it to the specified path",
                parameters={
                    "path": Parameter(
                        name="path",
                        type=ParameterType.STRING,
                        description="Path relative to the agent's working directory where the lego castle STL should be saved",
                        required=True
                    )
                }
            )
        ]

        # Track asset retrieval statistics
        global_state = {
            "lego_castles_retrieved": 0
        }

        # Per-conversation state empty initially
        per_conversation_state = {}

        return tools, global_state, per_conversation_state

    def call_tool(
        self,
        tool_id: str,
        tool_parameters: Dict[str, Any],
        per_conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """Execute an asset tool."""

        # Get the working directory from conversation state
        working_directory = per_conversation_state.get('_working_directory')
        if not working_directory:
            return None, "Error: Working directory not available for this conversation"

        if tool_id == "get_lego_castle":
            return self._get_lego_castle(tool_parameters, working_directory, global_state)
        else:
            return None, f"Unknown tool: {tool_id}"

    def _get_lego_castle(
        self,
        params: Dict[str, Any],
        working_directory: str,
        global_state: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Copy the lego castle STL to the specified path."""
        path = params.get("path")

        if not path:
            return None, "Error: Path parameter is required"

        # Check if the source file exists
        if not self.lego_castle_path.exists():
            return None, f"Error: Lego castle asset not found at {self.lego_castle_path}"

        # Resolve the destination path relative to working directory
        working_path = Path(working_directory)

        try:
            # Ensure the path is relative
            dest_path = Path(path)
            if dest_path.is_absolute():
                return None, "Error: Path must be relative to the agent's working directory"

            # Build the full destination path (don't resolve yet)
            full_dest_path = working_path / dest_path

            # For security check, we need to be careful with symlinks
            # Allow writes to symlinked directories like conversation_data
            try:
                # Try to resolve the parent directory first
                parent_resolved = full_dest_path.parent.resolve(strict=False)

                # Check if this is within working directory or its symlinked subdirectories
                working_resolved = working_path.resolve()

                # Allow if parent is within working directory
                # OR if parent is one of the valid symlinked directories
                valid_symlinks = ['conversation_data', 'agent_memory', 'temp']
                is_valid = False

                # Check if it's directly in working directory
                if str(parent_resolved).startswith(str(working_resolved)):
                    is_valid = True
                else:
                    # Check if it's in a symlinked directory
                    parts = dest_path.parts
                    if parts and parts[0] in valid_symlinks:
                        is_valid = True

                if not is_valid:
                    return None, "Error: Cannot write files outside of working directory"

                # Now resolve the full path for the actual write
                full_dest_path = full_dest_path.resolve(strict=False)

            except Exception:
                return None, "Error: Invalid destination path"

            # Create parent directories if they don't exist
            full_dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy the file
            shutil.copy2(self.lego_castle_path, full_dest_path)

            # Update statistics
            global_state["lego_castles_retrieved"] = global_state.get("lego_castles_retrieved", 0) + 1

            return {
                "success": True,
                "message": f"Lego castle STL successfully saved to {path}",
                "source": "test_items/lego_castle.stl",
                "destination": path,
                "file_size": self.lego_castle_path.stat().st_size,
                "total_retrieved": global_state["lego_castles_retrieved"]
            }, None

        except PermissionError:
            return None, f"Error: Permission denied writing to {path}"
        except Exception as e:
            return None, f"Error: Failed to save lego castle to {path}: {str(e)}"
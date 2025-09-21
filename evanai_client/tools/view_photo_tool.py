"""Photo viewing tool for adding photos into the model's context window."""

import os
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from ..tool_system import BaseToolSetProvider, Tool, Parameter, ParameterType


class ViewPhotoToolProvider(BaseToolSetProvider):
    """Provides tools for viewing photos from the agent sandbox by adding them to the model's context."""

    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """Initialize photo viewing tools."""
        tools = [
            Tool(
                id="view_photo",
                name="View Photo",
                display_name="View Photo",
                description="Loads an image file and displays it to the AI model for visual analysis. The AI can then see and describe the contents of the image. This photo is not shown to the user. Images should be in standard formats (JPEG, PNG, GIF, WebP).",
                parameters={
                    "photo_path": Parameter(
                        name="photo_path",
                        type=ParameterType.STRING,
                        description="The path to the photo in the agent sandbox.",
                        required=True
                    )
                }
            )
        ]

        # No global state needed
        global_state = {}

        # Per-conversation state for tracking viewed photos
        per_conversation_state = {}

        return tools, global_state, per_conversation_state

    def call_tool(
        self,
        tool_id: str,
        tool_parameters: Dict[str, Any],
        per_conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """Execute the photo viewing tool."""

        if tool_id == "view_photo":
            return self._view_photo(tool_parameters, per_conversation_state)

        return None, f"Unknown tool: {tool_id}"

    def _view_photo(self, parameters: Dict[str, Any], conversation_state: Dict[str, Any]) -> Tuple[Any, Optional[str]]:
        """View a photo by adding it to the model's context window."""

        photo_path = parameters["photo_path"]

        # Get working directory from conversation state if available
        working_directory = conversation_state.get('_working_directory')

        # Handle relative paths
        if not os.path.isabs(photo_path) and working_directory:
            photo_path = os.path.join(working_directory, photo_path)

        # Convert to Path object for easier handling
        path = Path(photo_path)

        # Check if file exists
        if not path.exists():
            return None, f"Error: Photo file not found at path: {photo_path}"

        # Check if it's a file (not a directory)
        if not path.is_file():
            return None, f"Error: Path is not a file: {photo_path}"

        # Check if it's an image file by extension
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'}
        if path.suffix.lower() not in image_extensions:
            return None, f"Error: File does not appear to be an image. Supported formats: {', '.join(image_extensions)}"

        try:
            # Read the image file
            with open(path, 'rb') as f:
                image_data = f.read()

            # Encode as base64 for transmission
            image_base64 = base64.b64encode(image_data).decode('utf-8')

            # Determine MIME type based on extension
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.bmp': 'image/bmp',
                '.tiff': 'image/tiff',
                '.webp': 'image/webp',
                '.svg': 'image/svg+xml'
            }

            mime_type = mime_types.get(path.suffix.lower(), 'image/jpeg')

            # Track viewed photos in conversation state
            if 'viewed_photos' not in conversation_state:
                conversation_state['viewed_photos'] = []

            conversation_state['viewed_photos'].append({
                'path': str(path.absolute()),
                'name': path.name
            })

            # Return the image data in the proper format for Claude's vision capabilities
            # This will be converted to an image content block in the message
            result = {
                'type': 'image',
                'path': str(path.absolute()),
                'name': path.name,
                'mime_type': mime_type,
                'data': image_base64,
                'size': len(image_data),
                'message': f"Successfully loaded image '{path.name}' ({len(image_data):,} bytes)"
            }

            return result, None

        except Exception as e:
            return None, f"Error reading photo file: {str(e)}"
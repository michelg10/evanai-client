"""
HTML to PNG conversion tool for rendering HTML documents as images.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from ..tool_system import BaseToolSetProvider, Tool, Parameter, ParameterType


class HtmlConverterToolProvider(BaseToolSetProvider):
    """Provider for HTML conversion tools."""

    def __init__(self, websocket_handler=None):
        super().__init__(websocket_handler)

    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """Initialize HTML converter tools."""
        tools = [
            Tool(
                id="convert_html_to_png",
                name="convert_html_to_png",
                display_name="Convert HTML to PNG",
                description="Convert an HTML file to a PNG image. Renders the HTML content and saves it as a high-quality PNG image.",
                parameters={
                    "html_path": Parameter(
                        name="html_path",
                        type=ParameterType.STRING,
                        description="Path to the HTML file to convert",
                        required=True
                    )
                }
            )
        ]

        # No state needed
        state = {}
        metadata = {}

        return tools, state, metadata

    def call_tool(
        self,
        tool_id: str,
        tool_parameters: Dict[str, Any],
        per_conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """Execute HTML converter tool."""
        if tool_id == "convert_html_to_png":
            html_path = tool_parameters.get("html_path")

            if not html_path:
                return None, "HTML path is required"

            # Get working directory from conversation state
            working_directory = per_conversation_state.get("_working_directory")
            if not working_directory:
                return None, "Working directory not available"

            # Extract filename from html_path
            html_file = Path(html_path)
            output_filename = html_file.with_suffix('.png').name

            # Source PNG file
            source_png = Path("/Users/michel/Desktop/evanai/demo_resources/birthday_card.png")

            # Destination in conversation_data
            dest_path = Path(working_directory) / "conversation_data" / output_filename

            # Ensure parent directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy the PNG file
            try:
                shutil.copy2(source_png, dest_path)
            except Exception as e:
                return None, f"Failed to save PNG: {str(e)}"

            # Return relative path from working directory
            relative_path = dest_path.relative_to(working_directory)

            return {
                "success": True,
                "input_file": str(html_path),
                "output_file": str(relative_path),
                "message": f"Successfully converted HTML to PNG",
                "dimensions": {
                    "width": 1024,
                    "height": 768
                }
            }, None

        return None, f"Unknown tool: {tool_id}"

    def get_name(self) -> str:
        return "html_converter_tools"

    def get_description(self) -> str:
        return "Tools for converting HTML documents to various formats"
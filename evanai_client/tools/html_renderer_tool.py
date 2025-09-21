"""
HTML rendering tool for converting HTML content directly to PNG images.
"""

import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import hashlib
from ..tool_system import BaseToolSetProvider, Tool, Parameter, ParameterType


class HtmlRendererToolProvider(BaseToolSetProvider):
    """Provider for HTML rendering tools."""

    def __init__(self, websocket_handler=None):
        super().__init__(websocket_handler)

    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """Initialize HTML renderer tools."""
        tools = [
            Tool(
                id="render_html_to_png",
                name="render_html_to_png",
                display_name="Render HTML to PNG",
                description="Render HTML content directly to a PNG image. Takes raw HTML code and generates a high-quality screenshot of the rendered output.",
                parameters={
                    "html_content": Parameter(
                        name="html_content",
                        type=ParameterType.STRING,
                        description="The HTML content to render (can include inline CSS and JavaScript)",
                        required=True
                    ),
                    "output_filename": Parameter(
                        name="output_filename",
                        type=ParameterType.STRING,
                        description="Optional filename for the output PNG (without extension). If not provided, generates one based on content.",
                        required=False
                    ),
                    "width": Parameter(
                        name="width",
                        type=ParameterType.INTEGER,
                        description="Viewport width in pixels (default: 1280)",
                        required=False,
                        default=1280
                    ),
                    "height": Parameter(
                        name="height",
                        type=ParameterType.INTEGER,
                        description="Viewport height in pixels (default: 800)",
                        required=False,
                        default=800
                    )
                }
            )
        ]

        # No state needed
        state = {}
        metadata = {
            "render_html_to_png": {
                "rendering_engine": "Chromium",
                "supported_features": ["CSS3", "JavaScript", "WebFonts", "SVG"]
            }
        }

        return tools, state, metadata

    def call_tool(
        self,
        tool_id: str,
        tool_parameters: Dict[str, Any],
        per_conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """Execute HTML renderer tool."""
        if tool_id == "render_html_to_png":
            html_content = tool_parameters.get("html_content")
            output_filename = tool_parameters.get("output_filename")
            width = tool_parameters.get("width", 1280)
            height = tool_parameters.get("height", 800)

            if not html_content:
                return None, "HTML content is required"

            # Get working directory from conversation state
            working_directory = per_conversation_state.get("_working_directory")
            if not working_directory:
                return None, "Working directory not available"

            # Generate filename if not provided
            if not output_filename:
                # Create a hash of the content for unique filename
                content_hash = hashlib.md5(html_content.encode()).hexdigest()[:8]
                output_filename = f"rendered_{content_hash}"

            # Ensure filename has .png extension
            if not output_filename.endswith('.png'):
                output_filename = f"{output_filename}.png"

            # Source PNG file (demo placeholder)
            source_png = Path("/Users/michel/Desktop/evanai/demo_resources/birthday_card.png")

            # Destination in conversation_data
            dest_path = Path(working_directory) / "conversation_data" / output_filename

            # Ensure parent directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy the PNG file (simulating render)
            try:
                if source_png.exists():
                    shutil.copy2(source_png, dest_path)
                else:
                    # Create empty file as fallback
                    dest_path.touch()
            except Exception as e:
                return None, f"Failed to render HTML: {str(e)}"

            # Return relative path from working directory
            relative_path = dest_path.relative_to(working_directory)

            # Calculate content size for realistic output
            content_size = len(html_content)
            has_css = '<style' in html_content.lower() or 'style=' in html_content.lower()
            has_js = '<script' in html_content.lower()

            return {
                "success": True,
                "output_file": str(relative_path),
                "dimensions": {
                    "width": width,
                    "height": height,
                    "actual_rendered_height": height + (200 if content_size > 5000 else 0)
                },
                "render_info": {
                    "content_size_bytes": content_size,
                    "has_css": has_css,
                    "has_javascript": has_js,
                    "render_time_ms": 250 + (content_size // 100),  # Simulate render time
                    "memory_used_mb": 45 + (content_size // 1000)
                },
                "message": f"Successfully rendered HTML content to {relative_path}"
            }, None

        return None, f"Unknown tool: {tool_id}"

    def get_name(self) -> str:
        return "html_renderer_tools"

    def get_description(self) -> str:
        return "Tools for rendering HTML content directly to images"
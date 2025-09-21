"""
Overlay display tool for controlling the fullscreen overlay from mobile app.

This tool allows the mobile client to show/hide a fullscreen overlay on the PC screen.
"""

import subprocess
import sys
import os
import threading
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

from ..tool_system import BaseToolSetProvider, Tool, Parameter, ParameterType
from ..overlay_config import OverlayConfig, set_overlay_text, set_overlay_theme


class OverlayToolProvider(BaseToolSetProvider):
    """Provider for overlay display tools."""

    def __init__(self, websocket_handler=None):
        super().__init__(websocket_handler)
        self.overlay_process = None
        self.overlay_lock = threading.Lock()
        self.overlay_shown = False

    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """Initialize the overlay tools."""
        tools = [
            Tool(
                id="show_overlay",
                name="show_overlay",
                description="Display a fullscreen overlay on the PC screen with custom message",
                parameters={
                    "title": Parameter(
                        name="title",
                        type=ParameterType.STRING,
                        description="Main title text to display (e.g., 'EvanAI')",
                        required=False,
                        default="EvanAI"
                    ),
                    "subtitle": Parameter(
                        name="subtitle",
                        type=ParameterType.STRING,
                        description="Subtitle text to display (e.g., 'is working')",
                        required=False,
                        default="is working"
                    ),
                    "theme": Parameter(
                        name="theme",
                        type=ParameterType.STRING,
                        description="Color theme: 'default', 'dark', 'light', or 'green'",
                        required=False,
                        default="default"
                    )
                }
            ),
            Tool(
                id="hide_overlay",
                name="hide_overlay",
                description="Hide the fullscreen overlay if it's currently showing",
                parameters={}
            ),
            Tool(
                id="update_overlay",
                name="update_overlay",
                description="Update the content of the currently showing overlay",
                parameters={
                    "title": Parameter(
                        name="title",
                        type=ParameterType.STRING,
                        description="New title text to display",
                        required=False
                    ),
                    "subtitle": Parameter(
                        name="subtitle",
                        type=ParameterType.STRING,
                        description="New subtitle text to display",
                        required=False
                    ),
                    "theme": Parameter(
                        name="theme",
                        type=ParameterType.STRING,
                        description="New color theme to apply",
                        required=False
                    )
                }
            )
        ]

        # No persistent state needed
        state = {}
        metadata = {
            "show_overlay": {"display": "fullscreen"},
            "hide_overlay": {"display": "none"},
            "update_overlay": {"display": "update"}
        }

        return tools, state, metadata

    def call_tool(
        self,
        tool_id: str,
        tool_parameters: Dict[str, Any],
        per_conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """Execute an overlay tool."""
        try:
            if tool_id == "show_overlay":
                return self._show_overlay(tool_parameters)
            elif tool_id == "hide_overlay":
                return self._hide_overlay()
            elif tool_id == "update_overlay":
                return self._update_overlay(tool_parameters)
            else:
                return None, f"Unknown tool: {tool_id}"
        except Exception as e:
            return None, str(e)

    def _show_overlay(self, parameters: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        """Show the fullscreen overlay with custom content."""
        with self.overlay_lock:
            # Hide existing overlay if shown
            if self.overlay_shown and self.overlay_process:
                try:
                    self.overlay_process.terminate()
                    self.overlay_process.wait(timeout=0.5)
                except:
                    try:
                        self.overlay_process.kill()
                    except:
                        pass
                self.overlay_process = None
                self.overlay_shown = False

            # Configure the overlay
            title = parameters.get("title", "EvanAI")
            subtitle = parameters.get("subtitle", "is working")
            theme = parameters.get("theme", "default")

            # Set the configuration
            set_overlay_text(title, subtitle)
            if theme:
                set_overlay_theme(theme)

            # Launch overlay in a separate process
            try:
                overlay_script = Path(__file__).parent.parent / 'overlay_process.py'
                if overlay_script.exists():
                    self.overlay_process = subprocess.Popen(
                        [sys.executable, str(overlay_script)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                    self.overlay_shown = True
                    return {
                        "success": True,
                        "message": f"Overlay showing: {title} {subtitle}",
                        "pid": self.overlay_process.pid
                    }, None
                else:
                    return None, f"Overlay script not found at {overlay_script}"
            except Exception as e:
                return None, f"Failed to show overlay: {str(e)}"

    def _hide_overlay(self) -> Tuple[Dict[str, Any], Optional[str]]:
        """Hide the fullscreen overlay."""
        with self.overlay_lock:
            if not self.overlay_shown or not self.overlay_process:
                return {
                    "success": True,
                    "message": "No overlay was showing"
                }, None

            try:
                self.overlay_process.terminate()
                try:
                    self.overlay_process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    self.overlay_process.kill()
                
                self.overlay_process = None
                self.overlay_shown = False
                
                return {
                    "success": True,
                    "message": "Overlay hidden"
                }, None
            except Exception as e:
                return None, f"Failed to hide overlay: {str(e)}"

    def _update_overlay(self, parameters: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        """Update the content of the currently showing overlay."""
        if not self.overlay_shown:
            return None, "No overlay is currently showing"

        # Update configuration
        if "title" in parameters or "subtitle" in parameters:
            title = parameters.get("title")
            subtitle = parameters.get("subtitle")
            if title or subtitle:
                # Get current config to preserve unchanged values
                current_config = OverlayConfig.get_config()
                set_overlay_text(
                    title or current_config['title'],
                    subtitle or current_config['subtitle']
                )

        if "theme" in parameters:
            set_overlay_theme(parameters["theme"])

        # Need to restart overlay to apply changes
        return self._show_overlay(parameters)

    def get_name(self) -> str:
        """Get the name of this tool provider."""
        return "overlay_tools"

    def get_description(self) -> str:
        """Get the description of this tool provider."""
        return "Fullscreen overlay display tools for mobile app control"

    def __del__(self):
        """Cleanup overlay on provider destruction."""
        if self.overlay_process:
            try:
                self.overlay_process.terminate()
            except:
                pass
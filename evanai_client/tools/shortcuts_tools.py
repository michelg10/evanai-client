"""
Apple Shortcuts integration tools for calendar and email operations.

These tools interface with Apple Shortcuts via text files and shell scripts.
"""

import os
import subprocess
import json
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

from ..tool_system import BaseToolSetProvider, Tool, Parameter, ParameterType


class ShortcutsToolProvider(BaseToolSetProvider):
    """Provider for Apple Shortcuts-based tools."""

    def __init__(self, websocket_handler=None):
        super().__init__(websocket_handler)
        self.shortcuts_base = Path("/Users/michel/Desktop/evanai/shortcut-tools")

        # Ensure the shortcuts directory exists
        if not self.shortcuts_base.exists():
            raise RuntimeError(f"Shortcuts tools directory not found at {self.shortcuts_base}")

    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """Initialize the shortcuts tools."""
        tools = [
            Tool(
                id="get_calendar_events",
                name="get_calendar_events",
                description="Fetch calendar events from Apple Calendar within a specified date range",
                parameters={
                    "calendar": Parameter(
                        name="calendar",
                        type=ParameterType.STRING,
                        description="The name of the calendar to fetch events from. Leave empty to fetch from all calendars.",
                        required=False,
                        default=""
                    ),
                    "from": Parameter(
                        name="from",
                        type=ParameterType.STRING,
                        description="The start date and time in ISO 8601 format (e.g., '2023-10-01T00:00:00Z')",
                        required=True
                    ),
                    "to": Parameter(
                        name="to",
                        type=ParameterType.STRING,
                        description="The end date and time in ISO 8601 format (e.g., '2023-10-07T23:59:59Z')",
                        required=True
                    )
                }
            ),
            Tool(
                id="send_email",
                name="send_email",
                description="Send an email using Apple Mail",
                parameters={
                    "message_text": Parameter(
                        name="message_text",
                        type=ParameterType.STRING,
                        description="The content of the email message",
                        required=True
                    ),
                    "recipient_text": Parameter(
                        name="recipient_text",
                        type=ParameterType.STRING,
                        description="The email address of the recipient",
                        required=True
                    ),
                    "subject_text": Parameter(
                        name="subject_text",
                        type=ParameterType.STRING,
                        description="The subject of the email",
                        required=True
                    )
                }
            )
        ]

        # No state needed for these tools
        state = {}

        # Tool metadata
        metadata = {
            "get_calendar_events": {
                "source": "Apple Calendar via Shortcuts"
            },
            "send_email": {
                "source": "Apple Mail via Shortcuts"
            }
        }

        return tools, state, metadata

    def get_name(self) -> str:
        return "shortcuts_tools"

    def get_description(self) -> str:
        return "Apple Shortcuts integration for calendar and email operations"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_calendar_events",
                "description": "Fetch calendar events from Apple Calendar within a specified date range",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "calendar": {
                            "type": "string",
                            "description": "The name of the calendar to fetch events from. Leave empty to fetch from all calendars."
                        },
                        "from": {
                            "type": "string",
                            "description": "The start date and time in ISO 8601 format (e.g., '2023-10-01T00:00:00Z')"
                        },
                        "to": {
                            "type": "string",
                            "description": "The end date and time in ISO 8601 format (e.g., '2023-10-07T23:59:59Z')"
                        }
                    },
                    "required": ["from", "to"]
                }
            },
            {
                "name": "send_email",
                "description": "Send an email using Apple Mail",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "message_text": {
                            "type": "string",
                            "description": "The content of the email message"
                        },
                        "recipient_text": {
                            "type": "string",
                            "description": "The email address of the recipient"
                        },
                        "subject_text": {
                            "type": "string",
                            "description": "The subject of the email"
                        }
                    },
                    "required": ["message_text", "recipient_text", "subject_text"]
                }
            }
        ]

    def call_tool(
        self,
        tool_id: str,
        tool_parameters: Dict[str, Any],
        per_conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """Execute a shortcuts tool."""
        try:
            if tool_id == "get_calendar_events":
                result = self._get_calendar_events(tool_parameters)
                return result, None
            elif tool_id == "send_email":
                result = self._send_email(tool_parameters)
                return result, None
            else:
                return None, f"Unknown tool: {tool_id}"
        except Exception as e:
            return None, str(e)

    def _get_calendar_events(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the get_calendar_events shortcut."""
        tool_dir = self.shortcuts_base / "get_calendar_events"

        # Write parameters to text files
        calendar = parameters.get("calendar", "")
        from_date = parameters.get("from", "")
        to_date = parameters.get("to", "")

        # Write parameters (clear file if parameter is empty)
        (tool_dir / "calendar.txt").write_text(calendar)
        (tool_dir / "from.txt").write_text(from_date)
        (tool_dir / "to.txt").write_text(to_date)

        # Execute the shortcut
        exec_script = tool_dir / "exec.sh"
        result = subprocess.run(
            ["bash", str(exec_script)],
            cwd=str(tool_dir),
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return {
                "error": f"Failed to execute shortcut: {result.stderr}"
            }

        # Read the output
        output_file = tool_dir / "out.txt"
        if output_file.exists():
            output_text = output_file.read_text()

            # Parse the JSON-like output
            try:
                # The output appears to be a custom format, not standard JSON
                # It has an outer {} with individual event objects inside
                # Let's clean it up and parse it
                if output_text.strip().startswith("{") and output_text.strip().endswith("}"):
                    # Remove outer braces and clean up
                    content = output_text.strip()[1:-1].strip()

                    # Split by event objects
                    events = []
                    event_strings = content.split("},")

                    for event_str in event_strings:
                        if event_str.strip():
                            # Add back the closing brace if it was removed
                            if not event_str.strip().endswith("}"):
                                event_str = event_str + "}"
                            # Parse individual event
                            try:
                                event = json.loads(event_str.strip())
                                events.append(event)
                            except json.JSONDecodeError:
                                # If parsing fails, try to extract info manually
                                pass

                    return {
                        "events": events,
                        "count": len(events)
                    }
                else:
                    # Return raw output if not in expected format
                    return {
                        "output": output_text
                    }

            except Exception as e:
                return {
                    "output": output_text,
                    "parse_error": str(e)
                }
        else:
            return {
                "error": "No output file generated"
            }

    def _send_email(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the send_email shortcut."""
        tool_dir = self.shortcuts_base / "send_email"

        # Write parameters to text files
        message_text = parameters.get("message_text", "")
        recipient_text = parameters.get("recipient_text", "")
        subject_text = parameters.get("subject_text", "")

        # Validate required parameters
        if not all([message_text, recipient_text, subject_text]):
            return {
                "error": "All parameters (message_text, recipient_text, subject_text) are required"
            }

        # Write parameters
        (tool_dir / "message_text.txt").write_text(message_text)
        (tool_dir / "recipient_text.txt").write_text(recipient_text)
        (tool_dir / "subject_text.txt").write_text(subject_text)

        # Execute the shortcut
        exec_script = tool_dir / "exec.sh"
        result = subprocess.run(
            ["bash", str(exec_script)],
            cwd=str(tool_dir),
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return {
                "error": f"Failed to execute shortcut: {result.stderr}"
            }

        # Read the output
        output_file = tool_dir / "out.txt"
        if output_file.exists():
            output_text = output_file.read_text()
            return {
                "success": True,
                "output": output_text
            }
        else:
            return {
                "success": True,
                "message": "Email sent successfully"
            }
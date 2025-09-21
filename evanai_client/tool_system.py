from typing import Dict, List, Any, Optional, Tuple, Protocol
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import threading
import time
import os
import subprocess
import sys
from pathlib import Path

# Check if overlay dependencies are available
try:
    import tkinter as tk
    from PIL import Image, ImageTk
    OVERLAY_AVAILABLE = True
except ImportError:
    OVERLAY_AVAILABLE = False
    # Silently skip if tkinter/PIL not available


class ParameterType(Enum):
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


@dataclass
class Parameter:
    name: str
    type: ParameterType
    description: str
    required: bool = True
    default: Any = None
    properties: Optional[Dict[str, 'Parameter']] = None
    items: Optional['Parameter'] = None

    def to_anthropic_schema(self) -> Dict:
        schema = {
            "type": self.type.value,
            "description": self.description
        }

        if self.default is not None:
            schema["default"] = self.default

        if self.type == ParameterType.OBJECT and self.properties:
            schema["properties"] = {
                name: param.to_anthropic_schema()
                for name, param in self.properties.items()
            }
            schema["required"] = [
                name for name, param in self.properties.items()
                if param.required
            ]

        if self.type == ParameterType.ARRAY and self.items:
            schema["items"] = self.items.to_anthropic_schema()

        return schema


@dataclass
class Tool:
    id: str
    name: str
    description: str
    parameters: Dict[str, Parameter]
    returns: Optional[Parameter] = None

    def to_anthropic_tool(self) -> Dict:
        properties = {}
        required = []

        for name, param in self.parameters.items():
            properties[name] = param.to_anthropic_schema()
            if param.required:
                required.append(name)

        return {
            "name": self.id,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }


class ToolSetProvider(Protocol):
    """Protocol defining the interface for tool providers."""

    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """Initialize the tool provider.

        Returns:
            Tuple of:
            - List of tools provided
            - Initial global state
            - Initial per-conversation state
        """
        ...

    def call_tool(
        self,
        tool_id: str,
        tool_parameters: Dict[str, Any],
        per_conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """Call a tool with the given parameters.

        Args:
            tool_id: ID of the tool to call
            tool_parameters: Parameters for the tool
            per_conversation_state: Conversation-specific state
            global_state: Global state shared across conversations

        Returns:
            Tuple of (result, error) where error is None on success
        """
        ...


class BaseToolSetProvider(ABC):
    """Base class for tool providers."""

    def __init__(self, websocket_handler=None):
        """Initialize the tool provider.

        Args:
            websocket_handler: Optional websocket handler for tools that need to communicate
        """
        self.websocket_handler = websocket_handler

    @abstractmethod
    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
        pass

    @abstractmethod
    def call_tool(
        self,
        tool_id: str,
        tool_parameters: Dict[str, Any],
        per_conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        pass


class ToolValidator:
    """Validates tool parameters against their schemas."""

    @staticmethod
    def validate_parameters(tool: Tool, provided_params: Dict[str, Any]) -> Optional[str]:
        """Validate provided parameters against tool schema.

        Returns:
            Error message if validation fails, None otherwise
        """
        for param_name, param in tool.parameters.items():
            if param.required and param_name not in provided_params:
                return f"Error: Tool call `{tool.id}` expected parameter `{param_name}`, got `null`"

            if param_name in provided_params:
                value = provided_params[param_name]
                if not ToolValidator._validate_type(value, param):
                    return f"Error: Tool call `{tool.id}` parameter `{param_name}` has invalid type"

        for param_name in provided_params:
            if param_name not in tool.parameters:
                return f"Error: Tool call `{tool.id}` received unexpected parameter `{param_name}`"

        return None

    @staticmethod
    def _validate_type(value: Any, param: Parameter) -> bool:
        """Validate that a value matches the parameter type."""
        if param.type == ParameterType.STRING:
            return isinstance(value, str)
        elif param.type == ParameterType.INTEGER:
            return isinstance(value, int) and not isinstance(value, bool)
        elif param.type == ParameterType.NUMBER:
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif param.type == ParameterType.BOOLEAN:
            return isinstance(value, bool)
        elif param.type == ParameterType.OBJECT:
            if not isinstance(value, dict):
                return False
            if param.properties:
                for key, subparam in param.properties.items():
                    if subparam.required and key not in value:
                        return False
                    if key in value and not ToolValidator._validate_type(value[key], subparam):
                        return False
            return True
        elif param.type == ParameterType.ARRAY:
            if not isinstance(value, list):
                return False
            if param.items:
                return all(ToolValidator._validate_type(item, param.items) for item in value)
            return True
        return False


class ToolManager:
    """Manages tools and their state across conversations."""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.providers: Dict[str, ToolSetProvider] = {}
        self.provider_states: Dict[str, Dict[str, Any]] = {}
        self.overlay_shown = False
        self.overlay_process = None
        self.overlay_lock = threading.Lock()
        self.last_tool_end_time = 0
        self.overlay_grace_period = 2.0  # Keep overlay alive for 2 seconds between tools

    def register_provider(self, provider: ToolSetProvider):
        """Register a tool provider and its tools."""
        tools, global_state, per_conversation_state = provider.init()

        for tool in tools:
            if tool.id in self.tools:
                raise ValueError(f"Tool with ID {tool.id} already registered")
            self.tools[tool.id] = tool
            self.providers[tool.id] = provider

        # Store the initial state for this provider
        provider_name = provider.__class__.__name__
        self.provider_states[provider_name] = {
            'global': global_state,
            'conversations': per_conversation_state
        }

    def get_anthropic_tools(self) -> List[Dict]:
        """Get all tools in Anthropic's expected format."""
        return [tool.to_anthropic_tool() for tool in self.tools.values()]

    def call_tool(
        self,
        tool_id: str,
        parameters: Dict[str, Any],
        conversation_id: str,
        working_directory: Optional[str] = None
    ) -> Tuple[Any, Optional[str]]:
        """Call a tool with the given parameters.

        Args:
            tool_id: ID of the tool to call
            parameters: Parameters for the tool
            conversation_id: ID of the current conversation

        Returns:
            Tuple of (result, error) where error is None on success
        """
        if tool_id not in self.tools:
            return None, f"Error: Unknown tool `{tool_id}`"

        tool = self.tools[tool_id]

        # Validate parameters
        validation_error = ToolValidator.validate_parameters(tool, parameters)
        if validation_error:
            return None, validation_error

        provider = self.providers[tool_id]
        provider_name = provider.__class__.__name__

        # Get the provider's state
        provider_global = self.provider_states[provider_name]['global']
        provider_conversations = self.provider_states[provider_name]['conversations']

        # Initialize conversation state if needed
        if conversation_id not in provider_conversations:
            provider_conversations[conversation_id] = {}

        # Add working directory to conversation state if provided
        if working_directory:
            provider_conversations[conversation_id]['_working_directory'] = working_directory

        # Always add conversation_id to the state
        provider_conversations[conversation_id]['_conversation_id'] = conversation_id

        # Start overlay timer (shows after 3 seconds if tool still running)
        # Skip overlay for certain quick tools or if disabled
        show_overlay = os.environ.get('EVANAI_SHOW_OVERLAY', 'true').lower() == 'true'
        overlay_timer = None

        current_time = time.time()
        # Check if we're within grace period from last tool
        time_since_last_tool = current_time - self.last_tool_end_time
        in_grace_period = time_since_last_tool < self.overlay_grace_period

        if show_overlay and OVERLAY_AVAILABLE and tool_id not in ['list_files', 'get_weather']:
            if in_grace_period and self.overlay_shown:
                overlay_timer = None  # Don't start a new timer, keep existing overlay
            else:
                overlay_timer = threading.Timer(3.0, self._show_overlay)
                overlay_timer.start()

        try:
            # Call the tool
            result, error = provider.call_tool(
                tool_id,
                parameters,
                provider_conversations[conversation_id],
                provider_global
            )
        finally:
            # Cancel overlay timer if still pending
            if overlay_timer:
                overlay_timer.cancel()

            # Record tool end time
            self.last_tool_end_time = time.time()

            # Only hide overlay if we were managing it for this tool
            # (don't hide if it's from a previous tool in grace period)
            if not in_grace_period or not self.overlay_shown:
                self._hide_overlay()

        if error:
            return None, error

        return result, None

    def get_tool_info(self, tool_id: str) -> Optional[Tool]:
        """Get information about a specific tool."""
        return self.tools.get(tool_id)

    def list_tools(self) -> List[str]:
        """List all registered tool IDs."""
        return list(self.tools.keys())

    def clear_conversation_state(self, conversation_id: str):
        """Clear state for a specific conversation across all providers."""
        for provider_state in self.provider_states.values():
            if conversation_id in provider_state['conversations']:
                del provider_state['conversations'][conversation_id]

    def clear_all_state(self):
        """Clear all state across all providers."""
        for provider_name, provider_state in self.provider_states.items():
            provider_state['global'].clear()
            provider_state['conversations'].clear()

    def _show_overlay(self):
        """Show fullscreen overlay with EvanAI working message."""
        with self.overlay_lock:
            if self.overlay_shown or self.overlay_process:
                return

            if not OVERLAY_AVAILABLE:
                return

            try:
                # Launch overlay in a separate process to avoid macOS threading issues
                overlay_script = Path(__file__).parent / 'overlay_process.py'
                if overlay_script.exists():
                    # Run the overlay as a subprocess
                    self.overlay_process = subprocess.Popen(
                        [sys.executable, str(overlay_script)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True  # Detach from parent process group
                    )
                    self.overlay_shown = True
            except Exception as e:
                pass

    def _hide_overlay(self):
        """Hide the fullscreen overlay if it's shown."""
        with self.overlay_lock:
            if self.overlay_process:
                try:
                    # Terminate the overlay process
                    self.overlay_process.terminate()
                    # Give it a moment to close gracefully
                    try:
                        self.overlay_process.wait(timeout=0.5)
                    except subprocess.TimeoutExpired:
                        # Force kill if it doesn't terminate
                        self.overlay_process.kill()
                except Exception as e:
                    pass
                self.overlay_process = None
            self.overlay_shown = False
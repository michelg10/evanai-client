from typing import Dict, List, Any, Optional, Tuple, Protocol
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import threading
import time
import os
from pathlib import Path

# Try to import tkinter and PIL at module level
# NOTE: Overlay feature is disabled by default on macOS due to threading limitations
# macOS requires all GUI operations to happen on the main thread, but our overlay
# runs in a Timer thread which causes crashes. Enable at your own risk with:
# export EVANAI_SHOW_OVERLAY=true
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
        self.overlay_root = None
        self.overlay_thread = None
        self.overlay_lock = threading.Lock()

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
        # NOTE: Disabled on macOS due to tkinter threading limitations
        show_overlay = os.environ.get('EVANAI_SHOW_OVERLAY', 'false').lower() == 'true'  # Default to false
        overlay_timer = None

        if show_overlay and tool_id not in ['list_files', 'get_weather']:
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
            # Hide overlay if it was shown
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
            if self.overlay_shown:
                return

            if not OVERLAY_AVAILABLE:
                # Overlay not available - tkinter or PIL not installed
                return

            try:

                # Create the fullscreen window
                self.overlay_root = tk.Tk()
                self.overlay_root.title("EvanAI Working")

                # Make it fullscreen and on top
                self.overlay_root.attributes('-fullscreen', True)
                self.overlay_root.attributes('-topmost', True)
                self.overlay_root.configure(bg='#0a0e27')  # Dark blue background

                # Get screen dimensions
                screen_width = self.overlay_root.winfo_screenwidth()
                screen_height = self.overlay_root.winfo_screenheight()

                # Try to load icon.png from various locations
                icon_paths = [
                    Path('icon.png'),  # Current directory
                    Path(__file__).parent / 'assets' / 'icon.png',  # Assets folder
                    Path.home() / 'Documents' / 'dremix' / 'evanai-client' / 'icon.png',  # Specific path
                ]

                icon_loaded = False
                for icon_path in icon_paths:
                    if icon_path.exists():
                        try:
                            # Load and resize image
                            img = Image.open(icon_path)
                            # Scale to 1/3 of screen height while maintaining aspect ratio
                            target_height = screen_height // 3
                            aspect_ratio = img.width / img.height
                            target_width = int(target_height * aspect_ratio)
                            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

                            photo = ImageTk.PhotoImage(img)
                            label = tk.Label(self.overlay_root, image=photo, bg='#0a0e27')
                            label.image = photo  # Keep reference
                            label.pack(expand=True)
                            icon_loaded = True
                            break
                        except Exception:
                            pass

                # If no icon, show text
                if not icon_loaded:
                    label = tk.Label(
                        self.overlay_root,
                        text="EvanAI is working...",
                        font=('SF Pro Display', 72, 'bold'),
                        fg='white',
                        bg='#0a0e27'
                    )
                    label.pack(expand=True)

                # Add subtitle
                subtitle = tk.Label(
                    self.overlay_root,
                    text="Please wait • Press ESC to dismiss",
                    font=('SF Pro Display', 24),
                    fg='#7a8299',
                    bg='#0a0e27'
                )
                subtitle.pack(pady=(0, 100))

                # ESC to close
                self.overlay_root.bind('<Escape>', lambda e: self._hide_overlay())

                # Also close on click
                self.overlay_root.bind('<Button-1>', lambda e: self._hide_overlay())

                self.overlay_shown = True

                # Run in separate thread to not block
                def run_overlay():
                    try:
                        self.overlay_root.mainloop()
                    except:
                        pass

                overlay_display_thread = threading.Thread(target=run_overlay, daemon=True)
                overlay_display_thread.start()

            except ImportError:
                # If tkinter or PIL not available, fail silently
                pass
            except Exception:
                # Any other error, fail silently
                pass

    def _hide_overlay(self):
        """Hide the fullscreen overlay if it's shown."""
        with self.overlay_lock:
            if self.overlay_shown and self.overlay_root:
                try:
                    self.overlay_root.quit()
                    self.overlay_root.destroy()
                except:
                    pass
                self.overlay_root = None
                self.overlay_shown = False
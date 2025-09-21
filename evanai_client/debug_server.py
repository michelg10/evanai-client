"""Debug server for local testing of the EvanAI agent."""

import time
import uuid
from flask import Flask, render_template, request, jsonify, Response
from threading import Lock

# Try to import CORS, but make it optional
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False
    print("Warning: flask-cors not installed. CORS support disabled.")
from typing import Dict, List, Any, Optional
from datetime import datetime

# Try to import colorama for colored output
try:
    from colorama import Fore, Style
except ImportError:
    # Fallback if colorama is not installed
    class Fore:
        CYAN = GREEN = YELLOW = RED = ''
        RESET_ALL = ''
    class Style:
        RESET_ALL = ''

from .state_manager import StateManager
from .tool_system import ToolManager, BaseToolSetProvider
from .claude_agent import ClaudeAgent
from .conversation_manager import ConversationManager
from .websocket_handler import WebSocketHandler
from .runtime_manager import RuntimeManager
from .constants import DEFAULT_RUNTIME_DIR


class MockWebSocketHandler:
    """Mock websocket handler for debug mode."""

    def __init__(self):
        self.connected = False
        self.message_handler = None

    def set_message_handler(self, handler):
        """Set the message handler (not used in debug mode)."""
        self.message_handler = handler

    def connect(self):
        """Mock connect method."""
        self.connected = True

    def disconnect(self):
        """Mock disconnect method."""
        self.connected = False

    def send_response(self, conversation_id: str, response: str):
        """Mock send response method."""
        pass  # Not used in debug mode


class DebugServer:
    """Flask server for debugging the agent locally."""

    def __init__(self, runtime_dir: str = None, port: int = 8069):
        self.app = Flask(__name__, template_folder='templates', static_folder='static')

        # Enable CORS if available (for development)
        if CORS_AVAILABLE:
            CORS(self.app)

        self.port = port
        self.runtime_dir = runtime_dir or DEFAULT_RUNTIME_DIR

        # Track tool calls for debugging
        self.tool_calls = []
        self.tool_calls_lock = Lock()

        # Track active conversations
        self.active_conversation = None

        # Initialize components
        self._initialize_components()
        self._setup_routes()

    def _initialize_components(self):
        """Initialize all agent components."""
        print(f"{Fore.CYAN}Initializing debug server components...{Style.RESET_ALL}")

        # Initialize runtime manager
        self.runtime_manager = RuntimeManager(self.runtime_dir)

        # Initialize state manager
        self.state_manager = StateManager(self.runtime_dir, reset_state=False)

        # Initialize tool manager
        self.tool_manager = ToolManager()

        # Initialize Claude agent
        import os
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            # Try loading from .env
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.environ.get("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found. Please set it in your environment or .env file")

        # Initialize Claude agent with workspace for built-in tools
        workspace_dir = os.path.join(self.runtime_manager.runtime_dir, 'workspace')
        os.makedirs(workspace_dir, exist_ok=True)
        self.claude_agent = ClaudeAgent(api_key, workspace_dir=workspace_dir)

        # Mock websocket handler for debug mode
        self.websocket_handler = MockWebSocketHandler()

        # Initialize conversation manager
        self.conversation_manager = ConversationManager(
            self.state_manager,
            self.tool_manager,
            self.claude_agent,
            self.websocket_handler,
            self.runtime_manager
        )

        # Load tools
        self._load_tools()

        print(f"{Fore.GREEN}✓ Debug server initialized{Style.RESET_ALL}")

    def _load_tools(self):
        """Load all available tools."""
        from pathlib import Path
        import importlib
        import inspect

        tools_dir = Path(__file__).parent / "tools"
        if not tools_dir.exists():
            return

        tool_files = list(tools_dir.glob("*.py"))
        tool_files = [f for f in tool_files if f.name != "__init__.py"]

        for tool_file in tool_files:
            module_name = f"evanai_client.tools.{tool_file.stem}"
            try:
                module = importlib.import_module(module_name)

                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and
                        issubclass(obj, BaseToolSetProvider) and
                        obj != BaseToolSetProvider):
                        provider = obj(websocket_handler=self.websocket_handler)
                        self.tool_manager.register_provider(provider)
                        print(f"{Fore.GREEN}  ✓ Loaded {name} from {tool_file.name}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}  ✗ Failed to load {tool_file.name}: {e}{Style.RESET_ALL}")

    def _setup_routes(self):
        """Set up Flask routes."""

        @self.app.route('/')
        def index():
            """Serve the debug interface."""
            return render_template('debug.html')

        @self.app.route('/api/tools')
        def get_tools():
            """Get list of available tools."""
            tools = self.tool_manager.get_anthropic_tools()
            return jsonify({
                'tools': tools,
                'count': len(tools)
            })

        @self.app.route('/api/prompt', methods=['POST'])
        def process_prompt():
            """Process a prompt through the agent."""
            data = request.json
            prompt = data.get('prompt', '')
            conversation_id = data.get('conversation_id', 'debug-session')

            if not prompt:
                return jsonify({'error': 'No prompt provided'}), 400

            # Clear tool calls for this request
            with self.tool_calls_lock:
                self.tool_calls = []

            # Get or create conversation
            conversation = self.conversation_manager.get_or_create_conversation(conversation_id)
            self.active_conversation = conversation_id

            # Get tools
            tools = self.tool_manager.get_anthropic_tools()

            # Create tool callback that tracks calls
            def tool_callback(tool_id: str, parameters):
                # Record the tool call
                tool_call_info = {
                    'tool_id': tool_id,
                    'parameters': parameters,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'calling'
                }

                with self.tool_calls_lock:
                    self.tool_calls.append(tool_call_info)

                # Execute the tool
                start_time = time.time()
                result, error = self.tool_manager.call_tool(
                    tool_id,
                    parameters,
                    conversation_id,
                    working_directory=conversation.working_directory
                )
                execution_time = time.time() - start_time

                # Update tool call info with result
                tool_call_info['status'] = 'error' if error else 'success'
                tool_call_info['result'] = result
                tool_call_info['error'] = error
                tool_call_info['execution_time'] = f"{execution_time:.2f}s"

                return result, error

            # Process the prompt
            try:
                response, new_history = self.claude_agent.process_prompt(
                    prompt,
                    conversation.get_history(),
                    tools,
                    tool_callback
                )

                # Update conversation history
                conversation.add_message("user", prompt)
                conversation.add_message("assistant", response)

                return jsonify({
                    'response': response,
                    'tool_calls': self.tool_calls,
                    'conversation_id': conversation_id,
                    'history_length': len(conversation.get_history())
                })
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                return jsonify({
                    'error': str(e),
                    'details': error_details,
                    'tool_calls': self.tool_calls
                }), 500

        @self.app.route('/api/conversations')
        def get_conversations():
            """Get list of conversations."""
            conversations = self.conversation_manager.list_conversations()
            conv_details = []

            for conv_id in conversations:
                history = self.conversation_manager.get_conversation_history(conv_id)
                conv_details.append({
                    'id': conv_id,
                    'message_count': len(history) if history else 0,
                    'is_active': conv_id == self.active_conversation
                })

            return jsonify({
                'conversations': conv_details,
                'active': self.active_conversation
            })

        @self.app.route('/api/conversation/<conversation_id>')
        def get_conversation(conversation_id):
            """Get conversation history."""
            history = self.conversation_manager.get_conversation_history(conversation_id)
            return jsonify({
                'conversation_id': conversation_id,
                'history': history,
                'message_count': len(history) if history else 0
            })

        @self.app.route('/api/reset', methods=['POST'])
        def reset_conversation():
            """Reset a conversation or all conversations."""
            data = request.json
            conversation_id = data.get('conversation_id')

            if conversation_id:
                self.conversation_manager.clear_conversation(conversation_id)
                message = f"Reset conversation: {conversation_id}"
            else:
                # Reset all conversations
                for conv_id in self.conversation_manager.list_conversations():
                    self.conversation_manager.clear_conversation(conv_id)
                message = "Reset all conversations"

            return jsonify({'message': message})

        @self.app.route('/api/system')
        def get_system_info():
            """Get system information."""
            return jsonify({
                'runtime_dir': self.runtime_dir,
                'model': self.claude_agent.model,
                'max_tokens': self.claude_agent.max_tokens,
                'tool_count': len(self.tool_manager.tools),
                'conversation_count': len(self.conversation_manager.list_conversations()),
                'active_conversation': self.active_conversation
            })

    def run(self, debug: bool = True):
        """Run the debug server."""
        print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🚀 EvanAI Debug Server{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        print(f"\n📡 Server running at: {Fore.YELLOW}http://localhost:{self.port}{Style.RESET_ALL}")
        print(f"📚 API Docs: {Fore.YELLOW}http://localhost:{self.port}/api/tools{Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}Available Tools:{Style.RESET_ALL}")

        tools = self.tool_manager.get_anthropic_tools()
        for tool in tools:
            print(f"  • {tool['name']}")

        print(f"\n{Fore.YELLOW}Press Ctrl+C to stop the server{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")

        self.app.run(host='0.0.0.0', port=self.port, debug=debug)
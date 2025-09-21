#!/usr/bin/env python3
import click
import os
import sys
import time
import signal
from pathlib import Path
from dotenv import load_dotenv
from colorama import init, Fore, Style
import importlib
import inspect

from .constants import DEFAULT_RUNTIME_DIR, DEFAULT_CLAUDE_MODEL
from .state_manager import StateManager
from .tool_system import ToolManager, BaseToolSetProvider
from .claude_agent import ClaudeAgent
from .websocket_handler import WebSocketHandler
from .conversation_manager import ConversationManager
from .runtime_manager import RuntimeManager

init(autoreset=True)


class AgentClient:
    def __init__(self, reset_state: bool = False, runtime_dir: str = None):
        print(f"{Fore.CYAN}Initializing EvanAI Client...{Style.RESET_ALL}")

        # Initialize runtime manager first
        self.runtime_manager = RuntimeManager(runtime_dir or DEFAULT_RUNTIME_DIR)

        # Reset all persistence if requested
        if reset_state:
            print(f"{Fore.YELLOW}Resetting all persistence data...{Style.RESET_ALL}")
            self.runtime_manager.reset_all()

        # Initialize state manager with runtime directory
        self.state_manager = StateManager(runtime_dir, reset_state=False)  # Don't pass reset_state since we already handled it
        self.tool_manager = ToolManager()

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print(f"{Fore.RED}Error: ANTHROPIC_API_KEY not found in environment variables{Style.RESET_ALL}")
            print("Please set your Anthropic API key:")
            print("  export ANTHROPIC_API_KEY='your-key-here'")
            sys.exit(1)

        # Initialize Claude agent with workspace for built-in tools
        workspace_dir = os.path.join(self.runtime_manager.runtime_dir, 'workspace')
        os.makedirs(workspace_dir, exist_ok=True)
        self.claude_agent = ClaudeAgent(api_key, workspace_dir=workspace_dir)

        self.websocket_handler = WebSocketHandler()

        self.conversation_manager = ConversationManager(
            self.state_manager,
            self.tool_manager,
            self.claude_agent,
            self.websocket_handler,
            self.runtime_manager
        )

        self.load_tools()

        self.running = False

    def load_tools(self):
        print(f"{Fore.YELLOW}Loading tools...{Style.RESET_ALL}")

        tools_dir = Path(__file__).parent / "tools"
        if not tools_dir.exists():
            print(f"{Fore.YELLOW}No tools directory found, creating...{Style.RESET_ALL}")
            tools_dir.mkdir(exist_ok=True)

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

        tools = self.tool_manager.get_anthropic_tools()
        print(f"{Fore.GREEN}Loaded {len(tools)} tools total{Style.RESET_ALL}")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")

    def start(self):
        print(f"{Fore.CYAN}Starting EvanAI Client...{Style.RESET_ALL}")
        self.running = True

        print(f"{Fore.GREEN}Connecting to WebSocket server...{Style.RESET_ALL}")
        self.websocket_handler.connect()

        print(f"{Fore.GREEN}✓ Client is running and listening for prompts{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Press Ctrl+C to stop{Style.RESET_ALL}")

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        print(f"\n{Fore.YELLOW}Shutting down...{Style.RESET_ALL}")
        self.running = False
        self.websocket_handler.disconnect()
        print(f"{Fore.GREEN}✓ Client stopped{Style.RESET_ALL}")

    def status(self):
        print(f"\n{Fore.CYAN}=== EvanAI Client Status ==={Style.RESET_ALL}")

        # Show Claude model status
        current_model = self.claude_agent.get_current_model()
        if self.claude_agent.is_using_backup_model():
            print(f"Claude Model: {Fore.YELLOW}{current_model} [BACKUP MODE]{Style.RESET_ALL}")
            print(f"  Primary Model: {self.claude_agent.original_model} (failed)")
            print(f"  {Fore.YELLOW}⚠️  System is using backup model due to primary model failures{Style.RESET_ALL}")
        else:
            print(f"Claude Model: {Fore.GREEN}{current_model}{Style.RESET_ALL}")

        print(f"WebSocket connected: {self.websocket_handler.connected}")
        print(f"Active conversations: {len(self.conversation_manager.list_conversations())}")
        for conv_id in self.conversation_manager.list_conversations():
            history = self.conversation_manager.get_conversation_history(conv_id)
            print(f"  - {conv_id}: {len(history) if history else 0} messages")
        print(f"Tools loaded: {len(self.tool_manager.tools)}")
        for tool_id in self.tool_manager.tools:
            print(f"  - {tool_id}")


@click.group()
def cli():
    pass


@cli.command()
@click.option('--reset-state', is_flag=True, help='Reset all persistence (conversations, memory, tool states)')
@click.option('--runtime-dir', default=DEFAULT_RUNTIME_DIR, help='Path to runtime directory')
@click.option('--api-key', envvar='ANTHROPIC_API_KEY', help='Anthropic API key')
@click.option('--model', default=DEFAULT_CLAUDE_MODEL, help='Claude model to use')
def run(reset_state, runtime_dir, api_key, model):
    # Load environment variables from .env file
    load_dotenv()

    if api_key:
        os.environ['ANTHROPIC_API_KEY'] = api_key

    client = AgentClient(reset_state=reset_state, runtime_dir=runtime_dir)

    if model:
        client.claude_agent.set_model(model)

    def signal_handler(sig, frame):
        client.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    client.start()


@cli.command()
@click.option('--runtime-dir', default=DEFAULT_RUNTIME_DIR, help='Path to runtime directory')
def status(runtime_dir):
    load_dotenv()
    client = AgentClient(runtime_dir=runtime_dir)
    client.status()


@cli.command()
def runtime_info():
    """Display runtime directory structure and information."""
    runtime_manager = RuntimeManager()

    print(f"\n{Fore.CYAN}=== EvanAI Runtime Information ==={Style.RESET_ALL}")
    print(f"Runtime directory: {runtime_manager.runtime_dir}")
    print(f"Tool states file: {runtime_manager.tool_states_path}")
    print(f"Agent memory: {runtime_manager.agent_memory_path}")

    conversations = runtime_manager.list_conversations()
    print(f"\nActive conversations: {len(conversations)}")

    for conv_id in conversations:
        info = runtime_manager.get_conversation_info(conv_id)
        print(f"\n  {Fore.YELLOW}{conv_id}:{Style.RESET_ALL}")
        if info['exists'] and info['paths']:
            for key, value in info['paths'].items():
                if isinstance(value, dict) and 'target' in value:
                    print(f"    {key}: {'✓' if value['exists'] else '✗'} -> {value.get('target', 'N/A')}")
                else:
                    print(f"    {key}: {value}")


@cli.command()
@click.option('--runtime-dir', default=DEFAULT_RUNTIME_DIR, help='Path to runtime directory')
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
def reset_persistence(runtime_dir, force):
    """Reset all persistence data (conversations, memory, tool states)."""
    runtime_manager = RuntimeManager(runtime_dir)

    if not force:
        print(f"{Fore.YELLOW}This will delete all persistence data including:{Style.RESET_ALL}")
        print("  - All conversations and their history")
        print("  - Agent memory")
        print("  - Tool states")
        print("  - Working directories")
        response = click.confirm("Are you sure you want to continue?")
        if not response:
            print(f"{Fore.CYAN}Reset cancelled.{Style.RESET_ALL}")
            return

    print(f"{Fore.YELLOW}Resetting all persistence data...{Style.RESET_ALL}")
    runtime_manager.reset_all()
    print(f"{Fore.GREEN}✓ All persistence data has been reset{Style.RESET_ALL}")


@cli.command()
@click.option('--port', default=8069, help='Port to run the debug server on')
@click.option('--runtime-dir', default=DEFAULT_RUNTIME_DIR, help='Path to runtime directory')
def debug(port, runtime_dir):
    """Run the debug web interface for testing tools locally."""
    load_dotenv()

    try:
        from .debug_server import DebugServer
        server = DebugServer(runtime_dir=runtime_dir, port=port)
        server.run(debug=False)  # Run without Flask debug mode to avoid restart issues
    except ImportError:
        print(f"{Fore.RED}Error: Debug server dependencies not installed.{Style.RESET_ALL}")
        print("Please install Flask and flask-cors:")
        print("  pip install flask flask-cors")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}Error starting debug server: {e}{Style.RESET_ALL}")
        sys.exit(1)


@cli.command()
@click.argument('prompt')
@click.option('--conversation-id', default='test-conversation', help='Conversation ID')
def test_prompt(prompt, conversation_id):
    load_dotenv()
    client = AgentClient()

    print(f"\n{Fore.CYAN}Testing prompt processing...{Style.RESET_ALL}")
    print(f"Conversation ID: {conversation_id}")
    print(f"Prompt: {prompt}")

    conversation = client.conversation_manager.get_or_create_conversation(conversation_id)

    tools = client.tool_manager.get_anthropic_tools()

    def tool_callback(tool_id: str, parameters):
        result, error = client.tool_manager.call_tool(
            tool_id,
            parameters,
            conversation_id,
            working_directory=conversation.working_directory
        )
        return result, error

    response, new_history = client.claude_agent.process_prompt(
        prompt,
        conversation.get_history(),
        tools,
        tool_callback,
        enable_builtin_tools=['web_search', 'web_fetch', 'text_editor']  # Enable ALL built-in tools
    )

    print(f"\n{Fore.GREEN}Response:{Style.RESET_ALL}")
    print(response)


if __name__ == "__main__":
    cli()
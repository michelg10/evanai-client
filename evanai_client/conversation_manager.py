from typing import Dict, Any, List, Optional
import threading
from .claude_agent import ClaudeAgent
from .state_manager import StateManager
from .tool_system import ToolManager
from .websocket_handler import WebSocketHandler
from .runtime_manager import RuntimeManager


class Conversation:
    """Represents a single conversation with its history and state."""

    def __init__(self, conversation_id: str, working_directory: str = None):
        self.conversation_id = conversation_id
        self.history: List[Dict[str, Any]] = []
        self.state: Dict[str, Any] = {}
        self.working_directory = working_directory
        self.lock = threading.Lock()

    def add_message(self, role: str, content: Any):
        """Add a message to the conversation history."""
        with self.lock:
            self.history.append({"role": role, "content": content})

    def get_history(self) -> List[Dict[str, Any]]:
        """Get a copy of the conversation history."""
        with self.lock:
            return self.history.copy()


class ConversationManager:
    """Manages multiple conversations, coordinating between agents, tools, and the server."""

    def __init__(
        self,
        state_manager: StateManager,
        tool_manager: ToolManager,
        claude_agent: ClaudeAgent,
        websocket_handler: WebSocketHandler,
        runtime_manager: Optional[RuntimeManager] = None
    ):
        self.state_manager = state_manager
        self.tool_manager = tool_manager
        self.claude_agent = claude_agent
        self.websocket_handler = websocket_handler
        self.runtime_manager = runtime_manager or RuntimeManager()
        self.conversations: Dict[str, Conversation] = {}
        self.lock = threading.Lock()

        # Set up the websocket message handler
        self.websocket_handler.set_message_handler(self.handle_prompt)

    def get_or_create_conversation(self, conversation_id: str) -> Conversation:
        """Get an existing conversation or create a new one."""
        with self.lock:
            if conversation_id not in self.conversations:
                print(f"Creating new conversation: {conversation_id}")

                # Set up directories for the conversation
                dir_info = self.runtime_manager.setup_conversation_directories(conversation_id)
                print(f"Set up directories for conversation {conversation_id}:")
                print(f"  Working directory: {dir_info['working_directory']}")
                print(f"  Conversation data: {dir_info['conversation_data']}")

                # Create the conversation object with working directory
                conversation = Conversation(
                    conversation_id,
                    working_directory=dir_info['working_directory']
                )
                self.conversations[conversation_id] = conversation

                # Initialize state for the conversation
                self.state_manager.create_conversation(conversation_id)
            else:
                conversation = self.conversations[conversation_id]

            return conversation

    def handle_prompt(self, message: Dict[str, Any]):
        """Handle incoming prompt messages from the websocket."""
        try:
            payload = message.get("payload", {})
            conversation_id = payload.get("conversation_id")
            prompt = payload.get("prompt")

            if not conversation_id or not prompt:
                print(f"Invalid message format: missing conversation_id or prompt")
                return

            print(f"\n=== New prompt for conversation {conversation_id} ===")
            print(f"Prompt: {prompt[:100]}..." if len(prompt) > 100 else f"Prompt: {prompt}")

            # Get or create the conversation
            conversation = self.get_or_create_conversation(conversation_id)

            # Get available tools
            tools = self.tool_manager.get_anthropic_tools()

            # Create a tool callback that includes the conversation_id and working directory
            def tool_callback(tool_id: str, parameters: Dict[str, Any]) -> tuple:
                print(f"Calling tool: {tool_id} with parameters: {parameters}")

                # Get the tool's display name
                display_name = tool_id  # Default to tool_id
                if tool_id in self.tool_manager.tools:
                    display_name = self.tool_manager.tools[tool_id].get_display_name()

                # Broadcast the tool call
                try:
                    self.websocket_handler.broadcast_tool_call(conversation_id, tool_id, display_name, parameters)
                except Exception as e:
                    print(f"Failed to broadcast tool call: {e}")

                result, error = self.tool_manager.call_tool(
                    tool_id,
                    parameters,
                    conversation_id,
                    working_directory=conversation.working_directory
                )
                if error:
                    print(f"Tool error: {error}")
                else:
                    print(f"Tool result: {result}")
                return result, error

            # Process the prompt with Claude - enable all built-in tools by default
            response, new_history = self.claude_agent.process_prompt(
                prompt,
                conversation.get_history(),
                tools,
                tool_callback,
                enable_builtin_tools=['web_search', 'web_fetch', 'text_editor']  # Enable ALL built-in tools
            )

            # Update conversation history
            conversation.history = new_history

            print(f"Agent response: {response[:100]}..." if len(response) > 100 else f"Agent response: {response}")

            # Send response back through websocket
            success = self.websocket_handler.send_response(conversation_id, response)
            if success:
                print(f"Response sent successfully for conversation {conversation_id}")
            else:
                print(f"Failed to send response for conversation {conversation_id}")

        except Exception as e:
            print(f"Error handling prompt: {e}")
            import traceback
            traceback.print_exc()

    def list_conversations(self) -> List[str]:
        """List all active conversation IDs."""
        with self.lock:
            return list(self.conversations.keys())

    def get_conversation_history(self, conversation_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get the history for a specific conversation."""
        conversation = self.conversations.get(conversation_id)
        if conversation:
            return conversation.get_history()
        return None

    def get_conversation_working_directory(self, conversation_id: str) -> Optional[str]:
        """Get the working directory for a specific conversation."""
        conversation = self.conversations.get(conversation_id)
        if conversation:
            return conversation.working_directory
        return None

    def clear_conversation(self, conversation_id: str):
        """Clear a specific conversation and its state."""
        with self.lock:
            if conversation_id in self.conversations:
                del self.conversations[conversation_id]

                # Clear tool state
                self.tool_manager.clear_conversation_state(conversation_id)

                # Remove conversation state
                self.state_manager.remove_conversation(conversation_id)

                # Clean up conversation directories
                self.runtime_manager.remove_conversation(conversation_id)

                print(f"Cleared conversation: {conversation_id}")

    def cleanup_conversation_temp(self, conversation_id: str):
        """Clean up temporary files for a conversation without removing the conversation."""
        self.runtime_manager.cleanup_conversation_temp(conversation_id)

    def clear_all_conversations(self):
        """Clear all conversations and state."""
        with self.lock:
            # Get list of conversations before clearing
            conv_ids = list(self.conversations.keys())

            # Clear in-memory conversations
            self.conversations.clear()

            # Clear all state
            self.state_manager.clear_all()
            self.tool_manager.clear_all_state()

            # Remove directories for all conversations
            for conv_id in conv_ids:
                self.runtime_manager.remove_conversation(conv_id)

            print("Cleared all conversations and state")
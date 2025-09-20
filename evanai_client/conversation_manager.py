from typing import Dict, Any, List, Optional
import threading
from .claude_agent import ClaudeAgent
from .state_manager import StateManager
from .tool_system import ToolManager
from .websocket_handler import WebSocketHandler


class Conversation:
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.history: List[Dict[str, Any]] = []
        self.state: Dict[str, Any] = {}
        self.lock = threading.Lock()

    def add_message(self, role: str, content: Any):
        with self.lock:
            self.history.append({"role": role, "content": content})

    def get_history(self) -> List[Dict[str, Any]]:
        with self.lock:
            return self.history.copy()


class ConversationManager:
    def __init__(
        self,
        state_manager: StateManager,
        tool_manager: ToolManager,
        claude_agent: ClaudeAgent,
        websocket_handler: WebSocketHandler
    ):
        self.state_manager = state_manager
        self.tool_manager = tool_manager
        self.claude_agent = claude_agent
        self.websocket_handler = websocket_handler
        self.conversations: Dict[str, Conversation] = {}
        self.lock = threading.Lock()

        self.websocket_handler.set_message_handler(self.handle_prompt)

    def get_or_create_conversation(self, conversation_id: str) -> Conversation:
        with self.lock:
            if conversation_id not in self.conversations:
                print(f"Creating new conversation: {conversation_id}")
                self.conversations[conversation_id] = Conversation(conversation_id)
                self.state_manager.create_conversation(conversation_id)
            return self.conversations[conversation_id]

    def handle_prompt(self, message: Dict[str, Any]):
        try:
            payload = message.get("payload", {})
            conversation_id = payload.get("conversation_id")
            prompt = payload.get("prompt")

            if not conversation_id or not prompt:
                print(f"Invalid message format: missing conversation_id or prompt")
                return

            print(f"\n=== New prompt for conversation {conversation_id} ===")
            print(f"Prompt: {prompt[:100]}..." if len(prompt) > 100 else f"Prompt: {prompt}")

            conversation = self.get_or_create_conversation(conversation_id)

            conversation_state = self.state_manager.get_conversation_state(conversation_id)
            global_state = self.state_manager.get_global_state()

            tools = self.tool_manager.get_anthropic_tools()

            def tool_callback(tool_id: str, parameters: Dict[str, Any]) -> tuple:
                print(f"Calling tool: {tool_id} with parameters: {parameters}")
                result, error = self.tool_manager.call_tool(
                    tool_id,
                    parameters,
                    conversation_id,
                    global_state,
                    conversation_state
                )
                if error:
                    print(f"Tool error: {error}")
                else:
                    print(f"Tool result: {result}")
                return result, error

            response, new_history = self.claude_agent.process_prompt(
                prompt,
                conversation.get_history(),
                tools,
                tool_callback
            )

            conversation.history = new_history

            print(f"Agent response: {response[:100]}..." if len(response) > 100 else f"Agent response: {response}")

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
        with self.lock:
            return list(self.conversations.keys())

    def get_conversation_history(self, conversation_id: str) -> Optional[List[Dict[str, Any]]]:
        conversation = self.conversations.get(conversation_id)
        if conversation:
            return conversation.get_history()
        return None

    def clear_conversation(self, conversation_id: str):
        with self.lock:
            if conversation_id in self.conversations:
                del self.conversations[conversation_id]
                print(f"Cleared conversation: {conversation_id}")

    def clear_all_conversations(self):
        with self.lock:
            self.conversations.clear()
            self.state_manager.clear_all()
            print("Cleared all conversations and state")
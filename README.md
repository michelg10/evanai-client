# EvanAI Client

An AI agent client that connects to the EvanAI server, processes prompts using Claude, and supports extensible tool plugins.

## Features

- 🔌 WebSocket connection to EvanAI server for real-time communication
- 🤖 Claude API integration for intelligent responses with Agent Evan personality
- 🔧 Extensible tool system with plugin architecture
- 💾 Persistent state management (global and per-conversation)
- 🎯 Multi-conversation support
- 🛠️ Multiple tool calls in a single response
- 🌡️ Example tools included (weather and math operations)

## Installation

### Prerequisites

- Python 3.8+
- Anthropic API key

### Setup

1. Clone the repository and navigate to the client directory:
```bash
cd evanai-client
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install the client in development mode:
```bash
pip install -e .
```

4. Set up your environment variables:
```bash
cp .env.template .env
# Edit .env and add your ANTHROPIC_API_KEY
```

Or export directly:
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

## Usage

### Running the Client

Start the client to listen for prompts from the server:

```bash
# Basic usage
evanai-client run

# With options
evanai-client run --reset-state  # Clear all persisted state
evanai-client run --state-file custom_state.pkl  # Use custom state file
evanai-client run --model claude-3-opus-20240229  # Use different Claude model
```

### Commands

- `run` - Start the client and connect to the server
- `status` - Check client status and active conversations
- `test-weather <location>` - Test the weather tool
- `test-prompt <prompt>` - Test prompt processing locally

### Examples

```bash
# Start the client
evanai-client run

# Check status
evanai-client status

# Test weather tool
evanai-client test-weather "San Francisco, CA"

# Test a prompt locally
evanai-client test-prompt "What's the weather in New York?"
```

## Creating Custom Tools

Tools are plugins that extend the agent's capabilities. The system supports multiple tool calls in a single response. Create a new tool by:

1. Create a Python file in `evanai_client/tools/`
2. Implement a class that inherits from `BaseToolSetProvider`
3. Define tools in the `init()` method
4. Implement tool logic in `call_tool()`

### Example Tool

```python
from typing import Dict, List, Any, Optional, Tuple
from ..tool_system import BaseToolSetProvider, Tool, Parameter, ParameterType

class MyToolProvider(BaseToolSetProvider):
    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
        tools = [
            Tool(
                id="my_tool",
                name="My Tool",
                description="Does something useful",
                parameters={
                    "input": Parameter(
                        name="input",
                        type=ParameterType.STRING,
                        description="Input for the tool",
                        required=True
                    )
                }
            )
        ]

        # Global state shared across all conversations
        global_state = {"call_count": 0}

        # Per-conversation state (initially empty)
        per_conversation_state = {}

        return tools, global_state, per_conversation_state

    def call_tool(
        self,
        tool_id: str,
        tool_parameters: Dict[str, Any],
        per_conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        if tool_id == "my_tool":
            input_value = tool_parameters.get("input")

            # Update global state
            global_state["call_count"] += 1

            # Track in conversation state
            per_conversation_state.setdefault("history", []).append(input_value)

            # Tool logic here
            return {"result": f"Processed: {input_value}"}, None

        return None, f"Unknown tool: {tool_id}"
```

## Architecture

### Components

1. **WebSocket Handler** - Manages connection to EvanAI server
2. **Claude Agent** - Processes prompts using Anthropic's Claude API with support for multiple tool calls in a single response
3. **Tool System** - Plugin architecture for extensible functionality with built-in state management
4. **State Manager** - Persistent state management with pickle
5. **Conversation Manager** - Handles multiple conversation contexts

### Message Flow

1. Server sends prompt via WebSocket → `{"recipient": "agent", "type": "new_prompt", ...}`
2. Client processes with Claude + tools
3. Client broadcasts response → `{"recipient": "user_device", "type": "agent_response", ...}`

## State Management

- State persists between client restarts (default: `evanai_state.pkl`)
- Use `--reset-state` flag to clear all state
- State is separated into:
  - Global state (shared across all conversations)
  - Per-conversation state (isolated per conversation)

## Troubleshooting

### WebSocket Connection Issues
- Check internet connectivity
- Verify server URL: `wss://data-transmitter.hemeshchadalavada.workers.dev`
- Check for firewall/proxy issues

### Claude API Issues
- Verify ANTHROPIC_API_KEY is set correctly
- Check API key permissions
- Monitor rate limits

### Tool Loading Issues
- Ensure tools are in `evanai_client/tools/` directory
- Check tool implementation inherits from `BaseToolSetProvider`
- Verify tool IDs are unique

## Development

### Running Tests
```bash
# Test weather tool
evanai-client test-weather "London, UK"

# Test prompt processing
evanai-client test-prompt "What can you help me with?"
```

### Debug Mode
Set environment variable for verbose logging:
```bash
export DEBUG=1
evanai-client run
```

## License

See LICENSE file in the root directory.
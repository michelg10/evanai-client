# EvanAI Client

A sophisticated AI agent client that connects to the EvanAI server via WebSocket, processes natural language prompts using Claude API, and provides an extensible plugin system for custom tools. This client acts as an intelligent assistant capable of performing various tasks through its modular tool architecture while maintaining conversation context and persistent state.

## Features

- 🔌 **Real-time WebSocket Connection**: Maintains persistent connection to EvanAI server for instant communication
- 🤖 **Claude API Integration**: Leverages Anthropic's Claude models for intelligent, context-aware responses
- 🔧 **Extensible Tool System**: Plugin-based architecture allowing easy addition of custom tools
- 💾 **Dual-Level State Management**: Separate global and per-conversation state persistence
- 🎯 **Multi-Conversation Support**: Handle multiple independent conversation contexts simultaneously
- 🛠️ **Parallel Tool Execution**: Support for multiple tool calls in a single Claude response
- 📁 **Sandboxed File System**: Each conversation gets its own working directory with organized structure
- 🔄 **Auto-Reconnection**: Automatic WebSocket reconnection with configurable retry delays
- 🎨 **Rich CLI Interface**: Colored terminal output for better readability

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Installation](#installation)
- [Usage](#usage)
- [Creating Custom Tools](#creating-custom-tools)
- [Advanced Tool Development](#advanced-tool-development)
- [System Architecture](#system-architecture)
- [State Management](#state-management)
- [Runtime Directory Structure](#runtime-directory-structure)
- [Message Protocol](#message-protocol)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Best Practices](#best-practices)

## Architecture Overview

The EvanAI Client follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────┐
│                  EvanAI Server                  │
│              (WebSocket Endpoint)               │
└────────────────────┬───────────────────────────┘
                     │ WebSocket
                     ↓
┌─────────────────────────────────────────────────┐
│              WebSocket Handler                  │
│         (Connection Management & I/O)           │
└────────────────────┬───────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────┐
│           Conversation Manager                  │
│    (Routes Messages to Conversations)           │
└────────────────────┬───────────────────────────┘
                     │
          ┌──────────┼──────────┐
          ↓          ↓          ↓
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│Claude Agent │ │Tool Manager│ │State Manager │
│ (AI Brain)  │ │(Tool Exec) │ │(Persistence) │
└──────────────┘ └──────────┘ └──────────────┘
                     │
          ┌──────────┼──────────┐
          ↓          ↓          ↓
    [Weather]   [FileSystem]  [Upload]
    [Math]      [Asset]       [Custom...]
                Tools
```

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
evanai-client run --reset-state              # Clear all persisted state
evanai-client run --runtime-dir ./custom_dir  # Use custom runtime directory
evanai-client run --model claude-3-opus-20240229  # Use different Claude model
```

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `run` | Start the client and connect to server | `evanai-client run` |
| `status` | Check client status and conversations | `evanai-client status` |
| `runtime-info` | Display runtime directory structure | `evanai-client runtime-info` |
| `reset-persistence` | Reset all persistence data | `evanai-client reset-persistence --force` |
| `test-weather` | Test the weather tool locally | `evanai-client test-weather "London"` |
| `test-prompt` | Test prompt processing locally | `evanai-client test-prompt "Hello!"` |

### Command Options

#### `run` Command Options
- `--reset-state`: Clear all persistence data before starting
- `--runtime-dir PATH`: Specify custom runtime directory (default: `evanai_runtime`)
- `--api-key KEY`: Provide Anthropic API key (can also use env var)
- `--model MODEL`: Specify Claude model to use

#### `reset-persistence` Command Options
- `--force`: Skip confirmation prompt
- `--runtime-dir PATH`: Specify runtime directory to reset

### Real-World Examples

```bash
# Start fresh with no previous state
evanai-client run --reset-state

# Use a development environment
evanai-client run --runtime-dir ./dev_runtime --model claude-3-haiku-20240307

# Check what conversations are active
evanai-client runtime-info

# Test a complex prompt with tools
evanai-client test-prompt "What's the weather in Paris and calculate 15% tip on $85.50"

# Clean up after testing
evanai-client reset-persistence --force
```

## Creating Custom Tools

Tools are plugins that extend the agent's capabilities, allowing it to perform specialized tasks. The tool system is designed for flexibility, supporting multiple tool calls in a single Claude response and maintaining both global and per-conversation state.

### Tool System Components

1. **BaseToolSetProvider**: Abstract base class for all tool providers
2. **Tool**: Defines a tool's metadata and parameters
3. **Parameter**: Describes individual tool parameters with type validation
4. **ParameterType**: Enum defining supported parameter types (STRING, INTEGER, NUMBER, BOOLEAN, OBJECT, ARRAY)

### Step-by-Step Tool Creation Guide

#### 1. Create the Tool File

Create a new Python file in the `evanai_client/tools/` directory:

```bash
touch evanai_client/tools/my_custom_tool.py
```

#### 2. Import Required Components

```python
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from ..tool_system import BaseToolSetProvider, Tool, Parameter, ParameterType
```

#### 3. Implement the Tool Provider Class

```python
class MyCustomToolProvider(BaseToolSetProvider):
    """Provider for custom functionality."""

    def __init__(self, websocket_handler=None):
        super().__init__(websocket_handler)
        # Initialize any resources your tool needs
        self.config = self._load_config()

    def _load_config(self):
        """Load tool-specific configuration."""
        return {"api_endpoint": "https://api.example.com"}
```

#### 4. Define Tools in the init() Method

The `init()` method must return three components:
1. List of Tool objects
2. Initial global state dictionary
3. Initial per-conversation state dictionary

```python
def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
    tools = [
        Tool(
            id="fetch_data",  # Unique identifier
            name="Fetch Data",  # Human-readable name
            description="Fetch data from an external API",  # Clear description for Claude
            parameters={
                "query": Parameter(
                    name="query",
                    type=ParameterType.STRING,
                    description="Search query",
                    required=True
                ),
                "limit": Parameter(
                    name="limit",
                    type=ParameterType.INTEGER,
                    description="Maximum results to return",
                    required=False,
                    default=10
                ),
                "filters": Parameter(
                    name="filters",
                    type=ParameterType.OBJECT,
                    description="Optional filters",
                    required=False,
                    properties={
                        "category": Parameter(
                            name="category",
                            type=ParameterType.STRING,
                            description="Filter by category"
                        ),
                        "date_from": Parameter(
                            name="date_from",
                            type=ParameterType.STRING,
                            description="Start date (YYYY-MM-DD)"
                        )
                    }
                )
            },
            returns=Parameter(  # Optional: describe return value
                name="search_results",
                type=ParameterType.ARRAY,
                description="Array of search results"
            )
        )
    ]

    # Global state persists across all conversations
    global_state = {
        "total_api_calls": 0,
        "cache": {},
        "last_cleanup": None
    }

    # Per-conversation state is isolated per conversation
    per_conversation_state = {}

    return tools, global_state, per_conversation_state
```

#### 5. Implement the call_tool() Method

```python
def call_tool(
    self,
    tool_id: str,
    tool_parameters: Dict[str, Any],
    per_conversation_state: Dict[str, Any],
    global_state: Dict[str, Any]
) -> Tuple[Any, Optional[str]]:
    """Execute the requested tool.

    Returns:
        Tuple of (result, error_message)
        - result: Tool output (any JSON-serializable type)
        - error_message: None if successful, error string if failed
    """

    # Access working directory if needed
    working_dir = per_conversation_state.get('_working_directory')

    if tool_id == "fetch_data":
        try:
            # Extract parameters
            query = tool_parameters.get("query")
            limit = tool_parameters.get("limit", 10)
            filters = tool_parameters.get("filters", {})

            # Update global state
            global_state["total_api_calls"] += 1

            # Track in conversation state
            per_conversation_state.setdefault("queries", []).append(query)

            # Check cache
            cache_key = f"{query}:{limit}"
            if cache_key in global_state["cache"]:
                return {"results": global_state["cache"][cache_key], "from_cache": True}, None

            # Perform actual work
            results = self._fetch_from_api(query, limit, filters)

            # Update cache
            global_state["cache"][cache_key] = results

            return {"results": results, "from_cache": False}, None

        except Exception as e:
            return None, f"Error fetching data: {str(e)}"

    return None, f"Unknown tool: {tool_id}"

def _fetch_from_api(self, query: str, limit: int, filters: Dict) -> List[Dict]:
    """Private method for API interaction."""
    # Implementation here
    return [{"id": 1, "title": f"Result for {query}"}]
```

### Complete Example: Advanced Calculator Tool

```python
from typing import Dict, List, Any, Optional, Tuple
import math
import re
from ..tool_system import BaseToolSetProvider, Tool, Parameter, ParameterType

class CalculatorToolProvider(BaseToolSetProvider):
    """Advanced calculator with expression parsing and history."""

    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
        tools = [
            Tool(
                id="calculate",
                name="Calculate Expression",
                description="Evaluate mathematical expressions with variables",
                parameters={
                    "expression": Parameter(
                        name="expression",
                        type=ParameterType.STRING,
                        description="Mathematical expression (e.g., '2 + 2', 'sin(pi/2)', 'x^2 where x=5')",
                        required=True
                    ),
                    "variables": Parameter(
                        name="variables",
                        type=ParameterType.OBJECT,
                        description="Variable values for the expression",
                        required=False
                    ),
                    "precision": Parameter(
                        name="precision",
                        type=ParameterType.INTEGER,
                        description="Decimal precision (default: 4)",
                        required=False,
                        default=4
                    )
                }
            ),
            Tool(
                id="get_calculation_history",
                name="Get Calculation History",
                description="Retrieve previous calculations from this conversation",
                parameters={
                    "limit": Parameter(
                        name="limit",
                        type=ParameterType.INTEGER,
                        description="Number of recent calculations to retrieve",
                        required=False,
                        default=5
                    )
                }
            )
        ]

        global_state = {
            "total_calculations": 0,
            "all_time_history": []
        }

        per_conversation_state = {}

        return tools, global_state, per_conversation_state

    def call_tool(
        self,
        tool_id: str,
        tool_parameters: Dict[str, Any],
        per_conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:

        if tool_id == "calculate":
            return self._calculate(tool_parameters, per_conversation_state, global_state)
        elif tool_id == "get_calculation_history":
            return self._get_history(tool_parameters, per_conversation_state)

        return None, f"Unknown tool: {tool_id}"

    def _calculate(self, params: Dict, conv_state: Dict, global_state: Dict) -> Tuple[Dict, Optional[str]]:
        expression = params.get("expression")
        variables = params.get("variables", {})
        precision = params.get("precision", 4)

        try:
            # Substitute variables
            expr = expression
            for var, val in variables.items():
                expr = expr.replace(var, str(val))

            # Safe evaluation with math functions
            allowed_names = {
                k: v for k, v in math.__dict__.items()
                if not k.startswith("_")
            }
            allowed_names.update({"abs": abs, "round": round})

            # Replace ^ with ** for exponentiation
            expr = expr.replace("^", "**")

            # Evaluate
            result = eval(expr, {"__builtins__": {}}, allowed_names)

            # Round if float
            if isinstance(result, float):
                result = round(result, precision)

            # Update states
            global_state["total_calculations"] += 1

            calculation_record = {
                "expression": expression,
                "variables": variables,
                "result": result
            }

            conv_state.setdefault("history", []).append(calculation_record)
            global_state["all_time_history"].append(calculation_record)

            return {
                "expression": expression,
                "result": result,
                "variables_used": variables
            }, None

        except Exception as e:
            return None, f"Calculation error: {str(e)}"

    def _get_history(self, params: Dict, conv_state: Dict) -> Tuple[List, Optional[str]]:
        limit = params.get("limit", 5)
        history = conv_state.get("history", [])

        return history[-limit:] if history else [], None
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
# EvanAI Debug Interface

## Overview

The debug interface provides a local web-based UI for testing and developing tools without needing to go through the WebSocket server. This is perfect for rapid development and debugging.

## Features

- 🎯 **Direct Agent Interaction**: Chat directly with the agent without WebSocket complexity
- ⚡ **Real-time Tool Execution Display**: See every tool call, its parameters, and results
- 🛠️ **Tool Explorer**: Browse all available tools and their descriptions
- 📊 **System Information**: View runtime configuration and statistics
- 💬 **Conversation Management**: Full conversation history with reset capability
- 🎨 **Developer-Friendly UI**: Dark theme optimized for extended coding sessions

## Installation

Install the required dependencies:

```bash
pip install flask flask-cors
```

## Usage

Start the debug server:

```bash
python -m evanai_client.main debug
```

Options:
- `--port PORT`: Specify the port (default: 8069)
- `--runtime-dir DIR`: Specify runtime directory (default: evanai_runtime)

Example with custom port:
```bash
python -m evanai_client.main debug --port 8080
```

## Interface Overview

The debug interface is divided into three main sections:

### 1. **Left Sidebar**
- **Available Tools**: Lists all registered tools with descriptions
- **System Info**: Displays model, token limits, and runtime configuration
- **Controls**: Quick actions like refreshing tools and resetting conversations

### 2. **Main Chat Area**
- **Conversation Display**: Shows the full conversation history
- **Input Field**: Enter prompts to send to the agent
- **Message Count**: Track conversation length

### 3. **Right Panel - Tool Executions**
- **Real-time Display**: Shows tool calls as they happen
- **Parameters**: View exact parameters sent to each tool
- **Results**: See tool outputs and any errors
- **Execution Time**: Performance metrics for each tool call

## Development Workflow

1. **Start the Debug Server**
   ```bash
   python -m evanai_client.main debug
   ```

2. **Open Browser**
   Navigate to `http://localhost:8069`

3. **Test Your Tools**
   - Type prompts that trigger your tools
   - Watch tool executions in real-time
   - Debug using the detailed parameter and result display

4. **Iterate Quickly**
   - Modify your tool code
   - Restart the server
   - Test immediately without WebSocket setup

## Tool Development Tips

### Testing a New Tool

1. Create your tool provider in `evanai_client/tools/`
2. Start the debug server
3. Check the "Available Tools" section to confirm registration
4. Send prompts that should trigger your tool
5. Monitor the tool execution panel for debugging

### Debugging Tool Errors

The interface shows:
- Exact parameters received by the tool
- Full error messages and stack traces
- Execution time for performance optimization
- Success/failure status for each call

### Example Test Prompts

```
# File Management
"List all files in the conversation_data folder"
"Create a test file called hello.txt with some content"

# Weather Tool
"What's the weather in San Francisco?"

# Math Tools
"Calculate 25 * 4 + 10"

# Upload Tool
"Upload the file test.txt to the user"
```

## API Endpoints

The debug server exposes several API endpoints for advanced usage:

- `GET /api/tools` - List all available tools
- `POST /api/prompt` - Process a prompt
- `GET /api/conversations` - List conversations
- `GET /api/conversation/<id>` - Get conversation history
- `POST /api/reset` - Reset conversations
- `GET /api/system` - Get system information

## Troubleshooting

### Port Already in Use
```bash
# Use a different port
python -m evanai_client.main debug --port 8080
```

### Flask Not Installed
```bash
pip install flask flask-cors
```

### API Key Issues
Ensure your `.env` file contains:
```
ANTHROPIC_API_KEY=your-key-here
```

## Keyboard Shortcuts

- **Enter**: Send message (in input field)
- **Shift+Enter**: New line in message

## Security Note

⚠️ The debug server is intended for local development only. It has CORS enabled and no authentication. Never expose it to the public internet.

## Contributing

When developing new tools:
1. Use the debug interface for rapid testing
2. Ensure tools display useful information in results
3. Include clear error messages for debugging
4. Test edge cases using the interface

## Future Enhancements

Planned features:
- [ ] Export/import conversation history
- [ ] Tool execution history persistence
- [ ] Performance profiling dashboard
- [ ] Mock data generators for tools
- [ ] Automated test suite runner
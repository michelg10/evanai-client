# Bash Tool for EvanAI Client

The Bash tool provides Claude agents with the ability to execute bash commands in isolated, secure Docker containers. Each conversation gets its own container with lazy initialization for optimal resource usage.

## Key Features

✅ **Lazy Container Initialization** - Containers created only when bash is first used
✅ **Per-Conversation Isolation** - Each conversation has its own container
✅ **Read-Only Root Filesystem** - Security through immutable system files
✅ **Persistent Working Directory** - `/mnt` directory persists between commands
✅ **Automatic Cleanup** - Idle containers stop after timeout (default 5 min)
✅ **Resource Limits** - Configurable memory and CPU constraints
✅ **Host Network Access** - Full access to host network and services

## Architecture

```
Claude Agent (Conversation)
     ↓
  Bash Tool
     ↓
Lazy Manager → Creates container on first use
     ↓
Docker Container (Isolated Environment)
  - Read-only: / (system)
  - Writable: /mnt (workspace)
  - Unique per conversation
```

## Installation

### 1. Build the Agent Docker Image

```bash
cd evanai_client/tools/linux-desktop-environment
./build-agent.sh
```

### 2. Verify Installation

```bash
# Check Docker
docker --version

# Check image
docker images | grep claude-agent

# Run verification
./verify.sh
```

### 3. Install Python Dependencies

```bash
pip install docker
```

## Usage

### Basic Usage with Tool Manager

```python
from evanai_client.tool_system import ToolManager
from evanai_client.tools.bash_tool import BashToolProvider

# Initialize tool manager
tool_manager = ToolManager()

# Create and register bash tool
bash_provider = BashToolProvider(
    runtime_dir="./evanai-runtime",
    idle_timeout=300,  # 5 minutes
    memory_limit="2g",
    cpu_limit=2.0
)

tool_manager.register_provider(bash_provider)

# Execute bash command (container created on first use)
result, error = tool_manager.call_tool(
    "bash",
    {"command": "echo 'Hello from container!'"},
    conversation_id="chat-123"
)

print(result["output"])  # "Hello from container!"
```

### Integration with Claude Agent

```python
from evanai_client.claude_agent import ClaudeAgent
from evanai_client.tools import BashToolProvider

# Create agent
agent = ClaudeAgent()

# Add bash tool
bash_tool = BashToolProvider()
agent.tool_manager.register_provider(bash_tool)

# Claude can now use bash commands
response = agent.send_message(
    "Check the Python version using bash"
)
# Claude executes: bash({"command": "python3 --version"})
```

### Direct Tool Usage

```python
from evanai_client.tools.bash_tool import create_bash_tool

# Quick setup
bash_tool = create_bash_tool()

# Initialize
tools, global_state, conv_state = bash_tool.init()

# Set conversation ID
conv_state["_conversation_id"] = "my-conversation"

# Execute command
result, error = bash_tool.call_tool(
    "bash",
    {"command": "ls -la /mnt"},
    conv_state,
    global_state
)
```

## Tool Interface

### Available Tools

#### 1. `bash` - Execute Commands

```python
tool_manager.call_tool(
    "bash",
    {
        "command": "echo 'Hello World'",  # Required
        "timeout": 120,                   # Optional (seconds)
        "working_dir": "/mnt"             # Optional
    },
    conversation_id
)
```

**Returns:**
```python
{
    "exit_code": 0,
    "stdout": "Hello World\n",
    "stderr": "",
    "success": True,
    "output": "Hello World\n",
    "command": "echo 'Hello World'",
    "conversation_id": "chat-123",
    "command_number": 1,
    "container_was_created": True  # First command
}
```

#### 2. `bash_status` - Check Environment

```python
result, error = tool_manager.call_tool(
    "bash_status",
    {},
    conversation_id
)
```

**Returns:**
```python
{
    "conversation_id": "chat-123",
    "container_state": "running",
    "container_active": True,
    "command_count": 5,
    "last_activity": "2024-01-20T10:30:00",
    "uptime_seconds": 120.5,
    "idle_seconds": 10.2,
    "memory_limit": "2g",
    "cpu_limit": 2.0
}
```

#### 3. `bash_reset` - Reset Environment

```python
result, error = tool_manager.call_tool(
    "bash_reset",
    {"keep_data": False},  # Optional
    conversation_id
)
```

## Configuration

### Environment Variables

```bash
export EVANAI_RUNTIME_DIR=/path/to/runtime
export BASH_TOOL_IMAGE=claude-agent:latest
export BASH_TOOL_IDLE_TIMEOUT=300
export BASH_TOOL_MEMORY_LIMIT=4g
export BASH_TOOL_CPU_LIMIT=4
export BASH_TOOL_MAX_AGENTS=100
```

### Configuration File

Create `bash_tool_config.json`:

```json
{
  "runtime_dir": "./evanai-runtime",
  "docker_image": "claude-agent:latest",
  "idle_timeout": 300,
  "memory_limit": "2g",
  "cpu_limit": 2.0,
  "max_agents": 100,
  "auto_cleanup": true,
  "enable_logging": true,
  "network_name": "agent-network"
}
```

### Using Configuration

```python
from evanai_client.tools.bash_tool_config import BashToolConfig

# Load config
config = BashToolConfig("./bash_tool_config.json")

# Validate
if config.validate():
    # Create tool with config
    bash_tool = config.create_bash_tool_provider()
```

## Examples

### Example 1: Data Processing

```python
# Process data in isolated environment
commands = [
    "cd /mnt",
    "echo 'import pandas as pd; df = pd.DataFrame({\"a\": [1,2,3]}); print(df.sum())' > process.py",
    "python3 process.py"
]

for cmd in commands:
    result, _ = tool_manager.call_tool(
        "bash",
        {"command": cmd},
        "data-processor"
    )
    print(result["output"])
```

### Example 2: Accessing Host Services

```python
# Agent can access services running on the host
result, _ = tool_manager.call_tool(
    "bash",
    {"command": "curl http://localhost:3000/api/health"},
    "service-checker"
)
print(f"Host service response: {result['output']}")

# Can also connect to host databases
result, _ = tool_manager.call_tool(
    "bash",
    {"command": "psql -h localhost -U postgres -d mydb -c 'SELECT NOW()'"},
    "db-client"
)
```

### Example 3: File Operations

```python
# Each conversation has isolated /mnt
conversations = ["user-1", "user-2"]

for conv_id in conversations:
    # Create unique file
    tool_manager.call_tool(
        "bash",
        {"command": f"echo '{conv_id} data' > /mnt/user.txt"},
        conv_id
    )

# Files are isolated
for conv_id in conversations:
    result, _ = tool_manager.call_tool(
        "bash",
        {"command": "cat /mnt/user.txt"},
        conv_id
    )
    print(f"{conv_id}: {result['output']}")
    # user-1: user-1 data
    # user-2: user-2 data
```

### Example 4: Long Running Tasks

```python
# Start background process
tool_manager.call_tool(
    "bash",
    {"command": "nohup python3 /mnt/long_task.py > /mnt/output.log 2>&1 &"},
    "long-task"
)

# Check progress later
result, _ = tool_manager.call_tool(
    "bash",
    {"command": "tail -f /mnt/output.log | head -20"},
    "long-task"
)
```

## Security Features

### Read-Only Root Filesystem
- System files cannot be modified
- Only `/mnt` is writable
- Temporary files use tmpfs

### Resource Limits
- Memory limits enforced (default 2GB)
- CPU limits enforced (default 2 cores)
- Process limits (ulimits)

### Network Access
- **Host Network Mode**: Full access to host network
- Can access localhost services and bind to host ports
- Direct external connectivity without NAT
- Network capabilities: NET_RAW, NET_BIND_SERVICE

### Capability Restrictions
- Most capabilities dropped except essential ones
- No privileged operations (except network)
- No new privileges flag set

## Performance

### Container Lifecycle

| Stage | Time | Notes |
|-------|------|-------|
| Conversation start | 0ms | No container |
| First bash command | 2-3s | Container creation |
| Subsequent commands | 50-100ms | Container ready |
| Idle timeout | 5 min | Container stops |
| Resume after idle | 2-3s | Container restarts |

### Resource Usage

| State | Memory | CPU | Disk |
|-------|--------|-----|------|
| No bash used | 0 MB | 0% | 0 MB |
| Container idle | ~100 MB | ~0% | Image size |
| Active command | 100-200 MB | Varies | + data |

## Troubleshooting

### Container Not Creating

```python
# Check Docker
import docker
client = docker.from_env()
client.ping()  # Should not raise error

# Check image
client.images.get("claude-agent:latest")

# Check logs
bash_tool.enable_logging = True
```

### Permission Denied

```python
# Ensure /mnt is used for writes
result, _ = tool_manager.call_tool(
    "bash",
    {"command": "touch /mnt/test.txt"},  # Good
    conversation_id
)

# System paths are read-only
result, _ = tool_manager.call_tool(
    "bash",
    {"command": "touch /etc/test.txt"},  # Will fail
    conversation_id
)
```

### Container Stops Too Soon

```python
# Increase idle timeout
bash_tool = BashToolProvider(
    idle_timeout=1800  # 30 minutes
)
```

## Testing

Run the test suite:

```bash
# Basic tests
python test_bash_tool.py

# Test specific functionality
python -c "
from test_bash_tool import test_lazy_initialization
test_lazy_initialization()
"
```

## Advanced Usage

### Custom Docker Image

```python
bash_tool = BashToolProvider(
    image="my-custom-agent:latest"
)
```

### Persistent Data Across Resets

```python
# Reset container but keep /mnt data
tool_manager.call_tool(
    "bash_reset",
    {"keep_data": True},
    conversation_id
)
```

### Monitor Multiple Conversations

```python
# Get statistics
stats = bash_tool.manager.get_stats()
print(f"Active containers: {stats['agents_by_state']['running']}")
print(f"Total commands: {stats['total_commands']}")

for agent in stats['agents']:
    print(f"{agent['agent_id']}: {agent['command_count']} commands")
```

## API Reference

### BashToolProvider

```python
class BashToolProvider(BaseToolSetProvider):
    def __init__(
        self,
        runtime_dir: Optional[str] = None,
        idle_timeout: int = 300,
        memory_limit: str = "2g",
        cpu_limit: float = 2.0,
        image: str = "claude-agent:latest",
        auto_cleanup: bool = True,
        enable_logging: bool = True
    )
```

### Parameters

- `runtime_dir`: Base directory for agent data (default: `./evanai-runtime`)
- `idle_timeout`: Seconds before idle container stops (default: 300)
- `memory_limit`: Docker memory limit (default: "2g")
- `cpu_limit`: Docker CPU limit in cores (default: 2.0)
- `image`: Docker image name (default: "claude-agent:latest")
- `auto_cleanup`: Clean up stopped containers (default: True)
- `enable_logging`: Print debug logs (default: True)

## Best Practices

1. **Use `/mnt` for all file operations** - It's the only writable directory
2. **Handle container creation latency** - First command takes 2-3 seconds
3. **Set appropriate timeouts** - Long tasks need higher timeout values
4. **Clean up after conversations** - Use `bash_reset` when done
5. **Monitor resource usage** - Check stats regularly for production
6. **Use meaningful conversation IDs** - Makes debugging easier

## Support

For issues or questions:

1. Check container logs:
   ```python
   bash_tool.enable_logging = True
   ```

2. Verify Docker setup:
   ```bash
   docker run --rm claude-agent:latest echo "Test"
   ```

3. Review agent working directories:
   ```bash
   ls -la ./evanai-runtime/agent-working-directory/
   ```

## License

Part of the EvanAI Client project.
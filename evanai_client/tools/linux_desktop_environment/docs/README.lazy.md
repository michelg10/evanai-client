# Lazy Container Initialization for Claude Agents

An efficient container management system that **only spins up containers when the bash tool is invoked**, not when conversations start. This provides significant resource savings and better scalability.

## Key Features

✅ **Lazy Initialization**: Containers created only on first bash command
✅ **Conversation Isolation**: Each conversation gets its own container
✅ **Automatic Cleanup**: Idle containers stop after timeout (default 5 min)
✅ **Resource Efficiency**: No wasted containers for conversations without bash usage
✅ **Transparent Operation**: Seamless container lifecycle management

## Architecture

```
┌─────────────────────┐
│  Claude Agent       │
│  (Conversation)     │
└──────────┬──────────┘
           │
           │ bash("command")
           ▼
┌─────────────────────┐
│  Lazy Manager       │──► No Container? Create it!
│                     │──► Container exists? Use it!
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Docker Container   │
│  (Created on demand)│
│  /mnt → agent-dir   │
└─────────────────────┘
```

## Lifecycle Flow

```
1. Conversation starts     → No container (0 resources)
2. User asks question      → No container (just text)
3. User: "Check disk"      → Claude needs bash tool
4. bash("df -h")          → Container created NOW
5. bash("ls")             → Reuses same container
6. 5 minutes idle         → Container auto-stops
7. bash("pwd")            → Container restarts
```

## Quick Start

### 1. Build the Agent Image

```bash
./build-agent.sh
```

### 2. Run with Python API

```python
from lazy_agent_manager import ConversationAgent

# Create agent for conversation (NO container yet!)
agent = ConversationAgent(conversation_id="chat-12345")

# First bash command creates container
result = agent.bash("echo 'Container created now!'")
print(result["output"])  # Container spins up here

# Subsequent commands reuse container
result = agent.bash("ls -la /mnt")
print(result["output"])  # Uses existing container
```

### 3. Run with FastAPI Service

```bash
# Install dependencies
pip install fastapi uvicorn docker

# Start API server
python conversation_api.py

# In another terminal:
# First command creates container
curl -X POST http://localhost:8000/conversations/chat-001/bash \
  -H "Content-Type: application/json" \
  -d '{"command": "echo Hello"}'

# Check conversation status
curl http://localhost:8000/conversations/chat-001
```

## Usage Examples

### Basic Conversation Flow

```python
from lazy_agent_manager import LazyAgentManager

manager = LazyAgentManager(
    default_idle_timeout=300  # 5 minutes
)

# Conversation 1: Uses bash
conv1_result = manager.execute_bash(
    "conversation-001",
    "python3 --version"
)
# Container created for conversation-001

# Conversation 2: Never uses bash
# (No container ever created - saves resources!)

# Conversation 3: Uses bash later
# ... after 10 messages without bash ...
conv3_result = manager.execute_bash(
    "conversation-003",
    "ls -la"
)
# Container created only now when needed
```

### Integration with Claude

```python
class ClaudeConversation:
    """Example Claude conversation handler with lazy containers."""

    def __init__(self, conversation_id):
        self.conversation_id = conversation_id
        self.lazy_manager = LazyAgentManager()
        self.container_created = False

    def handle_message(self, message):
        """Process user message."""

        # Most messages don't need containers
        if not self.needs_bash(message):
            return self.generate_response(message)

        # Container created only when bash is needed
        if not self.container_created:
            print(f"Creating container for {self.conversation_id}")
            self.container_created = True

        # Execute bash command
        result = self.lazy_manager.execute_bash(
            self.conversation_id,
            self.extract_bash_command(message)
        )

        return self.format_bash_response(result)
```

### API Usage Examples

#### Check Container Status

```bash
# Get conversation info (shows if container exists)
curl http://localhost:8000/conversations/chat-001

# Response when no container yet:
{
  "conversation_id": "chat-001",
  "state": "not_created",
  "container_active": false,
  "command_count": 0
}

# Response after first bash command:
{
  "conversation_id": "chat-001",
  "state": "running",
  "container_active": true,
  "command_count": 1,
  "idle_seconds": 2.5
}
```

#### Simulate Claude Conversation

```bash
curl -X POST http://localhost:8000/demo/simulate-claude-conversation

# Shows container creation on first bash usage
```

## Resource Savings

### Traditional Approach
```
10 conversations started
└── 10 containers created immediately
└── 3 conversations use bash
└── 7 containers wasted (never used!)
```

### Lazy Approach
```
10 conversations started
└── 0 containers created
└── 3 conversations use bash
└── 3 containers created (only when needed)
└── 0 containers wasted!
```

### Memory Impact
- Traditional: 10 conversations × 2GB = 20GB allocated
- Lazy: 3 active × 2GB = 6GB allocated
- **Savings: 70% less memory usage**

## Configuration

### Idle Timeout

```python
# Short timeout for development (1 minute)
manager = LazyAgentManager(default_idle_timeout=60)

# Long timeout for long-running tasks (30 minutes)
manager = LazyAgentManager(default_idle_timeout=1800)

# No timeout (containers stay alive)
manager = LazyAgentManager(default_idle_timeout=0)
```

### Resource Limits

```python
agent = manager.get_or_create_agent(
    conversation_id="heavy-task",
    memory_limit="8g",  # More memory for data processing
    cpu_limit=4.0       # More CPU for computation
)
```

### Maximum Agents

```python
# Limit concurrent agents (LRU eviction)
manager = LazyAgentManager(
    max_agents=50  # Maximum 50 concurrent containers
)
```

## Monitoring

### Get System Statistics

```python
stats = manager.get_stats()
print(f"Total agents: {stats['total_agents']}")
print(f"By state: {stats['agents_by_state']}")
print(f"Total commands: {stats['total_commands']}")

# Output:
# Total agents: 5
# By state: {'not_created': 2, 'running': 2, 'stopped': 1}
# Total commands: 47
```

### Track Container Creation

```python
result = manager.execute_bash("conv-001", "echo test")

if result["command_count"] == 1:
    print("Container was just created!")
else:
    print(f"Reusing container (command #{result['command_count']})")
```

## Best Practices

### 1. Use Meaningful Conversation IDs

```python
# Good: Traceable and debuggable
conversation_id = f"user-{user_id}-session-{session_id}"
conversation_id = f"claude-{timestamp}-{request_id}"

# Bad: Random UUIDs make debugging hard
conversation_id = str(uuid.uuid4())
```

### 2. Handle Container Creation Latency

```python
async def execute_with_feedback(conversation_id, command):
    """Execute with user feedback about container creation."""

    # Check if container exists
    stats = manager.get_stats()
    container_exists = any(
        a["agent_id"] == conversation_id and a["state"] != "not_created"
        for a in stats["agents"]
    )

    if not container_exists:
        print("Initializing environment (first command)...")

    result = manager.execute_bash(conversation_id, command)

    if not container_exists:
        print("Environment ready!")

    return result
```

### 3. Cleanup After Conversations

```python
class ConversationContext:
    """Context manager for conversations."""

    def __init__(self, conversation_id):
        self.conversation_id = conversation_id
        self.manager = LazyAgentManager()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clean up container if it was created
        self.manager.cleanup_conversation(
            self.conversation_id,
            remove_data=True
        )

# Usage
with ConversationContext("chat-001") as ctx:
    # Container created only if bash is used
    result = ctx.manager.execute_bash("chat-001", "pwd")
# Container automatically cleaned up
```

### 4. Warm-up for Known Bash Usage

```python
async def prepare_for_heavy_task(conversation_id):
    """Pre-warm container if we know bash will be used."""

    # Create container proactively for known bash-heavy tasks
    manager.execute_bash(conversation_id, "echo 'Warming up'")

    # Now container is ready for immediate use
    return conversation_id
```

## Performance Characteristics

### Container Creation Time
- First bash command: ~2-3 seconds (container creation)
- Subsequent commands: ~50-100ms (container ready)

### Memory Usage
- Idle conversation: 0 MB (no container)
- Active container: ~100-200 MB (base overhead)
- With data loaded: Varies by workload

### Cleanup Timing
- Default idle timeout: 5 minutes
- Cleanup check interval: 1 minute
- Stop time: ~1 second

## Troubleshooting

### Container Not Creating

```python
# Check Docker connection
try:
    import docker
    client = docker.from_env()
    client.ping()
    print("Docker is accessible")
except Exception as e:
    print(f"Docker error: {e}")
```

### Container Stopping Too Soon

```python
# Increase idle timeout
manager = LazyAgentManager(
    default_idle_timeout=600  # 10 minutes instead of 5
)

# Or disable timeout for specific conversation
agent = manager.get_or_create_agent(
    "long-running-task",
    idle_timeout=0  # Never timeout
)
```

### Memory Issues

```bash
# Check container memory usage
docker stats claude-agent-*

# Increase memory limit
agent = manager.get_or_create_agent(
    "memory-intensive",
    memory_limit="8g"
)
```

## Comparison: Lazy vs Eager

| Aspect | Eager (Traditional) | Lazy (This System) |
|--------|--------------------|--------------------|
| Container Creation | On conversation start | On first bash command |
| Resource Usage | High (all conversations) | Low (only active) |
| Startup Time | Slow (create container) | Fast (no container) |
| First Bash Command | Fast (container ready) | Slower (create container) |
| Idle Conversations | Waste resources | Zero resources |
| Scalability | Limited by resources | Much higher |
| Complexity | Simple | Slightly complex |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/conversations/{id}/bash` | POST | Execute bash command (creates container if needed) |
| `/conversations/{id}` | GET | Get conversation info |
| `/conversations/{id}` | DELETE | Clean up conversation |
| `/conversations` | GET | List all conversations |
| `/stats` | GET | System statistics |
| `/health` | GET | Health check |

## Complete Example

```python
#!/usr/bin/env python3
"""Complete example of lazy container management."""

from lazy_agent_manager import LazyAgentManager
import time

def main():
    # Initialize manager
    manager = LazyAgentManager(
        runtime_dir="./evanai_runtime",
        default_idle_timeout=300,
        max_agents=10
    )

    # Simulate multiple conversations
    conversations = [
        ("conv-1", ["echo 'Hello'", "ls /mnt"]),  # Uses bash
        ("conv-2", []),  # No bash commands
        ("conv-3", ["python3 --version"]),  # Uses bash
        ("conv-4", []),  # No bash commands
    ]

    print("Starting conversations...")
    print(f"Initial stats: {manager.get_stats()['agents_by_state']}")

    for conv_id, commands in conversations:
        print(f"\nConversation: {conv_id}")

        if not commands:
            print("  No bash commands (no container created)")
            continue

        for cmd in commands:
            result = manager.execute_bash(conv_id, cmd)
            print(f"  Command: {cmd[:30]}...")
            print(f"  Container created: {result['command_count'] == 1}")

    # Check final state
    print(f"\nFinal stats: {manager.get_stats()['agents_by_state']}")
    print("Note: Only conversations with bash commands created containers!")

    # Cleanup
    manager.cleanup_all()

if __name__ == "__main__":
    main()
```

## Summary

The lazy container initialization system ensures:

1. **Containers are only created when bash is actually used**
2. **Each conversation gets its own isolated environment**
3. **Idle containers automatically stop to save resources**
4. **Transparent container lifecycle management**
5. **Significant resource savings for typical usage patterns**

This approach is ideal for Claude-like agents where many conversations may never need bash commands, resulting in dramatic resource savings while maintaining full functionality when needed.
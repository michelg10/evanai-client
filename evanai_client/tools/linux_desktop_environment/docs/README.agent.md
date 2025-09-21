# Claude Agent Isolated Environment

A secure, isolated Docker environment for running Claude-based agents with Bash execution capabilities. Each agent runs in a read-only container with only `/mnt` writable, mounted from a unique agent-specific directory.

## Key Features

- **Read-only root filesystem**: System files cannot be modified
- **Isolated working directory**: Each agent has unique `/mnt` mounted from `evanai_runtime/agent-working-directory/<ID>`
- **Resource limits**: Configurable memory and CPU constraints
- **Security hardening**: Dropped capabilities, no new privileges, ulimits
- **Agent isolation**: Each agent appears to have its own environment
- **Bash tool support**: Full bash command execution in controlled environment

## Architecture

```
evanai_runtime/
└── agent-working-directory/
    ├── agent-001/           # Agent 1's writable space (/mnt)
    ├── agent-002/           # Agent 2's writable space (/mnt)
    └── agent-xyz/           # Agent N's writable space (/mnt)

Each agent container:
- Read-only: / (entire root filesystem)
- Writable: /mnt (mounted from agent-specific directory)
- Temporary: /tmp/agent (tmpfs, cleared on restart)
```

## Quick Start

### 1. Build the Agent Image

```bash
# Make scripts executable
chmod +x build-agent.sh launch-agent.sh

# Build the image
./build-agent.sh

# Or build without cache
./build-agent.sh --no-cache
```

### 2. Launch an Agent

#### Option A: Using Launch Script (Recommended)
```bash
# Auto-generate agent ID
./launch-agent.sh --interactive

# Specify agent ID
./launch-agent.sh --id agent-001 --interactive

# Run with custom resources
./launch-agent.sh --id agent-002 --memory 4g --cpu 4

# Run command and exit
./launch-agent.sh --id agent-003 --rm python3 /mnt/script.py
```

#### Option B: Using Python Manager
```bash
# Install Docker Python library
pip install docker

# Create agent
python3 agent_manager.py create --id my-agent

# List agents
python3 agent_manager.py list

# Execute command in agent
python3 agent_manager.py exec my-agent ls -la /mnt

# View logs
python3 agent_manager.py logs my-agent

# Stop agent
python3 agent_manager.py stop my-agent

# Remove agent
python3 agent_manager.py remove my-agent --data
```

#### Option C: Direct Docker Commands
```bash
# Create working directory
mkdir -p evanai_runtime/agent-working-directory/my-agent

# Run agent container with host network
docker run -it --rm \
  --name claude-agent-my-agent \
  --network host \
  --read-only \
  --tmpfs /tmp/agent:rw,noexec,nosuid,size=100m \
  --tmpfs /home/agent/.cache:rw,noexec,nosuid,size=50m \
  -v $(pwd)/evanai_runtime/agent-working-directory/my-agent:/mnt \
  -e AGENT_ID=my-agent \
  --security-opt no-new-privileges \
  --cap-drop ALL \
  --cap-add CHOWN,DAC_OVERRIDE,SETGID,SETUID,NET_RAW,NET_BIND_SERVICE \
  claude-agent:latest
```

## Agent Management

### Python Agent Manager

The `agent_manager.py` provides programmatic control:

```python
from agent_manager import AgentManager

# Initialize manager
manager = AgentManager(runtime_dir="./evanai_runtime")

# Create agent
info = manager.create_agent(
    agent_id="data-processor",
    memory_limit="4g",
    cpu_limit=2.0
)

# Execute bash command
exit_code, stdout, stderr = manager.execute_command(
    "data-processor",
    "cd /mnt && python3 process.py"
)

# Get logs
logs = manager.get_logs("data-processor", tail=50)

# Stop and remove
manager.stop_agent("data-processor")
manager.remove_agent("data-processor", remove_data=True)
```

### Batch Operations

```bash
# Create multiple agents
for i in {1..5}; do
    ./launch-agent.sh --id "worker-$i" -d
done

# Execute command across all agents
for i in {1..5}; do
    docker exec claude-agent-worker-$i bash -c "echo 'Task $i' > /mnt/result.txt"
done

# Clean up stopped agents
python3 agent_manager.py cleanup
```

## Security Model

### Filesystem Isolation
- **Read-only root**: Prevents system modification
- **Writable /mnt**: Agent's only persistent storage
- **Tmpfs /tmp**: Temporary files cleared on restart

### Network Access
- **Host Network Mode**: Full access to host network
- **Can access localhost services**: Database, APIs, etc.
- **Direct external connectivity**: No NAT overhead
- **Port binding**: Can bind to host ports

### Resource Limits
- Memory: Default 2GB (configurable)
- CPU: Default 2 cores (configurable)
- File descriptors: 1024 soft, 2048 hard
- Processes: 512 soft, 1024 hard

### Capabilities
- **Dropped**: ALL capabilities by default
- **Added**: Minimal set for file operations
  - CHOWN: Change file ownership
  - DAC_OVERRIDE: Bypass file permissions
  - SETGID/SETUID: Change process identity

### Network Configuration
- **Host Network Mode**: Agents use host's network stack
- **Full connectivity**: Access to all host services and external networks
- **No isolation**: Agents share network namespace with host
- **Better performance**: No bridge/NAT overhead

## Environment Details

### Pre-installed Software

**Languages & Runtimes:**
- Python 3.12 with data science libraries
- Node.js 18.x with npm
- Java OpenJDK 21

**Tools:**
- Git, vim, nano
- Pandoc, ImageMagick
- FFmpeg, Tesseract OCR
- Database clients (sqlite3, psql, mysql)

**Python Libraries:**
- numpy, pandas, scipy
- matplotlib, Pillow
- requests, beautifulsoup4
- PyPDF, python-docx

### Environment Variables

Available in each agent:
```bash
AGENT_ID=<agent-identifier>
AGENT_WORK_DIR=/mnt
TMPDIR=/tmp/agent
PYTHONPATH=/mnt:$PYTHONPATH
```

## Use Cases

### 1. Data Processing Agent
```bash
# Create agent with data directory
./launch-agent.sh --id data-proc --memory 4g

# In another terminal, copy data
docker cp dataset.csv claude-agent-data-proc:/mnt/

# Execute processing
docker exec claude-agent-data-proc python3 -c "
import pandas as pd
df = pd.read_csv('/mnt/dataset.csv')
result = df.groupby('category').sum()
result.to_csv('/mnt/results.csv')
"

# Retrieve results
docker cp claude-agent-data-proc:/mnt/results.csv ./
```

### 2. Web Scraping Agent (With Host Network Access)
```bash
# Launch agent
./launch-agent.sh --id scraper -d

# Deploy scraping script (can access localhost services)
cat > evanai_runtime/agent-working-directory/scraper/scrape.py << 'EOF'
import requests
from bs4 import BeautifulSoup

# Can access both external sites and localhost services
response = requests.get('https://example.com')
soup = BeautifulSoup(response.content, 'html.parser')

# Can also access host services
local_api = requests.get('http://localhost:8080/api/data')

with open('/mnt/output.txt', 'w') as f:
    f.write(soup.get_text())
    f.write('\n\nLocal API response:\n')
    f.write(local_api.text)
EOF

# Execute
docker exec claude-agent-scraper python3 /mnt/scrape.py
```

### 3. Document Processing Agent
```bash
# Create agent
python3 agent_manager.py create --id doc-processor

# Convert documents
python3 agent_manager.py exec doc-processor \
    pandoc /mnt/input.md -o /mnt/output.pdf

# Process PDFs
python3 agent_manager.py exec doc-processor \
    python3 -c "
from pypdf import PdfReader
reader = PdfReader('/mnt/document.pdf')
text = ''.join(page.extract_text() for page in reader.pages)
with open('/mnt/extracted.txt', 'w') as f:
    f.write(text)
"
```

## Troubleshooting

### Container Won't Start
```bash
# Check if image exists
docker images | grep claude-agent

# Rebuild if needed
./build-agent.sh --no-cache

# Check for port/name conflicts
docker ps -a | grep claude-agent
```

### Permission Denied in /mnt
```bash
# Ensure directory exists and has correct permissions
mkdir -p evanai_runtime/agent-working-directory/my-agent
chmod 755 evanai_runtime/agent-working-directory/my-agent

# Check mount in container
docker exec claude-agent-my-agent mount | grep /mnt
```

### Out of Memory
```bash
# Increase memory limit
./launch-agent.sh --id my-agent --memory 8g

# Or modify running container (requires restart)
docker update --memory 8g claude-agent-my-agent
docker restart claude-agent-my-agent
```

### Read-only Filesystem Errors
```bash
# These paths should be writable:
/mnt            # Agent working directory
/tmp/agent      # Temporary files
/home/agent/.cache  # Cache directory

# Verify with:
docker exec claude-agent-my-agent touch /mnt/test.txt
docker exec claude-agent-my-agent touch /tmp/agent/test.txt
```

## Integration with Claude

The environment is designed for Claude-based agents using the Bash tool:

```python
# Example integration (pseudo-code)
class ClaudeAgent:
    def __init__(self, agent_id):
        self.manager = AgentManager()
        self.agent_id = agent_id
        self.manager.create_agent(agent_id=agent_id)

    def execute_bash(self, command):
        """Execute bash command in isolated environment"""
        exit_code, stdout, stderr = self.manager.execute_command(
            self.agent_id,
            command
        )
        return {
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr
        }

    def cleanup(self):
        self.manager.remove_agent(self.agent_id, remove_data=True)

# Usage
agent = ClaudeAgent("task-processor")
result = agent.execute_bash("cd /mnt && ls -la")
print(result["stdout"])
agent.cleanup()
```

## Best Practices

1. **Agent Naming**: Use descriptive IDs like `data-proc-20240120` or `web-scraper-001`

2. **Resource Allocation**: Start conservative, increase as needed
   ```bash
   # Development
   --memory 1g --cpu 1

   # Production
   --memory 4g --cpu 2
   ```

3. **Data Management**: Regular cleanup of unused agent directories
   ```bash
   # Remove agents older than 7 days
   find evanai_runtime/agent-working-directory -maxdepth 1 -type d -mtime +7 -exec rm -rf {} \;
   ```

4. **Monitoring**: Track resource usage
   ```bash
   # Real-time stats
   docker stats claude-agent-*

   # Check disk usage
   du -sh evanai_runtime/agent-working-directory/*
   ```

5. **Security**: Never mount sensitive host directories
   ```bash
   # Good: Agent-specific directory
   -v ./evanai_runtime/agent-working-directory/agent-001:/mnt

   # Bad: System directory
   -v /etc:/mnt  # NEVER DO THIS
   ```

## Cleanup

```bash
# Stop all agents
docker stop $(docker ps -q --filter name=claude-agent-)

# Remove all agents
docker rm $(docker ps -aq --filter name=claude-agent-)

# Clean working directories
rm -rf evanai_runtime/agent-working-directory/*

# Remove Docker image
docker rmi claude-agent:latest

# Remove network
docker network rm agent-network
```

## Performance Tuning

### For I/O Heavy Workloads
```bash
# Increase tmpfs size
--tmpfs /tmp/agent:rw,noexec,nosuid,size=1g
```

### For CPU Intensive Tasks
```bash
# Allow more CPU
./launch-agent.sh --cpu 8
```

### For Memory Intensive Tasks
```bash
# Increase memory and disable swap
./launch-agent.sh --memory 16g
docker update --memory-swap -1 claude-agent-xyz
```

## Support

For issues:
1. Check container logs: `docker logs claude-agent-<id>`
2. Verify image build: `./build-agent.sh`
3. Test basic functionality: `docker run --rm claude-agent:latest bash -c "python3 --version"`
4. Review agent state: `python3 agent_manager.py info <agent-id>`
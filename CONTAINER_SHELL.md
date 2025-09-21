# Container Shell Interface

A powerful interactive interface for debugging and testing EvanAI Linux containers.

## 🚀 Quick Start

### Instant Access
```bash
# Enter interactive mode - browse and select containers
evanai-client container

# Quick shell access (creates container if needed)
evanai-client shell my-test

# Use the quick start script
./container_quickstart.sh
```

## 📋 Features

### 1. **Interactive Mode**
Browse, create, and manage containers with an interactive menu:
```bash
evanai-client container
```

Features:
- List all containers with status
- Create new containers on-demand
- Enter shell with one selection
- Run verification and tests
- Clean up containers

### 2. **Direct Shell Access**
Jump straight into a container:
```bash
# Creates container if it doesn't exist
evanai-client shell my-session

# Or use full name
evanai-client shell claude-agent-my-session
```

### 3. **Container Verification**
Comprehensive environment checks:
```bash
python -m evanai_client.container_shell verify my-session
```

Checks:
- System information (OS, kernel, architecture)
- User and permissions
- Python and Node.js versions
- Skills directory (118 files)
- Working directory writability
- Environment variables
- Disk space and memory
- Running processes

### 4. **Skills Inspection**
Detailed analysis of the skills directory:
```bash
python -m evanai_client.container_shell skills my-session
```

Shows:
- Directory structure
- File counts by category (PDF, DOCX, PPTX, XLSX)
- Example skill files
- Access permissions

### 5. **Stateful Shell Testing**
Test that the shell maintains state:
```bash
python -m evanai_client.container_shell test my-session
```

Tests:
- Working directory persistence (`cd` commands)
- Environment variable persistence (`export`)
- Alias persistence
- File creation and access

## 🔧 Command Reference

### Main Commands

| Command | Description |
|---------|-------------|
| `evanai-client container` | Enter interactive mode |
| `evanai-client shell [name]` | Quick shell access |

### Python Module Commands

```bash
# List containers
python -m evanai_client.container_shell list [--all]

# Create container
python -m evanai_client.container_shell create [conversation_id]

# Enter shell
python -m evanai_client.container_shell shell [container_name]

# Execute command
python -m evanai_client.container_shell exec <container> <command>

# Verify environment
python -m evanai_client.container_shell verify <container>

# Inspect skills
python -m evanai_client.container_shell skills <container>

# Test stateful shell
python -m evanai_client.container_shell test <container>

# Stop container
python -m evanai_client.container_shell stop <container> [--force]

# Clean up all
python -m evanai_client.container_shell cleanup [--force]
```

## 🎯 Interactive Mode Features

When in interactive mode, you get:

### Container List Menu
```
Available containers:
  1. claude-agent-debug-session (running)
  2. claude-agent-test-123 (stopped)
  3. Create new container
  q. Quit
```

### Container Action Menu
```
Container: claude-agent-debug-session
1. Enter shell
2. Run verification
3. Inspect skills
4. Test stateful shell
5. Execute custom command
6. Stop container
7. Back to container list
```

## 📝 Example Workflows

### 1. Debug a Failed Command
```bash
# Create a test container
evanai-client shell debug-test

# Inside container, test commands
cd /tmp
pwd
export MY_VAR="test"
echo $MY_VAR
ls -la /mnt/skills
```

### 2. Verify Skills Are Present
```bash
# Quick verification
python -m evanai_client.container_shell verify debug-test

# Detailed skills inspection
python -m evanai_client.container_shell skills debug-test
```

### 3. Test Stateful Behavior
```bash
# Run automated tests
python -m evanai_client.container_shell test debug-test

# Or manually test
evanai-client shell debug-test
# Then run: cd /tmp && pwd
# Should stay in /tmp across commands
```

### 4. Clean Development Environment
```bash
# Remove all test containers
python -m evanai_client.container_shell cleanup --force
```

## 🔍 Verification Output Example

```
Container Verification: claude-agent-test
============================================================

System Info:
✓ Linux 6.10.11-linuxkit x86_64 GNU/Linux

User Info:
✓ agent
/mnt

Python Version:
✓ Python 3.12.3

Working Directory:
✓ /mnt (writable)

Skills Directory:
✓ 118 files found in /mnt/skills

Environment:
✓ AGENT_ID=test
✓ HOME=/home/agent
✓ USER=agent

Memory:
✓ 2GB allocated, 1.5GB free
```

## 🛠️ Container Details

Each container has:
- **Name**: `claude-agent-<conversation_id>`
- **Image**: `claude-agent:latest`
- **Network**: Host mode (full network access)
- **Memory**: 2GB limit
- **CPU**: 2 CPU quota
- **Volumes**: `/mnt` writable directory
- **Skills**: Pre-mounted at `/mnt/skills`
- **Shell**: Stateful bash with persistence

## 🐛 Troubleshooting

### Docker Not Running
```bash
Error: Cannot connect to Docker. Is Docker running?
# Solution: Start Docker Desktop
```

### Image Not Found
```bash
Image claude-agent:latest not found!
# Solution: Build the image
cd evanai_client/tools/linux_desktop_environment/scripts
./build-agent-image.sh
```

### Container Won't Start
```bash
# Check Docker logs
docker logs claude-agent-my-session

# Force recreate
python -m evanai_client.container_shell stop my-session --force
python -m evanai_client.container_shell create my-session
```

### Skills Not Found
```bash
# Rebuild image with skills
cd evanai_client/tools/linux_desktop_environment/scripts
./build-agent-image.sh

# Verify in container
evanai-client shell test
ls -la /mnt/skills/public
```

## 🎨 Features of the Shell

- **Color-coded output**: Green for success, red for errors, yellow for warnings
- **Auto-completion**: Container names are auto-suggested
- **Stateful sessions**: Each container maintains its own state
- **Quick access**: Direct shell command for immediate access
- **Batch operations**: Clean up multiple containers at once
- **Safe defaults**: Confirmation prompts for destructive operations

## 📚 Integration with Debug Interface

The container shell complements the debug interface:

1. Use debug interface (`evanai-client debug`) for agent testing
2. Use container shell for direct container inspection
3. Both share the same container infrastructure

## 🔐 Security Notes

- Containers run with limited privileges (agent user)
- 2GB memory limit prevents resource exhaustion
- Host network mode allows full network access (for testing)
- `/mnt` is the only writable directory
- Skills are read-only to prevent modification

## 💡 Tips

1. **Keep containers running**: With `idle_timeout=0`, containers persist for your entire session
2. **Name containers meaningfully**: Use descriptive names like `debug-pdf-test`
3. **Use verification first**: Always verify a new container before testing
4. **Check skills access**: Ensure `/mnt/skills` is accessible before testing skill-dependent features
5. **Clean up regularly**: Remove old test containers to save resources

## 🚀 Advanced Usage

### Custom Docker Options
Modify `container_shell.py` to customize:
- Memory limits
- CPU quotas
- Volume mounts
- Environment variables

### Scripting
Use the Python API directly:
```python
from evanai_client.container_shell import ContainerShell

shell = ContainerShell()
container_name = shell.create_container("my-test")
exit_code, output = shell.execute_command(container_name, "ls -la /mnt/skills")
print(output)
shell.cleanup_container(container_name, force=True)
```

### Integration with Tests
Use in pytest or other test frameworks:
```python
def test_skills_present():
    shell = ContainerShell()
    container = shell.create_container("test-skills")
    try:
        _, output = shell.execute_command(container, "find /mnt/skills -type f | wc -l")
        assert int(output.strip()) == 118
    finally:
        shell.cleanup_container(container, force=True)
```
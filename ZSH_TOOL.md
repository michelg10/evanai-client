# ZSH Tool - Persistent macOS Shell Access

A tool that provides persistent ZSH shell access to your macOS environment, maintaining state across command calls.

## Features

- **Persistent Sessions**: Maintains a single ZSH session per conversation
- **State Preservation**: Directory changes and environment variables persist across calls
- **macOS Environment Access**: Full access to your local macOS file system and tools
- **Automatic Session Management**: Creates session on first use, maintains throughout conversation
- **Configurable Timeout**: Default 3 seconds, can be customized per command
- **Clean Output**: Automatically removes shell prompts and control characters

## Usage

### Basic Commands

```python
# List home directory files
zsh("ls ~")

# Change directory (persists for future commands)
zsh("cd ~/Desktop")

# Next command runs in Desktop
zsh("ls")  # Lists Desktop files, not home directory

# Check current directory
zsh("pwd")  # Shows /Users/username/Desktop
```

### With Custom Timeout

```python
# Quick command with 1 second timeout
zsh("echo 'Hello'", timeout=1)

# Longer running command with 10 second timeout
zsh("find ~ -name '*.txt'", timeout=10)
```

## How It Works

### Session Management
1. First `zsh()` call creates a persistent ZSH subprocess
2. Session stays alive throughout the conversation
3. All subsequent commands run in the same session
4. Session cleaned up when conversation ends

### State Persistence Example

```python
# Call 1: Change to Desktop
zsh("cd ~/Desktop")

# Call 2: Create a file (in Desktop)
zsh("echo 'test' > test.txt")

# Call 3: List files (still in Desktop)
zsh("ls test.txt")  # Shows: test.txt

# Call 4: Check location
zsh("pwd")  # Shows: /Users/username/Desktop
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| command | string | Yes | - | The ZSH command to execute |
| timeout | number | No | 3.0 | Maximum seconds to wait for command completion |

## Return Format

```json
{
    "stdout": "Command output",
    "stderr": "Error output if any",
    "command": "The command that was executed",
    "session_active": true
}
```

## Technical Details

### Implementation
- Uses `subprocess.Popen` with `/bin/zsh -i` for interactive shell
- Maintains separate stdout/stderr reader threads
- Queue-based output collection with timeout
- Automatic session restart if process dies

### Differences from console_tool
- **Simpler Interface**: Single command function vs multiple session management functions
- **Automatic Sessions**: No need to explicitly start/stop sessions
- **ZSH vs Bash**: Uses ZSH (macOS default) instead of Bash
- **One Session Per Conversation**: Automatically maintains one session, not multiple

## Example Use Cases

### File Management
```python
# Navigate to Documents
zsh("cd ~/Documents")

# Create a new directory
zsh("mkdir my-project")

# Move into it
zsh("cd my-project")

# Create files
zsh("touch README.md main.py")

# List contents
zsh("ls -la")
```

### System Information
```python
# Check system info
zsh("uname -a")

# Check disk usage
zsh("df -h")

# See running processes
zsh("ps aux | grep python")
```

### Development Tasks
```python
# Check Python version
zsh("python3 --version")

# Run a Python script
zsh("python3 my_script.py")

# Check git status
zsh("cd ~/my-repo && git status")
```

## Limitations

- **Timeout**: Commands that exceed timeout will be interrupted
- **Interactive Programs**: Not suitable for interactive programs (like vim, less)
- **Background Jobs**: Background jobs may not behave as expected
- **Session Lifetime**: Session dies when conversation ends

## Security Considerations

- Has full access to user's macOS environment
- Can read/write files with user's permissions
- Can execute any command the user can run
- Use with appropriate caution

## Installation

The tool is automatically loaded when the EvanAI client starts. No additional installation needed.

## Files

- `evanai_client/tools/zsh_tool.py` - Main implementation
- `test_zsh_tool.py` - Test script demonstrating functionality
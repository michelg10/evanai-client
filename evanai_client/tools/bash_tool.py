"""
Bash tool for executing commands in isolated Linux containers.

This tool provides Claude agents with bash command execution capabilities
in isolated, per-conversation Docker containers. Containers are lazily
initialized on first use to save resources.
"""

import os
import sys
import json
import time
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Add linux-desktop-environment to path for imports
tool_dir = Path(__file__).parent
linux_env_dir = tool_dir / "linux-desktop-environment"
if str(linux_env_dir) not in sys.path:
    sys.path.insert(0, str(linux_env_dir))

from ..tool_system import BaseToolSetProvider, Tool, Parameter, ParameterType

# Import the lazy container manager
try:
    # Try relative import first
    from .linux_desktop_environment.lazy_agent_manager import LazyAgentManager, ConversationAgent
except ImportError:
    try:
        # Try absolute import
        from lazy_agent_manager import LazyAgentManager, ConversationAgent
    except ImportError:
        # Fallback to direct import if package structure is different
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "lazy_agent_manager",
            linux_env_dir / "lazy_agent_manager.py"
        )
        lazy_agent_manager = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lazy_agent_manager)
        LazyAgentManager = lazy_agent_manager.LazyAgentManager
        ConversationAgent = lazy_agent_manager.ConversationAgent


class BashToolProvider(BaseToolSetProvider):
    """
    Provides bash command execution in isolated Docker containers.

    Each conversation gets its own container with:
    - Read-only root filesystem (security)
    - Writable /mnt directory (workspace)
    - Lazy initialization (created on first use)
    - Automatic cleanup after idle timeout
    """

    def __init__(
        self,
        websocket_handler=None,  # Required by EvanAI tool system
        runtime_dir: Optional[str] = None,
        idle_timeout: int = 0,  # 0 = no timeout, container runs forever
        memory_limit: str = "2g",
        cpu_limit: float = 2.0,
        image: str = "claude-agent:latest",
        auto_cleanup: bool = True,
        enable_logging: bool = True
    ):
        """
        Initialize the Bash tool provider.

        Args:
            websocket_handler: WebSocket handler for communication (required by tool system)
            runtime_dir: Base directory for agent runtime data
            idle_timeout: Seconds before idle container stops (0 = no timeout)
            memory_limit: Memory limit for containers
            cpu_limit: CPU limit for containers
            image: Docker image to use for containers
            auto_cleanup: Automatically cleanup stopped containers
            enable_logging: Enable command logging
        """
        # Call parent constructor
        super().__init__(websocket_handler)

        self.websocket_handler = websocket_handler
        self.runtime_dir = runtime_dir or os.environ.get(
            'EVANAI_RUNTIME_DIR',
            './evanai_runtime'
        )
        self.idle_timeout = idle_timeout
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.image = image
        self.auto_cleanup = auto_cleanup
        self.enable_logging = enable_logging

        # Global container manager (shared across all conversations)
        self.manager = None

        # Host network configuration
        self.use_host_network = True

        # Track statistics
        self.total_commands = 0
        self.total_containers_created = 0

    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Any]]:
        """Initialize the bash tool."""

        # Define the bash tool
        tools = [
            Tool(
                id="bash",
                name="Bash Command Execution",
                description=(
                    "Execute bash commands in a stateful Linux environment with full network access. "
                    "Each conversation has its own persistent container with a writable /mnt directory. "
                    "The shell maintains state across commands (working directory, environment variables, aliases). "
                    "Use 'cd' to change directories - the shell remembers your location. "
                    "Network: Host network mode (full access to host network services)."
                ),
                parameters={
                    "command": Parameter(
                        name="command",
                        type=ParameterType.STRING,
                        description="Bash command to execute",
                        required=True
                    ),
                    "timeout": Parameter(
                        name="timeout",
                        type=ParameterType.INTEGER,
                        description="Command timeout in seconds (default: 0 = no timeout)",
                        required=False,
                        default=120
                    )
                }
            ),
            Tool(
                id="bash_status",
                name="Bash Environment Status",
                description="Get status of the bash environment for this conversation",
                parameters={}
            ),
            Tool(
                id="bash_reset",
                name="Reset Bash Environment",
                description="Reset the bash environment (stops and removes container)",
                parameters={
                    "keep_data": Parameter(
                        name="keep_data",
                        type=ParameterType.BOOLEAN,
                        description="Keep the /mnt data after reset",
                        required=False,
                        default=False
                    )
                }
            )
        ]

        # Initialize global manager
        if not self.manager:
            self.manager = LazyAgentManager(
                runtime_dir=self.runtime_dir,
                image=self.image,
                default_idle_timeout=self.idle_timeout,
                max_agents=100
            )
            print(f"[BashTool] Initialized with runtime dir: {self.runtime_dir}")
            print(f"[BashTool] Network mode: host (full network access)")

        # Global state (shared across conversations)
        global_state = {
            "manager": self.manager,
            "runtime_dir": self.runtime_dir,
            "total_commands": 0,
            "total_containers": 0
        }

        # Per-conversation state
        per_conversation_state = {
            "container_created": False,
            "command_count": 0,
            "last_command_time": None,
            "working_directory": "/mnt"
        }

        return tools, global_state, per_conversation_state

    def call_tool(
        self,
        tool_id: str,
        tool_parameters: Dict[str, Any],
        per_conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """
        Execute a bash tool command.

        Args:
            tool_id: The tool to execute (bash, bash_status, bash_reset)
            tool_parameters: Parameters for the tool
            per_conversation_state: State for this conversation
            global_state: Global state shared across conversations

        Returns:
            Tuple of (result, error_message)
        """

        # Get conversation ID from state or generate one
        conversation_id = per_conversation_state.get('_conversation_id')
        if not conversation_id:
            # Generate conversation ID if not set
            from datetime import datetime
            import uuid
            conversation_id = f"conv-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
            per_conversation_state['_conversation_id'] = conversation_id

        # Initialize conversation state if needed
        if 'command_count' not in per_conversation_state:
            per_conversation_state['command_count'] = 0
            per_conversation_state['container_created'] = False
            per_conversation_state['last_command_time'] = None
            per_conversation_state['working_directory'] = '/mnt'

        manager = global_state["manager"]

        try:
            if tool_id == "bash":
                return self._execute_bash(
                    manager,
                    conversation_id,
                    tool_parameters,
                    per_conversation_state,
                    global_state
                )
            elif tool_id == "bash_status":
                return self._get_status(
                    manager,
                    conversation_id,
                    per_conversation_state
                )
            elif tool_id == "bash_reset":
                return self._reset_environment(
                    manager,
                    conversation_id,
                    tool_parameters,
                    per_conversation_state
                )
            else:
                return None, f"Unknown tool: {tool_id}"

        except Exception as e:
            return None, f"Error executing {tool_id}: {str(e)}"

    def _execute_bash(
        self,
        manager: LazyAgentManager,
        conversation_id: str,
        parameters: Dict[str, Any],
        conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Execute a bash command in the conversation's container."""

        command = parameters.get("command")
        if not command:
            return None, "Command parameter is required"

        timeout = parameters.get("timeout", 120)  # Default 2 minute command timeout

        # Track if this is the first command
        is_first = conversation_state["command_count"] == 0

        # Log command if enabled
        if self.enable_logging:
            print(f"[BashTool][{conversation_id}] Executing: {command[:100]}...")

        # Execute command (container created lazily if needed)
        start_time = time.time()

        # Get agent and execute
        agent = manager.get_or_create_agent(
            conversation_id=conversation_id,
            memory_limit=self.memory_limit,
            cpu_limit=self.cpu_limit,
            idle_timeout=self.idle_timeout
        )

        exit_code, stdout, stderr = agent.execute_command(command, timeout)

        execution_time = time.time() - start_time

        # Update state
        conversation_state["command_count"] += 1
        conversation_state["last_command_time"] = datetime.now().isoformat()

        if is_first:
            conversation_state["container_created"] = True
            global_state["total_containers"] += 1
            self.total_containers_created += 1

            if self.enable_logging:
                print(f"[BashTool][{conversation_id}] Container created (lazy init)")

        global_state["total_commands"] += 1
        self.total_commands += 1

        # Prepare result
        result = {
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "success": exit_code == 0,
            "command": command,
            "execution_time": execution_time,
            "conversation_id": conversation_id,
            "command_number": conversation_state["command_count"],
            "container_was_created": is_first
        }

        # Add combined output for convenience
        if result["success"]:
            result["output"] = stdout
        else:
            result["output"] = stderr if stderr else stdout

        return result, None

    def _get_status(
        self,
        manager: LazyAgentManager,
        conversation_id: str,
        conversation_state: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Get status of the conversation's bash environment."""

        # Get agent if it exists
        if conversation_id in manager.agents:
            agent = manager.agents[conversation_id]
            stats = agent.get_stats()

            result = {
                "conversation_id": conversation_id,
                "container_state": stats["state"],
                "container_active": stats["state"] == "running",
                "command_count": stats["command_count"],
                "last_activity": stats.get("last_activity"),
                "uptime_seconds": stats.get("uptime_seconds"),
                "idle_seconds": stats.get("idle_seconds"),
                "work_dir": stats["work_dir"],
                "memory_limit": stats["memory_limit"],
                "cpu_limit": stats["cpu_limit"]
            }
        else:
            result = {
                "conversation_id": conversation_id,
                "container_state": "not_created",
                "container_active": False,
                "command_count": 0,
                "last_activity": None,
                "message": "No container created yet (will be created on first bash command)"
            }

        return result, None

    def _reset_environment(
        self,
        manager: LazyAgentManager,
        conversation_id: str,
        parameters: Dict[str, Any],
        conversation_state: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Reset the bash environment for this conversation."""

        keep_data = parameters.get("keep_data", False)

        # Clean up if container exists
        if conversation_id in manager.agents:
            agent = manager.agents[conversation_id]
            agent.cleanup(remove_data=not keep_data)
            del manager.agents[conversation_id]

            # Reset conversation state
            conversation_state["container_created"] = False
            conversation_state["command_count"] = 0
            conversation_state["last_command_time"] = None

            result = {
                "status": "reset",
                "conversation_id": conversation_id,
                "data_kept": keep_data,
                "message": "Container stopped and removed. New container will be created on next bash command."
            }

            if self.enable_logging:
                print(f"[BashTool][{conversation_id}] Environment reset")
        else:
            result = {
                "status": "no_container",
                "conversation_id": conversation_id,
                "message": "No container to reset"
            }

        return result, None

    def cleanup(self):
        """Clean up all resources."""
        if self.manager:
            if self.enable_logging:
                print(f"[BashTool] Cleaning up. Total commands: {self.total_commands}, "
                      f"Containers created: {self.total_containers_created}")

            if self.auto_cleanup:
                self.manager.cleanup_all(remove_data=True)


# Convenience function for direct usage
def create_bash_tool(
    websocket_handler=None,
    runtime_dir: Optional[str] = None,
    idle_timeout: int = 300,
    memory_limit: str = "2g",
    cpu_limit: float = 2.0
) -> BashToolProvider:
    """
    Create a bash tool provider with default settings.

    Args:
        websocket_handler: WebSocket handler for communication
        runtime_dir: Base directory for runtime data
        idle_timeout: Container idle timeout in seconds
        memory_limit: Memory limit for containers
        cpu_limit: CPU limit for containers

    Returns:
        Configured BashToolProvider instance
    """
    return BashToolProvider(
        websocket_handler=websocket_handler,
        runtime_dir=runtime_dir,
        idle_timeout=idle_timeout,
        memory_limit=memory_limit,
        cpu_limit=cpu_limit
    )


# Example usage
if __name__ == "__main__":
    print("=== Bash Tool Example ===\n")

    # Create tool provider
    bash_tool = BashToolProvider(
        runtime_dir="./evanai_runtime",
        idle_timeout=0  # No timeout
    )

    # Initialize
    tools, global_state, conv_state = bash_tool.init()

    # Simulate conversation
    conv_state["_conversation_id"] = "demo-conversation"

    print("1. Check status (no container yet)")
    result, error = bash_tool.call_tool(
        "bash_status", {}, conv_state, global_state
    )
    print(f"   Status: {result['container_state']}\n")

    print("2. Execute first command (creates container)")
    result, error = bash_tool.call_tool(
        "bash",
        {"command": "echo 'Hello from Bash tool!' && pwd"},
        conv_state,
        global_state
    )
    if not error:
        print(f"   Output: {result['output']}")
        print(f"   Container created: {result['container_was_created']}\n")

    print("3. Execute another command (reuses container)")
    result, error = bash_tool.call_tool(
        "bash",
        {"command": "echo 'Test data' > /mnt/test.txt && cat /mnt/test.txt"},
        conv_state,
        global_state
    )
    if not error:
        print(f"   Output: {result['output']}")
        print(f"   Command #: {result['command_number']}\n")

    print("4. Check status again")
    result, error = bash_tool.call_tool(
        "bash_status", {}, conv_state, global_state
    )
    print(f"   Container active: {result['container_active']}")
    print(f"   Commands executed: {result['command_count']}\n")

    print("5. Reset environment")
    result, error = bash_tool.call_tool(
        "bash_reset", {"keep_data": False}, conv_state, global_state
    )
    print(f"   Result: {result['message']}\n")

    # Cleanup
    bash_tool.cleanup()
    print("Done!")
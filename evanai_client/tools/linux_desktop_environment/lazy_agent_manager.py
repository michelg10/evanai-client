#!/usr/bin/env python3
"""
Lazy Agent Manager for Claude-based agents.

Containers are only created when the bash tool is first invoked,
not when conversations start. Includes automatic cleanup of idle containers.
"""

import os
import sys
import json
import time
import uuid
import shutil
import threading
import weakref
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import docker
from docker.errors import NotFound, APIError

# Import StatefulShell for maintaining shell state
try:
    from .stateful_shell import StatefulShell
except ImportError:
    from stateful_shell import StatefulShell


class AgentState(Enum):
    """Agent lifecycle states."""
    NOT_CREATED = "not_created"
    STARTING = "starting"
    RUNNING = "running"
    IDLE = "idle"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class LazyAgent:
    """
    Represents a single lazy-initialized agent container.
    Container is only created when first command is executed.
    """

    def __init__(
        self,
        agent_id: str,
        manager: 'LazyAgentManager',
        memory_limit: str = "2g",
        cpu_limit: float = 2.0,
        idle_timeout: int = 0  # 0 = no timeout
    ):
        self.agent_id = agent_id
        self.manager = manager
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.idle_timeout = idle_timeout

        self.state = AgentState.NOT_CREATED
        self.container = None
        self.container_name = f"claude-agent-{agent_id}"
        self.work_dir = self.manager.working_dir_base / agent_id

        self.last_activity = datetime.now()
        self.command_count = 0
        self.creation_time = None
        self.cleanup_timer = None

        # Stateful shell for maintaining shell state across commands
        self.shell_state = StatefulShell(agent_id, initial_workdir="/mnt")

        # Thread safety
        self._lock = threading.RLock()

    def _ensure_container(self) -> bool:
        """
        Ensure container exists and is running.
        This is called lazily on first command execution.
        """
        with self._lock:
            if self.state == AgentState.RUNNING:
                return True

            if self.state == AgentState.STARTING:
                # Wait for container to be ready
                timeout = 300  # Increase container start timeout to 5 minutes
                start = time.time()
                while self.state == AgentState.STARTING and time.time() - start < timeout:
                    time.sleep(0.1)
                return self.state == AgentState.RUNNING

            if self.state in [AgentState.STOPPED, AgentState.ERROR]:
                # Container existed but stopped, remove it first
                self._cleanup_container()

            # Create container
            return self._create_container()

    def _create_container(self) -> bool:
        """Create and start the container."""
        with self._lock:
            if self.state == AgentState.RUNNING:
                return True

            self.state = AgentState.STARTING
            print(f"[{self.agent_id}] Lazy-initializing container...")

            try:
                # Create working directory
                self.work_dir.mkdir(parents=True, exist_ok=True)

                # Container configuration
                config = {
                    "image": self.manager.image,
                    "name": self.container_name,
                    "environment": {
                        "AGENT_ID": self.agent_id,
                        "AGENT_WORK_DIR": "/mnt"
                    },
                    "volumes": {
                        str(self.work_dir): {"bind": "/mnt", "mode": "rw"}
                    },
                    "network_mode": "host",  # Use host network for full access
                    "mem_limit": self.memory_limit,
                    "nano_cpus": int(self.cpu_limit * 1_000_000_000),
                    "read_only": True,
                    "tmpfs": {
                        "/tmp": "rw,noexec,nosuid,size=100m",
                        "/home/agent/.cache": "rw,noexec,nosuid,size=50m"
                    },
                    "security_opt": ["no-new-privileges"],
                    "cap_drop": ["ALL"],
                    "cap_add": ["CHOWN", "DAC_OVERRIDE", "SETGID", "SETUID", "NET_RAW", "NET_BIND_SERVICE"],
                    "ulimits": [
                        docker.types.Ulimit(name="nofile", soft=1024, hard=2048),
                        docker.types.Ulimit(name="nproc", soft=512, hard=1024)
                    ],
                    "command": "tail -f /dev/null",  # Keep container running
                    "detach": True,
                    "stdin_open": True,
                    "tty": True
                }

                # Create container
                self.container = self.manager.docker.containers.run(**config)

                # Wait for container to be ready
                timeout = 60  # Increase wait timeout to 1 minute
                start = time.time()
                while time.time() - start < timeout:
                    self.container.reload()
                    if self.container.status == "running":
                        break
                    time.sleep(0.1)

                if self.container.status != "running":
                    raise RuntimeError(f"Container failed to start: {self.container.status}")

                self.state = AgentState.RUNNING
                self.creation_time = datetime.now()
                self.last_activity = datetime.now()

                # Start idle timer
                self._reset_idle_timer()

                print(f"[{self.agent_id}] Container ready")
                return True

            except Exception as e:
                print(f"[{self.agent_id}] Failed to create container: {e}")
                self.state = AgentState.ERROR
                self._cleanup_container()
                return False

    def execute_command(self, command: str, timeout: Optional[int] = None) -> Tuple[int, str, str]:
        """
        Execute a command in the container.
        Lazily creates container on first call.
        """
        # Ensure container exists (lazy initialization)
        if not self._ensure_container():
            return 1, "", f"Failed to initialize container for agent {self.agent_id}"

        with self._lock:
            try:
                # Update activity tracking
                self.last_activity = datetime.now()
                self.command_count += 1
                self._reset_idle_timer()

                # Build command with state restoration
                stateful_command = self.shell_state.build_command(command)

                # Execute command through bash
                bash_command = ["bash", "-c", stateful_command]
                result = self.container.exec_run(
                    bash_command,
                    stdout=True,
                    stderr=True,
                    stdin=False,
                    tty=False,
                    privileged=False,
                    user="agent",
                    detach=False,
                    stream=False,
                    environment={
                        "AGENT_ID": self.agent_id,
                        "HOME": "/home/agent",
                        "USER": "agent"
                    }
                )

                # Decode output
                output = result.output.decode('utf-8', errors='replace')

                # Update shell state from output and clean it
                cleaned_output = self.shell_state.update_state_from_output(output)

                # Return results with cleaned output
                return result.exit_code, cleaned_output, ""

            except Exception as e:
                return 1, "", str(e)

    def _reset_idle_timer(self):
        """Reset the idle timer for auto-cleanup."""
        with self._lock:
            # Cancel existing timer
            if self.cleanup_timer:
                self.cleanup_timer.cancel()

            # Start new timer
            if self.idle_timeout > 0:  # Skip timer if no timeout
                self.cleanup_timer = threading.Timer(
                    self.idle_timeout,
                    self._idle_cleanup
                )
                self.cleanup_timer.daemon = True
                self.cleanup_timer.start()

    def _idle_cleanup(self):
        """Called when idle timeout expires."""
        with self._lock:
            if self.state == AgentState.RUNNING:
                idle_time = (datetime.now() - self.last_activity).total_seconds()
                if idle_time >= self.idle_timeout:
                    print(f"[{self.agent_id}] Idle timeout reached, stopping container")
                    self.stop()

    def stop(self):
        """Stop the container but keep data."""
        with self._lock:
            if self.cleanup_timer:
                self.cleanup_timer.cancel()

            if self.container and self.state == AgentState.RUNNING:
                try:
                    self.state = AgentState.STOPPING
                    self.container.stop(timeout=30)  # Give more time for graceful shutdown
                    self.container.remove()
                    self.container = None
                    self.state = AgentState.STOPPED
                    print(f"[{self.agent_id}] Container stopped")
                except Exception as e:
                    print(f"[{self.agent_id}] Error stopping container: {e}")
                    self.state = AgentState.ERROR

    def _cleanup_container(self):
        """Remove container if it exists."""
        try:
            if self.container:
                self.container.remove(force=True)
                self.container = None
            else:
                # Try to remove by name
                container = self.manager.docker.containers.get(self.container_name)
                container.remove(force=True)
        except NotFound:
            pass
        except Exception as e:
            print(f"[{self.agent_id}] Cleanup error: {e}")

    def cleanup(self, remove_data: bool = False):
        """Complete cleanup including optional data removal."""
        self.stop()
        if remove_data and self.work_dir.exists():
            shutil.rmtree(self.work_dir)
            print(f"[{self.agent_id}] Data removed")

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        with self._lock:
            stats = {
                "agent_id": self.agent_id,
                "state": self.state.value,
                "command_count": self.command_count,
                "last_activity": self.last_activity.isoformat() if self.last_activity else None,
                "creation_time": self.creation_time.isoformat() if self.creation_time else None,
                "work_dir": str(self.work_dir),
                "container_name": self.container_name,
                "memory_limit": self.memory_limit,
                "cpu_limit": self.cpu_limit,
                "idle_timeout": self.idle_timeout
            }

            if self.creation_time:
                uptime = (datetime.now() - self.creation_time).total_seconds()
                stats["uptime_seconds"] = uptime

            if self.last_activity:
                idle_time = (datetime.now() - self.last_activity).total_seconds()
                stats["idle_seconds"] = idle_time

            return stats


class LazyAgentManager:
    """
    Manages lazy-initialized agent containers.
    Containers are only created when bash commands are executed.
    """

    def __init__(
        self,
        runtime_dir: str = "./evanai_runtime",
        image: str = "claude-agent:latest",
        default_idle_timeout: int = 0,  # 0 = no timeout
        max_agents: int = 100
    ):
        self.runtime_dir = Path(runtime_dir).absolute()
        self.working_dir_base = self.runtime_dir / "agent-working-directory"
        self.state_file = self.runtime_dir / "lazy-agent-state.json"
        self.image = image
        # No longer using isolated network - using host network
        self.use_host_network = True
        self.default_idle_timeout = default_idle_timeout
        self.max_agents = max_agents

        # Agent registry
        self.agents: Dict[str, LazyAgent] = {}
        self._lock = threading.RLock()

        # Initialize Docker client
        try:
            # Check for macOS Docker socket location
            import platform
            if platform.system() == 'Darwin':
                socket_path = os.path.expanduser('~/.docker/run/docker.sock')
                if os.path.exists(socket_path):
                    self.docker = docker.DockerClient(base_url=f'unix://{socket_path}')
                else:
                    self.docker = docker.from_env()
            else:
                self.docker = docker.from_env()
        except Exception as e:
            print(f"Error: Failed to connect to Docker: {e}")
            sys.exit(1)

        # Create directories
        self.working_dir_base.mkdir(parents=True, exist_ok=True)

        # No network setup needed for host network

        # Start cleanup thread
        self._start_cleanup_thread()

    # Network setup removed - using host network instead

    def _start_cleanup_thread(self):
        """Start background thread for periodic cleanup."""
        def cleanup_loop():
            while True:
                time.sleep(60)  # Check every minute
                self._cleanup_idle_agents()

        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()

    def _cleanup_idle_agents(self):
        """Clean up idle agents that have exceeded timeout."""
        with self._lock:
            for agent_id in list(self.agents.keys()):
                agent = self.agents[agent_id]
                if agent.state == AgentState.RUNNING:
                    idle_time = (datetime.now() - agent.last_activity).total_seconds()
                    # Only cleanup if idle_timeout is set (> 0) and exceeded
                    if agent.idle_timeout > 0 and idle_time > agent.idle_timeout:
                        print(f"[Manager] Cleaning up idle agent: {agent_id}")
                        agent.stop()

    def get_or_create_agent(
        self,
        conversation_id: str,
        memory_limit: str = "2g",
        cpu_limit: float = 2.0,
        idle_timeout: Optional[int] = None
    ) -> LazyAgent:
        """
        Get existing agent or create new one for a conversation.
        Agent is NOT started until first command execution.
        """
        with self._lock:
            # Use conversation ID as agent ID
            agent_id = conversation_id

            # Return existing agent if available
            if agent_id in self.agents:
                return self.agents[agent_id]

            # Check max agents limit
            if len(self.agents) >= self.max_agents:
                # Remove oldest idle agent
                self._evict_oldest_idle_agent()

            # Create new lazy agent (container NOT started yet)
            agent = LazyAgent(
                agent_id=agent_id,
                manager=self,
                memory_limit=memory_limit,
                cpu_limit=cpu_limit,
                idle_timeout=idle_timeout or self.default_idle_timeout
            )

            self.agents[agent_id] = agent
            print(f"[Manager] Registered lazy agent for conversation: {agent_id}")

            return agent

    def _evict_oldest_idle_agent(self):
        """Evict the oldest idle agent to make room."""
        oldest_agent = None
        oldest_time = datetime.now()

        for agent in self.agents.values():
            if agent.state in [AgentState.STOPPED, AgentState.NOT_CREATED]:
                if not oldest_agent or agent.last_activity < oldest_time:
                    oldest_agent = agent
                    oldest_time = agent.last_activity

        if oldest_agent:
            print(f"[Manager] Evicting agent: {oldest_agent.agent_id}")
            oldest_agent.cleanup(remove_data=True)
            del self.agents[oldest_agent.agent_id]

    def execute_bash(
        self,
        conversation_id: str,
        command: str,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute bash command for a conversation.
        Lazily creates container on first call.

        This is the main entry point for Claude agents.
        """
        # Get or create agent (lazy - no container yet)
        agent = self.get_or_create_agent(conversation_id)

        # Execute command (this triggers container creation if needed)
        exit_code, stdout, stderr = agent.execute_command(command, timeout)

        return {
            "success": exit_code == 0,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "conversation_id": conversation_id,
            "agent_id": agent.agent_id,
            "command_count": agent.command_count
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        with self._lock:
            stats = {
                "total_agents": len(self.agents),
                "agents_by_state": {},
                "total_commands": 0,
                "agents": []
            }

            for state in AgentState:
                stats["agents_by_state"][state.value] = 0

            for agent in self.agents.values():
                agent_stats = agent.get_stats()
                stats["agents"].append(agent_stats)
                stats["agents_by_state"][agent.state.value] += 1
                stats["total_commands"] += agent.command_count

            return stats

    def cleanup_conversation(self, conversation_id: str, remove_data: bool = False):
        """Clean up agent for a specific conversation."""
        with self._lock:
            if conversation_id in self.agents:
                agent = self.agents[conversation_id]
                agent.cleanup(remove_data=remove_data)
                del self.agents[conversation_id]
                print(f"[Manager] Cleaned up agent for conversation: {conversation_id}")

    def cleanup_all(self, remove_data: bool = False):
        """Clean up all agents."""
        with self._lock:
            for agent_id in list(self.agents.keys()):
                agent = self.agents[agent_id]
                agent.cleanup(remove_data=remove_data)
            self.agents.clear()
            print("[Manager] All agents cleaned up")


class ConversationAgent:
    """
    High-level interface for conversation-based agent management.
    Each conversation gets its own lazily-initialized container.
    """

    def __init__(
        self,
        conversation_id: Optional[str] = None,
        runtime_dir: str = "./evanai_runtime",
        idle_timeout: int = 0  # 0 = no timeout
    ):
        """
        Initialize agent for a conversation.

        Args:
            conversation_id: Unique conversation identifier (auto-generated if None)
            runtime_dir: Base directory for runtime data
            idle_timeout: Seconds before idle container stops
        """
        # Generate conversation ID if not provided
        if not conversation_id:
            conversation_id = f"conv-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"

        self.conversation_id = conversation_id
        self.manager = LazyAgentManager(
            runtime_dir=runtime_dir,
            default_idle_timeout=idle_timeout
        )

        print(f"Conversation agent initialized: {conversation_id}")
        print("Container will be created on first bash command")

    def bash(self, command: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute bash command in conversation's container.
        Container is created lazily on first call.

        This is the primary interface for Claude's bash tool.
        """
        result = self.manager.execute_bash(
            self.conversation_id,
            command,
            timeout
        )

        # Add convenience fields
        if result["success"]:
            result["output"] = result["stdout"]
        else:
            result["output"] = result["stderr"] or result["stdout"]

        return result

    def cleanup(self, remove_data: bool = True):
        """Clean up conversation's container and data."""
        self.manager.cleanup_conversation(
            self.conversation_id,
            remove_data=remove_data
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for this conversation."""
        all_stats = self.manager.get_stats()

        # Find this conversation's stats
        for agent_stats in all_stats["agents"]:
            if agent_stats["agent_id"] == self.conversation_id:
                return agent_stats

        return {"agent_id": self.conversation_id, "state": "not_created"}


# Example usage
if __name__ == "__main__":
    print("=== Lazy Agent Manager Demo ===\n")

    # Simulate a conversation
    conversation = ConversationAgent(conversation_id="demo-conv-001")

    print("1. Container not created yet (lazy)\n")
    print(f"   Stats: {conversation.get_stats()}\n")

    print("2. First bash command triggers container creation...")
    result = conversation.bash("echo 'Hello from lazy container!'")
    print(f"   Output: {result['output']}")
    print(f"   Container created: {result['command_count']} commands executed\n")

    print("3. Subsequent commands reuse container...")
    result = conversation.bash("pwd && ls -la /mnt")
    print(f"   Output:\n{result['output']}")
    print(f"   Commands executed: {result['command_count']}\n")

    print("4. Container stays alive between commands...")
    time.sleep(2)
    result = conversation.bash("echo 'Still here!' > /mnt/test.txt && cat /mnt/test.txt")
    print(f"   Output: {result['output']}")

    print("\n5. Stats after usage:")
    stats = conversation.get_stats()
    print(f"   State: {stats['state']}")
    print(f"   Commands: {stats['command_count']}")
    print(f"   Idle time: {stats.get('idle_seconds', 0):.1f} seconds")

    print("\n6. Cleanup...")
    conversation.cleanup()
    print("   Done!")

    print("\n=== Demo Complete ===")
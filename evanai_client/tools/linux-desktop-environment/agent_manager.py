#!/usr/bin/env python3
"""
Claude Agent Environment Manager

Manages isolated Docker containers for Claude-based agents.
Each agent gets its own working directory and isolated environment.
"""

import os
import sys
import json
import time
import uuid
import shutil
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import docker
from docker.errors import NotFound, APIError


class AgentManager:
    """Manages Claude agent containers with isolated environments."""

    def __init__(self, runtime_dir: str = "./evanai-runtime", image: str = "claude-agent:latest"):
        """
        Initialize the Agent Manager.

        Args:
            runtime_dir: Base directory for agent runtime data
            image: Docker image to use for agents
        """
        self.runtime_dir = Path(runtime_dir).absolute()
        self.working_dir_base = self.runtime_dir / "agent-working-directory"
        self.state_file = self.runtime_dir / "agent-state.json"
        self.image = image
        # No isolated network - using host network

        # Initialize Docker client
        try:
            self.docker = docker.from_env()
        except Exception as e:
            print(f"Error: Failed to connect to Docker: {e}")
            sys.exit(1)

        # Create directories
        self.working_dir_base.mkdir(parents=True, exist_ok=True)

        # Load or initialize state
        self.state = self._load_state()

        # No network setup needed for host network

    def _load_state(self) -> Dict[str, Any]:
        """Load agent state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"agents": {}}

    def _save_state(self):
        """Save agent state to file."""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2, default=str)

    # Network setup removed - using host network instead

    def _generate_agent_id(self) -> str:
        """Generate a unique agent ID."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        unique = str(uuid.uuid4())[:8]
        return f"{timestamp}-{unique}"

    def create_agent(
        self,
        agent_id: Optional[str] = None,
        memory_limit: str = "2g",
        cpu_limit: float = 2.0,
        environment: Optional[Dict[str, str]] = None,
        command: Optional[List[str]] = None,
        detached: bool = True,
        auto_remove: bool = False
    ) -> Dict[str, Any]:
        """
        Create and start a new agent container.

        Args:
            agent_id: Agent identifier (auto-generated if not provided)
            memory_limit: Memory limit for container
            cpu_limit: CPU limit for container
            environment: Additional environment variables
            command: Command to execute in container
            detached: Run container in background
            auto_remove: Remove container when it exits

        Returns:
            Agent information dictionary
        """
        # Generate or validate agent ID
        if not agent_id:
            agent_id = self._generate_agent_id()
        elif not agent_id.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Invalid agent ID. Use only alphanumeric, dash, and underscore.")

        # Check if agent already exists
        if agent_id in self.state["agents"]:
            raise ValueError(f"Agent {agent_id} already exists")

        # Create working directory
        work_dir = self.working_dir_base / agent_id
        work_dir.mkdir(parents=True, exist_ok=True)

        # Prepare environment variables
        env = {
            "AGENT_ID": agent_id,
            "AGENT_WORK_DIR": "/mnt"
        }
        if environment:
            env.update(environment)

        # Container configuration
        container_name = f"claude-agent-{agent_id}"

        # Security options
        security_opts = [
            "no-new-privileges",
        ]

        # Create container
        try:
            container = self.docker.containers.run(
                self.image,
                name=container_name,
                environment=env,
                volumes={
                    str(work_dir): {"bind": "/mnt", "mode": "rw"}
                },
                network_mode="host",  # Use host network for full access
                mem_limit=memory_limit,
                nano_cpus=int(cpu_limit * 1_000_000_000),  # Convert to nano CPUs
                read_only=True,  # Read-only root filesystem
                tmpfs={
                    "/tmp/agent": "rw,noexec,nosuid,size=100m",
                    "/home/agent/.cache": "rw,noexec,nosuid,size=50m"
                },
                security_opt=security_opts,
                cap_drop=["ALL"],
                cap_add=["CHOWN", "DAC_OVERRIDE", "SETGID", "SETUID", "NET_RAW", "NET_BIND_SERVICE"],
                ulimits=[
                    docker.types.Ulimit(name="nofile", soft=1024, hard=2048),
                    docker.types.Ulimit(name="nproc", soft=512, hard=1024)
                ],
                command=command,
                detach=detached,
                auto_remove=auto_remove,
                stdin_open=True,
                tty=True
            )

            # Store agent information
            agent_info = {
                "id": agent_id,
                "container_id": container.id[:12],
                "container_name": container_name,
                "work_dir": str(work_dir),
                "created": datetime.now().isoformat(),
                "status": "running",
                "memory_limit": memory_limit,
                "cpu_limit": cpu_limit,
                "auto_remove": auto_remove
            }

            self.state["agents"][agent_id] = agent_info
            self._save_state()

            return agent_info

        except Exception as e:
            # Clean up on failure
            if work_dir.exists() and not list(work_dir.iterdir()):
                work_dir.rmdir()
            raise Exception(f"Failed to create agent: {e}")

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents with their current status."""
        agents = []

        # Update status from Docker
        for agent_id, info in self.state["agents"].items():
            try:
                container = self.docker.containers.get(info["container_name"])
                info["status"] = container.status
                info["container_status"] = container.attrs["State"]
            except NotFound:
                info["status"] = "removed" if info.get("auto_remove") else "stopped"
            except Exception:
                info["status"] = "unknown"

            agents.append(info)

        # Save updated state
        self._save_state()

        return agents

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific agent."""
        if agent_id not in self.state["agents"]:
            return None

        info = self.state["agents"][agent_id].copy()

        # Get current status from Docker
        try:
            container = self.docker.containers.get(info["container_name"])
            info["status"] = container.status
            info["container_status"] = container.attrs["State"]
            info["stats"] = container.stats(stream=False)
        except NotFound:
            info["status"] = "removed" if info.get("auto_remove") else "stopped"
        except Exception:
            info["status"] = "unknown"

        return info

    def stop_agent(self, agent_id: str, timeout: int = 10) -> bool:
        """
        Stop an agent container.

        Args:
            agent_id: Agent identifier
            timeout: Seconds to wait before killing

        Returns:
            True if successful, False otherwise
        """
        if agent_id not in self.state["agents"]:
            return False

        info = self.state["agents"][agent_id]

        try:
            container = self.docker.containers.get(info["container_name"])
            container.stop(timeout=timeout)
            info["status"] = "stopped"
            self._save_state()
            return True
        except Exception:
            return False

    def remove_agent(self, agent_id: str, remove_data: bool = False) -> bool:
        """
        Remove an agent container and optionally its data.

        Args:
            agent_id: Agent identifier
            remove_data: Also remove agent's working directory

        Returns:
            True if successful, False otherwise
        """
        if agent_id not in self.state["agents"]:
            return False

        info = self.state["agents"][agent_id]

        # Remove container
        try:
            container = self.docker.containers.get(info["container_name"])
            container.remove(force=True)
        except NotFound:
            pass  # Already removed
        except Exception:
            return False

        # Remove working directory if requested
        if remove_data:
            work_dir = Path(info["work_dir"])
            if work_dir.exists():
                shutil.rmtree(work_dir)

        # Remove from state
        del self.state["agents"][agent_id]
        self._save_state()

        return True

    def execute_command(
        self,
        agent_id: str,
        command: str,
        timeout: Optional[int] = None
    ) -> tuple[int, str, str]:
        """
        Execute a command in an agent's container.

        Args:
            agent_id: Agent identifier
            command: Command to execute
            timeout: Command timeout in seconds

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        if agent_id not in self.state["agents"]:
            raise ValueError(f"Agent {agent_id} not found")

        info = self.state["agents"][agent_id]

        try:
            container = self.docker.containers.get(info["container_name"])

            if container.status != "running":
                raise RuntimeError(f"Agent {agent_id} is not running")

            # Execute command
            result = container.exec_run(
                command,
                stdout=True,
                stderr=True,
                stdin=False,
                tty=False,
                privileged=False,
                user="agent",
                detach=False,
                stream=False,
                environment={
                    "AGENT_ID": agent_id,
                    "AGENT_WORK_DIR": "/mnt"
                }
            )

            # Decode output
            output = result.output.decode('utf-8', errors='replace')

            # Try to split stdout and stderr (not always reliable)
            # For better separation, would need to use exec_run with stream=True
            stdout = output
            stderr = ""

            return result.exit_code, stdout, stderr

        except Exception as e:
            return 1, "", str(e)

    def get_logs(self, agent_id: str, tail: int = 100) -> str:
        """Get logs from an agent container."""
        if agent_id not in self.state["agents"]:
            return ""

        info = self.state["agents"][agent_id]

        try:
            container = self.docker.containers.get(info["container_name"])
            return container.logs(tail=tail).decode('utf-8', errors='replace')
        except Exception:
            return ""

    def cleanup_stopped(self) -> int:
        """Remove all stopped agents. Returns count of removed agents."""
        removed = 0

        for agent_id in list(self.state["agents"].keys()):
            info = self.state["agents"][agent_id]

            try:
                container = self.docker.containers.get(info["container_name"])
                if container.status == "exited":
                    if self.remove_agent(agent_id):
                        removed += 1
            except NotFound:
                # Container doesn't exist, remove from state
                del self.state["agents"][agent_id]
                removed += 1
            except Exception:
                pass

        self._save_state()
        return removed


def main():
    """CLI interface for the Agent Manager."""
    parser = argparse.ArgumentParser(
        description="Manage Claude agent Docker environments"
    )
    parser.add_argument(
        "--runtime-dir",
        default="./evanai-runtime",
        help="Base directory for runtime data"
    )
    parser.add_argument(
        "--image",
        default="claude-agent:latest",
        help="Docker image for agents"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new agent")
    create_parser.add_argument("--id", help="Agent ID (auto-generated if not provided)")
    create_parser.add_argument("--memory", default="2g", help="Memory limit")
    create_parser.add_argument("--cpu", type=float, default=2.0, help="CPU limit")
    create_parser.add_argument("--rm", action="store_true", help="Auto-remove on exit")
    create_parser.add_argument("--cmd", nargs="+", help="Command to execute")

    # List command
    subparsers.add_parser("list", help="List all agents")

    # Info command
    info_parser = subparsers.add_parser("info", help="Get agent information")
    info_parser.add_argument("id", help="Agent ID")

    # Execute command
    exec_parser = subparsers.add_parser("exec", help="Execute command in agent")
    exec_parser.add_argument("id", help="Agent ID")
    exec_parser.add_argument("command", nargs="+", help="Command to execute")

    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop an agent")
    stop_parser.add_argument("id", help="Agent ID")

    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove an agent")
    remove_parser.add_argument("id", help="Agent ID")
    remove_parser.add_argument("--data", action="store_true", help="Also remove data")

    # Logs command
    logs_parser = subparsers.add_parser("logs", help="Get agent logs")
    logs_parser.add_argument("id", help="Agent ID")
    logs_parser.add_argument("--tail", type=int, default=100, help="Number of lines")

    # Cleanup command
    subparsers.add_parser("cleanup", help="Remove stopped agents")

    args = parser.parse_args()

    # Initialize manager
    manager = AgentManager(args.runtime_dir, args.image)

    # Execute command
    if args.command == "create":
        try:
            info = manager.create_agent(
                agent_id=args.id,
                memory_limit=args.memory,
                cpu_limit=args.cpu,
                command=args.cmd,
                auto_remove=args.rm
            )
            print(f"Created agent: {info['id']}")
            print(f"Container: {info['container_name']}")
            print(f"Working directory: {info['work_dir']}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.command == "list":
        agents = manager.list_agents()
        if not agents:
            print("No agents found")
        else:
            print(f"{'ID':<30} {'Status':<10} {'Created':<20}")
            print("-" * 60)
            for agent in agents:
                created = agent['created'][:19]  # Trim to seconds
                print(f"{agent['id']:<30} {agent['status']:<10} {created:<20}")

    elif args.command == "info":
        info = manager.get_agent(args.id)
        if not info:
            print(f"Agent {args.id} not found")
        else:
            print(json.dumps(info, indent=2, default=str))

    elif args.command == "exec":
        try:
            exit_code, stdout, stderr = manager.execute_command(
                args.id,
                " ".join(args.command)
            )
            if stdout:
                print(stdout, end="")
            if stderr:
                print(stderr, end="", file=sys.stderr)
            sys.exit(exit_code)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.command == "stop":
        if manager.stop_agent(args.id):
            print(f"Stopped agent {args.id}")
        else:
            print(f"Failed to stop agent {args.id}")
            sys.exit(1)

    elif args.command == "remove":
        if manager.remove_agent(args.id, remove_data=args.data):
            print(f"Removed agent {args.id}")
        else:
            print(f"Failed to remove agent {args.id}")
            sys.exit(1)

    elif args.command == "logs":
        logs = manager.get_logs(args.id, tail=args.tail)
        if logs:
            print(logs, end="")
        else:
            print(f"No logs found for agent {args.id}")

    elif args.command == "cleanup":
        count = manager.cleanup_stopped()
        print(f"Removed {count} stopped agent(s)")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
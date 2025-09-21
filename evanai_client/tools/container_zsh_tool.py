"""
ZSH tool for executing commands in isolated Linux containers.

This tool provides Claude agents with ZSH command execution capabilities
in isolated, per-conversation Docker containers, supporting PowerPoint
creation workflows and other document processing tasks.
"""

import os
import sys
import json
import time
import base64
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Add linux_desktop_environment to path for imports
tool_dir = Path(__file__).parent
linux_env_dir = tool_dir / "linux_desktop_environment"
if str(linux_env_dir) not in sys.path:
    sys.path.insert(0, str(linux_env_dir))

from ..tool_system import BaseToolSetProvider, Tool, Parameter, ParameterType

# Import the lazy container manager
try:
    from .linux_desktop_environment.lazy_agent_manager import LazyAgentManager, ConversationAgent
except ImportError:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "lazy_agent_manager",
        linux_env_dir / "lazy_agent_manager.py"
    )
    lazy_agent_manager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lazy_agent_manager)
    LazyAgentManager = lazy_agent_manager.LazyAgentManager
    ConversationAgent = lazy_agent_manager.ConversationAgent


class ContainerZshToolProvider(BaseToolSetProvider):
    """
    Provides ZSH command execution in isolated Docker containers.
    
    Specifically designed for PowerPoint creation and document processing
    workflows that require ZSH shell features.
    """

    def __init__(
        self,
        websocket_handler=None,
        runtime_dir: Optional[str] = None,
        idle_timeout: int = 0,  # No timeout by default
        memory_limit: str = "4g",  # More memory for document processing
        cpu_limit: float = 4.0,
        image: str = "claude-agent:latest",
        auto_cleanup: bool = True,
        enable_logging: bool = False
    ):
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
        
        # Global container manager
        self.manager = None
        
        # Stats
        self.total_commands = 0
        self.total_containers_created = 0

    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """Initialize the ZSH tools."""
        tools = [
            Tool(
                id="zsh",
                name="zsh",
                description=(
                    "Execute ZSH commands in a sandboxed Linux container environment. "
                    "This tool runs in an isolated Docker container, not on the host machine. "
                    "Each conversation has its own persistent container with: "
                    "- Ubuntu 24.04 with ZSH shell installed \n"
                    "- PowerPoint creation tools (pptxgenjs, markitdown, python-pptx) \n"
                    "- Document processing tools (pandoc, libreoffice, imagemagick) \n"
                    "- Python 3.12 with data science and document libraries \n"
                    "- Node.js 18.x with document processing packages \n"
                    "- Skills directory at /mnt/skills with PPTX processing guides \n"
                    "- Working directory at /mnt (writable) \n"
                    "Perfect for PowerPoint creation workflows and document processing."
                ),
                parameters={
                    "command": Parameter(
                        name="command",
                        type=ParameterType.STRING,
                        description="ZSH command to execute in the container",
                        required=True
                    ),
                    "timeout": Parameter(
                        name="timeout",
                        type=ParameterType.INTEGER,
                        description="Command timeout in seconds (default: 300 for document operations)",
                        required=False,
                        default=300
                    )
                }
            ),
            Tool(
                id="container_status",
                name="container_status",
                description="Get the status of the current container environment",
                parameters={}
            ),
            Tool(
                id="container_reset",
                name="container_reset",
                description="Reset the container environment (creates new container)",
                parameters={
                    "preserve_files": Parameter(
                        name="preserve_files",
                        type=ParameterType.BOOLEAN,
                        description="Preserve /mnt directory contents when resetting",
                        required=False,
                        default=True
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
            if self.enable_logging:
                print(f"[ContainerZshTool] Initialized with runtime dir: {self.runtime_dir}")
        
        # Global state
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
        """Execute a ZSH tool command."""
        
        # Get or generate conversation ID
        conversation_id = per_conversation_state.get('_conversation_id')
        if not conversation_id:
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
            if tool_id == "zsh":
                return self._execute_zsh(
                    manager,
                    conversation_id,
                    tool_parameters,
                    per_conversation_state,
                    global_state
                )
            elif tool_id == "container_status":
                return self._get_status(
                    manager,
                    conversation_id,
                    per_conversation_state
                )
            elif tool_id == "container_reset":
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
    
    def _execute_zsh(
        self,
        manager: LazyAgentManager,
        conversation_id: str,
        parameters: Dict[str, Any],
        conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Execute a ZSH command in the container."""
        
        command = parameters.get("command")
        if not command:
            return None, "Command is required"
        
        timeout = parameters.get("timeout", 300)  # 5 minutes default for doc ops
        start_time = time.time()
        
        # Check if this is the first command
        is_first = not conversation_state["container_created"]
        
        try:
            # Get or create agent
            agent = manager.get_or_create_agent(
                conversation_id=conversation_id,
                memory_limit=self.memory_limit,
                cpu_limit=self.cpu_limit,
                idle_timeout=self.idle_timeout
            )

            # Execute command using ZSH
            # Create a temporary script to avoid shell escaping issues with heredocs
            # This preserves newlines and special characters properly

            # Encode the command to preserve all special characters and newlines
            encoded_cmd = base64.b64encode(command.encode('utf-8')).decode('ascii')

            # Use a wrapper that decodes and executes via zsh
            # This avoids JSON escaping issues with heredocs and multiline commands
            wrapper_cmd = f"echo '{encoded_cmd}' | base64 -d | zsh"

            exit_code, stdout, stderr = agent.execute_command(wrapper_cmd, timeout)

            execution_time = time.time() - start_time

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Container execution failed: {str(e)}"

            if self.enable_logging:
                print(f"[ContainerZshTool][{conversation_id}] Error: {error_msg}")

            # Return error result
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": error_msg,
                "success": False,
                "command": command,
                "shell": "zsh",
                "execution_time": execution_time,
                "conversation_id": conversation_id,
                "command_number": conversation_state["command_count"] + 1,
                "container_was_created": False,
                "output": error_msg,
                "error": "container_failure"
            }, None
        
        # Update state
        conversation_state["command_count"] += 1
        conversation_state["last_command_time"] = datetime.now().isoformat()
        
        if is_first:
            conversation_state["container_created"] = True
            global_state["total_containers"] += 1
            self.total_containers_created += 1
            
            if self.enable_logging:
                print(f"[ContainerZshTool][{conversation_id}] Container created")
        
        global_state["total_commands"] += 1
        self.total_commands += 1
        
        # Prepare result
        result = {
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "success": exit_code == 0,
            "command": command,
            "shell": "zsh",
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

        # Check for newly created PowerPoint files and other downloadable files
        try:
            download_info = self._check_for_downloadable_files(agent, conversation_id)
            if download_info:
                result["downloadable_files"] = download_info
        except Exception as e:
            if self.enable_logging:
                print(f"[ContainerZshTool][{conversation_id}] Error checking for files: {e}")

        return result, None
    
    def _get_status(
        self,
        manager: LazyAgentManager,
        conversation_id: str,
        conversation_state: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Get container status."""
        
        agent = manager.get_agent(conversation_id)
        
        if not agent:
            status = {
                "container_exists": False,
                "state": "not_created",
                "conversation_id": conversation_id,
                "commands_executed": conversation_state.get("command_count", 0)
            }
        else:
            status = {
                "container_exists": True,
                "state": agent.state.value,
                "conversation_id": conversation_id,
                "container_id": agent.container.id[:12] if agent.container else None,
                "commands_executed": conversation_state.get("command_count", 0),
                "last_command_time": conversation_state.get("last_command_time"),
                "working_directory": conversation_state.get("working_directory", "/mnt")
            }
        
        return status, None
    
    def _reset_environment(
        self,
        manager: LazyAgentManager,
        conversation_id: str,
        parameters: Dict[str, Any],
        conversation_state: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Reset the container environment."""
        
        preserve_files = parameters.get("preserve_files", True)
        
        # Stop existing container
        agent = manager.get_agent(conversation_id)
        if agent:
            agent.stop()
            manager.remove_agent(conversation_id)
        
        # Reset conversation state
        conversation_state["container_created"] = False
        conversation_state["command_count"] = 0
        conversation_state["last_command_time"] = None
        conversation_state["working_directory"] = "/mnt"
        
        result = {
            "success": True,
            "message": "Container environment reset. New container will be created on next command.",
            "preserve_files": preserve_files
        }
        
        return result, None

    def _check_for_downloadable_files(self, agent, conversation_id: str):
        """Check for downloadable files created in the container and provide download info."""
        try:
            # Get the container working directory from the agent
            work_dir = agent.work_dir

            if not work_dir.exists():
                return None

            downloadable_extensions = {'.pptx', '.pdf', '.docx', '.xlsx', '.txt', '.png', '.jpg', '.jpeg'}
            files_found = []

            # Scan for downloadable files
            for file_path in work_dir.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in downloadable_extensions:
                    relative_path = file_path.relative_to(work_dir)
                    file_info = {
                        'name': file_path.name,
                        'path': str(relative_path),
                        'size': file_path.stat().st_size,
                        'extension': file_path.suffix.lower(),
                        'download_url': f'/api/files/download/{conversation_id}/{relative_path}'
                    }
                    files_found.append(file_info)

            if files_found:
                # Sort by most recent first
                files_found.sort(key=lambda x: work_dir / x['path'], reverse=True)

                # Focus on PowerPoint files
                pptx_files = [f for f in files_found if f['extension'] == '.pptx']

                download_info = {
                    'total_files': len(files_found),
                    'powerpoint_files': pptx_files,
                    'all_files': files_found[:10],  # Limit to 10 most recent
                    'file_list_url': f'/api/files/container/{conversation_id}'
                }

                if pptx_files:
                    download_info['message'] = f"✅ Created {len(pptx_files)} PowerPoint file(s). Click the download links to access them."

                return download_info

            return None

        except Exception as e:
            if self.enable_logging:
                print(f"[ContainerZshTool] Error scanning files: {e}")
            return None

    def get_name(self) -> str:
        """Get the name of this tool provider."""
        return "container_zsh_tools"
    
    def get_description(self) -> str:
        """Get the description of this tool provider."""
        return "ZSH command execution in Docker containers with PowerPoint creation tools"
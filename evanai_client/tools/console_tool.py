import subprocess
import os
import signal
import threading
import queue
import time
from typing import Dict, List, Any, Optional, Tuple
from ..tool_system import BaseToolSetProvider, Tool, Parameter, ParameterType


class ConsoleToolProvider(BaseToolSetProvider):
    """Console tool provider for executing shell commands in a zsh environment."""

    def __init__(self, websocket_handler=None):
        super().__init__(websocket_handler)
        self.shells = {}
        self.output_queues = {}

    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
        tools = [
            Tool(
                id="execute_command",
                name="Execute Command",
                description="Execute a shell command in a zsh shell environment",
                parameters={
                    "command": Parameter(
                        name="command",
                        type=ParameterType.STRING,
                        description="The shell command to execute",
                        required=True
                    ),
                    "timeout": Parameter(
                        name="timeout",
                        type=ParameterType.NUMBER,
                        description="Command timeout in seconds (default: 5)",
                        required=False,
                        default=5
                    ),
                    "working_directory": Parameter(
                        name="working_directory",
                        type=ParameterType.STRING,
                        description="Working directory for command execution",
                        required=False
                    )
                }
            ),
            Tool(
                id="start_interactive_session",
                name="Start Interactive Session",
                description="Start a persistent interactive zsh shell session",
                parameters={
                    "session_id": Parameter(
                        name="session_id",
                        type=ParameterType.STRING,
                        description="Unique identifier for the shell session",
                        required=True
                    ),
                    "working_directory": Parameter(
                        name="working_directory",
                        type=ParameterType.STRING,
                        description="Initial working directory for the session",
                        required=False
                    )
                }
            ),
            Tool(
                id="send_to_session",
                name="Send to Session",
                description="Send a command to an active shell session",
                parameters={
                    "session_id": Parameter(
                        name="session_id",
                        type=ParameterType.STRING,
                        description="ID of the shell session",
                        required=True
                    ),
                    "command": Parameter(
                        name="command",
                        type=ParameterType.STRING,
                        description="Command to send to the session",
                        required=True
                    )
                }
            ),
            Tool(
                id="read_session_output",
                name="Read Session Output",
                description="Read buffered output from an active shell session",
                parameters={
                    "session_id": Parameter(
                        name="session_id",
                        type=ParameterType.STRING,
                        description="ID of the shell session",
                        required=True
                    ),
                    "timeout": Parameter(
                        name="timeout",
                        type=ParameterType.NUMBER,
                        description="Max time to wait for output in seconds",
                        required=False,
                        default=1
                    )
                }
            ),
            Tool(
                id="close_session",
                name="Close Session",
                description="Close an active shell session",
                parameters={
                    "session_id": Parameter(
                        name="session_id",
                        type=ParameterType.STRING,
                        description="ID of the shell session to close",
                        required=True
                    )
                }
            ),
            Tool(
                id="list_sessions",
                name="List Sessions",
                description="List all active shell sessions",
                parameters={}
            )
        ]

        global_state = {
            "default_timeout": 30,
            "max_sessions": 10
        }

        per_conversation_state = {}

        return tools, global_state, per_conversation_state

    def call_tool(
        self,
        tool_id: str,
        tool_parameters: Dict[str, Any],
        per_conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:

        try:
            if tool_id == "execute_command":
                return self._execute_command(tool_parameters, per_conversation_state)

            elif tool_id == "start_interactive_session":
                return self._start_session(tool_parameters, per_conversation_state, global_state)

            elif tool_id == "send_to_session":
                return self._send_to_session(tool_parameters, per_conversation_state)

            elif tool_id == "read_session_output":
                return self._read_session_output(tool_parameters, per_conversation_state)

            elif tool_id == "close_session":
                return self._close_session(tool_parameters, per_conversation_state)

            elif tool_id == "list_sessions":
                return self._list_sessions(per_conversation_state)

            else:
                return None, f"Unknown tool: {tool_id}"

        except Exception as e:
            return None, f"Error executing tool {tool_id}: {str(e)}"

    def _execute_command(
        self,
        parameters: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """Execute a single command and return its output."""
        command = parameters["command"]
        timeout = parameters.get("timeout", 30)
        working_dir = parameters.get("working_directory") or state.get("_working_directory")

        try:
            # Use zsh explicitly
            shell_command = ["zsh", "-c", command]

            result = subprocess.run(
                shell_command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_dir,
                env=os.environ.copy()
            )

            output = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "command": command
            }

            return output, None

        except subprocess.TimeoutExpired:
            return None, f"Command timed out after {timeout} seconds"
        except Exception as e:
            return None, f"Failed to execute command: {str(e)}"

    def _start_session(
        self,
        parameters: Dict[str, Any],
        state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """Start a new interactive shell session."""
        session_id = parameters["session_id"]
        working_dir = parameters.get("working_directory") or state.get("_working_directory")

        # Check if session already exists
        if "sessions" not in state:
            state["sessions"] = {}

        if session_id in state["sessions"]:
            return None, f"Session {session_id} already exists"

        # Check max sessions limit
        if len(state["sessions"]) >= global_state.get("max_sessions", 10):
            return None, f"Maximum number of sessions reached"

        try:
            # Start zsh process
            process = subprocess.Popen(
                ["zsh", "-i"],  # -i for interactive shell
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=working_dir,
                env=os.environ.copy(),
                bufsize=0  # Unbuffered
            )

            # Create output queue and reader thread
            output_queue = queue.Queue()

            def read_output(proc, q):
                """Read output from process and put in queue."""
                while True:
                    try:
                        line = proc.stdout.readline()
                        if line:
                            q.put(("stdout", line))
                        else:
                            if proc.poll() is not None:
                                break
                    except:
                        break

            def read_error(proc, q):
                """Read error output from process and put in queue."""
                while True:
                    try:
                        line = proc.stderr.readline()
                        if line:
                            q.put(("stderr", line))
                        else:
                            if proc.poll() is not None:
                                break
                    except:
                        break

            # Start reader threads
            stdout_thread = threading.Thread(target=read_output, args=(process, output_queue))
            stderr_thread = threading.Thread(target=read_error, args=(process, output_queue))
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()

            # Store session info
            state["sessions"][session_id] = {
                "process": process,
                "output_queue": output_queue,
                "stdout_thread": stdout_thread,
                "stderr_thread": stderr_thread,
                "working_directory": working_dir,
                "created_at": time.time()
            }

            return {
                "session_id": session_id,
                "status": "started",
                "pid": process.pid,
                "working_directory": working_dir
            }, None

        except Exception as e:
            return None, f"Failed to start session: {str(e)}"

    def _send_to_session(
        self,
        parameters: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """Send a command to an active session."""
        session_id = parameters["session_id"]
        command = parameters["command"]

        if "sessions" not in state or session_id not in state["sessions"]:
            return None, f"Session {session_id} not found"

        session = state["sessions"][session_id]
        process = session["process"]

        if process.poll() is not None:
            return None, f"Session {session_id} has terminated"

        try:
            # Send command to stdin
            process.stdin.write(command + "\n")
            process.stdin.flush()

            return {
                "session_id": session_id,
                "command_sent": command,
                "status": "sent"
            }, None

        except Exception as e:
            return None, f"Failed to send command: {str(e)}"

    def _read_session_output(
        self,
        parameters: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """Read buffered output from a session."""
        session_id = parameters["session_id"]
        timeout = parameters.get("timeout", 1)

        if "sessions" not in state or session_id not in state["sessions"]:
            return None, f"Session {session_id} not found"

        session = state["sessions"][session_id]
        output_queue = session["output_queue"]

        stdout_lines = []
        stderr_lines = []
        deadline = time.time() + timeout

        while time.time() < deadline:
            try:
                remaining = deadline - time.time()
                if remaining <= 0:
                    break

                stream_type, line = output_queue.get(timeout=min(0.1, remaining))

                if stream_type == "stdout":
                    stdout_lines.append(line)
                elif stream_type == "stderr":
                    stderr_lines.append(line)

            except queue.Empty:
                # Check if there's more output coming
                if not stdout_lines and not stderr_lines:
                    time.sleep(0.05)
                else:
                    break

        return {
            "session_id": session_id,
            "stdout": "".join(stdout_lines),
            "stderr": "".join(stderr_lines),
            "has_more": not output_queue.empty()
        }, None

    def _close_session(
        self,
        parameters: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """Close an active session."""
        session_id = parameters["session_id"]

        if "sessions" not in state or session_id not in state["sessions"]:
            return None, f"Session {session_id} not found"

        session = state["sessions"][session_id]
        process = session["process"]

        try:
            # Try graceful shutdown first
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if necessary
                    process.kill()
                    process.wait()

            # Clean up session
            del state["sessions"][session_id]

            return {
                "session_id": session_id,
                "status": "closed"
            }, None

        except Exception as e:
            return None, f"Failed to close session: {str(e)}"

    def _list_sessions(
        self,
        state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """List all active sessions."""
        if "sessions" not in state:
            return {"sessions": []}, None

        sessions_info = []
        for session_id, session in state["sessions"].items():
            process = session["process"]
            sessions_info.append({
                "session_id": session_id,
                "pid": process.pid,
                "active": process.poll() is None,
                "working_directory": session.get("working_directory"),
                "created_at": session.get("created_at")
            })

        return {"sessions": sessions_info}, None
11
"""ZSH tool for executing commands in a persistent zsh shell on macOS."""

import subprocess
import os
import threading
import queue
import time
import re
from typing import Dict, List, Any, Optional, Tuple
from ..tool_system import BaseToolSetProvider, Tool, Parameter, ParameterType


class ZshToolProvider(BaseToolSetProvider):
    """ZSH tool provider for executing commands in a persistent zsh environment."""

    def __init__(self, websocket_handler=None):
        super().__init__(websocket_handler)

    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """Initialize the zsh tool."""
        tools = [
            Tool(
                id="zsh",
                name="Execute ZSH Command",
                display_name="Execute Terminal Command",
                description="Execute a command in a zsh shell on the user's actual macOS system. Starts in the user's home directory. Has full access to the user's file system and macOS environment.",
                parameters={
                    "command": Parameter(
                        name="command",
                        type=ParameterType.STRING,
                        description="The zsh command to execute",
                        required=True
                    ),
                    "timeout": Parameter(
                        name="timeout",
                        type=ParameterType.NUMBER,
                        description="Command timeout in seconds",
                        required=False,
                        default=3.0
                    )
                }
            )
        ]

        # Global state for managing sessions
        global_state = {}

        # Per-conversation state for persistent shells
        per_conversation_state = {}

        return tools, global_state, per_conversation_state

    def call_tool(
        self,
        tool_id: str,
        tool_parameters: Dict[str, Any],
        per_conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """Execute tool calls."""
        try:
            if tool_id == "zsh":
                return self._execute_zsh(tool_parameters, per_conversation_state)
            else:
                return None, f"Unknown tool: {tool_id}"
        except Exception as e:
            return None, f"Error executing tool {tool_id}: {str(e)}"

    def _get_or_create_session(self, state: Dict[str, Any]) -> subprocess.Popen:
        """Get existing zsh session or create a new one."""

        # Check if we have an existing session
        if "zsh_process" in state and state["zsh_process"].poll() is None:
            return state["zsh_process"]

        # Create new zsh session
        # Start zsh with interactive mode and proper environment
        env = os.environ.copy()
        env['SHELL'] = '/bin/zsh'
        # Force terminal type for better output
        env['TERM'] = 'dumb'

        # Start in user's home directory, not agent's working directory
        home_dir = os.path.expanduser("~")

        process = subprocess.Popen(
            ['/bin/zsh', '-i', '-s'],  # Interactive zsh with stdin
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=home_dir,  # Start in user's home directory
            bufsize=0,  # Unbuffered
            universal_newlines=True
        )

        # Store process in state
        state["zsh_process"] = process

        # Create output queue and reader threads
        output_queue = queue.Queue()
        state["output_queue"] = output_queue

        def read_stdout(proc, q):
            """Read stdout from process."""
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

        def read_stderr(proc, q):
            """Read stderr from process."""
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
        stdout_thread = threading.Thread(target=read_stdout, args=(process, output_queue), daemon=True)
        stderr_thread = threading.Thread(target=read_stderr, args=(process, output_queue), daemon=True)

        stdout_thread.start()
        stderr_thread.start()

        state["stdout_thread"] = stdout_thread
        state["stderr_thread"] = stderr_thread

        # Clear any initial output (like shell prompts)
        time.sleep(0.2)
        while not output_queue.empty():
            try:
                output_queue.get_nowait()
            except queue.Empty:
                break

        return process

    def _execute_zsh(
        self,
        parameters: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """Execute a command in the persistent zsh session."""

        command = parameters["command"]
        timeout = parameters.get("timeout", 30.0)  # Default 30 second command timeout

        # Use simple mode for now until persistent session issue is fixed
        # TODO: Fix persistent session output collection
        return self._execute_zsh_simple(command, timeout)

        # Get or create zsh session
        process = self._get_or_create_session(state)
        output_queue = state.get("output_queue")

        if process.poll() is not None:
            # Process died, recreate it
            process = self._get_or_create_session(state)
            output_queue = state.get("output_queue")

        try:
            # Send command to zsh with a unique marker to detect when command completes
            marker = f"__DONE_{time.time()}__"
            full_command = f"{command}; echo '{marker}'"

            process.stdin.write(full_command + '\n')
            process.stdin.flush()

            # Collect output with timeout
            stdout_lines = []
            stderr_lines = []
            start_time = time.time()

            # Wait a bit longer for command to start processing
            time.sleep(0.2)

            # Read output until we see the marker or timeout
            found_marker = False
            while True:
                elapsed = time.time() - start_time
                # Only check timeout if timeout > 0 (0 = no timeout)
                if timeout > 0 and elapsed > timeout:
                    break

                try:
                    # Try to get output with a short timeout
                    stream_type, line = output_queue.get(timeout=0.2)

                    if stream_type == "stdout":
                        # Check if this line contains our marker
                        if marker in line:
                            # Remove the marker from output
                            line = line.replace(marker, "").strip()
                            if line:
                                stdout_lines.append(line)
                            found_marker = True
                            break
                        stdout_lines.append(line)
                    else:
                        stderr_lines.append(line)

                except queue.Empty:
                    # If we've been waiting for more than half the timeout with no output, break
                    # Only apply if timeout > 0
                    if timeout > 0 and elapsed > timeout / 2 and not stdout_lines and not stderr_lines:
                        break
                    continue

            # Combine output
            stdout = ''.join(stdout_lines)
            stderr = ''.join(stderr_lines)

            # Clean up prompts and control characters
            stdout = self._clean_output(stdout)
            # Clean stderr more aggressively - usually just contains prompts
            stderr = self._clean_stderr(stderr)

            result = {
                "stdout": stdout,
                "stderr": stderr,
                "command": command,
                "session_active": process.poll() is None
            }

            return result, None

        except Exception as e:
            return None, f"Error executing command: {str(e)}"

    def _execute_zsh_simple(self, command: str, timeout: float) -> Tuple[Any, Optional[str]]:
        """Simple non-persistent command execution as fallback."""
        try:
            # Run command directly with subprocess
            # If timeout is 0, don't set timeout (run indefinitely)
            kwargs = {
                'capture_output': True,
                'text': True,
                'cwd': os.path.expanduser("~")
            }
            if timeout > 0:
                kwargs['timeout'] = timeout

            result = subprocess.run(
                ['/bin/zsh', '-c', command],
                **kwargs
            )

            return {
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "command": command,
                "session_active": False  # No persistent session in simple mode
            }, None

        except subprocess.TimeoutExpired:
            return None, f"Command timed out after {timeout} seconds"
        except Exception as e:
            return None, f"Error executing command: {str(e)}"

    def _clean_output(self, output: str) -> str:
        """Clean shell output by removing prompts and control characters."""
        if not output:
            return ""

        lines = output.split('\n')
        cleaned_lines = []

        for line in lines:
            # Remove ANSI escape codes
            line = re.sub(r'\x1b\[[0-9;]*[mGKHJ]', '', line)

            # Skip lines that are ONLY a prompt character (not content ending with %)
            if line.strip() in ['%', '$', '#']:
                continue

            # Skip lines that look like full prompts (username@hostname dir %)
            if '@' in line and line.strip().endswith('%') and len(line.split()) <= 3:
                continue

            # Keep the line if it has actual content
            cleaned_lines.append(line.rstrip())

        # Remove leading/trailing empty lines
        while cleaned_lines and not cleaned_lines[0]:
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1]:
            cleaned_lines.pop()

        return '\n'.join(cleaned_lines)

    def _clean_stderr(self, stderr: str) -> str:
        """Clean stderr output - usually just contains prompts we want to remove."""
        if not stderr:
            return ""

        lines = stderr.split('\n')
        cleaned_lines = []

        for line in lines:
            # Remove ANSI escape codes
            line = re.sub(r'\x1b\[[0-9;]*[mGKHJ]', '', line)

            # Skip prompt lines (username@hostname path %)
            if '@' in line and '%' in line:
                continue

            # Skip lines that are just prompt characters
            line_stripped = line.strip()
            if line_stripped in ['%', '$', '#', '%%']:
                continue

            # Skip empty lines
            if not line_stripped:
                continue

            # Keep actual error messages
            cleaned_lines.append(line.rstrip())

        return '\n'.join(cleaned_lines)

    def cleanup_conversation(self, conversation_id: str, state: Dict[str, Any]):
        """Clean up resources when conversation ends."""
        if "zsh_process" in state:
            process = state["zsh_process"]
            if process.poll() is None:
                try:
                    process.terminate()
                    time.sleep(0.5)
                    if process.poll() is None:
                        process.kill()
                except:
                    pass
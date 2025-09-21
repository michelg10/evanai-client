"""
Claude Code Analyzer Tool

Runs Claude Code CLI to analyze and understand codebases.
Generates extensive technical reports about projects.
"""

import subprocess
import os
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

from ..tool_system import BaseToolSetProvider, Tool, Parameter, ParameterType


class ClaudeCodeAnalyzerProvider(BaseToolSetProvider):
    """Provider for Claude Code analysis tools."""

    def __init__(self, websocket_handler=None):
        super().__init__(websocket_handler)
        # Check if claude CLI is available
        self.claude_available = self._check_claude_cli()

    def _check_claude_cli(self) -> bool:
        """Check if claude CLI is available in PATH."""
        try:
            result = subprocess.run(
                ['which', 'claude'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """Initialize the Claude Code analyzer tools."""
        tools = [
            Tool(
                id="understand_codebase_with_claude_code",
                name="understand_codebase_with_claude_code",
                description=(
                    "Analyze a codebase using Claude Code to generate an extensive technical report. "
                    "This tool runs on the HOST MACHINE, not in a container. "
                    "It executes Claude Code CLI on the specified directory to understand the project's "
                    "technical makeup, architecture, patterns, and implementation details. "
                    "Returns a comprehensive analysis suitable for presentations."
                ),
                parameters={
                    "path": Parameter(
                        name="path",
                        type=ParameterType.STRING,
                        description="Path to the directory containing the codebase to analyze. This path should be a path on the user's **host machine** where the code resides.",
                        required=True
                    ),
                    "prompt": Parameter(
                        name="prompt",
                        type=ParameterType.STRING,
                        description="Custom prompt for Claude Code (optional, uses default comprehensive prompt if not provided)",
                        required=False,
                        default=None
                    ),
                    "timeout": Parameter(
                        name="timeout",
                        type=ParameterType.INTEGER,
                        description="Maximum time in seconds to wait for analysis (default: 600 seconds / 10 minutes)",
                        required=False,
                        default=600
                    )
                }
            )
        ]

        # No persistent state needed
        state = {}
        metadata = {
            "understand_codebase_with_claude_code": {
                "requires": "claude CLI",
                "available": self.claude_available
            }
        }

        return tools, state, metadata

    def call_tool(
        self,
        tool_id: str,
        tool_parameters: Dict[str, Any],
        per_conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """Execute a Claude Code analyzer tool."""
        if tool_id == "understand_codebase_with_claude_code":
            return self._analyze_codebase(tool_parameters)
        else:
            return None, f"Unknown tool: {tool_id}"

    def _analyze_codebase(self, parameters: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        """Analyze a codebase using Claude Code CLI."""
        if not self.claude_available:
            return None, "Claude CLI is not available. Please ensure 'claude' command is installed and in PATH."

        # Get parameters
        path = parameters.get("path")
        if not path:
            return None, "Path parameter is required"

        # Expand and validate path
        path = os.path.expanduser(path)
        path = os.path.abspath(path)
        
        if not os.path.exists(path):
            return None, f"Path does not exist: {path}"
        
        if not os.path.isdir(path):
            return None, f"Path is not a directory: {path}"

        # Use custom prompt or default
        prompt = parameters.get("prompt")
        if not prompt:
            prompt = (
                "Understand this codebase thoroughly. Output an extensive technical report. "
                "As extensive as you can be, for me to build a presentation about the technical "
                "makeup of the project. Include:\n"
                "1. Project overview and purpose\n"
                "2. Architecture and design patterns\n"
                "3. Core components and their interactions\n"
                "4. Key technologies and frameworks used\n"
                "5. Code organization and structure\n"
                "6. Notable implementation details\n"
                "7. Testing approach\n"
                "8. Build and deployment setup\n"
                "9. Areas of technical excellence\n"
                "10. Potential improvements or technical debt\n"
                "Remember that only your last output will be considered."
            )

        # Get timeout
        timeout = parameters.get("timeout", 300)
        if timeout <= 0:
            timeout = None  # No timeout

        try:
            # Build the claude command
            # Using --print to get output directly
            # Using --permission-mode plan as requested
            cmd = [
                'claude',
                '--model', 'sonnet',
                '--print', prompt,
                '--permission-mode', 'plan'
            ]

            # Execute the command in the specified directory
            result = subprocess.run(
                cmd,
                cwd=path,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            # Check for errors
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                return None, f"Claude Code analysis failed: {error_msg}"

            # Get the output
            output = result.stdout.strip()
            
            if not output:
                return None, "Claude Code returned no output"

            # Return the analysis result
            return {
                "analysis": output,
                "path": path,
                "status": "success",
                "message": f"Successfully analyzed codebase at {path}"
            }, None

        except subprocess.TimeoutExpired:
            return None, f"Analysis timed out after {timeout} seconds. Consider increasing the timeout parameter."
        except FileNotFoundError:
            return None, "Claude CLI not found. Please install Claude Code and ensure it's in your PATH."
        except Exception as e:
            return None, f"Error running Claude Code analysis: {str(e)}"

    def get_name(self) -> str:
        """Get the name of this tool provider."""
        return "claude_code_analyzer"

    def get_description(self) -> str:
        """Get the description of this tool provider."""
        return "Claude Code analyzer for generating comprehensive codebase reports"
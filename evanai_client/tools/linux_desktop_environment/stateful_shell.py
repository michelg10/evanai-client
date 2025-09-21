"""Stateful shell implementation for maintaining shell state across commands."""

import os
import json
from typing import Dict, Optional, Tuple, Any
from pathlib import Path


class StatefulShell:
    """
    Maintains shell state across command executions.
    Tracks working directory, environment variables, aliases, and functions.
    """

    def __init__(self, agent_id: str, initial_workdir: str = "/mnt"):
        self.agent_id = agent_id
        self.workdir = initial_workdir
        self.env_vars: Dict[str, str] = {}
        self.aliases: Dict[str, str] = {}
        self.functions: Dict[str, str] = {}
        self.shell_history: list = []
        self.exit_code = 0

    def build_command(self, command: str) -> str:
        """
        Build a command that includes all state restoration.
        """
        # Start with changing to the current working directory
        state_setup = []

        # Always cd to current directory first
        if self.workdir != "/mnt":
            state_setup.append(f"cd '{self.workdir}'")

        # Export all tracked environment variables
        for key, value in self.env_vars.items():
            # Escape single quotes in value
            escaped_value = value.replace("'", "'\\''")
            state_setup.append(f"export {key}='{escaped_value}'")

        # Set all aliases
        for name, cmd in self.aliases.items():
            escaped_cmd = cmd.replace("'", "'\\''")
            state_setup.append(f"alias {name}='{escaped_cmd}'")

        # Define all functions
        for name, body in self.functions.items():
            state_setup.append(body)

        # Handle special commands that change state
        parsed_cmd = self._parse_state_changing_command(command)

        # Build the full command
        if state_setup:
            # Join state setup with the actual command
            full_command = " && ".join(state_setup + [parsed_cmd])
        else:
            full_command = parsed_cmd

        # Add state extraction at the end
        # We'll get the pwd and environment after the command runs
        state_extraction = (
            f"EXIT_CODE=$?; "  # Capture exit code first
            f"echo '___STATE_MARKER___'; "
            f"pwd; "
            f"echo '___ENV_MARKER___'; "
            f"env | grep -E '^[A-Z_][A-Z0-9_]*=' || true; "
            f"echo '___ALIAS_MARKER___'; "
            f"alias 2>/dev/null || true; "
            f"echo '___END_MARKER___'; "
            f"exit $EXIT_CODE"  # Preserve original exit code
        )

        return f"({full_command}); {state_extraction}"

    def _parse_state_changing_command(self, command: str) -> str:
        """
        Parse commands that change state and track them.
        Returns the command, potentially modified for better state tracking.
        """
        cmd_stripped = command.strip()

        # Track commands in history
        self.shell_history.append(cmd_stripped)

        # Handle 'cd' commands - we'll update working directory from pwd output
        if cmd_stripped.startswith("cd "):
            # Just return the command, we'll track the new directory from pwd
            return cmd_stripped
        elif cmd_stripped == "cd":
            # cd with no args goes to home
            return "cd ~"

        # Handle 'export' commands
        if cmd_stripped.startswith("export "):
            # Parse export command
            export_part = cmd_stripped[7:].strip()
            if "=" in export_part:
                var_name = export_part.split("=")[0].strip()
                # Track that we need to capture this variable
                # The actual value will come from env output
                pass
            return cmd_stripped

        # Handle 'unset' commands
        if cmd_stripped.startswith("unset "):
            var_name = cmd_stripped[6:].strip()
            if var_name in self.env_vars:
                del self.env_vars[var_name]
            return cmd_stripped

        # Handle 'alias' commands
        if cmd_stripped.startswith("alias "):
            alias_def = cmd_stripped[6:].strip()
            if "=" in alias_def:
                alias_name = alias_def.split("=")[0].strip()
                alias_value = alias_def.split("=", 1)[1].strip()
                # Remove quotes if present
                if alias_value.startswith(("'", '"')) and alias_value.endswith(("'", '"')):
                    alias_value = alias_value[1:-1]
                self.aliases[alias_name] = alias_value
            return cmd_stripped

        # Handle 'unalias' commands
        if cmd_stripped.startswith("unalias "):
            alias_name = cmd_stripped[8:].strip()
            if alias_name in self.aliases:
                del self.aliases[alias_name]
            return cmd_stripped

        # Handle function definitions (simple case)
        if "() {" in cmd_stripped or cmd_stripped.startswith("function "):
            # Store the function definition
            if cmd_stripped.startswith("function "):
                func_name = cmd_stripped.split()[1].split("(")[0]
            else:
                func_name = cmd_stripped.split("(")[0].strip()
            self.functions[func_name] = cmd_stripped
            return cmd_stripped

        return cmd_stripped

    def update_state_from_output(self, output: str) -> str:
        """
        Parse output to extract state information and return cleaned output.
        """
        if "___STATE_MARKER___" not in output:
            # No state markers, return as-is
            return output

        try:
            # Split output to get user output and state info
            parts = output.split("___STATE_MARKER___")
            user_output = parts[0]

            if len(parts) > 1:
                state_output = parts[1]

                # Parse working directory
                if "___ENV_MARKER___" in state_output:
                    pwd_part = state_output.split("___ENV_MARKER___")[0].strip()
                    if pwd_part:
                        self.workdir = pwd_part.strip()

                # Parse environment variables
                if "___ENV_MARKER___" in state_output and "___ALIAS_MARKER___" in state_output:
                    env_part = state_output.split("___ENV_MARKER___")[1].split("___ALIAS_MARKER___")[0].strip()
                    if env_part:
                        # Parse environment variables
                        new_env = {}
                        for line in env_part.split("\n"):
                            if "=" in line and not line.startswith(("___", "PS1", "PS2", "BASH")):
                                key = line.split("=")[0]
                                value = line.split("=", 1)[1]
                                # Only track user-defined variables (rough heuristic)
                                if not key.startswith("BASH_") and key not in ["SHLVL", "PATH", "PWD", "OLDPWD", "_"]:
                                    new_env[key] = value

                        # Update our tracked environment
                        self.env_vars.update(new_env)

                # Parse aliases
                if "___ALIAS_MARKER___" in state_output and "___END_MARKER___" in state_output:
                    alias_part = state_output.split("___ALIAS_MARKER___")[1].split("___END_MARKER___")[0].strip()
                    if alias_part:
                        # Parse alias output (format: alias name='value')
                        for line in alias_part.split("\n"):
                            if line.startswith("alias "):
                                alias_def = line[6:].strip()
                                if "=" in alias_def:
                                    name = alias_def.split("=")[0]
                                    value = alias_def.split("=", 1)[1]
                                    # Remove quotes
                                    if value.startswith(("'", '"')) and value.endswith(("'", '"')):
                                        value = value[1:-1]
                                    self.aliases[name] = value

            return user_output

        except Exception as e:
            # If parsing fails, just return the full output
            print(f"[StatefulShell] Failed to parse state: {e}")
            return output

    def get_state(self) -> Dict[str, Any]:
        """Get current shell state."""
        return {
            "workdir": self.workdir,
            "env_vars": self.env_vars.copy(),
            "aliases": self.aliases.copy(),
            "functions": self.functions.copy(),
            "history": self.shell_history.copy()[-20:]  # Last 20 commands
        }

    def reset(self):
        """Reset shell state to initial state."""
        self.workdir = "/mnt"
        self.env_vars.clear()
        self.aliases.clear()
        self.functions.clear()
        self.shell_history.clear()
        self.exit_code = 0

    def save_state(self, filepath: str):
        """Save state to a file."""
        with open(filepath, 'w') as f:
            json.dump(self.get_state(), f, indent=2)

    def load_state(self, filepath: str):
        """Load state from a file."""
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                state = json.load(f)
                self.workdir = state.get('workdir', '/mnt')
                self.env_vars = state.get('env_vars', {})
                self.aliases = state.get('aliases', {})
                self.functions = state.get('functions', {})
                self.shell_history = state.get('history', [])
"""
Text Editor Tool - Anthropic Built-in Tool Wrapper

This module provides the implementation for Anthropic's built-in text editor tool.
It executes the commands that Claude sends through the Messages API.

The tool supports:
- view: View file or directory contents
- str_replace: Replace text in a file
- create: Create a new file
- insert: Insert text at a specific line
- undo_edit: Undo the last edit (Sonnet 3.7 only)

Based on Anthropic's text_editor_tool documentation.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


class TextEditorTool:
    """
    Executor for Anthropic's text editor tool commands.

    This class processes the commands that Claude sends when using
    the str_replace_based_edit_tool or str_replace_editor.
    """

    def __init__(self, workspace_dir: Optional[str] = None):
        """
        Initialize the text editor tool executor.

        Args:
            workspace_dir: Directory where file operations are allowed.
                          Defaults to current working directory.
        """
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()
        self.workspace_dir = self.workspace_dir.resolve()

        # Track edit history for undo functionality
        self.edit_history: Dict[str, List[Dict[str, Any]]] = {}

    def execute(self, command_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a text editor command from Claude.

        Args:
            command_input: The input dict from Claude's tool_use block

        Returns:
            Result dictionary with the command output
        """
        command = command_input.get("command")

        if not command:
            return self._error("No command specified")

        try:
            if command == "view":
                return self._view(command_input)
            elif command == "str_replace":
                return self._str_replace(command_input)
            elif command == "create":
                return self._create(command_input)
            elif command == "insert":
                return self._insert(command_input)
            elif command == "undo_edit":
                return self._undo_edit(command_input)
            else:
                return self._error(f"Unknown command: {command}")
        except Exception as e:
            return self._error(f"Error executing {command}: {str(e)}")

    def _view(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        View file or directory contents.

        Parameters:
            path: File or directory path
            view_range: Optional [start_line, end_line] for partial file viewing
        """
        path = params.get("path")
        if not path:
            return self._error("Path is required for view command")

        # Resolve path relative to workspace
        full_path = self._resolve_path(path)

        if not full_path.exists():
            return self._error(f"Path does not exist: {path}")

        if full_path.is_dir():
            # List directory contents
            return self._view_directory(full_path)
        else:
            # View file contents
            view_range = params.get("view_range")
            return self._view_file(full_path, view_range)

    def _view_file(self, path: Path, view_range: Optional[List[int]] = None) -> Dict[str, Any]:
        """View file contents with optional line range."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            total_lines = len(lines)

            if view_range:
                if len(view_range) != 2:
                    return self._error("view_range must be a list of two integers")

                start = view_range[0] - 1  # Convert to 0-indexed
                end = view_range[1] if view_range[1] != -1 else total_lines

                # Validate range
                start = max(0, min(start, total_lines - 1))
                end = max(start + 1, min(end, total_lines))

                selected_lines = lines[start:end]
                content = ''.join(selected_lines)

                return {
                    "success": True,
                    "content": content,
                    "view_range": [start + 1, end],  # Convert back to 1-indexed
                    "total_lines": total_lines
                }
            else:
                # View entire file
                content = ''.join(lines)
                return {
                    "success": True,
                    "content": content,
                    "total_lines": total_lines
                }

        except UnicodeDecodeError:
            return self._error(f"Cannot read file {path}: not a text file")
        except Exception as e:
            return self._error(f"Error reading file {path}: {str(e)}")

    def _view_directory(self, path: Path) -> Dict[str, Any]:
        """List directory contents."""
        try:
            entries = []
            for item in sorted(path.iterdir()):
                entry_type = "directory" if item.is_dir() else "file"
                size = item.stat().st_size if item.is_file() else None
                entries.append({
                    "name": item.name,
                    "type": entry_type,
                    "size": size
                })

            return {
                "success": True,
                "entries": entries,
                "total_entries": len(entries)
            }
        except Exception as e:
            return self._error(f"Error reading directory {path}: {str(e)}")

    def _str_replace(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Replace text in a file.

        Parameters:
            path: File path
            old_str: Text to replace (must match exactly)
            new_str: Replacement text
        """
        path = params.get("path")
        old_str = params.get("old_str")
        new_str = params.get("new_str")

        if not all([path, old_str is not None, new_str is not None]):
            return self._error("path, old_str, and new_str are required")

        full_path = self._resolve_path(path)

        if not full_path.exists():
            return self._error(f"File does not exist: {path}")

        if full_path.is_dir():
            return self._error(f"Cannot edit directory: {path}")

        try:
            # Read current content
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if old_str exists
            if old_str not in content:
                # Try to provide helpful context
                lines = content.split('\n')
                suggestions = []
                for i, line in enumerate(lines):
                    if any(part in line for part in old_str.split('\n') if part.strip()):
                        suggestions.append(f"Line {i+1}: {line[:100]}")

                error_msg = f"Text not found in file. The exact string '{old_str[:100]}' was not found."
                if suggestions:
                    error_msg += f"\n\nPossible matches:\n" + "\n".join(suggestions[:3])
                return self._error(error_msg)

            # Save to history for undo
            self._save_to_history(str(full_path), content)

            # Perform replacement
            new_content = content.replace(old_str, new_str, 1)  # Replace only first occurrence

            # Write new content
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            # Count lines changed
            old_lines = old_str.count('\n') + 1
            new_lines = new_str.count('\n') + 1

            return {
                "success": True,
                "message": f"Successfully replaced text in {path}",
                "lines_changed": max(old_lines, new_lines)
            }

        except Exception as e:
            return self._error(f"Error editing file {path}: {str(e)}")

    def _create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new file.

        Parameters:
            path: File path
            file_text: Content for the new file
        """
        path = params.get("path")
        file_text = params.get("file_text", "")

        if not path:
            return self._error("path is required for create command")

        full_path = self._resolve_path(path)

        if full_path.exists():
            return self._error(f"File already exists: {path}")

        try:
            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(file_text)

            line_count = file_text.count('\n') + 1 if file_text else 0

            return {
                "success": True,
                "message": f"Successfully created file {path}",
                "lines_written": line_count
            }

        except Exception as e:
            return self._error(f"Error creating file {path}: {str(e)}")

    def _insert(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert text at a specific line.

        Parameters:
            path: File path
            insert_line: Line number after which to insert (0 for beginning)
            new_str: Text to insert
        """
        path = params.get("path")
        insert_line = params.get("insert_line")
        new_str = params.get("new_str", "")

        if path is None or insert_line is None:
            return self._error("path and insert_line are required")

        full_path = self._resolve_path(path)

        if not full_path.exists():
            return self._error(f"File does not exist: {path}")

        try:
            # Read current content
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Save to history for undo
            self._save_to_history(str(full_path), ''.join(lines))

            # Validate line number
            if insert_line < 0:
                return self._error("insert_line must be >= 0")
            if insert_line > len(lines):
                return self._error(f"insert_line {insert_line} exceeds file length {len(lines)}")

            # Insert text
            if insert_line == 0:
                # Insert at beginning
                new_lines = [new_str] + lines
            else:
                # Insert after specified line
                new_lines = lines[:insert_line] + [new_str] + lines[insert_line:]

            # Ensure new_str ends with newline if it doesn't
            if new_str and not new_str.endswith('\n'):
                new_lines[insert_line] = new_str + '\n'

            # Write new content
            with open(full_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

            lines_added = new_str.count('\n') + 1 if new_str else 0

            return {
                "success": True,
                "message": f"Successfully inserted text at line {insert_line} in {path}",
                "lines_added": lines_added
            }

        except Exception as e:
            return self._error(f"Error inserting into file {path}: {str(e)}")

    def _undo_edit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Undo the last edit to a file.

        Parameters:
            path: File path
        """
        path = params.get("path")
        if not path:
            return self._error("path is required for undo_edit command")

        full_path = self._resolve_path(path)
        path_str = str(full_path)

        if path_str not in self.edit_history or not self.edit_history[path_str]:
            return self._error(f"No edit history for {path}")

        try:
            # Get last saved content
            last_content = self.edit_history[path_str].pop()["content"]

            # Restore content
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(last_content)

            return {
                "success": True,
                "message": f"Successfully undid last edit to {path}"
            }

        except Exception as e:
            return self._error(f"Error undoing edit for {path}: {str(e)}")

    def _resolve_path(self, path: str) -> Path:
        """Resolve path within the workspace sandbox.

        SANDBOXED MODE: All paths are resolved within workspace_dir.
        This prevents the agent from accessing files outside its sandbox.
        """
        # Strip /mnt/ prefix if present (agent might use absolute container paths)
        if path.startswith("/mnt/"):
            path = path[5:]  # Remove "/mnt/" (5 characters)
        elif path == "/mnt":
            path = "."

        p = Path(path)

        # Always resolve relative to workspace
        if self.workspace_dir:
            # Strip leading slash from absolute paths to make them relative
            if p.is_absolute():
                # Convert absolute path to relative by removing leading /
                path_str = str(p).lstrip('/')
                p = Path(path_str)

            # Resolve within workspace
            resolved = (self.workspace_dir / p).resolve()

            # Security check: ensure resolved path is within workspace
            try:
                resolved.relative_to(self.workspace_dir.resolve())
            except ValueError:
                # Path is outside workspace (e.g., due to ../ traversal)
                raise ValueError(f"Access denied: Path '{path}' is outside the workspace sandbox")

            return resolved
        else:
            # No workspace set - use current directory as sandbox
            resolved = p.resolve()
            cwd = Path.cwd()

            # Security check: ensure resolved path is within current directory
            try:
                resolved.relative_to(cwd)
            except ValueError:
                # Path is outside current directory
                raise ValueError(f"Access denied: Path '{path}' is outside the current directory sandbox")

            return resolved

    def _save_to_history(self, path: str, content: str):
        """Save file content to history for undo functionality."""
        if path not in self.edit_history:
            self.edit_history[path] = []

        # Keep only last 10 edits per file
        if len(self.edit_history[path]) >= 10:
            self.edit_history[path].pop(0)

        self.edit_history[path].append({
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def _error(self, message: str) -> Dict[str, Any]:
        """Return an error response."""
        return {
            "success": False,
            "error": message
        }
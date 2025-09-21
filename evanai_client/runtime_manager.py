"""Runtime directory manager for EvanAI client."""

import os
import shutil
from pathlib import Path
from typing import Optional


class RuntimeManager:
    """Manages the runtime directory structure for conversations and agent state."""

    def __init__(self, runtime_dir: str = "evanai_runtime"):
        self.runtime_dir = Path(runtime_dir)
        self._ensure_base_directories()

    def _ensure_base_directories(self):
        """Ensure all base directories exist."""
        # Create base runtime directories
        (self.runtime_dir / "agent-memory").mkdir(parents=True, exist_ok=True)
        (self.runtime_dir / "conversation-data").mkdir(parents=True, exist_ok=True)
        (self.runtime_dir / "agent-working-directory").mkdir(parents=True, exist_ok=True)

    @property
    def tool_states_path(self) -> Path:
        """Get the path to the tool states file."""
        return self.runtime_dir / "tool_states.pkl"

    @property
    def agent_memory_path(self) -> Path:
        """Get the path to the shared agent memory directory."""
        return self.runtime_dir / "agent-memory"

    def get_conversation_data_path(self, conversation_id: str) -> Path:
        """Get the path to a conversation's data directory."""
        return self.runtime_dir / "conversation-data" / conversation_id

    def get_working_directory_path(self, conversation_id: str) -> Path:
        """Get the path to a conversation's working directory."""
        return self.runtime_dir / "agent-working-directory" / conversation_id

    def setup_conversation_directories(self, conversation_id: str) -> dict:
        """Set up all directories for a new conversation.

        Returns:
            Dictionary with paths to all created directories
        """
        # Create conversation data directory
        conv_data_path = self.get_conversation_data_path(conversation_id)
        conv_data_path.mkdir(parents=True, exist_ok=True)

        # Create working directory for this conversation
        working_dir = self.get_working_directory_path(conversation_id)
        working_dir.mkdir(parents=True, exist_ok=True)

        # Create temp directory within working directory
        temp_dir = working_dir / "temp"
        temp_dir.mkdir(exist_ok=True)

        # Create symlink to shared agent-memory
        # NOTE: These symlinks are for host-side tools only (text_editor, file_system_tool, etc.)
        # Docker containers mount the actual directories directly, not via symlinks
        agent_memory_link = working_dir / "agent-memory"
        if not agent_memory_link.exists():
            # Calculate relative path from working dir to agent-memory
            rel_path = os.path.relpath(
                self.agent_memory_path,
                working_dir
            )
            agent_memory_link.symlink_to(rel_path)

        # Create symlink to conversation-specific data
        # NOTE: These symlinks are for host-side tools only (text_editor, file_system_tool, etc.)
        # Docker containers mount the actual directories directly, not via symlinks
        conv_data_link = working_dir / "conversation_data"
        if not conv_data_link.exists():
            # Calculate relative path from working dir to conversation data
            rel_path = os.path.relpath(
                conv_data_path,
                working_dir
            )
            conv_data_link.symlink_to(rel_path)

        return {
            "conversation_data": str(conv_data_path),
            "working_directory": str(working_dir),
            "temp_directory": str(temp_dir),
            "agent-memory_link": str(agent_memory_link),
            "conversation_data_link": str(conv_data_link)
        }

    def cleanup_conversation_temp(self, conversation_id: str):
        """Clean up temporary files for a conversation."""
        temp_dir = self.get_working_directory_path(conversation_id) / "temp"
        if temp_dir.exists():
            # Remove all files in temp directory but keep the directory
            for item in temp_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            print(f"Cleaned temp directory for conversation {conversation_id}")

    def remove_conversation(self, conversation_id: str):
        """Completely remove a conversation's directories."""
        # Remove conversation data
        conv_data_path = self.get_conversation_data_path(conversation_id)
        if conv_data_path.exists():
            shutil.rmtree(conv_data_path)

        # Remove working directory (including symlinks)
        working_dir = self.get_working_directory_path(conversation_id)
        if working_dir.exists():
            # Remove symlinks first (they're just links, safe to unlink)
            for link in ["agent-memory", "conversation_data"]:
                link_path = working_dir / link
                if link_path.is_symlink():
                    link_path.unlink()

            # Remove the working directory
            shutil.rmtree(working_dir)

        print(f"Removed all directories for conversation {conversation_id}")

    def list_conversations(self) -> list:
        """List all conversation IDs that have directories."""
        conv_data_dir = self.runtime_dir / "conversation-data"
        if conv_data_dir.exists():
            return [d.name for d in conv_data_dir.iterdir() if d.is_dir()]
        return []

    def get_conversation_info(self, conversation_id: str) -> dict:
        """Get information about a conversation's directories."""
        info = {
            "conversation_id": conversation_id,
            "exists": False,
            "paths": {}
        }

        conv_data_path = self.get_conversation_data_path(conversation_id)
        working_dir = self.get_working_directory_path(conversation_id)

        if conv_data_path.exists() or working_dir.exists():
            info["exists"] = True
            info["paths"] = {
                "conversation_data": str(conv_data_path) if conv_data_path.exists() else None,
                "working_directory": str(working_dir) if working_dir.exists() else None,
                "temp_directory": str(working_dir / "temp") if (working_dir / "temp").exists() else None,
            }

            # Check symlinks
            if working_dir.exists():
                agent_memory_link = working_dir / "agent-memory"
                conv_data_link = working_dir / "conversation_data"
                info["paths"]["agent-memory_link"] = {
                    "exists": agent_memory_link.exists(),
                    "is_symlink": agent_memory_link.is_symlink(),
                    "target": str(agent_memory_link.resolve()) if agent_memory_link.exists() else None
                }
                info["paths"]["conversation_data_link"] = {
                    "exists": conv_data_link.exists(),
                    "is_symlink": conv_data_link.is_symlink(),
                    "target": str(conv_data_link.resolve()) if conv_data_link.exists() else None
                }

        return info

    def reset_all(self):
        """Reset all runtime directories (use with caution)."""
        if self.runtime_dir.exists():
            # Keep the base structure but clear contents
            for subdir in ["conversation-data", "agent-working-directory"]:
                dir_path = self.runtime_dir / subdir
                if dir_path.exists():
                    shutil.rmtree(dir_path)
                    dir_path.mkdir()

            # Clear agent-memory contents but keep directory
            agent_mem = self.runtime_dir / "agent-memory"
            if agent_mem.exists():
                for item in agent_mem.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)

            # Remove tool states file
            if self.tool_states_path.exists():
                self.tool_states_path.unlink()

            print("Reset all runtime directories")
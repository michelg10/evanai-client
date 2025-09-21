"""
Memory tool for storing facts about the user across all conversations.

This tool maintains a persistent list of facts about the user that can be
accessed and referenced in all future conversations.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

from ..tool_system import BaseToolSetProvider, Tool, Parameter, ParameterType


class MemoryToolProvider(BaseToolSetProvider):
    """Provider for memory-related tools."""

    def __init__(self, websocket_handler=None, runtime_dir=None):
        super().__init__(websocket_handler)
        # Use the runtime directory to find agent-memory folder
        if runtime_dir:
            self.memory_dir = Path(runtime_dir) / "agent-memory"
        else:
            # Fallback to default
            self.memory_dir = Path("evanai_runtime") / "agent-memory"

        # Ensure directory exists
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self.facts_file = self.memory_dir / "user_facts.txt"

        # Initialize facts file if it doesn't exist
        if not self.facts_file.exists():
            self.facts_file.touch()

    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """Initialize the memory tools."""
        tools = [
            Tool(
                id="remember_user_fact",
                name="remember_user_fact",
                description=(
                    "Store a fact about the user that should be remembered across all conversations. "
                    "Use this tool when:\n"
                    "- The user explicitly asks you to remember something (e.g., 'Remember that I...')\n"
                    "- The user shares important preferences (e.g., 'I prefer detailed explanations')\n"
                    "- The user mentions their interests, background, or context (e.g., 'I'm studying physics')\n"
                    "- The user shares work/project details that would be helpful long-term\n"
                    "- The user corrects something about themselves you should know\n\n"
                    "DON'T use this for:\n"
                    "- Temporary or trivial information (e.g., 'I'm tired right now')\n"
                    "- Information that will quickly become outdated\n"
                    "- Sensitive personal information unless explicitly requested\n\n"
                    "The fact should be concise and self-contained."
                ),
                parameters={
                    "fact": Parameter(
                        name="fact",
                        type=ParameterType.STRING,
                        description="A concise, self-contained fact about the user to remember",
                        required=True
                    )
                }
            )
        ]

        # No state needed for this tool
        state = {}

        # Tool metadata
        metadata = {
            "remember_user_fact": {
                "storage_location": str(self.facts_file)
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
        """Execute a memory tool."""
        if tool_id == "remember_user_fact":
            fact = tool_parameters.get("fact", "").strip()

            if not fact:
                return None, "No fact provided"

            try:
                # Add timestamp to the fact for tracking
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Append the fact to the file
                with open(self.facts_file, "a", encoding="utf-8") as f:
                    f.write(f"{fact}\n")

                # Count total facts
                with open(self.facts_file, "r", encoding="utf-8") as f:
                    total_facts = len([line for line in f if line.strip()])

                return {
                    "success": True,
                    "message": f"I've remembered that fact about you. I now know {total_facts} facts about you.",
                    "fact": fact
                }, None

            except Exception as e:
                return None, f"Failed to save fact: {str(e)}"

        return None, f"Unknown tool: {tool_id}"

    def get_user_facts(self) -> List[str]:
        """Get all stored user facts."""
        if not self.facts_file.exists():
            return []

        try:
            with open(self.facts_file, "r", encoding="utf-8") as f:
                facts = [line.strip() for line in f if line.strip()]
                return facts
        except Exception:
            return []

    def get_name(self) -> str:
        return "memory_tools"

    def get_description(self) -> str:
        return "Tools for remembering facts about the user across conversations"
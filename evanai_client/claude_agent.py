import os
from typing import Dict, Any, List, Optional, Tuple
from anthropic import Anthropic
from anthropic.types import Message, ToolUseBlock, TextBlock
import json
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompts import get_system_prompt
from .constants import MAX_TOKENS, DEFAULT_CLAUDE_MODEL


class ClaudeAgent:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found. Set it as an environment variable or pass it to the constructor.")

        self.client = Anthropic(api_key=self.api_key)
        self.model = DEFAULT_CLAUDE_MODEL
        self.max_tokens = MAX_TOKENS
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Get the system prompt with current datetime."""
        try:
            current_datetime = datetime.now().strftime("%B %d, %Y at %I:%M %p %Z")
            return get_system_prompt(current_datetime)
        except Exception as e:
            print(f"Error loading system prompt: {e}")
            return ""

    def _process_tool_calls(
        self,
        content_blocks: List,
        tool_callback: Optional[callable]
    ) -> Tuple[List[Dict], str]:
        """Process tool calls from content blocks.

        Returns:
            Tuple of (tool_results, text_response)
        """
        tool_results = []
        text_response = ""

        for content_block in content_blocks:
            if isinstance(content_block, TextBlock):
                text_response += content_block.text
            elif isinstance(content_block, ToolUseBlock) and tool_callback:
                tool_result, error = tool_callback(
                    content_block.name,
                    content_block.input
                )

                tool_result_message = {
                    "type": "tool_result",
                    "tool_use_id": content_block.id,
                    "content": json.dumps(tool_result) if not error else error,
                    "is_error": bool(error)
                }
                tool_results.append(tool_result_message)

        return tool_results, text_response

    def _build_assistant_message(self, content_blocks: List) -> Dict:
        """Build assistant message from content blocks."""
        content = []
        for content_block in content_blocks:
            if isinstance(content_block, TextBlock):
                content.append({
                    "type": "text",
                    "text": content_block.text
                })
            elif isinstance(content_block, ToolUseBlock):
                content.append({
                    "type": "tool_use",
                    "id": content_block.id,
                    "name": content_block.name,
                    "input": content_block.input
                })
        return {"role": "assistant", "content": content}

    def process_prompt(
        self,
        prompt: str,
        conversation_history: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        tool_callback: Optional[callable] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Process a prompt with support for multiple tool calls in a single response."""
        messages = conversation_history + [{"role": "user", "content": prompt}]
        new_history = messages.copy()
        final_response = ""
        iteration = 0

        try:
            while True:
                iteration += 1

                # Log if we're in a long tool-calling chain
                if iteration > 50 and iteration % 10 == 0:
                    print(f"Note: Processing iteration {iteration} of tool calls...")

                # Make API call
                response = self.client.messages.create(
                    model=self.model,
                    messages=new_history,
                    max_tokens=self.max_tokens,
                    tools=tools if tools else None,
                    system=self.system_prompt if self.system_prompt else None
                )

                # Build and append assistant message
                assistant_message = self._build_assistant_message(response.content)
                new_history.append(assistant_message)

                # Process any tool calls and collect text
                tool_results, text_response = self._process_tool_calls(
                    response.content,
                    tool_callback
                )

                # Update final response with any text from this iteration
                if text_response:
                    final_response = text_response

                # If there were tool calls, add results and continue
                if tool_results:
                    tool_message = {
                        "role": "user",
                        "content": tool_results
                    }
                    new_history.append(tool_message)
                    # Continue loop to process Claude's response to tool results
                else:
                    # No tool calls, we're done
                    break

            return final_response, new_history

        except Exception as e:
            error_msg = f"Error processing prompt with Claude: {str(e)}"
            print(error_msg)
            return error_msg, messages

    def set_model(self, model: str):
        self.model = model

    def set_max_tokens(self, max_tokens: int):
        self.max_tokens = max_tokens

    def reload_system_prompt(self):
        """Reload the system prompt from file."""
        self.system_prompt = self._load_system_prompt()
        print("System prompt reloaded successfully.")
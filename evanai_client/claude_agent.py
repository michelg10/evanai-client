import os
from typing import Dict, Any, List, Optional, Tuple
from anthropic import Anthropic
from anthropic.types import Message, ToolUseBlock, TextBlock
import json


class ClaudeAgent:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found. Set it as an environment variable or pass it to the constructor.")

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"
        self.max_tokens = 4096

    def process_prompt(
        self,
        prompt: str,
        conversation_history: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        tool_callback: Optional[callable] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        messages = conversation_history + [
            {"role": "user", "content": prompt}
        ]

        try:
            response = self.client.messages.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                tools=tools if tools else None
            )

            new_history = messages.copy()
            assistant_message = {"role": "assistant", "content": []}

            final_response = ""
            tool_results = []

            for content_block in response.content:
                if isinstance(content_block, TextBlock):
                    assistant_message["content"].append({
                        "type": "text",
                        "text": content_block.text
                    })
                    final_response += content_block.text

                elif isinstance(content_block, ToolUseBlock):
                    tool_use = {
                        "type": "tool_use",
                        "id": content_block.id,
                        "name": content_block.name,
                        "input": content_block.input
                    }
                    assistant_message["content"].append(tool_use)

                    if tool_callback:
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

            new_history.append(assistant_message)

            if tool_results:
                tool_message = {
                    "role": "user",
                    "content": tool_results
                }
                new_history.append(tool_message)

                follow_up = self.client.messages.create(
                    model=self.model,
                    messages=new_history,
                    max_tokens=self.max_tokens,
                    tools=tools if tools else None
                )

                follow_up_content = []
                for content_block in follow_up.content:
                    if isinstance(content_block, TextBlock):
                        follow_up_content.append({
                            "type": "text",
                            "text": content_block.text
                        })
                        final_response = content_block.text
                    elif isinstance(content_block, ToolUseBlock):
                        follow_up_content.append({
                            "type": "tool_use",
                            "id": content_block.id,
                            "name": content_block.name,
                            "input": content_block.input
                        })

                new_history.append({
                    "role": "assistant",
                    "content": follow_up_content
                })

            return final_response, new_history

        except Exception as e:
            error_msg = f"Error processing prompt with Claude: {str(e)}"
            print(error_msg)
            return error_msg, messages

    def set_model(self, model: str):
        self.model = model

    def set_max_tokens(self, max_tokens: int):
        self.max_tokens = max_tokens
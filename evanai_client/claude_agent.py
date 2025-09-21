import os
from typing import Dict, Any, List, Optional, Tuple
from anthropic import Anthropic
from anthropic.types import ToolUseBlock, TextBlock
import json
from datetime import datetime
import time
import sys
from colorama import Fore, Style
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompts import get_system_prompt
from .constants import (
    MAX_TOKENS,
    DEFAULT_CLAUDE_MODEL,
    BACKUP_CLAUDE_MODEL,
    MAX_BACKOFF_SECONDS,
    INITIAL_BACKOFF_SECONDS,
    BACKOFF_MULTIPLIER,
    FALLBACK_RETRY_COUNT
)
from .tools.builtin.api_integration import BuiltinToolsIntegration


class ClaudeAgent:
    def __init__(self, api_key: Optional[str] = None, workspace_dir: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found. Set it as an environment variable or pass it to the constructor.")

        self.client = Anthropic(api_key=self.api_key)
        self.model = DEFAULT_CLAUDE_MODEL
        self.original_model = DEFAULT_CLAUDE_MODEL  # Store original model for reset
        self.max_tokens = MAX_TOKENS
        self.system_prompt = self._load_system_prompt()

        # Track if we're using backup model
        self.using_backup_model = False

        # Initialize built-in tools integration
        self.builtin_tools = BuiltinToolsIntegration(workspace_dir)
        self.builtin_tools_enabled = []

        # Retry configuration (can be overridden by environment variables)
        self.max_backoff = float(os.environ.get("CLAUDE_MAX_BACKOFF", MAX_BACKOFF_SECONDS))
        self.initial_backoff = float(os.environ.get("CLAUDE_INITIAL_BACKOFF", INITIAL_BACKOFF_SECONDS))
        self.backoff_multiplier = float(os.environ.get("CLAUDE_BACKOFF_MULTIPLIER", BACKOFF_MULTIPLIER))
        self.fallback_retry_count = int(os.environ.get("CLAUDE_FALLBACK_RETRY_COUNT", FALLBACK_RETRY_COUNT))
        self.backup_model = os.environ.get("CLAUDE_BACKUP_MODEL", BACKUP_CLAUDE_MODEL)

    def _load_system_prompt(self) -> str:
        """Get the system prompt with current datetime."""
        try:
            current_datetime = datetime.now().strftime("%B %d, %Y at %I:%M %p %Z")
            return get_system_prompt(current_datetime)
        except Exception as e:
            print(f"Error loading system prompt: {e}")
            return ""

    def _make_api_call_with_retry(self, messages, tools, extra_headers=None):
        """Make API call with exponential backoff retry logic. Retries indefinitely.
        This includes the entire stream processing, not just stream creation.

        Args:
            messages: Conversation messages
            tools: List of tools (both custom and built-in)
            extra_headers: Additional headers for the API request
        """
        retry_count = 0
        backoff = self.initial_backoff
        current_model = self.model
        switched_to_backup = False

        while True:  # No limit to retries - will retry indefinitely
            try:
                # Check if we need to switch to backup model (only once)
                if retry_count == self.fallback_retry_count and not switched_to_backup:
                    # Display prominent warning about switching to backup model
                    print(f"\n{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}⚠️  SWITCHING TO BACKUP MODEL{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}   Primary model failed {self.fallback_retry_count} times{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}   Now using: {self.backup_model}{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}   Will continue retrying indefinitely with backup model{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}{'='*70}{Style.RESET_ALL}\n")

                    current_model = self.backup_model
                    self.using_backup_model = True
                    switched_to_backup = True
                    # Reset backoff when switching models
                    backoff = self.initial_backoff

                # Show which model is being used on each retry (after initial failure)
                if retry_count > 0:
                    model_status = f"{Fore.CYAN}[BACKUP MODEL]{Style.RESET_ALL}" if self.using_backup_model else f"{Fore.GREEN}[PRIMARY MODEL]{Style.RESET_ALL}"
                    print(f"{model_status} Retry {retry_count} - Waiting {backoff:.2f} seconds...")
                    time.sleep(backoff)

                # Process the entire stream within the retry block
                content_blocks = []
                current_block = None
                current_text = ""
                current_tool_input = ""
                tool_block = None

                # Make the API call and process stream
                stream_kwargs = {
                    'model': current_model,
                    'messages': messages,
                    'max_tokens': self.max_tokens,
                    'system': self.system_prompt if self.system_prompt else None
                }

                if tools:
                    stream_kwargs['tools'] = tools

                if extra_headers:
                    stream_kwargs['extra_headers'] = extra_headers
                    # print(f"[DEBUG] Adding headers to API request: {extra_headers}")

                # Debug output disabled for cleaner output
                # print(f"[DEBUG] API call with model: {current_model}")
                # print(f"[DEBUG] Number of tools: {len(tools) if tools else 0}")
                # if tools and len(tools) > 0:
                #     print(f"[DEBUG] Tool names: {[t.get('name') for t in tools]}")

                with self.client.messages.stream(**stream_kwargs) as stream:
                    # Process streaming events manually to handle both text and tool use
                    for event in stream:
                        if not hasattr(event, 'type'):
                            continue

                        # Handle content block start
                        if event.type == 'content_block_start':
                            if hasattr(event, 'content_block'):
                                if event.content_block.type == 'text':
                                    current_block = 'text'
                                    current_text = getattr(event.content_block, 'text', '')
                                elif event.content_block.type == 'tool_use':
                                    current_block = 'tool_use'
                                    tool_block = ToolUseBlock(
                                        type='tool_use',
                                        id=event.content_block.id,
                                        name=event.content_block.name,
                                        input={}
                                    )
                                    current_tool_input = ""
                                elif event.content_block.type in ('server_tool_use', 'web_fetch_tool_result', 'web_search_tool_result'):
                                    # Handle server-side tool results
                                    current_block = 'server_tool'
                                    content_blocks.append(event.content_block)

                        # Handle content block delta
                        elif event.type == 'content_block_delta':
                            if hasattr(event, 'delta'):
                                # Text delta
                                if current_block == 'text' and hasattr(event.delta, 'text'):
                                    current_text += event.delta.text
                                # Tool use JSON delta
                                elif current_block == 'tool_use' and hasattr(event.delta, 'partial_json'):
                                    current_tool_input += event.delta.partial_json

                        # Handle content block stop
                        elif event.type == 'content_block_stop':
                            if current_block == 'text':
                                content_blocks.append(TextBlock(type='text', text=current_text))
                            elif current_block == 'tool_use' and tool_block:
                                # Parse the accumulated JSON
                                try:
                                    tool_block.input = json.loads(current_tool_input) if current_tool_input else {}
                                except json.JSONDecodeError as e:
                                    print(f"Warning: Failed to parse tool input JSON: {e}")
                                    tool_block.input = {}
                                content_blocks.append(tool_block)

                            # Reset for next block
                            current_block = None
                            current_text = ""
                            current_tool_input = ""
                            tool_block = None

                # If successful and using backup model, show success message
                if self.using_backup_model and retry_count > 0:
                    print(f"{Fore.GREEN}✓ Backup model responded successfully{Style.RESET_ALL}")

                return content_blocks

            except Exception as e:
                error_str = str(e)
                retry_count += 1

                # Check if it's an overloaded error or other retryable error
                # Also check for the error dict structure from Anthropic
                is_retryable = (
                    'overloaded_error' in error_str or
                    'overloaded' in error_str.lower() or
                    'rate_limit' in error_str or
                    'timeout' in error_str or
                    '529' in error_str  # HTTP status code for overloaded
                )

                if is_retryable:
                    if retry_count == 1:
                        print(f"{Fore.RED}API call failed: {error_str}{Style.RESET_ALL}")

                    # Exponential backoff with max limit
                    backoff = min(backoff * self.backoff_multiplier, self.max_backoff)
                else:
                    # Non-retryable error, raise it
                    raise e

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

                # Special handling for view_photo tool - return image content blocks
                if content_block.name == "view_photo" and tool_result and not error:
                    # Check if the result contains image data
                    if isinstance(tool_result, dict) and tool_result.get('type') == 'image':
                        # Create content array with image and text
                        content_array = [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": tool_result.get('mime_type', 'image/jpeg'),
                                    "data": tool_result['data']
                                }
                            },
                            {
                                "type": "text",
                                "text": f"I can now see the image '{tool_result.get('name', 'image')}'. The image has been loaded into my context."
                            }
                        ]

                        tool_result_message = {
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": content_array,
                            "is_error": False
                        }
                    else:
                        # Fallback to normal handling if not proper image format
                        tool_result_message = {
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": json.dumps(tool_result) if not error else error,
                            "is_error": bool(error)
                        }
                else:
                    # Normal handling for other tools
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
        tool_callback: Optional[callable] = None,
        enable_builtin_tools: Optional[List[str]] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Process a prompt with support for multiple tool calls in a single response.

        Args:
            prompt: User prompt
            conversation_history: Previous messages
            tools: Custom tools list
            tool_callback: Callback for custom tool execution
            enable_builtin_tools: List of built-in tools to enable ('web_fetch', 'web_search', 'text_editor')
        """
        messages = conversation_history + [{"role": "user", "content": prompt}]
        new_history = messages.copy()
        final_response = ""
        iteration = 0

        # Configure built-in tools if requested
        extra_headers = None
        all_tools = tools.copy() if tools else []

        if enable_builtin_tools:
            # Get headers for built-in tools
            extra_headers = self.builtin_tools.get_api_headers(enable_builtin_tools)
            print(f"[INFO] Built-in tools enabled: {enable_builtin_tools}")

            # Add built-in tool configurations
            builtin_configs = self.builtin_tools.get_tools_config(
                enable_builtin_tools,
                self.model
            )
            # print(f"[DEBUG] Built-in tool configs: {json.dumps(builtin_configs, indent=2)}")
            all_tools.extend(builtin_configs)
            self.builtin_tools_enabled = enable_builtin_tools

        try:
            while True:
                iteration += 1

                # Log if we're in a long tool-calling chain
                if iteration > 50 and iteration % 10 == 0:
                    print(f"Note: Processing iteration {iteration} of tool calls...")

                # Make API call with retry logic - this now handles the entire stream processing
                content_blocks = self._make_api_call_with_retry(new_history, all_tools, extra_headers)

                # Build and append assistant message
                assistant_message = self._build_assistant_message(content_blocks)
                new_history.append(assistant_message)

                # Process any tool calls and collect text
                tool_results, text_response = self._process_tool_calls(
                    content_blocks,
                    tool_callback
                )

                # Handle built-in text editor tool responses if needed
                for i, block in enumerate(content_blocks):
                    if isinstance(block, ToolUseBlock) and block.name == 'str_replace_based_edit_tool':
                        # This is a client-side built-in tool that needs handling
                        result = self.builtin_tools.handle_tool_use({
                            'type': 'tool_use',
                            'id': block.id,
                            'name': block.name,
                            'input': block.input
                        })
                        # Add to tool results if not already processed
                        if not any(r.get('tool_use_id') == block.id for r in tool_results):
                            tool_results.append(result)

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
        self.original_model = model  # Update original model as well

    def set_max_tokens(self, max_tokens: int):
        self.max_tokens = max_tokens

    def reload_system_prompt(self):
        """Reload the system prompt from file."""
        self.system_prompt = self._load_system_prompt()
        print("System prompt reloaded successfully.")

    def configure_retry(
        self,
        max_backoff: Optional[float] = None,
        initial_backoff: Optional[float] = None,
        backoff_multiplier: Optional[float] = None,
        fallback_retry_count: Optional[int] = None,
        backup_model: Optional[str] = None
    ):
        """Configure retry settings for API calls.

        Args:
            max_backoff: Maximum backoff duration in seconds
            initial_backoff: Initial backoff duration in seconds
            backoff_multiplier: Exponential multiplier for backoff
            fallback_retry_count: Number of retries before switching to backup model
            backup_model: Backup model to use after fallback_retry_count retries
        """
        if max_backoff is not None:
            self.max_backoff = max_backoff
        if initial_backoff is not None:
            self.initial_backoff = initial_backoff
        if backoff_multiplier is not None:
            self.backoff_multiplier = backoff_multiplier
        if fallback_retry_count is not None:
            self.fallback_retry_count = fallback_retry_count
        if backup_model is not None:
            self.backup_model = backup_model

    def reset_model(self):
        """Reset to original model (useful after fallback to backup model)."""
        self.model = self.original_model
        self.using_backup_model = False
        print(f"{Fore.GREEN}✓ Model reset to: {self.model}{Style.RESET_ALL}")

    def get_current_model(self) -> str:
        """Get the currently active model."""
        return self.backup_model if self.using_backup_model else self.model

    def is_using_backup_model(self) -> bool:
        """Check if currently using backup model."""
        return self.using_backup_model
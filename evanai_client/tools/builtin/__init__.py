"""
Anthropic Built-in Tools Package

This package contains handlers for Anthropic's official built-in tools.
These are not custom tools but executors/handlers for tools provided
directly by Anthropic's API.

Available tools:
- TextEditorTool: Handles text editor commands (view, str_replace, create, insert, undo_edit)
- WebFetchTool: Handles web content fetching results
- WebSearchTool: Handles web search results with citations
"""

from .text_editor import TextEditorTool
from .web_fetch import WebFetchTool
from .web_search import WebSearchTool
from .api_integration import BuiltinToolsIntegration

__all__ = [
    'TextEditorTool',
    'WebFetchTool',
    'WebSearchTool',
    'BuiltinToolsIntegration'
]

# Tool type identifiers as used in Anthropic's API
TOOL_TYPES = {
    'text_editor': 'str_replace_editor',  # or 'str_replace_based_edit_tool'
    'web_fetch': 'web_fetch_20250910',
    'web_search': 'web_search_20250305'
}


def get_builtin_tool(tool_name: str, **kwargs):
    """
    Get a built-in tool handler by name.

    Args:
        tool_name: Name of the tool ('text_editor', 'web_fetch', 'web_search')
        **kwargs: Arguments to pass to the tool constructor

    Returns:
        Tool handler instance

    Raises:
        ValueError: If tool_name is not found
    """
    tools = {
        'text_editor': TextEditorTool,
        'web_fetch': WebFetchTool,
        'web_search': WebSearchTool
    }

    if tool_name not in tools:
        raise ValueError(f"Unknown built-in tool: {tool_name}. Available: {list(tools.keys())}")

    return tools[tool_name](**kwargs)

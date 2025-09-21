"""
EvanAI Tools Package

Collection of tools that can be used by Claude agents.
"""

from .weather_tool import WeatherToolProvider
from .file_system_tool import FileSystemToolProvider
from .upload_tool import UploadToolProvider
from .asset_tool import AssetToolProvider
from .view_photo_tool import ViewPhotoToolProvider
from .write_tool import WriteToolProvider
from .bash_tool import BashToolProvider
from .zsh_tool import ZshToolProvider

__all__ = [
    'WeatherToolProvider',
    'FileSystemToolProvider',
    'UploadToolProvider',
    'AssetToolProvider',
    'ViewPhotoToolProvider',
    'WriteToolProvider',
    'BashToolProvider',
    'ZshToolProvider'
]

# Tool registry for easy access
AVAILABLE_TOOLS = {
    'weather': WeatherToolProvider,
    'file_system': FileSystemToolProvider,
    'upload': UploadToolProvider,
    'asset': AssetToolProvider,
    'view_photo': ViewPhotoToolProvider,
    'write': WriteToolProvider,
    'bash': BashToolProvider,
    'zsh': ZshToolProvider
}


def get_tool_provider(tool_name: str, **kwargs):
    """
    Get a tool provider by name.

    Args:
        tool_name: Name of the tool provider
        **kwargs: Arguments to pass to the provider constructor

    Returns:
        Tool provider instance

    Raises:
        ValueError: If tool_name is not found
    """
    if tool_name not in AVAILABLE_TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}. Available tools: {list(AVAILABLE_TOOLS.keys())}")

    provider_class = AVAILABLE_TOOLS[tool_name]
    return provider_class(**kwargs)


def list_available_tools():
    """List all available tool providers."""
    return list(AVAILABLE_TOOLS.keys())
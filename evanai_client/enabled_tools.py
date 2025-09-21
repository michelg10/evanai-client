"""
Tool enablement configuration for EvanAI Client.

Simply comment out any tools you don't want to enable.
Import the tool providers you want to use and add them to ENABLED_TOOLS.
"""

# Core system tools
from .tools.file_system_tool import FileSystemToolProvider
from .tools.upload_tool import UploadToolProvider
from .tools.memory_tool import MemoryToolProvider

# Shell and command execution
# from .tools.bash_tool import BashToolProvider
# from .tools.zsh_tool import ZshToolProvider
from .tools.container_zsh_tool import ContainerZshToolProvider

# Media and conversion tools
from .tools.view_photo_tool import ViewPhotoToolProvider

# Development and analysis tools
from .tools.claude_code_analyzer import ClaudeCodeAnalyzerProvider
# from .tools.self_analysis_tool import SelfAnalysisToolProvider

# System integration
from .tools.shortcuts_tools import ShortcutsToolProvider
# from .tools.overlay_tool import OverlayToolProvider


ENABLED_TOOLS = [
    # Core system tools
    FileSystemToolProvider,      # File operations (read, write, list)
    UploadToolProvider,          # Upload files to user
    MemoryToolProvider,          # Remember facts about users

    # Shell and command execution
    # BashToolProvider,           # Linux container bash execution
    # ZshToolProvider,            # ZSH shell execution
    ContainerZshToolProvider,    # Container-based ZSH execution

    # Media and conversion tools
    ViewPhotoToolProvider,      # View and analyze images

    # Development and analysis tools
    ClaudeCodeAnalyzerProvider,  # Analyze code with Claude
    # SelfAnalysisToolProvider,    # Self-analysis and debugging (disabled - use natural tool flow)

    # System integration
    ShortcutsToolProvider,       # macOS Shortcuts integration
    # OverlayToolProvider,         # Fullscreen overlay display
]
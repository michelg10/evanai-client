"""
Overlay configuration for EvanAI Client.
Customize the overlay appearance and content.
"""
from typing import Optional, Dict, Any
from pathlib import Path


class OverlayConfig:
    """Configuration for the fullscreen overlay display."""

    # Default configuration
    _config = {
        'display_mode': 'text',  # 'text', 'icon', or 'custom'
        'title': 'EvanAI',
        'subtitle': 'is working',
        'title_color': '#4A90E2',
        'subtitle_color': '#B0C4DE',
        'background_color': '#0a0e27',
        'title_font_size': 96,
        'subtitle_font_size': 48,
        'show_animation': True,
        'animation_speed': 600,  # milliseconds
        'icon_path': None,  # Path to custom icon
        'custom_content': None,  # For advanced customization
    }

    @classmethod
    def set_display_mode(cls, mode: str):
        """Set display mode: 'text', 'icon', or 'custom'."""
        if mode in ['text', 'icon', 'custom']:
            cls._config['display_mode'] = mode

    @classmethod
    def set_text(cls, title: str = None, subtitle: str = None):
        """Set the text to display in the overlay."""
        if title is not None:
            cls._config['title'] = title
        if subtitle is not None:
            cls._config['subtitle'] = subtitle

    @classmethod
    def set_colors(cls, title_color: str = None, subtitle_color: str = None,
                   background_color: str = None):
        """Set colors for the overlay."""
        if title_color:
            cls._config['title_color'] = title_color
        if subtitle_color:
            cls._config['subtitle_color'] = subtitle_color
        if background_color:
            cls._config['background_color'] = background_color

    @classmethod
    def set_icon(cls, icon_path: str):
        """Set a custom icon to display."""
        path = Path(icon_path)
        if path.exists():
            cls._config['icon_path'] = str(path)
            cls._config['display_mode'] = 'icon'
            return True
        return False

    @classmethod
    def set_custom_content(cls, content: Dict[str, Any]):
        """Set completely custom content for advanced users."""
        cls._config['custom_content'] = content
        cls._config['display_mode'] = 'custom'

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get the current configuration."""
        return cls._config.copy()

    @classmethod
    def reset(cls):
        """Reset to default configuration."""
        cls._config = {
            'display_mode': 'text',
            'title': 'EvanAI',
            'subtitle': 'is working',
            'title_color': '#4A90E2',
            'subtitle_color': '#B0C4DE',
            'background_color': '#0a0e27',
            'title_font_size': 96,
            'subtitle_font_size': 48,
            'show_animation': True,
            'animation_speed': 600,
            'icon_path': None,
            'custom_content': None,
        }


# Convenience functions for easy customization
def set_overlay_text(title: str, subtitle: str = "is working"):
    """Quick function to change overlay text."""
    OverlayConfig.set_text(title, subtitle)


def set_overlay_icon(icon_path: str):
    """Quick function to set an icon for the overlay."""
    return OverlayConfig.set_icon(icon_path)


def set_overlay_theme(theme: str):
    """Apply a predefined theme to the overlay."""
    themes = {
        'default': {
            'title_color': '#4A90E2',
            'subtitle_color': '#B0C4DE',
            'background_color': '#0a0e27',
        },
        'dark': {
            'title_color': '#FFFFFF',
            'subtitle_color': '#CCCCCC',
            'background_color': '#000000',
        },
        'light': {
            'title_color': '#333333',
            'subtitle_color': '#666666',
            'background_color': '#F5F5F5',
        },
        'green': {
            'title_color': '#4CAF50',
            'subtitle_color': '#81C784',
            'background_color': '#1B5E20',
        },
    }

    if theme in themes:
        OverlayConfig.set_colors(**themes[theme])
        return True
    return False
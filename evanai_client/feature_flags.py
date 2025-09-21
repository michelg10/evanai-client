"""
Feature flags for EvanAI Client

This module contains feature flags that can be used to enable/disable
various features during development.
"""

# Enable the bash tool and Linux desktop environment
# Set to False to disable bash tool loading (currently disabled for development)
ENABLE_BASH_TOOL = True

# Enable the zsh tool for terminal commands
# Set to False to disable zsh tool loading
ENABLE_ZSH_TOOL = False

# Enable the HTML to PNG converter tool
# Set to False to disable HTML to PNG conversion
ENABLE_HTML_CONVERTER_TOOL = False

# Enable the model training tool
# Set to False to disable remote model training functionality
ENABLE_MODEL_TRAINING_TOOL = True

# Enable the HTML renderer tool
# Set to False to disable direct HTML to PNG rendering
ENABLE_HTML_RENDERER_TOOL = False

# Add more feature flags as needed
# ENABLE_EXPERIMENTAL_FEATURE = False
# DEBUG_MODE = False
# VERBOSE_LOGGING = False
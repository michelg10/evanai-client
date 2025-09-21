# EvanAI Fullscreen Overlay Feature

A fullscreen overlay that can be:
1. **Automatically triggered** when tools take longer than 3 seconds to execute
2. **Manually controlled** via the overlay tool API (for mobile app integration)

## Implementation

The overlay runs in a separate subprocess to avoid macOS threading limitations. This allows the GUI to run on its own main thread while being triggered from the tool execution timer or API calls.

## Mobile App Control

The overlay can be directly controlled from the mobile app using these tools:

### Tools Available

- **show_overlay** - Display fullscreen overlay with custom text
  - `title` (optional): Main text (default: "EvanAI")
  - `subtitle` (optional): Subtitle text (default: "is working")
  - `theme` (optional): Color theme ("default", "dark", "light", "green")

- **hide_overlay** - Hide the overlay if it's showing

- **update_overlay** - Update content while overlay is showing
  - Same parameters as show_overlay

### Example API Calls

```python
# Show overlay from mobile app
{
    "tool": "show_overlay",
    "parameters": {
        "title": "Processing",
        "subtitle": "your request",
        "theme": "dark"
    }
}

# Hide overlay
{
    "tool": "hide_overlay",
    "parameters": {}
}
```

## Configuration

- **Enable/Disable**: Set `EVANAI_SHOW_OVERLAY=false` to disable the overlay
- **Default**: Enabled (overlay will show after 3 seconds of tool execution)

## Features

- **Automatic Trigger**: Shows after 3 seconds of tool execution
- **Fullscreen Display**: Takes over the entire screen with a dark blue background
- **Icon Support**: Displays `icon.png` if available
- **Easy Dismissal**: Press ESC or click anywhere to dismiss
- **Non-blocking**: Runs in a separate thread, doesn't block tool execution
- **Configurable**: Can be disabled via environment variable

## How It Works

1. When a tool starts executing, a 3-second timer begins
2. If the tool is still running after 3 seconds, the overlay appears
3. The overlay shows either:
   - Your custom `icon.png` (if available)
   - "EvanAI is working..." text (fallback)
4. When the tool completes, the overlay automatically disappears
5. Users can also dismiss it manually with ESC or by clicking

## Configuration

### Enable/Disable
```bash
# Disable overlay
export EVANAI_SHOW_OVERLAY=false

# Enable overlay (default)
export EVANAI_SHOW_OVERLAY=true
```

### Custom Icon
Place your `icon.png` in one of these locations:
- Current working directory: `./icon.png`
- Assets folder: `evanai_client/assets/icon.png`
- Project root: `/path/to/evanai-client/icon.png`

Recommended icon size: 512x512 pixels

### Excluded Tools
Quick tools are automatically excluded from showing the overlay:
- `list_files`
- `get_weather`

## Testing

Run the test script to see the overlay in action:
```bash
.venv/bin/python test_overlay.py
```

## Creating an Icon

Use the provided script to create a placeholder icon:
```bash
.venv/bin/python create_icon.py
```

Or create your own 512x512 PNG image with your desired logo/design.

## Technical Details

- Implemented in `tool_system.py` in the `ToolManager` class
- Uses `tkinter` for the GUI (included with Python on macOS)
- Uses `Pillow` for image handling (needs to be installed)
- Thread-safe with locks to prevent multiple overlays
- Fails silently if dependencies are missing

## Dependencies

Add to your virtual environment:
```bash
pip install Pillow
```

## Troubleshooting

1. **No overlay appears**: Check if `EVANAI_SHOW_OVERLAY` is set to `false`
2. **Text instead of icon**: Make sure `icon.png` exists in one of the expected locations
3. **Can't dismiss overlay**: Press ESC or click anywhere on the screen
4. **ImportError**: Install Pillow with `pip install Pillow`

## Future Improvements

- Progress bar or spinner animation
- Custom messages per tool
- Sound notifications
- Multiple monitor support configuration
- Fade in/out animations
#!/usr/bin/env python3
"""
Standalone overlay display process.
Run as a separate process to avoid macOS threading issues.
"""
import sys
import signal
import platform
import subprocess
from pathlib import Path

# Add parent directory to path to import overlay_config
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import tkinter as tk
    from PIL import Image, ImageTk
except ImportError:
    print("Error: tkinter or PIL not available", file=sys.stderr)
    sys.exit(1)

try:
    from evanai_client.overlay_config import OverlayConfig
    config = OverlayConfig.get_config()
except ImportError:
    # Fallback to default config if import fails
    config = {
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
    }


def create_overlay():
    """Create and display the fullscreen overlay."""
    root = tk.Tk()
    root.title("EvanAI Working")

    # Make it fullscreen and on top
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.configure(bg=config['background_color'])

    # Force window to front on macOS
    root.lift()
    root.attributes('-topmost', True)
    root.focus_force()
    root.update()

    # Additional activation for stubborn window managers
    root.wm_attributes('-topmost', 1)
    root.wm_attributes('-topmost', 0)
    root.wm_attributes('-topmost', 1)  # Toggle to force refresh

    # Get screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Display based on configuration mode
    if config['display_mode'] == 'icon' and config['icon_path']:
        # Icon mode
        try:
            img = Image.open(config['icon_path'])
            target_height = screen_height // 3
            aspect_ratio = img.width / img.height
            target_width = int(target_height * aspect_ratio)
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(img)
            label = tk.Label(root, image=photo, bg=config['background_color'])
            label.image = photo  # Keep reference
            label.pack(expand=True)
        except Exception as e:
            # Fall back to text if icon fails
            config['display_mode'] = 'text'

    if config['display_mode'] == 'text':
        # Text mode (default)
        center_frame = tk.Frame(root, bg=config['background_color'])
        center_frame.pack(expand=True)

        # Main title text
        title_label = tk.Label(
            center_frame,
            text=config['title'],
            font=('SF Pro Display', config['title_font_size'], 'bold'),
            fg=config['title_color'],
            bg=config['background_color']
        )
        title_label.pack()

        # Subtitle with optional animation
        subtitle_label = tk.Label(
            center_frame,
            text=config['subtitle'] + "..." if config['show_animation'] else config['subtitle'],
            font=('SF Pro Display', config['subtitle_font_size']),
            fg=config['subtitle_color'],
            bg=config['background_color']
        )
        subtitle_label.pack(pady=(10, 0))

        # Animation function for dots
        if config['show_animation']:
            dot_count = 0
            def animate_dots():
                nonlocal dot_count
                dot_count = (dot_count % 3) + 1
                dots = "." * dot_count
                spaces = " " * (3 - dot_count)  # Keep consistent width
                subtitle_label.config(text=f"{config['subtitle']}{dots}{spaces}")
                root.after(config['animation_speed'], animate_dots)

            # Start the animation
            animate_dots()

    elif config['display_mode'] == 'custom' and config.get('custom_content'):
        # Custom mode for advanced users
        # This would need to be implemented based on specific requirements
        pass

    # Add subtitle with better positioning
    subtitle = tk.Label(
        root,
        text="Press ESC or click to dismiss",
        font=('SF Pro Display', 20),
        fg='#6B7280',  # Subtle gray
        bg='#0a0e27'
    )
    subtitle.pack(side='bottom', pady=50)

    # ESC to close
    root.bind('<Escape>', lambda e: root.quit())

    # Also close on click
    root.bind('<Button-1>', lambda e: root.quit())

    # Handle SIGTERM gracefully
    def handle_term(signum, frame):
        root.quit()

    signal.signal(signal.SIGTERM, handle_term)

    # macOS-specific: Activate Python app to bring window to front
    if platform.system() == 'Darwin':
        try:
            # Use AppleScript to activate Python and bring to front
            subprocess.run(['osascript', '-e', 'tell application "Python" to activate'],
                         capture_output=True, timeout=1)
        except:
            pass

    # Final activation before mainloop
    root.deiconify()
    root.lift()
    root.attributes('-topmost', True)
    root.focus_force()
    root.update_idletasks()
    root.update()

    # Schedule another activation attempt after window is fully loaded
    def ensure_visible():
        root.lift()
        root.focus_force()
        root.attributes('-topmost', True)
        # Try grab for 100ms to ensure visibility
        try:
            root.grab_set_global()
            root.after(100, root.grab_release)
        except:
            pass

    root.after(100, ensure_visible)

    # Run the GUI
    root.mainloop()


if __name__ == "__main__":
    try:
        create_overlay()
    except KeyboardInterrupt:
        pass
    sys.exit(0)
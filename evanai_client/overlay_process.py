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

try:
    import tkinter as tk
    from PIL import Image, ImageTk
except ImportError:
    print("Error: tkinter or PIL not available", file=sys.stderr)
    sys.exit(1)


def create_overlay():
    """Create and display the fullscreen overlay."""
    root = tk.Tk()
    root.title("EvanAI Working")

    # Make it fullscreen and on top
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.configure(bg='#0a0e27')  # Dark blue background

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

    # Try to load icon.png from various locations
    icon_paths = [
        Path('icon.png'),  # Current directory
        Path(__file__).parent / 'assets' / 'icon.png',  # Assets folder
        Path(__file__).parent.parent / 'icon.png',  # Parent directory
    ]

    icon_loaded = False
    for icon_path in icon_paths:
        if icon_path.exists():
            try:
                # Load and resize image
                img = Image.open(icon_path)
                # Scale to 1/3 of screen height while maintaining aspect ratio
                target_height = screen_height // 3
                aspect_ratio = img.width / img.height
                target_width = int(target_height * aspect_ratio)
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

                photo = ImageTk.PhotoImage(img)
                label = tk.Label(root, image=photo, bg='#0a0e27')
                label.image = photo  # Keep reference
                label.pack(expand=True)
                icon_loaded = True
                break
            except Exception as e:
                print(f"Error loading icon: {e}", file=sys.stderr)

    # Create main text label with nice typography
    if not icon_loaded:
        # Create a frame for centering content
        center_frame = tk.Frame(root, bg='#0a0e27')
        center_frame.pack(expand=True)

        # Main "EvanAI" text with larger, bold font
        evan_label = tk.Label(
            center_frame,
            text="EvanAI",
            font=('SF Pro Display', 96, 'bold'),
            fg='#4A90E2',  # Nice blue color
            bg='#0a0e27'
        )
        evan_label.pack()

        # "is working..." text with animated dots
        working_label = tk.Label(
            center_frame,
            text="is working...",
            font=('SF Pro Display', 48),
            fg='#B0C4DE',  # Lighter blue-gray
            bg='#0a0e27'
        )
        working_label.pack(pady=(10, 0))

        # Animation function for dots
        dot_count = 0
        def animate_dots():
            nonlocal dot_count
            dot_count = (dot_count % 3) + 1
            dots = "." * dot_count
            spaces = " " * (3 - dot_count)  # Keep consistent width
            working_label.config(text=f"is working{dots}{spaces}")
            root.after(600, animate_dots)  # Update every 600ms

        # Start the animation
        animate_dots()

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
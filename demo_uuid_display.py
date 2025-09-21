#!/usr/bin/env python3
"""Demo script showing how the conversation UUID will appear in the debug interface."""

from colorama import Fore, Style

def show_debug_interface_preview():
    print("\n" + "="*60)
    print(f"{Fore.CYAN}Debug Interface - Conversation UUID Display Preview{Style.RESET_ALL}")
    print("="*60)

    # Simulate the conversation header
    print("\n┌─────────────────────────────────────────────────────────────┐")
    print(f"│ 💬 Conversation  {Fore.GREEN}UUID: debug-session-1758414333021{Style.RESET_ALL}   │ 0 messages")
    print("├─────────────────────────────────────────────────────────────┤")
    print("│                                                             │")
    print("│              [Conversation Messages Area]                  │")
    print("│                                                             │")
    print("└─────────────────────────────────────────────────────────────┘")

    print(f"\n{Fore.YELLOW}Features:{Style.RESET_ALL}")
    print("✓ UUID displayed in conversation header")
    print("✓ Updates automatically when conversation resets")
    print("✓ Styled in green to match the interface theme")
    print("✓ Compact display that doesn't clutter the UI")

    print(f"\n{Fore.CYAN}UUID Format:{Style.RESET_ALL}")
    print("  debug-session-[timestamp]")
    print("  Example: debug-session-1758414333021")

    print(f"\n{Fore.GREEN}Benefits:{Style.RESET_ALL}")
    print("• Easy tracking of conversation sessions")
    print("• Clear identification for debugging")
    print("• Helps correlate logs with specific sessions")
    print("• Visible confirmation when conversation resets")

    print(f"\n{Fore.YELLOW}How to View:{Style.RESET_ALL}")
    print("1. Start debug server: evanai-client debug")
    print("2. Open browser: http://localhost:8069")
    print("3. UUID appears in conversation header")
    print("4. Click 'Reset Conversation' to see it change")

    print("\n" + "="*60)

if __name__ == "__main__":
    show_debug_interface_preview()
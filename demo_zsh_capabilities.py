#!/usr/bin/env python3
"""Demo script showing ZSH tool capabilities."""

from colorama import Fore, Style

def show_zsh_capabilities():
    """Display the capabilities of the ZSH tool."""

    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🚀 ZSH Tool - Persistent macOS Shell Access{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

    print(f"\n{Fore.GREEN}✅ Key Features:{Style.RESET_ALL}")
    print("• Persistent ZSH session per conversation")
    print("• Full access to macOS environment")
    print("• State persists across commands")
    print("• Configurable timeout (default 3 seconds)")
    print("• Automatic session management")

    print(f"\n{Fore.YELLOW}📝 Example Usage:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}────────────────────────────────────────{Style.RESET_ALL}")

    print("\n1. Navigate and explore:")
    print(f'   {Fore.GREEN}zsh("ls ~"){Style.RESET_ALL}                    # List home directory')
    print(f'   {Fore.GREEN}zsh("cd ~/Desktop"){Style.RESET_ALL}            # Change to Desktop')
    print(f'   {Fore.GREEN}zsh("pwd"){Style.RESET_ALL}                      # Shows: /Users/you/Desktop')
    print(f'   {Fore.GREEN}zsh("ls"){Style.RESET_ALL}                       # Lists Desktop files')

    print("\n2. State persistence demonstration:")
    print(f'   {Fore.GREEN}zsh("export MY_VAR=\'Hello\'"){Style.RESET_ALL}   # Set environment variable')
    print(f'   {Fore.GREEN}zsh("echo $MY_VAR"){Style.RESET_ALL}             # Shows: Hello (persists!)')
    print(f'   {Fore.GREEN}zsh("cd /tmp"){Style.RESET_ALL}                  # Change directory')
    print(f'   {Fore.GREEN}zsh("pwd"){Style.RESET_ALL}                      # Shows: /tmp (persisted!)')

    print("\n3. System operations:")
    print(f'   {Fore.GREEN}zsh("date"){Style.RESET_ALL}                     # Current date/time')
    print(f'   {Fore.GREEN}zsh("whoami"){Style.RESET_ALL}                   # Current user')
    print(f'   {Fore.GREEN}zsh("df -h"){Style.RESET_ALL}                    # Disk usage')
    print(f'   {Fore.GREEN}zsh("ps aux | grep python"){Style.RESET_ALL}    # Running Python processes')

    print("\n4. File operations:")
    print(f'   {Fore.GREEN}zsh("touch test.txt"){Style.RESET_ALL}          # Create file')
    print(f'   {Fore.GREEN}zsh("echo \'data\' > file.txt"){Style.RESET_ALL}  # Write to file')
    print(f'   {Fore.GREEN}zsh("cat file.txt"){Style.RESET_ALL}             # Read file')
    print(f'   {Fore.GREEN}zsh("rm file.txt"){Style.RESET_ALL}              # Delete file')

    print("\n5. With custom timeout:")
    print(f'   {Fore.GREEN}zsh("sleep 1", timeout=2){Style.RESET_ALL}     # OK: completes in time')
    print(f'   {Fore.GREEN}zsh("sleep 5", timeout=2){Style.RESET_ALL}     # Timeout after 2 seconds')
    print(f'   {Fore.GREEN}zsh("find / -name x", timeout=10){Style.RESET_ALL}  # Long search with 10s timeout')

    print(f"\n{Fore.YELLOW}🔄 Session Persistence Flow:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}────────────────────────────────────────{Style.RESET_ALL}")
    print("1️⃣  First command → Creates ZSH session")
    print("2️⃣  cd ~/Desktop  → Changes directory")
    print("3️⃣  ls            → Lists Desktop (state persisted!)")
    print("4️⃣  mkdir test    → Creates dir in Desktop")
    print("5️⃣  cd test       → Enters test directory")
    print("6️⃣  pwd           → Shows ~/Desktop/test")
    print("✨ All in the same persistent session!")

    print(f"\n{Fore.YELLOW}⚡ Differences from console_tool:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}────────────────────────────────────────{Style.RESET_ALL}")

    print(f"\n{Fore.GREEN}ZSH Tool (Simple):{Style.RESET_ALL}")
    print("• Single command: zsh()")
    print("• Auto session management")
    print("• One session per conversation")
    print("• ZSH shell (macOS default)")

    print(f"\n{Fore.CYAN}Console Tool (Complex):{Style.RESET_ALL}")
    print("• Multiple commands: start_session(), send_to_session(), etc.")
    print("• Manual session management")
    print("• Multiple named sessions")
    print("• Bash shell")

    print(f"\n{Fore.RED}⚠️  Important Notes:{Style.RESET_ALL}")
    print("• Full access to your macOS system")
    print("• Commands run with your user permissions")
    print("• Session dies when conversation ends")
    print("• Not for interactive programs (vim, etc.)")

    print(f"\n{Fore.GREEN}✅ Ready to use in the EvanAI system!{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

if __name__ == "__main__":
    show_zsh_capabilities()
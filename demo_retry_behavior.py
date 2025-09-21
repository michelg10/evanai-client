#!/usr/bin/env python3
"""Demo script to show the retry behavior with backup model."""

import time
from colorama import Fore, Style

def simulate_retry_behavior():
    """Simulate the retry behavior to show what users will see."""

    print(f"\n{Fore.CYAN}Simulating API overload scenario...{Style.RESET_ALL}\n")

    # Primary model retries
    print(f"{Fore.RED}API call failed: Error code: 529, error type: overloaded_error{Style.RESET_ALL}")

    for i in range(1, 11):
        backoff = min(0.1 * (2 ** (i-1)), 3.0)
        print(f"{Fore.GREEN}[PRIMARY MODEL]{Style.RESET_ALL} Retry {i} - Waiting {backoff:.2f} seconds...")
        time.sleep(0.3)  # Simulate wait (shortened for demo)

    # Switch to backup model
    print(f"\n{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}⚠️  SWITCHING TO BACKUP MODEL{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}   Primary model failed 10 times{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}   Now using: claude-sonnet-4-20250514{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}   Will continue retrying indefinitely with backup model{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'='*70}{Style.RESET_ALL}\n")

    # Backup model retries
    for i in range(11, 16):
        backoff = min(0.1 * (2 ** ((i-11) % 5)), 3.0)  # Reset backoff after switch
        print(f"{Fore.CYAN}[BACKUP MODEL]{Style.RESET_ALL} Retry {i} - Waiting {backoff:.2f} seconds...")
        time.sleep(0.3)  # Simulate wait (shortened for demo)

    # Success with backup model
    print(f"{Fore.GREEN}✓ Backup model responded successfully{Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}Actual behavior:{Style.RESET_ALL}")
    print("• Primary model retries 10 times with exponential backoff")
    print("• After 10 failures, switches to backup model automatically")
    print("• Backup model retries indefinitely until successful")
    print("• Maximum backoff time: 3 seconds")
    print("• No retry limit - will continue forever if needed")

    print(f"\n{Fore.YELLOW}Configuration:{Style.RESET_ALL}")
    print(f"  Primary Model: claude-opus-4-1-20250805")
    print(f"  Backup Model: claude-sonnet-4-20250514")
    print(f"  Fallback After: 10 retries")
    print(f"  Max Backoff: 3.0 seconds")
    print(f"  Initial Backoff: 0.1 seconds")

if __name__ == "__main__":
    simulate_retry_behavior()
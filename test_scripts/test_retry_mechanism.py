#!/usr/bin/env python3
"""Test script to demonstrate Claude API retry mechanism."""

import os
import sys

try:
    from dotenv import load_dotenv
except ImportError:
    # If dotenv is not available, create a dummy function
    def load_dotenv():
        pass

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evanai_client.claude_agent import ClaudeAgent

def test_retry_configuration():
    """Test the retry configuration and display settings."""
    print("Testing Claude API Retry Mechanism")
    print("=" * 50)

    # Load environment variables
    load_dotenv()

    # Create Claude agent instance
    agent = ClaudeAgent()

    # Display current configuration
    print("\nCurrent Retry Configuration:")
    print(f"  Max Backoff: {agent.max_backoff}s")
    print(f"  Initial Backoff: {agent.initial_backoff}s")
    print(f"  Backoff Multiplier: {agent.backoff_multiplier}x")
    print(f"  Fallback Retry Count: {agent.fallback_retry_count}")
    print(f"  Default Model: {agent.model}")
    print(f"  Backup Model: {agent.backup_model}")

    # Test custom configuration
    print("\nTesting Custom Configuration:")
    agent.configure_retry(
        max_backoff=5.0,
        initial_backoff=0.5,
        backoff_multiplier=3.0,
        fallback_retry_count=5,
        backup_model="claude-3-haiku-20240307"
    )

    print(f"  New Max Backoff: {agent.max_backoff}s")
    print(f"  New Initial Backoff: {agent.initial_backoff}s")
    print(f"  New Backoff Multiplier: {agent.backoff_multiplier}x")
    print(f"  New Fallback Retry Count: {agent.fallback_retry_count}")
    print(f"  New Backup Model: {agent.backup_model}")

    print("\n✅ Retry mechanism configured successfully!")
    print("\nThe system will now automatically:")
    print("1. Retry failed API calls with exponential backoff")
    print(f"2. Start with {agent.initial_backoff}s delay, increasing up to {agent.max_backoff}s")
    print(f"3. After {agent.fallback_retry_count} retries, switch to backup model: {agent.backup_model}")
    print("4. Continue retrying indefinitely until successful")

    print("\nEnvironment Variable Configuration:")
    print("You can also configure retry settings via environment variables:")
    print("  CLAUDE_MAX_BACKOFF=3")
    print("  CLAUDE_INITIAL_BACKOFF=0.1")
    print("  CLAUDE_BACKOFF_MULTIPLIER=2")
    print("  CLAUDE_FALLBACK_RETRY_COUNT=10")
    print("  CLAUDE_BACKUP_MODEL=claude-sonnet-4-20250514")

if __name__ == "__main__":
    test_retry_configuration()
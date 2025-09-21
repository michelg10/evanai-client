#!/usr/bin/env python3
"""
Example integration showing how to use the agent environment
with a Claude-based agent that has Bash tool access.

This demonstrates how each agent gets an isolated environment
with only /mnt writable.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from agent_manager import AgentManager


class ClaudeAgentEnvironment:
    """
    Wrapper for Claude agents to execute Bash commands in isolated environments.
    Each agent instance gets its own container with unique working directory.
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        runtime_dir: str = "./evanai-runtime",
        memory_limit: str = "2g",
        cpu_limit: float = 2.0,
        auto_cleanup: bool = True
    ):
        """
        Initialize a Claude agent environment.

        Args:
            agent_id: Unique identifier for this agent
            runtime_dir: Base directory for runtime data
            memory_limit: Memory limit for container
            cpu_limit: CPU limit for container
            auto_cleanup: Automatically cleanup on exit
        """
        self.manager = AgentManager(runtime_dir=runtime_dir)
        self.auto_cleanup = auto_cleanup

        # Create the agent container
        agent_info = self.manager.create_agent(
            agent_id=agent_id,
            memory_limit=memory_limit,
            cpu_limit=cpu_limit,
            detached=True,
            auto_remove=False  # We'll handle cleanup
        )

        self.agent_id = agent_info["id"]
        self.work_dir = Path(agent_info["work_dir"])

        print(f"Created agent environment: {self.agent_id}")
        print(f"Working directory: {self.work_dir}")

    def execute_bash(self, command: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute a bash command in the agent's environment.

        This is the primary tool interface for Claude agents.

        Args:
            command: Bash command to execute
            timeout: Optional timeout in seconds

        Returns:
            Dictionary with exit_code, stdout, and stderr
        """
        try:
            exit_code, stdout, stderr = self.manager.execute_command(
                self.agent_id,
                command,
                timeout=timeout
            )

            return {
                "success": exit_code == 0,
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "command": command,
                "agent_id": self.agent_id
            }

        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "command": command,
                "agent_id": self.agent_id
            }

    def upload_file(self, local_path: str, remote_name: str) -> bool:
        """
        Upload a file to the agent's /mnt directory.

        Args:
            local_path: Path to local file
            remote_name: Name for file in /mnt

        Returns:
            True if successful
        """
        try:
            dest = self.work_dir / remote_name
            with open(local_path, 'rb') as src:
                with open(dest, 'wb') as dst:
                    dst.write(src.read())
            return True
        except Exception as e:
            print(f"Upload failed: {e}")
            return False

    def download_file(self, remote_name: str, local_path: str) -> bool:
        """
        Download a file from the agent's /mnt directory.

        Args:
            remote_name: Name of file in /mnt
            local_path: Path to save locally

        Returns:
            True if successful
        """
        try:
            src = self.work_dir / remote_name
            with open(src, 'rb') as src_file:
                with open(local_path, 'wb') as dst:
                    dst.write(src_file.read())
            return True
        except Exception as e:
            print(f"Download failed: {e}")
            return False

    def get_logs(self, tail: int = 100) -> str:
        """Get recent logs from the agent container."""
        return self.manager.get_logs(self.agent_id, tail=tail)

    def cleanup(self, remove_data: bool = True):
        """Clean up the agent environment."""
        print(f"Cleaning up agent: {self.agent_id}")
        self.manager.remove_agent(self.agent_id, remove_data=remove_data)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup if configured."""
        if self.auto_cleanup:
            self.cleanup()

    def __del__(self):
        """Destructor - ensure cleanup."""
        if hasattr(self, 'auto_cleanup') and self.auto_cleanup:
            try:
                self.cleanup()
            except:
                pass  # Ignore errors during cleanup


# Example usage scenarios
def example_basic_usage():
    """Basic usage example."""
    print("=== Basic Usage Example ===\n")

    # Create an agent environment
    agent = ClaudeAgentEnvironment(agent_id="example-basic")

    # Execute bash commands
    result = agent.execute_bash("echo 'Hello from agent environment!'")
    print(f"Command output: {result['stdout']}")

    # Work with files in /mnt
    result = agent.execute_bash("""
        cd /mnt
        echo 'This is a test file' > test.txt
        cat test.txt
    """)
    print(f"File content: {result['stdout']}")

    # Show environment info
    result = agent.execute_bash("pwd && ls -la")
    print(f"Working directory:\n{result['stdout']}")

    # Cleanup
    agent.cleanup()


def example_data_processing():
    """Example of data processing agent."""
    print("\n=== Data Processing Example ===\n")

    with ClaudeAgentEnvironment(agent_id="data-processor", memory_limit="4g") as agent:
        # Create a Python script in the agent
        script = """
import pandas as pd
import numpy as np

# Generate sample data
data = {
    'id': range(1, 101),
    'value': np.random.randn(100),
    'category': np.random.choice(['A', 'B', 'C'], 100)
}

df = pd.DataFrame(data)

# Process data
summary = df.groupby('category')['value'].agg(['mean', 'std', 'count'])
summary.to_csv('/mnt/summary.csv')

print("Data processing complete!")
print(summary)
"""

        # Write script to agent
        result = agent.execute_bash(f"cat > /mnt/process.py << 'EOF'\n{script}\nEOF")

        # Execute the script
        result = agent.execute_bash("cd /mnt && python3 process.py")
        print(f"Processing output:\n{result['stdout']}")

        # Read the results
        result = agent.execute_bash("cat /mnt/summary.csv")
        print(f"\nSummary CSV:\n{result['stdout']}")


def example_web_scraping():
    """Example of web scraping agent."""
    print("\n=== Web Scraping Example ===\n")

    with ClaudeAgentEnvironment(agent_id="web-scraper") as agent:
        # Install additional requirements if needed
        # (Note: In production, these would be in the base image)
        agent.execute_bash("pip3 install --user requests beautifulsoup4 2>/dev/null")

        # Create scraping script
        scraper = """
import requests
from bs4 import BeautifulSoup
import json

# Scrape a simple website
response = requests.get('https://httpbin.org/html')
soup = BeautifulSoup(response.content, 'html.parser')

# Extract data
data = {
    'title': soup.title.string if soup.title else 'No title',
    'paragraphs': len(soup.find_all('p')),
    'links': len(soup.find_all('a'))
}

# Save results
with open('/mnt/scrape_results.json', 'w') as f:
    json.dump(data, f, indent=2)

print(json.dumps(data, indent=2))
"""

        # Write and execute scraper
        agent.execute_bash(f"cat > /mnt/scraper.py << 'EOF'\n{scraper}\nEOF")
        result = agent.execute_bash("cd /mnt && python3 scraper.py")
        print(f"Scraping results:\n{result['stdout']}")


def example_parallel_agents():
    """Example of running multiple agents in parallel."""
    print("\n=== Parallel Agents Example ===\n")

    agents = []

    # Create multiple agents
    for i in range(3):
        agent = ClaudeAgentEnvironment(agent_id=f"worker-{i}")
        agents.append(agent)

    # Give each agent a task
    for i, agent in enumerate(agents):
        command = f"""
        echo 'Agent {i} starting work...'
        sleep 2
        echo 'Result from agent {i}: $((RANDOM % 100))' > /mnt/result.txt
        cat /mnt/result.txt
        """
        result = agent.execute_bash(command)
        print(f"Agent {i}: {result['stdout'].strip()}")

    # Cleanup all agents
    for agent in agents:
        agent.cleanup()


def example_document_processing():
    """Example of document processing agent."""
    print("\n=== Document Processing Example ===\n")

    with ClaudeAgentEnvironment(agent_id="doc-processor") as agent:
        # Create a markdown document
        markdown = """
# Sample Document

## Introduction
This is a sample document for processing.

## Data
- Item 1
- Item 2
- Item 3

## Conclusion
Document processing is complete.
"""

        # Write markdown file
        agent.execute_bash(f"cat > /mnt/document.md << 'EOF'\n{markdown}\nEOF")

        # Convert to HTML using pandoc
        result = agent.execute_bash(
            "pandoc /mnt/document.md -o /mnt/document.html"
        )

        if result['success']:
            # Read the HTML
            result = agent.execute_bash("cat /mnt/document.html")
            print("Converted HTML:")
            print(result['stdout'][:500])  # First 500 chars
        else:
            print(f"Conversion failed: {result['stderr']}")


def example_error_handling():
    """Example of error handling."""
    print("\n=== Error Handling Example ===\n")

    with ClaudeAgentEnvironment(agent_id="error-test") as agent:
        # Try to write to read-only filesystem (should fail)
        result = agent.execute_bash("echo 'test' > /etc/test.txt")
        if not result['success']:
            print(f"Expected error - read-only filesystem: {result['stderr'][:100]}")

        # Try to exceed memory (safely)
        result = agent.execute_bash("""
        python3 -c "
try:
    x = [0] * (10**9)  # Try to allocate huge list
except MemoryError:
    print('Memory limit enforced')
"
        """)
        print(f"Memory test: {result['stdout']}")

        # Show that /mnt is still writable
        result = agent.execute_bash("echo 'But /mnt works!' > /mnt/writable.txt && cat /mnt/writable.txt")
        print(f"Writable test: {result['stdout']}")


if __name__ == "__main__":
    # Run examples
    examples = [
        example_basic_usage,
        example_data_processing,
        example_web_scraping,
        example_parallel_agents,
        example_document_processing,
        example_error_handling
    ]

    print("Claude Agent Environment - Integration Examples")
    print("=" * 50)
    print()

    for example in examples:
        try:
            example()
            print()
        except Exception as e:
            print(f"Example failed: {e}")
            print()

    print("All examples completed!")
    print("\nNote: Check ./evanai-runtime/agent-working-directory/ for agent data")
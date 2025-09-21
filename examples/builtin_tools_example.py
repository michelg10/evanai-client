#!/usr/bin/env python3
"""
Example of using Anthropic's built-in tools with EvanAI Client

This example demonstrates how to properly configure and use:
1. Web Search (server-side tool)
2. Web Fetch (server-side tool, beta)
3. Text Editor (client-side tool)

IMPORTANT: 
- Web search requires organization admin to enable it in Console
- Web fetch is in beta and requires the beta header
- Text editor requires implementing file operations
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evanai_client.claude_agent import ClaudeAgent
from evanai_client.tools.builtin import BuiltinToolsIntegration


def example_web_search():
    """
    Example using the web search tool.
    No beta header needed - generally available.
    """
    print("\n" + "="*60)
    print("WEB SEARCH EXAMPLE")
    print("="*60)
    
    # Initialize agent
    agent = ClaudeAgent()
    
    # Prepare conversation
    conversation_history = []
    
    # Enable web search
    response, updated_history = agent.process_prompt(
        prompt="What are the latest developments in quantum computing in 2024?",
        conversation_history=conversation_history,
        tools=[],  # No custom tools
        enable_builtin_tools=['web_search']  # Enable web search
    )
    
    print(f"\nResponse with web search:\n{response}")
    return updated_history


def example_web_fetch():
    """
    Example using the web fetch tool.
    Requires beta header.
    """
    print("\n" + "="*60)
    print("WEB FETCH EXAMPLE (BETA)")
    print("="*60)
    
    # Initialize agent
    agent = ClaudeAgent()
    
    # Prepare conversation
    conversation_history = []
    
    # Enable web fetch with configuration
    response, updated_history = agent.process_prompt(
        prompt="Please analyze the content at https://www.anthropic.com/news/claude-3-5-sonnet",
        conversation_history=conversation_history,
        tools=[],  # No custom tools
        enable_builtin_tools=['web_fetch']  # Enable web fetch
    )
    
    print(f"\nResponse with web fetch:\n{response}")
    return updated_history


def example_text_editor():
    """
    Example using the text editor tool.
    This is a client-side tool that requires implementation.
    """
    print("\n" + "="*60)
    print("TEXT EDITOR EXAMPLE")
    print("="*60)
    
    # Create a test file
    test_file = Path("/tmp/test_example.py")
    test_file.write_text('''
def greet(name):
    prin(f"Hello, {name}!")  # Typo: should be 'print'
    return f"Greeted {name}"

greet("World")
''')
    
    print(f"Created test file: {test_file}")
    print(f"Content:\n{test_file.read_text()}")
    
    # Initialize agent with workspace directory
    agent = ClaudeAgent(workspace_dir="/tmp")
    
    # Prepare conversation
    conversation_history = []
    
    # Enable text editor
    response, updated_history = agent.process_prompt(
        prompt=f"Please fix the typo in {test_file}. The function should print correctly.",
        conversation_history=conversation_history,
        tools=[],  # No custom tools
        enable_builtin_tools=['text_editor']  # Enable text editor
    )
    
    print(f"\nResponse with text editor:\n{response}")
    print(f"\nFile after editing:\n{test_file.read_text()}")
    return updated_history


def example_combined_tools():
    """
    Example using multiple built-in tools together.
    """
    print("\n" + "="*60)
    print("COMBINED TOOLS EXAMPLE")
    print("="*60)
    
    # Initialize agent
    agent = ClaudeAgent(workspace_dir="/tmp")
    
    # Prepare conversation
    conversation_history = []
    
    # Enable multiple tools
    response, updated_history = agent.process_prompt(
        prompt="Search for the latest Python web framework benchmarks, "
               "fetch detailed results from the top result, "
               "and create a summary file at /tmp/benchmark_summary.md",
        conversation_history=conversation_history,
        tools=[],  # No custom tools
        enable_builtin_tools=['web_search', 'web_fetch', 'text_editor']  # Enable all
    )
    
    print(f"\nResponse with combined tools:\n{response}")
    
    summary_file = Path("/tmp/benchmark_summary.md")
    if summary_file.exists():
        print(f"\nCreated summary file content:\n{summary_file.read_text()[:500]}...")
    
    return updated_history


def example_with_configuration():
    """
    Example with detailed tool configuration.
    """
    print("\n" + "="*60)
    print("CONFIGURED TOOLS EXAMPLE")
    print("="*60)
    
    # Initialize the built-in tools integration directly for more control
    builtin_tools = BuiltinToolsIntegration(workspace_dir="/tmp")
    
    # Configure tools with specific settings
    tools_config = builtin_tools.get_tools_config(
        tools=['web_search', 'web_fetch'],
        model='claude-opus-4-1-20250805',
        web_search_config={
            'max_uses': 3,
            'allowed_domains': ['arxiv.org', 'github.com'],
            'user_location': {
                'city': 'San Francisco',
                'region': 'California',
                'country': 'US',
                'timezone': 'America/Los_Angeles'
            }
        },
        web_fetch_config={
            'max_uses': 5,
            'enable_citations': True,
            'max_content_tokens': 50000
        }
    )
    
    # Get required headers
    headers = builtin_tools.get_api_headers(['web_search', 'web_fetch'])
    
    print("Tool configurations:")
    for tool in tools_config:
        print(f"  - {tool['name']}: {tool['type']}")
    
    print(f"\nRequired headers: {headers}")
    
    # Now use with the agent
    agent = ClaudeAgent(workspace_dir="/tmp")
    
    response, updated_history = agent.process_prompt(
        prompt="Find recent machine learning papers on arxiv and analyze one in detail",
        conversation_history=[],
        tools=[],
        enable_builtin_tools=['web_search', 'web_fetch']
    )
    
    print(f"\nResponse:\n{response[:500]}...")
    return updated_history


def main():
    """
    Run examples of using built-in tools.
    """
    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it with: export ANTHROPIC_API_KEY='your-api-key'")
        sys.exit(1)
    
    print("\n" + "#"*60)
    print("# Anthropic Built-in Tools Examples")
    print("#"*60)
    
    # Choose which examples to run
    examples_to_run = [
        # Uncomment the examples you want to run:
        # example_web_search,      # Generally available
        # example_web_fetch,        # Beta - requires header
        example_text_editor,        # Client-side implementation
        # example_combined_tools,   # Multiple tools
        # example_with_configuration,  # Advanced configuration
    ]
    
    for example_func in examples_to_run:
        try:
            example_func()
        except Exception as e:
            print(f"\nError in {example_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "#"*60)
    print("# Examples completed")
    print("#"*60)


if __name__ == "__main__":
    main()

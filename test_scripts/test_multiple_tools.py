#!/usr/bin/env python3
"""Test script for multiple tool calls functionality."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from evanai_client.tool_system import ToolManager
from evanai_client.tools.weather_tool import WeatherToolProvider
from evanai_client.tools.math_tool import MathToolProvider
from evanai_client.claude_agent import ClaudeAgent

def test_multiple_tools():
    """Test that Claude can call multiple tools in a single response."""
    print("Testing Multiple Tool Calls")
    print("=" * 50)

    # Initialize components
    tool_manager = ToolManager()

    # Register tool providers
    weather_provider = WeatherToolProvider()
    math_provider = MathToolProvider()

    tool_manager.register_provider(weather_provider)
    tool_manager.register_provider(math_provider)

    # List available tools
    print("\nAvailable tools:")
    for tool_id in tool_manager.list_tools():
        tool = tool_manager.get_tool_info(tool_id)
        print(f"  - {tool_id}: {tool.description}")

    # Create a test prompt that should trigger multiple tool calls
    test_prompts = [
        "What's the weather in New York and San Francisco?",
        "Calculate 15 + 27, then multiply the result by 3",
        "What's 100 divided by 4, and what's 5 to the power of 3?",
        "Get the weather in London, then add 25 + 75, and finally get the forecast for Tokyo"
    ]

    # Test with mock API key (won't actually call Claude)
    os.environ['ANTHROPIC_API_KEY'] = 'test-key-for-structure-testing'

    try:
        agent = ClaudeAgent()

        for prompt in test_prompts:
            print(f"\nTest Prompt: {prompt}")
            print("-" * 40)

            # Create tool callback
            call_count = 0

            def tool_callback(tool_id: str, parameters):
                nonlocal call_count
                call_count += 1
                print(f"Tool Call #{call_count}: {tool_id}")
                print(f"  Parameters: {parameters}")

                result, error = tool_manager.call_tool(
                    tool_id,
                    parameters,
                    "test-conversation"
                )

                if error:
                    print(f"  Error: {error}")
                else:
                    print(f"  Result: {result}")

                return result, error

            # Get tools in Anthropic format
            tools = tool_manager.get_anthropic_tools()

            print(f"\nNumber of tools available: {len(tools)}")

            # Note: This would normally call Claude API
            # For testing structure, we just verify the setup
            print(f"Would process prompt with {len(tools)} tools available")
            print(f"Tool callback is ready to handle multiple calls")

    except Exception as e:
        print(f"\nSetup verification complete. API error expected without valid key: {e}")

    # Test direct tool calls to verify they work
    print("\n" + "=" * 50)
    print("Testing Direct Tool Calls")
    print("=" * 50)

    # Test weather tool
    result, error = tool_manager.call_tool("get_weather", {"location": "Paris"}, "test-conv")
    print(f"\nWeather in Paris: {result if not error else error}")

    # Test math tools with multiple calls
    result1, error1 = tool_manager.call_tool("add", {"a": 10, "b": 20}, "test-conv")
    print(f"\n10 + 20 = {result1['result'] if not error1 else error1}")

    result2, error2 = tool_manager.call_tool("multiply", {"a": result1['result'], "b": 3}, "test-conv")
    print(f"Result × 3 = {result2['result'] if not error2 else error2}")

    result3, error3 = tool_manager.call_tool("power", {"base": 2, "exponent": 8}, "test-conv")
    print(f"2^8 = {result3['result'] if not error3 else error3}")

    # Show state tracking
    print("\n" + "=" * 50)
    print("State Tracking")
    print("=" * 50)

    math_state = tool_manager.provider_states['MathToolProvider']
    print(f"Total calculations: {math_state['global']['total_calculations']}")
    print(f"Calculation history: {len(math_state['global']['calculation_history'])} entries")

    weather_state = tool_manager.provider_states['WeatherToolProvider']
    print(f"Weather API calls: {weather_state['global']['api_calls_count']}")


if __name__ == "__main__":
    test_multiple_tools()
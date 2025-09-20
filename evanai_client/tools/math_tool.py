"""Math tools for testing multiple tool calls."""

from typing import Dict, List, Any, Optional, Tuple
from ..tool_system import BaseToolSetProvider, Tool, Parameter, ParameterType


class MathToolProvider(BaseToolSetProvider):
    """Provides basic math operations as tools."""

    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """Initialize math tools."""
        tools = [
            Tool(
                id="add",
                name="Add Numbers",
                description="Add two numbers together",
                parameters={
                    "a": Parameter(
                        name="a",
                        type=ParameterType.NUMBER,
                        description="First number",
                        required=True
                    ),
                    "b": Parameter(
                        name="b",
                        type=ParameterType.NUMBER,
                        description="Second number",
                        required=True
                    )
                }
            ),
            Tool(
                id="multiply",
                name="Multiply Numbers",
                description="Multiply two numbers together",
                parameters={
                    "a": Parameter(
                        name="a",
                        type=ParameterType.NUMBER,
                        description="First number",
                        required=True
                    ),
                    "b": Parameter(
                        name="b",
                        type=ParameterType.NUMBER,
                        description="Second number",
                        required=True
                    )
                }
            ),
            Tool(
                id="subtract",
                name="Subtract Numbers",
                description="Subtract the second number from the first",
                parameters={
                    "a": Parameter(
                        name="a",
                        type=ParameterType.NUMBER,
                        description="Number to subtract from",
                        required=True
                    ),
                    "b": Parameter(
                        name="b",
                        type=ParameterType.NUMBER,
                        description="Number to subtract",
                        required=True
                    )
                }
            ),
            Tool(
                id="divide",
                name="Divide Numbers",
                description="Divide the first number by the second",
                parameters={
                    "a": Parameter(
                        name="a",
                        type=ParameterType.NUMBER,
                        description="Dividend",
                        required=True
                    ),
                    "b": Parameter(
                        name="b",
                        type=ParameterType.NUMBER,
                        description="Divisor",
                        required=True
                    )
                }
            ),
            Tool(
                id="power",
                name="Calculate Power",
                description="Raise a number to a power",
                parameters={
                    "base": Parameter(
                        name="base",
                        type=ParameterType.NUMBER,
                        description="Base number",
                        required=True
                    ),
                    "exponent": Parameter(
                        name="exponent",
                        type=ParameterType.NUMBER,
                        description="Exponent",
                        required=True
                    )
                }
            )
        ]

        # Global state to track total calculations
        global_state = {
            "total_calculations": 0,
            "calculation_history": []
        }

        # Per-conversation state empty initially
        per_conversation_state = {}

        return tools, global_state, per_conversation_state

    def call_tool(
        self,
        tool_id: str,
        tool_parameters: Dict[str, Any],
        per_conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """Execute a math tool."""
        # Track calculations
        global_state["total_calculations"] = global_state.get("total_calculations", 0) + 1

        # Track per-conversation calculations
        per_conversation_state.setdefault("calculations", [])

        try:
            if tool_id == "add":
                a = tool_parameters["a"]
                b = tool_parameters["b"]
                result = a + b
                operation = f"{a} + {b} = {result}"

            elif tool_id == "multiply":
                a = tool_parameters["a"]
                b = tool_parameters["b"]
                result = a * b
                operation = f"{a} × {b} = {result}"

            elif tool_id == "subtract":
                a = tool_parameters["a"]
                b = tool_parameters["b"]
                result = a - b
                operation = f"{a} - {b} = {result}"

            elif tool_id == "divide":
                a = tool_parameters["a"]
                b = tool_parameters["b"]
                if b == 0:
                    return None, "Error: Division by zero"
                result = a / b
                operation = f"{a} ÷ {b} = {result}"

            elif tool_id == "power":
                base = tool_parameters["base"]
                exponent = tool_parameters["exponent"]
                result = base ** exponent
                operation = f"{base}^{exponent} = {result}"

            else:
                return None, f"Unknown tool: {tool_id}"

            # Store in history
            per_conversation_state["calculations"].append(operation)
            global_state.setdefault("calculation_history", []).append({
                "tool": tool_id,
                "operation": operation,
                "result": result
            })

            return {
                "result": result,
                "operation": operation,
                "total_calculations": global_state["total_calculations"]
            }, None

        except Exception as e:
            return None, f"Calculation error: {str(e)}"
import random
from typing import Dict, List, Any, Optional, Tuple
from ..tool_system import BaseToolSetProvider, Tool, Parameter, ParameterType


class WeatherToolProvider(BaseToolSetProvider):
    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
        tools = [
            Tool(
                id="get_weather",
                name="Get Weather",
                description="Get the current weather for a specified location",
                parameters={
                    "location": Parameter(
                        name="location",
                        type=ParameterType.STRING,
                        description="The city and state/country to get weather for",
                        required=True
                    ),
                    "units": Parameter(
                        name="units",
                        type=ParameterType.STRING,
                        description="Temperature units (celsius or fahrenheit)",
                        required=False,
                        default="celsius"
                    )
                },
                returns=Parameter(
                    name="weather_data",
                    type=ParameterType.OBJECT,
                    description="Weather information for the location",
                    properties={
                        "temperature": Parameter(
                            name="temperature",
                            type=ParameterType.NUMBER,
                            description="Current temperature"
                        ),
                        "conditions": Parameter(
                            name="conditions",
                            type=ParameterType.STRING,
                            description="Weather conditions"
                        ),
                        "humidity": Parameter(
                            name="humidity",
                            type=ParameterType.INTEGER,
                            description="Humidity percentage"
                        ),
                        "wind_speed": Parameter(
                            name="wind_speed",
                            type=ParameterType.NUMBER,
                            description="Wind speed"
                        )
                    }
                )
            ),
            Tool(
                id="get_forecast",
                name="Get Weather Forecast",
                description="Get the weather forecast for the next few days",
                parameters={
                    "location": Parameter(
                        name="location",
                        type=ParameterType.STRING,
                        description="The city and state/country to get forecast for",
                        required=True
                    ),
                    "days": Parameter(
                        name="days",
                        type=ParameterType.INTEGER,
                        description="Number of days to forecast (1-7)",
                        required=False,
                        default=3
                    )
                },
                returns=Parameter(
                    name="forecast_data",
                    type=ParameterType.ARRAY,
                    description="Array of daily forecasts",
                    items=Parameter(
                        name="daily_forecast",
                        type=ParameterType.OBJECT,
                        description="Daily forecast data",
                        properties={
                            "date": Parameter(
                                name="date",
                                type=ParameterType.STRING,
                                description="Forecast date"
                            ),
                            "high": Parameter(
                                name="high",
                                type=ParameterType.NUMBER,
                                description="High temperature"
                            ),
                            "low": Parameter(
                                name="low",
                                type=ParameterType.NUMBER,
                                description="Low temperature"
                            ),
                            "conditions": Parameter(
                                name="conditions",
                                type=ParameterType.STRING,
                                description="Weather conditions"
                            )
                        }
                    )
                )
            )
        ]

        global_state = {
            "api_calls_count": 0,
            "last_cache_clear": None
        }

        per_conversation_state = {}

        return tools, global_state, per_conversation_state

    def call_tool(
        self,
        tool_id: str,
        tool_parameters: Dict[str, Any],
        per_conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        global_state["api_calls_count"] = global_state.get("api_calls_count", 0) + 1

        if tool_id == "get_weather":
            return self._get_weather(tool_parameters, per_conversation_state)
        elif tool_id == "get_forecast":
            return self._get_forecast(tool_parameters, per_conversation_state)
        else:
            return None, f"Unknown tool: {tool_id}"

    def _get_weather(self, params: Dict[str, Any], conversation_state: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        location = params.get("location")
        units = params.get("units", "celsius")

        conversation_state.setdefault("weather_queries", []).append(location)

        conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Rainy", "Stormy", "Snowy", "Foggy"]

        if units == "celsius":
            temp = random.randint(-10, 35)
            wind_unit = "km/h"
        else:
            temp = random.randint(14, 95)
            wind_unit = "mph"

        weather_data = {
            "location": location,
            "temperature": temp,
            "conditions": random.choice(conditions),
            "humidity": random.randint(30, 90),
            "wind_speed": round(random.uniform(0, 30), 1),
            "units": units,
            "wind_unit": wind_unit
        }

        return weather_data, None

    def _get_forecast(self, params: Dict[str, Any], conversation_state: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        location = params.get("location")
        days = min(max(params.get("days", 3), 1), 7)

        conversation_state.setdefault("forecast_queries", []).append(location)

        conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Rainy", "Stormy", "Snowy", "Foggy"]

        from datetime import datetime, timedelta

        forecast = []
        base_date = datetime.now()

        for i in range(days):
            date = base_date + timedelta(days=i)
            forecast.append({
                "date": date.strftime("%Y-%m-%d"),
                "high": random.randint(15, 30),
                "low": random.randint(5, 15),
                "conditions": random.choice(conditions),
                "precipitation_chance": random.randint(0, 100)
            })

        return forecast, None
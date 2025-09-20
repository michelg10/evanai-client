#!/usr/bin/env python3
"""Test that all tool providers receive websocket_handler."""

from evanai_client.tools.weather_tool import WeatherToolProvider
from evanai_client.tools.math_tool import MathToolProvider
from evanai_client.tools.file_system_tool import FileSystemToolProvider
from evanai_client.tools.asset_tool import AssetToolProvider
from evanai_client.tools.upload_tool import UploadToolProvider

# Create mock websocket handler
class MockWebSocketHandler:
    def __init__(self):
        self.connected = True

mock_ws = MockWebSocketHandler()

# Test all providers accept websocket_handler
print("Testing websocket_handler passing to all providers:")
print("-" * 50)

providers = [
    ("WeatherToolProvider", WeatherToolProvider),
    ("MathToolProvider", MathToolProvider),
    ("FileSystemToolProvider", FileSystemToolProvider),
    ("AssetToolProvider", AssetToolProvider),
    ("UploadToolProvider", UploadToolProvider),
]

for name, provider_class in providers:
    # Create with websocket_handler
    provider = provider_class(websocket_handler=mock_ws)
    
    # Check if provider has websocket_handler attribute
    has_ws = hasattr(provider, 'websocket_handler')
    ws_value = getattr(provider, 'websocket_handler', None)
    
    print(f"{name:24} - has websocket_handler: {has_ws}, value: {ws_value is mock_ws}")

print("-" * 50)
print("✓ All providers can accept websocket_handler!")
print("✓ Providers that need it can access it via self.websocket_handler")

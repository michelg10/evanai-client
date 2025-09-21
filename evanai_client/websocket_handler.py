import websocket
import json
import threading
import time
import requests
import ssl
import certifi
import warnings
from typing import Callable, Optional, Dict, Any
from datetime import datetime
from .constants import WEBSOCKET_SERVER_URL


class WebSocketHandler:
    def __init__(self, url: str = None):
        self.url = url or WEBSOCKET_SERVER_URL
        self.ws = None
        self.connected = False
        self.message_handler: Optional[Callable[[Dict[str, Any]], None]] = None
        self.reconnect_delay = 5
        self.should_run = True
        self.thread = None

    def set_message_handler(self, handler: Callable[[Dict[str, Any]], None]):
        self.message_handler = handler

    def connect(self):
        self.should_run = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def _run(self):
        while self.should_run:
            try:
                # Disable SSL verification for testing (not recommended for production)
                ssl_opt = {"cert_reqs": ssl.CERT_NONE}

                self.ws = websocket.WebSocketApp(
                    self.url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )
                self.ws.run_forever(sslopt=ssl_opt)

                if self.should_run:
                    print(f"WebSocket disconnected. Reconnecting in {self.reconnect_delay} seconds...")
                    time.sleep(self.reconnect_delay)

            except Exception as e:
                print(f"WebSocket connection error: {e}")
                if self.should_run:
                    time.sleep(self.reconnect_delay)

    def _on_open(self, ws):
        self.connected = True
        print(f"Connected to WebSocket server at {self.url}")

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)

            if data.get('recipient') == 'agent' and data.get('type') == 'new_prompt':
                if self.message_handler:
                    self.message_handler(data)
                else:
                    print(f"Received message but no handler set: {data}")

        except json.JSONDecodeError as e:
            print(f"Failed to parse message: {e}")
        except Exception as e:
            print(f"Error handling message: {e}")

    def _on_error(self, ws, error):
        print(f"WebSocket error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        self.connected = False
        print(f"WebSocket connection closed: {close_status_code} - {close_msg}")

    def disconnect(self):
        self.should_run = False
        if self.ws:
            self.ws.close()
        if self.thread:
            self.thread.join(timeout=5)

    def send_response(self, conversation_id: str, response: str) -> bool:
        broadcast_url = "https://data-transmitter.hemeshchadalavada.workers.dev/broadcast"

        data = {
            "device": "evanai-client",
            "format": "agent_response",
            "recipient": "user_device",
            "type": "agent_response",
            "payload": {
                "conversation_id": conversation_id,
                "prompt": response
            },
            "timestamp": int(datetime.now().timestamp() * 1000)
        }

        try:
            # Disable SSL warnings for testing
            from urllib3.exceptions import InsecureRequestWarning
            warnings.filterwarnings('ignore', category=InsecureRequestWarning)

            # Disable SSL verification for testing (not recommended for production)
            response = requests.post(broadcast_url, json=data, verify=False)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to send response: {e}")
            return False

    def broadcast_tool_call(self, conversation_id: str, tool_name: str, display_name: Optional[str] = None, parameters: Optional[Dict] = None) -> bool:
        """Broadcast a tool call notification to the user device.

        Args:
            conversation_id: The conversation ID
            tool_name: The name of the tool being called
            display_name: Human-readable display name for the tool
            parameters: Optional parameters dict (for future use)

        Returns:
            True if broadcast successful, False otherwise
        """
        broadcast_url = "https://data-transmitter.hemeshchadalavada.workers.dev/broadcast"

        data = {
            "device": "evanai-client",
            "format": "tool_call",
            "recipient": "user_device",
            "type": "tool_call",
            "payload": {
                "conversation_id": conversation_id,
                "tool_name": tool_name,
                "display_name": display_name if display_name else tool_name,
                "timestamp": datetime.now().isoformat()
            },
            "timestamp": int(datetime.now().timestamp() * 1000)
        }

        try:
            # Disable SSL warnings for testing
            from urllib3.exceptions import InsecureRequestWarning
            warnings.filterwarnings('ignore', category=InsecureRequestWarning)

            # Disable SSL verification for testing (not recommended for production)
            response = requests.post(broadcast_url, json=data, verify=False)
            response.raise_for_status()
            print(f"📡 Broadcast tool call: {tool_name}")
            return True
        except Exception as e:
            print(f"Failed to broadcast tool call: {e}")
            return False

    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        latest_url = "https://data-transmitter.hemeshchadalavada.workers.dev/latest"

        try:
            # Disable SSL warnings for testing
            from urllib3.exceptions import InsecureRequestWarning
            warnings.filterwarnings('ignore', category=InsecureRequestWarning)

            # Disable SSL verification for testing (not recommended for production)
            response = requests.get(latest_url, verify=False)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to get latest data: {e}")
            return None
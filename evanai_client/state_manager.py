import os
import pickle
import json
from typing import Any, Dict, Optional
from pathlib import Path
import threading


class StateManager:
    def __init__(self, state_file: str = "evanai_state.pkl", reset_state: bool = False):
        self.state_file = Path(state_file)
        self.lock = threading.Lock()

        if reset_state and self.state_file.exists():
            os.remove(self.state_file)

        self._load_state()

    def _load_state(self):
        if self.state_file.exists():
            try:
                with open(self.state_file, 'rb') as f:
                    data = pickle.load(f)
                    self.global_state = data.get('global', {})
                    self.per_conversation_state = data.get('conversations', {})
            except Exception as e:
                print(f"Error loading state: {e}, initializing fresh state")
                self._initialize_state()
        else:
            self._initialize_state()

    def _initialize_state(self):
        self.global_state = {}
        self.per_conversation_state = {}
        self._save_state()

    def _save_state(self):
        with self.lock:
            data = {
                'global': self.global_state,
                'conversations': self.per_conversation_state
            }
            with open(self.state_file, 'wb') as f:
                pickle.dump(data, f)

    def get_global_state(self) -> Dict[str, Any]:
        return self.global_state

    def set_global_state(self, key: str, value: Any):
        with self.lock:
            self.global_state[key] = value
            self._save_state()

    def get_conversation_state(self, conversation_id: str) -> Dict[str, Any]:
        if conversation_id not in self.per_conversation_state:
            self.per_conversation_state[conversation_id] = {}
        return self.per_conversation_state[conversation_id]

    def set_conversation_state(self, conversation_id: str, key: str, value: Any):
        with self.lock:
            if conversation_id not in self.per_conversation_state:
                self.per_conversation_state[conversation_id] = {}
            self.per_conversation_state[conversation_id][key] = value
            self._save_state()

    def create_conversation(self, conversation_id: str):
        if conversation_id not in self.per_conversation_state:
            self.per_conversation_state[conversation_id] = {}
            self._save_state()

    def clear_all(self):
        with self.lock:
            self._initialize_state()
"""Constants for EvanAI Client."""

# WebSocket endpoints
WEBSOCKET_SERVER_URL = "wss://data-transmitter.hemeshchadalavada.workers.dev"
BROADCAST_API_URL = "https://data-transmitter.hemeshchadalavada.workers.dev/broadcast"

# File upload service
FILE_UPLOAD_API_URL = "https://file-upload-api.hemeshchadalavada.workers.dev/upload"

# Default configurations
DEFAULT_RUNTIME_DIR = "evanai_runtime"
DEFAULT_CLAUDE_MODEL = "claude-opus-4-1-20250805"
BACKUP_CLAUDE_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 32000

# Retry configuration
MAX_BACKOFF_SECONDS = 3  # Maximum backoff duration
INITIAL_BACKOFF_SECONDS = 0.1  # Initial backoff duration
BACKOFF_MULTIPLIER = 2  # Exponential multiplier
FALLBACK_RETRY_COUNT = 10  # Number of retries before switching to backup model
# No limit to total retries - will keep retrying indefinitely
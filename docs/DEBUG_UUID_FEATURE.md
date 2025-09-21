# Debug Interface - Conversation UUID Display

The debug interface now displays the current conversation UUID for easier tracking and debugging.

## Changes Made

### 1. **HTML Template Updates** (`debug.html`)
- Added UUID display in the conversation header
- Shows as: `UUID: debug-session-1758414333021`
- Styled with green color (#00ff88) and slight transparency

### 2. **JavaScript Updates**
- Added `updateConversationDisplay()` function
- UUID updates on:
  - Page load
  - Conversation reset
  - New conversation creation

### 3. **Debug Server Updates** (`debug_server.py`)
- System info endpoint now includes `active_conversation`
- Returns current conversation UUID in API responses

## Visual Layout

```
┌─────────────────────────────────────────────┐
│ 💬 Conversation  UUID: debug-session-123...  │ 0 messages
├─────────────────────────────────────────────┤
│                                             │
│           [Conversation Messages]           │
│                                             │
└─────────────────────────────────────────────┘
```

## Features

- **Automatic Display**: UUID shown immediately on page load
- **Dynamic Updates**: Changes when conversation is reset
- **Visual Style**: Green color matching the theme
- **Compact Design**: Doesn't clutter the interface

## API Endpoints

### GET /api/system
Now returns:
```json
{
  "runtime_dir": "evanai_runtime",
  "model": "claude-opus-4-1-20250805",
  "max_tokens": 32000,
  "tool_count": 17,
  "conversation_count": 1,
  "active_conversation": "debug-session-1758414333021"
}
```

## Testing

1. Start the debug server:
```bash
evanai-client debug
```

2. Open browser to: `http://localhost:8069`

3. Look for UUID in the conversation header

4. Test reset functionality to see UUID change

## Test Script

Run the test script to verify:
```bash
python test_debug_uuid.py
```

This will:
- Check system info endpoint
- Verify active conversation tracking
- Test UUID updates with new prompts
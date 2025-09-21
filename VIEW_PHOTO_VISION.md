# View Photo Tool - Vision Integration

The `view_photo` tool now properly integrates with Claude's vision capabilities to actually SEE and analyze images.

## How It Works

### 1. Tool Execution
When `view_photo` is called with an image path:
- Reads the image file from disk
- Encodes it as base64
- Returns structured data with MIME type

### 2. Special Processing in ClaudeAgent
The `_process_tool_calls` method now:
- Detects when `view_photo` tool returns image data
- Converts it to proper Claude vision format:
```json
{
  "type": "tool_result",
  "tool_use_id": "...",
  "content": [
    {
      "type": "image",
      "source": {
        "type": "base64",
        "media_type": "image/jpeg",
        "data": "<base64_data>"
      }
    },
    {
      "type": "text",
      "text": "I can now see the image..."
    }
  ]
}
```

### 3. Claude Receives Image
- Image is sent in the proper format for vision API
- Claude can actually SEE the image content
- Can analyze colors, shapes, text, objects, people, etc.

## Key Changes Made

### `claude_agent.py`
- Added special handling for `view_photo` tool results
- Creates proper image content blocks instead of JSON strings
- Follows Claude's vision API format exactly

### `view_photo_tool.py`
- Returns structured data with image base64 and MIME type
- Updated description to clarify actual vision capability
- Supports JPEG, PNG, GIF, WebP formats

## Supported Formats
- **JPEG** (.jpg, .jpeg)
- **PNG** (.png)
- **GIF** (.gif)
- **WebP** (.webp)

## Size Limits
- Max 5MB per image
- Max 8000x8000 pixels
- Optimal: ~1.15 megapixels (1092x1092)

## Usage Example

```python
# Agent can now:
1. Call view_photo("/path/to/image.jpg")
2. Actually SEE the image content
3. Describe what's in the image accurately
4. Answer questions about colors, objects, text, etc.
```

## Before vs After

### Before (Broken)
- Tool returned JSON with base64 data
- Data was just stringified, not sent as image
- Claude couldn't see anything, just hallucinated

### After (Fixed)
- Tool result converted to proper image content block
- Sent using Claude's vision API format
- Claude can actually see and analyze the image

## Technical Details

The fix required understanding that:
1. Tool results are normally JSON-stringified
2. Images need special content block format
3. `view_photo` needs special handling in `_process_tool_calls`
4. Content must match Claude's vision API structure exactly

Now the agent can truly see and understand images!
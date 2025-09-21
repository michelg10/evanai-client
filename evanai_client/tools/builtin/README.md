# Anthropic Built-in Tools Integration

This module provides integration with Anthropic's official built-in tools for the Claude API.

## Overview

Anthropic provides three built-in tools that Claude can use:

1. **Web Search** - Real-time web search with automatic citations
2. **Web Fetch** - Fetch and analyze full content from web pages and PDFs
3. **Text Editor** - File manipulation using str_replace commands

## Tool Types

### Server-side Tools (Automatic)

These tools execute automatically on Anthropic's servers:

- **Web Search** (`web_search_20250305`)
  - Generally available, no beta header needed
  - Requires organization admin to enable in Console
  - Costs $10 per 1,000 searches + token costs

- **Web Fetch** (`web_fetch_20250910`)
  - Beta feature, requires header: `anthropic-beta: web-fetch-2025-09-10`
  - No additional cost beyond token usage
  - Supports text and PDF content

### Client-side Tools (Requires Implementation)

- **Text Editor** (`text_editor_20250728` for Claude 4)
  - Requires implementing file operations locally
  - Commands: view, str_replace, create, insert, undo_edit
  - Standard token pricing only

## Usage

### Basic Usage with ClaudeAgent

```python
from evanai_client.claude_agent import ClaudeAgent

# Initialize agent
agent = ClaudeAgent(workspace_dir="/tmp")

# Enable built-in tools
response, history = agent.process_prompt(
    prompt="Search for Python news and summarize it",
    conversation_history=[],
    tools=[],  # Custom tools
    enable_builtin_tools=['web_search']  # Built-in tools
)
```

### Advanced Configuration

```python
from evanai_client.tools.builtin import BuiltinToolsIntegration

# Initialize integration
builtin = BuiltinToolsIntegration(workspace_dir="/tmp")

# Configure tools
tools_config = builtin.get_tools_config(
    tools=['web_search', 'web_fetch'],
    model='claude-opus-4-1-20250805',
    web_search_config={
        'max_uses': 5,
        'allowed_domains': ['example.com'],
        'user_location': {
            'city': 'San Francisco',
            'region': 'California',
            'country': 'US',
            'timezone': 'America/Los_Angeles'
        }
    },
    web_fetch_config={
        'max_uses': 3,
        'enable_citations': True,
        'max_content_tokens': 100000
    }
)

# Get required headers
headers = builtin.get_api_headers(['web_search', 'web_fetch'])
```

## API Request Format

### Web Search Request

```bash
curl https://api.anthropic.com/v1/messages \
  --header "x-api-key: $ANTHROPIC_API_KEY" \
  --header "anthropic-version: 2023-06-01" \
  --header "content-type: application/json" \
  --data '{
    "model": "claude-opus-4-1-20250805",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Search for AI news"}],
    "tools": [{
      "type": "web_search_20250305",
      "name": "web_search",
      "max_uses": 5
    }]
  }'
```

### Web Fetch Request (Beta)

```bash
curl https://api.anthropic.com/v1/messages \
  --header "x-api-key: $ANTHROPIC_API_KEY" \
  --header "anthropic-version: 2023-06-01" \
  --header "anthropic-beta: web-fetch-2025-09-10" \
  --header "content-type: application/json" \
  --data '{
    "model": "claude-opus-4-1-20250805",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Analyze https://example.com"}],
    "tools": [{
      "type": "web_fetch_20250910",
      "name": "web_fetch",
      "max_uses": 5
    }]
  }'
```

### Text Editor Request

```bash
curl https://api.anthropic.com/v1/messages \
  --header "x-api-key: $ANTHROPIC_API_KEY" \
  --header "anthropic-version: 2023-06-01" \
  --header "content-type: application/json" \
  --data '{
    "model": "claude-opus-4-1-20250805",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Fix the bug in main.py"}],
    "tools": [{
      "type": "text_editor_20250728",
      "name": "str_replace_based_edit_tool"
    }]
  }'
```

## Implementation Details

### Module Structure

```
builtin/
├── __init__.py              # Package initialization
├── api_integration.py       # Main integration layer
├── text_editor.py          # Text editor command executor
├── web_fetch.py            # Web fetch result processor
├── web_search.py           # Web search result processor
└── README.md               # This file
```

### Classes

- **BuiltinToolsIntegration**: Main integration class
  - Configures API requests with proper headers
  - Manages tool configurations
  - Handles tool_use/tool_result flow for text editor

- **TextEditorTool**: Executes text editor commands
  - Commands: view, str_replace, create, insert, undo_edit
  - Workspace directory security
  - Edit history for undo

- **WebFetchTool**: Processes web fetch results
  - Handles text and binary (PDF) content
  - Citation extraction
  - Content caching

- **WebSearchTool**: Processes web search results
  - Citation formatting
  - Encrypted content management for multi-turn
  - Search history tracking

## Security Considerations

### Web Fetch
- Risk of data exfiltration in untrusted environments
- Use domain filtering to restrict access
- Consider `max_content_tokens` to limit token usage

### Text Editor
- Provides filesystem access
- Use workspace directory restrictions
- Validate all file paths

### Web Search
- Generally safe
- Use domain filtering if needed
- Organization-level restrictions apply

## Model Compatibility

All tools work with:
- Claude Opus 4.1, Claude Opus 4, Claude Sonnet 4
- Claude Sonnet 3.7, Claude Sonnet 3.5, Claude Haiku 3.5

## Examples

See `examples/builtin_tools_example.py` for complete usage examples.

## Troubleshooting

### Web Search Not Working
- Ensure organization admin has enabled web search in Console
- Check for `web_search_20250305` in tools list
- No beta header should be present

### Web Fetch Not Working
- Ensure beta header is included: `anthropic-beta: web-fetch-2025-09-10`
- Check URL is accessible and not blocked by domain filters
- Verify content type is supported (text or PDF)

### Text Editor Not Working
- Ensure workspace directory is set and writable
- Check file paths are within workspace
- Verify str_replace old_str matches exactly

## References

- [Web Search Documentation](https://docs.anthropic.com/en/docs/build-with-claude/web-search)
- [Web Fetch Documentation](https://docs.anthropic.com/en/docs/build-with-claude/web-fetch)
- [Text Editor Documentation](https://docs.anthropic.com/en/docs/build-with-claude/text-editor)

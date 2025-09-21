# Claude API Retry Mechanism

The EvanAI client now includes automatic retry with exponential backoff for Claude API calls, with clear visual feedback when using backup models.

## Features

- **Automatic Retry**: Failed API calls are automatically retried with exponential backoff
- **Model Fallback**: After 10 retries (configurable), switches to backup model
- **Indefinite Retries**: Both primary and backup models retry indefinitely until successful
- **Clear Visual Feedback**: Prominent CLI indicators show when backup model is active
- **Configurable Settings**: All retry parameters can be customized

## Default Configuration

- **Max Backoff**: 3 seconds
- **Initial Backoff**: 0.1 seconds
- **Backoff Multiplier**: 2x
- **Fallback Retry Count**: 10 attempts
- **Default Model**: `claude-opus-4-1-20250805`
- **Backup Model**: `claude-sonnet-4-20250514`

## Retry Behavior

### Primary Model Phase
1. When an API call fails with `overloaded_error`, `rate_limit`, or `timeout`:
   - Shows `[PRIMARY MODEL]` indicator in green
   - First retry after 0.1s
   - Second retry after 0.2s
   - Third retry after 0.4s
   - Fourth retry after 0.8s
   - Fifth retry after 1.6s
   - Sixth retry after 3.0s (max)
   - Continues at 3.0s intervals...

### Backup Model Phase
2. After 10 retries, system displays prominent warning:
   ```
   ======================================================================
   ⚠️  SWITCHING TO BACKUP MODEL
      Primary model failed 10 times
      Now using: claude-sonnet-4-20250514
      Will continue retrying indefinitely with backup model
   ======================================================================
   ```

3. Backup model retries:
   - Shows `[BACKUP MODEL]` indicator in cyan
   - Resets backoff to 0.1s
   - Continues indefinitely until successful
   - Shows success message when backup model responds

## Visual Indicators

- **[PRIMARY MODEL]** - Green indicator during primary model retries
- **[BACKUP MODEL]** - Cyan indicator during backup model retries
- **Yellow Warning Box** - Prominent notification when switching to backup
- **Success Message** - Green checkmark when backup model responds

## Configuration Methods

### Environment Variables

```bash
export CLAUDE_MAX_BACKOFF=3
export CLAUDE_INITIAL_BACKOFF=0.1
export CLAUDE_BACKOFF_MULTIPLIER=2
export CLAUDE_FALLBACK_RETRY_COUNT=10
export CLAUDE_BACKUP_MODEL=claude-sonnet-4-20250514
```

### Programmatic Configuration

```python
from evanai_client.claude_agent import ClaudeAgent

agent = ClaudeAgent()
agent.configure_retry(
    max_backoff=5.0,
    initial_backoff=0.5,
    backoff_multiplier=3.0,
    fallback_retry_count=5,
    backup_model="claude-3-haiku-20240307"
)
```

### Constants File

Edit `evanai_client/constants.py` to change defaults:

```python
MAX_BACKOFF_SECONDS = 3
INITIAL_BACKOFF_SECONDS = 0.1
BACKOFF_MULTIPLIER = 2
FALLBACK_RETRY_COUNT = 10
BACKUP_CLAUDE_MODEL = "claude-sonnet-4-20250514"
```

## Testing

Run the test script to verify configuration:

```bash
python test_retry_mechanism.py
```

## Model Status Methods

Check and manage the current model status:

```python
# Check if using backup model
if agent.is_using_backup_model():
    print("Currently using backup model")

# Get current active model name
current = agent.get_current_model()
print(f"Active model: {current}")

# Reset to original model after fallback
agent.reset_model()  # Returns to original model
```

## Demo

Run the demo script to see the retry behavior:

```bash
python demo_retry_behavior.py
```
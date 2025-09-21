# EvanAI Client Setup Guide

## Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Environment Variables**

   Copy the template file:
   ```bash
   cp .env.template .env
   ```

   Edit `.env` and add your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your-actual-api-key-here
   ```

   Get your API key from: https://console.anthropic.com/account/keys

3. **Run the Client**
   ```bash
   python -m evanai_client.main run
   ```

## Common Issues

### "Error: ANTHROPIC_API_KEY not found in environment variables"

**Solution**: The client now automatically loads the `.env` file. Make sure:
1. Your `.env` file exists in the evanai-client directory
2. The file contains: `ANTHROPIC_API_KEY=your-actual-key`
3. You have installed `python-dotenv`: `pip install python-dotenv`

### "ModuleNotFoundError: No module named 'dotenv'"

**Solution**: Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Verifying Your Setup

Test that your API key is properly configured:
```bash
python -m evanai_client.main status
```

If successful, you should see the client status without any API key errors.

## Alternative API Key Methods

You can also provide your API key in several ways:

1. **Environment Variable** (traditional method):
   ```bash
   export ANTHROPIC_API_KEY='your-key-here'
   python -m evanai_client.main run
   ```

2. **Command Line Argument**:
   ```bash
   python -m evanai_client.main run --api-key 'your-key-here'
   ```

3. **.env File** (recommended):
   Place your key in `.env` file as shown above. The client will automatically load it.

## Reset Persistence

If you need to reset all stored data:
```bash
python -m evanai_client.main reset-persistence
```

Or reset when starting:
```bash
python -m evanai_client.main run --reset-state
```
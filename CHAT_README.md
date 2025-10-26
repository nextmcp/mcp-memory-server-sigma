# AI Chat Client

A simple, interactive terminal chat client for LiteLLM proxy with model switching capabilities.

## Quick Start

```bash
# Basic usage (defaults to staging environment and claude-sonnet-4-5)
uv run chat.py sk-YOUR-API-KEY-HERE

# Specify environment and model
uv run chat.py sk-YOUR-API-KEY-HERE staging claude-sonnet-4-5

# Use different environments
uv run chat.py sk-YOUR-API-KEY-HERE production gpt-4o
uv run chat.py sk-YOUR-API-KEY-HERE dev gpt-4o-mini
```

## Features

- 💬 **Interactive Chat**: Clean terminal interface with rich markdown formatting
- 🔄 **Model Switching**: Change AI models without restarting
- 📝 **Conversation History**: Maintains context throughout your session
- 🎨 **Rich Formatting**: Beautiful markdown rendering for responses
- ⌨️ **Simple Commands**: Easy-to-use slash commands

## Available Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| `/help` | `/h` | Show available commands |
| `/switch [model]` | - | Switch to a different model |
| `/clear` | `/c` | Clear conversation history |
| `/quit` | `/q`, `/exit` | Exit the chat |

## Environments

The client supports three environments:

- **staging**: `https://api.staging.example.com`
- **dev**: `https://api.dev.example.com`
- **production**: `https://api.production.example.com`

## Common Models

Depending on your API key permissions, you may have access to:

- `claude-sonnet-4-5` - Anthropic Claude Sonnet 4.5
- `gpt-4o` - OpenAI GPT-4 Optimized
- `gpt-4o-mini` - OpenAI GPT-4 Mini
- `gpt-4-turbo` - OpenAI GPT-4 Turbo
- Other models supported by your LiteLLM proxy

## Usage Examples

### Basic Chat

```bash
uv run chat.py sk-YOUR-API-KEY-HERE
```

This starts a chat session with:
- Environment: staging (default)
- Model: claude-sonnet-4-5 (default)

### Switching Models During Chat

```bash
You: /switch gpt-4o
✓ Switched to gpt-4o

You: /switch claude-sonnet-4-5
✓ Switched to claude-sonnet-4-5

You: /switch
Enter model name [claude-sonnet-4-5]: gpt-4o-mini
✓ Switched to gpt-4o-mini
```

### Specifying Model at Startup

```bash
# Use Claude Sonnet
uv run chat.py sk-YOUR-API-KEY-HERE staging claude-sonnet-4-5

# Use GPT-4o
uv run chat.py sk-YOUR-API-KEY-HERE staging gpt-4o

# Use GPT-4o-mini in production
uv run chat.py sk-YOUR-API-KEY-HERE production gpt-4o-mini
```

### Clearing History

```bash
You: Hello, I'm working on a Python project
AI: [response about Python]

You: /clear
✓ History cleared

You: What were we talking about?
AI: [no memory of Python - fresh start]
```

## Troubleshooting

### Error 401: Model Access Denied

```
Error 401: {"error":{"message":"key not allowed to access model..."}}
```

**Solution**: Your API key doesn't have permission for that model. Switch to an allowed model:

```bash
# If your key only allows claude-sonnet-4-5
You: /switch claude-sonnet-4-5
```

Or restart with the correct model:

```bash
uv run chat.py sk-YOUR-API-KEY-HERE staging claude-sonnet-4-5
```

### Connection Errors

If you see connection errors:
1. Check your internet connection
2. Verify the environment URL is accessible
3. Ensure your API key is valid

### Interrupted Chat

If you accidentally press `Ctrl+C`:
```
Interrupted. Type /quit to exit.
You: 
```

You can continue chatting or type `/quit` to exit properly.

## Dependencies

The script uses inline dependencies (PEP 723):
- `requests` - HTTP client for API calls
- `rich` - Terminal formatting and UI

These are automatically installed by `uv run`.

## Command Line Arguments

```
uv run chat.py <api-key> [environment] [model]
```

**Arguments:**
1. `api-key` (required) - Your LiteLLM API key (starts with `sk-`)
2. `environment` (optional) - One of: `staging`, `dev`, `production` (default: `staging`)
3. `model` (optional) - Model name (default: `claude-sonnet-4-5`)

## Tips & Best Practices

### Finding Your Allowed Models

If you get a 401 error, the error message will tell you which models you can access:

```json
{
  "error": {
    "message": "key not allowed to access model. This key can only access models=['claude-sonnet-4-5']"
  }
}
```

Use `/switch` to switch to an allowed model.

### Managing Conversation Length

Clear history periodically to reset context:
```bash
You: /clear
```

This is useful when:
- Starting a new topic
- The conversation is getting too long
- You want to save on token usage

### Keyboard Shortcuts

- `Ctrl+C` - Interrupt (doesn't exit, just pauses)
- `Ctrl+D` - EOF, exits gracefully
- Type `/quit` - Clean exit with goodbye message

## Example Session

```bash
$ uv run chat.py sk-YOUR-API-KEY-HERE staging claude-sonnet-4-5

╭───────────────────────────╮
│ 💬 AI Chat                │
│                           │
│ Environment: staging      │
│ Model: claude-sonnet-4-5  │
│                           │
│ Type your message or use: │
│   /clear - Clear history  │
│   /quit  - Exit           │
╰───────────────────────────╯

You: Hello! What model are you?

Thinking...

AI
I'm Claude Sonnet 4.5, an AI assistant created by Anthropic...

You: /switch gpt-4o
✓ Switched to gpt-4o

You: Now what model are you?

Thinking...

AI
I'm GPT-4o, an AI language model created by OpenAI...

You: /quit

Goodbye! 👋
```

## Advanced Usage

### Different Environments

```bash
# Development testing
uv run chat.py sk-YOUR-API-KEY-HERE dev gpt-4o-mini

# Staging testing
uv run chat.py sk-YOUR-API-KEY-HERE staging claude-sonnet-4-5

# Production usage
uv run chat.py sk-YOUR-API-KEY-HERE production gpt-4o
```

### Quick Model Testing

Test multiple models in one session:

```bash
You: /switch gpt-4o-mini
You: Explain quantum computing
[get response]

You: /switch gpt-4o
You: Explain quantum computing
[compare response]

You: /switch claude-sonnet-4-5
You: Explain quantum computing
[compare response]
```

## Security Notes

⚠️ **Never commit your API keys to version control!**

- Keep your API keys private
- Don't share your keys in public repositories
- Use environment variables or secure vaults for keys in production
- Rotate keys regularly

## Support

For issues with:
- **The chat script**: Check this README or the script's inline help (`/help`)
- **LiteLLM proxy**: Contact your LiteLLM administrator
- **API keys**: Contact your organization's key administrator

## License

Part of the MCP Memory Server project. See project LICENSE for details.

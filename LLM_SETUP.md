# LLM Setup Guide

## Quick Setup

To enable LLM responses in the chat service, you need to configure your OpenAI API key.

## Step 1: Get Your OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign in or create an account
3. Navigate to **API Keys** section: https://platform.openai.com/api-keys
4. Click **"Create new secret key"**
5. Copy the API key (you won't be able to see it again!)

## Step 2: Configure in .env File

1. Open or create `.env` file in the project root:
   ```bash
   cd /Users/dheerajmehra/Documents/projects/ai-chat-with-knowledgebase/ai-chat-with-kb-backend
   ```

2. Add or update the following variables:
   ```bash
   # Enable LLM
   LLM_ENABLED=true
   
   # Your OpenAI API Key (replace with your actual key)
   OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   
   # Optional: Customize LLM settings
   LLM_MODEL=gpt-4o
   LLM_MAX_TOKENS=1000
   LLM_TEMPERATURE=0.7
   ```

3. **Important**: Make sure `.env` is in `.gitignore` (it should be by default) to avoid committing your API key.

## Step 3: Restart the Chat Service

After updating `.env`, restart the chat service:

```bash
# Stop the current service (Ctrl+C if running)
# Then restart:
./run_server.sh chat
# Or if running both services:
./run_server.sh both
```

## Verification

### Check if API Key is Loaded

The service will log on startup:
- ✅ `Initialized LLM service with model: gpt-4o` - Success!
- ⚠️ `LLM is enabled but OPENAI_API_KEY is not set` - API key missing
- ❌ `Failed to initialize LLM service: ...` - Check error message

### Test the API Key

You can test if your API key works:

```bash
# Using curl (replace with your actual key)
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-proj-your-key-here"
```

If successful, you'll see a list of available models.

## Common Issues

### Error: "Invalid or missing OpenAI API key"

**Solution:**
1. Check that `OPENAI_API_KEY` is set in `.env`
2. Make sure there are no extra spaces or quotes around the key
3. Verify the key starts with `sk-` (for secret key)
4. Restart the service after updating `.env`

### Error: "OpenAI API quota exceeded"

**Solution:**
1. Check your OpenAI account billing: https://platform.openai.com/account/billing
2. Ensure you have credits or a payment method on file
3. Check usage limits: https://platform.openai.com/account/limits

### Error: "Rate limit exceeded"

**Solution:**
1. You're making too many requests too quickly
2. Wait a few seconds and try again
3. Consider reducing `top_k` to retrieve fewer chunks per request

### LLM Service Not Initializing

**Check:**
1. Is `LLM_ENABLED=true` in `.env`?
2. Is `OPENAI_API_KEY` set and valid?
3. Check logs for specific error messages
4. Verify OpenAI SDK is installed: `pip install openai>=1.3.7`

## Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_ENABLED` | No | `false` | Enable/disable LLM responses |
| `OPENAI_API_KEY` | Yes (if LLM enabled) | - | Your OpenAI API key |
| `LLM_MODEL` | No | `gpt-4o` | OpenAI model to use |
| `LLM_MAX_TOKENS` | No | `1000` | Maximum response length |
| `LLM_TEMPERATURE` | No | `0.7` | Response creativity (0.0-2.0) |
| `LLM_SYSTEM_PROMPT` | No | (default) | Custom system prompt |

## Security Best Practices

1. **Never commit `.env` to git** - It should be in `.gitignore`
2. **Use environment-specific keys** - Different keys for dev/prod
3. **Rotate keys regularly** - Especially if exposed
4. **Monitor usage** - Set up billing alerts in OpenAI dashboard
5. **Use least privilege** - Don't share API keys unnecessarily

## Cost Management

- **Model costs vary**: `gpt-4o` is more expensive than `gpt-3.5-turbo`
- **Token usage**: Each request uses input tokens (query + chunks) + output tokens (response)
- **Monitor usage**: Check https://platform.openai.com/usage
- **Set limits**: Configure usage limits in OpenAI dashboard

## Example .env File

```bash
# Application Settings
APP_NAME=DFSA RAG Ingestion Pipeline
APP_VERSION=1.0.0
LOG_LEVEL=INFO

# Vector Store
VECTOR_STORE_TYPE=file
VECTOR_STORE_PATH=data/vector_store.pkl
EMBEDDING_PROVIDER=sentence-transformers

# LLM Configuration
LLM_ENABLED=true
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_MODEL=gpt-4o
LLM_MAX_TOKENS=1000
LLM_TEMPERATURE=0.7

# Chunking
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

## Need Help?

1. Check the logs: `tail -f logs/*.log`
2. Review error messages in the terminal
3. Verify API key at: https://platform.openai.com/api-keys
4. Check OpenAI status: https://status.openai.com/

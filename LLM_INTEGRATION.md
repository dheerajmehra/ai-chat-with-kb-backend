# LLM Integration Guide

## Overview

The chat service now supports optional LLM (Large Language Model) integration using OpenAI's API. When enabled, the system will:

1. Retrieve relevant chunks from the vector store (as before)
2. Send the user query + retrieved chunks to an LLM
3. Return the LLM-generated response to the frontend

This provides more natural, conversational responses while still maintaining references to the source documents.

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# LLM Configuration
LLM_ENABLED=false                    # Set to true to enable LLM responses
LLM_MODEL=gpt-4o                     # OpenAI model (e.g., gpt-4o, gpt-4-turbo, gpt-3.5-turbo)
LLM_MAX_TOKENS=1000                  # Maximum tokens in response
LLM_TEMPERATURE=0.7                  # Temperature (0.0-2.0, higher = more creative)
OPENAI_API_KEY=your-openai-api-key   # Required when LLM_ENABLED=true

# Optional: Custom system prompt
# LLM_SYSTEM_PROMPT=Your custom system prompt here
```

### Default System Prompt

If `LLM_SYSTEM_PROMPT` is not set, the following default is used:

```
You are an expert assistant helping users understand DFSA (Dubai Financial Services Authority) 
rulebooks and regulations. Your responses should be clear, accurate, and based solely on the 
provided excerpts from the rulebooks. Always cite specific rules, modules, or page numbers when 
referencing information. If you cannot answer a question based on the provided excerpts, 
clearly state that the information is not available in the provided context.
```

## Usage

### API Request

The `/api/chat` endpoint accepts an optional `use_llm` parameter:

```json
{
  "message": "What are capital requirements for banks?",
  "user_id": "user123",
  "session_id": "session456",
  "top_k": 5,
  "use_llm": true  // Optional: overrides LLM_ENABLED config
}
```

### Behavior

- **If `use_llm` is `true`** (or `LLM_ENABLED=true` and `use_llm` is not specified):
  - Retrieves chunks from vector store
  - Sends query + chunks to LLM
  - Returns LLM-generated response
  - Still includes `references` array for citation

- **If `use_llm` is `false`** (or `LLM_ENABLED=false`):
  - Retrieves chunks from vector store
  - Returns default formatted message
  - Includes `references` array

### Response Format

The response format remains the same:

```json
{
  "message": "LLM-generated or default response text",
  "references": [
    {
      "id": "...",
      "document_id": "...",
      "document_name": "...",
      "page_number": 42,
      "chunk_text": "...",
      "score": 0.85,
      "module_code": "GEN",
      "rule_number": "GEN 2.1.1",
      ...
    }
  ]
}
```

## Implementation Details

### Architecture

1. **LLM Service** (`shared/services/llm_service.py`):
   - Singleton service for OpenAI client management
   - Handles prompt construction with retrieved chunks
   - Manages API calls to OpenAI

2. **Configuration** (`shared/config.py`):
   - `llm_enabled`: Global enable/disable flag
   - `llm_model`: OpenAI model to use
   - `llm_max_tokens`: Maximum response length
   - `llm_temperature`: Response creativity
   - `llm_system_prompt`: Custom system prompt

3. **Chat Endpoint** (`chat-service/api/main.py`):
   - Checks `use_llm` parameter or config
   - Calls LLM service if enabled
   - Falls back to default message on error

### Error Handling

- If LLM is requested but not configured: Falls back to default message
- If LLM API call fails: Falls back to default message with error note
- If LLM is disabled: Uses default message format

## Example

### Without LLM (default)

**Request:**
```json
{
  "message": "What are capital requirements?",
  "user_id": "user1",
  "session_id": "session1",
  "top_k": 5
}
```

**Response:**
```json
{
  "message": "Found 3 relevant results for your query. Results from: GEN, PRU.",
  "references": [...]
}
```

### With LLM Enabled

**Request:**
```json
{
  "message": "What are capital requirements?",
  "user_id": "user1",
  "session_id": "session1",
  "top_k": 5,
  "use_llm": true
}
```

**Response:**
```json
{
  "message": "Based on the DFSA rulebooks, capital requirements for banks are defined in the Prudential (PRU) module. According to GEN 2.1.1 and PRU 3.2.1, banks must maintain minimum capital ratios... [LLM-generated detailed response]",
  "references": [...]
}
```

## Cost Considerations

- LLM calls incur API costs based on:
  - Model used (gpt-4o is more expensive than gpt-3.5-turbo)
  - Input tokens (query + chunks)
  - Output tokens (response length)

- To minimize costs:
  - Use `gpt-3.5-turbo` for lower cost
  - Reduce `top_k` to retrieve fewer chunks
  - Set lower `LLM_MAX_TOKENS` to limit response length

## Testing

1. **Test without LLM:**
   ```bash
   # Ensure LLM_ENABLED=false in .env
   curl -X POST http://localhost:8002/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "test", "user_id": "u1", "session_id": "s1"}'
   ```

2. **Test with LLM:**
   ```bash
   # Set LLM_ENABLED=true and OPENAI_API_KEY in .env
   curl -X POST http://localhost:8002/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "test", "user_id": "u1", "session_id": "s1", "use_llm": true}'
   ```

## Troubleshooting

### LLM not working

1. Check `LLM_ENABLED=true` in `.env`
2. Verify `OPENAI_API_KEY` is set correctly
3. Check logs for initialization errors
4. Ensure OpenAI API key has sufficient credits

### LLM responses are too long/short

- Adjust `LLM_MAX_TOKENS` in `.env`
- Modify system prompt to request specific response length

### LLM responses are not accurate

- Increase `top_k` to retrieve more context
- Adjust `LLM_TEMPERATURE` (lower = more focused)
- Customize `LLM_SYSTEM_PROMPT` for better guidance

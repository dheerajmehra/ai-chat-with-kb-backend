# Chat Service Vector Store Access Fix

## Problem

When querying the chat service, you were getting:
```
"No relevant information found for your query: 'What are capital requirements for banks?'. 
Try rephrasing or check if relevant documents have been ingested."
```

## Root Causes

1. **Wrong Vector Store Type**: `.env` had `VECTOR_STORE_TYPE=local` instead of `file`
   - `local` = in-memory (single process only, lost on restart)
   - `file` = file-based (shared between processes, persistent)

2. **Missing Startup Event**: The ingestion service didn't have a startup event handler to automatically ingest PDFs

3. **Empty Vector Store**: The vector store file (`data/vector_store.pkl`) didn't exist because PDFs hadn't been ingested yet

## Fixes Applied

### 1. Updated `.env` Configuration
Changed:
```env
VECTOR_STORE_TYPE=local  # Options: azure, openai, local
```

To:
```env
VECTOR_STORE_TYPE=file  # Options: azure, openai, local, file
VECTOR_STORE_PATH=data/vector_store.pkl
```

### 2. Added Startup Event Handler
Added automatic PDF ingestion on startup in `ingestion-service/api/main.py`:
- Checks if vector store type is `local` or `file`
- Loads all configured PDFs from `downloads/` folder
- Checks if vector store already has chunks (avoids duplicates)
- Ingests PDFs sequentially if store is empty
- Provides detailed logging

### 3. Added `get_chunk_count()` Method
Added to `FileBasedVectorStore` class to check if vector store has existing chunks before ingesting.

## How It Works Now

### For Split Architecture (Recommended)

1. **Ingestion Service** (port 8001):
   - On startup, automatically ingests all PDFs from `downloads/` folder
   - Saves chunks to `data/vector_store.pkl` (file-based store)
   - Can also accept manual uploads via `/ingest` endpoint

2. **Chat Service** (port 8002):
   - On startup, loads existing chunks from `data/vector_store.pkl`
   - Searches the file-based store for queries
   - Both services share the same vector store file

### Vector Store File Location

- **Path**: `data/vector_store.pkl` (configurable via `VECTOR_STORE_PATH`)
- **Format**: Pickle file containing list of `DocumentChunk` objects
- **Shared Access**: Both services can read/write using file locking

## Verification Steps

1. **Check `.env` configuration**:
   ```bash
   grep VECTOR_STORE .env
   # Should show:
   # VECTOR_STORE_TYPE=file
   # VECTOR_STORE_PATH=data/vector_store.pkl
   ```

2. **Start ingestion service**:
   ```bash
   ./run_server.sh ingestion
   # Or: uvicorn ingestion-service.api.main:app --reload --port 8001
   ```

3. **Check startup logs**:
   - Should see "STARTUP: Automatic PDF Ingestion" message
   - Should see PDFs being ingested
   - Should see "AUTOMATIC INGESTION SUMMARY" with chunk counts

4. **Verify vector store file exists**:
   ```bash
   ls -lh data/vector_store.pkl
   # Should show the file exists and has size > 0
   ```

5. **Start chat service**:
   ```bash
   ./run_server.sh chat
   # Or: uvicorn chat-service.api.main:app --reload --port 8002
   ```

6. **Test chat query**:
   ```bash
   curl -X POST http://localhost:8002/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "What are capital requirements for banks?", "top_k": 5}'
   ```

## Troubleshooting

### Issue: Still getting "No relevant information found"

**Check:**
1. ✅ Vector store file exists: `ls -lh data/vector_store.pkl`
2. ✅ File has content: `du -h data/vector_store.pkl` (should be > 0)
3. ✅ Ingestion service logs show successful ingestion
4. ✅ Chat service is using same `VECTOR_STORE_PATH` as ingestion service
5. ✅ Both services are reading from same `.env` file

**Solution:**
- Restart both services after ensuring `.env` is correct
- Check ingestion service logs for errors
- Verify PDFs exist in `downloads/` folder
- Verify PDFs are configured in `shared/config/pdf_metadata.json`

### Issue: Vector store file not being created

**Check:**
1. ✅ `data/` directory exists (will be created automatically)
2. ✅ Ingestion service has write permissions to `data/` directory
3. ✅ `VECTOR_STORE_TYPE=file` in `.env`
4. ✅ Ingestion service startup logs show ingestion happening

**Solution:**
- Create `data/` directory manually: `mkdir -p data`
- Check file permissions: `ls -ld data/`
- Review ingestion service logs for errors

### Issue: Chat service can't read vector store

**Check:**
1. ✅ Chat service is using `VECTOR_STORE_TYPE=file` (not `local`)
2. ✅ Chat service `VECTOR_STORE_PATH` matches ingestion service
3. ✅ Vector store file exists before chat service starts
4. ✅ Chat service has read permissions to `data/vector_store.pkl`

**Solution:**
- Ensure both services use same `.env` file
- Start ingestion service first, wait for ingestion to complete
- Then start chat service
- Check chat service logs for file loading messages

## Key Points

1. **File-based store is required** for split architecture (two separate services)
2. **Automatic ingestion** happens on ingestion service startup
3. **Both services share** the same vector store file
4. **File locking** prevents concurrent write conflicts
5. **Vector store persists** across service restarts

## Next Steps

1. Restart both services:
   ```bash
   ./run_server.sh both
   ```

2. Wait for ingestion to complete (check logs)

3. Test chat query from frontend or via curl

4. Verify results are returned with similarity scores


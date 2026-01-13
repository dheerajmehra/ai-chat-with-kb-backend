# Automatic PDF Ingestion on Startup

## Overview

When using the **local vector store**, the backend automatically ingests all configured PDFs from the `downloads/` folder on server startup. This ensures the vector store is populated and ready for chat queries immediately after the server starts.

## How It Works

### Startup Event Handler

The FastAPI application includes a `startup_event` handler that:

1. **Checks Vector Store Type**: Only runs if `VECTOR_STORE_TYPE=local` in `.env`
2. **Loads PDF Configuration**: Reads all PDFs from `config/pdf_metadata.json`
3. **Finds Available PDFs**: Checks which configured PDFs exist in `downloads/` folder
4. **Checks Existing Chunks**: Skips ingestion if vector store already has chunks (avoids duplicates)
5. **Ingests Sequentially**: Processes each PDF one by one
6. **Logs Progress**: Provides detailed logging of the ingestion process

### Behavior

#### When Vector Store is Empty
- ✅ Automatically ingests all PDFs found in `downloads/`
- ✅ Logs detailed progress for each PDF
- ✅ Provides summary at the end

#### When Vector Store Has Existing Chunks
- ⏭️ Skips automatic ingestion to avoid duplicates
- ℹ️ Logs a message explaining why ingestion was skipped
- 💡 Suggests restarting server if re-ingestion is needed

#### When Using Non-Local Vector Store
- ⏭️ Skips automatic ingestion (Azure/OpenAI stores are persistent)
- ℹ️ Logs a message explaining why ingestion was skipped

## Configuration

### Required Setup

1. **PDFs in `downloads/` folder**:
   ```bash
   downloads/
   ├── DFSA1547_15954_VER260126.pdf
   ├── DFSA1547_1843_VER700126.pdf
   └── DFSA1547_5717_VER630126.pdf
   ```

2. **PDFs configured in `config/pdf_metadata.json`**:
   ```json
   {
     "pdfs": [
       {
         "file_name": "DFSA1547_15954_VER260126.pdf",
         "alias": "Markets Rules",
         ...
       }
     ]
   }
   ```

3. **Environment variable** (`.env`):
   ```env
   VECTOR_STORE_TYPE=local
   ```

## Example Startup Logs

### Successful Ingestion

```
================================================================================
STARTUP: Automatic PDF Ingestion for Local Vector Store
================================================================================
Found 3 PDF(s) configured in pdf_metadata.json
  ✓ DFSA1547_15954_VER260126.pdf (Markets Rules) - Found
  ✓ DFSA1547_1843_VER700126.pdf (General Module) - Found
  ✓ DFSA1547_5717_VER630126.pdf (Glossary) - Found

Starting automatic ingestion of 3 PDF(s)...

================================================================================
Ingesting: DFSA1547_15954_VER260126.pdf
Alias: Markets Rules | Module: MKT
================================================================================
✓ Successfully ingested DFSA1547_15954_VER260126.pdf: 384 chunks, 332 pages in 12.45s

================================================================================
Ingesting: DFSA1547_1843_VER700126.pdf
Alias: General Module | Module: GEN
================================================================================
✓ Successfully ingested DFSA1547_1843_VER700126.pdf: 496 chunks, 436 pages in 15.23s

================================================================================
Ingesting: DFSA1547_5717_VER630126.pdf
Alias: Glossary | Module: GLO
================================================================================
✓ Successfully ingested DFSA1547_5717_VER630126.pdf: 661 chunks, 4 pages in 4.56s

================================================================================
AUTOMATIC INGESTION SUMMARY
================================================================================
Total PDFs configured: 3
PDFs found in downloads/: 3
Successfully ingested: 3
Failed: 0
Total chunks in vector store: 1541
================================================================================

✓ Backend is ready! Chat functionality is available.
```

### When Vector Store Already Has Chunks

```
================================================================================
STARTUP: Automatic PDF Ingestion for Local Vector Store
================================================================================
Found 3 PDF(s) configured in pdf_metadata.json
  ✓ DFSA1547_15954_VER260126.pdf (Markets Rules) - Found
  ✓ DFSA1547_1843_VER700126.pdf (General Module) - Found
  ✓ DFSA1547_5717_VER630126.pdf (Glossary) - Found

Starting automatic ingestion of 3 PDF(s)...
Vector store already contains 1541 chunk(s). Skipping automatic ingestion to avoid duplicates.
If you want to re-ingest, restart the server with an empty vector store.
```

### When PDFs Are Missing

```
================================================================================
STARTUP: Automatic PDF Ingestion for Local Vector Store
================================================================================
Found 3 PDF(s) configured in pdf_metadata.json
  ✗ DFSA1547_15954_VER260126.pdf (Markets Rules) - Not found in downloads/
  ✗ DFSA1547_1843_VER700126.pdf (General Module) - Not found in downloads/
  ✗ DFSA1547_5717_VER630126.pdf (Glossary) - Not found in downloads/

No PDFs found in downloads/ folder. Skipping automatic ingestion.
```

## Benefits

### 1. **Zero-Configuration Chat**
- Chat functionality works immediately after server starts
- No manual ingestion required
- Perfect for development and testing

### 2. **Automatic State Management**
- Detects existing chunks and avoids duplicates
- Prevents unnecessary re-processing
- Saves time and resources

### 3. **Clear Logging**
- Detailed progress for each PDF
- Summary statistics
- Clear error messages if something fails

### 4. **Development-Friendly**
- Fast iteration during development
- Automatic reload on code changes (with `--reload`)
- No manual steps required

## Manual Ingestion (Still Available)

The automatic ingestion doesn't replace manual ingestion. You can still:

1. **Use the `/ingest` endpoint**:
   ```bash
   curl -X POST "http://localhost:8000/ingest" \
     -F "file=@downloads/new-file.pdf"
   ```

2. **Use `test_pipeline.py`**:
   ```bash
   python test_pipeline.py downloads/file.pdf --step all
   ```

## Troubleshooting

### Issue: PDFs Not Being Ingested

**Check:**
1. ✅ `VECTOR_STORE_TYPE=local` in `.env`
2. ✅ PDFs exist in `downloads/` folder
3. ✅ PDFs are listed in `config/pdf_metadata.json`
4. ✅ File names match exactly (case-sensitive)

### Issue: Duplicate Ingestion

**Solution:**
- The system automatically detects existing chunks and skips ingestion
- If you want to re-ingest, restart the server (which clears the in-memory store)

### Issue: Ingestion Fails

**Check logs:**
- Look for error messages in the startup logs
- Check `logs/ingestion_*.log` for detailed error information
- Verify PDF files are not corrupted

## Implementation Details

### Code Location
- **File**: `api/main.py`
- **Function**: `startup_event()` (decorated with `@app.on_event("startup")`)

### Key Components
1. **MetadataLoader**: Loads PDF configuration
2. **IngestionService**: Handles PDF processing
3. **VectorStore**: Stores ingested chunks
4. **Logger**: Provides detailed logging

### Safety Features
- ✅ Only runs for local vector store
- ✅ Checks for existing chunks before ingesting
- ✅ Handles errors gracefully
- ✅ Provides clear logging

## Future Enhancements

Potential improvements:
- [ ] Parallel ingestion for faster startup
- [ ] Configurable auto-ingestion (enable/disable via env var)
- [ ] Selective ingestion (ingest only specific PDFs)
- [ ] Incremental updates (only ingest changed PDFs)
- [ ] Health check endpoint showing ingestion status


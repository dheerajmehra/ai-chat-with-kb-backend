# Split Architecture Implementation Guide

## Overview

The backend has been split into two separate services:
1. **Ingestion Service** (Port 8001): Handles PDF vectorization
2. **Chat Service** (Port 8002): Handles user queries and document serving

Both services share common code from the `shared/` directory and use a **file-based vector store** that can be accessed by both services.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Ingestion Service                      │
│  Port: 8001                                              │
│  - POST /ingest (upload PDF)                             │
│  - GET /status/{job_id}                                  │
│  - DELETE /ingest/{job_id}                               │
│  - Writes to: File-based Vector Store                    │
└─────────────────────────────────────────────────────────┘
                          │
                          │ Writes vectors
                          ▼
              ┌───────────────────────┐
              │   File-Based Vector   │
              │   Store (shared file) │
              │   data/vector_store.pkl│
              └───────────────────────┘
                          │
                          │ Reads vectors
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    Chat Service                         │
│  Port: 8002                                              │
│  - POST /api/chat (user queries)                        │
│  - GET /api/documents (list PDFs)                       │
│  - GET /api/documents/{file}/file (serve PDF)           │
│  - Reads from: File-based Vector Store                  │
└─────────────────────────────────────────────────────────┘
```

## Directory Structure

```
ai-chat-with-kb-backend/
├── shared/                    # Shared code
│   ├── models/
│   │   └── schemas.py
│   ├── services/
│   │   ├── vector_store.py    # Includes FileBasedVectorStore
│   │   ├── ingestion_service.py
│   │   └── embedding_service.py
│   ├── utils/
│   │   ├── pdf_extractor.py
│   │   ├── chunker.py
│   │   └── ...
│   └── config/
│       ├── config.py
│       └── pdf_metadata.json
│
├── ingestion-service/
│   └── api/
│       └── main.py            # Ingestion endpoints
│
├── chat-service/
│   └── api/
│       └── main.py           # Chat endpoints
│
├── docker-compose.yml         # Orchestrates both services
├── Dockerfile.ingestion       # Ingestion service image
├── Dockerfile.chat            # Chat service image
└── requirements.txt           # Shared dependencies
```

## File-Based Vector Store

The file-based vector store (`FileBasedVectorStore`) stores vectors in a pickle file that can be shared between processes:

- **Location**: `data/vector_store.pkl` (configurable via `VECTOR_STORE_PATH`)
- **Format**: Pickle file containing list of `DocumentChunk` objects
- **Thread-safe**: Uses file locking to prevent concurrent write conflicts
- **Auto-reload**: Chat service reloads from file on each search to get latest data

### Configuration

Set in `.env`:
```env
VECTOR_STORE_TYPE=file
VECTOR_STORE_PATH=data/vector_store.pkl
```

## Running the Services

### Option 1: Docker Compose (Recommended)

```bash
# Start both services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 2: Manual (Development)

**Terminal 1 - Ingestion Service:**
```bash
cd /path/to/ai-chat-with-kb-backend
uvicorn ingestion-service.api.main:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2 - Chat Service:**
```bash
cd /path/to/ai-chat-with-kb-backend
uvicorn chat-service.api.main:app --host 0.0.0.0 --port 8002 --reload
```

## API Endpoints

### Ingestion Service (Port 8001)

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /ingest` - Upload and ingest PDF
- `GET /status/{job_id}` - Get ingestion job status
- `DELETE /ingest/{job_id}` - Delete ingestion job

### Chat Service (Port 8002)

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /api/chat` - Process chat query
- `GET /api/documents` - List all PDFs
- `GET /api/documents/{file_name}/file` - Serve PDF file

## Frontend Configuration

Update frontend to point to chat service:

```typescript
// In frontend .env or config
VITE_API_BASE_URL=http://localhost:8002
```

## Shared Resources

Both services share:
- **Vector Store File**: `data/vector_store.pkl`
- **PDF Files**: `downloads/` directory
- **Configuration**: `shared/config/pdf_metadata.json`
- **Logs**: `logs/` directory (separate log files per service)

## Benefits

1. **Separation of Concerns**: Ingestion and querying are independent
2. **Independent Scaling**: Scale each service based on load
3. **Independent Deployment**: Deploy updates to one service without affecting the other
4. **Fault Isolation**: If one service fails, the other continues working
5. **Resource Optimization**: Different resource requirements per service

## Migration from Single Backend

The original `api/main.py` is still available for backward compatibility. To migrate:

1. Update frontend to use chat service (port 8002)
2. Use ingestion service (port 8001) for PDF uploads
3. Ensure `VECTOR_STORE_TYPE=file` in `.env`

## Troubleshooting

### Issue: Services can't find shared code

**Solution**: Ensure you're running from the project root directory, and `shared/` directory exists.

### Issue: Vector store file not found

**Solution**: 
- Create `data/` directory: `mkdir -p data`
- Ensure `VECTOR_STORE_PATH` is set correctly in `.env`

### Issue: Import errors in shared code

**Solution**: All shared files use `shared.` prefix for imports. Ensure imports are correct.

### Issue: File locking conflicts

**Solution**: The file-based store uses thread locks. If you see conflicts, ensure only one process writes at a time (ingestion service writes, chat service only reads).

## Next Steps

- [ ] Add service discovery (if needed)
- [ ] Add load balancing
- [ ] Add monitoring and metrics
- [ ] Add health check endpoints
- [ ] Consider message queue for async ingestion


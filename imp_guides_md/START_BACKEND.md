# How to Start the Backend Services

## Overview

The backend has been split into two separate services:
- **Ingestion Service** (Port 8001): Handles PDF vectorization
- **Chat Service** (Port 8002): Handles user queries and document serving

Both services share a file-based vector store for data consistency.

## Quick Start (Recommended)

### Option 1: Run Both Services (Recommended)

```bash
cd /Users/dheerajmehra/Documents/projects/ai-chat-with-knowledgebase/ai-chat-with-kb-backend
./run_server.sh
```

This will start both services in the background. Press `Ctrl+C` to stop both.

**Note:** Make sure the script is executable:
```bash
chmod +x run_server.sh
```

### Option 2: Run Services Separately

**Terminal 1 - Ingestion Service:**
```bash
cd /Users/dheerajmehra/Documents/projects/ai-chat-with-knowledgebase/ai-chat-with-kb-backend
./run_ingestion.sh
```

**Terminal 2 - Chat Service:**
```bash
cd /Users/dheerajmehra/Documents/projects/ai-chat-with-knowledgebase/ai-chat-with-kb-backend
./run_chat.sh
```

### Option 3: Manual Start

**Terminal 1 - Ingestion Service:**
```bash
cd /Users/dheerajmehra/Documents/projects/ai-chat-with-knowledgebase/ai-chat-with-kb-backend
source venv/bin/activate
uvicorn ingestion_service.api.main:app --reload --host 0.0.0.0 --port 8001
```

**Terminal 2 - Chat Service:**
```bash
cd /Users/dheerajmehra/Documents/projects/ai-chat-with-knowledgebase/ai-chat-with-kb-backend
source venv/bin/activate
uvicorn chat_service.api.main:app --reload --host 0.0.0.0 --port 8002
```

## Step-by-Step Instructions

### Step 1: Navigate to Project Directory
```bash
cd /Users/dheerajmehra/Documents/projects/ai-chat-with-knowledgebase/ai-chat-with-kb-backend
```

### Step 2: Activate Virtual Environment

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt when activated.

### Step 3: Start the Services

**Option A: Both Services (Single Command)**
```bash
./run_server.sh both
```

**Option B: Individual Services**
```bash
# Terminal 1
./run_server.sh ingestion

# Terminal 2 (new terminal)
./run_server.sh chat
```

### Step 4: Verify Services are Running

You should see output like:

**Ingestion Service:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Application startup complete.
```

**Chat Service:**
```
INFO:     Uvicorn running on http://0.0.0.0:8002 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Application startup complete.
```

### Step 5: Test the Services

**Ingestion Service:**
- **API Docs**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health
- **Root**: http://localhost:8001/

**Chat Service:**
- **API Docs**: http://localhost:8002/docs
- **Health Check**: http://localhost:8002/health
- **Root**: http://localhost:8002/

## Service Endpoints

### Ingestion Service (Port 8001)

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /ingest` - Upload and ingest PDF
- `GET /status/{job_id}` - Check ingestion status
- `DELETE /ingest/{job_id}` - Delete ingestion job
- `GET /docs` - Swagger API documentation

### Chat Service (Port 8002)

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /api/chat` - Process chat query
- `GET /api/documents` - List all PDFs
- `GET /api/documents/{file_name}/file` - Serve PDF file
- `GET /docs` - Swagger API documentation

## Troubleshooting

### Issue: "ModuleNotFoundError" or "No module named 'fastapi'"

**Solution:** Make sure virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Port 8001/8002 already in use"

**Solution:** 
- Check if services are already running: `lsof -i :8001` or `lsof -i :8002`
- Kill existing processes: `pkill -f "uvicorn.*8001"` or `pkill -f "uvicorn.*8002"`
- Or use different ports (update the scripts)

### Issue: "Permission denied" when running scripts

**Solution:** Make scripts executable:
```bash
chmod +x run_server.sh run_ingestion.sh run_chat.sh
```

### Issue: Virtual environment not found

**Solution:** Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: Vector store file not found

**Solution:** 
- Create data directory: `mkdir -p data`
- Ensure `VECTOR_STORE_TYPE=file` in `.env`
- Ensure `VECTOR_STORE_PATH=data/vector_store.pkl` in `.env`

### Issue: Services can't find shared code

**Solution:** 
- Ensure you're running from the project root directory
- Ensure `shared/` directory exists with all required files
- Check that imports use `shared.` prefix

## Environment Setup (First Time Only)

If you haven't set up the environment yet:

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate it:**
   ```bash
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create .env file:**
   ```bash
   cp env.example .env
   # Edit .env with your settings
   ```

5. **Set vector store type in .env:**
   ```env
   VECTOR_STORE_TYPE=file
   VECTOR_STORE_PATH=data/vector_store.pkl
   PDF_LIBRARY=pdfplumber  # or pymupdf
   ```

6. **Create data directory:**
   ```bash
   mkdir -p data
   ```

## Stopping the Services

**If running both services together:**
- Press `CTRL+C` in the terminal (stops both)

**If running separately:**
- Press `CTRL+C` in each terminal

**To stop background processes:**
```bash
pkill -f "uvicorn.*ingestion_service"
pkill -f "uvicorn.*chat_service"
```

## Running in Background (Optional)

To run services in the background:

**Ingestion Service:**
```bash
nohup uvicorn ingestion_service.api.main:app --reload --host 0.0.0.0 --port 8001 > ingestion.log 2>&1 &
```

**Chat Service:**
```bash
nohup uvicorn chat_service.api.main:app --reload --host 0.0.0.0 --port 8002 > chat.log 2>&1 &
```

**To stop:**
```bash
pkill -f "uvicorn.*ingestion_service"
pkill -f "uvicorn.*chat_service"
```

## Using Docker Compose (Alternative)

If you prefer Docker:

```bash
# Start both services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

See `SPLIT_ARCHITECTURE_GUIDE.md` for more details.

## Next Steps

Once the backend services are running:

1. **Start the frontend** (in a separate terminal):
   ```bash
   cd /Users/dheerajmehra/Documents/projects/ai-chat-with-knowledgebase/ai-chat-with-kb-frontend
   npm run dev
   ```

2. **Update frontend configuration:**
   - Point frontend to chat service: `http://localhost:8002`
   - Update `VITE_API_BASE_URL` in frontend `.env` if needed

3. **Test the integration:**
   - Frontend: http://localhost:8080
   - Ingestion Service: http://localhost:8001
   - Chat Service: http://localhost:8002
   - API Docs: http://localhost:8002/docs

## Quick Reference

```bash
# Run both services
./run_server.sh

# Run only ingestion service
./run_server.sh ingestion

# Run only chat service
./run_server.sh chat

# Manual start (both in separate terminals)
uvicorn ingestion_service.api.main:app --reload --host 0.0.0.0 --port 8001
uvicorn chat_service.api.main:app --reload --host 0.0.0.0 --port 8002
```

## Architecture Notes

- Both services share the same file-based vector store (`data/vector_store.pkl`)
- Ingestion service writes to the vector store
- Chat service reads from the vector store (auto-reloads on each search)
- Services can be run independently or together
- See `SPLIT_ARCHITECTURE_GUIDE.md` for detailed architecture information

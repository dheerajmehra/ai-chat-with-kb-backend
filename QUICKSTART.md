# Quick Start Guide

## 1. Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (pdfplumber is included by default)
pip install -r requirements.txt
```

### PDF Library Selection

The pipeline supports two PDF extraction libraries. **You must specify which one to use in your `.env` file:**

**Option 1: pdfplumber (Default - Recommended)**
- ✅ Works on all Python versions (3.8+)
- ✅ Easy installation, no build dependencies
- ✅ Good for text extraction
- Already included in requirements.txt
- Set in `.env`: `PDF_LIBRARY=pdfplumber`

**Option 2: PyMuPDF (Optional - Faster)**
- ✅ Faster extraction
- ✅ Better for complex PDFs
- ❌ May not work on Python 3.13 (no pre-built wheels)
- ❌ Requires build tools on some systems
- Set in `.env`: `PDF_LIBRARY=pymupdf`

**To use PyMuPDF:**
1. Install it: `pip install PyMuPDF>=1.23.0` (or use conda for Python 3.13)
2. Set in `.env`: `PDF_LIBRARY=pymupdf`

**Important:** The library specified in `.env` must be installed. The code will raise a clear error if the specified library is not available.

## 2. Configuration

Create a `.env` file in the project root (copy from `env.example`):

```env
# Application Settings
APP_NAME=DFSA RAG Ingestion Pipeline
LOG_LEVEL=INFO

# PDF Processing Library (required)
PDF_LIBRARY=pdfplumber  # Options: pdfplumber, pymupdf
# Must match the library you have installed. Default is pdfplumber.

# Vector Store (choose one)
VECTOR_STORE_TYPE=local  # Options: azure, openai, local
EMBEDDING_PROVIDER=sentence-transformers  # Options: openai, azure, sentence-transformers

# For Azure AI Search (if using)
AZURE_SEARCH_ENDPOINT=https://your-service.search.windows.net
AZURE_SEARCH_KEY=your-key
AZURE_SEARCH_INDEX_NAME=dfsa-rulebooks

# For Azure OpenAI (if using)
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT_NAME=text-embedding-ada-002

# For OpenAI (if using)
OPENAI_API_KEY=your-key

# Chunking Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

## 3. Set Up Azure AI Search (Optional)

If using Azure AI Search, create the index:

```bash
python scripts/setup_azure_index.py
```

## 4. Start the Server

**IMPORTANT:** Make sure your virtual environment is activated first!

```bash
# Activate virtual environment
source venv/bin/activate

# Then run the server
# Run both services (recommended)
./run_server.sh

# Or run individually:
# Terminal 1: Ingestion Service
uvicorn ingestion-service.api.main:app --reload --host 0.0.0.0 --port 8001

# Terminal 2: Chat Service
uvicorn chat-service.api.main:app --reload --host 0.0.0.0 --port 8002
```

**Or use the helper script:**
```bash
./run_server.sh
```

**Troubleshooting:** If you get `ModuleNotFoundError`, make sure:
1. Virtual environment is activated (you should see `(venv)` in your prompt)
2. Dependencies are installed: `pip install -r requirements.txt`

## 5. Test the API

### Health Check
```bash
curl http://localhost:8000/health
```

### Ingest a PDF
```bash
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@downloads/DFSA1547_15954_VER260126.pdf"
```

### Check Status
```bash
curl http://localhost:8000/status/{job_id}
```

## 6. View API Documentation

Open your browser to:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Troubleshooting

### Import Errors
Make sure you're in the project root directory and the virtual environment is activated.

### PDF Extraction Issues
If PDFs fail to extract, check:
1. PDF is not corrupted
2. PDF is not password-protected
3. At least one PDF library is installed (pdfplumber or PyMuPDF)
4. Run `python test_installation.py` to verify PDF libraries

**Common Issues:**
- **"No PDF library available"**: Install pdfplumber: `pip install pdfplumber`
- **PyMuPDF build errors**: Use pdfplumber instead or install via conda
- **Python 3.13 compatibility**: Use pdfplumber (recommended) or conda-installed PyMuPDF

### Azure Connection Issues
Verify:
1. Azure credentials are correct
2. Index exists (run setup script)
3. Network connectivity to Azure

### Embedding Errors
Check:
1. API keys are set correctly
2. Model names match your deployment
3. Rate limits not exceeded


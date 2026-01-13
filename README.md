# DFSA Rulebook RAG Ingestion Pipeline

A FastAPI-based agentic RAG (Retrieval-Augmented Generation) ingestion pipeline for processing Dubai Financial Services Authority (DFSA) rulebook PDFs into a vector store.

## Overview

This project processes DFSA rulebook PDFs with structure-aware extraction, intelligent chunking, and configurable vectorization and storage options. The pipeline is designed to handle the hierarchical structure of DFSA rulebooks (modules, chapters, sections, subsections) and preserve this structure in metadata.

## Features

- **Structure-Aware PDF Extraction**: Extracts text while preserving DFSA rulebook hierarchy (modules, chapters, sections, subsections)
- **Intelligent Chunking**: Rule-aware chunker that respects sentence and section boundaries
- **Multiple Embedding Providers**: Support for OpenAI, Azure OpenAI, and Sentence Transformers
- **Multiple Vector Stores**: Support for Azure AI Search, OpenAI Vector Store, and local in-memory store
- **Asynchronous Processing**: Background task processing with job status tracking
- **Comprehensive Metadata**: Granular metadata for each chunk including hierarchy path, rule numbers, page numbers, etc.
- **Highly Configurable**: Environment-based configuration for all services

## Project Structure

```
.
├── shared/                   # Shared code for both services
│   ├── models/              # Pydantic models
│   ├── services/            # Core services (vector store, embedding, ingestion)
│   ├── utils/               # Utilities (PDF extraction, chunking, etc.)
│   └── config/              # Configuration files
├── ingestion-service/        # PDF vectorization service (Port 8001)
│   └── api/
│       └── main.py          # Ingestion endpoints
├── chat-service/            # Chat and document serving service (Port 8002)
│   └── api/
│       └── main.py          # Chat endpoints
├── api/                     # Legacy single-backend (for backward compatibility)
│   └── main.py              # Combined endpoints
├── config.py                # Configuration management
├── requirements.txt         # Python dependencies
├── docker-compose.yml       # Docker orchestration for both services
├── run_server.sh            # Helper script to run services
├── .env.example             # Example environment variables
└── README.md                # This file
```

**Note:** The project now uses a **split architecture** with separate ingestion and chat services. See `SPLIT_ARCHITECTURE_GUIDE.md` for details.

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-chat-with-kb-backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy and configure environment variables:
```bash
cp env.example .env
# Edit .env with your configuration
# IMPORTANT: Set PDF_LIBRARY=pdfplumber (default) or PDF_LIBRARY=pymupdf
```

## Configuration

### Data Framework Selection

The project uses **Pandas** for data manipulation and processing. For larger-scale processing, you could consider:
- **Dask**: For parallel and distributed computing
- **Polars**: For high-performance dataframes
- **Pandas**: Current choice (good balance of features and performance)

**Would you like to switch to a different data framework?** Please let me know your preference.

### PDF Library Selection

**IMPORTANT**: You must specify which PDF library to use in your `.env` file:

1. **pdfplumber** (default, recommended)
   - Works on all Python versions (3.8+)
   - Easy installation, no build dependencies
   - Set in `.env`: `PDF_LIBRARY=pdfplumber`

2. **PyMuPDF** (optional, faster)
   - Faster extraction
   - Better for complex PDFs
   - May require special installation on Python 3.13
   - Set in `.env`: `PDF_LIBRARY=pymupdf`
   - Install: `pip install PyMuPDF` (or use conda for Python 3.13)

The code will raise a clear error if the specified library is not installed.

### Vectorization Options

1. **OpenAI Embeddings** (default)
   - Model: `text-embedding-ada-002`
   - Requires: `OPENAI_API_KEY`

2. **Azure OpenAI Embeddings**
   - Model: Configurable deployment
   - Requires: Azure OpenAI endpoint and API key

3. **Sentence Transformers** (local)
   - Model: `all-MiniLM-L6-v2` (configurable)
   - No API required, runs locally

### Vector Store Options

1. **Azure AI Search** (recommended for production)
   - Fully managed search service
   - Requires: Azure Search endpoint, key, and index name
   - **Note**: You'll need to create the index with vector fields. See setup instructions below.

2. **OpenAI Vector Store**
   - Managed by OpenAI
   - Requires: OpenAI API key

3. **Local Vector Store** (for development/testing)
   - In-memory storage
   - No external dependencies

## Azure AI Search Index Setup

If using Azure AI Search, create an index with the following schema:

```json
{
  "name": "dfsa-rulebooks",
  "fields": [
    {
      "name": "id",
      "type": "Edm.String",
      "key": true
    },
    {
      "name": "content",
      "type": "Edm.String",
      "searchable": true
    },
    {
      "name": "contentVector",
      "type": "Collection(Edm.Single)",
      "dimensions": 1536,
      "vectorSearchProfile": "default-vector-profile"
    },
    {
      "name": "file_name",
      "type": "Edm.String",
      "filterable": true
    },
    {
      "name": "module_code",
      "type": "Edm.String",
      "filterable": true
    },
    {
      "name": "rule_number",
      "type": "Edm.String",
      "filterable": true
    },
    {
      "name": "page_number",
      "type": "Edm.Int32",
      "filterable": true
    },
    {
      "name": "hierarchy_path",
      "type": "Edm.String",
      "filterable": true
    }
  ],
  "vectorSearch": {
    "profiles": [
      {
        "name": "default-vector-profile",
        "algorithm": "default-algorithm"
      }
    ],
    "algorithms": [
      {
        "name": "default-algorithm",
        "kind": "hnsw"
      }
    ]
  }
}
```

## Usage

### Start the Server

```bash
# Run both services (recommended)
./run_server.sh

# Or run individually:
# Terminal 1: Ingestion Service (Port 8001)
uvicorn ingestion-service.api.main:app --reload --host 0.0.0.0 --port 8001

# Terminal 2: Chat Service (Port 8002)
uvicorn chat-service.api.main:app --reload --host 0.0.0.0 --port 8002
```

**Ingestion Service** will be available at `http://localhost:8001` with interactive docs at `http://localhost:8001/docs`.

**Chat Service** will be available at `http://localhost:8002` with interactive docs at `http://localhost:8002/docs`.

### Ingest a PDF

```bash
curl -X POST "http://localhost:8001/ingest" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/rulebook.pdf"
```

Response:
```json
{
  "job_id": "uuid-here",
  "status": "processing",
  "message": "File rulebook.pdf is being processed",
  "timestamp": "2024-01-01T00:00:00"
}
```

### Check Job Status

```bash
curl "http://localhost:8001/status/{job_id}"
```

Response:
```json
{
  "job_id": "uuid-here",
  "status": "completed",
  "total_chunks": 150,
  "total_pages": 45,
  "processing_time_seconds": 12.5,
  "error_message": null
}
```

## DFSA Rulebook Structure

DFSA rulebooks follow a hierarchical structure:

- **Module Level**: e.g., "GEN" (General Module), "GLO" (Glossary Module)
- **Chapter Level**: e.g., "1 Introduction", "2 General Requirements"
- **Section Level**: e.g., "2.1 Scope", "2.2 Definitions"
- **Subsection Level**: e.g., "2.1.1 Application", "2.1.2 Exemptions"
- **Rule Numbers**: e.g., "GEN 2.1.1" (Module + Section)

The extraction and chunking logic is designed to preserve this hierarchy in metadata.

## Best Practices

1. **Chunking**: The chunker respects section boundaries and sentence boundaries to avoid breaking context
2. **Metadata**: Each chunk includes comprehensive metadata for precise retrieval
3. **Error Handling**: Robust error handling for corrupted PDFs and API failures
4. **Logging**: Comprehensive logging for debugging and monitoring
5. **Configuration**: All settings are configurable via environment variables

## Next Steps

The user asked: **"Would you like me to provide the specific Python function for the 'Rule-Aware' chunker to ensure it doesn't break rules in the middle of a sentence?"**

The current implementation already includes rule-aware chunking that:
- Respects section boundaries
- Respects sentence boundaries
- Maintains hierarchy information
- Handles overlap between chunks

However, if you'd like to enhance it further or have specific requirements, please let me know!

## License

[Your License Here]


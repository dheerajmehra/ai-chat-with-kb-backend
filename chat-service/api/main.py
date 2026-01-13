"""FastAPI chat service - handles user queries and document serving."""
import sys
from pathlib import Path

# Add parent directory to path to access shared code
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import uuid
from typing import List, Dict, Any
from datetime import datetime
from shared.models.schemas import (
    ChatRequest, ChatResponse, ReferenceResponse
)
from shared.services.embedding_service import get_embedding_service
from shared.services.vector_store import get_vector_store
from shared.services.llm_service import get_llm_service
from shared.config import get_settings
from shared.utils.logger import logger
from shared.utils.metadata_loader import MetadataLoader

settings = get_settings()
app = FastAPI(
    title="DFSA RAG Chat Service",
    version=settings.app_version,
    description="Chat and document serving service for DFSA Rulebooks"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",  # Frontend dev server
        "http://localhost:3000",  # Alternative port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create logs directory
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "DFSA RAG Chat Service",
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "vector_store": settings.vector_store_type,
        "embedding_provider": settings.embedding_provider
    }


def get_pdf_page_count(file_path: Path) -> int:
    """
    Get page count from PDF file.
    Tries pdfplumber first, falls back to PyPDF2 if available.
    """
    try:
        import pdfplumber
        with pdfplumber.open(str(file_path)) as pdf:
            return len(pdf.pages)
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Error getting page count with pdfplumber for {file_path}: {e}")
    
    try:
        import PyPDF2
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            return len(pdf_reader.pages)
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Error getting page count with PyPDF2 for {file_path}: {e}")
    
    logger.warning(f"Could not determine page count for {file_path}")
    return 0


@app.get("/api/documents")
async def get_documents():
    """
    Get list of all configured PDF documents.
    Returns PDFs from pdf_metadata.json that exist in downloads folder.
    """
    metadata_loader = MetadataLoader()
    downloads_dir = Path("downloads")
    documents: List[Dict[str, Any]] = []
    
    if not downloads_dir.exists():
        logger.warning(f"Downloads directory not found: {downloads_dir}")
        return {"documents": []}
    
    for file_name, metadata in metadata_loader.get_all_metadata().items():
        file_path = downloads_dir / file_name
        if file_path.exists():
            try:
                file_size = file_path.stat().st_size
                file_mtime = file_path.stat().st_mtime
                
                # Get page count from PDF
                page_count = get_pdf_page_count(file_path)
                
                documents.append({
                    "id": file_name,  # Using file_name as ID
                    "file_name": file_name,
                    "alias": metadata.get("alias", file_name),
                    "module_code": metadata.get("module_code", ""),
                    "module_name": metadata.get("module_name", ""),
                    "description": metadata.get("description", ""),
                    "size": file_size,
                    "page_count": page_count,
                    "url": f"/api/documents/{file_name}/file",
                    "uploaded_at": datetime.fromtimestamp(file_mtime).isoformat()
                })
            except Exception as e:
                logger.error(f"Error processing file {file_name}: {e}")
                continue
    
    logger.info(f"Returning {len(documents)} documents")
    return {"documents": documents}


@app.get("/api/documents/{file_name}/file")
async def get_pdf_file(file_name: str):
    """Serve PDF file for viewing."""
    # Validate file name (prevent directory traversal)
    if ".." in file_name or "/" in file_name or "\\" in file_name:
        raise HTTPException(status_code=400, detail="Invalid file name")
    
    # Check if file is configured
    metadata_loader = MetadataLoader()
    if not metadata_loader.has_metadata(file_name):
        raise HTTPException(
            status_code=404,
            detail=f"PDF '{file_name}' is not configured"
        )
    
    # Construct file path
    file_path = Path("downloads") / file_name
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"PDF file '{file_name}' not found"
        )
    
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=file_name,
        headers={
            "Content-Disposition": f'inline; filename="{file_name}"'
        }
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_documents(request: ChatRequest):
    """
    Process a chat query, search the vector store, and return relevant chunks.
    Optionally uses LLM to generate a response based on retrieved chunks.
    """
    try:
        embedding_service = get_embedding_service()
        vector_store = get_vector_store()

        # 1. Embed the user's query
        query_embedding = await embedding_service.embed_text(request.message)

        # 2. Search the vector store
        relevant_chunks = await vector_store.search(
            query_embedding, 
            top_k=request.top_k
        )
        
        if not relevant_chunks:
            return ChatResponse(
                message=f"No relevant information found for your query: '{request.message}'. Try rephrasing or check if relevant documents have been ingested.",
                references=[]
            )
        
        # Step 3: Map chunks to reference responses (always include for citation)
        references: List[ReferenceResponse] = []
        for chunk in relevant_chunks:
            # Generate unique ID for reference
            ref_id = f"{chunk.metadata.file_name}_{chunk.metadata.chunk_index}_{uuid.uuid4().hex[:8]}"
            
            # Get document alias/name from metadata
            document_name = chunk.metadata.alias or chunk.metadata.module_name or chunk.metadata.file_name
            
            # Get similarity score from chunk metadata (stored by vector store search)
            score = chunk.metadata.custom_metadata.get('similarity_score', 0.0)
            
            reference = ReferenceResponse(
                id=ref_id,
                document_id=chunk.metadata.file_name,
                document_name=document_name,
                page_number=chunk.metadata.page_number,
                chunk_text=chunk.content[:500],  # Limit text length for response
                score=score,
                module_code=chunk.metadata.module_code,
                module_name=chunk.metadata.module_name,
                rule_number=chunk.metadata.rule_number,
                hierarchy_path=chunk.metadata.hierarchy_path
            )
            references.append(reference)
        
        # Step 4: Determine if LLM should be used
        # Priority: request.use_llm > config.llm_enabled
        use_llm = request.use_llm if request.use_llm is not None else settings.llm_enabled
        
        # Step 5: Generate response message
        if use_llm:
            try:
                llm_service = get_llm_service()
                if llm_service.is_enabled():
                    # Generate LLM response
                    message = await llm_service.generate_response(
                        user_query=request.message,
                        chunks=relevant_chunks
                    )
                    logger.info(f"Generated LLM response for query (using {len(references)} chunks)")
                else:
                    # LLM requested but not enabled, fall back to default message
                    logger.warning("LLM requested but not enabled in configuration, using default message")
                    message = _format_default_message(references)
            except Exception as e:
                logger.error(f"Error generating LLM response: {e}", exc_info=True)
                # Fall back to default message on LLM error
                message = _format_default_message(references)
                message += f" (Note: LLM response generation failed: {str(e)})"
        else:
            # Use default message format
            message = _format_default_message(references)
        
        return ChatResponse(
            message=message,
            references=references
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


def _format_default_message(references: List[ReferenceResponse]) -> str:
    """Format default response message when LLM is not used."""
    if len(references) == 1:
        message = f"Found 1 relevant result for your query."
    else:
        message = f"Found {len(references)} relevant results for your query."
    
    # Add summary of modules found
    modules_found = set(ref.module_code for ref in references if ref.module_code)
    if modules_found:
        modules_str = ", ".join(sorted(modules_found))
        message += f" Results from: {modules_str}."
    
    return message


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)


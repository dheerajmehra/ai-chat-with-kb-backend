"""FastAPI ingestion service - handles PDF vectorization."""
import sys
from pathlib import Path

# Add parent directory to path to access shared code
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import aiofiles
import uuid
from typing import Optional
from shared.models.schemas import (
    IngestResponse, ProcessingStatus, ProcessingResult
)
from shared.services.ingestion_service import IngestionService
from shared.config import get_settings
from shared.utils.logger import logger

settings = get_settings()
app = FastAPI(
    title="DFSA RAG Ingestion Service",
    version=settings.app_version,
    description="PDF vectorization service for DFSA Rulebooks"
)

# Initialize services
ingestion_service = IngestionService()

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Create logs directory
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


@app.on_event("startup")
async def startup_event():
    """
    Startup event handler.
    Automatically ingests all configured PDFs when using local/file vector store.
    """
    if settings.vector_store_type.lower() not in ["local", "file"]:
        logger.info(
            f"Vector store type is '{settings.vector_store_type}', "
            "skipping automatic PDF ingestion on startup."
        )
        return
    
    logger.info("=" * 80)
    logger.info("STARTUP: Automatic PDF Ingestion for Local/File Vector Store")
    logger.info("=" * 80)
    
    try:
        from shared.utils.metadata_loader import MetadataLoader
        from shared.services.vector_store import get_vector_store
        
        metadata_loader = MetadataLoader()
        vector_store = get_vector_store()
        
        # Check if vector store already has chunks
        chunk_count = 0
        if hasattr(vector_store, 'get_chunk_count'):
            chunk_count = vector_store.get_chunk_count()
        elif hasattr(vector_store, 'chunks'):
            chunk_count = len(vector_store.chunks)
        
        if chunk_count > 0:
            logger.info(
                f"Vector store already contains {chunk_count} chunks. "
                "Skipping automatic ingestion to avoid duplicates."
            )
            logger.info("If you want to re-ingest, delete the vector store file and restart.")
            return
        
        # Get all configured PDFs
        all_metadata = metadata_loader.get_all_metadata()
        downloads_dir = Path("downloads")
        
        if not downloads_dir.exists():
            logger.warning(f"Downloads directory not found: {downloads_dir}")
            return
        
        # Find PDFs that exist and are configured
        pdfs_to_ingest = []
        for file_name, metadata in all_metadata.items():
            file_path = downloads_dir / file_name
            if file_path.exists():
                pdfs_to_ingest.append((file_name, metadata))
                logger.info(
                    f"  ✓ {file_name} ({metadata.get('alias', 'N/A')}) - Found"
                )
            else:
                logger.warning(f"  ✗ {file_name} - Not found in downloads/")
        
        if not pdfs_to_ingest:
            logger.info("No PDFs found to ingest.")
            return
        
        logger.info(f"\nStarting automatic ingestion of {len(pdfs_to_ingest)} PDF(s)...\n")
        
        # Ingest each PDF sequentially
        total_chunks = 0
        total_pages = 0
        successful = 0
        failed = 0
        
        for file_name, metadata in pdfs_to_ingest:
            file_path = downloads_dir / file_name
            logger.info("=" * 80)
            logger.info(f"Ingesting: {file_name}")
            logger.info(
                f"Alias: {metadata.get('alias', 'N/A')} | "
                f"Module: {metadata.get('module_code', 'N/A')}"
            )
            logger.info("=" * 80)
            
            try:
                job_id = f"startup_{file_name}"
                result = await ingestion_service.ingest_pdf(str(file_path), job_id)
                
                if result.status == ProcessingStatus.COMPLETED:
                    total_chunks += result.total_chunks
                    total_pages += result.total_pages
                    successful += 1
                    logger.info(
                        f"✓ Successfully ingested {file_name}: "
                        f"{result.total_chunks} chunks, {result.total_pages} pages "
                        f"in {result.processing_time_seconds:.2f}s"
                    )
                else:
                    failed += 1
                    error_msg = result.error_message or f"Status: {result.status}"
                    logger.error(
                        f"✗ Failed to ingest {file_name}: {error_msg}"
                    )
            except Exception as e:
                failed += 1
                logger.error(f"✗ Error ingesting {file_name}: {e}", exc_info=True)
        
        # Summary
        logger.info("=" * 80)
        logger.info("AUTOMATIC INGESTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total PDFs processed: {len(pdfs_to_ingest)}")
        logger.info(f"  ✓ Successful: {successful}")
        logger.info(f"  ✗ Failed: {failed}")
        logger.info(f"Total chunks ingested: {total_chunks}")
        logger.info(f"Total pages processed: {total_pages}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error during startup ingestion: {e}", exc_info=True)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "DFSA RAG Ingestion Service",
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


@app.post("/ingest", response_model=IngestResponse)
async def ingest_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Ingest a PDF file into the vector store.
    
    This endpoint accepts a PDF file and processes it asynchronously.
    Returns immediately with a job ID for tracking.
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    # Check if PDF is configured
    from shared.utils.metadata_loader import MetadataLoader
    metadata_loader = MetadataLoader()
    if not metadata_loader.has_metadata(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"PDF '{file.filename}' is not configured in pdf_metadata.json. "
                   "Only PDFs listed in the configuration file can be processed."
        )
    
    # Validate file size
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    max_size = settings.max_file_size_mb * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum of {settings.max_file_size_mb}MB"
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Save file temporarily
    file_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        logger.info(f"Received file {file.filename} (job_id: {job_id})")
        
        # Add background task
        background_tasks.add_task(
            process_pdf_background,
            str(file_path),
            job_id
        )
        
        return IngestResponse(
            job_id=job_id,
            status=ProcessingStatus.PROCESSING,
            message=f"File {file.filename} is being processed"
        )
        
    except Exception as e:
        logger.error(f"Error handling upload: {e}")
        # Clean up file if it was created
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )


async def process_pdf_background(pdf_path: str, job_id: str):
    """
    Background task to process PDF.
    
    Args:
        pdf_path: Path to the PDF file
        job_id: Job identifier
    """
    try:
        logger.info(f"Starting background processing for job {job_id}")
        result = await ingestion_service.ingest_pdf(pdf_path, job_id)
        
        # Clean up temporary file
        file_path = Path(pdf_path)
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Cleaned up temporary file: {pdf_path}")
        
        logger.info(f"Background processing completed for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error in background processing for job {job_id}: {e}")
        # Ensure file is cleaned up even on error
        file_path = Path(pdf_path)
        if file_path.exists():
            file_path.unlink()


@app.get("/status/{job_id}", response_model=ProcessingResult)
async def get_status(job_id: str):
    """
    Get the status of an ingestion job.
    
    Args:
        job_id: Job identifier returned from /ingest endpoint
    """
    result = ingestion_service.get_job_status(job_id)
    
    if result.status == ProcessingStatus.PENDING:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )
    
    return result


@app.delete("/ingest/{job_id}")
async def delete_ingestion(job_id: str):
    """
    Delete an ingestion job and its associated data.
    
    Args:
        job_id: Job identifier
    """
    result = ingestion_service.get_job_status(job_id)
    
    if result.status == ProcessingStatus.PENDING:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )
    
    return {
        "message": f"Job {job_id} deletion requested",
        "status": "success"
    }


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
    uvicorn.run(app, host="0.0.0.0", port=8001)


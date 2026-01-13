"""Main ingestion service orchestrating the pipeline."""
import uuid
import time
from typing import Dict
from pathlib import Path
from shared.models.schemas import ProcessingStatus, ProcessingResult, DocumentChunk
from shared.utils.pdf_extractor import DFSAExtractor
from shared.utils.metadata_loader import MetadataLoader
from shared.utils.chunking_strategy_factory import ChunkingStrategyFactory
from shared.services.embedding_service import get_embedding_service
from shared.services.vector_store import get_vector_store
from shared.utils.logger import logger
from shared.config import get_settings

settings = get_settings()


class IngestionService:
    """Service for ingesting PDF documents into the vector store."""
    
    def __init__(self):
        self.metadata_loader = MetadataLoader()
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()
        self.job_status: Dict[str, ProcessingResult] = {}
    
    async def ingest_pdf(self, pdf_path: str, job_id: str = None) -> ProcessingResult:
        """
        Ingest a PDF file into the vector store.
        
        Args:
            pdf_path: Path to the PDF file
            job_id: Optional job ID (will be generated if not provided)
            
        Returns:
            ProcessingResult with ingestion status
        """
        if job_id is None:
            job_id = str(uuid.uuid4())
        
        start_time = time.time()
        
        try:
            logger.info(f"Starting ingestion for {pdf_path} (job_id: {job_id})")
            
            # Update status
            result = ProcessingResult(
                job_id=job_id,
                status=ProcessingStatus.PROCESSING,
                total_chunks=0,
                total_pages=0,
                processing_time_seconds=0
            )
            self.job_status[job_id] = result
            
            # Step 0: Load metadata and validate PDF is in config
            file_name = Path(pdf_path).name
            if not self.metadata_loader.has_metadata(file_name):
                raise ValueError(
                    f"PDF '{file_name}' is not configured in pdf_metadata.json. "
                    "Only PDFs listed in the configuration file can be processed."
                )
            
            config_metadata = self.metadata_loader.get_metadata(file_name)
            chunking_config = self.metadata_loader.get_chunking_config(file_name)
            page_filter_config = self.metadata_loader.get_page_filtering_config(file_name)
            
            logger.info(f"Processing PDF: {config_metadata.get('alias', file_name)} "
                       f"(Module: {config_metadata.get('module_code', 'Unknown')}, "
                       f"Strategy: {chunking_config.get('chunking_strategy', 'section_aware')})")
            
            # Step 1: Extract text with structure (with page filtering)
            logger.info(f"Extracting text from PDF: {pdf_path}")
            extractor = DFSAExtractor(page_filter_config=page_filter_config)
            sections = extractor.extract_text_with_structure(pdf_path)
            
            # Merge extracted metadata with config metadata
            extracted_metadata = extractor.extract_file_metadata(pdf_path, config_metadata)
            
            if not sections:
                raise ValueError("No content extracted from PDF")
            
            result.total_pages = max(s.page_number for s in sections) if sections else 0
            
            # Step 2: Chunk text using appropriate strategy
            logger.info(f"Chunking {len(sections)} sections using {chunking_config.get('chunking_strategy', 'section_aware')} strategy")
            chunker = ChunkingStrategyFactory.create_chunker(chunking_config)
            chunks = chunker.chunk_sections(sections, extracted_metadata)
            result.total_chunks = len(chunks)
            
            # Step 3: Generate embeddings
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            texts = [chunk.content for chunk in chunks]
            embeddings = await self.embedding_service.embed_batch(texts)
            
            # Add embeddings to chunks
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
            
            # Step 4: Upsert to vector store
            logger.info(f"Upserting {len(chunks)} chunks to vector store")
            await self.vector_store.upsert_chunks(chunks)
            
            # Update result
            processing_time = time.time() - start_time
            result.status = ProcessingStatus.COMPLETED
            result.processing_time_seconds = processing_time
            
            logger.info(f"Ingestion completed for {pdf_path} in {processing_time:.2f}s")
            self.job_status[job_id] = result
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error ingesting {pdf_path}: {error_msg}")
            
            processing_time = time.time() - start_time
            result = ProcessingResult(
                job_id=job_id,
                status=ProcessingStatus.FAILED,
                total_chunks=0,
                total_pages=0,
                processing_time_seconds=processing_time,
                error_message=error_msg
            )
            self.job_status[job_id] = result
            return result
    
    def get_job_status(self, job_id: str) -> ProcessingResult:
        """Get the status of an ingestion job."""
        return self.job_status.get(job_id, ProcessingResult(
            job_id=job_id,
            status=ProcessingStatus.PENDING,
            total_chunks=0,
            total_pages=0,
            processing_time_seconds=0
        ))


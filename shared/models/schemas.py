"""Pydantic schemas for request/response models."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ProcessingStatus(str, Enum):
    """Status of document processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestResponse(BaseModel):
    """Response model for ingestion endpoint."""
    job_id: str = Field(..., description="Unique job identifier")
    status: ProcessingStatus = Field(..., description="Current processing status")
    message: str = Field(..., description="Status message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChunkMetadata(BaseModel):
    """Metadata for a text chunk."""
    module_code: Optional[str] = None  # e.g., "GEN", "GLO", "AML"
    module_name: Optional[str] = None
    chapter_number: Optional[str] = None
    chapter_title: Optional[str] = None
    section_number: Optional[str] = None
    section_title: Optional[str] = None
    subsection_number: Optional[str] = None
    subsection_title: Optional[str] = None
    rule_number: Optional[str] = None  # e.g., "GEN 2.1.1"
    page_number: int
    chunk_index: int
    total_chunks: int
    file_name: str
    file_version: Optional[str] = None
    hierarchy_path: str  # e.g., "GEN > GEN 2 > GEN 2.1 > GEN 2.1.1"
    content_type: Optional[str] = None  # e.g., "rule", "appendix", "glossary", "glossary_definition"
    parent_sections: List[str] = Field(default_factory=list)
    alias: Optional[str] = None  # Human-readable alias for the PDF
    term: Optional[str] = None  # For glossary: the defined term
    definition: Optional[str] = None  # For glossary: the definition text
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)  # Custom metadata fields


class DocumentChunk(BaseModel):
    """A chunk of document with metadata."""
    content: str
    metadata: ChunkMetadata
    embedding: Optional[List[float]] = None


class ProcessingResult(BaseModel):
    """Result of document processing."""
    job_id: str
    status: ProcessingStatus
    total_chunks: int
    total_pages: int
    processing_time_seconds: float
    error_message: Optional[str] = None
    chunks: Optional[List[DocumentChunk]] = None


class ChatRequest(BaseModel):
    """Request model for chat/search endpoint."""
    message: str = Field(..., description="User query message")
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of top results to return")
    use_llm: Optional[bool] = Field(default=None, description="Whether to use LLM for response generation. If None, uses config default.")


class ReferenceResponse(BaseModel):
    """Response model for a single reference/chunk."""
    id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="PDF file name")
    document_name: str = Field(..., description="Human-readable document name/alias")
    page_number: int = Field(..., description="Page number where chunk appears")
    chunk_text: str = Field(..., description="Text content of the chunk")
    score: float = Field(..., description="Similarity score (0-1)")
    module_code: Optional[str] = Field(None, description="Module code (e.g., GEN, MKT)")
    module_name: Optional[str] = Field(None, description="Module name")
    rule_number: Optional[str] = Field(None, description="Rule number (e.g., GEN 2.1.1)")
    hierarchy_path: Optional[str] = Field(None, description="Hierarchy path (e.g., GEN > GEN 2 > GEN 2.1)")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    message: str = Field(..., description="Response message summarizing results")
    references: List[ReferenceResponse] = Field(default_factory=list, description="List of relevant document chunks")


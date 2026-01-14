"""Unit tests for Pydantic models and schemas."""
import pytest
from pydantic import ValidationError
from shared.models.schemas import (
    ChunkMetadata,
    DocumentChunk,
    ChatRequest,
    ChatResponse,
    ReferenceResponse,
    ProcessingStatus,
    ProcessingResult,
    IngestResponse
)
from datetime import datetime


@pytest.mark.unit
class TestChunkMetadata:
    """Test ChunkMetadata model."""
    
    def test_create_minimal_metadata(self):
        """Test creating metadata with minimal required fields."""
        metadata = ChunkMetadata(
            page_number=1,
            chunk_index=0,
            total_chunks=1,
            file_name="test.pdf",
            hierarchy_path="GEN"
        )
        assert metadata.page_number == 1
        assert metadata.file_name == "test.pdf"
        assert metadata.module_code is None
    
    def test_create_full_metadata(self):
        """Test creating metadata with all fields."""
        metadata = ChunkMetadata(
            module_code="GEN",
            module_name="General",
            rule_number="GEN 2.1.1",
            page_number=10,
            chunk_index=0,
            total_chunks=5,
            file_name="test.pdf",
            hierarchy_path="GEN > GEN 2.1.1",
            content_type="rule",
            term="Test Term",
            definition="Test definition",
            custom_metadata={"key": "value"}
        )
        assert metadata.module_code == "GEN"
        assert metadata.rule_number == "GEN 2.1.1"
        assert metadata.custom_metadata["key"] == "value"
    
    def test_custom_metadata_default(self):
        """Test that custom_metadata defaults to empty dict."""
        metadata = ChunkMetadata(
            page_number=1,
            chunk_index=0,
            total_chunks=1,
            file_name="test.pdf",
            hierarchy_path="GEN"
        )
        assert metadata.custom_metadata == {}
        assert isinstance(metadata.custom_metadata, dict)


@pytest.mark.unit
class TestDocumentChunk:
    """Test DocumentChunk model."""
    
    def test_create_chunk(self, sample_chunk_metadata):
        """Test creating a document chunk."""
        chunk = DocumentChunk(
            content="Test content",
            metadata=sample_chunk_metadata
        )
        assert chunk.content == "Test content"
        assert chunk.metadata == sample_chunk_metadata
        assert chunk.embedding is None
    
    def test_create_chunk_with_embedding(self, sample_chunk_metadata):
        """Test creating a chunk with embedding."""
        embedding = [0.1, 0.2, 0.3]
        chunk = DocumentChunk(
            content="Test",
            metadata=sample_chunk_metadata,
            embedding=embedding
        )
        assert chunk.embedding == embedding


@pytest.mark.unit
class TestChatRequest:
    """Test ChatRequest model."""
    
    def test_create_request(self):
        """Test creating a chat request."""
        request = ChatRequest(
            message="Test query",
            user_id="user1",
            session_id="session1"
        )
        assert request.message == "Test query"
        assert request.user_id == "user1"
        assert request.top_k == 5  # Default
    
    def test_top_k_validation(self):
        """Test top_k validation."""
        # Valid range
        request = ChatRequest(
            message="test",
            user_id="u",
            session_id="s",
            top_k=10
        )
        assert request.top_k == 10
        
        # Too low
        with pytest.raises(ValidationError):
            ChatRequest(
                message="test",
                user_id="u",
                session_id="s",
                top_k=0
            )
        
        # Too high
        with pytest.raises(ValidationError):
            ChatRequest(
                message="test",
                user_id="u",
                session_id="s",
                top_k=21
            )
    
    def test_use_llm_optional(self):
        """Test use_llm is optional."""
        request = ChatRequest(
            message="test",
            user_id="u",
            session_id="s"
        )
        assert request.use_llm is None
        
        request = ChatRequest(
            message="test",
            user_id="u",
            session_id="s",
            use_llm=True
        )
        assert request.use_llm is True


@pytest.mark.unit
class TestChatResponse:
    """Test ChatResponse model."""
    
    def test_create_response(self):
        """Test creating a chat response."""
        response = ChatResponse(
            message="Test response"
        )
        assert response.message == "Test response"
        assert response.references == []
    
    def test_response_with_references(self):
        """Test response with references."""
        references = [
            ReferenceResponse(
                id="ref1",
                document_id="doc1.pdf",
                document_name="Doc 1",
                page_number=1,
                chunk_text="Content",
                score=0.9
            )
        ]
        response = ChatResponse(
            message="Found results",
            references=references
        )
        assert len(response.references) == 1
        assert response.references[0].score == 0.9


@pytest.mark.unit
class TestReferenceResponse:
    """Test ReferenceResponse model."""
    
    def test_create_reference(self):
        """Test creating a reference response."""
        ref = ReferenceResponse(
            id="ref1",
            document_id="doc.pdf",
            document_name="Document",
            page_number=10,
            chunk_text="Content here",
            score=0.85
        )
        assert ref.id == "ref1"
        assert ref.score == 0.85
        assert ref.module_code is None  # Optional field


@pytest.mark.unit
class TestProcessingStatus:
    """Test ProcessingStatus enum."""
    
    def test_status_values(self):
        """Test all status values exist."""
        assert ProcessingStatus.PENDING == "pending"
        assert ProcessingStatus.PROCESSING == "processing"
        assert ProcessingStatus.COMPLETED == "completed"
        assert ProcessingStatus.FAILED == "failed"


@pytest.mark.unit
class TestProcessingResult:
    """Test ProcessingResult model."""
    
    def test_create_result(self):
        """Test creating a processing result."""
        result = ProcessingResult(
            job_id="job1",
            status=ProcessingStatus.COMPLETED,
            total_chunks=10,
            total_pages=5,
            processing_time_seconds=2.5
        )
        assert result.job_id == "job1"
        assert result.status == ProcessingStatus.COMPLETED
        assert result.error_message is None


@pytest.mark.unit
class TestIngestResponse:
    """Test IngestResponse model."""
    
    def test_create_response(self):
        """Test creating an ingest response."""
        response = IngestResponse(
            job_id="job1",
            status=ProcessingStatus.PENDING,
            message="Processing started"
        )
        assert response.job_id == "job1"
        assert isinstance(response.timestamp, datetime)

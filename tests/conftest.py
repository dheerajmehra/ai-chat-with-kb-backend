"""Pytest configuration and shared fixtures."""
import pytest
import sys
from pathlib import Path
from typing import Generator, List
from unittest.mock import Mock, AsyncMock, MagicMock
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.config import get_settings
from shared.models.schemas import DocumentChunk, ChunkMetadata, ProcessingStatus


@pytest.fixture(scope="session")
def project_root_path():
    """Return project root path."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_settings():
    """Get test settings."""
    return get_settings()


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def sample_chunk_metadata():
    """Create sample chunk metadata for testing."""
    return ChunkMetadata(
        module_code="GEN",
        module_name="General Module",
        chapter_number="2",
        chapter_title="Chapter 2",
        section_number="2.1",
        section_title="Section 2.1",
        rule_number="GEN 2.1.1",
        page_number=10,
        chunk_index=0,
        total_chunks=5,
        file_name="test.pdf",
        hierarchy_path="GEN > GEN 2 > GEN 2.1 > GEN 2.1.1",
        content_type="rule",
        alias="Test Document"
    )


@pytest.fixture
def sample_document_chunk(sample_chunk_metadata):
    """Create a sample document chunk for testing."""
    return DocumentChunk(
        content="This is a test chunk content for testing purposes. It contains some text that can be used to test vector search and other functionality.",
        metadata=sample_chunk_metadata,
        embedding=[0.1 * (i % 10) for i in range(1536)]  # Mock embedding (1536 dims for OpenAI)
    )


@pytest.fixture
def sample_chunks(sample_chunk_metadata):
    """Create multiple sample chunks for testing."""
    chunks = []
    for i in range(5):
        chunk = DocumentChunk(
            content=f"Test chunk content {i}. This is chunk number {i} with some sample text for testing vector search functionality.",
            metadata=ChunkMetadata(
                module_code="GEN",
                module_name="General Module",
                rule_number=f"GEN 2.1.{i+1}",
                page_number=10 + i,
                chunk_index=i,
                total_chunks=5,
                file_name="test.pdf",
                hierarchy_path=f"GEN > GEN 2.1.{i+1}",
                content_type="rule",
                alias="Test Document"
            ),
            embedding=[float(i) * 0.1 + j * 0.01 for j in range(1536)]  # Mock embedding
        )
        chunks.append(chunk)
    return chunks


@pytest.fixture
def glossary_chunk():
    """Create a sample glossary definition chunk."""
    return DocumentChunk(
        content="Authorised Firm: A firm that is authorised by the DFSA to conduct financial services.",
        metadata=ChunkMetadata(
            module_code="GLO",
            module_name="Glossary Module",
            page_number=1,
            chunk_index=0,
            total_chunks=1,
            file_name="glossary.pdf",
            hierarchy_path="Glossary > Authorised Firm",
            content_type="glossary_definition",
            term="Authorised Firm",
            definition="A firm that is authorised by the DFSA to conduct financial services.",
            alias="Glossary"
        ),
        embedding=[0.2] * 1536
    )


@pytest.fixture
def mock_openai_api_key(monkeypatch):
    """Mock OpenAI API key for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-sk-proj-test123")
    return "test-key-sk-proj-test123"


@pytest.fixture
def disable_llm(monkeypatch):
    """Disable LLM for testing."""
    monkeypatch.setenv("LLM_ENABLED", "false")


@pytest.fixture
def enable_llm(monkeypatch, mock_openai_api_key):
    """Enable LLM for testing with mocked API key."""
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", mock_openai_api_key)


@pytest.fixture
def temp_vector_store_path(tmp_path):
    """Create a temporary vector store path for testing."""
    store_path = tmp_path / "test_vector_store.pkl"
    return store_path


@pytest.fixture
def mock_embedding_response():
    """Mock OpenAI embedding API response."""
    return {
        "data": [{
            "embedding": [0.1 * (i % 10) for i in range(1536)]
        }]
    }


@pytest.fixture
def mock_openai_client(mock_embedding_response):
    """Mock OpenAI client for testing."""
    mock_client = MagicMock()
    mock_embeddings = MagicMock()
    mock_embeddings.create = AsyncMock(return_value=type('obj', (object,), {
        'data': [type('obj', (object,), {'embedding': mock_embedding_response['data'][0]['embedding']})()]
    })())
    mock_client.embeddings = mock_embeddings
    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=type('obj', (object,), {
        'choices': [type('obj', (object,), {
            'message': type('obj', (object,), {'content': 'Test LLM response'})()
        })()]
    })())
    return mock_client


@pytest.fixture
def sample_pdf_section():
    """Create a sample PDFSection for testing chunker."""
    from shared.utils.pdf_extractor import PDFSection
    return PDFSection(
        level=3,
        title="GEN 2.1.1",
        content="This is a test section content that will be chunked. It contains multiple sentences. Each sentence should be handled properly.",
        page_number=10,
        rule_number="GEN 2.1.1",
        parent_path=[(1, "GEN"), (2, "GEN 2"), (3, "GEN 2.1")]
    )


@pytest.fixture
def sample_pdf_sections(sample_pdf_section):
    """Create multiple PDF sections for testing."""
    sections = [sample_pdf_section]
    for i in range(2, 5):
        from shared.utils.pdf_extractor import PDFSection
        section = PDFSection(
            level=3,
            title=f"GEN 2.1.{i}",
            content=f"Section {i} content with multiple sentences. This is sentence two. And sentence three.",
            page_number=10 + i,
            rule_number=f"GEN 2.1.{i}",
            parent_path=[(1, "GEN"), (2, "GEN 2"), (3, "GEN 2.1")]
        )
        sections.append(section)
    return sections


@pytest.fixture
def file_metadata():
    """Sample file metadata for testing."""
    return {
        "file_name": "test.pdf",
        "alias": "Test Document",
        "module_code": "GEN",
        "module_name": "General Module",
        "file_version": "1.0"
    }

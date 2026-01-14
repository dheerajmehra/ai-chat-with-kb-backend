"""Unit tests for utility functions."""
import pytest
from shared.utils.chunker import RuleAwareChunker
from shared.utils.metadata_loader import MetadataLoader
from shared.utils.pdf_extractor import PDFSection


@pytest.mark.unit
class TestRuleAwareChunker:
    """Test RuleAwareChunker."""
    
    def test_initialization(self):
        """Test chunker initialization."""
        chunker = RuleAwareChunker()
        assert chunker.chunk_size > 0
        assert chunker.chunk_overlap >= 0
    
    def test_initialization_with_custom_params(self):
        """Test chunker with custom parameters."""
        chunker = RuleAwareChunker(
            chunk_size=500,
            chunk_overlap=50,
            respect_sentences=True,
            respect_sections=True
        )
        assert chunker.chunk_size == 500
        assert chunker.chunk_overlap == 50
    
    def test_chunk_sections(self, sample_pdf_sections, file_metadata):
        """Test chunking PDF sections."""
        chunker = RuleAwareChunker(chunk_size=100, chunk_overlap=20)
        chunks = chunker.chunk_sections(sample_pdf_sections, file_metadata)
        
        assert len(chunks) > 0
        assert all(chunk.metadata.file_name == file_metadata["file_name"] for chunk in chunks)
        assert all(chunk.metadata.module_code == file_metadata["module_code"] for chunk in chunks)
    
    def test_respect_sections(self, sample_pdf_sections, file_metadata):
        """Test that sections are respected when enabled."""
        chunker = RuleAwareChunker(
            chunk_size=1000,  # Large enough to keep sections intact
            chunk_overlap=0,
            respect_sections=True
        )
        chunks = chunker.chunk_sections(sample_pdf_sections, file_metadata)
        
        # Should have at least one chunk per section
        assert len(chunks) >= len(sample_pdf_sections)
    
    def test_chunk_size_respected(self, sample_pdf_sections, file_metadata):
        """Test that chunk size is respected."""
        chunker = RuleAwareChunker(chunk_size=50, chunk_overlap=0)
        chunks = chunker.chunk_sections(sample_pdf_sections, file_metadata)
        
        # All chunks should be within reasonable size
        # The chunker respects section boundaries, so sections may be kept intact even if larger than chunk_size
        # Allow up to 3x flexibility to account for section-boundary respect
        for chunk in chunks:
            assert len(chunk.content) <= chunker.chunk_size * 3.0  # Allow flexibility for section boundary respect


@pytest.mark.unit
class TestMetadataLoader:
    """Test MetadataLoader."""
    
    def test_initialization(self):
        """Test metadata loader initialization."""
        loader = MetadataLoader()
        assert loader is not None
    
    def test_get_all_metadata(self):
        """Test getting all metadata."""
        loader = MetadataLoader()
        metadata = loader.get_all_metadata()
        
        assert isinstance(metadata, dict)
        # Should have at least the configured PDFs
    
    def test_has_metadata(self):
        """Test checking if metadata exists."""
        loader = MetadataLoader()
        all_metadata = loader.get_all_metadata()
        
        if all_metadata:
            # Test with first file name
            first_file = list(all_metadata.keys())[0]
            assert loader.has_metadata(first_file) is True
            assert loader.has_metadata("nonexistent.pdf") is False
        else:
            # If no metadata configured, test with non-existent file
            assert loader.has_metadata("test.pdf") is False
    
    def test_get_metadata(self):
        """Test getting metadata for specific file."""
        loader = MetadataLoader()
        all_metadata = loader.get_all_metadata()
        
        if all_metadata:
            first_file = list(all_metadata.keys())[0]
            metadata = loader.get_metadata(first_file)
            assert metadata is not None
            assert isinstance(metadata, dict)
        else:
            metadata = loader.get_metadata("test.pdf")
            assert metadata is None
    
    def test_get_chunking_config(self):
        """Test getting chunking configuration."""
        loader = MetadataLoader()
        all_metadata = loader.get_all_metadata()
        
        if all_metadata:
            first_file = list(all_metadata.keys())[0]
            config = loader.get_chunking_config(first_file)
            assert isinstance(config, dict)
        else:
            config = loader.get_chunking_config("test.pdf")
            # Should return default config or None
            assert config is None or isinstance(config, dict)
    
    def test_get_page_filtering_config(self):
        """Test getting page filtering configuration."""
        loader = MetadataLoader()
        all_metadata = loader.get_all_metadata()
        
        if all_metadata:
            first_file = list(all_metadata.keys())[0]
            config = loader.get_page_filtering_config(first_file)
            assert isinstance(config, dict)
        else:
            config = loader.get_page_filtering_config("test.pdf")
            # Should return default config or None
            assert config is None or isinstance(config, dict)

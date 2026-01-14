"""Unit tests for page filter utilities."""
import pytest
from shared.utils.page_filter import PageFilter


@pytest.mark.unit
class TestPageFilter:
    """Test PageFilter class."""
    
    def test_initialization_defaults(self):
        """Test PageFilter initialization with defaults."""
        config = {}
        filter_obj = PageFilter(config)
        
        assert filter_obj.skip_cover_pages is True
        assert filter_obj.skip_toc is True
        assert filter_obj.skip_disclaimers is True
        assert filter_obj.remove_headers_footers is True
        assert filter_obj.cover_page_range == [1, 1]
    
    def test_initialization_custom_config(self):
        """Test PageFilter with custom configuration."""
        config = {
            "skip_cover_pages": False,
            "skip_toc": False,
            "skip_disclaimers": False,
            "remove_headers_footers": False,
            "cover_page_range": [1, 2],
            "toc_page_range": [3, 5]
        }
        filter_obj = PageFilter(config)
        
        assert filter_obj.skip_cover_pages is False
        assert filter_obj.skip_toc is False
        assert filter_obj.skip_disclaimers is False
        assert filter_obj.remove_headers_footers is False
        assert filter_obj.cover_page_range == [1, 2]
        assert filter_obj.toc_page_range == [3, 5]
    
    def test_should_skip_page_cover_page(self):
        """Test skipping cover pages."""
        config = {"skip_cover_pages": True, "cover_page_range": [1, 1]}
        filter_obj = PageFilter(config)
        
        assert filter_obj.should_skip_page(1, "Cover page content") is True
        assert filter_obj.should_skip_page(2, "Regular content") is False
    
    def test_should_skip_page_toc(self):
        """Test skipping table of contents."""
        config = {
            "skip_toc": True,
            "toc_page_range": [2, 3]
        }
        filter_obj = PageFilter(config)
        
        toc_text = "Table of Contents\n1. Introduction ... 5"
        assert filter_obj.should_skip_page(2, toc_text) is True
        assert filter_obj.should_skip_page(4, "Regular content") is False
    
    def test_should_skip_page_disclaimer(self):
        """Test skipping disclaimer pages."""
        config = {"skip_disclaimers": True}
        filter_obj = PageFilter(config)
        
        # Need multiple disclaimer patterns to trigger (score >= 2)
        disclaimer_text = "DISCLAIMER\nLEGAL NOTICE\nThis document is for informational purposes only.\nCopyright 2024. All rights reserved."
        assert filter_obj.should_skip_page(10, disclaimer_text) is True
        assert filter_obj.should_skip_page(10, "Regular content") is False
    
    def test_filter_text(self):
        """Test filter_text method for removing headers and footers."""
        config = {"remove_headers_footers": True}
        filter_obj = PageFilter(config)
        
        text_with_header = "DFSA Rulebook\n\nActual content here\n\nGEN / VER123\n\nMore content"
        cleaned = filter_obj.filter_text(text_with_header)
        # Headers/footers should be removed
        assert "DFSA Rulebook" not in cleaned or cleaned != text_with_header
    
    def test_filter_text_disabled(self):
        """Test that headers/footers are not removed when disabled."""
        config = {"remove_headers_footers": False}
        filter_obj = PageFilter(config)
        
        text = "DFSA Rulebook\n\nActual content"
        cleaned = filter_obj.filter_text(text)
        assert cleaned == text
    
    def test_filter_pages(self):
        """Test filter_pages method."""
        config = {
            "skip_cover_pages": True,
            "cover_page_range": [1, 1],
            "skip_toc": True,
            "toc_page_range": [2, 2],
            "remove_headers_footers": True
        }
        filter_obj = PageFilter(config)
        
        pages = [
            (1, "Cover page content"),
            (2, "Table of Contents\n1. Intro ... 5"),
            (3, "DFSA Rulebook\n\nActual content here\n\nGEN / VER123"),
            (4, "More content here")
        ]
        
        filtered = filter_obj.filter_pages(pages)
        
        # Cover and TOC should be skipped
        assert len(filtered) == 2
        assert filtered[0][0] == 3  # First content page
        assert filtered[1][0] == 4  # Second content page

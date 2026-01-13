"""Page filtering utilities to skip non-content pages."""
from typing import List, Set, Optional
import re
from shared.utils.logger import logger


class PageFilter:
    """Filters out non-content pages like cover pages, TOC, disclaimers, headers/footers."""
    
    def __init__(self, config: dict):
        """
        Initialize page filter with configuration.
        
        Args:
            config: Page filtering configuration dictionary
        """
        self.skip_cover_pages = config.get("skip_cover_pages", True)
        self.skip_toc = config.get("skip_toc", True)
        self.skip_disclaimers = config.get("skip_disclaimers", True)
        self.remove_headers_footers = config.get("remove_headers_footers", True)
        
        # Page ranges to skip
        self.cover_page_range = config.get("cover_page_range", [1, 1])
        self.toc_page_range = config.get("toc_page_range")
        
        # Patterns for detection
        self.toc_patterns = [
            re.compile(r'contents?', re.IGNORECASE),
            re.compile(r'table\s+of\s+contents?', re.IGNORECASE),
            re.compile(r'^\s*\d+\.\s+.*\.{3,}\s+\d+\s*$', re.MULTILINE),  # TOC entry pattern
        ]
        
        self.disclaimer_patterns = [
            re.compile(r'disclaimer', re.IGNORECASE),
            re.compile(r'legal\s+notice', re.IGNORECASE),
            re.compile(r'copyright', re.IGNORECASE),
            re.compile(r'all\s+rights\s+reserved', re.IGNORECASE),
        ]
        
        self.header_footer_patterns = [
            re.compile(r'^DFSA\s+Rulebook', re.IGNORECASE),
            re.compile(r'^[A-Z]{2,4}\s*/\s*VER\d+', re.IGNORECASE),  # Module code/version
            re.compile(r'^\d+\s*$'),  # Page number alone
        ]
    
    def should_skip_page(self, page_num: int, page_text: str) -> bool:
        """
        Determine if a page should be skipped.
        
        Args:
            page_num: Page number (1-indexed)
            page_text: Text content of the page
            
        Returns:
            True if page should be skipped, False otherwise
        """
        # Check cover pages
        if self.skip_cover_pages and self.cover_page_range:
            start, end = self.cover_page_range
            if start <= page_num <= end:
                logger.debug(f"Skipping cover page {page_num}")
                return True
        
        # Check TOC pages
        if self.skip_toc:
            if self.toc_page_range:
                start, end = self.toc_page_range
                if start <= page_num <= end:
                    logger.debug(f"Skipping TOC page {page_num}")
                    return True
            
            # Pattern-based TOC detection
            if self._is_toc_page(page_text):
                logger.debug(f"Skipping TOC page {page_num} (pattern detected)")
                return True
        
        # Check disclaimer pages
        if self.skip_disclaimers and self._is_disclaimer_page(page_text):
            logger.debug(f"Skipping disclaimer page {page_num}")
            return True
        
        return False
    
    def _is_toc_page(self, text: str) -> bool:
        """Check if text appears to be a table of contents."""
        if not text or len(text.strip()) < 50:
            return False
        
        # Check for TOC patterns
        for pattern in self.toc_patterns:
            if pattern.search(text):
                # Additional check: high density of page numbers
                page_refs = re.findall(r'\.{3,}\s*\d+', text)
                if len(page_refs) >= 5:  # At least 5 TOC entries
                    return True
        
        return False
    
    def _is_disclaimer_page(self, text: str) -> bool:
        """Check if text appears to be a disclaimer/legal notice page."""
        if not text:
            return False
        
        text_lower = text.lower()
        disclaimer_score = 0
        
        for pattern in self.disclaimer_patterns:
            if pattern.search(text):
                disclaimer_score += 1
        
        # If multiple disclaimer patterns found, likely a disclaimer page
        return disclaimer_score >= 2
    
    def filter_text(self, text: str) -> str:
        """
        Remove headers and footers from text.
        
        Args:
            text: Text content to filter
            
        Returns:
            Filtered text with headers/footers removed
        """
        if not self.remove_headers_footers or not text:
            return text
        
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip lines matching header/footer patterns
            skip = False
            for pattern in self.header_footer_patterns:
                if pattern.match(line_stripped):
                    skip = True
                    break
            
            # Skip very short lines that are likely page numbers or separators
            if not skip and len(line_stripped) <= 3 and line_stripped.isdigit():
                skip = True
            
            if not skip:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def filter_pages(self, pages: List[tuple]) -> List[tuple]:
        """
        Filter a list of (page_num, page_text) tuples.
        
        Args:
            pages: List of (page_number, page_text) tuples
            
        Returns:
            Filtered list of pages
        """
        filtered = []
        
        for page_num, page_text in pages:
            # Skip non-content pages
            if self.should_skip_page(page_num, page_text):
                continue
            
            # Remove headers/footers
            filtered_text = self.filter_text(page_text)
            
            # Only include if there's meaningful content left
            if filtered_text.strip():
                filtered.append((page_num, filtered_text))
        
        return filtered


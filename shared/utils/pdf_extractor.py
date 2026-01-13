"""PDF text extraction with DFSA rulebook hierarchy awareness."""
from typing import List, Dict, Optional, Tuple
import re
from dataclasses import dataclass
from shared.utils.logger import logger
from shared.models.schemas import ChunkMetadata
from shared.config import get_settings

settings = get_settings()


@dataclass
class PDFSection:
    """Represents a section in the PDF with hierarchy information."""
    level: int  # 0 = module, 1 = chapter, 2 = section, 3 = subsection, etc.
    title: str
    content: str
    page_number: int
    rule_number: Optional[str] = None  # e.g., "GEN 2.1.1"
    parent_path: List[str] = None
    
    def __post_init__(self):
        if self.parent_path is None:
            self.parent_path = []


class DFSAExtractor:
    """Extracts text from DFSA rulebook PDFs with structure awareness."""
    
    # DFSA rulebook patterns
    MODULE_PATTERN = re.compile(r'^([A-Z]{2,4})\s+(\d+)\s+(.+)$', re.MULTILINE)  # e.g., "GEN 1 Introduction"
    RULE_PATTERN = re.compile(r'^([A-Z]{2,4})\s+(\d+(?:\.\d+)+)\s+(.+)$', re.MULTILINE)  # e.g., "GEN 2.1.1 Title"
    # Standalone rule number with content (e.g., "1.1.1 (1) Content" or "1.1.2 Content")
    # Matches rule number followed by content (not just a short heading)
    STANDALONE_RULE_PATTERN = re.compile(r'^(\d+(?:\.\d+)+)\s+[\(A-Z]', re.MULTILINE)  # e.g., "1.1.1 (1)" or "1.1.2 Where"
    CHAPTER_PATTERN = re.compile(r'^(\d+)\s+(.+)$', re.MULTILINE)  # e.g., "1 Introduction"
    SECTION_PATTERN = re.compile(r'^(\d+\.\d+)\s+(.+)$', re.MULTILINE)  # e.g., "2.1 General Requirements"
    SUBSECTION_PATTERN = re.compile(r'^(\d+\.\d+\.\d+)\s+(.+)$', re.MULTILINE)  # e.g., "2.1.1 Scope"
    
    def __init__(self, pdf_library: str = None, page_filter_config: dict = None):
        """
        Initialize PDF extractor.
        
        Args:
            pdf_library: PDF library to use ('pdfplumber' or 'pymupdf'). 
                        If None, uses value from config.
            page_filter_config: Page filtering configuration dictionary
        """
        self.pdf_library = pdf_library or settings.pdf_library.lower()
        self.current_module = None
        self.current_chapter = None
        self.current_section = None
        self.current_subsection = None
        self.hierarchy_stack = []
        
        # Initialize page filter if config provided
        if page_filter_config:
            from shared.utils.page_filter import PageFilter
            self.page_filter = PageFilter(page_filter_config)
        else:
            self.page_filter = None
        
        # Validate and import the specified library
        self._validate_and_import_library()
    
    def _validate_and_import_library(self):
        """Validate that the specified PDF library is available."""
        if self.pdf_library == "pymupdf":
            try:
                import fitz  # PyMuPDF
                self.fitz = fitz
                logger.info("Using PyMuPDF for PDF extraction")
            except ImportError:
                raise ImportError(
                    "PyMuPDF is not installed. Install it with: pip install PyMuPDF\n"
                    "Or change PDF_LIBRARY=pdfplumber in your .env file"
                )
        elif self.pdf_library == "pdfplumber":
            try:
                import pdfplumber
                self.pdfplumber = pdfplumber
                logger.info("Using pdfplumber for PDF extraction")
            except ImportError:
                raise ImportError(
                    "pdfplumber is not installed. Install it with: pip install pdfplumber"
                )
        else:
            raise ValueError(
                f"Invalid PDF_LIBRARY setting: {self.pdf_library}. "
                "Must be 'pdfplumber' or 'pymupdf'"
            )
    
    def extract_text_with_structure(self, pdf_path: str) -> List[PDFSection]:
        """
        Extract text from PDF preserving DFSA rulebook hierarchy.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of PDFSection objects with hierarchy information
        """
        if self.pdf_library == "pymupdf":
            return self._extract_with_pymupdf(pdf_path)
        elif self.pdf_library == "pdfplumber":
            return self._extract_with_pdfplumber(pdf_path)
        else:
            raise ValueError(f"Unknown PDF library: {self.pdf_library}")
    
    def _extract_with_pymupdf(self, pdf_path: str) -> List[PDFSection]:
        """Extract using PyMuPDF."""
        try:
            doc = self.fitz.open(pdf_path)
            sections = []
            
            # Collect all pages with text and blocks for filtering
            pages_data = []
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text("text")
                if text:
                    blocks = page.get_text("dict")["blocks"]
                    pages_data.append((page_num, text, blocks))
            
            doc.close()
            
            # Apply page filtering if configured
            if self.page_filter:
                # Filter pages (text only for filtering logic)
                filtered_pages = []
                for page_num, text, blocks in pages_data:
                    if not self.page_filter.should_skip_page(page_num, text):
                        filtered_text = self.page_filter.filter_text(text)
                        if filtered_text.strip():
                            filtered_pages.append((page_num, filtered_text, blocks))
                pages_data = filtered_pages
            
            # Process filtered pages
            for page_num, text, blocks in pages_data:
                # Process blocks to maintain structure
                page_sections = self._process_page_blocks(blocks, page_num, text)
                sections.extend(page_sections)
            
            logger.info(f"Extracted {len(sections)} sections from {pdf_path} using PyMuPDF")
            return sections
            
        except Exception as e:
            logger.error(f"Error extracting PDF with PyMuPDF {pdf_path}: {str(e)}")
            raise
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> List[PDFSection]:
        """Extract using pdfplumber."""
        try:
            # Check if this is a glossary file (GLO module) - use table extraction
            if self._is_glossary_file(pdf_path):
                return self._extract_glossary_tables(pdf_path)
            
            sections = []
            
            # Collect all pages first for filtering
            pages_data = []
            with self.pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    if text:
                        pages_data.append((page_num, text))
            
            # Apply page filtering if configured
            if self.page_filter:
                pages_data = self.page_filter.filter_pages(pages_data)
            
            # Process filtered pages
            for page_num, text in pages_data:
                # Split text into lines for processing
                lines = text.split('\n')
                page_sections = self._process_text_lines(lines, page_num)
                sections.extend(page_sections)
            
            logger.info(f"Extracted {len(sections)} sections from {pdf_path} using pdfplumber")
            return sections
            
        except Exception as e:
            logger.error(f"Error extracting PDF with pdfplumber {pdf_path}: {str(e)}")
            raise
    
    def _is_glossary_file(self, pdf_path: str) -> bool:
        """Check if PDF is a glossary file (GLO module)."""
        import os
        from pathlib import Path
        file_name = Path(pdf_path).name.upper()
        # Check filename for GLO or GLOSSARY
        if "GLO" in file_name or "GLOSSARY" in file_name:
            return True
        
        # Also check if we have metadata indicating it's a glossary
        try:
            from shared.utils.metadata_loader import MetadataLoader
            loader = MetadataLoader()
            if loader.has_metadata(Path(pdf_path).name):
                metadata = loader.get_metadata(Path(pdf_path).name)
                if metadata.get("module_code") == "GLO":
                    return True
        except:
            pass
        
        return False
    
    def _extract_glossary_tables(self, pdf_path: str) -> List[PDFSection]:
        """
        Extract glossary terms and definitions from table structure.
        
        Assumes PDF has tables with two columns: "Defined Term" and "Definition".
        """
        sections = []
        
        try:
            with self.pdfplumber.open(pdf_path) as pdf:
                # Collect all pages first for filtering
                pages_to_process = []
                for page_num, page in enumerate(pdf.pages, start=1):
                    pages_to_process.append((page_num, page))
                
                # Apply page filtering if configured
                if self.page_filter:
                    filtered_pages = []
                    for page_num, page in pages_to_process:
                        text = page.extract_text() or ""
                        if not self.page_filter.should_skip_page(page_num, text):
                            filtered_pages.append((page_num, page))
                    pages_to_process = filtered_pages
                
                # Extract tables from each page
                for page_num, page in pages_to_process:
                    tables = page.extract_tables()
                    
                    for table in tables:
                        if not table or len(table) < 2:
                            continue
                        
                        # Check if this looks like a glossary table (has header row)
                        header_row = table[0]
                        if len(header_row) < 2:
                            continue
                        
                        # Look for "Defined Term" and "Definition" headers
                        header_text = " ".join([str(cell) if cell else "" for cell in header_row]).upper()
                        if "DEFINED TERM" not in header_text or "DEFINITION" not in header_text:
                            # Might be continuation table without header
                            # Check if rows have 2 columns with term-like content
                            if len(table) > 0 and len(table[0]) == 2:
                                # Process as data rows
                                for row_idx, row in enumerate(table):
                                    if len(row) >= 2 and row[0] and row[1]:
                                        term = str(row[0]).strip()
                                        definition = str(row[1]).strip()
                                        # Clean up whitespace
                                        term = " ".join(term.split())
                                        definition = " ".join(definition.split())
                                        if term and definition:
                                            # Skip header-like rows
                                            if term.upper() in ["DEFINED TERM", "DEFINITION", "BACK TO TOP"]:
                                                continue
                                            section = PDFSection(
                                                level=3,
                                                title=term,
                                                content=definition,
                                                page_number=page_num,
                                                rule_number=None,
                                                parent_path=[(1, "Glossary")]
                                            )
                                            sections.append(section)
                            continue
                        
                        # Process table rows (skip header)
                        for row_idx, row in enumerate(table[1:], start=1):
                            if len(row) < 2:
                                continue
                            
                            term = str(row[0]).strip() if row[0] else ""
                            definition = str(row[1]).strip() if row[1] else ""
                            
                            # Clean up term and definition (remove extra whitespace and newlines)
                            term = " ".join(term.split())
                            definition = " ".join(definition.split())
                            
                            # Skip empty rows
                            if not term or not definition:
                                continue
                            
                            # Skip header-like rows
                            if term.upper() in ["DEFINED TERM", "DEFINITION", "BACK TO TOP"]:
                                continue
                            
                            # Create section for this term-definition pair
                            section = PDFSection(
                                level=3,
                                title=term,
                                content=definition,
                                page_number=page_num,
                                rule_number=None,
                                parent_path=[(1, "Glossary")]
                            )
                            sections.append(section)
            
            logger.info(f"Extracted {len(sections)} glossary term-definition pairs from {pdf_path} using table extraction")
            return sections
            
        except Exception as e:
            logger.error(f"Error extracting glossary tables from {pdf_path}: {str(e)}")
            raise
    
    def _process_text_lines(self, lines: List[str], page_num: int) -> List[PDFSection]:
        """Process text lines to identify structure (for pdfplumber)."""
        sections = []
        current_content = []
        current_title = None
        current_level = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect hierarchy level
            level, title, rule_num = self._detect_hierarchy_level(line)
            
            if level is not None:
                # Save previous section if exists
                if current_content and current_title:
                    sections.append(PDFSection(
                        level=current_level,
                        title=current_title,
                        content="\n".join(current_content).strip(),
                        page_number=page_num,
                        rule_number=self._extract_rule_number(current_title),
                        parent_path=self.hierarchy_stack.copy()
                    ))
                
                # Start new section
                current_title = title
                current_level = level
                current_content = []
                
                # For rule numbers (level 3 with rule_num), include the full line in content
                # This ensures content starts with the rule number and full text
                if rule_num is not None:
                    current_content.append(line)
                # Also check for standalone rule pattern match
                elif level == 3 and self.STANDALONE_RULE_PATTERN.match(line):
                    current_content.append(line)
                # Check for RULE_PATTERN match (with module code)
                elif level == 3 and self.RULE_PATTERN.match(line):
                    current_content.append(line)
                
                # Update hierarchy stack
                self._update_hierarchy_stack(level, title)
            else:
                # Regular content line
                current_content.append(line)
        
        # Add final section
        if current_content and current_title:
            sections.append(PDFSection(
                level=current_level,
                title=current_title,
                content="\n".join(current_content).strip(),
                page_number=page_num,
                rule_number=self._extract_rule_number(current_title),
                parent_path=self.hierarchy_stack.copy()
            ))
        
        return sections
    
    def _process_page_blocks(self, blocks: List[Dict], page_num: int, full_text: str) -> List[PDFSection]:
        """Process page blocks to identify structure."""
        sections = []
        current_content = []
        current_title = None
        current_level = 0
        
        for block in blocks:
            if "lines" not in block:
                continue
                
            for line in block.get("lines", []):
                line_text = " ".join([span.get("text", "") for span in line.get("spans", [])])
                line_text = line_text.strip()
                
                if not line_text:
                    continue
                
                # Detect hierarchy level
                level, title, rule_num = self._detect_hierarchy_level(line_text)
                
                if level is not None:
                    # Save previous section if exists
                    if current_content and current_title:
                        sections.append(PDFSection(
                            level=current_level,
                            title=current_title,
                            content="\n".join(current_content).strip(),
                            page_number=page_num,
                            rule_number=self._extract_rule_number(current_title),
                            parent_path=self.hierarchy_stack.copy()
                        ))
                    
                    # Start new section
                    current_title = title
                    current_level = level
                    current_content = []
                    
                    # For rule numbers (level 3 with rule_num), include the full line in content
                    # This ensures content starts with the rule number and full text
                    if rule_num is not None:
                        current_content.append(line_text)
                    # Also check for standalone rule pattern match
                    elif level == 3 and self.STANDALONE_RULE_PATTERN.match(line_text):
                        current_content.append(line_text)
                    # Check for RULE_PATTERN match (with module code)
                    elif level == 3 and self.RULE_PATTERN.match(line_text):
                        current_content.append(line_text)
                    
                    # Update hierarchy stack
                    self._update_hierarchy_stack(level, title)
                else:
                    # Regular content line
                    current_content.append(line_text)
        
        # Add final section
        if current_content and current_title:
            sections.append(PDFSection(
                level=current_level,
                title=current_title,
                content="\n".join(current_content).strip(),
                page_number=page_num,
                rule_number=self._extract_rule_number(current_title),
                parent_path=self.hierarchy_stack.copy()
            ))
        
        return sections
    
    def _detect_hierarchy_level(self, text: str) -> Tuple[Optional[int], Optional[str], Optional[str]]:
        """
        Detect if text is a heading and return its hierarchy level.
        
        Returns:
            Tuple of (level, title, rule_number)
            - level: Hierarchy level (0=module, 1=chapter, 2=section, 3=subsection/rule)
            - title: Just the heading/number part (not full content)
            - rule_number: Full rule number if applicable (e.g., "MKT 1.1.1")
        """
        # Module level (e.g., "GEN 1 Introduction")
        match = self.MODULE_PATTERN.match(text)
        if match:
            self.current_module = match.group(1)
            return 0, text, match.group(1)
        
        # Rule number pattern with module code (e.g., "GEN 2.1.1 Title")
        match = self.RULE_PATTERN.match(text)
        if match:
            rule_num = f"{match.group(1)} {match.group(2)}"
            # Return just the rule number as title (e.g., "2.1.1"), not the full line
            title = match.group(2)  # Just the number part
            return 3, title, rule_num
        
        # Standalone rule number pattern (e.g., "1.1.1 (1) Content" or "1.1.2 Content")
        # This handles cases where rule number appears without module code
        # Check this BEFORE subsection pattern to catch rule numbers with content
        match = self.STANDALONE_RULE_PATTERN.match(text)
        if match:
            rule_num_part = match.group(1)  # e.g., "1.1.1"
            # Try to get module code from current context
            module_code = self.current_module or ""
            if module_code:
                rule_num = f"{module_code} {rule_num_part}"
            else:
                rule_num = rule_num_part
            # Return just the rule number as title
            return 3, rule_num_part, rule_num
        
        # Chapter (e.g., "1 Introduction")
        match = self.CHAPTER_PATTERN.match(text)
        if match and len(text) < 100:  # Likely a heading
            self.current_chapter = text
            return 1, text, None
        
        # Section (e.g., "2.1 General Requirements")
        match = self.SECTION_PATTERN.match(text)
        if match and len(text) < 100:
            self.current_section = text
            return 2, text, None
        
        # Subsection (e.g., "2.1.1 Scope")
        # Only match if it's a short heading (not a rule with content)
        # If text is long, it's likely a rule with content, not a heading
        match = self.SUBSECTION_PATTERN.match(text)
        if match and len(text) < 100:
            self.current_subsection = text
            return 3, text, None
        
        return None, None, None
    
    def _extract_rule_number(self, text: str) -> Optional[str]:
        """Extract rule number from text."""
        # Try full rule pattern with module code
        match = self.RULE_PATTERN.match(text)
        if match:
            return f"{match.group(1)} {match.group(2)}"
        
        # Try standalone rule pattern
        match = self.STANDALONE_RULE_PATTERN.match(text)
        if match:
            rule_num_part = match.group(1)
            module_code = self.current_module or ""
            if module_code:
                return f"{module_code} {rule_num_part}"
            return rule_num_part
        
        # Try to extract just the number pattern (e.g., "1.1.1")
        number_match = re.match(r'^(\d+(?:\.\d+)+)', text)
        if number_match:
            rule_num_part = number_match.group(1)
            module_code = self.current_module or ""
            if module_code:
                return f"{module_code} {rule_num_part}"
            return rule_num_part
        
        return None
    
    def _update_hierarchy_stack(self, level: int, title: str):
        """Update the hierarchy stack based on level."""
        # Remove deeper levels
        self.hierarchy_stack = [h for h in self.hierarchy_stack if h[0] < level]
        # Add current level
        self.hierarchy_stack.append((level, title))
    
    def extract_file_metadata(self, pdf_path: str, config_metadata: dict = None) -> Dict[str, str]:
        """
        Extract metadata from PDF file name and properties.
        
        Args:
            pdf_path: Path to PDF file
            config_metadata: Optional metadata from configuration file
            
        Returns:
            Merged metadata dictionary
        """
        import os
        from pathlib import Path
        
        file_name = Path(pdf_path).name
        metadata = {
            "file_name": file_name,
            "file_path": pdf_path
        }
        
        # Try to extract version from filename (e.g., VER260126)
        version_match = re.search(r'VER(\d+)', file_name)
        if version_match:
            metadata["file_version"] = version_match.group(1)
        
        # Try to extract module code from filename or content
        module_match = re.search(r'([A-Z]{2,4})', file_name)
        if module_match:
            metadata["module_code"] = module_match.group(1)
        
        # Try to extract metadata from PDF
        try:
            if self.pdf_library == "pymupdf":
                doc = self.fitz.open(pdf_path)
                if doc.metadata:
                    if doc.metadata.get("title"):
                        metadata["document_title"] = doc.metadata["title"]
                    if doc.metadata.get("author"):
                        metadata["author"] = doc.metadata["author"]
                doc.close()
            elif self.pdf_library == "pdfplumber":
                with self.pdfplumber.open(pdf_path) as pdf:
                    if pdf.metadata:
                        if pdf.metadata.get("Title"):
                            metadata["document_title"] = pdf.metadata["Title"]
                        if pdf.metadata.get("Author"):
                            metadata["author"] = pdf.metadata["Author"]
        except:
            pass
        
        # Merge with config metadata (config takes precedence)
        if config_metadata:
            metadata.update(config_metadata)
        
        return metadata


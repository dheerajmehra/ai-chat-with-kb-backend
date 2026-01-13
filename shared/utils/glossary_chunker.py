"""Glossary-specific chunking strategy that keeps definitions intact."""
from typing import List, Optional
import re
from shared.models.schemas import ChunkMetadata, DocumentChunk
from shared.utils.pdf_extractor import PDFSection
from shared.utils.logger import logger


class GlossaryChunker:
    """Chunks glossary content keeping each definition intact."""
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 0,
        definition_pattern: Optional[str] = None,
        term_extraction_pattern: Optional[str] = None,
        max_definition_length: int = 2000
    ):
        """
        Initialize glossary chunker.
        
        Args:
            chunk_size: Maximum chunk size (for definitions that exceed this)
            chunk_overlap: Overlap between chunks (typically 0 for glossary)
            definition_pattern: Regex pattern to identify definition start
            term_extraction_pattern: Regex pattern to extract term
            max_definition_length: Maximum length for a single definition
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_definition_length = max_definition_length
        
        # Default patterns for DFSA glossary format
        # Format: "Term Has the meaning given in..." or "Term Means..." or "Term Includes..."
        self.definition_pattern = re.compile(
            definition_pattern or r'^([A-Z][A-Za-z\s]+(?:[A-Z][A-Za-z\s]+)*)\s+(Has the meaning|Means|Includes)',
            re.MULTILINE
        )
        
        self.term_pattern = re.compile(
            term_extraction_pattern or r'^([A-Z][A-Za-z\s]+(?:[A-Z][A-Za-z\s]+)*)',
            re.MULTILINE
        )
        
        # Pattern to detect definition continuation
        self.continuation_pattern = re.compile(r'^[a-z]', re.MULTILINE)
    
    def chunk_sections(
        self,
        sections: List[PDFSection],
        file_metadata: dict
    ) -> List[DocumentChunk]:
        """
        Chunk glossary sections into definition-based chunks.
        
        Args:
            sections: List of PDFSection objects
            file_metadata: File-level metadata
            
        Returns:
            List of DocumentChunk objects, one per definition
        """
        chunks = []
        chunk_index = 0
        
        for section in sections:
            # If section title is the term and content is the definition (from table extraction)
            # This means the PDF extractor already parsed the table correctly
            if section.title and section.content and section.title != section.content:
                # Direct term-definition pair from table extraction
                chunk = self._create_definition_chunk(
                    term=section.title,
                    definition=section.content,
                    section=section,
                    file_metadata=file_metadata,
                    chunk_index=chunk_index,
                    total_chunks=0  # Will update later
                )
                chunks.append(chunk)
                chunk_index += 1
            else:
                # Fallback: Extract definitions from section content (for non-table formats)
                definitions = self._extract_definitions(section.content)
                
                for term, definition in definitions:
                    # Create chunk for each definition
                    chunk = self._create_definition_chunk(
                        term=term,
                        definition=definition,
                        section=section,
                        file_metadata=file_metadata,
                        chunk_index=chunk_index,
                        total_chunks=0  # Will update later
                    )
                    chunks.append(chunk)
                    chunk_index += 1
        
        # Update total_chunks in metadata
        total = len(chunks)
        for chunk in chunks:
            chunk.metadata.total_chunks = total
        
        logger.info(f"Created {total} glossary chunks from {len(sections)} sections")
        return chunks
    
    def _extract_definitions(self, content: str) -> List[tuple]:
        """
        Extract term-definition pairs from content.
        
        Args:
            content: Text content to extract definitions from
            
        Returns:
            List of (term, definition) tuples
        """
        definitions = []
        lines = content.split('\n')
        
        current_term = None
        current_definition = []
        
        for line in lines:
            line = line.strip()
            if not line:
                # Empty line - save current definition if exists
                if current_term and current_definition:
                    definition_text = ' '.join(current_definition)
                    if len(definition_text) <= self.max_definition_length:
                        definitions.append((current_term, definition_text))
                    current_term = None
                    current_definition = []
                continue
            
            # Check if line starts a new definition
            match = self.definition_pattern.match(line)
            if match:
                # Save previous definition
                if current_term and current_definition:
                    definition_text = ' '.join(current_definition)
                    if len(definition_text) <= self.max_definition_length:
                        definitions.append((current_term, definition_text))
                
                # Start new definition
                current_term = match.group(1).strip()
                current_definition = [line]
            elif current_term:
                # Continuation of current definition
                # Check if it's still part of the definition (starts with lowercase or is continuation)
                if self.continuation_pattern.match(line) or not line[0].isupper():
                    current_definition.append(line)
                else:
                    # Might be a new term without explicit pattern
                    # Save current and check if this is a new term
                    if current_definition:
                        definition_text = ' '.join(current_definition)
                        if len(definition_text) <= self.max_definition_length:
                            definitions.append((current_term, definition_text))
                    
                    # Try to extract term from this line
                    term_match = self.term_pattern.match(line)
                    if term_match:
                        current_term = term_match.group(1).strip()
                        current_definition = [line]
                    else:
                        current_term = None
                        current_definition = []
            else:
                # Try to find a term at the start
                term_match = self.term_pattern.match(line)
                if term_match:
                    current_term = term_match.group(1).strip()
                    current_definition = [line]
        
        # Save final definition
        if current_term and current_definition:
            definition_text = ' '.join(current_definition)
            if len(definition_text) <= self.max_definition_length:
                definitions.append((current_term, definition_text))
        
        return definitions
    
    def _create_definition_chunk(
        self,
        term: str,
        definition: str,
        section: PDFSection,
        file_metadata: dict,
        chunk_index: int,
        total_chunks: int
    ) -> DocumentChunk:
        """Create a DocumentChunk for a glossary definition."""
        # Build content with term and definition
        content = f"{term}: {definition}"
        
        # Build hierarchy path
        hierarchy_parts = [h[1] for h in section.parent_path] + [section.title]
        hierarchy_path = " > ".join(hierarchy_parts)
        
        # Extract module info
        module_code = file_metadata.get("module_code", "GLO")
        
        metadata = ChunkMetadata(
            module_code=module_code,
            module_name=file_metadata.get("module_name", "Glossary Module"),
            chapter_number=None,
            chapter_title=None,
            section_number=None,
            section_title=section.title,
            subsection_number=None,
            subsection_title=None,
            rule_number=None,
            page_number=section.page_number,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            file_name=file_metadata.get("file_name", "unknown"),
            file_version=file_metadata.get("file_version"),
            hierarchy_path=hierarchy_path,
            content_type="glossary_definition",
            parent_sections=[h[1] for h in section.parent_path],
            alias=file_metadata.get("alias"),
            term=term,
            definition=definition,
            custom_metadata=file_metadata.get("custom_metadata", {})
        )
        
        return DocumentChunk(
            content=content,
            metadata=metadata
        )


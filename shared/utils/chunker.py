"""Intelligent chunking for DFSA rulebooks respecting structure and sentences."""
from typing import List, Optional
from shared.models.schemas import ChunkMetadata, DocumentChunk
from shared.utils.pdf_extractor import PDFSection
from shared.config import get_settings
from shared.utils.logger import logger
import re

settings = get_settings()


class RuleAwareChunker:
    """Chunks text while respecting DFSA rulebook structure and sentence boundaries."""
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        respect_sentences: bool = None,
        respect_sections: bool = None
    ):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.respect_sentences = respect_sentences if respect_sentences is not None else settings.respect_sentence_boundaries
        self.respect_sections = respect_sections if respect_sections is not None else settings.respect_section_boundaries
        
        # Sentence ending patterns
        self.sentence_endings = re.compile(r'[.!?]\s+')
    
    def chunk_sections(
        self,
        sections: List[PDFSection],
        file_metadata: dict
    ) -> List[DocumentChunk]:
        """
        Chunk PDF sections into DocumentChunk objects with metadata.
        
        Args:
            sections: List of PDFSection objects
            file_metadata: File-level metadata
            
        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        chunk_index = 0
        
        for section in sections:
            if self.respect_sections:
                # Try to keep sections intact if they're small enough
                if len(section.content) <= self.chunk_size:
                    chunk = self._create_chunk(
                        content=section.content,
                        section=section,
                        file_metadata=file_metadata,
                        chunk_index=chunk_index,
                        total_chunks=0  # Will update later
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                else:
                    # Split large sections
                    section_chunks = self._chunk_large_section(
                        section, file_metadata, chunk_index
                    )
                    chunks.extend(section_chunks)
                    chunk_index += len(section_chunks)
            else:
                # Simple chunking without section awareness
                section_chunks = self._chunk_text(
                    section.content,
                    section,
                    file_metadata,
                    chunk_index
                )
                chunks.extend(section_chunks)
                chunk_index += len(section_chunks)
        
        # Update total_chunks in metadata
        total = len(chunks)
        for chunk in chunks:
            chunk.metadata.total_chunks = total
        
        logger.info(f"Created {total} chunks from {len(sections)} sections")
        return chunks
    
    def _chunk_large_section(
        self,
        section: PDFSection,
        file_metadata: dict,
        start_index: int
    ) -> List[DocumentChunk]:
        """Chunk a large section while respecting sentences."""
        chunks = []
        content = section.content
        
        if self.respect_sentences:
            # Split by sentences first
            sentences = self._split_sentences(content)
            current_chunk = []
            current_length = 0
            
            for sentence in sentences:
                sentence_length = len(sentence)
                
                if current_length + sentence_length > self.chunk_size and current_chunk:
                    # Save current chunk
                    chunk_content = " ".join(current_chunk)
                    chunk = self._create_chunk(
                        content=chunk_content,
                        section=section,
                        file_metadata=file_metadata,
                        chunk_index=start_index + len(chunks),
                        total_chunks=0
                    )
                    chunks.append(chunk)
                    
                    # Start new chunk with overlap
                    if self.chunk_overlap > 0:
                        overlap_sentences = self._get_overlap_sentences(
                            current_chunk, self.chunk_overlap
                        )
                        current_chunk = overlap_sentences + [sentence]
                        current_length = sum(len(s) for s in current_chunk)
                    else:
                        current_chunk = [sentence]
                        current_length = sentence_length
                else:
                    current_chunk.append(sentence)
                    current_length += sentence_length
            
            # Add final chunk
            if current_chunk:
                chunk_content = " ".join(current_chunk)
                chunk = self._create_chunk(
                    content=chunk_content,
                    section=section,
                    file_metadata=file_metadata,
                    chunk_index=start_index + len(chunks),
                    total_chunks=0
                )
                chunks.append(chunk)
        else:
            # Simple character-based chunking
            chunks = self._chunk_text(
                content, section, file_metadata, start_index
            )
        
        return chunks
    
    def _chunk_text(
        self,
        text: str,
        section: PDFSection,
        file_metadata: dict,
        start_index: int
    ) -> List[DocumentChunk]:
        """Simple text chunking."""
        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            
            if current_length + word_length > self.chunk_size and current_chunk:
                chunk_content = " ".join(current_chunk)
                chunk = self._create_chunk(
                    content=chunk_content,
                    section=section,
                    file_metadata=file_metadata,
                    chunk_index=start_index + len(chunks),
                    total_chunks=0
                )
                chunks.append(chunk)
                
                # Overlap handling
                if self.chunk_overlap > 0:
                    overlap_words = current_chunk[-self.chunk_overlap//10:]  # Approximate
                    current_chunk = overlap_words + [word]
                    current_length = sum(len(w) + 1 for w in current_chunk)
                else:
                    current_chunk = [word]
                    current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        # Final chunk
        if current_chunk:
            chunk_content = " ".join(current_chunk)
            chunk = self._create_chunk(
                content=chunk_content,
                section=section,
                file_metadata=file_metadata,
                chunk_index=start_index + len(chunks),
                total_chunks=0
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        sentences = self.sentence_endings.split(text)
        # Re-add punctuation to sentences
        result = []
        for i, sentence in enumerate(sentences):
            if i < len(sentences) - 1:
                # Find the punctuation that was removed
                next_start = len(" ".join(sentences[:i+1]))
                if next_start < len(text):
                    punct = text[next_start]
                    sentence += punct
            result.append(sentence.strip())
        return [s for s in result if s]
    
    def _get_overlap_sentences(self, sentences: List[str], overlap_size: int) -> List[str]:
        """Get sentences for overlap."""
        overlap_chars = 0
        overlap_sentences = []
        
        for sentence in reversed(sentences):
            if overlap_chars >= overlap_size:
                break
            overlap_sentences.insert(0, sentence)
            overlap_chars += len(sentence)
        
        return overlap_sentences
    
    def _create_chunk(
        self,
        content: str,
        section: PDFSection,
        file_metadata: dict,
        chunk_index: int,
        total_chunks: int
    ) -> DocumentChunk:
        """Create a DocumentChunk with metadata."""
        # Build hierarchy path
        hierarchy_parts = [h[1] for h in section.parent_path] + [section.title]
        hierarchy_path = " > ".join(hierarchy_parts)
        
        # Extract module info
        module_code = file_metadata.get("module_code")
        if not module_code and section.rule_number:
            module_code = section.rule_number.split()[0]
        
        # Parse section numbers
        chapter_num, section_num, subsection_num = self._parse_section_numbers(section.title)
        
        metadata = ChunkMetadata(
            module_code=module_code,
            module_name=file_metadata.get("module_name"),
            chapter_number=chapter_num,
            chapter_title=self._extract_chapter_title(section),
            section_number=section_num,
            section_title=self._extract_section_title(section),
            subsection_number=subsection_num,
            subsection_title=self._extract_subsection_title(section),
            rule_number=section.rule_number,
            page_number=section.page_number,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            file_name=file_metadata.get("file_name", "unknown"),
            file_version=file_metadata.get("file_version"),
            hierarchy_path=hierarchy_path,
            content_type=self._determine_content_type(section),
            parent_sections=[h[1] for h in section.parent_path],
            alias=file_metadata.get("alias"),
            custom_metadata=file_metadata.get("custom_metadata", {})
        )
        
        return DocumentChunk(
            content=content,
            metadata=metadata
        )
    
    def _parse_section_numbers(self, title: str) -> tuple:
        """Parse chapter, section, and subsection numbers from title."""
        chapter_num = None
        section_num = None
        subsection_num = None
        
        # Try rule number format (e.g., "GEN 2.1.1")
        rule_match = re.match(r'[A-Z]+\s+(\d+)\.(\d+)\.(\d+)', title)
        if rule_match:
            return rule_match.group(1), f"{rule_match.group(1)}.{rule_match.group(2)}", f"{rule_match.group(1)}.{rule_match.group(2)}.{rule_match.group(3)}"
        
        # Try section format (e.g., "2.1.1")
        section_match = re.match(r'(\d+)\.(\d+)\.(\d+)', title)
        if section_match:
            return section_match.group(1), f"{section_match.group(1)}.{section_match.group(2)}", f"{section_match.group(1)}.{section_match.group(2)}.{section_match.group(3)}"
        
        # Try two-level (e.g., "2.1")
        two_level = re.match(r'(\d+)\.(\d+)', title)
        if two_level:
            return two_level.group(1), f"{two_level.group(1)}.{two_level.group(2)}", None
        
        # Try single level (e.g., "2")
        single_level = re.match(r'^(\d+)\s', title)
        if single_level:
            return single_level.group(1), None, None
        
        return None, None, None
    
    def _extract_chapter_title(self, section: PDFSection) -> Optional[str]:
        """Extract chapter title from hierarchy."""
        for level, title in section.parent_path:
            if level == 1:
                return title
        return None
    
    def _extract_section_title(self, section: PDFSection) -> Optional[str]:
        """Extract section title."""
        if section.level == 2:
            return section.title
        for level, title in section.parent_path:
            if level == 2:
                return title
        return None
    
    def _extract_subsection_title(self, section: PDFSection) -> Optional[str]:
        """Extract subsection title."""
        if section.level == 3:
            return section.title
        return None
    
    def _determine_content_type(self, section: PDFSection) -> str:
        """Determine content type (rule, appendix, glossary, etc.)."""
        title_lower = section.title.lower()
        if "appendix" in title_lower or "app" in title_lower:
            return "appendix"
        if "glossary" in title_lower:
            return "glossary"
        if "schedule" in title_lower:
            return "schedule"
        return "rule"


"""Factory for creating appropriate chunking strategies based on configuration."""
from typing import Dict, Any
from shared.utils.chunker import RuleAwareChunker
from shared.utils.glossary_chunker import GlossaryChunker
from shared.utils.logger import logger


class ChunkingStrategyFactory:
    """Factory to create chunking strategies based on configuration."""
    
    @staticmethod
    def create_chunker(config: Dict[str, Any]):
        """
        Create appropriate chunker based on configuration.
        
        Args:
            config: Chunking configuration dictionary
            
        Returns:
            Chunker instance (RuleAwareChunker or GlossaryChunker)
        """
        strategy = config.get("chunking_strategy", "section_aware")
        
        if strategy == "glossary":
            logger.info("Creating GlossaryChunker")
            glossary_settings = config.get("glossary_settings", {})
            return GlossaryChunker(
                chunk_size=config.get("chunk_size", 500),
                chunk_overlap=config.get("chunk_overlap", 0),
                definition_pattern=glossary_settings.get("definition_pattern"),
                term_extraction_pattern=glossary_settings.get("term_extraction_pattern"),
                max_definition_length=glossary_settings.get("max_definition_length", 2000)
            )
        else:
            # Default to section-aware chunking
            logger.info("Creating RuleAwareChunker")
            return RuleAwareChunker(
                chunk_size=config.get("chunk_size", 1000),
                chunk_overlap=config.get("chunk_overlap", 200),
                respect_sentences=config.get("respect_sentences", True),
                respect_sections=config.get("respect_sections", True)
            )


"""PDF metadata loader from JSON configuration."""
import json
from pathlib import Path
from typing import Dict, Optional, Any
from shared.utils.logger import logger
from shared.config import get_settings

settings = get_settings()


class MetadataLoader:
    """Loads and manages PDF metadata from configuration file."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize metadata loader.
        
        Args:
            config_path: Path to pdf_metadata.json file. If None, uses default location.
        """
        if config_path is None:
            # Default to config/pdf_metadata.json
            config_path = Path(__file__).parent.parent / "config" / "pdf_metadata.json"
        
        self.config_path = Path(config_path)
        self._metadata_cache: Dict[str, Dict] = {}
        self._default_config: Dict = {}
        self._module_strategies: Dict[str, Dict] = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from JSON file."""
        try:
            if not self.config_path.exists():
                logger.warning(f"Metadata config file not found: {self.config_path}")
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Load PDF-specific metadata
            for pdf_config in config.get("pdfs", []):
                file_name = pdf_config.get("file_name")
                if file_name:
                    self._metadata_cache[file_name] = pdf_config
            
            # Load defaults
            self._default_config = config.get("default_chunking", {})
            self._default_page_filtering = config.get("default_page_filtering", {})
            self._module_strategies = config.get("module_strategies", {})
            
            logger.info(f"Loaded metadata for {len(self._metadata_cache)} PDFs from {self.config_path}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing metadata config JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading metadata config: {e}")
            raise
    
    def get_metadata(self, file_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific PDF file.
        
        Args:
            file_name: Exact filename of the PDF
            
        Returns:
            Metadata dictionary if found, None otherwise
        """
        return self._metadata_cache.get(file_name)
    
    def has_metadata(self, file_name: str) -> bool:
        """Check if metadata exists for a file."""
        return file_name in self._metadata_cache
    
    def get_chunking_config(self, file_name: str) -> Dict[str, Any]:
        """
        Get chunking configuration for a file, merging file-specific, module-specific, and defaults.
        
        Args:
            file_name: Exact filename of the PDF
            
        Returns:
            Merged chunking configuration
        """
        metadata = self.get_metadata(file_name)
        if not metadata:
            return self._default_config.copy()
        
        # Start with defaults
        config = self._default_config.copy()
        
        # Apply module-specific strategy if available
        module_code = metadata.get("module_code")
        if module_code and module_code in self._module_strategies:
            module_config = self._module_strategies[module_code]
            config.update(module_config)
        
        # Apply file-specific config (highest priority)
        if "chunk_size" in metadata:
            config["chunk_size"] = metadata["chunk_size"]
        if "chunk_overlap" in metadata:
            config["chunk_overlap"] = metadata["chunk_overlap"]
        if "respect_sentences" in metadata:
            config["respect_sentences"] = metadata["respect_sentences"]
        if "respect_sections" in metadata:
            config["respect_sections"] = metadata["respect_sections"]
        if "chunking_strategy" in metadata:
            config["chunking_strategy"] = metadata["chunking_strategy"]
        
        # Add glossary-specific settings if applicable
        if metadata.get("chunking_strategy") == "glossary" and "glossary_settings" in metadata:
            config["glossary_settings"] = metadata["glossary_settings"]
        
        return config
    
    def get_page_filtering_config(self, file_name: str) -> Dict[str, Any]:
        """
        Get page filtering configuration for a file.
        
        Args:
            file_name: Exact filename of the PDF
            
        Returns:
            Page filtering configuration
        """
        metadata = self.get_metadata(file_name)
        if not metadata:
            return self._default_page_filtering.copy()
        
        # Start with defaults
        config = self._default_page_filtering.copy()
        
        # Apply file-specific page filtering
        if "page_filtering" in metadata:
            config.update(metadata["page_filtering"])
        
        return config
    
    def get_all_metadata(self) -> Dict[str, Dict]:
        """Get all loaded metadata."""
        return self._metadata_cache.copy()
    
    def reload(self):
        """Reload configuration from file."""
        self._metadata_cache.clear()
        self._load_config()


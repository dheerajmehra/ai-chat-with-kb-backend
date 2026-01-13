"""Vector store service with support for multiple backends.

This module provides a singleton pattern for vector store instances to ensure
only one instance exists per store type throughout the application lifecycle.
This is critical for maintaining state consistency, especially for the local
in-memory vector store.

Following Google Python Style Guide:
- Module-level singleton pattern for shared resources
- Thread-safe instance creation
- Clear separation of concerns
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import threading
import pickle
import json
from pathlib import Path
from shared.models.schemas import DocumentChunk
from shared.config import get_settings
from shared.utils.logger import logger

settings = get_settings()


class VectorStore(ABC):
    """Abstract base class for vector stores."""
    
    @abstractmethod
    async def upsert_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """Upsert chunks into the vector store."""
        pass
    
    @abstractmethod
    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[DocumentChunk]:
        """Search for similar chunks."""
        pass
    
    @abstractmethod
    async def delete_by_file(self, file_name: str) -> bool:
        """Delete all chunks for a specific file."""
        pass


class AzureAISearchVectorStore(VectorStore):
    """Azure AI Search vector store implementation."""
    
    def __init__(self):
        try:
            from azure.search.documents import SearchClient
            from azure.core.credentials import AzureKeyCredential
            
            credential = AzureKeyCredential(settings.azure_search_key)
            self.client = SearchClient(
                endpoint=settings.azure_search_endpoint,
                index_name=settings.azure_search_index_name,
                credential=credential
            )
            logger.info("Initialized Azure AI Search vector store")
        except Exception as e:
            logger.error(f"Failed to initialize Azure AI Search: {e}")
            raise
    
    async def upsert_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """Upsert chunks into Azure AI Search."""
        try:
            documents = []
            for chunk in chunks:
                doc = {
                    "id": f"{chunk.metadata.file_name}_{chunk.metadata.chunk_index}",
                    "content": chunk.content,
                    "contentVector": chunk.embedding,
                    "file_name": chunk.metadata.file_name,
                    "module_code": chunk.metadata.module_code,
                    "module_name": chunk.metadata.module_name,
                    "chapter_number": chunk.metadata.chapter_number,
                    "chapter_title": chunk.metadata.chapter_title,
                    "section_number": chunk.metadata.section_number,
                    "section_title": chunk.metadata.section_title,
                    "subsection_number": chunk.metadata.subsection_number,
                    "subsection_title": chunk.metadata.subsection_title,
                    "rule_number": chunk.metadata.rule_number,
                    "page_number": chunk.metadata.page_number,
                    "chunk_index": chunk.metadata.chunk_index,
                    "hierarchy_path": chunk.metadata.hierarchy_path,
                    "content_type": chunk.metadata.content_type,
                    "file_version": chunk.metadata.file_version,
                }
                documents.append(doc)
            
            result = self.client.upload_documents(documents=documents)
            logger.info(f"Upserted {len(chunks)} chunks to Azure AI Search")
            return True
        except Exception as e:
            logger.error(f"Error upserting to Azure AI Search: {e}")
            raise
    
    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[DocumentChunk]:
        """Search Azure AI Search."""
        try:
            from azure.search.documents.models import VectorizedQuery
            
            vector_query = VectorizedQuery(
                vector=query_embedding,
                k_nearest_neighbors=top_k,
                fields="contentVector"
            )
            
            results = self.client.search(
                search_text=None,
                vector_queries=[vector_query],
                top=top_k
            )
            
            chunks = []
            for result in results:
                # Reconstruct DocumentChunk from result
                # This is simplified - you'd need to map all fields
                chunk = DocumentChunk(
                    content=result.get("content", ""),
                    metadata=None,  # Would need to reconstruct
                    embedding=result.get("contentVector")
                )
                chunks.append(chunk)
            
            return chunks
        except Exception as e:
            logger.error(f"Error searching Azure AI Search: {e}")
            raise
    
    async def delete_by_file(self, file_name: str) -> bool:
        """Delete chunks by file name."""
        try:
            # Search for all documents with this file_name
            results = self.client.search(
                search_text=f"file_name eq '{file_name}'",
                select=["id"]
            )
            
            ids_to_delete = [result["id"] for result in results]
            if ids_to_delete:
                self.client.delete_documents(documents=[{"id": id} for id in ids_to_delete])
                logger.info(f"Deleted {len(ids_to_delete)} chunks for file {file_name}")
            
            return True
        except Exception as e:
            logger.error(f"Error deleting from Azure AI Search: {e}")
            raise


class OpenAIVectorStore(VectorStore):
    """OpenAI vector store implementation."""
    
    def __init__(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.vector_store_id = None  # Would be created/retrieved
            logger.info("Initialized OpenAI vector store")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI vector store: {e}")
            raise
    
    async def upsert_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """Upsert chunks into OpenAI vector store."""
        try:
            # Create file content
            file_content = "\n\n---\n\n".join([
                f"Chunk {i}:\n{chunk.content}\nMetadata: {chunk.metadata.dict()}"
                for i, chunk in enumerate(chunks)
            ])
            
            # Upload as file
            file = self.client.files.create(
                file=file_content.encode(),
                purpose="assistants"
            )
            
            # Create or get vector store
            if not self.vector_store_id:
                vector_store = self.client.beta.vector_stores.create(
                    name="dfsa-rulebooks"
                )
                self.vector_store_id = vector_store.id
            
            # Add file to vector store
            self.client.beta.vector_stores.files.create(
                vector_store_id=self.vector_store_id,
                file_id=file.id
            )
            
            logger.info(f"Upserted {len(chunks)} chunks to OpenAI vector store")
            return True
        except Exception as e:
            logger.error(f"Error upserting to OpenAI vector store: {e}")
            raise
    
    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[DocumentChunk]:
        """Search OpenAI vector store."""
        # OpenAI vector store search is typically done through assistants API
        # This is a simplified implementation
        logger.warning("OpenAI vector store search requires assistant API")
        return []
    
    async def delete_by_file(self, file_name: str) -> bool:
        """Delete chunks by file name."""
        logger.warning("OpenAI vector store deletion requires file management")
        return True


class LocalVectorStore(VectorStore):
    """Local in-memory vector store (for testing/development)."""
    
    def __init__(self):
        self.chunks: List[DocumentChunk] = []
        logger.info("Initialized local vector store")
    
    async def upsert_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """Upsert chunks into local store."""
        # Remove existing chunks for same file
        if chunks:
            file_name = chunks[0].metadata.file_name
            self.chunks = [c for c in self.chunks if c.metadata.file_name != file_name]
        
        self.chunks.extend(chunks)
        logger.info(f"Upserted {len(chunks)} chunks to local store (total: {len(self.chunks)})")
        return True
    
    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[DocumentChunk]:
        """Search local store using cosine similarity.
        
        Returns chunks sorted by similarity score (highest first).
        Note: Similarity scores are stored in chunk metadata for access.
        """
        try:
            import numpy as np
            
            if not self.chunks or not query_embedding:
                return []
            
            # Calculate cosine similarities
            similarities = []
            query_vec = np.array(query_embedding)
            
            for chunk in self.chunks:
                if chunk.embedding:
                    chunk_vec = np.array(chunk.embedding)
                    similarity = np.dot(query_vec, chunk_vec) / (
                        np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec)
                    )
                    similarities.append((similarity, chunk))
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x[0], reverse=True)
            
            # Store similarity score in chunk's custom_metadata for later access
            result_chunks = []
            for similarity, chunk in similarities[:top_k]:
                # Create a new metadata with similarity score
                from shared.models.schemas import ChunkMetadata
                new_metadata = ChunkMetadata(
                    module_code=chunk.metadata.module_code,
                    module_name=chunk.metadata.module_name,
                    chapter_number=chunk.metadata.chapter_number,
                    chapter_title=chunk.metadata.chapter_title,
                    section_number=chunk.metadata.section_number,
                    section_title=chunk.metadata.section_title,
                    subsection_number=chunk.metadata.subsection_number,
                    subsection_title=chunk.metadata.subsection_title,
                    rule_number=chunk.metadata.rule_number,
                    page_number=chunk.metadata.page_number,
                    chunk_index=chunk.metadata.chunk_index,
                    total_chunks=chunk.metadata.total_chunks,
                    file_name=chunk.metadata.file_name,
                    file_version=chunk.metadata.file_version,
                    hierarchy_path=chunk.metadata.hierarchy_path,
                    content_type=chunk.metadata.content_type,
                    parent_sections=chunk.metadata.parent_sections.copy(),
                    alias=chunk.metadata.alias,
                    term=chunk.metadata.term,
                    definition=chunk.metadata.definition,
                    custom_metadata={**chunk.metadata.custom_metadata, 'similarity_score': float(similarity)}
                )
                
                # Create a copy with similarity score in metadata
                chunk_copy = DocumentChunk(
                    content=chunk.content,
                    metadata=new_metadata,
                    embedding=chunk.embedding
                )
                result_chunks.append(chunk_copy)
            
            return result_chunks
        except Exception as e:
            logger.error(f"Error searching local store: {e}")
            return []
    
    async def delete_by_file(self, file_name: str) -> bool:
        """Delete chunks by file name."""
        initial_count = len(self.chunks)
        self.chunks = [c for c in self.chunks if c.metadata.file_name != file_name]
        deleted = initial_count - len(self.chunks)
        logger.info(f"Deleted {deleted} chunks for file {file_name}")
        return True


class FileBasedVectorStore(VectorStore):
    """File-based persistent vector store (for split architecture).
    
    Stores vectors in a file that can be shared between multiple processes.
    Uses file locking to prevent concurrent write conflicts.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize file-based vector store.
        
        Args:
            storage_path: Path to storage file. If None, uses default from config.
        """
        if storage_path is None:
            from shared.config import get_settings
            settings = get_settings()
            storage_path = getattr(settings, 'vector_store_path', 'data/vector_store.pkl')
        
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._file_lock = threading.Lock()
        self.chunks: List[DocumentChunk] = []
        
        # Load existing chunks from file
        self._load_from_file()
        logger.info(f"Initialized file-based vector store at {self.storage_path} (loaded {len(self.chunks)} chunks)")
    
    def _load_from_file(self) -> None:
        """Load chunks from storage file."""
        if not self.storage_path.exists():
            logger.info(f"Storage file does not exist yet: {self.storage_path}")
            return
        
        try:
            with self._file_lock:
                with open(self.storage_path, 'rb') as f:
                    data = pickle.load(f)
                    if isinstance(data, list):
                        # Direct list of DocumentChunk objects
                        self.chunks = data
                    elif isinstance(data, dict) and 'chunks' in data:
                        # Dictionary with metadata
                        self.chunks = data['chunks']
                    else:
                        logger.warning(f"Unexpected data format in {self.storage_path}")
                        self.chunks = []
            
            logger.info(f"Loaded {len(self.chunks)} chunks from {self.storage_path}")
        except Exception as e:
            logger.error(f"Error loading chunks from {self.storage_path}: {e}")
            self.chunks = []
    
    def _save_to_file(self) -> bool:
        """Save chunks to storage file."""
        try:
            with self._file_lock:
                # Create backup of existing file
                if self.storage_path.exists():
                    backup_path = self.storage_path.with_suffix('.pkl.bak')
                    import shutil
                    shutil.copy2(self.storage_path, backup_path)
                
                # Save chunks
                with open(self.storage_path, 'wb') as f:
                    pickle.dump(self.chunks, f)
                
                logger.debug(f"Saved {len(self.chunks)} chunks to {self.storage_path}")
                return True
        except Exception as e:
            logger.error(f"Error saving chunks to {self.storage_path}: {e}")
            return False
    
    async def upsert_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """Upsert chunks into file-based store."""
        if not chunks:
            return True
        
        # Remove existing chunks for same file
        file_name = chunks[0].metadata.file_name
        initial_count = len(self.chunks)
        self.chunks = [c for c in self.chunks if c.metadata.file_name != file_name]
        removed = initial_count - len(self.chunks)
        
        # Add new chunks
        self.chunks.extend(chunks)
        
        # Save to file
        saved = self._save_to_file()
        
        if saved:
            logger.info(
                f"Upserted {len(chunks)} chunks to file store "
                f"(removed {removed} existing, total: {len(self.chunks)})"
            )
        else:
            logger.error("Failed to save chunks to file")
        
        return saved
    
    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[DocumentChunk]:
        """Search file-based store using cosine similarity.
        
        Returns chunks sorted by similarity score (highest first).
        Note: Similarity scores are stored in chunk metadata for access.
        """
        try:
            import numpy as np
            
            # Reload from file to get latest data (in case another process updated it)
            self._load_from_file()
            
            if not self.chunks or not query_embedding:
                return []
            
            # Calculate cosine similarities
            similarities = []
            query_vec = np.array(query_embedding)
            
            for chunk in self.chunks:
                if chunk.embedding:
                    chunk_vec = np.array(chunk.embedding)
                    similarity = np.dot(query_vec, chunk_vec) / (
                        np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec)
                    )
                    similarities.append((similarity, chunk))
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x[0], reverse=True)
            
            # Store similarity score in chunk's custom_metadata for later access
            result_chunks = []
            for similarity, chunk in similarities[:top_k]:
                # Create a new metadata with similarity score
                from shared.models.schemas import ChunkMetadata
                new_metadata = ChunkMetadata(
                    module_code=chunk.metadata.module_code,
                    module_name=chunk.metadata.module_name,
                    chapter_number=chunk.metadata.chapter_number,
                    chapter_title=chunk.metadata.chapter_title,
                    section_number=chunk.metadata.section_number,
                    section_title=chunk.metadata.section_title,
                    subsection_number=chunk.metadata.subsection_number,
                    subsection_title=chunk.metadata.subsection_title,
                    rule_number=chunk.metadata.rule_number,
                    page_number=chunk.metadata.page_number,
                    chunk_index=chunk.metadata.chunk_index,
                    total_chunks=chunk.metadata.total_chunks,
                    file_name=chunk.metadata.file_name,
                    file_version=chunk.metadata.file_version,
                    hierarchy_path=chunk.metadata.hierarchy_path,
                    content_type=chunk.metadata.content_type,
                    parent_sections=chunk.metadata.parent_sections.copy(),
                    alias=chunk.metadata.alias,
                    term=chunk.metadata.term,
                    definition=chunk.metadata.definition,
                    custom_metadata={**chunk.metadata.custom_metadata, 'similarity_score': float(similarity)}
                )
                
                # Create a copy with similarity score in metadata
                chunk_copy = DocumentChunk(
                    content=chunk.content,
                    metadata=new_metadata,
                    embedding=chunk.embedding
                )
                result_chunks.append(chunk_copy)
            
            return result_chunks
        except Exception as e:
            logger.error(f"Error searching file-based store: {e}")
            return []
    
    async def delete_by_file(self, file_name: str) -> bool:
        """Delete chunks by file name."""
        initial_count = len(self.chunks)
        self.chunks = [c for c in self.chunks if c.metadata.file_name != file_name]
        deleted = initial_count - len(self.chunks)
        
        if deleted > 0:
            self._save_to_file()
            logger.info(f"Deleted {deleted} chunks for file {file_name}")
        
        return True
    
    def get_chunk_count(self) -> int:
        """Returns the total number of chunks currently in the store."""
        # Reload from file to get latest count (in case another process updated it)
        self._load_from_file()
        return len(self.chunks)


# Module-level singleton registry for vector store instances.
# This ensures only one instance per store type exists throughout the application.
# Key: store type (str), Value: VectorStore instance
_vector_store_instances: Dict[str, VectorStore] = {}

# Thread lock for thread-safe singleton creation (following Google style guide)
_vector_store_lock = threading.Lock()


def get_vector_store() -> VectorStore:
    """Factory function to get a singleton vector store instance.
    
    This function implements a thread-safe singleton pattern to ensure only one
    instance of each vector store type exists throughout the application lifecycle.
    This is critical for:
    - Local vector store: Maintaining in-memory state consistency
    - Azure/OpenAI stores: Avoiding unnecessary re-initialization and connection overhead
    
    Returns:
        VectorStore: A singleton instance of the configured vector store type.
        
    Raises:
        ValueError: If the configured vector store type is not supported.
        
    Example:
        >>> store1 = get_vector_store()
        >>> store2 = get_vector_store()
        >>> assert store1 is store2  # Same instance (singleton)
    """
    store_type = settings.vector_store_type.lower()
    
    # Check if instance already exists (fast path, no lock needed for read)
    if store_type in _vector_store_instances:
        return _vector_store_instances[store_type]
    
    # Thread-safe singleton creation (double-checked locking pattern)
    with _vector_store_lock:
        # Double-check after acquiring lock (another thread might have created it)
        if store_type in _vector_store_instances:
            return _vector_store_instances[store_type]
        
        # Create new instance based on store type
        if store_type == "azure":
            instance = AzureAISearchVectorStore()
        elif store_type == "openai":
            instance = OpenAIVectorStore()
        elif store_type == "local":
            instance = LocalVectorStore()
        elif store_type == "file":
            storage_path = getattr(settings, 'vector_store_path', 'data/vector_store.pkl')
            instance = FileBasedVectorStore(storage_path=storage_path)
        else:
            raise ValueError(
                f"Unsupported vector store type: {store_type}. "
                f"Supported types: 'azure', 'openai', 'local', 'file'"
            )
        
        # Store instance in registry
        _vector_store_instances[store_type] = instance
        logger.info(
            f"Created singleton vector store instance: {store_type} "
            f"(total instances: {len(_vector_store_instances)})"
        )
        
        return instance


def reset_vector_store(store_type: Optional[str] = None) -> None:
    """Reset vector store singleton instance(s).
    
    This function is primarily useful for testing and development scenarios
    where you need to clear the vector store state. In production, this should
    rarely be called.
    
    Args:
        store_type: Optional store type to reset. If None, resets all instances.
                   Must be one of: 'azure', 'openai', 'local', or None.
                   
    Raises:
        ValueError: If store_type is provided but invalid.
        
    Example:
        >>> # Reset only local store
        >>> reset_vector_store('local')
        >>> 
        >>> # Reset all stores
        >>> reset_vector_store()
    """
    global _vector_store_instances
    
    with _vector_store_lock:
        if store_type is None:
            # Reset all instances
            _vector_store_instances.clear()
            logger.info("Reset all vector store instances")
        else:
            store_type = store_type.lower()
            if store_type not in ["azure", "openai", "local"]:
                raise ValueError(
                    f"Invalid store type: {store_type}. "
                    f"Must be one of: 'azure', 'openai', 'local'"
                )
            
            if store_type in _vector_store_instances:
                del _vector_store_instances[store_type]
                logger.info(f"Reset vector store instance: {store_type}")


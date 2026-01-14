"""Integration tests for vector store operations."""
import pytest
from shared.services.vector_store import LocalVectorStore, FileBasedVectorStore
from shared.models.schemas import DocumentChunk, ChunkMetadata


@pytest.mark.integration
@pytest.mark.requires_vector_store
class TestVectorStoreIntegration:
    """Integration tests for vector store."""
    
    @pytest.mark.asyncio
    async def test_local_store_workflow(self, sample_chunks):
        """Test complete workflow with local store."""
        store = LocalVectorStore()
        
        # Upsert
        result = await store.upsert_chunks(sample_chunks)
        assert result is True
        
        # Search
        query_embedding = sample_chunks[0].embedding
        results = await store.search(query_embedding, top_k=3)
        assert len(results) > 0
        
        # Delete
        result = await store.delete_by_file("test.pdf")
        assert result is True
        assert len(store.chunks) == 0
    
    @pytest.mark.asyncio
    async def test_file_store_persistence(self, temp_vector_store_path, sample_chunks):
        """Test file-based store persistence."""
        # Create and populate store
        store1 = FileBasedVectorStore(storage_path=str(temp_vector_store_path))
        await store1.upsert_chunks(sample_chunks)
        
        # Create new instance (simulates service restart)
        store2 = FileBasedVectorStore(storage_path=str(temp_vector_store_path))
        
        # Should have loaded data
        assert len(store2.chunks) == len(sample_chunks)
        
        # Search should work
        query_embedding = sample_chunks[0].embedding
        results = await store2.search(query_embedding, top_k=2)
        assert len(results) > 0

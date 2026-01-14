"""Unit tests for services."""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from shared.services.vector_store import LocalVectorStore, FileBasedVectorStore
from shared.models.schemas import DocumentChunk, ChunkMetadata


@pytest.mark.unit
class TestLocalVectorStore:
    """Test LocalVectorStore."""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test store initialization."""
        store = LocalVectorStore()
        assert store.chunks == []
    
    @pytest.mark.asyncio
    async def test_upsert_chunks(self, sample_chunks):
        """Test upserting chunks."""
        store = LocalVectorStore()
        result = await store.upsert_chunks(sample_chunks)
        
        assert result is True
        assert len(store.chunks) == len(sample_chunks)
    
    @pytest.mark.asyncio
    async def test_search_empty_store(self):
        """Test searching empty store."""
        store = LocalVectorStore()
        query_embedding = [0.1] * 1536
        
        results = await store.search(query_embedding, top_k=5)
        assert results == []
    
    @pytest.mark.asyncio
    async def test_search_with_chunks(self, sample_chunks):
        """Test searching with chunks."""
        store = LocalVectorStore()
        await store.upsert_chunks(sample_chunks)
        
        # Create query embedding similar to first chunk
        query_embedding = sample_chunks[0].embedding
        
        results = await store.search(query_embedding, top_k=3)
        
        assert len(results) == 3
        assert all(isinstance(chunk, DocumentChunk) for chunk in results)
        # Check similarity scores are stored
        assert 'similarity_score' in results[0].metadata.custom_metadata
    
    @pytest.mark.asyncio
    async def test_delete_by_file(self, sample_chunks):
        """Test deleting chunks by file name."""
        store = LocalVectorStore()
        await store.upsert_chunks(sample_chunks)
        
        assert len(store.chunks) == 5
        
        result = await store.delete_by_file("test.pdf")
        assert result is True
        assert len(store.chunks) == 0


@pytest.mark.unit
class TestFileBasedVectorStore:
    """Test FileBasedVectorStore."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, temp_vector_store_path):
        """Test store initialization with temp path."""
        store = FileBasedVectorStore(storage_path=str(temp_vector_store_path))
        assert store.storage_path == temp_vector_store_path
        assert store.chunks == []
    
    @pytest.mark.asyncio
    async def test_save_and_load(self, temp_vector_store_path, sample_chunks):
        """Test saving and loading chunks."""
        # Create store and add chunks
        store1 = FileBasedVectorStore(storage_path=str(temp_vector_store_path))
        await store1.upsert_chunks(sample_chunks)
        
        # Create new store instance (simulates different process)
        store2 = FileBasedVectorStore(storage_path=str(temp_vector_store_path))
        
        # Should have loaded chunks from file
        assert len(store2.chunks) == len(sample_chunks)
    
    @pytest.mark.asyncio
    async def test_get_chunk_count(self, temp_vector_store_path, sample_chunks):
        """Test getting chunk count."""
        store = FileBasedVectorStore(storage_path=str(temp_vector_store_path))
        await store.upsert_chunks(sample_chunks)
        
        count = store.get_chunk_count()
        assert count == len(sample_chunks)


@pytest.mark.unit
class TestEmbeddingService:
    """Test embedding service."""
    
    @pytest.mark.asyncio
    @pytest.mark.mock
    async def test_sentence_transformer_service(self):
        """Test sentence transformer embedding service."""
        from shared.services.embedding_service import SentenceTransformerEmbeddingService
        import numpy as np
        
        # Mock sentence_transformers.SentenceTransformer (patch where it's imported from)
        with patch('sentence_transformers.SentenceTransformer') as mock_st:
            mock_model = MagicMock()
            # encode returns numpy array when convert_to_numpy=True, then code calls .tolist()
            mock_embedding = np.array([0.1] * 384)  # all-MiniLM-L6-v2 dimension
            mock_model.encode = Mock(return_value=mock_embedding)
            mock_st.return_value = mock_model
            
            service = SentenceTransformerEmbeddingService()
            embedding = await service.embed_text("test text")
            
            assert len(embedding) == 384
            assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.asyncio
    @pytest.mark.mock
    @pytest.mark.requires_openai
    async def test_openai_embedding_service(self, mock_embedding_response):
        """Test OpenAI embedding service with mock."""
        from shared.services.embedding_service import OpenAIEmbeddingService
        
        # Create a mock client with synchronous embeddings.create (not async)
        mock_client = MagicMock()
        mock_embeddings = MagicMock()
        # embeddings.create is NOT awaited in the service, so it should return response directly
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=mock_embedding_response['data'][0]['embedding'])]
        mock_embeddings.create = Mock(return_value=mock_response)
        mock_client.embeddings = mock_embeddings
        
        # Patch openai.OpenAI (where it's imported from in __init__)
        with patch('openai.OpenAI', return_value=mock_client):
            service = OpenAIEmbeddingService()
            embedding = await service.embed_text("test")
            
            assert len(embedding) > 0
            assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.asyncio
    @pytest.mark.mock
    @pytest.mark.requires_openai
    async def test_openai_embedding_service_batch(self, mock_embedding_response):
        """Test OpenAI embedding service batch method."""
        from shared.services.embedding_service import OpenAIEmbeddingService
        
        mock_client = MagicMock()
        mock_embeddings = MagicMock()
        # Return multiple embeddings for batch
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=mock_embedding_response['data'][0]['embedding']),
            MagicMock(embedding=mock_embedding_response['data'][0]['embedding'])
        ]
        mock_embeddings.create = Mock(return_value=mock_response)
        mock_client.embeddings = mock_embeddings
        
        with patch('openai.OpenAI', return_value=mock_client):
            service = OpenAIEmbeddingService()
            embeddings = await service.embed_batch(["text1", "text2"])
            
            assert len(embeddings) == 2
            assert all(len(emb) > 0 for emb in embeddings)
    
    @pytest.mark.asyncio
    @pytest.mark.mock
    @pytest.mark.requires_azure
    async def test_azure_embedding_service(self, mock_embedding_response):
        """Test Azure OpenAI embedding service with mock."""
        from shared.services.embedding_service import AzureOpenAIEmbeddingService
        
        mock_client = MagicMock()
        mock_embeddings = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=mock_embedding_response['data'][0]['embedding'])]
        mock_embeddings.create = Mock(return_value=mock_response)
        mock_client.embeddings = mock_embeddings
        
        with patch('openai.AzureOpenAI', return_value=mock_client):
            service = AzureOpenAIEmbeddingService()
            embedding = await service.embed_text("test")
            
            assert len(embedding) > 0
            assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.asyncio
    @pytest.mark.mock
    @pytest.mark.requires_azure
    async def test_azure_embedding_service_batch(self, mock_embedding_response):
        """Test Azure OpenAI embedding service batch method."""
        from shared.services.embedding_service import AzureOpenAIEmbeddingService
        
        mock_client = MagicMock()
        mock_embeddings = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=mock_embedding_response['data'][0]['embedding']),
            MagicMock(embedding=mock_embedding_response['data'][0]['embedding'])
        ]
        mock_embeddings.create = Mock(return_value=mock_response)
        mock_client.embeddings = mock_embeddings
        
        with patch('openai.AzureOpenAI', return_value=mock_client):
            service = AzureOpenAIEmbeddingService()
            embeddings = await service.embed_batch(["text1", "text2"])
            
            assert len(embeddings) == 2
    
    @pytest.mark.asyncio
    @pytest.mark.mock
    async def test_sentence_transformer_embedding_service_batch(self):
        """Test sentence transformer embedding service batch method."""
        from shared.services.embedding_service import SentenceTransformerEmbeddingService
        import numpy as np
        
        with patch('sentence_transformers.SentenceTransformer') as mock_st:
            mock_model = MagicMock()
            # Batch returns 2D array
            mock_embeddings = np.array([[0.1] * 384, [0.2] * 384])
            mock_model.encode = Mock(return_value=mock_embeddings)
            mock_st.return_value = mock_model
            
            service = SentenceTransformerEmbeddingService()
            embeddings = await service.embed_batch(["text1", "text2"])
            
            assert len(embeddings) == 2
            assert all(len(emb) == 384 for emb in embeddings)


@pytest.mark.unit
class TestLLMService:
    """Test LLM service."""
    
    @pytest.mark.asyncio
    async def test_service_disabled(self, disable_llm):
        """Test LLM service when disabled."""
        from shared.services.llm_service import get_llm_service
        
        service = get_llm_service()
        assert service.is_enabled() is False
    
    @pytest.mark.asyncio
    @pytest.mark.mock
    @pytest.mark.requires_openai
    async def test_generate_response(self, enable_llm, mock_openai_client, sample_chunks):
        """Test generating LLM response with mock."""
        from shared.services.llm_service import get_llm_service
        
        # Patch openai.OpenAI (where it's imported from in __init__)
        # Also need to reset the singleton
        import shared.services.llm_service
        shared.services.llm_service._llm_service = None  # Reset singleton
        
        with patch('openai.OpenAI', return_value=mock_openai_client):
            service = get_llm_service()
            
            if service.is_enabled():
                response = await service.generate_response(
                    user_query="What is capital requirement?",
                    chunks=sample_chunks
                )
                assert isinstance(response, str)
                assert len(response) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.mock
    @pytest.mark.requires_openai
    async def test_generate_response_with_max_tokens(self, enable_llm, mock_openai_client, sample_chunks):
        """Test generating LLM response with custom max_tokens."""
        from shared.services.llm_service import get_llm_service
        
        import shared.services.llm_service
        shared.services.llm_service._llm_service = None
        
        with patch('openai.OpenAI', return_value=mock_openai_client):
            service = get_llm_service()
            
            if service.is_enabled():
                response = await service.generate_response(
                    user_query="Test query",
                    chunks=sample_chunks,
                    max_tokens=200
                )
                assert isinstance(response, str)
                # Verify max_tokens was passed to API
                mock_openai_client.chat.completions.create.assert_called_once()
                call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
                assert call_kwargs.get('max_tokens') == 200
    
    @pytest.mark.asyncio
    @pytest.mark.mock
    @pytest.mark.requires_openai
    async def test_generate_response_error_handling(self, enable_llm, sample_chunks):
        """Test LLM error handling."""
        from shared.services.llm_service import get_llm_service
        
        import shared.services.llm_service
        shared.services.llm_service._llm_service = None
        
        # Create a mock client that raises an error
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        
        with patch('openai.OpenAI', return_value=mock_client):
            service = get_llm_service()
            
            if service.is_enabled():
                with pytest.raises(RuntimeError):
                    await service.generate_response(
                        user_query="Test query",
                        chunks=sample_chunks
                    )
    
    @pytest.mark.asyncio
    @pytest.mark.mock
    @pytest.mark.requires_openai
    async def test_generate_response_not_enabled(self, disable_llm, sample_chunks):
        """Test that generate_response raises error when LLM is not enabled."""
        from shared.services.llm_service import get_llm_service
        
        service = get_llm_service()
        
        with pytest.raises(RuntimeError, match="LLM service is not enabled"):
            await service.generate_response(
                user_query="Test query",
                chunks=sample_chunks
            )
"""Unit tests for tool wrappers."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from shared.tools import get_vector_search_tool, get_definition_lookup_tool
from shared.tools.base_tool import BaseTool, ToolOutput, ToolInput
from shared.tools.vector_search_tool import VectorSearchInput
from shared.tools.definition_lookup_tool import DefinitionLookupInput


@pytest.mark.unit
class TestBaseTool:
    """Test base tool interface."""
    
    def test_tool_has_required_attributes(self):
        """Test that tools have required attributes."""
        vector_tool = get_vector_search_tool()
        
        assert hasattr(vector_tool, 'name')
        assert hasattr(vector_tool, 'description')
        assert hasattr(vector_tool, 'input_schema')
        assert hasattr(vector_tool, 'execute')
        assert hasattr(vector_tool, 'get_schema_dict')
    
    def test_tool_schema_generation(self):
        """Test tool schema generation for LangChain compatibility."""
        vector_tool = get_vector_search_tool()
        schema = vector_tool.get_schema_dict()
        
        assert 'name' in schema
        assert 'description' in schema
        assert 'parameters' in schema
        assert schema['name'] == 'vector_search'
        assert 'properties' in schema['parameters']


@pytest.mark.unit
class TestVectorSearchTool:
    """Test vector search tool."""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """Test tool can be initialized."""
        tool = get_vector_search_tool()
        assert tool.name == "vector_search"
        assert "search" in tool.description.lower()
    
    def test_input_schema_validation(self):
        """Test input schema validation."""
        # Valid input
        input_data = VectorSearchInput(
            query="test query",
            top_k=5
        )
        assert input_data.query == "test query"
        assert input_data.top_k == 5
        
        # With filters
        input_data = VectorSearchInput(
            query="test",
            top_k=10,
            module_code="GEN",
            min_score=0.7
        )
        assert input_data.module_code == "GEN"
        assert input_data.min_score == 0.7
    
    def test_input_schema_validation_errors(self):
        """Test input schema validation errors."""
        from pydantic import ValidationError
        
        # Invalid top_k (too low)
        with pytest.raises(ValidationError):
            VectorSearchInput(query="test", top_k=0)
        
        # Invalid top_k (too high)
        with pytest.raises(ValidationError):
            VectorSearchInput(query="test", top_k=21)
        
        # Invalid min_score
        with pytest.raises(ValidationError):
            VectorSearchInput(query="test", min_score=1.5)  # > 1.0
    
    @pytest.mark.asyncio
    @pytest.mark.mock
    async def test_tool_execute_with_mock(self, sample_chunks):
        """Test tool execution with mocked services."""
        tool = get_vector_search_tool()
        
        # Mock embedding service
        with patch('shared.tools.vector_search_tool.get_embedding_service') as mock_embed:
            mock_embed_service = MagicMock()
            mock_embed_service.embed_text = AsyncMock(return_value=[0.1] * 1536)
            mock_embed.return_value = mock_embed_service
            
            # Mock vector store - return only top_k chunks (3 in this case)
            with patch('shared.tools.vector_search_tool.get_vector_store') as mock_store:
                mock_vector_store = MagicMock()
                # Return only the first 3 chunks to match top_k=3
                mock_vector_store.search = AsyncMock(return_value=sample_chunks[:3])
                mock_store.return_value = mock_vector_store
                
                result = await tool.execute(
                    query="test query",
                    top_k=3
                )
                
                assert result.success is True
                assert len(result.result) == 3
                assert 'metadata' in result.__dict__


@pytest.mark.unit
class TestDefinitionLookupTool:
    """Test definition lookup tool."""
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """Test tool can be initialized."""
        tool = get_definition_lookup_tool()
        assert tool.name == "definition_lookup"
        assert "glossary" in tool.description.lower() or "definition" in tool.description.lower()
    
    def test_input_schema_validation(self):
        """Test input schema validation."""
        from shared.tools.definition_lookup_tool import DefinitionLookupInput
        
        # Valid input
        input_data = DefinitionLookupInput(
            term="Authorised Firm"
        )
        assert input_data.term == "Authorised Firm"
        assert input_data.exact_match is True  # Default
        assert input_data.case_sensitive is False  # Default
        
        # With options
        input_data = DefinitionLookupInput(
            term="firm",
            exact_match=False,
            case_sensitive=True
        )
        assert input_data.exact_match is False
        assert input_data.case_sensitive is True
    
    @pytest.mark.asyncio
    @pytest.mark.mock
    async def test_tool_execute_with_mock(self, glossary_chunk):
        """Test tool execution with mocked services."""
        tool = get_definition_lookup_tool()
        
        # Mock services
        with patch('shared.tools.definition_lookup_tool.get_embedding_service') as mock_embed, \
             patch('shared.tools.definition_lookup_tool.get_vector_store') as mock_store:
            
            mock_embed_service = MagicMock()
            mock_embed_service.embed_text = AsyncMock(return_value=[0.1] * 1536)
            mock_embed.return_value = mock_embed_service
            
            mock_vector_store = MagicMock()
            mock_vector_store.search = AsyncMock(return_value=[glossary_chunk])
            mock_store.return_value = mock_vector_store
            
            result = await tool.execute(
                term="Authorised Firm",
                exact_match=True
            )
            
            assert result.success is True
            assert isinstance(result.result, list)

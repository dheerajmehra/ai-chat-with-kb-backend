"""Vector search tool for semantic similarity search in the vector store."""
from typing import Optional, List
from pydantic import BaseModel, Field
from shared.tools.base_tool import BaseTool, ToolInput, ToolOutput
from shared.services.vector_store import get_vector_store
from shared.services.embedding_service import get_embedding_service
from shared.models.schemas import DocumentChunk
from shared.utils.logger import logger


class VectorSearchInput(ToolInput):
    """Input schema for vector search tool."""
    query: str = Field(..., description="The search query to find relevant document chunks")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of top results to return")
    module_code: Optional[str] = Field(None, description="Filter by module code (e.g., 'GEN', 'PRU', 'GLO')")
    rule_number: Optional[str] = Field(None, description="Filter by rule number (e.g., 'GEN 2.1.1')")
    content_type: Optional[str] = Field(None, description="Filter by content type (e.g., 'rule', 'glossary_definition')")
    min_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum similarity score threshold")


class VectorSearchTool(BaseTool):
    """
    Tool for performing semantic similarity search in the vector store.
    
    This tool wraps the existing vector_store.search() functionality and makes it
    available as a tool that can be used by agents (e.g., LangChain agents).
    
    Example usage:
        tool = VectorSearchTool()
        result = await tool.execute(
            query="What are capital requirements?",
            top_k=5,
            module_code="PRU"
        )
    """
    
    def __init__(self):
        """Initialize the vector search tool."""
        super().__init__(
            name="vector_search",
            description=(
                "Search the DFSA rulebook vector store for relevant document chunks "
                "based on semantic similarity. Use this tool to find information "
                "related to a query. Returns chunks with similarity scores."
            ),
            input_schema=VectorSearchInput
        )
        self._vector_store = None
        self._embedding_service = None
    
    def _get_services(self):
        """Lazy initialization of services."""
        if self._vector_store is None:
            self._vector_store = get_vector_store()
        if self._embedding_service is None:
            self._embedding_service = get_embedding_service()
    
    async def execute(self, **kwargs) -> ToolOutput:
        """
        Execute vector search.
        
        Args:
            query: Search query
            top_k: Number of results (default: 5)
            module_code: Optional module filter
            rule_number: Optional rule number filter
            content_type: Optional content type filter
            min_score: Optional minimum similarity score
        
        Returns:
            ToolOutput with list of DocumentChunk results
        """
        try:
            # Validate input
            input_data = VectorSearchInput(**kwargs)
            
            # Get services
            self._get_services()
            
            # Embed the query
            logger.debug(f"VectorSearchTool: Embedding query: {input_data.query[:100]}...")
            query_embedding = await self._embedding_service.embed_text(input_data.query)
            
            # Search vector store
            logger.debug(f"VectorSearchTool: Searching with top_k={input_data.top_k}")
            chunks = await self._vector_store.search(
                query_embedding=query_embedding,
                top_k=input_data.top_k
            )
            
            # Apply filters
            filtered_chunks = chunks
            if input_data.module_code:
                filtered_chunks = [
                    c for c in filtered_chunks
                    if c.metadata.module_code == input_data.module_code
                ]
                logger.debug(f"VectorSearchTool: Filtered by module_code={input_data.module_code}: {len(filtered_chunks)} results")
            
            if input_data.rule_number:
                filtered_chunks = [
                    c for c in filtered_chunks
                    if c.metadata.rule_number == input_data.rule_number
                ]
                logger.debug(f"VectorSearchTool: Filtered by rule_number={input_data.rule_number}: {len(filtered_chunks)} results")
            
            if input_data.content_type:
                filtered_chunks = [
                    c for c in filtered_chunks
                    if c.metadata.content_type == input_data.content_type
                ]
                logger.debug(f"VectorSearchTool: Filtered by content_type={input_data.content_type}: {len(filtered_chunks)} results")
            
            # Apply minimum score filter
            if input_data.min_score is not None:
                filtered_chunks = [
                    c for c in filtered_chunks
                    if c.metadata.custom_metadata.get('similarity_score', 0.0) >= input_data.min_score
                ]
                logger.debug(f"VectorSearchTool: Filtered by min_score={input_data.min_score}: {len(filtered_chunks)} results")
            
            # Format results
            results = []
            for chunk in filtered_chunks:
                score = chunk.metadata.custom_metadata.get('similarity_score', 0.0)
                results.append({
                    "content": chunk.content[:500],  # Limit content length
                    "score": score,
                    "module_code": chunk.metadata.module_code,
                    "module_name": chunk.metadata.module_name,
                    "rule_number": chunk.metadata.rule_number,
                    "page_number": chunk.metadata.page_number,
                    "hierarchy_path": chunk.metadata.hierarchy_path,
                    "file_name": chunk.metadata.file_name,
                    "document_name": chunk.metadata.alias or chunk.metadata.module_name or chunk.metadata.file_name,
                })
            
            logger.info(f"VectorSearchTool: Found {len(results)} results for query: {input_data.query[:50]}...")
            
            return ToolOutput(
                success=True,
                result=results,
                metadata={
                    "query": input_data.query,
                    "total_results": len(results),
                    "filters_applied": {
                        "module_code": input_data.module_code,
                        "rule_number": input_data.rule_number,
                        "content_type": input_data.content_type,
                        "min_score": input_data.min_score,
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"VectorSearchTool error: {e}", exc_info=True)
            return ToolOutput(
                success=False,
                result=[],
                error=str(e),
                metadata={"query": kwargs.get("query", "unknown")}
            )


# Singleton instance
_vector_search_tool: Optional[VectorSearchTool] = None


def get_vector_search_tool() -> VectorSearchTool:
    """Get or create vector search tool singleton."""
    global _vector_search_tool
    if _vector_search_tool is None:
        _vector_search_tool = VectorSearchTool()
    return _vector_search_tool

"""Definition lookup tool for finding glossary definitions from the GLO module."""
from typing import Optional, List
from pydantic import BaseModel, Field
from shared.tools.base_tool import BaseTool, ToolInput, ToolOutput
from shared.services.vector_store import get_vector_store
from shared.services.embedding_service import get_embedding_service
from shared.utils.logger import logger


class DefinitionLookupInput(ToolInput):
    """Input schema for definition lookup tool."""
    term: str = Field(..., description="The term to look up in the glossary (e.g., 'Authorised Firm', 'Capital Requirement')")
    exact_match: bool = Field(default=True, description="Whether to require exact term match (True) or allow fuzzy matching (False)")
    case_sensitive: bool = Field(default=False, description="Whether the term match should be case-sensitive")


class DefinitionLookupTool(BaseTool):
    """
    Tool for looking up definitions from the DFSA Glossary (GLO module).
    
    This tool searches for glossary definitions by term name. It looks for chunks
    with content_type="glossary_definition" and matches the term field.
    
    Example usage:
        tool = DefinitionLookupTool()
        result = await tool.execute(
            term="Authorised Firm",
            exact_match=True
        )
    """
    
    def __init__(self):
        """Initialize the definition lookup tool."""
        super().__init__(
            name="definition_lookup",
            description=(
                "Look up the definition of a term from the DFSA Glossary (GLO module). "
                "Use this tool when you need to understand what a specific term means "
                "according to DFSA regulations. Returns the term and its definition."
            ),
            input_schema=DefinitionLookupInput
        )
        self._vector_store = None
        self._embedding_service = None
    
    def _get_services(self):
        """Lazy initialization of services."""
        if self._vector_store is None:
            self._vector_store = get_vector_store()
        if self._embedding_service is None:
            self._embedding_service = get_embedding_service()
    
    async def _search_glossary_chunks(self, term: str, exact_match: bool, case_sensitive: bool) -> List:
        """
        Search for glossary chunks containing the term.
        
        This method uses vector search to find relevant glossary chunks, then
        filters for exact term matches.
        """
        self._get_services()
        
        # Use vector search to find glossary chunks related to the term
        # We search for the term in the glossary context
        query = f"definition of {term}"
        query_embedding = await self._embedding_service.embed_text(query)
        
        # Search with higher top_k to get more candidates for filtering
        chunks = await self._vector_store.search(
            query_embedding=query_embedding,
            top_k=20  # Get more candidates for filtering
        )
        
        # Filter for glossary definitions only
        glossary_chunks = [
            c for c in chunks
            if c.metadata.content_type == "glossary_definition"
        ]
        
        # Match terms
        matched_chunks = []
        term_normalized = term if case_sensitive else term.lower()
        
        for chunk in glossary_chunks:
            chunk_term = chunk.metadata.term
            if not chunk_term:
                continue
            
            chunk_term_normalized = chunk_term if case_sensitive else chunk_term.lower()
            
            if exact_match:
                if chunk_term_normalized == term_normalized:
                    matched_chunks.append(chunk)
            else:
                # Fuzzy match: check if term is contained in chunk term or vice versa
                if (term_normalized in chunk_term_normalized or 
                    chunk_term_normalized in term_normalized):
                    matched_chunks.append(chunk)
        
        return matched_chunks
    
    async def execute(self, **kwargs) -> ToolOutput:
        """
        Execute definition lookup.
        
        Args:
            term: The term to look up
            exact_match: Whether to require exact match (default: True)
            case_sensitive: Whether match is case-sensitive (default: False)
        
        Returns:
            ToolOutput with definition results
        """
        try:
            # Validate input
            input_data = DefinitionLookupInput(**kwargs)
            
            logger.debug(f"DefinitionLookupTool: Looking up term: {input_data.term}")
            
            # Search for glossary chunks
            matched_chunks = await self._search_glossary_chunks(
                term=input_data.term,
                exact_match=input_data.exact_match,
                case_sensitive=input_data.case_sensitive
            )
            
            if not matched_chunks:
                logger.info(f"DefinitionLookupTool: No definition found for term: {input_data.term}")
                return ToolOutput(
                    success=True,
                    result=[],
                    metadata={
                        "term": input_data.term,
                        "exact_match": input_data.exact_match,
                        "case_sensitive": input_data.case_sensitive,
                        "message": f"No definition found for term: {input_data.term}"
                    }
                )
            
            # Format results
            results = []
            for chunk in matched_chunks:
                term = chunk.metadata.term
                definition = chunk.metadata.definition or chunk.content
                
                # Extract definition if it's in the format "Term: definition"
                if not chunk.metadata.definition and ":" in chunk.content:
                    parts = chunk.content.split(":", 1)
                    if len(parts) == 2:
                        term = parts[0].strip()
                        definition = parts[1].strip()
                
                results.append({
                    "term": term,
                    "definition": definition,
                    "module_code": chunk.metadata.module_code,
                    "module_name": chunk.metadata.module_name,
                    "page_number": chunk.metadata.page_number,
                    "hierarchy_path": chunk.metadata.hierarchy_path,
                    "file_name": chunk.metadata.file_name,
                })
            
            logger.info(f"DefinitionLookupTool: Found {len(results)} definition(s) for term: {input_data.term}")
            
            return ToolOutput(
                success=True,
                result=results,
                metadata={
                    "term": input_data.term,
                    "exact_match": input_data.exact_match,
                    "case_sensitive": input_data.case_sensitive,
                    "count": len(results)
                }
            )
            
        except Exception as e:
            logger.error(f"DefinitionLookupTool error: {e}", exc_info=True)
            return ToolOutput(
                success=False,
                result=[],
                error=str(e),
                metadata={"term": kwargs.get("term", "unknown")}
            )


# Singleton instance
_definition_lookup_tool: Optional[DefinitionLookupTool] = None


def get_definition_lookup_tool() -> DefinitionLookupTool:
    """Get or create definition lookup tool singleton."""
    global _definition_lookup_tool
    if _definition_lookup_tool is None:
        _definition_lookup_tool = DefinitionLookupTool()
    return _definition_lookup_tool

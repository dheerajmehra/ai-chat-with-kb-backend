# RAG Tools

This directory contains tool definitions for the agentic RAG system. These tools are designed to be compatible with LangChain/LangGraph, allowing easy integration when those frameworks are added.

## Tools

### 1. VectorSearchTool

Performs semantic similarity search in the vector store.

**Input:**
- `query` (str): Search query
- `top_k` (int, default=5): Number of results
- `module_code` (str, optional): Filter by module (e.g., "GEN", "PRU")
- `rule_number` (str, optional): Filter by rule number
- `content_type` (str, optional): Filter by content type
- `min_score` (float, optional): Minimum similarity score

**Output:**
- List of document chunks with metadata and similarity scores

**Example:**
```python
from shared.tools import get_vector_search_tool

tool = get_vector_search_tool()
result = await tool.execute(
    query="What are capital requirements?",
    top_k=5,
    module_code="PRU"
)
```

### 2. DefinitionLookupTool

Looks up definitions from the DFSA Glossary (GLO module).

**Input:**
- `term` (str): Term to look up
- `exact_match` (bool, default=True): Require exact match
- `case_sensitive` (bool, default=False): Case-sensitive matching

**Output:**
- List of definitions matching the term

**Example:**
```python
from shared.tools import get_definition_lookup_tool

tool = get_definition_lookup_tool()
result = await tool.execute(
    term="Authorised Firm",
    exact_match=True
)
```

## Design Philosophy

### LangChain Compatibility

These tools are designed to be easily wrapped for LangChain:

```python
# Future integration (when LangChain is added):
from langchain.tools import StructuredTool
from shared.tools import get_vector_search_tool

vector_tool = get_vector_search_tool()
langchain_tool = StructuredTool.from_function(
    func=vector_tool.execute,
    name=vector_tool.name,
    description=vector_tool.description,
    args_schema=vector_tool.input_schema
)
```

### Tool Interface

All tools inherit from `BaseTool` which provides:
- Standardized input/output schemas
- Error handling
- Metadata tracking
- Schema generation for LangChain

### Singleton Pattern

Tools use singleton pattern for consistency:
- `get_vector_search_tool()` - Returns singleton instance
- `get_definition_lookup_tool()` - Returns singleton instance

## Usage Without Agents

These tools can be used directly without LangChain:

```python
from shared.tools import get_vector_search_tool, get_definition_lookup_tool

# Vector search
vector_tool = get_vector_search_tool()
result = await vector_tool.execute(query="capital requirements", top_k=5)
if result.success:
    for chunk in result.result:
        print(f"Score: {chunk['score']}, Content: {chunk['content'][:100]}")

# Definition lookup
def_tool = get_definition_lookup_tool()
result = await def_tool.execute(term="Authorised Firm")
if result.success:
    for definition in result.result:
        print(f"{definition['term']}: {definition['definition']}")
```

## Future Extensions

When implementing agents, additional tools can be added:
- `CrossReferenceTool` - Find related rules
- `MetadataFilterTool` - Advanced filtering
- `QueryRewriteTool` - Improve queries
- `RuleLookupTool` - Find specific rules by number

## Testing

Tools can be tested independently:

```python
import asyncio
from shared.tools import get_vector_search_tool

async def test_vector_search():
    tool = get_vector_search_tool()
    result = await tool.execute(
        query="What are capital requirements?",
        top_k=3
    )
    print(f"Success: {result.success}")
    print(f"Results: {len(result.result)}")
    print(f"Metadata: {result.metadata}")

asyncio.run(test_vector_search())
```

# Tool Wrappers Implementation

## Overview

Tool wrappers have been created for vector search and definition lookup. These tools are designed to be compatible with LangChain/LangGraph but can be used independently now.

## What Was Created

### Directory Structure

```
shared/tools/
├── __init__.py                    # Tool exports
├── base_tool.py                   # Base tool interface
├── vector_search_tool.py          # Vector search tool
├── definition_lookup_tool.py      # Definition lookup tool
└── README.md                      # Tool documentation
```

### Files Created

1. **`shared/tools/base_tool.py`**
   - Base class for all tools
   - Provides standardized interface
   - LangChain-compatible schema generation
   - Error handling and metadata tracking

2. **`shared/tools/vector_search_tool.py`**
   - Wraps `vector_store.search()`
   - Supports filtering by module, rule number, content type
   - Returns chunks with similarity scores
   - Singleton pattern

3. **`shared/tools/definition_lookup_tool.py`**
   - Looks up glossary definitions from GLO module
   - Supports exact and fuzzy matching
   - Case-sensitive/insensitive options
   - Uses vector search to find relevant glossary chunks

4. **`shared/tools/README.md`**
   - Usage documentation
   - Examples
   - LangChain integration guide

5. **`test_tools.py`**
   - Test script to verify tools work
   - Can be run independently

## Tool Interface

### BaseTool Class

All tools inherit from `BaseTool` which provides:

```python
class BaseTool:
    name: str                    # Tool name (e.g., "vector_search")
    description: str             # Description for LLM
    input_schema: BaseModel      # Pydantic input schema
    
    async def execute(**kwargs) -> ToolOutput
    def get_schema_dict() -> Dict  # For LangChain compatibility
```

### ToolOutput

Standardized output format:

```python
class ToolOutput:
    success: bool                # Execution success
    result: Any                 # Tool result
    error: Optional[str]        # Error message if failed
    metadata: Dict[str, Any]    # Additional metadata
```

## Usage Examples

### Vector Search Tool

```python
from shared.tools import get_vector_search_tool

tool = get_vector_search_tool()
result = await tool.execute(
    query="What are capital requirements?",
    top_k=5,
    module_code="PRU",
    min_score=0.7
)

if result.success:
    for chunk in result.result:
        print(f"Score: {chunk['score']}")
        print(f"Content: {chunk['content']}")
```

### Definition Lookup Tool

```python
from shared.tools import get_definition_lookup_tool

tool = get_definition_lookup_tool()
result = await tool.execute(
    term="Authorised Firm",
    exact_match=True
)

if result.success:
    for definition in result.result:
        print(f"{definition['term']}: {definition['definition']}")
```

## LangChain Compatibility

When LangChain is added, tools can be wrapped easily:

```python
from langchain.tools import StructuredTool
from shared.tools import get_vector_search_tool

# Get our tool
vector_tool = get_vector_search_tool()

# Wrap for LangChain
langchain_tool = StructuredTool.from_function(
    func=vector_tool.execute,
    name=vector_tool.name,
    description=vector_tool.description,
    args_schema=vector_tool.input_schema
)

# Use in agent
agent = create_agent(tools=[langchain_tool])
```

## Tool Features

### VectorSearchTool

**Input Parameters:**
- `query` (str): Search query
- `top_k` (int, default=5): Number of results
- `module_code` (str, optional): Filter by module
- `rule_number` (str, optional): Filter by rule number
- `content_type` (str, optional): Filter by content type
- `min_score` (float, optional): Minimum similarity score

**Output:**
- List of chunks with:
  - Content (truncated to 500 chars)
  - Similarity score
  - Module code/name
  - Rule number
  - Page number
  - Hierarchy path
  - File name

### DefinitionLookupTool

**Input Parameters:**
- `term` (str): Term to look up
- `exact_match` (bool, default=True): Require exact match
- `case_sensitive` (bool, default=False): Case-sensitive matching

**Output:**
- List of definitions with:
  - Term
  - Definition text
  - Module code/name
  - Page number
  - Hierarchy path
  - File name

## Design Decisions

### 1. Singleton Pattern
- Tools use singleton pattern for consistency
- Lazy initialization of services (vector store, embedding service)

### 2. Async Interface
- All tools are async for consistency with existing codebase
- Can be called from async contexts

### 3. Pydantic Schemas
- Input validation using Pydantic
- Type-safe parameters
- Automatic schema generation for LangChain

### 4. Error Handling
- Tools return `ToolOutput` with success flag
- Errors are captured and returned, not raised
- Allows agents to handle failures gracefully

### 5. Metadata Tracking
- All tool outputs include metadata
- Useful for debugging and monitoring
- Tracks filters applied, query terms, etc.

## Testing

Run the test script:

```bash
python test_tools.py
```

This will:
- Test vector search with various filters
- Test definition lookup with exact/fuzzy matching
- Verify tool schemas
- Show LangChain compatibility

## Next Steps

1. **Add LangChain** (when ready):
   ```bash
   pip install langchain langchain-openai langgraph
   ```

2. **Wrap tools for LangChain**:
   - Use `StructuredTool.from_function()`
   - Add to agent tool list

3. **Create additional tools** (future):
   - `CrossReferenceTool` - Find related rules
   - `MetadataFilterTool` - Advanced filtering
   - `QueryRewriteTool` - Improve queries

4. **Build agents**:
   - Query planning agent
   - Retrieval agent
   - Synthesis agent

## Notes

- Tools are **not used** in the current chat endpoint yet
- Tools are **ready** for LangChain/LangGraph integration
- Tools can be **tested independently** without agents
- All tools follow the same interface pattern
- Error handling is consistent across all tools

## Files Modified

- None (all new files)

## Files Created

- `shared/tools/__init__.py`
- `shared/tools/base_tool.py`
- `shared/tools/vector_search_tool.py`
- `shared/tools/definition_lookup_tool.py`
- `shared/tools/README.md`
- `test_tools.py`
- `TOOLS_IMPLEMENTATION.md` (this file)

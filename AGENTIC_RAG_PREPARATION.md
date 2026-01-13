# Agentic RAG Migration - Pre-Implementation Guide

## Overview

This document outlines what needs to be done **before** implementing an agentic RAG approach. An agentic RAG system enables autonomous query planning, multi-step retrieval, iterative refinement, and intelligent tool use.

## Current Architecture Analysis

### What We Have Now
- ✅ **Simple RAG Pipeline**: Query → Embed → Search → Return chunks
- ✅ **LLM Integration**: Optional response generation from retrieved chunks
- ✅ **Vector Store**: File-based persistent storage with similarity search
- ✅ **Metadata-Rich Chunks**: Rule numbers, modules, hierarchy paths
- ✅ **Split Architecture**: Ingestion and Chat services

### What's Missing for Agentic Approach
- ❌ **Query Planning**: No decomposition of complex queries
- ❌ **Multi-Step Retrieval**: Single retrieval pass only
- ❌ **Tool System**: No structured tools for agents to use
- ❌ **State Management**: No conversation/planning state tracking
- ❌ **Iterative Refinement**: No ability to refine queries based on results
- ❌ **Decision Making**: No autonomous decision about when to stop/continue

## Pre-Implementation Checklist

### 1. Framework Selection & Dependencies

#### Option A: LangChain + LangGraph (Recommended)
**Pros:**
- Mature ecosystem with agent frameworks
- Built-in tool system
- State management with LangGraph
- Good documentation

**Cons:**
- Larger dependency footprint
- Can be complex for simple use cases

**Dependencies to Add:**
```txt
langchain>=0.1.0
langchain-openai>=0.0.5
langgraph>=0.0.20
langchain-community>=0.0.20
```

#### Option B: OpenAI Function Calling + Custom Orchestration
**Pros:**
- Lightweight
- Direct control
- No additional dependencies

**Cons:**
- More custom code to write
- Manual state management

**Dependencies:**
- Already have `openai>=1.3.7` ✅

#### Option C: LlamaIndex Agent Framework
**Pros:**
- RAG-optimized
- Built-in query engines
- Good for document Q&A

**Cons:**
- Less flexible than LangChain
- May require restructuring

**Dependencies:**
```txt
llama-index>=0.10.0
llama-index-agent-openai>=0.1.0
```

**Recommendation: Start with Option A (LangChain + LangGraph)**

### 2. Tool Definitions

Before implementing agents, define what tools they can use:

#### Required Tools

1. **Vector Search Tool**
   - Input: Query string, top_k, filters (module, rule_number, etc.)
   - Output: List of relevant chunks with scores
   - Current implementation: ✅ Exists in `vector_store.search()`

2. **Definition Lookup Tool** (for Glossary)
   - Input: Term name
   - Output: Definition from GLO module
   - Current implementation: ❌ Need to build

3. **Metadata Filter Tool**
   - Input: Module code, rule number, page range
   - Output: Filtered chunks
   - Current implementation: ⚠️ Partial (need to enhance)

4. **Cross-Reference Tool**
   - Input: Rule number (e.g., "GEN 2.1.1")
   - Output: Related rules and references
   - Current implementation: ❌ Need to build

5. **Query Rewriter Tool**
   - Input: Original query, context
   - Output: Improved/expanded query
   - Current implementation: ❌ Need to build

#### Action Items
- [ ] Create `shared/services/tools.py` with tool definitions
- [ ] Implement definition lookup from GLO module
- [ ] Enhance vector store with metadata filtering
- [ ] Build cross-reference index during ingestion

### 3. Agent Architecture Design

#### Proposed Agent Structure

```
┌─────────────────────────────────────────────────┐
│           Query Planning Agent                   │
│  - Analyzes user query                           │
│  - Decomposes into sub-queries                   │
│  - Determines retrieval strategy                 │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│           Retrieval Agent                       │
│  - Executes vector search                        │
│  - Applies filters                               │
│  - Fetches definitions                            │
│  - Follows cross-references                      │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│           Synthesis Agent                       │
│  - Combines retrieved information                │
│  - Generates coherent response                   │
│  - Adds citations                                │
└─────────────────────────────────────────────────┘
```

#### State Management

Need to track:
- Original query
- Sub-queries and their results
- Retrieved chunks (with deduplication)
- Tool call history
- Current reasoning step
- Confidence scores

**Action Items:**
- [ ] Design state schema (`AgentState` model)
- [ ] Implement state persistence (optional, for debugging)
- [ ] Create state transition logic

### 4. Data Structure Enhancements

#### Current Chunk Metadata
```python
ChunkMetadata:
  - module_code, module_name
  - rule_number, hierarchy_path
  - page_number, chunk_index
  - term, definition (for glossary)
```

#### Needed Additions
- [ ] **Cross-reference mapping**: Which rules reference this rule?
- [ ] **Definition index**: Fast lookup for glossary terms
- [ ] **Rule dependency graph**: Relationships between rules
- [ ] **Content type classification**: Rule, definition, example, etc.

**Action Items:**
- [ ] Enhance ingestion to extract cross-references
- [ ] Build definition index during GLO processing
- [ ] Create rule dependency graph
- [ ] Add content classification

### 5. Configuration Updates

#### New Environment Variables Needed

```bash
# Agent Configuration
AGENT_ENABLED=true
AGENT_FRAMEWORK=langchain  # or "openai" or "llama-index"
AGENT_MAX_ITERATIONS=5
AGENT_ENABLE_PLANNING=true
AGENT_ENABLE_REFINEMENT=true

# Tool Configuration
TOOL_VECTOR_SEARCH_ENABLED=true
TOOL_DEFINITION_LOOKUP_ENABLED=true
TOOL_CROSS_REFERENCE_ENABLED=true
TOOL_QUERY_REWRITE_ENABLED=true

# Agent Model (can be different from LLM model)
AGENT_MODEL=gpt-4o
AGENT_TEMPERATURE=0.3  # Lower for more deterministic planning
```

**Action Items:**
- [ ] Add agent config to `shared/config.py`
- [ ] Update `env.example` with new variables
- [ ] Document configuration options

### 6. Testing Strategy

#### Before Implementation
- [ ] Create test queries of varying complexity:
  - Simple: "What is capital requirement?"
  - Medium: "Compare capital requirements in GEN and PRU modules"
  - Complex: "Explain how capital requirements apply to banks that also do insurance business"
- [ ] Define success criteria for each query type
- [ ] Set up evaluation framework

#### During Implementation
- [ ] Unit tests for each tool
- [ ] Integration tests for agent workflows
- [ ] End-to-end tests with real queries
- [ ] Performance benchmarks

**Action Items:**
- [ ] Create `tests/agent/` directory
- [ ] Write test query suite
- [ ] Set up evaluation metrics (accuracy, relevance, completeness)

### 7. Migration Path

#### Phase 1: Foundation (Week 1)
- [ ] Install dependencies
- [ ] Create tool definitions
- [ ] Build definition lookup tool
- [ ] Enhance metadata extraction

#### Phase 2: Basic Agent (Week 2)
- [ ] Implement query planning agent
- [ ] Create retrieval agent with tools
- [ ] Add state management
- [ ] Basic end-to-end flow

#### Phase 3: Advanced Features (Week 3)
- [ ] Iterative refinement
- [ ] Cross-reference following
- [ ] Multi-step reasoning
- [ ] Response synthesis

#### Phase 4: Optimization (Week 4)
- [ ] Performance tuning
- [ ] Cost optimization
- [ ] Error handling
- [ ] Documentation

### 8. Code Structure Planning

#### Proposed Directory Structure

```
shared/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py          # Base agent class
│   ├── query_planner.py        # Query planning agent
│   ├── retrieval_agent.py      # Retrieval agent
│   ├── synthesis_agent.py      # Response synthesis agent
│   └── orchestrator.py         # Main orchestrator
├── tools/
│   ├── __init__.py
│   ├── vector_search_tool.py
│   ├── definition_lookup_tool.py
│   ├── cross_reference_tool.py
│   └── query_rewrite_tool.py
├── state/
│   ├── __init__.py
│   ├── agent_state.py          # State model
│   └── state_manager.py         # State management
└── services/
    └── ... (existing services)
```

**Action Items:**
- [ ] Create directory structure
- [ ] Plan interfaces and abstractions
- [ ] Design base classes

### 9. Cost & Performance Considerations

#### API Cost Impact
- **Current**: 1 LLM call per query (if enabled)
- **Agentic**: 3-10+ LLM calls per query (planning, retrieval decisions, synthesis)
- **Mitigation**: 
  - Use cheaper models for planning (`gpt-3.5-turbo`)
  - Cache common queries
  - Set max iterations limit

#### Latency Impact
- **Current**: ~1-2 seconds
- **Agentic**: ~5-15 seconds (multiple LLM calls)
- **Mitigation**:
  - Parallel tool execution where possible
  - Streaming responses
  - Optimize tool calls

**Action Items:**
- [ ] Set up cost monitoring
- [ ] Define performance SLAs
- [ ] Plan optimization strategies

### 10. Documentation & Monitoring

#### Before Starting
- [ ] Document current RAG pipeline performance (baseline)
- [ ] Set up logging for agent decisions
- [ ] Plan observability (what to track)
- [ ] Design debugging tools

#### What to Monitor
- Agent decision paths
- Tool usage frequency
- Query complexity vs. iterations
- Success/failure rates
- Cost per query
- Response quality metrics

**Action Items:**
- [ ] Enhance logging for agent workflows
- [ ] Create monitoring dashboard (optional)
- [ ] Set up error tracking

## Immediate Next Steps

### Step 1: Install Dependencies
```bash
pip install langchain>=0.1.0 langchain-openai>=0.0.5 langgraph>=0.0.20 langchain-community>=0.0.20
```

### Step 2: Create Tool Definitions
Start with the vector search tool wrapper to understand the pattern.

### Step 3: Build Definition Lookup
Extract and index glossary terms during ingestion.

### Step 4: Design Agent State Model
Define what information needs to be tracked.

### Step 5: Implement Basic Query Planner
Start with simple query decomposition.

## Questions to Answer Before Starting

1. **Framework Choice**: LangChain, OpenAI Functions, or LlamaIndex?
2. **Complexity Level**: Simple multi-step or full autonomous agent?
3. **Cost Budget**: How many LLM calls per query is acceptable?
4. **Performance Target**: What's acceptable latency?
5. **Backward Compatibility**: Keep old endpoint or replace?
6. **Rollout Strategy**: Feature flag or separate endpoint?

## Recommended Starting Point

1. **Week 1**: 
   - Install LangChain dependencies
   - Create tool definitions (start with vector search)
   - Build definition lookup tool
   - Test tools independently

2. **Week 2**:
   - Implement basic query planner
   - Create simple retrieval agent
   - End-to-end test with simple queries

3. **Week 3+**:
   - Add iterative refinement
   - Implement synthesis agent
   - Optimize and polish

## Resources

- [LangChain Agents](https://python.langchain.com/docs/modules/agents/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Agentic RAG Patterns](https://www.pinecone.io/learn/agentic-rag/)

## Summary

**Critical Pre-Implementation Tasks:**
1. ✅ Choose framework (recommend LangChain + LangGraph)
2. ✅ Define tool interfaces
3. ✅ Enhance data structures (cross-refs, definitions)
4. ✅ Design agent architecture
5. ✅ Plan state management
6. ✅ Set up testing strategy
7. ✅ Configure monitoring

**Estimated Preparation Time**: 2-3 days
**Estimated Implementation Time**: 3-4 weeks

Start with tool definitions and definition lookup - these are foundational and can be built independently.

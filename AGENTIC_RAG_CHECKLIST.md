# Agentic RAG Migration - Quick Checklist

## 🎯 Before You Start - Critical Tasks

### 1. Framework Decision (30 min)
- [ ] **Choose framework**: LangChain+LangGraph (recommended) vs OpenAI Functions vs LlamaIndex
- [ ] **Decision criteria**: Complexity needs, team expertise, cost constraints
- [ ] **Document decision** with rationale

### 2. Dependencies (15 min)
- [ ] **Install chosen framework**:
  ```bash
  # For LangChain approach:
  pip install langchain>=0.1.0 langchain-openai>=0.0.5 langgraph>=0.0.20 langchain-community>=0.0.20
  
  # Update requirements.txt
  ```
- [ ] **Test installation**: Verify imports work
- [ ] **Check compatibility**: Ensure works with existing dependencies

### 3. Tool System Foundation (2-3 hours)
- [ ] **Create `shared/tools/` directory**
- [ ] **Define tool interfaces**:
  - [ ] Vector search tool (wrap existing `vector_store.search()`)
  - [ ] Definition lookup tool (new - for glossary)
  - [ ] Metadata filter tool (enhance existing)
  - [ ] Cross-reference tool (new)
- [ ] **Test each tool independently**

### 4. Data Enhancements (4-6 hours)
- [ ] **Glossary Index**: Extract and index all GLO definitions during ingestion
- [ ] **Cross-Reference Extraction**: Parse rule references (e.g., "see GEN 2.1.1")
- [ ] **Rule Dependency Graph**: Build relationships between rules
- [ ] **Content Classification**: Tag chunks as rule/definition/example/etc.

### 5. Configuration Setup (30 min)
- [ ] **Add to `shared/config.py`**:
  ```python
  agent_enabled: bool = False
  agent_framework: str = "langchain"
  agent_max_iterations: int = 5
  agent_model: str = "gpt-4o"
  ```
- [ ] **Update `env.example`** with new variables
- [ ] **Document configuration options**

### 6. State Management Design (1-2 hours)
- [ ] **Create `AgentState` model** in `shared/models/schemas.py`:
  ```python
  class AgentState(BaseModel):
      query: str
      sub_queries: List[str]
      retrieved_chunks: List[DocumentChunk]
      tool_calls: List[ToolCall]
      reasoning_steps: List[str]
      confidence: float
  ```
- [ ] **Plan state transitions**
- [ ] **Design persistence** (optional, for debugging)

### 7. Testing Foundation (2 hours)
- [ ] **Create test query suite**:
  - Simple queries (1 retrieval step)
  - Medium queries (2-3 steps)
  - Complex queries (4+ steps, multiple tools)
- [ ] **Set up test directory**: `tests/agent/`
- [ ] **Define success metrics**: Accuracy, relevance, completeness

### 8. Architecture Planning (1 hour)
- [ ] **Design agent workflow**:
  ```
  Query → Planner → Retrieval Agent → Synthesis Agent → Response
  ```
- [ ] **Create directory structure**:
  ```
  shared/
  ├── agents/
  ├── tools/
  └── state/
  ```
- [ ] **Plan interfaces** between components

### 9. Cost & Performance Baseline (1 hour)
- [ ] **Measure current performance**:
  - Average response time
  - Cost per query (if LLM enabled)
  - Success rate
- [ ] **Set targets** for agentic approach
- [ ] **Plan monitoring** for agent decisions

### 10. Migration Strategy (30 min)
- [ ] **Decide rollout**: Feature flag vs separate endpoint
- [ ] **Plan backward compatibility**
- [ ] **Design A/B testing** (optional)

## 📋 Quick Start (Minimum Viable Preparation)

If you want to start quickly, do these **5 essential tasks**:

1. ✅ **Install LangChain dependencies**
2. ✅ **Create tool definitions** (start with vector search wrapper)
3. ✅ **Build definition lookup** (extract GLO terms)
4. ✅ **Design AgentState model**
5. ✅ **Set up basic test queries**

## 🚀 Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Tools working independently
- [ ] Definition lookup functional
- [ ] Basic state management

### Phase 2: Basic Agent (Week 2)
- [ ] Query planner implemented
- [ ] Retrieval agent with tools
- [ ] End-to-end flow working

### Phase 3: Advanced (Week 3+)
- [ ] Iterative refinement
- [ ] Cross-reference following
- [ ] Response synthesis

## ⚠️ Critical Decisions Needed

1. **Framework**: LangChain vs OpenAI Functions vs LlamaIndex?
2. **Complexity**: Simple multi-step or full autonomous agent?
3. **Cost**: How many LLM calls per query acceptable? (Current: 1, Agentic: 3-10+)
4. **Performance**: Acceptable latency? (Current: 1-2s, Agentic: 5-15s)
5. **Rollout**: Feature flag or separate endpoint?

## 📚 Resources

- Full guide: See `AGENTIC_RAG_PREPARATION.md`
- LangChain docs: https://python.langchain.com/docs/modules/agents/
- LangGraph: https://langchain-ai.github.io/langgraph/

## ✅ Ready to Start?

Once you've completed the checklist above, you're ready to begin implementation. Start with:
1. Tool definitions (foundational)
2. Definition lookup (independent, can be built in parallel)
3. Basic query planner (first agent component)

---

**Estimated Preparation Time**: 2-3 days
**Estimated Implementation Time**: 3-4 weeks

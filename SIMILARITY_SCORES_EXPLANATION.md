# Why We Store Similarity Scores in Vector Store Search

## The Problem We Solved

When a user asks a question in the chat, the system:
1. Converts the query to an embedding vector
2. Searches the vector store using **cosine similarity**
3. Returns the top K most similar chunks

**The original implementation had a gap**: The similarity scores were calculated but **not returned** to the caller. This meant:
- ❌ The API couldn't tell users how relevant each result was
- ❌ The frontend couldn't display confidence/relevance indicators
- ❌ No way to filter low-quality results
- ❌ No transparency into why certain chunks were returned

## What Are Similarity Scores?

**Cosine Similarity** measures how similar two vectors are:
- **Range**: -1.0 to 1.0 (typically 0.0 to 1.0 for normalized embeddings)
- **1.0** = Perfect match (identical meaning)
- **0.8-0.9** = Very relevant
- **0.6-0.7** = Moderately relevant
- **< 0.5** = Weak match, may not be relevant

### Example:
```
User Query: "What are capital requirements for banks?"

Chunk 1: "Capital requirements for banks must be maintained at 8%..."
  → Similarity: 0.92 (very relevant!)

Chunk 2: "Banks must file quarterly reports..."
  → Similarity: 0.45 (weak match, probably not relevant)
```

## Why We Need to Store and Return Scores

### 1. **User Transparency** 🎯
Users can see **why** certain results were returned:
- High score (0.8+) = "This is highly relevant to your question"
- Low score (<0.5) = "This might not be what you're looking for"

### 2. **Quality Filtering** 🔍
The frontend can:
- Hide results below a threshold (e.g., < 0.6)
- Highlight high-confidence results
- Show a "relevance meter" or progress bar

### 3. **Debugging & Improvement** 🐛
Developers can:
- Identify when search isn't working well
- Tune embedding models or chunking strategies
- See if queries are too vague or specific

### 4. **Future Features** 🚀
Enables advanced functionality:
- **Reranking**: Combine similarity with other factors
- **Confidence-based responses**: "I'm 95% confident this answers your question"
- **Adaptive retrieval**: If top result has low score, try different strategy
- **A/B testing**: Compare different embedding models

## How We Implemented It

### Step 1: Calculate Score in Vector Store
```python
# services/vector_store.py - LocalVectorStore.search()
for chunk in self.chunks:
    similarity = np.dot(query_vec, chunk_vec) / (
        np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec)
    )
    similarities.append((similarity, chunk))
```

### Step 2: Store Score in Chunk Metadata
```python
# Store in custom_metadata so it's accessible later
new_metadata = ChunkMetadata(
    ...,
    custom_metadata={
        **chunk.metadata.custom_metadata, 
        'similarity_score': float(similarity)  # ← Store here
    }
)
```

**Why `custom_metadata`?**
- `DocumentChunk` doesn't have a native `score` field
- `custom_metadata` is a flexible dictionary for arbitrary data
- Keeps the schema clean while allowing extensibility

### Step 3: Extract Score in API Endpoint
```python
# api/main.py - /api/chat endpoint
score = chunk.metadata.custom_metadata.get('similarity_score', 0.0)
reference = ReferenceResponse(
    ...,
    score=score  # ← Pass to frontend
)
```

### Step 4: Display in Frontend
```typescript
// Frontend can show score as:
- Percentage: "85% relevant"
- Badge: "High confidence"
- Visual indicator: Progress bar
- Sort by relevance
```

## Data Flow Diagram

```
User Query: "What are capital requirements?"
    ↓
[Embedding Service] → Query Vector [0.1, 0.3, -0.2, ...]
    ↓
[Vector Store Search]
    ├─ Calculate cosine similarity for each chunk
    ├─ Chunk 1: similarity = 0.92
    ├─ Chunk 2: similarity = 0.78
    └─ Chunk 3: similarity = 0.65
    ↓
[Store scores in chunk.metadata.custom_metadata]
    ├─ Chunk 1: custom_metadata['similarity_score'] = 0.92
    ├─ Chunk 2: custom_metadata['similarity_score'] = 0.78
    └─ Chunk 3: custom_metadata['similarity_score'] = 0.65
    ↓
[API Endpoint] → Extract scores → ReferenceResponse
    ├─ Reference 1: score = 0.92
    ├─ Reference 2: score = 0.78
    └─ Reference 3: score = 0.65
    ↓
[Frontend] → Display with relevance indicators
```

## Real-World Example

### Without Scores:
```
User: "What are capital requirements?"
Response: 
  - Result 1: "Capital requirements..."
  - Result 2: "Banks must maintain..."
  - Result 3: "Quarterly reports..."
```
❓ **User can't tell which result is most relevant**

### With Scores:
```
User: "What are capital requirements?"
Response:
  - Result 1: "Capital requirements..." [92% relevant] ⭐⭐⭐
  - Result 2: "Banks must maintain..." [78% relevant] ⭐⭐
  - Result 3: "Quarterly reports..." [45% relevant] ⭐
```
✅ **User immediately sees Result 1 is the best match**

## Technical Benefits

1. **Non-Breaking**: Uses existing `custom_metadata` field
2. **Extensible**: Can add more search metrics later (e.g., `bm25_score`, `hybrid_score`)
3. **Type-Safe**: Pydantic validates the score is a float
4. **Backward Compatible**: Defaults to 0.0 if score missing

## Future Enhancements Enabled

With similarity scores available, we can now implement:

1. **Hybrid Search**: Combine vector similarity + keyword matching
   ```python
   final_score = 0.7 * similarity_score + 0.3 * bm25_score
   ```

2. **Reranking**: Use scores to reorder results
   ```python
   if similarity_score > 0.8:
       boost = 1.2  # Boost high-confidence results
   ```

3. **Confidence Thresholds**: Filter low-quality results
   ```python
   if score < 0.6:
       return "I'm not confident about these results..."
   ```

4. **Analytics**: Track search quality over time
   ```python
   avg_score = sum(scores) / len(scores)
   if avg_score < 0.5:
       alert("Search quality degraded")
   ```

## Summary

**We store similarity scores because:**
- ✅ Provides transparency to users
- ✅ Enables quality filtering and confidence indicators
- ✅ Helps debug and improve search quality
- ✅ Enables future advanced features
- ✅ Minimal code change, maximum value

**Without scores**, the system is a "black box" - users don't know why certain results were returned. **With scores**, the system is transparent, trustworthy, and provides actionable feedback.


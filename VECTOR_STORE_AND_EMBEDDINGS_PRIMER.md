# Vector Store and Embeddings Primer

## Table of Contents
1. [Local Vector Store](#local-vector-store)
2. [Sentence Transformers](#sentence-transformers)
3. [How They Work Together](#how-they-work-together)
4. [Technical Details](#technical-details)
5. [Performance Considerations](#performance-considerations)

---

## Local Vector Store

### Overview

The **Local Vector Store** is an in-memory vector database implementation designed for development, testing, and small-scale deployments. It stores document chunks and their embeddings in Python memory, enabling fast semantic search without external dependencies.

### Architecture

```
┌─────────────────────────────────────┐
│      LocalVectorStore               │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  chunks: List[DocumentChunk]  │  │
│  │  - content: str               │  │
│  │  - metadata: ChunkMetadata    │  │
│  │  - embedding: List[float]     │  │
│  └──────────────────────────────┘  │
│                                     │
│  Operations:                        │
│  - upsert_chunks()                  │
│  - search()                         │
│  - delete_by_file()                 │
└─────────────────────────────────────┘
```

### Key Characteristics

**Storage:**
- **Type**: In-memory Python list (`List[DocumentChunk]`)
- **Persistence**: None (data lost on restart)
- **Location**: Application memory (RAM)
- **Capacity**: Limited by available RAM

**Data Structure:**
```python
DocumentChunk:
  - content: str              # The actual text
  - metadata: ChunkMetadata   # Rich metadata (module, rule number, etc.)
  - embedding: List[float]    # Vector representation (384 dimensions for all-MiniLM-L6-v2)
```

### Operations

#### 1. Upsert (Insert/Update)

```python
async def upsert_chunks(self, chunks: List[DocumentChunk]) -> bool:
    # Remove existing chunks for same file (update behavior)
    if chunks:
        file_name = chunks[0].metadata.file_name
        self.chunks = [c for c in self.chunks if c.metadata.file_name != file_name]
    
    # Add new chunks
    self.chunks.extend(chunks)
    return True
```

**Behavior:**
- **Upsert** = Update if exists, Insert if new
- If chunks with same `file_name` exist, they're removed first
- New chunks are appended to the list
- This ensures re-ingestion updates existing data

**Example:**
```python
# First ingestion
await store.upsert_chunks([chunk1, chunk2, chunk3])
# Store now has 3 chunks

# Re-ingest same file (updated content)
await store.upsert_chunks([chunk1_updated, chunk2_updated])
# Store now has 2 chunks (old 3 removed, new 2 added)
```

#### 2. Search

```python
async def search(self, query_embedding: List[float], top_k: int = 5) -> List[DocumentChunk]:
    # Calculate cosine similarity for each chunk
    similarities = []
    query_vec = np.array(query_embedding)
    
    for chunk in self.chunks:
        if chunk.embedding:
            chunk_vec = np.array(chunk.embedding)
            # Cosine similarity formula
            similarity = np.dot(query_vec, chunk_vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec)
            )
            similarities.append((similarity, chunk))
    
    # Sort by similarity (highest first)
    similarities.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in similarities[:top_k]]
```

**How It Works:**
1. **Input**: Query embedding (vector representation of search query)
2. **Process**: Calculate cosine similarity between query and all stored chunks
3. **Output**: Top-k most similar chunks, sorted by similarity score

**Cosine Similarity:**
- Measures angle between two vectors
- Range: -1 to 1 (1 = identical, 0 = orthogonal, -1 = opposite)
- Formula: `cos(θ) = (A · B) / (||A|| × ||B||)`
- Higher score = more similar content

**Example:**
```python
# Query: "What is Accepting Deposits?"
query_embedding = [0.1, 0.2, 0.3, ...]  # 384 dimensions

# Search
results = await store.search(query_embedding, top_k=5)

# Results (sorted by similarity):
# 1. [0.95] "Accepting Deposits: Has the meaning given in GEN section 2.4."
# 2. [0.82] "Account Information Service: Has the meaning given in..."
# 3. [0.75] "Accounting Records: Means records and underlying documents..."
# ...
```

#### 3. Delete

```python
async def delete_by_file(self, file_name: str) -> bool:
    initial_count = len(self.chunks)
    self.chunks = [c for c in self.chunks if c.metadata.file_name != file_name]
    deleted = initial_count - len(self.chunks)
    return True
```

**Behavior:**
- Removes all chunks with matching `file_name`
- Returns count of deleted chunks
- Useful for re-indexing or removing outdated content

### Advantages

✅ **No External Dependencies**: Works without databases or cloud services
✅ **Fast for Small Datasets**: O(n) search, very fast for < 10,000 chunks
✅ **Simple**: Easy to understand and debug
✅ **Zero Configuration**: No setup required
✅ **Perfect for Development**: Ideal for testing and prototyping

### Limitations

❌ **No Persistence**: Data lost on restart
❌ **Memory Limited**: All data must fit in RAM
❌ **Scalability**: Performance degrades with large datasets (> 100K chunks)
❌ **No Advanced Features**: No filtering, faceting, or complex queries
❌ **Single Process**: Not suitable for distributed systems

### When to Use

**Good For:**
- Development and testing
- Small datasets (< 10,000 chunks)
- Prototyping and demos
- Local development environments
- Quick experiments

**Not Good For:**
- Production with large datasets
- Systems requiring persistence
- Multi-user or distributed systems
- High-performance requirements

---

## Sentence Transformers

### Overview

**Sentence Transformers** is a Python framework for creating dense vector representations (embeddings) of text. It's based on transformer models (like BERT) but optimized for semantic similarity tasks.

### What Are Embeddings?

**Embeddings** are numerical representations of text that capture semantic meaning:

```
Text: "Accepting Deposits"
      ↓
Embedding: [0.123, -0.456, 0.789, ..., 0.234]  (384 numbers)
      ↓
Vector Space: Similar texts are close together
```

**Key Properties:**
- **Fixed Size**: Same length regardless of input text length
- **Semantic**: Similar meanings → similar vectors
- **Dense**: Every dimension carries information (unlike sparse one-hot encoding)

### Model: `all-MiniLM-L6-v2`

**Current Configuration:**
```python
sentence_transformer_model: str = "all-MiniLM-L6-v2"
```

**Model Details:**
- **Architecture**: MiniLM (lightweight BERT variant)
- **Dimensions**: 384 (output vector size)
- **Size**: ~80 MB (small, fast)
- **Speed**: ~10,000 sentences/second on CPU
- **Quality**: Good balance of speed and accuracy

**Model Card:**
- **Base Model**: Microsoft's MiniLM
- **Training**: Fine-tuned on 1B+ sentence pairs
- **Use Case**: General-purpose semantic similarity
- **Languages**: Primarily English (works well for technical/legal English)

### How It Works

#### 1. Model Initialization

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
# Downloads model (~80 MB) on first use
# Loads into memory (~200-300 MB)
```

**What Happens:**
1. Downloads model from Hugging Face (if not cached)
2. Loads transformer architecture and weights
3. Prepares tokenizer for text processing
4. Model ready for encoding

#### 2. Text Encoding

```python
# Single text
embedding = model.encode("Accepting Deposits")
# Returns: numpy array of shape (384,)

# Batch encoding (faster)
texts = ["Accepting Deposits", "Account Information Service", ...]
embeddings = model.encode(texts)
# Returns: numpy array of shape (n, 384)
```

**Process:**
1. **Tokenization**: Text → tokens (subwords)
   ```
   "Accepting Deposits" → ["accept", "##ing", "deposit", "##s"]
   ```

2. **Embedding**: Tokens → vectors
   ```
   Tokens → [768-dim vectors] (internal representation)
   ```

3. **Pooling**: Token vectors → sentence vector
   ```
   Mean pooling: Average all token vectors → 384-dim vector
   ```

4. **Normalization**: Optional L2 normalization
   ```
   Vector / ||Vector|| (unit length)
   ```

#### 3. Implementation in Code

```python
class SentenceTransformerEmbeddingService(EmbeddingService):
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    async def embed_text(self, text: str) -> List[float]:
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()  # Convert to Python list
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
```

**Key Parameters:**
- `convert_to_numpy=True`: Returns NumPy array (faster)
- Batch encoding is more efficient (parallel processing)

### Embedding Characteristics

**Dimensions: 384**
- Each text → 384 floating-point numbers
- Fixed size regardless of input length
- Example: "Hi" and "This is a very long sentence..." both → 384 numbers

**Value Range:**
- Typically: -1 to 1 (after normalization)
- Depends on model and normalization settings

**Semantic Properties:**
- Similar texts → similar vectors (high cosine similarity)
- Different texts → different vectors (low cosine similarity)
- Preserves semantic relationships

**Example:**
```python
text1 = "Accepting Deposits"
text2 = "Taking customer money"
text3 = "Stock market trading"

emb1 = model.encode(text1)
emb2 = model.encode(text2)
emb3 = model.encode(text3)

# Similarity scores:
cosine_similarity(emb1, emb2) ≈ 0.85  # High (similar meaning)
cosine_similarity(emb1, emb3) ≈ 0.15  # Low (different meaning)
```

### Advantages

✅ **Local Processing**: No API calls, works offline
✅ **Fast**: ~10K sentences/second on CPU
✅ **Free**: No usage costs
✅ **Privacy**: Data never leaves your machine
✅ **Consistent**: Same input → same output
✅ **Batch Processing**: Efficient for multiple texts

### Limitations

❌ **Model Size**: ~80 MB download, ~200-300 MB RAM
❌ **CPU Intensive**: Can be slow on large batches
❌ **Language**: Optimized for English
❌ **Domain**: General-purpose (may not be optimal for legal/technical jargon)
❌ **No Fine-tuning**: Uses pre-trained model (can't customize easily)

### Alternative Models

**Available Models (can change in config):**

1. **all-MiniLM-L6-v2** (Current) ⭐
   - 384 dims, 80 MB, Fast, Good quality
   - Best for: General use, speed priority

2. **all-mpnet-base-v2**
   - 768 dims, 420 MB, Slower, Better quality
   - Best for: Quality priority, larger datasets

3. **all-MiniLM-L12-v2**
   - 384 dims, 120 MB, Medium speed, Better than L6
   - Best for: Balance of speed and quality

4. **paraphrase-multilingual-MiniLM-L12-v2**
   - 384 dims, 420 MB, Multilingual
   - Best for: Multiple languages

**To Change Model:**
```bash
# In .env file
SENTENCE_TRANSFORMER_MODEL=all-mpnet-base-v2
```

---

## How They Work Together

### Complete Flow

```
1. PDF Ingestion
   ↓
2. Text Extraction & Chunking
   ↓
3. Embedding Generation (Sentence Transformers)
   Text → [384-dim vector]
   ↓
4. Storage (Local Vector Store)
   Chunk + Embedding → Memory
   ↓
5. Search Query
   Query → Embedding → Cosine Similarity → Results
```

### Example: Full Pipeline

```python
# 1. Extract and chunk PDF
sections = extractor.extract_text_with_structure("rulebook.pdf")
chunks = chunker.chunk_sections(sections, metadata)

# 2. Generate embeddings
embedding_service = SentenceTransformerEmbeddingService()
texts = [chunk.content for chunk in chunks]
embeddings = await embedding_service.embed_batch(texts)

# 3. Add embeddings to chunks
for chunk, embedding in zip(chunks, embeddings):
    chunk.embedding = embedding

# 4. Store in vector store
vector_store = LocalVectorStore()
await vector_store.upsert_chunks(chunks)

# 5. Search
query = "What is Accepting Deposits?"
query_embedding = await embedding_service.embed_text(query)
results = await vector_store.search(query_embedding, top_k=5)

# 6. Display results
for chunk in results:
    print(f"{chunk.content[:100]}...")
```

### Memory Usage Example

**For 661 chunks (Glossary PDF):**

```
Chunks: 661
Embedding size: 384 dimensions × 4 bytes = 1,536 bytes per chunk
Total embeddings: 661 × 1,536 = ~1 MB
Content: ~661 × 100 bytes = ~66 KB
Metadata: ~661 × 500 bytes = ~330 KB
Total: ~1.4 MB in memory
```

**For 10,000 chunks:**
- Embeddings: ~15 MB
- Content: ~1 MB
- Metadata: ~5 MB
- **Total: ~21 MB**

---

## Technical Details

### Cosine Similarity Calculation

```python
import numpy as np

def cosine_similarity(vec1, vec2):
    """
    Calculate cosine similarity between two vectors.
    
    Formula: cos(θ) = (A · B) / (||A|| × ||B||)
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    # Dot product
    dot_product = np.dot(vec1, vec2)
    
    # Magnitudes (L2 norms)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    # Cosine similarity
    similarity = dot_product / (norm1 * norm2)
    
    return similarity
```

**Why Cosine Similarity?**
- **Scale Invariant**: Works regardless of vector magnitude
- **Angle-Based**: Measures semantic direction, not magnitude
- **Normalized**: Results in -1 to 1 range
- **Efficient**: Fast to compute

### Search Complexity

**Time Complexity:**
- **Upsert**: O(1) per chunk (append to list)
- **Search**: O(n) where n = number of chunks
  - Must compare query with every chunk
  - For 10,000 chunks: ~10,000 similarity calculations
  - Typically < 100ms on modern CPU

**Space Complexity:**
- **Storage**: O(n × d) where n = chunks, d = embedding dimensions
- **Temporary**: O(n) for similarity calculations during search

### Performance Benchmarks

**Embedding Generation (all-MiniLM-L6-v2):**
- Single text: ~1-2 ms
- Batch of 100: ~50-100 ms
- Batch of 1000: ~500-1000 ms

**Vector Store Search:**
- 100 chunks: < 1 ms
- 1,000 chunks: ~5-10 ms
- 10,000 chunks: ~50-100 ms
- 100,000 chunks: ~500-1000 ms

**Memory:**
- Model: ~200-300 MB (loaded once)
- Per chunk: ~1.5 KB (embedding + metadata)
- 10,000 chunks: ~15 MB

---

## Performance Considerations

### Optimization Tips

1. **Batch Embedding Generation**
   ```python
   # Good: Batch processing
   embeddings = await service.embed_batch(texts)
   
   # Bad: One at a time
   for text in texts:
       embedding = await service.embed_text(text)
   ```

2. **Reuse Model Instance**
   ```python
   # Good: Single instance
   service = SentenceTransformerEmbeddingService()
   # Reuse for multiple operations
   
   # Bad: Create new instance each time
   # (Model loading is expensive)
   ```

3. **Limit Search Scope**
   ```python
   # Use top_k appropriately
   results = await store.search(query_embedding, top_k=5)  # Good
   results = await store.search(query_embedding, top_k=1000)  # Unnecessary
   ```

4. **Consider GPU for Large Batches**
   ```python
   # If available, GPU speeds up embedding generation
   model = SentenceTransformer('all-MiniLM-L6-v2', device='cuda')
   ```

### When to Upgrade

**Consider upgrading from Local Vector Store when:**
- Dataset > 50,000 chunks
- Need persistence across restarts
- Require advanced filtering
- Need distributed access
- Production deployment

**Consider upgrading embedding model when:**
- Need better semantic understanding
- Working with specialized domain (legal, medical)
- Quality more important than speed
- Have GPU resources

---

## Summary

**Local Vector Store:**
- Simple in-memory storage
- Fast for small-medium datasets
- Perfect for development
- No persistence

**Sentence Transformers:**
- Local embedding generation
- Fast and free
- Good semantic understanding
- 384-dimensional vectors

**Together:**
- Complete RAG pipeline
- No external dependencies
- Fast and efficient
- Ideal for development and testing

---

## References

- [Sentence Transformers Documentation](https://www.sbert.net/)
- [Hugging Face Model Hub](https://huggingface.co/sentence-transformers)
- [all-MiniLM-L6-v2 Model Card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- [Cosine Similarity Explained](https://en.wikipedia.org/wiki/Cosine_similarity)


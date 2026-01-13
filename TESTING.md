# Testing Guide

This guide explains how to test the DFSA RAG ingestion pipeline at different stages.

## Quick Start

### 1. Test PDF Extraction Only

Extract text from a PDF and see the sections:

```bash
python test_pipeline.py downloads/DFSA1547_15954_VER260126.pdf --step extract
```

To see all sections (not just first 10):
```bash
python test_pipeline.py downloads/DFSA1547_15954_VER260126.pdf --step extract --show-all
```

### 2. Test Extraction + Chunking

Test both extraction and chunking:

```bash
python test_pipeline.py downloads/DFSA1547_15954_VER260126.pdf --step chunk
```

### 3. Test Full Pipeline (Without Embeddings)

Test extraction and chunking without requiring embeddings/vector store:

```bash
python test_pipeline.py downloads/DFSA1547_15954_VER260126.pdf --step pipeline --skip-embeddings
```

### 4. Test Full Pipeline (With Embeddings)

Test the complete pipeline including embeddings and vector store:

```bash
python test_pipeline.py downloads/DFSA1547_15954_VER260126.pdf --step pipeline
```

**Note:** This requires:
- Embedding provider configured (OpenAI, Azure OpenAI, or Sentence Transformers)
- Vector store configured (Azure AI Search, OpenAI, or Local)

### 5. Save Results to Files

Save extraction and chunking results to JSON files:

```bash
python test_pipeline.py downloads/DFSA1547_15954_VER260126.pdf --save
```

Results will be saved to `test_output/` directory:
- `extracted_sections.json` - All extracted sections
- `chunks.json` - All chunks with metadata

## Command Line Options

```
positional arguments:
  pdf_path              Path to the PDF file to test

optional arguments:
  --step {extract,chunk,pipeline,all}
                        Which step to test (default: all)
  --show-all            Show all sections/chunks (default: show first 10)
  --max-items N         Maximum items to show when not using --show-all (default: 10)
  --skip-embeddings     Skip embeddings and vector store in pipeline test
  --save                Save results to JSON files in test_output/ directory
```

## Examples

### Example 1: Quick Test (First 5 Sections)
```bash
python test_pipeline.py downloads/DFSA1547_15954_VER260126.pdf --step extract --max-items 5
```

### Example 2: Full Inspection
```bash
python test_pipeline.py downloads/DFSA1547_15954_VER260126.pdf --show-all --save
```

### Example 3: Test All PDFs
```bash
for pdf in downloads/*.pdf; do
    echo "Testing $pdf"
    python test_pipeline.py "$pdf" --step chunk --max-items 3
done
```

## Understanding the Output

### Extraction Output

For each section, you'll see:
- **Level**: Hierarchy level (0=module, 1=chapter, 2=section, 3=subsection)
- **Page**: Page number where section appears
- **Rule**: Rule number (e.g., "GEN 2.1.1") if detected
- **Title**: Section title
- **Hierarchy**: Parent sections in hierarchy
- **Content**: Text content (preview or full)

### Chunking Output

For each chunk, you'll see:
- **Chunk #**: Chunk number and total chunks
- **Page**: Page number
- **Index**: Chunk index
- **Rule**: Rule number if applicable
- **Module**: Module code (e.g., "GEN")
- **Section**: Section number
- **Hierarchy**: Full hierarchy path
- **Content Type**: Type (rule, appendix, glossary, etc.)
- **Content**: Text content (preview or full)
- **Embedding**: Dimensions if embeddings were generated

## Testing Without Full Configuration

If you haven't configured embeddings or vector store yet, you can still test:

1. **Extraction only**: Works without any configuration
2. **Chunking**: Works without any configuration
3. **Full pipeline without embeddings**: Use `--skip-embeddings` flag

## Troubleshooting

### Import Errors
Make sure your virtual environment is activated:
```bash
source venv/bin/activate
```

### PDF Library Errors
Check your `.env` file has the correct `PDF_LIBRARY` setting:
```env
PDF_LIBRARY=pdfplumber  # or pymupdf
```

### Configuration Errors
If testing full pipeline, ensure your `.env` file has the required settings for your chosen embedding provider and vector store.

## Next Steps

After testing:
1. Review the extracted sections to verify hierarchy detection
2. Check chunks to ensure proper section boundaries
3. Adjust chunking parameters in `.env` if needed:
   - `CHUNK_SIZE`: Size of chunks
   - `CHUNK_OVERLAP`: Overlap between chunks
   - `RESPECT_SENTENCE_BOUNDARIES`: Whether to respect sentence boundaries
   - `RESPECT_SECTION_BOUNDARIES`: Whether to respect section boundaries


# PDF Metadata Configuration Guide

## Overview

The system uses a JSON configuration file (`config/pdf_metadata.json`) to manage PDF metadata, aliases, and chunking strategies. Only PDFs listed in this configuration file can be processed.

## Configuration File Structure

### Location
`config/pdf_metadata.json`

### Structure

```json
{
  "pdfs": [
    {
      "file_name": "exact-filename.pdf",
      "alias": "Human Readable Name",
      "module_code": "MKT",
      "module_name": "Module Full Name",
      "description": "Description of the module",
      "chunking_strategy": "section_aware",
      "chunk_size": 1000,
      "chunk_overlap": 200,
      "respect_sentences": true,
      "respect_sections": true,
      "page_filtering": {
        "skip_cover_pages": true,
        "skip_toc": true,
        "skip_disclaimers": true,
        "remove_headers_footers": true,
        "toc_page_range": [2, 2],
        "cover_page_range": [1, 1]
      },
      "custom_metadata": {
        "category": "core",
        "priority": "high"
      }
    }
  ],
  "default_chunking": { ... },
  "default_page_filtering": { ... },
  "module_strategies": { ... }
}
```

## Configuration Fields

### Required Fields

- **file_name**: Exact filename of the PDF (must match exactly)
- **alias**: Human-readable name for the PDF

### Optional Fields

- **module_code**: Module code (e.g., "GEN", "GLO", "MKT", "AML")
- **module_name**: Full module name
- **description**: Description of the module
- **chunking_strategy**: Strategy to use ("section_aware" or "glossary")
- **chunk_size**: Maximum chunk size in characters
- **chunk_overlap**: Overlap between chunks in characters
- **respect_sentences**: Whether to respect sentence boundaries
- **respect_sections**: Whether to respect section boundaries

### Glossary-Specific Fields

For glossary files (GLO module), use:

```json
{
  "chunking_strategy": "glossary",
  "chunk_size": 500,
  "chunk_overlap": 0,
  "glossary_settings": {
    "keep_definitions_intact": true,
    "definition_pattern": "^([A-Z][A-Za-z\\s]+(?:\\s+[A-Z][A-Za-z\\s]+)*)\\s+(Has the meaning|Means|Includes)",
    "term_extraction_pattern": "^([A-Z][A-Za-z\\s]+(?:\\s+[A-Z][A-Za-z\\s]+)*)",
    "max_definition_length": 2000
  }
}
```

### Page Filtering Configuration

```json
{
  "page_filtering": {
    "skip_cover_pages": true,
    "skip_toc": true,
    "skip_disclaimers": true,
    "remove_headers_footers": true,
    "toc_page_range": [2, 2],  // [start_page, end_page] or null for auto-detect
    "cover_page_range": [1, 1]  // [start_page, end_page]
  }
}
```

## Chunking Strategies

### 1. Section-Aware (Default)
- Respects document hierarchy
- Keeps sections intact when possible
- Uses configurable chunk size and overlap
- Best for: Regular rulebook modules (GEN, MKT, AML, etc.)

### 2. Glossary
- Keeps each definition intact
- Smaller chunks (typically 500 chars)
- No overlap (definitions are self-contained)
- Extracts term and definition separately
- Best for: Glossary module (GLO)

## Adding a New PDF

1. Add entry to `pdfs` array in `config/pdf_metadata.json`
2. Use exact filename (case-sensitive)
3. Specify appropriate chunking strategy
4. Configure page filtering if needed
5. Restart the service to load new configuration

## Example Configurations

### Markets Rules Module
```json
{
  "file_name": "DFSA1547_15954_VER260126.pdf",
  "alias": "Markets Rules",
  "module_code": "MKT",
  "module_name": "Markets Rules",
  "chunking_strategy": "section_aware",
  "chunk_size": 1000,
  "chunk_overlap": 200
}
```

### Glossary Module
```json
{
  "file_name": "DFSA1547_5717_VER630126.pdf",
  "alias": "Glossary",
  "module_code": "GLO",
  "module_name": "Glossary Module",
  "chunking_strategy": "glossary",
  "chunk_size": 500,
  "chunk_overlap": 0
}
```

## Validation

- The system validates that PDFs are in the config before processing
- If a PDF is not configured, ingestion will fail with a clear error message
- Configuration is loaded on service startup and can be reloaded

## Troubleshooting

### PDF Not Found Error
- Check exact filename match (case-sensitive)
- Verify file is listed in `pdfs` array
- Check JSON syntax is valid

### Page Filtering Issues
- Adjust `toc_page_range` if TOC pages are not being skipped
- Adjust `cover_page_range` if cover pages are not being skipped
- Set ranges to `null` for auto-detection

### Glossary Chunking Issues
- Verify `definition_pattern` matches your glossary format
- Adjust `max_definition_length` if definitions are being truncated
- Check that `chunking_strategy` is set to "glossary"


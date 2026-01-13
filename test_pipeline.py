#!/usr/bin/env python3
"""
Test script for the DFSA RAG ingestion pipeline.
Allows step-by-step testing of PDF extraction, chunking, and full pipeline.
"""
import sys
import json
from pathlib import Path
from typing import Optional, List
from config import get_settings
from utils.pdf_extractor import DFSAExtractor
from utils.metadata_loader import MetadataLoader
from utils.chunking_strategy_factory import ChunkingStrategyFactory
from utils.logger import logger

settings = get_settings()
metadata_loader = MetadataLoader()


def print_section(section, max_content_length=200):
    """Print a PDF section in a readable format."""
    print(f"\n{'='*80}")
    print(f"Level: {section.level} | Page: {section.page_number}")
    if section.rule_number:
        print(f"Rule: {section.rule_number}")
    print(f"Title: {section.title}")
    print(f"Hierarchy: {' > '.join([h[1] for h in section.parent_path]) if section.parent_path else 'Root'}")
    content_preview = section.content[:max_content_length]
    if len(section.content) > max_content_length:
        content_preview += "..."
    print(f"Content ({len(section.content)} chars): {content_preview}")
    print(f"{'='*80}")


def print_chunk(chunk, chunk_num, max_content_length=200):
    """Print a chunk in a readable format."""
    print(f"\n{'='*80}")
    print(f"Chunk #{chunk_num} of {chunk.metadata.total_chunks}")
    print(f"Page: {chunk.metadata.page_number} | Index: {chunk.metadata.chunk_index}")
    if chunk.metadata.alias:
        print(f"Alias: {chunk.metadata.alias}")
    if chunk.metadata.rule_number:
        print(f"Rule: {chunk.metadata.rule_number}")
    if chunk.metadata.module_code:
        print(f"Module: {chunk.metadata.module_code}")
    if chunk.metadata.module_name:
        print(f"Module Name: {chunk.metadata.module_name}")
    if chunk.metadata.section_number:
        print(f"Section: {chunk.metadata.section_number}")
    if chunk.metadata.term:
        print(f"Term: {chunk.metadata.term}")
    print(f"Hierarchy: {chunk.metadata.hierarchy_path}")
    print(f"Content Type: {chunk.metadata.content_type}")
    content_preview = chunk.content[:max_content_length]
    if len(chunk.content) > max_content_length:
        content_preview += "..."
    print(f"Content ({len(chunk.content)} chars): {content_preview}")
    if chunk.embedding:
        print(f"Embedding: {len(chunk.embedding)} dimensions")
    print(f"{'='*80}")


def test_pdf_extraction(pdf_path: str, show_all: bool = False, max_sections: int = 10):
    """Test PDF extraction and display results."""
    print("\n" + "="*80)
    print("STEP 1: PDF EXTRACTION TEST")
    print("="*80)
    
    try:
        # Check if PDF is in config
        file_name = Path(pdf_path).name
        if not metadata_loader.has_metadata(file_name):
            print(f"\n❌ Error: PDF '{file_name}' is not configured in pdf_metadata.json")
            print("Only PDFs listed in the configuration file can be processed.")
            print(f"\nAvailable PDFs in config:")
            for pdf_name in metadata_loader.get_all_metadata().keys():
                print(f"  - {pdf_name}")
            return None, None
        
        # Load metadata and config
        config_metadata = metadata_loader.get_metadata(file_name)
        page_filter_config = metadata_loader.get_page_filtering_config(file_name)
        
        print(f"\n📄 PDF Configuration:")
        print(f"  Alias: {config_metadata.get('alias', 'N/A')}")
        print(f"  Module: {config_metadata.get('module_code', 'N/A')} - {config_metadata.get('module_name', 'N/A')}")
        print(f"  Description: {config_metadata.get('description', 'N/A')}")
        
        # Create extractor with page filtering
        extractor = DFSAExtractor(page_filter_config=page_filter_config)
        print(f"\nUsing PDF library: {extractor.pdf_library}")
        print(f"Extracting from: {pdf_path}")
        
        if page_filter_config.get("skip_cover_pages") or page_filter_config.get("skip_toc"):
            print(f"\nPage filtering enabled:")
            if page_filter_config.get("skip_cover_pages"):
                cover_range = page_filter_config.get("cover_page_range", [])
                print(f"  - Skipping cover pages: {cover_range}")
            if page_filter_config.get("skip_toc"):
                toc_range = page_filter_config.get("toc_page_range")
                if toc_range:
                    print(f"  - Skipping TOC pages: {toc_range}")
                else:
                    print(f"  - Skipping TOC pages: (auto-detect)")
            if page_filter_config.get("remove_headers_footers"):
                print(f"  - Removing headers/footers")
        
        sections = extractor.extract_text_with_structure(pdf_path)
        file_metadata = extractor.extract_file_metadata(pdf_path, config_metadata)
        
        print(f"\n✅ Extraction successful!")
        print(f"Total sections extracted: {len(sections)}")
        print(f"Total pages: {max(s.page_number for s in sections) if sections else 0}")
        print(f"\nFile metadata:")
        for key, value in file_metadata.items():
            if key not in ["file_path"]:  # Skip internal paths
                print(f"  {key}: {value}")
        
        if show_all:
            print(f"\n{'='*80}")
            print("ALL SECTIONS:")
            print(f"{'='*80}")
            for i, section in enumerate(sections, 1):
                print_section(section)
        else:
            print(f"\n{'='*80}")
            print(f"FIRST {min(max_sections, len(sections))} SECTIONS (use --show-all to see all):")
            print(f"{'='*80}")
            for i, section in enumerate(sections[:max_sections], 1):
                print(f"\nSection {i}/{len(sections)}:")
                print_section(section)
        
        return sections, file_metadata
        
    except Exception as e:
        print(f"\n❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_chunking(sections, file_metadata, show_all: bool = False, max_chunks: int = 10):
    """Test chunking and display results."""
    print("\n" + "="*80)
    print("STEP 2: CHUNKING TEST")
    print("="*80)
    
    if not sections:
        print("❌ No sections to chunk. Run extraction first.")
        return None
    
    try:
        # Get chunking config from metadata
        file_name = file_metadata.get("file_name")
        if not file_name:
            print("❌ Error: File name not found in metadata")
            return None
        
        chunking_config = metadata_loader.get_chunking_config(file_name)
        strategy = chunking_config.get("chunking_strategy", "section_aware")
        
        print(f"\nChunking strategy: {strategy}")
        print(f"Chunking configuration:")
        print(f"  Chunk size: {chunking_config.get('chunk_size', 1000)}")
        print(f"  Chunk overlap: {chunking_config.get('chunk_overlap', 200)}")
        print(f"  Respect sentences: {chunking_config.get('respect_sentences', True)}")
        print(f"  Respect sections: {chunking_config.get('respect_sections', True)}")
        
        if strategy == "glossary":
            glossary_settings = chunking_config.get("glossary_settings", {})
            print(f"\nGlossary-specific settings:")
            print(f"  Keep definitions intact: {glossary_settings.get('keep_definitions_intact', True)}")
            print(f"  Max definition length: {glossary_settings.get('max_definition_length', 2000)}")
        
        # Create appropriate chunker
        chunker = ChunkingStrategyFactory.create_chunker(chunking_config)
        
        chunks = chunker.chunk_sections(sections, file_metadata)
        
        print(f"\n✅ Chunking successful!")
        print(f"Total chunks created: {len(chunks)}")
        
        # Statistics
        total_chars = sum(len(c.content) for c in chunks)
        avg_chunk_size = total_chars / len(chunks) if chunks else 0
        print(f"Total characters: {total_chars:,}")
        print(f"Average chunk size: {avg_chunk_size:.0f} characters")
        
        # Group by content type
        content_types = {}
        for chunk in chunks:
            ct = chunk.metadata.content_type or "unknown"
            content_types[ct] = content_types.get(ct, 0) + 1
        
        print(f"\nChunks by content type:")
        for ct, count in content_types.items():
            print(f"  {ct}: {count}")
        
        # Show glossary-specific stats if applicable
        if strategy == "glossary":
            terms_count = sum(1 for c in chunks if c.metadata.term)
            print(f"\nGlossary statistics:")
            print(f"  Terms extracted: {terms_count}")
            print(f"  Definitions: {len(chunks)}")
        
        if show_all:
            print(f"\n{'='*80}")
            print("ALL CHUNKS:")
            print(f"{'='*80}")
            for i, chunk in enumerate(chunks, 1):
                print_chunk(chunk, i)
        else:
            print(f"\n{'='*80}")
            print(f"FIRST {min(max_chunks, len(chunks))} CHUNKS (use --show-all to see all):")
            print(f"{'='*80}")
            for i, chunk in enumerate(chunks[:max_chunks], 1):
                print_chunk(chunk, i, max_content_length=300)
        
        return chunks
        
    except Exception as e:
        print(f"\n❌ Chunking failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_full_pipeline(pdf_path: str, skip_embeddings: bool = False):
    """Test the full ingestion pipeline."""
    print("\n" + "="*80)
    print("STEP 3: FULL PIPELINE TEST")
    print("="*80)
    
    try:
        from services.ingestion_service import IngestionService
        import asyncio
        
        service = IngestionService()
        
        if skip_embeddings:
            print("\n⚠️  Skipping embeddings and vector store (testing extraction + chunking only)")
            # Manual pipeline without embeddings using metadata config
            file_name = Path(pdf_path).name
            if not metadata_loader.has_metadata(file_name):
                print(f"❌ Error: PDF '{file_name}' is not configured in pdf_metadata.json")
                return None
            
            config_metadata = metadata_loader.get_metadata(file_name)
            chunking_config = metadata_loader.get_chunking_config(file_name)
            page_filter_config = metadata_loader.get_page_filtering_config(file_name)
            
            extractor = DFSAExtractor(page_filter_config=page_filter_config)
            chunker = ChunkingStrategyFactory.create_chunker(chunking_config)
            
            sections = extractor.extract_text_with_structure(pdf_path)
            file_metadata = extractor.extract_file_metadata(pdf_path, config_metadata)
            chunks = chunker.chunk_sections(sections, file_metadata)
            
            print(f"\n✅ Pipeline test successful!")
            print(f"  Sections: {len(sections)}")
            print(f"  Chunks: {len(chunks)}")
            return chunks
        else:
            print(f"\nRunning full pipeline (including embeddings and vector store)...")
            print(f"  Vector Store: {settings.vector_store_type}")
            print(f"  Embedding Provider: {settings.embedding_provider}")
            
            result = asyncio.run(service.ingest_pdf(pdf_path))
            
            print(f"\n✅ Pipeline test successful!")
            print(f"  Status: {result.status}")
            print(f"  Total chunks: {result.total_chunks}")
            print(f"  Total pages: {result.total_pages}")
            print(f"  Processing time: {result.processing_time_seconds:.2f}s")
            if result.error_message:
                print(f"  Error: {result.error_message}")
            
            return result
            
    except Exception as e:
        print(f"\n❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_vector_store_search(
    pdf_path: str,
    queries: List[str] = None,
    top_k: int = 5,
    interactive: bool = False
):
    """
    Test vector store search capability with different queries.
    
    Args:
        pdf_path: Path to PDF file (will be ingested if not already)
        queries: List of query strings to test
        top_k: Number of top results to return
        interactive: If True, enter interactive search mode
    """
    print("\n" + "="*80)
    print("STEP 4: VECTOR STORE SEARCH TEST")
    print("="*80)
    
    try:
        import asyncio
        from services.ingestion_service import IngestionService
        from services.embedding_service import get_embedding_service
        from services.vector_store import get_vector_store
        import numpy as np
        
        # Initialize services
        embedding_service = get_embedding_service()
        vector_store = get_vector_store()
        
        print(f"\nVector Store: {settings.vector_store_type}")
        print(f"Embedding Provider: {settings.embedding_provider}")
        
        # Check if we need to ingest the PDF first
        file_name = Path(pdf_path).name
        needs_ingestion = True
        
        # For local vector store, check if chunks exist
        if settings.vector_store_type == "local":
            # Try to get chunks count (if store has a way to check)
            if hasattr(vector_store, 'chunks') and len(vector_store.chunks) > 0:
                # Check if this file is already ingested
                existing_files = set(c.metadata.file_name for c in vector_store.chunks)
                if file_name in existing_files:
                    needs_ingestion = False
                    print(f"\n✅ PDF already ingested ({len(vector_store.chunks)} chunks in store)")
        
        # Ingest if needed
        if needs_ingestion:
            print(f"\n📥 Ingesting PDF to vector store...")
            service = IngestionService()
            result = asyncio.run(service.ingest_pdf(pdf_path))
            
            if result.status.value != "completed":
                print(f"❌ Ingestion failed: {result.error_message}")
                return None
            
            print(f"✅ Ingested {result.total_chunks} chunks")
            
            # Re-fetch vector store to get updated instance (in case singleton wasn't used)
            # This ensures we have the latest state
            vector_store = get_vector_store()
        
        # Get current chunk count
        if hasattr(vector_store, 'chunks'):
            total_chunks = len(vector_store.chunks)
        else:
            total_chunks = "unknown"
        
        print(f"\nTotal chunks in vector store: {total_chunks}")
        
        # Interactive mode
        if interactive:
            print(f"\n{'='*80}")
            print("INTERACTIVE SEARCH MODE")
            print("Enter queries to search (type 'exit' or 'quit' to stop)")
            print(f"{'='*80}")
            
            while True:
                try:
                    query = input("\n🔍 Search query: ").strip()
                    
                    if query.lower() in ['exit', 'quit', 'q']:
                        print("Exiting interactive mode...")
                        break
                    
                    if not query:
                        continue
                    
                    # Perform search
                    _perform_search(query, embedding_service, vector_store, top_k)
                    
                except KeyboardInterrupt:
                    print("\n\nExiting interactive mode...")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Test with provided queries
        elif queries:
            print(f"\n{'='*80}")
            print(f"TESTING {len(queries)} QUERIES")
            print(f"{'='*80}")
            
            for i, query in enumerate(queries, 1):
                print(f"\n{'='*80}")
                print(f"Query {i}/{len(queries)}: {query}")
                print(f"{'='*80}")
                _perform_search(query, embedding_service, vector_store, top_k)
        
        # Default: test with sample queries
        else:
            print(f"\n{'='*80}")
            print("TESTING WITH SAMPLE QUERIES")
            print(f"{'='*80}")
            
            # Generate sample queries based on PDF type
            config_metadata = metadata_loader.get_metadata(file_name)
            module_code = config_metadata.get("module_code", "")
            
            if module_code == "GLO":
                sample_queries = [
                    "What is Accepting Deposits?",
                    "Define Account Information Service",
                    "What does Accounting Records mean?",
                    "Explain Authorised Firm",
                    "What is a Reporting Entity?"
                ]
            else:
                sample_queries = [
                    "What are the application requirements?",
                    "What rules apply to reporting entities?",
                    "What are the capital requirements?",
                    "What is the scope of this module?",
                    "What are the compliance obligations?"
                ]
            
            for i, query in enumerate(sample_queries, 1):
                print(f"\n{'='*80}")
                print(f"Query {i}/{len(sample_queries)}: {query}")
                print(f"{'='*80}")
                _perform_search(query, embedding_service, vector_store, top_k)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Search test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def _perform_search(query: str, embedding_service, vector_store, top_k: int):
    """Perform a single search and display results."""
    import asyncio
    import numpy as np
    
    try:
        # Generate query embedding
        query_embedding = asyncio.run(embedding_service.embed_text(query))
        
        # Search vector store
        results = asyncio.run(vector_store.search(query_embedding, top_k=top_k))
        
        if not results:
            print("❌ No results found")
            return
        
        print(f"\n✅ Found {len(results)} results (showing top {top_k}):\n")
        
        # Calculate and display similarity scores for local store
        if settings.vector_store_type == "local" and hasattr(vector_store, 'chunks'):
            query_vec = np.array(query_embedding)
            similarities = []
            
            for chunk in results:
                if chunk.embedding:
                    chunk_vec = np.array(chunk.embedding)
                    similarity = np.dot(query_vec, chunk_vec) / (
                        np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec)
                    )
                    similarities.append((similarity, chunk))
            
            # Sort by similarity (if not already sorted)
            similarities.sort(key=lambda x: x[0], reverse=True)
            
            # Display results with scores
            for rank, (similarity, chunk) in enumerate(similarities[:top_k], 1):
                print(f"{'─'*80}")
                print(f"Result #{rank} [Similarity: {similarity:.4f}]")
                print(f"{'─'*80}")
                _print_search_result(chunk, rank)
        else:
            # Display results without scores (for other vector stores)
            for rank, chunk in enumerate(results, 1):
                print(f"{'─'*80}")
                print(f"Result #{rank}")
                print(f"{'─'*80}")
                _print_search_result(chunk, rank)
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        import traceback
        traceback.print_exc()


def _print_search_result(chunk, rank: int):
    """Print a single search result in a readable format."""
    metadata = chunk.metadata
    
    # Basic info
    if metadata.alias:
        print(f"Alias: {metadata.alias}")
    if metadata.module_code:
        print(f"Module: {metadata.module_code} - {metadata.module_name or ''}")
    if metadata.rule_number:
        print(f"Rule: {metadata.rule_number}")
    if metadata.term:
        print(f"Term: {metadata.term}")
    if metadata.section_number:
        print(f"Section: {metadata.section_number}")
    
    print(f"Page: {metadata.page_number} | Chunk: {metadata.chunk_index + 1}/{metadata.total_chunks}")
    print(f"Content Type: {metadata.content_type or 'N/A'}")
    print(f"Hierarchy: {metadata.hierarchy_path}")
    
    # Content preview
    content_preview = chunk.content
    max_length = 300
    if len(content_preview) > max_length:
        content_preview = content_preview[:max_length] + "..."
    
    print(f"\nContent:\n{content_preview}")
    print()


def save_results(sections, chunks, output_dir: str = "test_output"):
    """Save extraction and chunking results to files."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    if sections:
        sections_data = []
        for section in sections:
            sections_data.append({
                "level": section.level,
                "title": section.title,
                "content": section.content,
                "page_number": section.page_number,
                "rule_number": section.rule_number,
                "parent_path": [h[1] for h in section.parent_path] if section.parent_path else []
            })
        
        sections_file = output_path / "extracted_sections.json"
        with open(sections_file, "w", encoding="utf-8") as f:
            json.dump(sections_data, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Saved {len(sections)} sections to {sections_file}")
    
    if chunks:
        chunks_data = []
        for chunk in chunks:
            chunk_dict = {
                "content": chunk.content,
                "metadata": chunk.metadata.dict(),
            }
            if chunk.embedding:
                chunk_dict["embedding_dimensions"] = len(chunk.embedding)
            chunks_data.append(chunk_dict)
        
        chunks_file = output_path / "chunks.json"
        with open(chunks_file, "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved {len(chunks)} chunks to {chunks_file}")


def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test the DFSA RAG ingestion pipeline"
    )
    parser.add_argument(
        "pdf_path",
        type=str,
        help="Path to the PDF file to test"
    )
    parser.add_argument(
        "--step",
        choices=["extract", "chunk", "pipeline", "search", "all"],
        default="all",
        help="Which step to test (default: all)"
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Show all sections/chunks (default: show first 10)"
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=10,
        help="Maximum items to show when not using --show-all (default: 10)"
    )
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip embeddings and vector store in pipeline test"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save results to JSON files in test_output/ directory"
    )
    parser.add_argument(
        "--search-queries",
        nargs="+",
        help="List of queries to test search (e.g., --search-queries 'query1' 'query2')"
    )
    parser.add_argument(
        "--interactive-search",
        action="store_true",
        help="Enter interactive search mode (allows testing multiple queries)"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of top results to return in search (default: 5)"
    )
    
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"❌ Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    # Check if PDF is in config
    file_name = pdf_path.name
    if not metadata_loader.has_metadata(file_name):
        print(f"❌ Error: PDF '{file_name}' is not configured in pdf_metadata.json")
        print("Only PDFs listed in the configuration file can be processed.")
        print(f"\nAvailable PDFs in config:")
        for pdf_name, pdf_config in metadata_loader.get_all_metadata().items():
            alias = pdf_config.get("alias", "N/A")
            module = pdf_config.get("module_code", "N/A")
            print(f"  - {pdf_name} ({alias}, Module: {module})")
        sys.exit(1)
    
    # Show PDF info from config
    config_metadata = metadata_loader.get_metadata(file_name)
    
    print("="*80)
    print("DFSA RAG PIPELINE TEST")
    print("="*80)
    print(f"PDF: {pdf_path}")
    print(f"Alias: {config_metadata.get('alias', 'N/A')}")
    print(f"Module: {config_metadata.get('module_code', 'N/A')} - {config_metadata.get('module_name', 'N/A')}")
    print(f"Chunking Strategy: {metadata_loader.get_chunking_config(file_name).get('chunking_strategy', 'section_aware')}")
    print(f"Step: {args.step}")
    print("="*80)
    
    sections = None
    file_metadata = None
    chunks = None
    
    # Step 1: Extraction
    if args.step in ["extract", "all"]:
        sections, file_metadata = test_pdf_extraction(
            str(pdf_path),
            show_all=args.show_all,
            max_sections=args.max_items
        )
        if not sections:
            print("\n❌ Extraction failed. Cannot continue.")
            sys.exit(1)
    
    # Step 2: Chunking
    if args.step in ["chunk", "all"]:
        if sections is None:
            # Try to extract first
            sections, file_metadata = test_pdf_extraction(
                str(pdf_path),
                show_all=False,
                max_sections=1
            )
            if not sections:
                print("\n❌ Extraction failed. Cannot chunk.")
                sys.exit(1)
        
        chunks = test_chunking(
            sections,
            file_metadata,
            show_all=args.show_all,
            max_chunks=args.max_items
        )
    
    # Step 3: Full Pipeline
    if args.step == "pipeline":
        result = test_full_pipeline(str(pdf_path), skip_embeddings=args.skip_embeddings)
    
    # Step 4: Vector Store Search
    if args.step in ["search", "all"]:
        # Note: test_vector_store_search will handle ingestion if needed
        # No need to pre-ingest here since it checks and ingests automatically
        test_vector_store_search(
            str(pdf_path),
            queries=args.search_queries,
            top_k=args.top_k,
            interactive=args.interactive_search
        )
    
    # Save results if requested
    if args.save and sections:
        save_results(sections, chunks)
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()


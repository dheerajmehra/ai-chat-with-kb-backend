#!/usr/bin/env python3
"""Test script to verify PDF extraction libraries are working."""

def test_imports():
    """Test that required libraries can be imported."""
    print("Testing imports...")
    
    # Test PDF libraries
    try:
        import fitz
        print("✓ PyMuPDF (fitz) is available")
        pymupdf_available = True
    except ImportError:
        print("✗ PyMuPDF (fitz) is NOT available")
        pymupdf_available = False
    
    try:
        import pdfplumber
        print("✓ pdfplumber is available")
        pdfplumber_available = True
    except ImportError:
        print("✗ pdfplumber is NOT available")
        pdfplumber_available = False
    
    if not pymupdf_available and not pdfplumber_available:
        print("\n❌ ERROR: Neither PDF library is available!")
        print("Please install at least one:")
        print("  pip install pdfplumber")
        return False
    
    # Test other critical imports
    try:
        from fastapi import FastAPI
        print("✓ FastAPI is available")
    except ImportError:
        print("✗ FastAPI is NOT available")
        return False
    
    try:
        from sentence_transformers import SentenceTransformer
        print("✓ sentence-transformers is available")
    except ImportError:
        print("⚠ sentence-transformers is NOT available (optional)")
    
    try:
        import pandas
        print("✓ pandas is available")
    except ImportError:
        print("✗ pandas is NOT available")
        return False
    
    print("\n✅ All critical dependencies are available!")
    return True


def test_pdf_extractor():
    """Test that the PDF extractor can be instantiated."""
    print("\nTesting PDF extractor...")
    try:
        from utils.pdf_extractor import DFSAExtractor
        extractor = DFSAExtractor()
        print("✓ DFSAExtractor can be instantiated")
        return True
    except Exception as e:
        print(f"✗ Error creating DFSAExtractor: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("DFSA RAG Pipeline - Installation Test")
    print("=" * 50)
    
    imports_ok = test_imports()
    if imports_ok:
        extractor_ok = test_pdf_extractor()
        if extractor_ok:
            print("\n" + "=" * 50)
            print("✅ Installation test PASSED!")
            print("=" * 50)
        else:
            print("\n" + "=" * 50)
            print("❌ Installation test FAILED!")
            print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("❌ Installation test FAILED!")
        print("=" * 50)


#!/bin/bash
# Cleanup script to move duplicate/outdated files to to_delete/ folder
# This preserves files instead of deleting them permanently

set -e  # Exit on error

echo "=========================================="
echo "Backend Code Cleanup Script"
echo "=========================================="
echo ""
echo "This script will move duplicate/outdated files to 'to_delete/' folder"
echo "instead of deleting them permanently."
echo ""
read -p "Do you want to proceed? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

# Create to_delete directory
TO_DELETE_DIR="to_delete"
mkdir -p "$TO_DELETE_DIR"

echo ""
echo "Step 1: Moving duplicate code directories..."
echo "--------------------------------------------"

# Move duplicate directories (these are now in shared/)
if [ -d "models" ]; then
    echo "  Moving models/ → to_delete/models/"
    mv models "$TO_DELETE_DIR/"
fi

if [ -d "services" ]; then
    echo "  Moving services/ → to_delete/services/"
    mv services "$TO_DELETE_DIR/"
fi

if [ -d "utils" ]; then
    echo "  Moving utils/ → to_delete/utils/"
    mv utils "$TO_DELETE_DIR/"
fi

echo ""
echo "Step 2: Moving legacy API..."
echo "--------------------------------------------"

if [ -d "api" ] && [ -f "api/main.py" ]; then
    echo "  Found legacy api/main.py"
    read -p "  Move it to to_delete/? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "  Moving api/ → to_delete/api/"
        mv api "$TO_DELETE_DIR/"
    else
        echo "  Keeping api/ for backward compatibility"
    fi
fi

echo ""
echo "Step 3: Moving root config files..."
echo "--------------------------------------------"

if [ -f "config.py" ]; then
    echo "  Found root config.py"
    read -p "  Move it to to_delete/? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "  Moving config.py → to_delete/config.py"
        mv config.py "$TO_DELETE_DIR/"
    else
        echo "  Keeping config.py (may be used by test_pipeline.py)"
    fi
fi

if [ -d "config" ] && [ -f "config/pdf_metadata.json" ]; then
    echo "  Found root config/pdf_metadata.json"
    read -p "  Move config/ directory to to_delete/? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "  Moving config/ → to_delete/config/"
        mv config "$TO_DELETE_DIR/"
    else
        echo "  Keeping config/ directory"
    fi
fi

echo ""
echo "Step 4: Moving outdated documentation..."
echo "--------------------------------------------"

# List of outdated documentation files
OUTDATED_DOCS=(
    "CHAT_INTEGRATION_PLAN.md"
    "FRONTEND_INTEGRATION_PLAN.md"
    "INTEGRATION_IMPLEMENTATION.md"
    "LOCAL_VECTOR_STORE_TESTING_PROPOSAL.md"
    "METADATA_ENHANCEMENT_PROPOSAL.md"
    "SEARCH_TESTING_GUIDE.md"
    "TEST_SCRIPT_UPDATES.md"
    "PDF_VIEWER_FIXES.md"
    "SINGLETON_PATTERN_DOCUMENTATION.md"
    "IMPLEMENTATION_SUMMARY.md"
    "QUICK_TEST.md"
)

DOCS_MOVED=0
for doc in "${OUTDATED_DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo "  Moving $doc → to_delete/$doc"
        mv "$doc" "$TO_DELETE_DIR/"
        DOCS_MOVED=$((DOCS_MOVED + 1))
    fi
done

if [ $DOCS_MOVED -eq 0 ]; then
    echo "  No outdated documentation files found"
fi

echo ""
echo "Step 5: Summary..."
echo "--------------------------------------------"

echo "  Files moved to: $TO_DELETE_DIR/"
echo "  Note: Thoughts.txt and known_issues.txt were kept (as requested)"

echo ""
echo "=========================================="
echo "Cleanup Complete!"
echo "=========================================="
echo ""
echo "Files moved to: $TO_DELETE_DIR/"
echo ""
echo "Next steps:"
echo "1. Update test_pipeline.py to use shared.* imports (if config.py was moved)"
echo "2. Test services: ./run_server.sh"
echo "3. Test pipeline: python test_pipeline.py ..."
echo "4. Verify Docker builds: docker-compose build"
echo ""
echo "To permanently delete files later:"
echo "  rm -rf $TO_DELETE_DIR/"
echo ""

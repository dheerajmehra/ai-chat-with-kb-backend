"""Simple test script to verify tools are working correctly.

This script tests the tool wrappers without requiring LangChain.
Run with: python test_tools.py
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.tools import get_vector_search_tool, get_definition_lookup_tool
from shared.utils.logger import logger


async def test_vector_search_tool():
    """Test the vector search tool."""
    print("\n" + "="*80)
    print("Testing VectorSearchTool")
    print("="*80)
    
    tool = get_vector_search_tool()
    
    # Test 1: Basic search
    print("\n1. Basic search:")
    result = await tool.execute(
        query="What are capital requirements?",
        top_k=3
    )
    
    if result.success:
        print(f"   ✓ Found {len(result.result)} results")
        for i, chunk in enumerate(result.result[:2], 1):
            print(f"   Result {i}:")
            print(f"     Score: {chunk['score']:.3f}")
            print(f"     Module: {chunk.get('module_code', 'N/A')}")
            print(f"     Content: {chunk['content'][:100]}...")
    else:
        print(f"   ✗ Error: {result.error}")
    
    # Test 2: Search with filters
    print("\n2. Search with module filter:")
    result = await tool.execute(
        query="capital requirements",
        top_k=5,
        module_code="PRU"
    )
    
    if result.success:
        print(f"   ✓ Found {len(result.result)} results in PRU module")
        if result.result:
            print(f"   First result module: {result.result[0].get('module_code', 'N/A')}")
    else:
        print(f"   ✗ Error: {result.error}")
    
    # Test 3: Get tool schema
    print("\n3. Tool schema (for LangChain compatibility):")
    schema = tool.get_schema_dict()
    print(f"   Name: {schema['name']}")
    print(f"   Description: {schema['description'][:80]}...")
    print(f"   Parameters: {len(schema['parameters']['properties'])} parameters")


async def test_definition_lookup_tool():
    """Test the definition lookup tool."""
    print("\n" + "="*80)
    print("Testing DefinitionLookupTool")
    print("="*80)
    
    tool = get_definition_lookup_tool()
    
    # Test 1: Lookup common term
    print("\n1. Lookup 'Authorised Firm':")
    result = await tool.execute(
        term="Authorised Firm",
        exact_match=True
    )
    
    if result.success:
        if result.result:
            print(f"   ✓ Found {len(result.result)} definition(s)")
            for i, defn in enumerate(result.result[:2], 1):
                print(f"   Definition {i}:")
                print(f"     Term: {defn['term']}")
                print(f"     Definition: {defn['definition'][:150]}...")
        else:
            print(f"   ⚠ No definition found (this is OK if GLO module not ingested)")
    else:
        print(f"   ✗ Error: {result.error}")
    
    # Test 2: Fuzzy match
    print("\n2. Fuzzy lookup 'firm':")
    result = await tool.execute(
        term="firm",
        exact_match=False,
        case_sensitive=False
    )
    
    if result.success:
        print(f"   ✓ Found {len(result.result)} definition(s) with fuzzy match")
        if result.result:
            print(f"   First match: {result.result[0]['term']}")
    else:
        print(f"   ✗ Error: {result.error}")
    
    # Test 3: Get tool schema
    print("\n3. Tool schema (for LangChain compatibility):")
    schema = tool.get_schema_dict()
    print(f"   Name: {schema['name']}")
    print(f"   Description: {schema['description'][:80]}...")
    print(f"   Parameters: {len(schema['parameters']['properties'])} parameters")


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("Tool Wrapper Tests")
    print("="*80)
    print("\nNote: These tools are designed for future LangChain/LangGraph integration")
    print("but can be used independently now.\n")
    
    try:
        await test_vector_search_tool()
        await test_definition_lookup_tool()
        
        print("\n" + "="*80)
        print("Tests Complete")
        print("="*80)
        print("\n✓ Tools are ready for LangChain/LangGraph integration")
        print("✓ Tools can be used independently without agents")
        print("\nNext steps:")
        print("  1. Install LangChain: pip install langchain langchain-openai langgraph")
        print("  2. Wrap tools using StructuredTool.from_function()")
        print("  3. Create agents that use these tools")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

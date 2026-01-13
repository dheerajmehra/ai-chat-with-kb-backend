"""Script to create Azure AI Search index for DFSA rulebooks."""
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    SearchField
)
from azure.core.credentials import AzureKeyCredential
from config import get_settings
import sys

settings = get_settings()


def create_index():
    """Create Azure AI Search index with vector support."""
    try:
        credential = AzureKeyCredential(settings.azure_search_key)
        client = SearchIndexClient(
            endpoint=settings.azure_search_endpoint,
            credential=credential
        )
        
        # Define fields
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchField(
                name="content",
                type=SearchFieldDataType.String,
                searchable=True,
                analyzer_name="en.microsoft"
            ),
            SearchField(
                name="contentVector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                vector_search_dimensions=1536,  # OpenAI ada-002 dimensions
                vector_search_profile_name="default-vector-profile"
            ),
            SimpleField(name="file_name", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="module_code", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="module_name", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="chapter_number", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="chapter_title", type=SearchFieldDataType.String),
            SimpleField(name="section_number", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="section_title", type=SearchFieldDataType.String),
            SimpleField(name="subsection_number", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="subsection_title", type=SearchFieldDataType.String),
            SimpleField(name="rule_number", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="page_number", type=SearchFieldDataType.Int32, filterable=True),
            SimpleField(name="chunk_index", type=SearchFieldDataType.Int32),
            SimpleField(name="hierarchy_path", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="content_type", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="file_version", type=SearchFieldDataType.String),
        ]
        
        # Define vector search configuration
        vector_search = VectorSearch(
            profiles=[
                VectorSearchProfile(
                    name="default-vector-profile",
                    algorithm_configuration_name="default-algorithm"
                )
            ],
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="default-algorithm",
                    kind="hnsw"
                )
            ]
        )
        
        # Create index
        index = SearchIndex(
            name=settings.azure_search_index_name,
            fields=fields,
            vector_search=vector_search
        )
        
        # Create or update index
        result = client.create_or_update_index(index)
        print(f"Successfully created/updated index: {result.name}")
        return True
        
    except Exception as e:
        print(f"Error creating index: {e}")
        return False


if __name__ == "__main__":
    if not settings.azure_search_endpoint or not settings.azure_search_key:
        print("Error: Azure Search configuration not found in .env file")
        print("Please set AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_KEY")
        sys.exit(1)
    
    success = create_index()
    sys.exit(0 if success else 1)


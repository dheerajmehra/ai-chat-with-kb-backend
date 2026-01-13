"""Configuration management for the DFSA RAG ingestion pipeline."""
from pydantic_settings import BaseSettings
from typing import Literal
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "DFSA RAG Ingestion Pipeline"
    app_version: str = "1.0.0"
    log_level: str = "INFO"
    
    # PDF Processing Library
    pdf_library: Literal["pdfplumber", "pymupdf"] = "pdfplumber"
    
    # Vector Store
    vector_store_type: Literal["azure", "openai", "local", "file"] = "file"
    vector_store_path: str = "data/vector_store.pkl"  # For file-based store
    embedding_provider: Literal["openai", "azure", "sentence-transformers"] = "sentence-transformers"
    
    # Azure AI Search
    azure_search_endpoint: str = ""
    azure_search_key: str = ""
    azure_search_index_name: str = "dfsa-rulebooks"
    
    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-02-15-preview"
    azure_openai_deployment_name: str = "text-embedding-ada-002"
    
    # OpenAI
    openai_api_key: str = ""  # Set via OPENAI_API_KEY environment variable
    openai_embedding_model: str = "text-embedding-ada-002"
    
    # LLM Configuration (for chat responses)
    llm_enabled: bool = False  # Set to True to enable LLM-based responses
    llm_model: str = "gpt-4o"  # OpenAI model to use (e.g., gpt-4o, gpt-4-turbo, gpt-3.5-turbo)
    llm_max_tokens: int = 1000  # Maximum tokens in LLM response
    llm_temperature: float = 0.7  # Temperature for LLM (0.0-2.0, higher = more creative)
    llm_system_prompt: str = (
        "You are an expert assistant helping users understand DFSA (Dubai Financial Services Authority) "
        "rulebooks and regulations. Your responses should be clear, accurate, and based solely on the "
        "provided excerpts from the rulebooks. Always cite specific rules, modules, or page numbers when "
        "referencing information. If you cannot answer a question based on the provided excerpts, "
        "clearly state that the information is not available in the provided context."
    )
    
    # Sentence Transformers
    sentence_transformer_model: str = "all-MiniLM-L6-v2"
    
    # Chunking
    chunk_size: int = 1000
    chunk_overlap: int = 200
    respect_sentence_boundaries: bool = True
    respect_section_boundaries: bool = True
    
    # Processing
    max_file_size_mb: int = 50
    supported_file_types: str = "pdf"
    background_task_timeout: int = 3600
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


"""Embedding service with support for multiple providers."""
from abc import ABC, abstractmethod
from typing import List
from shared.config import get_settings
from shared.utils.logger import logger

settings = get_settings()


class EmbeddingService(ABC):
    """Abstract base class for embedding services."""
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass


class OpenAIEmbeddingService(EmbeddingService):
    """OpenAI embedding service."""
    
    def __init__(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model = settings.openai_embedding_model
            logger.info("Initialized OpenAI embedding service")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI service: {e}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error generating OpenAI batch embeddings: {e}")
            raise


class AzureOpenAIEmbeddingService(EmbeddingService):
    """Azure OpenAI embedding service."""
    
    def __init__(self):
        try:
            from openai import AzureOpenAI
            self.client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint
            )
            self.deployment = settings.azure_openai_deployment_name
            logger.info("Initialized Azure OpenAI embedding service")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI service: {e}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        try:
            response = self.client.embeddings.create(
                model=self.deployment,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating Azure OpenAI embedding: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            response = self.client.embeddings.create(
                model=self.deployment,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error generating Azure OpenAI batch embeddings: {e}")
            raise


class SentenceTransformerEmbeddingService(EmbeddingService):
    """Local sentence transformer embedding service."""
    
    def __init__(self):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(settings.sentence_transformer_model)
            logger.info(f"Initialized SentenceTransformer service with {settings.sentence_transformer_model}")
        except Exception as e:
            logger.error(f"Failed to initialize SentenceTransformer service: {e}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating SentenceTransformer embedding: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating SentenceTransformer batch embeddings: {e}")
            raise


def get_embedding_service() -> EmbeddingService:
    """Factory function to get the appropriate embedding service."""
    provider = settings.embedding_provider.lower()
    
    if provider == "openai":
        return OpenAIEmbeddingService()
    elif provider == "azure":
        return AzureOpenAIEmbeddingService()
    elif provider == "sentence-transformers":
        return SentenceTransformerEmbeddingService()
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")


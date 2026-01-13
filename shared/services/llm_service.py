"""LLM service for generating responses using OpenAI."""
from typing import List, Optional
from shared.config import get_settings
from shared.utils.logger import logger
from shared.models.schemas import DocumentChunk

settings = get_settings()


class LLMService:
    """Service for interacting with OpenAI LLM."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        self.client = None
        self.model = None
        self.system_prompt = None
        
        if not settings.llm_enabled:
            logger.info("LLM service is disabled in configuration")
            return
        
        if not settings.openai_api_key:
            logger.warning("LLM is enabled but OPENAI_API_KEY is not set. LLM service will not be available.")
            return
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model = settings.llm_model
            self.system_prompt = settings.llm_system_prompt
            logger.info(f"Initialized LLM service with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            # Don't raise - allow service to continue without LLM
            self.client = None
    
    def is_enabled(self) -> bool:
        """Check if LLM service is enabled."""
        return settings.llm_enabled and self.client is not None
    
    async def generate_response(
        self,
        user_query: str,
        chunks: List[DocumentChunk],
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate LLM response based on user query and retrieved chunks.
        
        Args:
            user_query: The user's question/query
            chunks: List of relevant document chunks retrieved from vector store
            max_tokens: Maximum tokens in response (uses default from config if None)
        
        Returns:
            Generated response string from LLM
        """
        if not self.is_enabled():
            raise RuntimeError("LLM service is not enabled")
        
        # Format chunks as context
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            chunk_info = f"Excerpt {i}"
            if chunk.metadata.rule_number:
                chunk_info += f" (Rule: {chunk.metadata.rule_number})"
            if chunk.metadata.module_code:
                chunk_info += f" (Module: {chunk.metadata.module_code})"
            if chunk.metadata.page_number:
                chunk_info += f" (Page: {chunk.metadata.page_number})"
            
            context_parts.append(f"{chunk_info}\n{chunk.content}")
        
        context = "\n\n".join(context_parts)
        
        # Build the prompt
        user_prompt = (
            f"I'm asking you a query about information in DFSA (Dubai Financial Services Authority) rulebooks. "
            f"I'll give you the query, and excerpts from the rulebooks that are most relevant to the query. "
            f"You should use the excerpts to answer the query. "
            f"If the query is not answerable using the provided excerpts, or if the query is not clear, you should say so. "
            f"If the query is answerable using the provided excerpts, you should answer it in a clear and concise manner. "
            f"Please cite the specific rules, modules, or page numbers when referencing information from the excerpts.\n\n"
            f"Query: {user_query}\n\n"
            f"Excerpts:\n{context}\n\n"
            f"Answer:"
        )
        
        try:
            # Prepare messages
            messages = []
            if self.system_prompt:
                messages.append({
                    "role": "system",
                    "content": self.system_prompt
                })
            messages.append({
                "role": "user",
                "content": user_prompt
            })
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens or settings.llm_max_tokens,
                temperature=settings.llm_temperature
            )
            
            answer = response.choices[0].message.content
            logger.info(f"Generated LLM response ({len(answer)} chars)")
            return answer
            
        except Exception as e:
            # Provide more detailed error messages
            error_msg = str(e)
            if hasattr(e, 'response') and hasattr(e.response, 'json'):
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('error', {}).get('message', error_msg)
                    error_type = error_data.get('error', {}).get('type', 'Unknown')
                    logger.error(f"OpenAI API error ({error_type}): {error_msg}")
                except:
                    pass
            
            # Check for common error scenarios
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower() or "invalid" in error_msg.lower():
                error_msg = f"Invalid or missing OpenAI API key. Please check your OPENAI_API_KEY in .env file. Original error: {error_msg}"
            elif "insufficient_quota" in error_msg.lower() or "billing" in error_msg.lower():
                error_msg = f"OpenAI API quota exceeded or billing issue. Please check your OpenAI account. Original error: {error_msg}"
            elif "rate_limit" in error_msg.lower():
                error_msg = f"OpenAI API rate limit exceeded. Please try again later. Original error: {error_msg}"
            
            logger.error(f"Error generating LLM response: {error_msg}", exc_info=True)
            raise RuntimeError(error_msg) from e


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

"""Base tool interface for agentic RAG tools.

This interface is designed to be compatible with LangChain's tool system,
allowing easy integration later without code changes.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from shared.utils.logger import logger


class ToolInput(BaseModel):
    """Base input schema for tools."""
    pass


class ToolOutput(BaseModel):
    """Base output schema for tools."""
    success: bool = Field(..., description="Whether the tool execution was successful")
    result: Any = Field(..., description="The result of the tool execution")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BaseTool(ABC):
    """
    Base class for all tools in the agentic RAG system.
    
    This interface is designed to be compatible with LangChain's tool system.
    When LangChain is integrated, tools can be easily wrapped using:
    
    ```python
    from langchain.tools import StructuredTool
    langchain_tool = StructuredTool.from_function(
        func=tool.execute,
        name=tool.name,
        description=tool.description,
        args_schema=tool.input_schema
    )
    ```
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        input_schema: type[BaseModel]
    ):
        """
        Initialize the tool.
        
        Args:
            name: Unique name of the tool (e.g., "vector_search")
            description: Human-readable description for the LLM
            input_schema: Pydantic model defining the input parameters
        """
        self.name = name
        self.description = description
        self.input_schema = input_schema
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolOutput:
        """
        Execute the tool with the given parameters.
        
        Args:
            **kwargs: Tool-specific parameters (validated against input_schema)
        
        Returns:
            ToolOutput with the result or error
        """
        pass
    
    def get_schema_dict(self) -> Dict[str, Any]:
        """
        Get the tool schema as a dictionary.
        
        This format is compatible with LangChain's tool system.
        
        Returns:
            Dictionary with name, description, and input schema
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema.model_json_schema()
        }
    
    def __call__(self, **kwargs) -> ToolOutput:
        """
        Allow tools to be called directly (for LangChain compatibility).
        
        Note: This is a synchronous wrapper. For async execution, use execute().
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If event loop is running, create a task
                # Note: This is a simplified approach. In production, you might
                # want to use a different pattern for async in sync context
                raise RuntimeError(
                    "Cannot call async tool from sync context. Use await tool.execute() instead."
                )
            else:
                return loop.run_until_complete(self.execute(**kwargs))
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self.execute(**kwargs))

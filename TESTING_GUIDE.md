# Testing Framework Guide

## Overview

This project uses **pytest** as the testing framework with comprehensive unit and integration test coverage. The testing setup follows best practices for FastAPI applications and RAG systems.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── __init__.py
│   ├── test_models.py      # Pydantic model tests
│   ├── test_tools.py       # Tool wrapper tests
│   ├── test_services.py    # Service layer tests
│   └── test_utils.py       # Utility function tests
└── integration/            # Integration tests
    ├── __init__.py
    ├── test_api.py         # API endpoint tests
    └── test_vector_store.py # Vector store integration tests
```

## Running Tests

### Run All Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov

# Run with verbose output
pytest -v
```

### Run Specific Test Categories

```bash
# Only unit tests (fast)
pytest -m unit

# Only integration tests
pytest -m integration

# Only API tests
pytest -m api

# Skip slow tests
pytest -m "not slow"

# Skip tests requiring OpenAI
pytest -m "not requires_openai"
```

### Run Specific Test Files

```bash
# Run specific test file
pytest tests/unit/test_models.py

# Run specific test class
pytest tests/unit/test_models.py::TestChunkMetadata

# Run specific test function
pytest tests/unit/test_models.py::TestChunkMetadata::test_create_minimal_metadata
```

### Coverage Reports

```bash
# Terminal report
pytest --cov --cov-report=term-missing

# HTML report (opens in browser)
pytest --cov --cov-report=html
open htmlcov/index.html

# XML report (for CI/CD)
pytest --cov --cov-report=xml
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)

- **Fast**: Run in milliseconds
- **Isolated**: No external dependencies
- **Mocked**: Use mocks for external services
- **Coverage**: Test individual functions/classes

**Examples:**
- Pydantic model validation
- Tool input/output schemas
- Utility functions
- Service methods with mocked dependencies

### Integration Tests (`@pytest.mark.integration`)

- **Slower**: May take seconds
- **Real dependencies**: Use actual services when possible
- **End-to-end**: Test component interactions

**Examples:**
- Vector store persistence
- API endpoint workflows
- Service integration

### API Tests (`@pytest.mark.api`)

- **FastAPI TestClient**: Use FastAPI's test client
- **Request/Response**: Test HTTP endpoints
- **Status codes**: Verify correct responses

## Writing Tests

### Example: Unit Test

```python
import pytest
from shared.models.schemas import ChatRequest

@pytest.mark.unit
class TestChatRequest:
    def test_create_request(self):
        """Test creating a chat request."""
        request = ChatRequest(
            message="test",
            user_id="user1",
            session_id="session1"
        )
        assert request.message == "test"
        assert request.top_k == 5  # Default
```

### Example: Test with Fixtures

```python
@pytest.mark.unit
def test_chunk_creation(sample_chunk_metadata):
    """Test creating a document chunk."""
    chunk = DocumentChunk(
        content="Test",
        metadata=sample_chunk_metadata
    )
    assert chunk.content == "Test"
```

### Example: Async Test

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_vector_search(sample_chunks):
    """Test vector search."""
    store = LocalVectorStore()
    await store.upsert_chunks(sample_chunks)
    
    results = await store.search([0.1] * 1536, top_k=3)
    assert len(results) == 3
```

### Example: Test with Mocks

```python
@pytest.mark.unit
@pytest.mark.mock
async def test_tool_with_mock(mock_openai_client):
    """Test tool with mocked OpenAI client."""
    with patch('shared.services.llm_service.OpenAI', return_value=mock_openai_client):
        service = get_llm_service()
        response = await service.generate_response("test", [])
        assert isinstance(response, str)
```

## Available Fixtures

### Data Fixtures

- `sample_chunk_metadata`: Sample ChunkMetadata object
- `sample_document_chunk`: Sample DocumentChunk
- `sample_chunks`: List of 5 sample chunks
- `glossary_chunk`: Sample glossary definition chunk
- `sample_pdf_section`: Sample PDFSection
- `file_metadata`: Sample file metadata dict

### Service Fixtures

- `mock_openai_client`: Mocked OpenAI client
- `mock_embedding_response`: Mock embedding API response
- `temp_vector_store_path`: Temporary path for vector store

### Configuration Fixtures

- `disable_llm`: Disable LLM in config
- `enable_llm`: Enable LLM with mocked key
- `mock_openai_api_key`: Mock API key
- `test_settings`: Test configuration

## Test Coverage Goals

### Current Targets

- **Overall**: 70% minimum
- **Critical paths**: 90%+
- **Services**: 80%+
- **Models**: 95%+
- **Utils**: 75%+

### Coverage by Component

| Component | Target | Current |
|-----------|--------|---------|
| Models/Schemas | 95% | - |
| Tools | 80% | - |
| Services | 80% | - |
| Utils | 75% | - |
| API Endpoints | 70% | - |

## Best Practices

### 1. Test Naming

```python
# Good
def test_create_chunk_with_metadata():
def test_search_returns_top_k_results():
def test_validation_rejects_invalid_top_k():

# Bad
def test1():
def test_chunk():
```

### 2. Test Organization

```python
@pytest.mark.unit
class TestVectorStore:
    """Test VectorStore class."""
    
    def test_initialization(self):
        """Test store initialization."""
        pass
    
    def test_upsert_chunks(self):
        """Test upserting chunks."""
        pass
```

### 3. Use Fixtures

```python
# Good - reuse fixtures
def test_something(sample_chunks):
    pass

# Bad - create data in test
def test_something():
    chunks = [DocumentChunk(...)]  # Don't do this
```

### 4. Mock External Services

```python
# Good - mock external API
@pytest.mark.mock
def test_with_mock(mock_openai_client):
    with patch('module.OpenAI', return_value=mock_openai_client):
        # test code
```

### 5. Test Edge Cases

```python
def test_empty_input():
    """Test handling of empty input."""
    result = function([])
    assert result == []

def test_invalid_input():
    """Test validation of invalid input."""
    with pytest.raises(ValidationError):
        Model(invalid_field="value")
```

### 6. Async Tests

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov --cov-report=xml
      - uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Common Patterns

### Testing Pydantic Models

```python
def test_model_validation():
    # Valid
    model = MyModel(required_field="value")
    assert model.required_field == "value"
    
    # Invalid
    with pytest.raises(ValidationError):
        MyModel()  # Missing required field
```

### Testing Async Functions

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await my_async_function()
    assert result is not None
```

### Testing with Mocks

```python
@patch('module.external_service')
def test_with_mock(mock_service):
    mock_service.return_value = "mocked"
    result = function_using_service()
    assert result == "mocked"
```

### Testing FastAPI Endpoints

```python
def test_endpoint(client):
    response = client.get("/api/endpoint")
    assert response.status_code == 200
    assert "data" in response.json()
```

## Troubleshooting

### Tests Not Found

```bash
# Check test discovery
pytest --collect-only

# Check if files match pattern
pytest tests/ -v
```

### Import Errors

```bash
# Ensure project root is in path (conftest.py handles this)
# Or run from project root
cd /path/to/project
pytest
```

### Coverage Not Working

```bash
# Check coverage installation
pip install pytest-cov

# Run with explicit coverage
pytest --cov=shared --cov-report=term
```

## Next Steps

1. **Add more unit tests** for existing code
2. **Add integration tests** for API workflows
3. **Set up CI/CD** to run tests automatically
4. **Increase coverage** to meet targets
5. **Add performance tests** for critical paths

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Coverage.py](https://coverage.readthedocs.io/)

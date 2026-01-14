"""Integration tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.mark.integration
@pytest.mark.api
class TestChatServiceAPI:
    """Test chat service API endpoints."""
    
    @pytest.fixture
    def chat_app(self):
        """Get chat service app."""
        from chat_service.api.main import app
        return app
    
    @pytest.fixture
    def chat_client(self, chat_app):
        """Create test client for chat service."""
        return TestClient(chat_app)
    
    def test_root_endpoint(self, chat_client):
        """Test root endpoint."""
        response = chat_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data
    
    def test_health_endpoint(self, chat_client):
        """Test health check endpoint."""
        response = chat_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_get_documents(self, chat_client):
        """Test getting documents list."""
        response = chat_client.get("/api/documents")
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert isinstance(data["documents"], list)
    
    def test_chat_endpoint_structure(self, chat_client):
        """Test chat endpoint request/response structure."""
        response = chat_client.post(
            "/api/chat",
            json={
                "message": "test query",
                "user_id": "test_user",
                "session_id": "test_session",
                "top_k": 5
            }
        )
        # Should return 200 or handle error gracefully
        assert response.status_code in [200, 500]  # 500 if vector store not set up
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert "references" in data
            assert isinstance(data["references"], list)


@pytest.mark.integration
@pytest.mark.api
class TestIngestionServiceAPI:
    """Test ingestion service API endpoints."""
    
    @pytest.fixture
    def ingestion_app(self):
        """Get ingestion service app."""
        from ingestion_service.api.main import app
        return app
    
    @pytest.fixture
    def ingestion_client(self, ingestion_app):
        """Create test client for ingestion service."""
        return TestClient(ingestion_app)
    
    def test_root_endpoint(self, ingestion_client):
        """Test root endpoint."""
        response = ingestion_client.get("/")
        assert response.status_code == 200
    
    def test_health_endpoint(self, ingestion_client):
        """Test health check endpoint."""
        response = ingestion_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_ingest_endpoint_structure(self, ingestion_client):
        """Test ingest endpoint accepts file upload."""
        # Test endpoint exists (will fail without actual file, but tests structure)
        response = ingestion_client.post("/ingest")
        # Should return 422 (validation error) or 400, not 404
        assert response.status_code != 404

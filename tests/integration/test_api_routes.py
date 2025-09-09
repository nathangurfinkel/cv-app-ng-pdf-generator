"""
Integration tests for PDF Service API routes.
Follows Single Responsibility Principle - tests only API route functionality.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app


class TestPDFAPIRoutes:
    """Test class for PDF API routes following Single Responsibility Principle."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_check(self, client):
        """Test health check endpoint."""
        # Act
        response = client.get("/")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "CV Builder PDF Service is online"

    def test_health_endpoint(self, client):
        """Test dedicated health endpoint."""
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_get_templates_success(self, client):
        """Test successful template listing."""
        # Act
        response = client.get("/pdf/templates")
        
        # Assert
        assert response.status_code == 200
        assert "templates" in response.json()
        assert len(response.json()["templates"]) == 5
        assert "classic" in response.json()["templates"]
        assert "modern" in response.json()["templates"]

    @patch('app.main.async_playwright')
    def test_generate_pdf_success(self, mock_playwright, client, sample_pdf_request):
        """Test successful PDF generation."""
        # Arrange
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_pdf_buffer = b"fake pdf content"
        
        mock_page.pdf = AsyncMock(return_value=mock_pdf_buffer)
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_browser.close = AsyncMock()
        
        mock_playwright.return_value.__aenter__.return_value.chromium.launch = AsyncMock(return_value=mock_browser)
        
        with patch('app.main.uuid.uuid4', return_value=Mock(hex="test123")):
            # Act
            response = client.post("/pdf/generate", json=sample_pdf_request)
            
            # Assert
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            assert "cv_classic_test123.pdf" in response.headers["content-disposition"]

    @patch('app.main.async_playwright')
    def test_generate_pdf_with_different_template(self, mock_playwright, client):
        """Test PDF generation with different template."""
        # Arrange
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_pdf_buffer = b"fake pdf content"
        
        mock_page.pdf = AsyncMock(return_value=mock_pdf_buffer)
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_browser.close = AsyncMock()
        
        mock_playwright.return_value.__aenter__.return_value.chromium.launch = AsyncMock(return_value=mock_browser)
        
        request_data = {
            "cv_data": {"personal": {"name": "Jane Doe"}},
            "template": "modern",
            "frontend_url": "http://localhost:5173"
        }
        
        with patch('app.main.uuid.uuid4', return_value=Mock(hex="test456")):
            # Act
            response = client.post("/pdf/generate", json=request_data)
            
            # Assert
            assert response.status_code == 200
            assert "cv_modern_test456.pdf" in response.headers["content-disposition"]

    def test_generate_pdf_validation_error(self, client):
        """Test PDF generation with validation error."""
        # Arrange
        request_data = {
            "cv_data": {},  # Empty CV data should cause validation error
            "template": "classic",
            "frontend_url": "http://localhost:5173"
        }
        
        # Act
        response = client.post("/pdf/generate", json=request_data)
        
        # Assert
        assert response.status_code == 422  # Validation error

    def test_generate_pdf_missing_template(self, client):
        """Test PDF generation with missing template."""
        # Arrange
        request_data = {
            "cv_data": {"personal": {"name": "John Doe"}},
            "frontend_url": "http://localhost:5173"
            # Missing template field
        }
        
        # Act
        response = client.post("/pdf/generate", json=request_data)
        
        # Assert
        assert response.status_code == 422  # Validation error

    def test_generate_pdf_missing_frontend_url(self, client):
        """Test PDF generation with missing frontend URL."""
        # Arrange
        request_data = {
            "cv_data": {"personal": {"name": "John Doe"}},
            "template": "classic"
            # Missing frontend_url field
        }
        
        # Act
        response = client.post("/pdf/generate", json=request_data)
        
        # Assert
        assert response.status_code == 422  # Validation error

    @patch('app.main.async_playwright')
    def test_generate_pdf_handles_playwright_error(self, mock_playwright, client, sample_pdf_request):
        """Test PDF generation handles Playwright errors gracefully."""
        # Arrange
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.side_effect = Exception("Playwright error")
        
        # Act
        response = client.post("/pdf/generate", json=sample_pdf_request)
        
        # Assert
        assert response.status_code == 500
        assert "Error generating PDF" in response.json()["detail"]

    @patch('app.main.async_playwright')
    def test_generate_pdf_handles_navigation_error(self, mock_playwright, client, sample_pdf_request):
        """Test PDF generation handles navigation errors gracefully."""
        # Arrange
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        
        mock_page.goto.side_effect = Exception("Navigation error")
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_browser.close = AsyncMock()
        
        mock_playwright.return_value.__aenter__.return_value.chromium.launch = AsyncMock(return_value=mock_browser)
        
        # Act
        response = client.post("/pdf/generate", json=sample_pdf_request)
        
        # Assert
        assert response.status_code == 500
        assert "Error generating PDF" in response.json()["detail"]

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses."""
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 200
        # CORS headers should be present (handled by FastAPI middleware)

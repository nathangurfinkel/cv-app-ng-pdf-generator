"""
Pytest configuration and fixtures for PDF Service tests.
Follows Single Responsibility Principle - handles only test configuration.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client for FastAPI application."""
    return TestClient(app)


@pytest.fixture
def sample_cv_data():
    """Sample CV data for testing."""
    return {
        "personal": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "location": "New York, NY"
        },
        "professional_summary": "Experienced software engineer with 5+ years of experience",
        "experience": [
            {
                "title": "Senior Software Engineer",
                "company": "Tech Corp",
                "startDate": "2020-01",
                "endDate": "2023-12",
                "description": "Led development of microservices architecture"
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science in Computer Science",
                "school": "University of Technology",
                "graduationYear": "2019"
            }
        ],
        "skills": {
            "technical": ["Python", "FastAPI", "AWS"],
            "soft": ["Leadership", "Communication"]
        }
    }


@pytest.fixture
def sample_pdf_request():
    """Sample PDF generation request for testing."""
    return {
        "cv_data": {
            "personal": {"name": "John Doe", "email": "john@example.com"},
            "experience": [{"title": "Software Engineer", "company": "Tech Corp"}],
            "education": [{"degree": "Bachelor of Science", "school": "University"}],
            "skills": {"technical": ["Python", "FastAPI"], "soft": ["Communication"]}
        },
        "template": "classic",
        "frontend_url": "http://localhost:5173"
    }


@pytest.fixture
def mock_playwright():
    """Mock Playwright for testing."""
    with patch('app.main.async_playwright') as mock_playwright:
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_pdf_buffer = b"fake pdf content"
        
        mock_page.pdf = AsyncMock(return_value=mock_pdf_buffer)
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_browser.close = AsyncMock()
        
        mock_playwright.return_value.__aenter__.return_value.chromium.launch = AsyncMock(return_value=mock_browser)
        
        yield {
            'browser': mock_browser,
            'page': mock_page,
            'pdf_buffer': mock_pdf_buffer
        }


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

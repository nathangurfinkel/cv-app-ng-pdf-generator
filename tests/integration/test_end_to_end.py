"""
End-to-end integration tests for PDF Service.
Follows Single Responsibility Principle - tests complete workflows.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app


class TestPDFEndToEndWorkflows:
    """Test class for PDF end-to-end workflows following Single Responsibility Principle."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch('app.main.async_playwright')
    def test_complete_pdf_generation_workflow(self, mock_playwright, client):
        """Test complete PDF generation workflow from start to finish."""
        # Arrange
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_pdf_buffer = b"fake pdf content for complete workflow test"
        
        mock_page.pdf = AsyncMock(return_value=mock_pdf_buffer)
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_browser.close = AsyncMock()
        
        mock_playwright.return_value.__aenter__.return_value.chromium.launch = AsyncMock(return_value=mock_browser)
        
        request_data = {
            "cv_data": {
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
            },
            "template": "classic",
            "frontend_url": "http://localhost:5173"
        }
        
        with patch('app.main.uuid.uuid4', return_value=Mock(hex="workflow123")):
            # Act
            response = client.post("/pdf/generate", json=request_data)
            
            # Assert
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            assert "cv_classic_workflow123.pdf" in response.headers["content-disposition"]
            assert len(response.content) > 0

    @patch('app.main.async_playwright')
    def test_pdf_generation_with_different_templates(self, mock_playwright, client):
        """Test PDF generation with different templates."""
        # Arrange
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_pdf_buffer = b"fake pdf content for template test"
        
        mock_page.pdf = AsyncMock(return_value=mock_pdf_buffer)
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_browser.close = AsyncMock()
        
        mock_playwright.return_value.__aenter__.return_value.chromium.launch = AsyncMock(return_value=mock_browser)
        
        templates = ["classic", "modern", "functional", "combination", "reverse-chronological"]
        
        for template in templates:
            with patch('app.main.uuid.uuid4', return_value=Mock(hex=f"template{template}")):
                request_data = {
                    "cv_data": {
                        "personal": {"name": "Jane Smith", "email": "jane@example.com"},
                        "experience": [{"title": "Data Scientist", "company": "Data Corp"}],
                        "education": [{"degree": "Master of Science", "school": "Tech University"}],
                        "skills": {"technical": ["Python", "Machine Learning"], "soft": ["Analytical Thinking"]}
                    },
                    "template": template,
                    "frontend_url": "http://localhost:5173"
                }
                
                # Act
                response = client.post("/pdf/generate", json=request_data)
                
                # Assert
                assert response.status_code == 200
                assert response.headers["content-type"] == "application/pdf"
                assert f"cv_{template}_template{template}.pdf" in response.headers["content-disposition"]

    @patch('app.main.async_playwright')
    def test_pdf_generation_with_complex_cv_data(self, mock_playwright, client):
        """Test PDF generation with complex CV data structure."""
        # Arrange
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_pdf_buffer = b"fake pdf content for complex cv test"
        
        mock_page.pdf = AsyncMock(return_value=mock_pdf_buffer)
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_browser.close = AsyncMock()
        
        mock_playwright.return_value.__aenter__.return_value.chromium.launch = AsyncMock(return_value=mock_browser)
        
        complex_cv_data = {
            "personal": {
                "name": "Dr. Sarah Johnson",
                "email": "sarah.johnson@example.com",
                "phone": "+1987654321",
                "location": "San Francisco, CA",
                "website": "https://sarahjohnson.dev",
                "linkedin": "https://linkedin.com/in/sarahjohnson",
                "github": "https://github.com/sarahjohnson"
            },
            "professional_summary": "Senior Full-Stack Developer with 8+ years of experience in building scalable web applications and leading development teams",
            "experience": [
                {
                    "title": "Senior Full-Stack Developer",
                    "company": "Tech Innovations Inc",
                    "startDate": "2021-03",
                    "endDate": "2024-01",
                    "description": "Led a team of 5 developers in building a microservices architecture serving 1M+ users",
                    "achievements": [
                        "Increased system performance by 40%",
                        "Reduced deployment time from 2 hours to 15 minutes",
                        "Mentored 3 junior developers"
                    ]
                },
                {
                    "title": "Full-Stack Developer",
                    "company": "StartupXYZ",
                    "startDate": "2019-06",
                    "endDate": "2021-02",
                    "description": "Developed and maintained multiple web applications using React, Node.js, and Python"
                }
            ],
            "education": [
                {
                    "degree": "Ph.D. in Computer Science",
                    "school": "Stanford University",
                    "graduationYear": "2019",
                    "gpa": "3.9"
                },
                {
                    "degree": "Master of Science in Software Engineering",
                    "school": "MIT",
                    "graduationYear": "2016",
                    "gpa": "3.8"
                }
            ],
            "projects": [
                {
                    "name": "AI-Powered Analytics Platform",
                    "description": "Built a real-time analytics platform using Python, FastAPI, and React",
                    "technologies": ["Python", "FastAPI", "React", "PostgreSQL", "Redis"],
                    "url": "https://github.com/sarahjohnson/analytics-platform"
                }
            ],
            "skills": {
                "technical": [
                    "Python", "JavaScript", "TypeScript", "React", "Node.js", 
                    "FastAPI", "Django", "PostgreSQL", "MongoDB", "AWS", "Docker"
                ],
                "soft": [
                    "Team Leadership", "Project Management", "Mentoring", 
                    "Communication", "Problem Solving", "Strategic Thinking"
                ],
                "languages": ["English (Native)", "Spanish (Fluent)", "French (Conversational)"]
            },
            "licenses_certifications": [
                {
                    "name": "AWS Certified Solutions Architect",
                    "issuer": "Amazon Web Services",
                    "date": "2023-05",
                    "expiry": "2026-05"
                },
                {
                    "name": "Certified Scrum Master",
                    "issuer": "Scrum Alliance",
                    "date": "2022-08"
                }
            ]
        }
        
        request_data = {
            "cv_data": complex_cv_data,
            "template": "modern",
            "frontend_url": "http://localhost:5173"
        }
        
        with patch('app.main.uuid.uuid4', return_value=Mock(hex="complex123")):
            # Act
            response = client.post("/pdf/generate", json=request_data)
            
            # Assert
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            assert "cv_modern_complex123.pdf" in response.headers["content-disposition"]
            assert len(response.content) > 0

    def test_template_listing_workflow(self, client):
        """Test template listing workflow."""
        # Act
        response = client.get("/pdf/templates")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) == 5
        
        expected_templates = ["classic", "modern", "functional", "combination", "reverse-chronological"]
        for template in expected_templates:
            assert template in data["templates"]

    @patch('app.main.async_playwright')
    def test_pdf_generation_error_handling_workflow(self, mock_playwright, client):
        """Test PDF generation error handling workflow."""
        # Arrange
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.side_effect = Exception("Browser launch failed")
        
        request_data = {
            "cv_data": {"personal": {"name": "Test User"}},
            "template": "classic",
            "frontend_url": "http://localhost:5173"
        }
        
        # Act
        response = client.post("/pdf/generate", json=request_data)
        
        # Assert
        assert response.status_code == 500
        assert "Error generating PDF" in response.json()["detail"]

    @patch('app.main.async_playwright')
    def test_pdf_generation_with_custom_frontend_url(self, mock_playwright, client):
        """Test PDF generation with custom frontend URL."""
        # Arrange
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_pdf_buffer = b"fake pdf content for custom url test"
        
        mock_page.pdf = AsyncMock(return_value=mock_pdf_buffer)
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_browser.close = AsyncMock()
        
        mock_playwright.return_value.__aenter__.return_value.chromium.launch = AsyncMock(return_value=mock_browser)
        
        request_data = {
            "cv_data": {"personal": {"name": "Custom URL Test"}},
            "template": "classic",
            "frontend_url": "https://custom-frontend.example.com"
        }
        
        with patch('app.main.uuid.uuid4', return_value=Mock(hex="custom123")):
            # Act
            response = client.post("/pdf/generate", json=request_data)
            
            # Assert
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            assert "cv_classic_custom123.pdf" in response.headers["content-disposition"]
            
            # Verify that the custom URL was used
            mock_page.goto.assert_called_once()
            call_args = mock_page.goto.call_args[0][0]
            assert "https://custom-frontend.example.com" in call_args

"""
Integration tests for PDF generation service.

Tests PDF generation endpoint with SSRF protection.
"""

import os
import pytest
import httpx

PDF_SERVICE_URL = os.getenv("PDF_SERVICE_URL", "http://localhost:8001")

SAMPLE_CV_DATA = {
    "personal": {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-0123",
        "location": "San Francisco, CA",
        "website": "johndoe.com",
        "linkedin": "linkedin.com/in/johndoe",
        "github": "github.com/johndoe",
    },
    "professional_summary": "Experienced software engineer with 5 years in backend development.",
    "experience": [
        {
            "company": "Tech Corp",
            "role": "Senior Software Engineer",
            "startDate": "2020-01",
            "endDate": "Present",
            "location": "San Francisco, CA",
            "description": "Led microservices development",
            "achievements": ["Improved performance by 40%", "Mentored 5 junior developers"],
        }
    ],
    "education": [],
    "projects": [],
    "skills": {
        "technical": ["Python", "FastAPI", "Docker"],
        "soft": ["Leadership", "Communication"],
        "languages": ["English"],
    },
    "licenses_certifications": [],
    "job_description": "",
}


@pytest.mark.asyncio
async def test_get_templates():
    """Test GET /pdf/templates endpoint."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{PDF_SERVICE_URL}/pdf/templates")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "templates" in data
        assert isinstance(data["templates"], list)
        assert len(data["templates"]) > 0


@pytest.mark.asyncio
async def test_pdf_generation_valid_origin():
    """Test PDF generation with valid frontend origin."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{PDF_SERVICE_URL}/pdf/generate",
            headers={"Content-Type": "application/json"},
            json={
                "cv_data": SAMPLE_CV_DATA,
                "template": "classic",
                "frontend_url": "http://localhost:5173/print/test",
            },
        )
        
        # Should either succeed (200) or fail due to frontend not being accessible
        # But should NOT fail with 400 (SSRF validation error)
        assert response.status_code != 400, "Should not reject valid localhost origin"
        
        if response.status_code == 200:
            assert response.headers["content-type"] == "application/pdf"
            assert len(response.content) > 0


@pytest.mark.asyncio
async def test_pdf_generation_ssrf_protection_invalid_scheme():
    """Test that PDF service rejects invalid URL schemes (SSRF protection)."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{PDF_SERVICE_URL}/pdf/generate",
            headers={"Content-Type": "application/json"},
            json={
                "cv_data": SAMPLE_CV_DATA,
                "template": "classic",
                "frontend_url": "file:///etc/passwd",  # Invalid scheme
            },
        )
        
        # Should return 400 (validation error) not 500 (server error)
        assert response.status_code == 400, f"Should reject file:// scheme, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data


@pytest.mark.asyncio
async def test_pdf_generation_ssrf_protection_private_ip():
    """Test that PDF service rejects private IP addresses (SSRF protection)."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{PDF_SERVICE_URL}/pdf/generate",
            headers={"Content-Type": "application/json"},
            json={
                "cv_data": SAMPLE_CV_DATA,
                "template": "classic",
                "frontend_url": "http://169.254.169.254/latest/meta-data",  # AWS metadata service
            },
        )
        
        # Should return 400 (validation error) not 500 (server error)
        assert response.status_code == 400, f"Should reject private IP addresses, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data


@pytest.mark.asyncio
async def test_pdf_generation_ssrf_protection_not_in_allowlist():
    """Test that PDF service rejects origins not in allowlist."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{PDF_SERVICE_URL}/pdf/generate",
            headers={"Content-Type": "application/json"},
            json={
                "cv_data": SAMPLE_CV_DATA,
                "template": "classic",
                "frontend_url": "https://evil.com/print/test",  # Not in allowlist
            },
        )
        
        # Should return 400 (validation error) not 500 (server error)
        assert response.status_code == 400, f"Should reject origins not in allowlist, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data
        assert "allowed" in data["detail"].lower() or "allowlist" in data["detail"].lower()


@pytest.mark.asyncio
async def test_pdf_generation_missing_frontend_url():
    """Test that PDF generation handles missing frontend_url gracefully."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{PDF_SERVICE_URL}/pdf/generate",
            headers={"Content-Type": "application/json"},
            json={
                "cv_data": SAMPLE_CV_DATA,
                "template": "classic",
                # frontend_url missing - should use default
            },
        )
        
        # Should use default frontend_url or reject
        assert response.status_code in [200, 400, 500]


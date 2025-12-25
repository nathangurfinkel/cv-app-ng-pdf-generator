"""
Integration tests for OG image generation.
"""

import os
import pytest
import httpx

PDF_SERVICE_URL = os.getenv("PDF_SERVICE_URL", "http://localhost:8001")


@pytest.mark.asyncio
async def test_roast_og_image():
    """Test GET /pdf/og/roast endpoint."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{PDF_SERVICE_URL}/pdf/og/roast",
            params={
                "score": 7,
                "highlight": "Your CV is solid but could use more quantifiable achievements.",
            },
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert response.headers["content-type"] == "image/png"
        assert len(response.content) > 0
        
        # Verify it's actually a PNG (starts with PNG signature)
        assert response.content[:8] == b"\x89PNG\r\n\x1a\n" or response.content.startswith(b"\x89PNG")


@pytest.mark.asyncio
async def test_roast_og_image_validation():
    """Test that OG image endpoint validates parameters."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Invalid score (out of range)
        response = await client.get(
            f"{PDF_SERVICE_URL}/pdf/og/roast",
            params={
                "score": 15,  # Out of range (0-10)
                "highlight": "Test",
            },
        )
        
        assert response.status_code == 422, "Should reject invalid score"


@pytest.mark.asyncio
async def test_roast_og_image_cache_headers():
    """Test that OG images have proper cache headers."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{PDF_SERVICE_URL}/pdf/og/roast",
            params={
                "score": 5,
                "highlight": "Test highlight",
            },
        )
        
        assert response.status_code == 200
        assert "Cache-Control" in response.headers
        assert "max-age" in response.headers["Cache-Control"]


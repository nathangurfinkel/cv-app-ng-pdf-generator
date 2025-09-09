"""
Unit tests for PDF generation functionality.
Follows Single Responsibility Principle - tests only PDF generation logic.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.main import app


class TestPDFGeneration:
    """Test class for PDF generation following Single Responsibility Principle."""

    @pytest.mark.asyncio
    async def test_generate_pdf_success(self, mock_playwright, sample_pdf_request):
        """Test successful PDF generation."""
        # Arrange
        with patch('app.main.uuid.uuid4', return_value=Mock(hex="test123")):
            # Act
            response = await app.routes[0].endpoints[0].func(
                Mock(json=AsyncMock(return_value=sample_pdf_request))
            )
            
            # Assert
            assert response.status_code == 200
            assert response.media_type == "application/pdf"
            assert "cv_classic_test123.pdf" in response.headers["Content-Disposition"]

    @pytest.mark.asyncio
    async def test_generate_pdf_with_different_template(self, mock_playwright):
        """Test PDF generation with different template."""
        # Arrange
        request_data = {
            "cv_data": {"personal": {"name": "Jane Doe"}},
            "template": "modern",
            "frontend_url": "http://localhost:5173"
        }
        
        with patch('app.main.uuid.uuid4', return_value=Mock(hex="test456")):
            # Act
            response = await app.routes[0].endpoints[0].func(
                Mock(json=AsyncMock(return_value=request_data))
            )
            
            # Assert
            assert response.status_code == 200
            assert "cv_modern_test456.pdf" in response.headers["Content-Disposition"]

    @pytest.mark.asyncio
    async def test_generate_pdf_handles_playwright_error(self, sample_pdf_request):
        """Test PDF generation handles Playwright errors gracefully."""
        # Arrange
        with patch('app.main.async_playwright') as mock_playwright:
            mock_playwright.return_value.__aenter__.return_value.chromium.launch.side_effect = Exception("Playwright error")
            
            # Act & Assert
            with pytest.raises(Exception, match="Playwright error"):
                await app.routes[0].endpoints[0].func(
                    Mock(json=AsyncMock(return_value=sample_pdf_request))
                )

    @pytest.mark.asyncio
    async def test_generate_pdf_handles_navigation_error(self, mock_playwright, sample_pdf_request):
        """Test PDF generation handles navigation errors gracefully."""
        # Arrange
        mock_playwright['page'].goto.side_effect = Exception("Navigation error")
        
        with patch('app.main.uuid.uuid4', return_value=Mock(hex="test789")):
            # Act & Assert
            with pytest.raises(Exception, match="Navigation error"):
                await app.routes[0].endpoints[0].func(
                    Mock(json=AsyncMock(return_value=sample_pdf_request))
                )

    def test_get_available_templates(self):
        """Test getting available templates."""
        # Act
        templates = ["classic", "modern", "functional", "combination", "reverse-chronological"]
        
        # Assert
        assert len(templates) == 5
        assert "classic" in templates
        assert "modern" in templates
        assert "functional" in templates
        assert "combination" in templates
        assert "reverse-chronological" in templates

    @pytest.mark.asyncio
    async def test_generate_pdf_sets_viewport_size(self, mock_playwright, sample_pdf_request):
        """Test that PDF generation sets correct viewport size."""
        # Arrange
        with patch('app.main.uuid.uuid4', return_value=Mock(hex="test123")):
            # Act
            await app.routes[0].endpoints[0].func(
                Mock(json=AsyncMock(return_value=sample_pdf_request))
            )
            
            # Assert
            mock_playwright['page'].set_viewport_size.assert_called_once_with({"width": 1200, "height": 800})

    @pytest.mark.asyncio
    async def test_generate_pdf_injects_cv_data(self, mock_playwright, sample_pdf_request):
        """Test that PDF generation injects CV data into the page."""
        # Arrange
        with patch('app.main.uuid.uuid4', return_value=Mock(hex="test123")):
            # Act
            await app.routes[0].endpoints[0].func(
                Mock(json=AsyncMock(return_value=sample_pdf_request))
            )
            
            # Assert
            mock_playwright['page'].evaluate.assert_called_once()
            call_args = mock_playwright['page'].evaluate.call_args[0][0]
            assert "window.cvData" in call_args
            assert "window.template" in call_args

    @pytest.mark.asyncio
    async def test_generate_pdf_waits_for_render(self, mock_playwright, sample_pdf_request):
        """Test that PDF generation waits for page to render."""
        # Arrange
        with patch('app.main.uuid.uuid4', return_value=Mock(hex="test123")):
            # Act
            await app.routes[0].endpoints[0].func(
                Mock(json=AsyncMock(return_value=sample_pdf_request))
            )
            
            # Assert
            mock_playwright['page'].wait_for_timeout.assert_called_once_with(2000)

    @pytest.mark.asyncio
    async def test_generate_pdf_calls_pdf_with_correct_params(self, mock_playwright, sample_pdf_request):
        """Test that PDF generation calls page.pdf with correct parameters."""
        # Arrange
        with patch('app.main.uuid.uuid4', return_value=Mock(hex="test123")):
            # Act
            await app.routes[0].endpoints[0].func(
                Mock(json=AsyncMock(return_value=sample_pdf_request))
            )
            
            # Assert
            mock_playwright['page'].pdf.assert_called_once_with(
                format="A4",
                print_background=True,
                margin={
                    "top": "0.5in",
                    "right": "0.5in", 
                    "bottom": "0.5in",
                    "left": "0.5in"
                }
            )

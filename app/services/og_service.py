"""
Open Graph (OG) Image Generation Service.
Uses Playwright to render HTML templates to PNG images for social sharing.
"""
from playwright.async_api import async_playwright
from pathlib import Path
from typing import Optional
from ..utils.debug import print_step


class OGService:
    """Service for generating Open Graph images for social media sharing."""
    
    def __init__(self):
        """Initialize the OG service with template paths."""
        self.templates_dir = Path(__file__).parent.parent.parent / "templates"
        self.roast_template_path = self.templates_dir / "roast_og_template.html"
    
    async def generate_roast_image(
        self, 
        score: int, 
        highlight: str
    ) -> bytes:
        """
        Generate an Open Graph image for a roast result.
        
        Args:
            score: Roast score (0-10)
            highlight: Key highlight text to display
            
        Returns:
            PNG image bytes optimized for Open Graph (1200x630)
        """
        print_step("OG Image Generation", {
            "score": score,
            "highlight_length": len(highlight)
        }, "input")
        
        try:
            # Load template
            if not self.roast_template_path.exists():
                raise FileNotFoundError(f"Template not found: {self.roast_template_path}")
            
            template_html = self.roast_template_path.read_text(encoding='utf-8')
            
            # Replace placeholders
            # Escape HTML in highlight to prevent XSS
            safe_highlight = (
                highlight
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;')
            )
            
            # Truncate highlight if too long (for visual balance)
            if len(safe_highlight) > 200:
                safe_highlight = safe_highlight[:197] + "..."
            
            rendered_html = template_html.replace("{{ score }}", str(score))
            rendered_html = rendered_html.replace("{{ highlight }}", safe_highlight)
            
            # Generate image using Playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu'
                    ]
                )
                
                page = await browser.new_page()
                
                # Set viewport to exact OG image dimensions
                await page.set_viewport_size({"width": 1200, "height": 630})
                
                # Load HTML content
                await page.set_content(rendered_html)
                
                # Wait for fonts and rendering
                await page.wait_for_timeout(500)
                
                # Take screenshot
                screenshot_bytes = await page.screenshot(
                    type='png',
                    full_page=False
                )
                
                await browser.close()
                
                print_step("OG Image Generated", {
                    "image_size_bytes": len(screenshot_bytes)
                }, "output")
                
                return screenshot_bytes
                
        except Exception as e:
            print_step("OG Image Generation Error", str(e), "error")
            raise Exception(f"Failed to generate OG image: {str(e)}")



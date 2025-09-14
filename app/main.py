"""
PDF Generation Service FastAPI application entry point for AWS Fargate.
This service handles PDF generation using Playwright for pixel-perfect rendering.
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from playwright.async_api import async_playwright
import asyncio
import json
import uuid
import os
from .core.config import settings
from .utils.debug import print_step

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application for PDF service.
    
    Returns:
        Configured FastAPI application
    """
    # Create FastAPI app
    app = FastAPI(
        title="CV Builder PDF Service",
        version="1.0.0",
        description="PDF generation service using Playwright for pixel-perfect CV rendering",
        debug=settings.DEBUG
    )
    
    # Add CORS middleware
    print_step("CORS Configuration", {"origins": settings.CORS_ORIGINS}, "input")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALL_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )
    print_step("FastAPI App Initialization", "FastAPI app and CORS middleware configured", "output")
    
    # Health check endpoint
    @app.get("/")
    def read_root():
        return {"status": "CV Builder PDF Service is online", "service": "pdf"}
    
    @app.get("/health")
    def health_check():
        return {"status": "healthy", "service": "pdf"}
    
    @app.get("/pdf/templates")
    async def get_available_templates():
        """
        Get list of available PDF templates.
        """
        try:
            templates = [
                "classic",
                "modern", 
                "functional",
                "combination",
                "reverse-chronological"
            ]
            return {"templates": templates}
        except Exception as e:
            print_step("Template List Error", str(e), "error")
            raise HTTPException(status_code=500, detail=f"Error getting templates: {e}")
    
    @app.post("/pdf/generate")
    async def generate_pdf(request: Request):
        """
        Generate a PDF from CV data using Playwright for pixel-perfect rendering.
        """
        try:
            # Parse the request body
            body = await request.json()
            cv_data = body.get("cv_data", {})
            template = body.get("template", "classic")
            frontend_url = body.get("frontend_url", os.getenv("FRONTEND_URL", "http://localhost:5173"))
            
            print_step("PDF Generation Request", {
                "template": template,
                "frontend_url": frontend_url,
                "cv_data_keys": list(cv_data.keys()) if cv_data else []
            }, "input")
            
            # Generate a unique ID for this PDF generation
            unique_id = str(uuid.uuid4())
            
            # For now, we'll use a simple approach where we pass the data directly
            # In production, you might want to store this in a database temporarily
            print_url = f"{frontend_url}/print/{unique_id}"
            
            # Launch Playwright and generate PDF
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
                
                # Set viewport for consistent rendering
                await page.set_viewport_size({"width": 1200, "height": 800})
                
                # Navigate to the print page
                await page.goto(print_url, wait_until="networkidle")
                
                # Inject the CV data into the page
                await page.evaluate(f"""
                    window.cvData = {json.dumps(cv_data)};
                    window.template = '{template}';
                """)
                
                # Wait a bit for the page to render
                await page.wait_for_timeout(2000)
                
                # Generate PDF
                pdf_buffer = await page.pdf(
                    format="A4",
                    print_background=True,
                    margin={
                        "top": "0.5in",
                        "right": "0.5in", 
                        "bottom": "0.5in",
                        "left": "0.5in"
                    }
                )
                
                await browser.close()
                
                print_step("PDF Generation Complete", {
                    "pdf_size_bytes": len(pdf_buffer),
                    "template": template
                }, "output")
                
                # Return the PDF as a response
                return Response(
                    content=pdf_buffer,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f"attachment; filename=cv_{template}_{unique_id[:8]}.pdf"
                    }
                )
                
        except Exception as e:
            print_step("PDF Generation Error", str(e), "error")
            raise HTTPException(status_code=500, detail=f"Error generating PDF: {e}")
    
    return app

# Create the app instance
app = create_app()

# Application startup message
print_step("PDF Service Startup", "CV Builder PDF Service is ready to serve requests!", "output")
print("\n" + "="*80)
print("📄 CV BUILDER PDF SERVICE STARTED SUCCESSFULLY")
print("="*80)
print("📋 Available Endpoints:")
print("   • GET  /                    - Health check")
print("   • GET  /health              - Health check")
print("   • GET  /pdf/templates       - Get available PDF templates")
print("   • POST /pdf/generate        - Generate PDF from CV data")
print("="*80)
print("🔧 Debug Mode: ENABLED - Detailed logging will be shown for each request")
print("="*80 + "\n")

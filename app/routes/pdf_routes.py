"""
PDF generation API routes.
"""
from fastapi import APIRouter, HTTPException
from ..models.cv_models import PDFRequest
from ..services.pdf_service import PDFService
from ..utils.debug import print_step

router = APIRouter(prefix="/pdf", tags=["PDF"])

# Initialize PDF service
pdf_service = PDFService()

@router.post("/generate")
async def generate_pdf(request: PDFRequest):
    """
    Generate a PDF from CV data using the specified template.
    """
    try:
        return await pdf_service.generate_pdf(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print_step("PDF Generation Error", str(e), "error")
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {e}")

@router.get("/templates")
async def get_available_templates():
    """
    Get list of available PDF templates.
    """
    try:
        templates = pdf_service.get_available_templates()
        return {"templates": templates}
    except Exception as e:
        print_step("Template List Error", str(e), "error")
        raise HTTPException(status_code=500, detail=f"Error getting templates: {e}")

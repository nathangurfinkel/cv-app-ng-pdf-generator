"""
PDF generation service using WeasyPrint and Jinja2.
"""
import os
import jinja2
from weasyprint import HTML
from fastapi.responses import Response
from ..core.config import settings
from ..utils.debug import print_step
from ..models.cv_models import PDFRequest

class PDFService:
    """Service for PDF generation operations."""
    
    def __init__(self):
        """Initialize the PDF service."""
        self.template_env = None
        self._initialize_templates()
    
    def _initialize_templates(self) -> None:
        """Initialize Jinja2 template environment."""
        print_step("Jinja2 Template Setup", "Initializing template environment", "input")
        
        template_loader = jinja2.FileSystemLoader(searchpath=settings.TEMPLATES_DIR)
        self.template_env = jinja2.Environment(loader=template_loader)
        
        # Add custom filters
        def month_name_filter(month_num):
            """Convert month number to month name."""
            if not month_num:
                return ""
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            try:
                return month_names[int(month_num) - 1]
            except (ValueError, IndexError):
                return str(month_num)
        
        self.template_env.filters['month_name'] = month_name_filter
        
        print_step("Jinja2 Template Setup", "Template environment initialized with custom filters", "output")
    
    async def generate_pdf(self, request: PDFRequest) -> Response:
        """
        Generate a PDF from CV data using the specified template.
        
        Args:
            request: PDF generation request
            
        Returns:
            PDF response
        """
        print_step("PDF Generation Request", {
            "template_id": request.templateId,
            "personal_name": request.data.personal.name,
            "experience_count": len(request.data.experience),
            "education_count": len(request.data.education)
        }, "input")
        
        try:
            # Check if template exists
            template_file = f"{request.templateId}.html"
            template_path = os.path.join(settings.TEMPLATES_DIR, template_file)
            
            if not os.path.exists(template_path):
                print_step("PDF Generation Error", f"Template not found: {template_file}", "error")
                raise ValueError(f"Template '{request.templateId}' not found")
            
            print_step("Template Loading", {"template_file": template_file}, "input")
            template = self.template_env.get_template(template_file)
            print_step("Template Loading", "Template loaded successfully", "output")
            
            # Render the HTML with the user's data
            print_step("HTML Rendering", {
                "data_keys": list(request.data.model_dump().keys())
            }, "input")
            
            html_content = template.render(request.data.model_dump())
            print_step("HTML Rendering", {"html_length": len(html_content)}, "output")
            
            # Generate PDF from the rendered HTML
            print_step("PDF Generation", {"html_length": len(html_content)}, "input")
            pdf_bytes = HTML(string=html_content).write_pdf()
            print_step("PDF Generation", {"pdf_size_bytes": len(pdf_bytes)}, "output")
            
            # Set headers for file download
            headers = {
                'Content-Disposition': f'attachment; filename="cv_{request.data.personal.name.replace(" ", "_")}.pdf"'
            }
            
            print_step("PDF Generation Complete", {
                "pdf_size_kb": round(len(pdf_bytes) / 1024, 2),
                "filename": f"cv_{request.data.personal.name.replace(' ', '_')}.pdf"
            }, "output")
            
            return Response(pdf_bytes, headers=headers, media_type='application/pdf')
            
        except Exception as e:
            print_step("PDF Generation Error", str(e), "error")
            raise ValueError(f"Error generating PDF: {e}")
    
    def get_available_templates(self) -> list:
        """
        Get list of available templates.
        
        Returns:
            List of template names
        """
        if not os.path.exists(settings.TEMPLATES_DIR):
            return []
        
        templates = []
        for file in os.listdir(settings.TEMPLATES_DIR):
            if file.endswith('.html'):
                template_name = file[:-5]  # Remove .html extension
                templates.append(template_name)
        
        return templates

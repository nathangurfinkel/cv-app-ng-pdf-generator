"""
Open Graph (OG) Image Generation Routes.
Generates dynamic social media preview images.
"""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import Response
from ..services.og_service import OGService
from ..utils.debug import print_step

router = APIRouter(prefix="/og", tags=["og"])


@router.get("/roast")
async def generate_roast_og_image(
    score: int = Query(..., ge=0, le=10, description="Roast score out of 10"),
    highlight: str = Query(..., max_length=500, description="Key highlight text to display")
):
    """
    Generate a dynamic Open Graph image for roast shares.
    
    Returns a PNG image (1200x630) optimized for social media platforms.
    Images are suitable for Twitter, LinkedIn, Facebook, etc.
    
    Args:
        score: The roast score (0-10)
        highlight: A short text highlight from the roast
        
    Returns:
        PNG image with Cache-Control headers for 7-day caching
    """
    print_step("OG Roast Image Request", {
        "score": score,
        "highlight_length": len(highlight)
    }, "input")
    
    try:
        og_service = OGService()
        
        image_bytes = await og_service.generate_roast_image(
            score=score,
            highlight=highlight
        )
        
        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=604800, immutable",  # Cache for 7 days
                "Content-Disposition": "inline; filename=roast-og.png"
            }
        )
        
    except Exception as e:
        print_step("OG Image Generation Failed", str(e), "error")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate OG image: {str(e)}"
        )



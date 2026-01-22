"""
Idea Generation API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

try:
    from services.idea_generator import (
        generate_ideas,
        is_idea_gen_configured
    )
    IDEA_GEN_SERVICE_AVAILABLE = True
except ImportError:
    IDEA_GEN_SERVICE_AVAILABLE = False
    generate_ideas = None

router = APIRouter()


class IdeaGenRequest(BaseModel):
    notebook_ids: Optional[List[str]] = None
    domain: Optional[str] = None
    count: int = 5
    idea_type: str = "research"  # research, project, essay, presentation


@router.post("/generate")
async def generate_ideas_endpoint(request: IdeaGenRequest):
    """Generate research/project ideas from notebooks or domain"""
    if not IDEA_GEN_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Idea generator service not available")
    
    if not is_idea_gen_configured():
        raise HTTPException(status_code=503, detail="Idea generator not configured. OpenAI API key required.")
    
    try:
        result = generate_ideas(
            notebook_ids=request.notebook_ids,
            domain=request.domain,
            count=request.count,
            idea_type=request.idea_type
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate ideas"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating ideas: {str(e)}")







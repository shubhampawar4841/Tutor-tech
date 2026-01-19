"""
Co-Writer API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

try:
    from services.cowriter_service import (
        rewrite_text,
        shorten_text,
        expand_text,
        narrate_text,
        is_cowriter_configured
    )
    COWRITER_SERVICE_AVAILABLE = True
except ImportError:
    COWRITER_SERVICE_AVAILABLE = False
    rewrite_text = None
    shorten_text = None
    expand_text = None
    narrate_text = None

router = APIRouter()


class RewriteRequest(BaseModel):
    text: str
    instruction: str
    use_rag: bool = False
    knowledge_base_id: Optional[str] = None


class NarrateRequest(BaseModel):
    text: str
    voice: str = "default"


@router.post("/rewrite")
async def rewrite_text_endpoint(request: RewriteRequest):
    """Rewrite text with AI"""
    if not COWRITER_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Co-writer service not available")
    
    if not is_cowriter_configured():
        raise HTTPException(status_code=503, detail="Co-writer service not configured. OpenAI API key required.")
    
    try:
        result = await rewrite_text(
            text=request.text,
            instruction=request.instruction,
            use_rag=request.use_rag,
            knowledge_base_id=request.knowledge_base_id
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to rewrite text"))
        
        return {
            "original": result.get("original"),
            "rewritten": result.get("rewritten"),
            "status": result.get("status", "completed")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rewriting text: {str(e)}")


@router.post("/shorten")
async def shorten_text_endpoint(request: RewriteRequest):
    """Shorten text"""
    if not COWRITER_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Co-writer service not available")
    
    if not is_cowriter_configured():
        raise HTTPException(status_code=503, detail="Co-writer service not configured. OpenAI API key required.")
    
    try:
        result = await shorten_text(
            text=request.text,
            instruction=request.instruction or "Summarize and make it concise"
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to shorten text"))
        
        return {
            "original": result.get("original"),
            "shortened": result.get("rewritten"),  # shorten_text returns "rewritten" key
            "status": result.get("status", "completed")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error shortening text: {str(e)}")


@router.post("/expand")
async def expand_text_endpoint(request: RewriteRequest):
    """Expand text"""
    if not COWRITER_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Co-writer service not available")
    
    if not is_cowriter_configured():
        raise HTTPException(status_code=503, detail="Co-writer service not configured. OpenAI API key required.")
    
    try:
        result = await expand_text(
            text=request.text,
            instruction=request.instruction or "Expand with more details and explanations"
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to expand text"))
        
        return {
            "original": result.get("original"),
            "expanded": result.get("rewritten"),  # expand_text returns "rewritten" key
            "status": result.get("status", "completed")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error expanding text: {str(e)}")


@router.post("/narrate")
async def narrate_text_endpoint(request: NarrateRequest):
    """Generate audio narration"""
    if not COWRITER_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Co-writer service not available")
    
    try:
        result = await narrate_text(
            text=request.text,
            voice=request.voice
        )
        
        return {
            "audio_url": result.get("audio_url"),
            "status": result.get("status", "completed"),
            "message": result.get("message", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error narrating text: {str(e)}")











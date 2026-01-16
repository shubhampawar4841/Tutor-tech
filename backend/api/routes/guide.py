"""
Guided Learning API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()

# Try to import database functions and guide generator
try:
    from database.db import (
        create_guide_session as db_create_guide_session,
        get_guide_session as db_get_guide_session,
        update_guide_session as db_update_guide_session,
        is_supabase_configured
    )
    from services.guide_generator import generate_guide
    USE_DATABASE = is_supabase_configured()
    GUIDE_GENERATOR_AVAILABLE = True
except ImportError:
    USE_DATABASE = False
    GUIDE_GENERATOR_AVAILABLE = False
    db_create_guide_session = None
    db_get_guide_session = None
    db_update_guide_session = None
    generate_guide = None


class GuideStartRequest(BaseModel):
    notebook_ids: List[str]
    max_points: int = 5


@router.post("/start")
async def start_guide(request: GuideStartRequest):
    """
    Start a guided learning session from notebooks
    
    Analyzes notebook content and generates a structured learning guide
    """
    if not USE_DATABASE or not db_create_guide_session:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    if not GUIDE_GENERATOR_AVAILABLE or not generate_guide:
        raise HTTPException(status_code=503, detail="Guide generator not available")
    
    if not request.notebook_ids:
        raise HTTPException(status_code=400, detail="At least one notebook ID is required")
    
    try:
        # Step 1: Generate guide content
        print(f"[GUIDE] Starting guide generation for {len(request.notebook_ids)} notebooks...")
        guide_result = generate_guide(
            notebook_ids=request.notebook_ids,
            max_points=request.max_points
        )
        
        if not guide_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=guide_result.get("error", "Failed to generate guide")
            )
        
        guide_content = guide_result.get("content", {})
        total_steps = guide_content.get("total_steps", request.max_points)
        
        # Step 2: Create guide session in database
        session = db_create_guide_session(
            notebook_ids=request.notebook_ids,
            max_points=request.max_points
        )
        
        # Step 3: Update session with generated content
        session = db_update_guide_session(
            session.get("id"),
            total_steps=total_steps,
            content=guide_content
        )
        
        return {
            "session_id": session.get("id"),
            "status": "active",
            "notebook_ids": request.notebook_ids,
            "current_step": 1,
            "total_steps": total_steps,
            "content": guide_content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to start guide: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error starting guide: {str(e)}")


@router.get("/{session_id}")
async def get_guide_session(session_id: str):
    """Get guided learning session"""
    if not USE_DATABASE or not db_get_guide_session:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        session = db_get_guide_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Guide session not found")
        
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting guide session: {str(e)}")


@router.post("/{session_id}/next")
async def next_step(session_id: str):
    """Move to next step in the guide"""
    if not USE_DATABASE or not db_get_guide_session or not db_update_guide_session:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        session = db_get_guide_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Guide session not found")
        
        current_step = session.get("current_step", 1)
        total_steps = session.get("total_steps", 1)
        
        if current_step >= total_steps:
            # Mark as completed
            session = db_update_guide_session(
                session_id,
                status="completed"
            )
            return {
                "session_id": session_id,
                "current_step": current_step,
                "message": "Guide completed!",
                "completed": True
            }
        
        # Move to next step
        new_step = current_step + 1
        session = db_update_guide_session(
            session_id,
            current_step=new_step
        )
        
        return {
            "session_id": session_id,
            "current_step": new_step,
            "total_steps": total_steps,
            "message": f"Moved to step {new_step}",
            "completed": False
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error moving to next step: {str(e)}")








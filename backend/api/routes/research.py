"""
Deep Research API Routes
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import Optional

try:
    from services.research_service import (
        start_research,
        get_research_status,
        get_research_result,
        is_research_configured
    )
    RESEARCH_SERVICE_AVAILABLE = True
except ImportError:
    RESEARCH_SERVICE_AVAILABLE = False
    start_research = None
    get_research_status = None
    get_research_result = None

router = APIRouter()


class ResearchStartRequest(BaseModel):
    topic: str
    knowledge_base_id: Optional[str] = None
    mode: str = "auto"  # auto or manual
    max_subtopics: int = 5
    execution_mode: str = "series"  # series or parallel


@router.post("/start")
async def start_research_endpoint(request: ResearchStartRequest):
    """Start a research task"""
    if not RESEARCH_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Research service not available")
    
    if not is_research_configured():
        raise HTTPException(status_code=503, detail="Research service not configured. OpenAI API key required.")
    
    try:
        result = await start_research(
            topic=request.topic,
            knowledge_base_id=request.knowledge_base_id,
            mode=request.mode,
            max_subtopics=request.max_subtopics,
            execution_mode=request.execution_mode
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to start research"))
        
        return {
            "research_id": result.get("research_id"),
            "status": result.get("status", "started"),
            "topic": result.get("topic")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting research: {str(e)}")


@router.get("/{research_id}/status")
async def get_research_status_endpoint(research_id: str):
    """Get research status"""
    if not RESEARCH_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Research service not available")
    
    try:
        status = get_research_status(research_id)
        if not status:
            raise HTTPException(status_code=404, detail="Research session not found")
        
        return {
            "research_id": research_id,
            "status": status.get("status", "researching"),
            "phase": status.get("phase", "researching"),
            "progress": status.get("progress", "0%"),
            "current_section": status.get("current_section"),
            "section_index": status.get("section_index"),
            "total_sections": status.get("total_sections")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting research status: {str(e)}")


@router.get("/{research_id}/result")
async def get_research_result_endpoint(research_id: str):
    """Get research report"""
    if not RESEARCH_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Research service not available")
    
    try:
        result = get_research_result(research_id)
        if not result:
            raise HTTPException(status_code=404, detail="Research session not found")
        
        if result.get("status") != "completed":
            return {
                "research_id": research_id,
                "status": result.get("status", "researching"),
                "message": result.get("message", "Research still in progress")
            }
        
        return {
            "research_id": research_id,
            "report": result.get("report", ""),
            "sections": result.get("sections", []),
            "status": "completed"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting research result: {str(e)}")


@router.websocket("/{research_id}/stream")
async def research_stream(websocket: WebSocket, research_id: str):
    """WebSocket stream for real-time research updates"""
    await websocket.accept()
    try:
        import asyncio
        last_status = None
        
        while True:
            # Poll for status updates
            if RESEARCH_SERVICE_AVAILABLE:
                status = get_research_status(research_id)
                if status:
                    current_status = {
                        "type": "progress",
                        "status": status.get("status"),
                        "progress": status.get("progress"),
                        "current_section": status.get("current_section"),
                        "section_index": status.get("section_index"),
                        "total_sections": status.get("total_sections"),
                        "research_id": research_id
                    }
                    
                    # Only send if status changed
                    if current_status != last_status:
                        await websocket.send_json(current_status)
                        last_status = current_status
                        
                        # If completed, send result and close
                        if status.get("status") == "completed":
                            result = get_research_result(research_id)
                            if result:
                                await websocket.send_json({
                                    "type": "completed",
                                    "research_id": research_id,
                                    "report": result.get("report", ""),
                                    "sections": result.get("sections", [])
                                })
                            break
            
            await asyncio.sleep(2)  # Poll every 2 seconds
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e),
            "research_id": research_id
        })











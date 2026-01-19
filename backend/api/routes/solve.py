"""
Solve Module API Routes
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import Optional
import json

try:
    from services.solve_service import solve_problem, is_solve_configured
    SOLVE_SERVICE_AVAILABLE = True
except ImportError:
    SOLVE_SERVICE_AVAILABLE = False
    solve_problem = None

router = APIRouter()


class SolveRequest(BaseModel):
    question: str
    knowledge_base_id: Optional[str] = None
    use_web_search: bool = False
    use_code_execution: bool = True


@router.post("/start")
async def start_solve(request: SolveRequest):
    """Start solving a problem"""
    if not SOLVE_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Solve service not available")
    
    if not is_solve_configured():
        raise HTTPException(status_code=503, detail="Solve service not configured. OpenAI API key required.")
    
    try:
        result = await solve_problem(
            question=request.question,
            knowledge_base_id=request.knowledge_base_id,
            use_web_search=request.use_web_search,
            use_code_execution=request.use_code_execution
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to solve problem"))
        
        return {
            "solve_id": result.get("solve_id"),
            "status": result.get("status", "completed"),
            "question": result.get("question"),
            "solution": result.get("solution"),
            "steps": result.get("steps", []),
            "citations": result.get("citations", []),
            "answer": result.get("answer")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error solving problem: {str(e)}")


@router.get("/{solve_id}/status")
async def get_solve_status(solve_id: str):
    """Get solve status"""
    # For now, solve is synchronous, so status is always completed
    # In future, can implement async solving with status tracking
    return {
        "solve_id": solve_id,
        "status": "completed",
        "progress": "100%"
    }


@router.get("/{solve_id}/result")
async def get_solve_result(solve_id: str):
    """Get solve result"""
    # Results are returned immediately from /start
    # This endpoint is for future async implementation
    return {
        "solve_id": solve_id,
        "status": "completed",
        "message": "Result is returned from /start endpoint"
    }


@router.websocket("/{solve_id}/stream")
async def solve_stream(websocket: WebSocket, solve_id: str):
    """WebSocket stream for real-time solve updates"""
    await websocket.accept()
    try:
        # TODO: Implement actual streaming logic for async solving
        while True:
            data = await websocket.receive_text()
            # Process and send updates
            await websocket.send_json({
                "type": "progress",
                "message": "Processing...",
                "solve_id": solve_id
            })
    except WebSocketDisconnect:
        pass











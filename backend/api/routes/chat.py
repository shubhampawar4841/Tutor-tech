"""
Chat API Routes
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json

try:
    from services.chat_service import (
        create_chat_session,
        get_chat_session,
        send_chat_message,
        list_chat_sessions,
        is_chat_configured
    )
    CHAT_SERVICE_AVAILABLE = True
except ImportError:
    CHAT_SERVICE_AVAILABLE = False
    create_chat_session = None
    get_chat_session = None
    send_chat_message = None
    list_chat_sessions = None

router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    knowledge_base_id: Optional[str] = None
    use_rag: bool = False
    use_web_search: bool = False


class ChatSession(BaseModel):
    session_id: str
    messages: List[dict]


@router.get("/sessions")
async def list_sessions():
    """List all chat sessions"""
    if not CHAT_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Chat service not available")
    
    try:
        result = list_chat_sessions()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")


@router.post("/sessions")
async def create_session():
    """Create a new chat session"""
    if not CHAT_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Chat service not available")
    
    if not is_chat_configured():
        raise HTTPException(status_code=503, detail="Chat service not configured. OpenAI API key required.")
    
    try:
        session = create_chat_session()
        return {
            "session_id": session["session_id"],
            "created_at": session["created_at"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get chat session messages"""
    if not CHAT_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Chat service not available")
    
    try:
        session = get_chat_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session_id,
            "messages": session.get("messages", [])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session: {str(e)}")


@router.post("/sessions/{session_id}/message")
async def send_message(session_id: str, message: ChatMessage):
    """Send a message in chat session"""
    if not CHAT_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Chat service not available")
    
    if not is_chat_configured():
        raise HTTPException(status_code=503, detail="Chat service not configured. OpenAI API key required.")
    
    try:
        result = await send_chat_message(
            session_id=session_id,
            message=message.message,
            knowledge_base_id=message.knowledge_base_id,
            use_rag=message.use_rag,
            use_web_search=message.use_web_search
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to send message"))
        
        return {
            "session_id": session_id,
            "response": result.get("response"),
            "citations": result.get("citations"),
            "status": result.get("status", "completed")
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[CHAT API] Error sending message: {e}")
        print(f"[CHAT API] Traceback: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")


@router.websocket("/sessions/{session_id}/stream")
async def chat_stream(websocket: WebSocket, session_id: str):
    """WebSocket stream for real-time chat"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message and stream response
            if CHAT_SERVICE_AVAILABLE and is_chat_configured():
                result = await send_chat_message(
                    session_id=session_id,
                    message=message_data.get("message", ""),
                    knowledge_base_id=message_data.get("knowledge_base_id"),
                    use_rag=message_data.get("use_rag", False),
                    use_web_search=message_data.get("use_web_search", False)
                )
                
                if result.get("success"):
                    await websocket.send_json({
                        "type": "message",
                        "content": result.get("response", ""),
                        "session_id": session_id
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "content": result.get("error", "Failed to generate response"),
                        "session_id": session_id
                    })
            else:
                await websocket.send_json({
                    "type": "error",
                    "content": "Chat service not available",
                    "session_id": session_id
                })
    except WebSocketDisconnect:
        pass


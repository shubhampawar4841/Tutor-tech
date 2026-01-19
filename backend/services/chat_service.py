"""
Chat Service
Manages chat sessions and generates conversational responses using RAG
"""
import os
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Try to import OpenAI
try:
    from openai import OpenAI
    import httpx
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    httpx = None

# Try to import RAG service
try:
    from services.rag import ask_question
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    ask_question = None

# Try to import database
try:
    from database.db import (
        is_supabase_configured,
        supabase_client
    )
    USE_DATABASE = is_supabase_configured()
except ImportError:
    USE_DATABASE = False
    supabase_client = None

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# In-memory storage for chat sessions (fallback if no database)
chat_sessions: Dict[str, Dict[str, Any]] = {}

# Workaround for httpx compatibility
def create_http_client(timeout=60.0):
    """Create an httpx client compatible with OpenAI library"""
    if not httpx:
        return None
    try:
        return httpx.Client(timeout=timeout)
    except Exception:
        try:
            return httpx.Client()
        except Exception:
            return None


def is_chat_configured() -> bool:
    """Check if chat service is properly configured"""
    return OPENAI_AVAILABLE and OPENAI_API_KEY


def create_chat_session() -> Dict[str, Any]:
    """Create a new chat session"""
    session_id = f"chat_{uuid.uuid4().hex[:12]}"
    session = {
        "session_id": session_id,
        "messages": [],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    if USE_DATABASE:
        try:
            # Store in database if available
            result = supabase_client.table("chat_sessions").insert({
                "id": session_id,
                "messages": [],
                "created_at": session["created_at"],
                "updated_at": session["updated_at"]
            }).execute()
            if result.data:
                return session
        except Exception as e:
            print(f"[CHAT] Database error creating session, using in-memory: {e}")
            import traceback
            traceback.print_exc()
    
    # Fallback to in-memory (always store in memory as backup)
    chat_sessions[session_id] = session
    return session


def get_chat_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get a chat session by ID"""
    if USE_DATABASE:
        try:
            result = supabase_client.table("chat_sessions").select("*").eq("id", session_id).execute()
            if result.data and len(result.data) > 0:
                session_data = result.data[0]
                # Ensure messages is a list
                if "messages" not in session_data or not isinstance(session_data.get("messages"), list):
                    session_data["messages"] = []
                return session_data
        except Exception as e:
            print(f"[CHAT] Database error getting session, using in-memory: {e}")
            import traceback
            traceback.print_exc()
    
    # Fallback to in-memory
    return chat_sessions.get(session_id)


def save_message(session_id: str, role: str, content: str) -> None:
    """Save a message to a chat session"""
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if USE_DATABASE:
        try:
            # Get current session
            session = get_chat_session(session_id)
            if session:
                messages = session.get("messages", [])
                if not isinstance(messages, list):
                    messages = []
                messages.append(message)
                # Update in database
                supabase_client.table("chat_sessions").update({
                    "messages": messages,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", session_id).execute()
                return
        except Exception as e:
            print(f"[CHAT] Database error saving message, using in-memory: {e}")
            import traceback
            traceback.print_exc()
    
    # Fallback to in-memory
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "session_id": session_id,
            "messages": [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    chat_sessions[session_id]["messages"].append(message)
    chat_sessions[session_id]["updated_at"] = datetime.utcnow().isoformat()


async def send_chat_message(
    session_id: str,
    message: str,
    knowledge_base_id: Optional[str] = None,
    use_rag: bool = False,
    use_web_search: bool = False
) -> Dict[str, Any]:
    """
    Send a message in a chat session and get a response
    
    Args:
        session_id: Chat session ID
        message: User message
        knowledge_base_id: Optional knowledge base for RAG
        use_rag: Whether to use RAG for context
        use_web_search: Whether to use web search (not implemented)
    
    Returns:
        Response dictionary with assistant's message
    """
    if not is_chat_configured():
        return {
            "success": False,
            "error": "Chat service not configured. OpenAI API key required."
        }
    
    # Get or create session
    session = get_chat_session(session_id)
    if not session:
        # Try to create session if it doesn't exist
        try:
            session = create_chat_session()
            if session.get("session_id") != session_id:
                # Session ID mismatch, use the one we have
                session_id = session.get("session_id", session_id)
        except Exception as e:
            print(f"[CHAT] Error creating session: {e}")
            return {
                "success": False,
                "error": f"Chat session not found and could not be created: {str(e)}"
            }
    
    # Save user message
    try:
        save_message(session_id, "user", message)
    except Exception as e:
        print(f"[CHAT] Error saving user message: {e}")
        # Continue anyway, message might be saved in memory
    
    try:
        # Get conversation history
        session = get_chat_session(session_id)
        if not session:
            return {
                "success": False,
                "error": "Chat session not found after saving message"
            }
        messages_history = session.get("messages", [])
        # Filter to get only previous messages (exclude the just-added user message)
        if messages_history and messages_history[-1].get("role") == "user" and messages_history[-1].get("content") == message:
            messages_history = messages_history[:-1]
        
        # Build context from RAG if enabled
        context = ""
        citations = []
        if use_rag and knowledge_base_id and RAG_AVAILABLE:
            # ask_question is not async, so don't await it
            rag_result = ask_question(
                question=message,
                kb_id=knowledge_base_id,
                top_k=3,
                threshold=0.3
            )
            if rag_result and rag_result.get("success"):
                context = rag_result.get("answer", "")
                citations = rag_result.get("citations", [])
        
        # Build messages for LLM
        llm_messages = [
            {
                "role": "system",
                "content": "You are a helpful, friendly AI tutor. Answer questions clearly and conversationally. If context is provided, use it to inform your answers."
            }
        ]
        
        # Add context if available
        if context:
            llm_messages.append({
                "role": "system",
                "content": f"Context from knowledge base:\n{context}\n\nUse this context to inform your answer, but keep it conversational."
            })
        
        # Add conversation history (last 10 messages to avoid token limits)
        for msg in messages_history[-10:]:
            llm_messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        # Add current message
        llm_messages.append({
            "role": "user",
            "content": message
        })
        
        # Generate response
        # Set API key via environment variable
        if OPENAI_API_KEY and "OPENAI_API_KEY" not in os.environ:
            os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        
        # Create client
        http_client = create_http_client(timeout=120.0)
        if http_client:
            # When using custom http_client, still need to pass api_key
            client = OpenAI(api_key=OPENAI_API_KEY, http_client=http_client)
        else:
            client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=llm_messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        assistant_message = response.choices[0].message.content
        
        # Save assistant message
        save_message(session_id, "assistant", assistant_message)
        
        return {
            "success": True,
            "session_id": session_id,
            "response": assistant_message,
            "citations": citations if citations else None,
            "status": "completed"
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[CHAT] Error generating response: {e}")
        print(f"[CHAT] Traceback: {error_trace}")
        return {
            "success": False,
            "error": f"Error generating response: {str(e)}"
        }


def list_chat_sessions() -> Dict[str, Any]:
    """List all chat sessions"""
    if USE_DATABASE:
        try:
            # Supabase order syntax
            result = supabase_client.table("chat_sessions").select("*").order("updated_at", desc=True).limit(50).execute()
            return {
                "sessions": result.data or [],
                "total": len(result.data) if result.data else 0
            }
        except Exception as e:
            print(f"[CHAT] Database error, using in-memory: {e}")
            import traceback
            traceback.print_exc()
    
    # Fallback to in-memory
    sessions = list(chat_sessions.values())
    sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return {
        "sessions": sessions[:50],
        "total": len(sessions)
    }


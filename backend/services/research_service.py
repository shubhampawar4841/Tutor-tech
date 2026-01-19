"""
Deep Research Service
Generates comprehensive research reports on topics
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

# In-memory storage for research sessions (fallback)
research_sessions: Dict[str, Dict[str, Any]] = {}

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


def is_research_configured() -> bool:
    """Check if research service is properly configured"""
    return OPENAI_AVAILABLE and OPENAI_API_KEY


async def start_research(
    topic: str,
    knowledge_base_id: Optional[str] = None,
    mode: str = "auto",
    max_subtopics: int = 5,
    execution_mode: str = "series"
) -> Dict[str, Any]:
    """
    Start a research task
    
    Args:
        topic: Research topic
        knowledge_base_id: Optional knowledge base for context
        mode: Research mode (auto/manual)
        max_subtopics: Maximum number of subtopics
        execution_mode: series or parallel
    
    Returns:
        Dictionary with research_id and status
    """
    research_id = f"research_{uuid.uuid4().hex[:12]}"
    
    session = {
        "research_id": research_id,
        "topic": topic,
        "status": "researching",
        "phase": "researching",
        "progress": "0%",
        "subtopics": [],
        "sections": [],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    if USE_DATABASE:
        try:
            result = supabase_client.table("research_sessions").insert({
                "id": research_id,
                "topic": topic,
                "status": "researching",
                "content": {
                    "subtopics": [],
                    "sections": []
                },
                "created_at": session["created_at"],
                "updated_at": session["updated_at"]
            }).execute()
            if result.data:
                return {
                    "success": True,
                    "research_id": research_id,
                    "status": "started",
                    "topic": topic
                }
        except Exception as e:
            print(f"[RESEARCH] Database error, using in-memory: {e}")
    
    # Fallback to in-memory
    research_sessions[research_id] = session
    
    # Start research in background
    import asyncio
    asyncio.create_task(generate_research_report(research_id, topic, knowledge_base_id, max_subtopics))
    
    return {
        "success": True,
        "research_id": research_id,
        "status": "started",
        "topic": topic
    }


async def generate_research_report(
    research_id: str,
    topic: str,
    knowledge_base_id: Optional[str] = None,
    max_subtopics: int = 5
) -> None:
    """Generate research report in background"""
    try:
        # Update status
        update_research_status(research_id, "researching", "0%")
        
        # Get context from knowledge base if available
        context_sections = []
        if knowledge_base_id and RAG_AVAILABLE:
            # Generate subtopics first
            subtopics = await generate_subtopics(topic, max_subtopics)
            
            # Research each subtopic
            for i, subtopic in enumerate(subtopics):
                update_research_status(
                    research_id,
                    "researching",
                    f"{int((i / len(subtopics)) * 80)}%",
                    current_section=subtopic,
                    section_index=i,
                    total_sections=len(subtopics)
                )
                
                # Get information about this subtopic
                if RAG_AVAILABLE:
                    # ask_question is not async, so don't await it
                    rag_result = ask_question(
                        question=f"{topic}: {subtopic}",
                        kb_id=knowledge_base_id,
                        top_k=5,
                        threshold=0.3
                    )
                    if rag_result and rag_result.get("success"):
                        context_sections.append({
                            "subtopic": subtopic,
                            "content": rag_result.get("answer", ""),
                            "citations": rag_result.get("citations", [])
                        })
        else:
            # No knowledge base, generate general research
            subtopics = await generate_subtopics(topic, max_subtopics)
            for i, subtopic in enumerate(subtopics):
                update_research_status(
                    research_id,
                    "researching",
                    f"{int((i / len(subtopics)) * 80)}%",
                    current_section=subtopic,
                    section_index=i,
                    total_sections=len(subtopics)
                )
                
                # Generate content for subtopic
                content = await generate_subtopic_content(topic, subtopic)
                context_sections.append({
                    "subtopic": subtopic,
                    "content": content,
                    "citations": []
                })
        
        # Generate final report
        update_research_status(research_id, "writing", "90%")
        report = await generate_final_report(topic, context_sections)
        
        # Save report
        save_research_result(research_id, report, context_sections)
        update_research_status(research_id, "completed", "100%")
        
    except Exception as e:
        print(f"[RESEARCH] Error generating report: {e}")
        update_research_status(research_id, "error", "0%", error=str(e))


async def generate_subtopics(topic: str, max_count: int = 5) -> List[str]:
    """Generate subtopics for research"""
    if not is_research_configured():
        return [f"{topic} Overview", f"{topic} Details", f"{topic} Applications"]
    
    try:
        http_client = create_http_client()
        client = OpenAI(
            api_key=OPENAI_API_KEY,
            http_client=http_client
        ) if http_client else OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a research assistant. Generate relevant subtopics for research."
                },
                {
                    "role": "user",
                    "content": f"Generate {max_count} relevant subtopics for researching: {topic}\n\nReturn only a JSON array of strings, e.g. [\"subtopic1\", \"subtopic2\"]"
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        import json
        content = response.choices[0].message.content
        # Try to parse JSON
        try:
            subtopics = json.loads(content)
            if isinstance(subtopics, list):
                return subtopics[:max_count]
        except:
            # Fallback: parse lines
            lines = [l.strip().strip('"').strip("'") for l in content.split('\n') if l.strip()]
            return [l for l in lines if l][:max_count]
        
        return [f"{topic} - Subtopic {i+1}" for i in range(max_count)]
        
    except Exception as e:
        print(f"[RESEARCH] Error generating subtopics: {e}")
        return [f"{topic} - Section {i+1}" for i in range(max_count)]


async def generate_subtopic_content(topic: str, subtopic: str) -> str:
    """Generate content for a subtopic"""
    if not is_research_configured():
        return f"Content about {subtopic} related to {topic}."
    
    try:
        http_client = create_http_client()
        client = OpenAI(
            api_key=OPENAI_API_KEY,
            http_client=http_client
        ) if http_client else OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a research assistant writing comprehensive content."
                },
                {
                    "role": "user",
                    "content": f"Write a detailed paragraph about: {subtopic} (in the context of {topic})"
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"[RESEARCH] Error generating content: {e}")
        return f"Content about {subtopic}."


async def generate_final_report(topic: str, sections: List[Dict[str, Any]]) -> str:
    """Generate final research report"""
    if not is_research_configured():
        return f"Research report on {topic}"
    
    try:
        # Build report sections
        report_sections = []
        for section in sections:
            report_sections.append(f"## {section.get('subtopic', 'Section')}\n\n{section.get('content', '')}\n")
        
        report_content = "\n".join(report_sections)
        
        http_client = create_http_client()
        client = OpenAI(
            api_key=OPENAI_API_KEY,
            http_client=http_client
        ) if http_client else OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a research assistant. Write comprehensive research reports."
                },
                {
                    "role": "user",
                    "content": f"Write a comprehensive research report on: {topic}\n\nUse the following sections:\n\n{report_content}\n\nFormat as a well-structured research report with introduction, body sections, and conclusion."
                }
            ],
            temperature=0.7,
            max_tokens=3000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"[RESEARCH] Error generating report: {e}")
        return f"Research report on {topic}"


def update_research_status(
    research_id: str,
    status: str,
    progress: str,
    current_section: Optional[str] = None,
    section_index: Optional[int] = None,
    total_sections: Optional[int] = None,
    error: Optional[str] = None
) -> None:
    """Update research session status"""
    update_data = {
        "status": status,
        "progress": progress,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    if current_section:
        update_data["current_section"] = current_section
    if section_index is not None:
        update_data["section_index"] = section_index
    if total_sections is not None:
        update_data["total_sections"] = total_sections
    if error:
        update_data["error"] = error
    
    if USE_DATABASE:
        try:
            supabase_client.table("research_sessions").update(update_data).eq("id", research_id).execute()
        except Exception as e:
            print(f"[RESEARCH] Database error: {e}")
    
    # Update in-memory
    if research_id in research_sessions:
        research_sessions[research_id].update(update_data)


def save_research_result(research_id: str, report: str, sections: List[Dict[str, Any]]) -> None:
    """Save research result"""
    result_data = {
        "status": "completed",
        "report": report,
        "sections": sections,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    if USE_DATABASE:
        try:
            supabase_client.table("research_sessions").update({
                "status": "completed",
                "content": {
                    "report": report,
                    "sections": sections
                },
                "updated_at": result_data["updated_at"]
            }).eq("id", research_id).execute()
        except Exception as e:
            print(f"[RESEARCH] Database error: {e}")
    
    # Update in-memory
    if research_id in research_sessions:
        research_sessions[research_id].update(result_data)


def get_research_status(research_id: str) -> Optional[Dict[str, Any]]:
    """Get research session status"""
    if USE_DATABASE:
        try:
            result = supabase_client.table("research_sessions").select("*").eq("id", research_id).execute()
            if result.data and len(result.data) > 0:
                return result.data[0]
        except Exception as e:
            print(f"[RESEARCH] Database error: {e}")
    
    return research_sessions.get(research_id)


def get_research_result(research_id: str) -> Optional[Dict[str, Any]]:
    """Get research result"""
    session = get_research_status(research_id)
    if not session:
        return None
    
    if session.get("status") == "completed":
        content = session.get("content", {})
        if isinstance(content, dict):
            return {
                "research_id": research_id,
                "report": content.get("report", ""),
                "sections": content.get("sections", []),
                "status": "completed"
            }
        else:
            # Fallback for in-memory
            return {
                "research_id": research_id,
                "report": session.get("report", ""),
                "sections": session.get("sections", []),
                "status": "completed"
            }
    
    return {
        "research_id": research_id,
        "status": session.get("status", "researching"),
        "message": "Research still in progress"
    }


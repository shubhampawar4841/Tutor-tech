"""
Co-Writer Service
AI-powered text rewriting, shortening, expanding, and narration
"""
import os
from typing import Dict, Any, Optional
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

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

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


def is_cowriter_configured() -> bool:
    """Check if co-writer service is properly configured"""
    return OPENAI_AVAILABLE and OPENAI_API_KEY


async def rewrite_text(
    text: str,
    instruction: str,
    use_rag: bool = False,
    knowledge_base_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Rewrite text according to instructions
    
    Args:
        text: Text to rewrite
        instruction: How to rewrite it (e.g., "make it more formal", "simplify")
        use_rag: Whether to use knowledge base for context
        knowledge_base_id: Optional knowledge base ID
    
    Returns:
        Dictionary with rewritten text
    """
    if not is_cowriter_configured():
        return {
            "success": False,
            "error": "Co-writer service not configured. OpenAI API key required."
        }
    
    try:
        # Get context from RAG if enabled
        context = ""
        if use_rag and knowledge_base_id and RAG_AVAILABLE:
            # Use the instruction as a query to get relevant context
            # ask_question is not async, so don't await it
            rag_result = ask_question(
                question=instruction,
                kb_id=knowledge_base_id,
                top_k=3,
                threshold=0.3
            )
            if rag_result and rag_result.get("success"):
                context = rag_result.get("answer", "")
        
        # Build prompt
        if context:
            prompt = f"""Rewrite the following text according to these instructions: {instruction}

Context from knowledge base (use as reference):
{context}

Original text:
{text}

Please rewrite the text following the instructions while maintaining the core meaning. Use the context as a reference for style and terminology if relevant."""
        else:
            prompt = f"""Rewrite the following text according to these instructions: {instruction}

Original text:
{text}

Please rewrite the text following the instructions while maintaining the core meaning."""
        
        # Generate rewritten text
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
                    "content": "You are an expert writing assistant. Rewrite text according to instructions while preserving meaning."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        rewritten = response.choices[0].message.content
        
        return {
            "success": True,
            "original": text,
            "rewritten": rewritten,
            "status": "completed"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error rewriting text: {str(e)}"
        }


async def shorten_text(
    text: str,
    instruction: str = "Summarize and make it concise"
) -> Dict[str, Any]:
    """
    Shorten/summarize text
    
    Args:
        text: Text to shorten
        instruction: Optional instruction on how to shorten
    
    Returns:
        Dictionary with shortened text
    """
    return await rewrite_text(text, instruction or "Summarize and make it concise", use_rag=False)


async def expand_text(
    text: str,
    instruction: str = "Expand with more details and explanations"
) -> Dict[str, Any]:
    """
    Expand text with more details
    
    Args:
        text: Text to expand
        instruction: Optional instruction on how to expand
    
    Returns:
        Dictionary with expanded text
    """
    return await rewrite_text(text, instruction or "Expand with more details and explanations", use_rag=False)


async def narrate_text(
    text: str,
    voice: str = "default"
) -> Dict[str, Any]:
    """
    Generate audio narration from text (placeholder - requires TTS service)
    
    Args:
        text: Text to narrate
        voice: Voice to use (not implemented yet)
    
    Returns:
        Dictionary with audio URL (placeholder)
    """
    # TODO: Implement actual text-to-speech
    # For now, return a placeholder
    # You can integrate with:
    # - OpenAI TTS API
    # - Google Cloud Text-to-Speech
    # - Amazon Polly
    # - ElevenLabs
    
    return {
        "success": True,
        "audio_url": f"/audio/narration_{os.urandom(8).hex()}.mp3",
        "status": "completed",
        "message": "Narration feature coming soon. This is a placeholder."
    }


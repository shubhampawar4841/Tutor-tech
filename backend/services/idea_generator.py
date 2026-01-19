"""
Idea Generator Service
Generates research ideas and project concepts from notebooks
"""
import os
from typing import Dict, Any, Optional, List
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

# Try to import database
try:
    from database.db import (
        is_supabase_configured,
        supabase_client,
        get_notebook,
        list_notebook_items
    )
    USE_DATABASE = is_supabase_configured()
except ImportError:
    USE_DATABASE = False
    supabase_client = None
    get_notebook = None
    list_notebook_items = None

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


def is_idea_gen_configured() -> bool:
    """Check if idea generator service is properly configured"""
    return OPENAI_AVAILABLE and OPENAI_API_KEY


def extract_notebook_content(notebook_ids: List[str]) -> Dict[str, Any]:
    """Extract content from notebooks for idea generation"""
    if not USE_DATABASE:
        print("[IDEA_GEN] Database not configured, cannot extract notebook content")
        return {"content": [], "topics": []}
    
    if not list_notebook_items:
        print("[IDEA_GEN] list_notebook_items function not available")
        return {"content": [], "topics": []}
    
    all_content = []
    all_topics = set()
    
    print(f"[IDEA_GEN] Extracting content from {len(notebook_ids)} notebooks...")
    
    for notebook_id in notebook_ids:
        try:
            # Get notebook items
            items = list_notebook_items(notebook_id)
            print(f"[IDEA_GEN] Found {len(items)} items in notebook {notebook_id}")
            
            if not items:
                print(f"[IDEA_GEN] No items found in notebook {notebook_id}")
                continue
            
            for item in items:
                item_type = item.get("type", "")
                content_data = item.get("content", {})
                
                # Handle both dict and string content
                if isinstance(content_data, str):
                    try:
                        import json
                        content_data = json.loads(content_data)
                    except:
                        content_data = {"text": content_data}
                
                print(f"[IDEA_GEN] Processing item type: {item_type}")
                
                if item_type == "solve":
                    # Extract question and answer
                    question = content_data.get("question", "")
                    answer = content_data.get("answer", "")
                    if question:
                        content_str = f"Question: {question}\nAnswer: {answer[:500] if answer else 'No answer provided'}"
                        all_content.append(content_str)
                        # Extract topics from question
                        words = question.lower().split()
                        all_topics.update([w for w in words if len(w) > 4])
                        print(f"[IDEA_GEN] Added solve item: {question[:50]}...")
                
                elif item_type == "question":
                    # Extract question content
                    question_text = content_data.get("question", "")
                    answer_text = content_data.get("answer", "")
                    if question_text:
                        content_str = f"Practice Question: {question_text}\nAnswer: {answer_text[:500] if answer_text else 'No answer provided'}"
                        all_content.append(content_str)
                        print(f"[IDEA_GEN] Added question item: {question_text[:50]}...")
                
                elif item_type == "research":
                    # Extract research content
                    topic = content_data.get("topic", "")
                    summary = content_data.get("summary", content_data.get("text", ""))
                    if topic or summary:
                        content_str = f"Research Topic: {topic}\nSummary: {summary[:500] if summary else 'No summary'}"
                        all_content.append(content_str)
                        if topic:
                            all_topics.add(topic.lower())
                        print(f"[IDEA_GEN] Added research item: {topic[:50] if topic else 'Untitled'}...")
                
                elif item_type == "note":
                    # Extract note content
                    note_text = content_data.get("text", content_data.get("content", ""))
                    if note_text:
                        all_content.append(f"Note: {note_text[:500]}")
                        print(f"[IDEA_GEN] Added note item: {note_text[:50]}...")
        
        except Exception as e:
            print(f"[IDEA_GEN] Error extracting content from notebook {notebook_id}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"[IDEA_GEN] Extracted {len(all_content)} content items and {len(all_topics)} topics")
    return {
        "content": all_content,
        "topics": list(all_topics)
    }


def generate_ideas(
    notebook_ids: Optional[List[str]] = None,
    domain: Optional[str] = None,
    count: int = 5,
    idea_type: str = "research"  # research, project, essay, presentation
) -> Dict[str, Any]:
    """
    Generate ideas based on notebook content or domain
    
    Args:
        notebook_ids: Optional list of notebook IDs to analyze
        domain: Optional domain/topic to focus on
        count: Number of ideas to generate
        idea_type: Type of ideas (research, project, essay, presentation)
    
    Returns:
        Dictionary with generated ideas
    """
    if not is_idea_gen_configured():
        return {
            "success": False,
            "error": "Idea generator not configured. OpenAI API key required."
        }
    
    try:
        # Extract content from notebooks if provided
        notebook_content = ""
        topics = []
        if notebook_ids and len(notebook_ids) > 0:
            print(f"[IDEA_GEN] Extracting content from {len(notebook_ids)} notebooks...")
            extracted = extract_notebook_content(notebook_ids)
            notebook_content = "\n\n".join(extracted["content"])
            topics = extracted["topics"]
            print(f"[IDEA_GEN] Extracted {len(extracted['content'])} content items, {len(topics)} topics")
            print(f"[IDEA_GEN] Content preview: {notebook_content[:200]}...")
        
        # Build prompt
        if notebook_content and len(notebook_content.strip()) > 0:
            print(f"[IDEA_GEN] Using notebook content ({len(notebook_content)} chars) for idea generation")
            # Limit content to avoid token limits, but keep more context
            content_preview = notebook_content[:4000]  # Increased from 3000
            if len(notebook_content) > 4000:
                content_preview += f"\n\n[... {len(notebook_content) - 4000} more characters of content ...]"
            
            prompt = f"""Based on the following learning content from notebooks, generate {count} creative {idea_type} ideas.

LEARNING CONTENT FROM NOTEBOOKS:
{content_preview}

{"FOCUS DOMAIN: " + domain if domain else ""}

IMPORTANT: The ideas MUST be based on and build upon the learning content provided above. Analyze the concepts, topics, and themes in the content and create ideas that extend or explore these areas further.

Please generate {count} {idea_type} ideas that:
1. DIRECTLY relate to and build upon the concepts in the learning content above
2. Are creative and interesting extensions of those concepts
3. Are feasible and well-defined
4. Include a brief description for each idea
5. Reference specific topics or concepts from the learning content

Format your response as a JSON array, where each idea has:
- "title": Short title
- "description": 2-3 sentence description that references the learning content
- "key_concepts": Array of key concepts/topics from the content
- "difficulty": easy/medium/hard

Return ONLY valid JSON, no other text."""
        else:
            # Generate ideas from domain/topic only
            prompt = f"""Generate {count} creative {idea_type} ideas{" for " + domain if domain else "on various topics"}.

Please generate {count} {idea_type} ideas that:
1. Are creative and interesting
2. Are feasible and well-defined
3. Include a brief description for each idea

Format your response as a JSON array, where each idea has:
- "title": Short title
- "description": 2-3 sentence description
- "key_concepts": Array of key concepts/topics
- "difficulty": easy/medium/hard

Return ONLY valid JSON, no other text."""
        
        # Generate ideas using LLM
        http_client = create_http_client(timeout=120.0)
        if http_client:
            client = OpenAI(api_key=OPENAI_API_KEY, http_client=http_client)
        else:
            client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a creative idea generator. Generate innovative, feasible ideas based on learning content or topics."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.8,  # Higher temperature for creativity
            max_tokens=2000
        )
        
        ideas_text = response.choices[0].message.content
        
        # Parse JSON response
        import json
        try:
            # Try to extract JSON from response
            ideas_text = ideas_text.strip()
            if ideas_text.startswith("```json"):
                ideas_text = ideas_text[7:]
            if ideas_text.startswith("```"):
                ideas_text = ideas_text[3:]
            if ideas_text.endswith("```"):
                ideas_text = ideas_text[:-3]
            ideas_text = ideas_text.strip()
            
            ideas = json.loads(ideas_text)
            if not isinstance(ideas, list):
                ideas = [ideas]
            
            # Limit to requested count
            ideas = ideas[:count]
            
            return {
                "success": True,
                "ideas": ideas,
                "count": len(ideas),
                "type": idea_type,
                "domain": domain,
                "notebook_ids": notebook_ids
            }
        except json.JSONDecodeError as e:
            print(f"[IDEA_GEN] JSON parse error: {e}")
            print(f"[IDEA_GEN] Response text: {ideas_text[:500]}")
            # Fallback: try to extract ideas manually
            return {
                "success": True,
                "ideas": [{"title": "Idea", "description": ideas_text[:200], "key_concepts": [], "difficulty": "medium"}],
                "count": 1,
                "type": idea_type,
                "domain": domain,
                "notebook_ids": notebook_ids,
                "warning": "Could not parse JSON, returning raw text"
            }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": f"Error generating ideas: {str(e)}"
        }


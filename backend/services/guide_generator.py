"""
Guided Learning Generator Service
Creates interactive learning guides from notebook content using RAG
"""
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

try:
    from openai import OpenAI
    import httpx
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    httpx = None

# Try to import database and embeddings
try:
    from database.db import (
        get_notebook,
        list_notebook_items,
        get_notebook_item
    )
    from services.embeddings import generate_embedding, create_http_client
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    get_notebook = None
    list_notebook_items = None
    get_notebook_item = None
    generate_embedding = None
    create_http_client = None

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")


def is_guide_configured() -> bool:
    """Check if guide generation is configured"""
    return OPENAI_AVAILABLE and OPENAI_API_KEY is not None


def extract_notebook_content(notebook_ids: List[str]) -> Dict[str, Any]:
    """
    Extract all content from notebooks
    
    Args:
        notebook_ids: List of notebook IDs
    
    Returns:
        Dict with organized content by type
    """
    if not get_notebook or not list_notebook_items:
        return {"solves": [], "questions": [], "research": [], "notes": []}
    
    all_content = {
        "solves": [],
        "questions": [],
        "research": [],
        "notes": [],
        "notebook_names": []
    }
    
    for notebook_id in notebook_ids:
        try:
            notebook = get_notebook(notebook_id)
            if not notebook:
                continue
            
            all_content["notebook_names"].append(notebook.get("name", "Unknown"))
            
            items = list_notebook_items(notebook_id)
            for item in items:
                item_type = item.get("type", "").lower()
                if item_type == "solve":
                    all_content["solves"].append({
                        "title": item.get("title", ""),
                        "question": item.get("content", {}).get("question", ""),
                        "answer": item.get("content", {}).get("answer", ""),
                        "notebook": notebook.get("name", "")
                    })
                elif item_type == "question":
                    all_content["questions"].append({
                        "title": item.get("title", ""),
                        "questions": item.get("content", {}).get("questions", []),
                        "knowledge_point": item.get("content", {}).get("knowledge_point", ""),
                        "notebook": notebook.get("name", "")
                    })
                elif item_type == "research":
                    all_content["research"].append({
                        "title": item.get("title", ""),
                        "topic": item.get("content", {}).get("topic", ""),
                        "summary": item.get("content", {}).get("summary", ""),
                        "notebook": notebook.get("name", "")
                    })
                elif item_type == "note":
                    all_content["notes"].append({
                        "title": item.get("title", ""),
                        "content": item.get("content", {}).get("text", ""),
                        "notebook": notebook.get("name", "")
                    })
        except Exception as e:
            print(f"[GUIDE] Error extracting content from notebook {notebook_id}: {e}")
            continue
    
    return all_content


def build_guide_prompt(content: Dict[str, Any], max_points: int = 5) -> str:
    """
    Build prompt for generating learning guide
    
    Args:
        content: Extracted notebook content
        max_points: Maximum number of learning points/steps
    
    Returns:
        Formatted prompt
    """
    # Build context from content with FULL details
    context_parts = []
    
    if content.get("solves"):
        context_parts.append("## Solutions & Answers:")
        for idx, solve in enumerate(content["solves"][:8], 1):  # Limit to avoid token limits
            question = solve.get('question', '')
            answer = solve.get('answer', '')
            title = solve.get('title', f'Solution {idx}')
            context_parts.append(f"\n### {title}")
            context_parts.append(f"Question: {question}")
            if answer:
                # Include full answer, but limit length
                answer_preview = answer[:1000] if len(answer) > 1000 else answer
                context_parts.append(f"Answer: {answer_preview}")
                if len(answer) > 1000:
                    context_parts.append("... (answer continues)")
    
    if content.get("questions"):
        context_parts.append("\n## Practice Questions:")
        for idx, q in enumerate(content["questions"][:8], 1):
            title = q.get('title', f'Questions {idx}')
            knowledge_point = q.get('knowledge_point', '')
            questions_list = q.get('questions', [])
            context_parts.append(f"\n### {title}")
            if knowledge_point:
                context_parts.append(f"Topic: {knowledge_point}")
            if questions_list:
                for q_item in questions_list[:3]:  # Show first 3 questions
                    q_text = q_item.get('question', '') if isinstance(q_item, dict) else str(q_item)
                    context_parts.append(f"- {q_text[:300]}")
    
    if content.get("research"):
        context_parts.append("\n## Research Topics:")
        for idx, r in enumerate(content["research"][:8], 1):
            title = r.get('title', f'Research {idx}')
            topic = r.get('topic', '')
            summary = r.get('summary', '')
            context_parts.append(f"\n### {title}")
            if topic:
                context_parts.append(f"Topic: {topic}")
            if summary:
                summary_preview = summary[:500] if len(summary) > 500 else summary
                context_parts.append(f"Summary: {summary_preview}")
    
    if content.get("notes"):
        context_parts.append("\n## Notes:")
        for idx, note in enumerate(content["notes"][:8], 1):
            title = note.get('title', f'Note {idx}')
            note_content = note.get('content', '')
            context_parts.append(f"\n### {title}")
            if note_content:
                note_preview = note_content[:500] if len(note_content) > 500 else note_content
                context_parts.append(f"{note_preview}")
    
    context_text = "\n".join(context_parts)
    notebook_names = ", ".join(content.get("notebook_names", []))
    
    prompt = f"""You are an expert educator creating a structured learning guide from student's saved materials.

IMPORTANT: Use ONLY the actual content provided below. Do NOT make up or invent information. Base your guide strictly on what the student has saved in their notebooks.

Notebooks Used: {notebook_names}

ACTUAL CONTENT FROM NOTEBOOKS:
{context_text}

Create a structured learning guide with {max_points} learning points/steps that:
1. Uses ONLY the actual content provided above - do not add information not in the notebooks
2. Organizes the content logically based on what's actually there
3. Builds from basic concepts to advanced (if the content allows)
4. Extracts and presents key topics and concepts from the actual saved content
5. Provides a clear learning path based on the real material
6. References specific questions, answers, and topics from the notebooks
7. If content is limited, create a guide that works with what's available

CRITICAL: Your guide must be based on the actual content shown above. Do not invent topics, concepts, or information that isn't in the provided content.

Output Format (JSON):
{{
  "title": "Learning Guide Title",
  "description": "Brief description of what will be learned",
  "total_steps": {max_points},
  "steps": [
    {{
      "step_number": 1,
      "title": "Step title",
      "description": "What you'll learn in this step",
      "key_points": ["Point 1", "Point 2", "Point 3"],
      "content": "Detailed explanation and learning material",
      "related_items": ["Reference to notebook items if relevant"]
    }},
    ...
  ]
}}

Generate the learning guide now:"""
    
    return prompt


def generate_guide(notebook_ids: List[str], max_points: int = 5) -> Dict[str, Any]:
    """
    Generate a learning guide from notebooks
    
    Args:
        notebook_ids: List of notebook IDs to use
        max_points: Maximum number of learning points
    
    Returns:
        Dict with generated guide content
    """
    if not is_guide_configured():
        return {
            "success": False,
            "error": "OpenAI API not configured. Set OPENAI_API_KEY in .env",
            "content": None
        }
    
    try:
        # Step 1: Extract content from notebooks
        print(f"[GUIDE] Extracting content from {len(notebook_ids)} notebooks...")
        content = extract_notebook_content(notebook_ids)
        
        total_items = (
            len(content.get("solves", [])) +
            len(content.get("questions", [])) +
            len(content.get("research", [])) +
            len(content.get("notes", []))
        )
        
        if total_items == 0:
            return {
                "success": False,
                "error": "No content found in selected notebooks. Add items to notebooks first.",
                "content": None
            }
        
        print(f"[GUIDE] Found {total_items} items across notebooks")
        
        # Step 2: Build prompt
        prompt = build_guide_prompt(content, max_points)
        
        # Step 3: Generate guide using LLM
        print(f"[GUIDE] Generating learning guide using {LLM_MODEL}...")
        
        if OPENAI_API_KEY and "OPENAI_API_KEY" not in os.environ:
            os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        
        http_client = create_http_client(timeout=120.0) if create_http_client else None
        if http_client:
            client = OpenAI(http_client=http_client)
        else:
            client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert educator. Generate learning guides in valid JSON format. Return only the JSON object, no additional text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=4000,
        )
        
        answer_text = response.choices[0].message.content.strip()
        print(f"[GUIDE] Generated response ({len(answer_text)} chars)")
        
        # Step 4: Parse response
        import json
        import re
        
        guide_content = None
        
        # Try to extract JSON from response
        try:
            # Try parsing entire response as JSON
            guide_content = json.loads(answer_text)
        except json.JSONDecodeError:
            # Try to extract JSON object from text
            json_match = re.search(r'\{[\s\S]*\}', answer_text, re.MULTILINE)
            if json_match:
                try:
                    guide_content = json.loads(json_match.group())
                except:
                    pass
        
        if not guide_content:
            print("[WARNING] Failed to parse guide JSON, creating fallback structure")
            guide_content = {
                "title": "Learning Guide",
                "description": "Structured learning path from your notebooks",
                "total_steps": max_points,
                "steps": [
                    {
                        "step_number": i + 1,
                        "title": f"Step {i + 1}",
                        "description": "Learning content",
                        "key_points": [],
                        "content": "Content will be generated",
                        "related_items": []
                    }
                    for i in range(max_points)
                ]
            }
        
        # Validate structure
        if "steps" not in guide_content:
            guide_content["steps"] = []
        
        if "total_steps" not in guide_content:
            guide_content["total_steps"] = len(guide_content.get("steps", []))
        
        print(f"[GUIDE] Successfully generated guide with {guide_content.get('total_steps', 0)} steps")
        
        return {
            "success": True,
            "content": guide_content,
            "metadata": {
                "notebook_ids": notebook_ids,
                "total_items": total_items,
                "max_points": max_points
            }
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to generate guide: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": f"Failed to generate guide: {str(e)}",
            "content": None
        }


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
# Use gpt-4o for guide generation (better teaching quality)
GUIDE_LLM_MODEL = os.getenv("GUIDE_LLM_MODEL", "gpt-4o")


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


def build_guide_prompt(content: Dict[str, Any], max_points: int = 12) -> str:
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
    
    prompt = f"""You are a PROFESSOR teaching a student who knows NOTHING about this topic. Your job is to TEACH from zero, not summarize.

Notebooks Used: {notebook_names}

CONTENT FROM NOTEBOOKS:
{context_text}

CRITICAL TEACHING REQUIREMENTS:

You must create {max_points} knowledge points that TEACH, not summarize. Each knowledge point must be SMALL and FOCUSED on ONE concept.

For EVERY knowledge point, you MUST follow this structure:

1. **START WITH INTUITION/STORY/ANALOGY** (REQUIRED):
   - Begin with a relatable analogy, story, or mental model
   - Make it concrete and visual
   - Example: "Imagine Earth like a bank account of energy..."
   - This helps the student build intuition BEFORE learning definitions

2. **THEN GIVE SIMPLE DEFINITION** (REQUIRED):
   - After building intuition, provide a clear, simple definition
   - Use plain language, not jargon
   - Connect it back to the intuition/analogy

3. **EXPLAIN HOW IT WORKS** (REQUIRED):
   - Break down the mechanism step-by-step
   - Show the process, not just the conclusion
   - Use "first... then... finally..." structure
   - Make it visual and concrete

4. **EXPLAIN WHY IT MATTERS** (REQUIRED):
   - What happens if it works correctly?
   - What happens if it breaks?
   - Why should the student care?
   - Real-world consequences

5. **GIVE REAL-WORLD EXAMPLES** (REQUIRED):
   - At least 2-3 concrete examples
   - Connect to everyday life
   - Show different contexts where it applies

6. **EXPLAIN COMMON MISTAKES** (REQUIRED):
   - What misconceptions do students have?
   - How to avoid them?
   - What to watch out for?

FORBIDDEN:
❌ NO Wikipedia-style summaries
❌ NO definition-only explanations
❌ NO conclusion-only statements
❌ NO "X is Y" without explaining WHY and HOW

REQUIRED:
✅ Start with intuition/story/analogy
✅ Build understanding step-by-step
✅ Explain mechanisms, not just conclusions
✅ Use examples and real-world connections
✅ Teach from zero knowledge

Output Format (JSON) - STRICT STRUCTURE:
{{
  "title": "Learning Guide Title",
  "description": "Brief description of what will be learned",
  "total_knowledge_points": {max_points},
  "knowledge_points": [
    {{
      "knowledge_point_number": 1,
      "knowledge_title": "Knowledge point title (one small concept)",
      "description": "What you'll learn in this knowledge point",
      "content": {{
        "intuition": "Start here: A relatable analogy, story, or mental model that builds intuition. Make it concrete and visual. Example: 'Imagine Earth like a bank account of energy...'",
        "definition": "After intuition: A clear, simple definition in plain language. Connect it back to the intuition.",
        "how_it_works": "Step-by-step explanation of the mechanism. Use 'first... then... finally...' structure. Show the process, not just the conclusion.",
        "why_it_matters": "What happens if it works correctly? What happens if it breaks? Why should the student care? Real-world consequences.",
        "examples": [
          "Example 1: Concrete, real-world example",
          "Example 2: Another example in different context",
          "Example 3: One more example"
        ],
        "common_mistakes": [
          "Common misconception 1 and how to avoid it",
          "Common misconception 2 and what to watch out for"
        ]
      }},
      "key_points": ["Key takeaway 1", "Key takeaway 2", "Key takeaway 3"],
      "questions": [],  // Questions will be matched from notebooks - leave empty
      "related_items": ["Reference to notebook items if relevant"]
    }},
    ...
  ]
}}

CRITICAL: Each knowledge point must be SMALL and FOCUSED. Break complex topics into multiple small knowledge points. 
For example, "Heat Budget" should be split into: "Energy Balance Concept", "Incoming Solar Radiation", "Outgoing Terrestrial Radiation", "Heat Budget Balance", etc.

NOTE: Questions will be automatically matched from notebooks based on topic. Leave the "questions" array empty in your response.

Generate the learning guide now:"""
    
    return prompt


def match_questions_from_notebooks(
    knowledge_point: Dict[str, Any],
    notebook_content: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Match questions from notebooks to a knowledge point based on topic similarity
    
    Args:
        knowledge_point: Knowledge point dict with title, content, etc.
        notebook_content: Extracted notebook content with questions
    
    Returns:
        List of matched questions from notebooks
    """
    matched_questions = []
    
    # Get knowledge point title and key terms
    kp_title = knowledge_point.get("knowledge_title") or knowledge_point.get("title", "")
    kp_content = knowledge_point.get("content", "")
    kp_key_points = knowledge_point.get("key_points", [])
    
    # Extract key terms from knowledge point
    kp_terms = set()
    kp_text = f"{kp_title} {kp_content} {' '.join(kp_key_points)}".lower()
    # Simple keyword extraction
    for word in kp_text.split():
        if len(word) > 4:  # Only meaningful words
            kp_terms.add(word)
    
    # Check questions from notebooks
    notebook_questions = notebook_content.get("questions", [])
    
    for q_item in notebook_questions:
        q_knowledge_point = q_item.get("knowledge_point", "").lower()
        q_title = q_item.get("title", "").lower()
        questions_list = q_item.get("questions", [])
        
        # Check if knowledge point matches
        match_score = 0
        if q_knowledge_point:
            # Direct match
            if q_knowledge_point in kp_title.lower() or kp_title.lower() in q_knowledge_point:
                match_score += 10
            # Keyword overlap
            q_terms = set(q_knowledge_point.split())
            overlap = len(kp_terms.intersection(q_terms))
            match_score += overlap
        
        # If title contains relevant terms
        if q_title:
            q_title_terms = set(q_title.split())
            title_overlap = len(kp_terms.intersection(q_title_terms))
            match_score += title_overlap * 0.5
        
        # If match score is high enough, include these questions
        if match_score >= 2 and questions_list:
            for q in questions_list:
                if isinstance(q, dict):
                    # Convert notebook question format to guide question format
                    matched_questions.append({
                        "question": q.get("question", ""),
                        "type": q.get("type", "understanding"),
                        "hint": q.get("hint", ""),
                        "expected_key_points": q.get("expected_key_points", []),
                        "answer": q.get("answer", ""),  # Include answer for evaluation
                        "options": q.get("options", []),  # For multiple choice
                        "difficulty": q.get("difficulty", "medium"),
                        "source": "notebook"  # Mark as from notebook
                    })
                elif isinstance(q, str):
                    # Simple string question
                    matched_questions.append({
                        "question": q,
                        "type": "understanding",
                        "hint": "",
                        "expected_key_points": kp_key_points[:2] if kp_key_points else [],
                        "source": "notebook"
                    })
    
    return matched_questions


def generate_questions_for_step(
    step: Dict[str, Any],
    notebook_ids: List[str],
    content: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Generate questions for a step if they're missing
    
    Args:
        step: Step dictionary
        notebook_ids: Notebook IDs for context
        content: Extracted notebook content
    
    Returns:
        List of question dictionaries
    """
    if not is_guide_configured():
        return []
    
    try:
        step_title = step.get("title", "this step")
        step_content = step.get("content", "")
        key_points = step.get("key_points", [])
        
        question_prompt = f"""Generate 2-3 thoughtful questions for a learning step about: {step_title}

STEP CONTENT:
{step_content[:1500]}

KEY POINTS:
{chr(10).join(f"- {point}" for point in key_points[:5])}

Generate 2-3 questions that:
1. Test understanding of core concepts (not just recall)
2. Require students to apply what they learned
3. Help identify knowledge gaps
4. Include hints to guide learning
5. Mix question types: understanding, application, and analysis

Return JSON array:
[
  {{
    "question": "Question text",
    "type": "understanding",
    "hint": "Helpful hint",
    "expected_key_points": ["Key point 1", "Key point 2"]
  }},
  ...
]"""

        if OPENAI_API_KEY and "OPENAI_API_KEY" not in os.environ:
            os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        
        http_client = create_http_client(timeout=60.0) if create_http_client else None
        if http_client:
            client = OpenAI(http_client=http_client)
        else:
            client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert educator. Generate learning questions in valid JSON array format. Return only the JSON array, no additional text."
                },
                {
                    "role": "user",
                    "content": question_prompt
                }
            ],
            temperature=0.7,
            max_tokens=1500,
        )
        
        answer_text = response.choices[0].message.content.strip()
        
        import json
        import re
        
        try:
            questions = json.loads(answer_text)
            if isinstance(questions, list):
                return questions
            elif isinstance(questions, dict) and "questions" in questions:
                return questions["questions"]
        except json.JSONDecodeError:
            json_match = re.search(r'\[[\s\S]*\]', answer_text, re.MULTILINE)
            if json_match:
                try:
                    questions = json.loads(json_match.group())
                    if isinstance(questions, list):
                        return questions
                except:
                    pass
        
        # Fallback: create basic questions
        return [
            {
                "question": f"Explain the key concept of {step_title} in your own words.",
                "type": "understanding",
                "hint": "Review the key points and main content above.",
                "expected_key_points": key_points[:2] if key_points else ["Main concept"]
            },
            {
                "question": f"How would you apply the concept of {step_title} in a real-world scenario?",
                "type": "application",
                "hint": "Think about practical examples and use cases.",
                "expected_key_points": ["Application", "Example"]
            }
        ]
        
    except Exception as e:
        print(f"[ERROR] Failed to generate questions for step: {e}")
        # Return basic fallback questions
        return [
            {
                "question": f"Explain the main concept of {step.get('title', 'this step')}.",
                "type": "understanding",
                "hint": "Review the content above carefully.",
                "expected_key_points": ["Main concept"]
            }
        ]


def evaluate_answer(
    question: Dict[str, Any],
    user_answer: str,
    step_content: str,
    notebook_ids: List[str]
) -> Dict[str, Any]:
    """
    Evaluate a user's answer to a question and provide feedback
    
    Args:
        question: Question dict with question text, type, hint, expected_key_points
        user_answer: User's submitted answer
        step_content: The learning content for this step
        notebook_ids: Notebook IDs for context
    
    Returns:
        Dict with score, feedback, and recommendations
    """
    if not is_guide_configured():
        return {
            "score": 0.5,
            "feedback": "Evaluation not available",
            "is_correct": False,
            "suggestions": []
        }
    
    try:
        expected_points = question.get("expected_key_points", [])
        question_text = question.get("question", "")
        question_type = question.get("type", "understanding")
        
        evaluation_prompt = f"""You are an expert educator evaluating a student's answer to a learning question.

LEARNING CONTENT (for context):
{step_content[:2000]}

QUESTION:
{question_text}

QUESTION TYPE: {question_type}

EXPECTED KEY POINTS (what a good answer should include):
{chr(10).join(f"- {point}" for point in expected_points)}

STUDENT'S ANSWER:
{user_answer}

Evaluate the student's answer and provide:
1. A score from 0.0 to 1.0 based on how well they understood and answered
2. Specific, constructive feedback on what they got right and what needs improvement
3. Whether they demonstrated understanding (is_correct: true/false)
4. Specific suggestions for improvement if needed

Consider:
- Did they address the key points?
- Is their understanding accurate?
- Did they demonstrate comprehension or just memorization?
- Are there misconceptions that need correction?

Return your evaluation as JSON:
{{
  "score": 0.85,
  "feedback": "Your answer shows good understanding of X, but you missed Y. Consider Z...",
  "is_correct": true,
  "suggestions": ["Suggestion 1", "Suggestion 2"],
  "strengths": ["What they did well"],
  "areas_for_improvement": ["What needs work"]
}}"""

        if OPENAI_API_KEY and "OPENAI_API_KEY" not in os.environ:
            os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        
        http_client = create_http_client(timeout=60.0) if create_http_client else None
        if http_client:
            client = OpenAI(http_client=http_client)
        else:
            client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert educator. Evaluate answers and provide constructive feedback in valid JSON format. Return only the JSON object, no additional text."
                },
                {
                    "role": "user",
                    "content": evaluation_prompt
                }
            ],
            temperature=0.3,  # Lower temperature for more consistent evaluation
            max_tokens=1000,
        )
        
        answer_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        import json
        import re
        
        try:
            evaluation = json.loads(answer_text)
        except json.JSONDecodeError:
            # Try to extract JSON
            json_match = re.search(r'\{[\s\S]*\}', answer_text, re.MULTILINE)
            if json_match:
                try:
                    evaluation = json.loads(json_match.group())
                except:
                    evaluation = {
                        "score": 0.5,
                        "feedback": "Could not parse evaluation. Please review your answer.",
                        "is_correct": False,
                        "suggestions": []
                    }
            else:
                evaluation = {
                    "score": 0.5,
                    "feedback": answer_text[:500] if answer_text else "Evaluation unavailable",
                    "is_correct": False,
                    "suggestions": []
                }
        
        # Ensure all required fields
        evaluation.setdefault("score", 0.5)
        evaluation.setdefault("feedback", "No feedback provided")
        evaluation.setdefault("is_correct", evaluation.get("score", 0.5) >= 0.6)
        evaluation.setdefault("suggestions", [])
        evaluation.setdefault("strengths", [])
        evaluation.setdefault("areas_for_improvement", [])
        
        return evaluation
        
    except Exception as e:
        print(f"[ERROR] Failed to evaluate answer: {e}")
        import traceback
        traceback.print_exc()
        return {
            "score": 0.5,
            "feedback": f"Error evaluating answer: {str(e)}",
            "is_correct": False,
            "suggestions": ["Please try again or review the content"]
        }


def generate_remedial_content(
    knowledge_point: Dict[str, Any],
    understanding_gaps: Dict[str, Any],
    notebook_ids: List[str]
) -> Dict[str, Any]:
    """
    Generate additional remedial content when user has understanding gaps
    
    Args:
        knowledge_point: Current knowledge point
        understanding_gaps: Gap tracking info (score, total_questions, needs_review)
        notebook_ids: Notebook IDs for context
    
    Returns:
        Dict with remedial content (explanation, examples, practice)
    """
    if not is_guide_configured():
        return {
            "title": "Review Section",
            "content": "Please review the previous content carefully.",
            "type": "remedial"
        }
    
    try:
        kp_title = knowledge_point.get("knowledge_title") or knowledge_point.get("title", "")
        kp_content = knowledge_point.get("content", "")
        avg_score = understanding_gaps.get("score", 0) / max(understanding_gaps.get("total_questions", 1), 1)
        
        remedial_prompt = f"""The student is struggling with: {kp_title}

CURRENT CONTENT:
{kp_content[:2000]}

UNDERSTANDING SCORE: {avg_score:.2%}

The student's understanding is below 60%. Generate additional remedial content to help them understand better:

1. **Simplified Explanation**: Break down the concept into simpler terms
2. **Step-by-Step Guide**: Provide a clear step-by-step explanation
3. **Concrete Examples**: Give 2-3 concrete, real-world examples
4. **Common Mistakes**: Explain common mistakes students make and how to avoid them
5. **Practice Tips**: Provide tips for practicing and mastering this concept

Return JSON:
{{
  "title": "Additional Help: [Topic]",
  "simplified_explanation": "Simple explanation...",
  "step_by_step": ["Step 1", "Step 2", ...],
  "examples": ["Example 1", "Example 2", ...],
  "common_mistakes": ["Mistake 1", "Mistake 2", ...],
  "practice_tips": ["Tip 1", "Tip 2", ...]
}}"""

        if OPENAI_API_KEY and "OPENAI_API_KEY" not in os.environ:
            os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        
        http_client = create_http_client(timeout=60.0) if create_http_client else None
        if http_client:
            client = OpenAI(http_client=http_client)
        else:
            client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert tutor. Generate remedial learning content in valid JSON format. Return only the JSON object."
                },
                {
                    "role": "user",
                    "content": remedial_prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        
        answer_text = response.choices[0].message.content.strip()
        
        import json
        import re
        
        try:
            remedial_content = json.loads(answer_text)
        except json.JSONDecodeError:
            json_match = re.search(r'\{[\s\S]*\}', answer_text, re.MULTILINE)
            if json_match:
                try:
                    remedial_content = json.loads(json_match.group())
                except:
                    remedial_content = {
                        "title": "Review Section",
                        "content": "Please review the previous content carefully.",
                        "type": "remedial"
                    }
            else:
                remedial_content = {
                    "title": "Review Section",
                    "content": answer_text[:1000] if answer_text else "Please review the previous content carefully.",
                    "type": "remedial"
                }
        
        remedial_content["type"] = "remedial"
        remedial_content["generated_at"] = None  # Will be set by database
        
        return remedial_content
        
    except Exception as e:
        print(f"[ERROR] Failed to generate remedial content: {e}")
        import traceback
        traceback.print_exc()
        return {
            "title": "Review Section",
            "content": "Please review the previous content carefully.",
            "type": "remedial"
        }


def generate_guide(notebook_ids: List[str], max_points: int = 12) -> Dict[str, Any]:
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
        print(f"[GUIDE] Generating learning guide using {GUIDE_LLM_MODEL}...")
        
        if OPENAI_API_KEY and "OPENAI_API_KEY" not in os.environ:
            os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        
        http_client = create_http_client(timeout=120.0) if create_http_client else None
        if http_client:
            client = OpenAI(http_client=http_client)
        else:
            client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=GUIDE_LLM_MODEL,
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
            max_tokens=8000,  # Increased for structured teaching content with more knowledge points
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
                "total_knowledge_points": max_points,
                "knowledge_points": [
                    {
                        "knowledge_point_number": i + 1,
                        "knowledge_title": f"Knowledge Point {i + 1}",
                        "description": "Learning content",
                        "key_points": [],
                        "content": "Content will be generated",
                        "related_items": []
                    }
                    for i in range(max_points)
                ]
            }
        
        # Validate structure - support both old "steps" and new "knowledge_points"
        if "knowledge_points" not in guide_content and "steps" in guide_content:
            # Migrate old format to new format
            guide_content["knowledge_points"] = []
            for step in guide_content.get("steps", []):
                guide_content["knowledge_points"].append({
                    "knowledge_point_number": step.get("step_number", 0),
                    "knowledge_title": step.get("title", ""),
                    "description": step.get("description", ""),
                    "key_points": step.get("key_points", []),
                    "content": step.get("content", ""),
                    "questions": step.get("questions", []),
                    "related_items": step.get("related_items", [])
                })
            guide_content["total_knowledge_points"] = guide_content.get("total_steps", len(guide_content["knowledge_points"]))
        
        if "knowledge_points" not in guide_content:
            guide_content["knowledge_points"] = []
        
        if "total_knowledge_points" not in guide_content:
            guide_content["total_knowledge_points"] = len(guide_content.get("knowledge_points", []))
        
        # Ensure each knowledge point has questions - generate if missing
        # Also validate content structure (support both old string format and new structured format)
        for kp in guide_content.get("knowledge_points", []):
            # Validate content structure - if it's a string, keep it (backward compatibility)
            # If it's missing or invalid object, we'll handle it in frontend
            content_field = kp.get("content")
            if content_field and isinstance(content_field, str):
                # Old format - string content (backward compatible)
                pass
            elif content_field and isinstance(content_field, dict):
                # New format - structured content
                # Validate required fields exist
                if not any(key in content_field for key in ["intuition", "definition", "how_it_works"]):
                    print(f"[WARNING] Knowledge point {kp.get('knowledge_point_number', '?')} has structured content but missing required fields")
            
            if "questions" not in kp or not kp.get("questions") or len(kp.get("questions", [])) == 0:
                print(f"[GUIDE] Knowledge point {kp.get('knowledge_point_number', '?')} missing questions, generating...")
                kp["questions"] = generate_questions_for_step(
                    step=kp,  # Function still uses "step" internally
                    notebook_ids=notebook_ids,
                    content=content
                )
        
        print(f"[GUIDE] Successfully generated guide with {guide_content.get('total_knowledge_points', 0)} knowledge points")
        
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


def generate_learning_summary(
    session_id: str,
    notebook_ids: List[str],
    content: Dict[str, Any]
) -> str:
    """
    Generate a learning summary when guide is completed
    
    Args:
        session_id: Guide session ID
        notebook_ids: Notebook IDs used
        content: Guide content with knowledge points
    
    Returns:
        Markdown-formatted learning summary
    """
    if not is_guide_configured():
        return "# Learning Summary\n\nYou have completed the guided learning session!"


def generate_guide_plan(notebook_ids: List[str], max_points: int = 12) -> Dict[str, Any]:
    """
    Generates a plan for creating a learning guide.
    """
    if not is_guide_configured():
        return {
            "success": False,
            "error": "OpenAI API not configured. Set OPENAI_API_KEY in .env",
            "plan": None
        }

    try:
        # Step 1: Extract content from notebooks to get an idea of the scope
        content = extract_notebook_content(notebook_ids)
        notebook_names = ", ".join(content.get("notebook_names", []))
        
        # Summarize content for the plan
        content_summary = []
        if content.get("solves"):
            content_summary.append(f"{len(content['solves'])} solved problems")
        if content.get("questions"):
            content_summary.append(f"{len(content['questions'])} question sets")
        if content.get("research"):
            content_summary.append(f"{len(content['research'])} research summaries")
        if content.get("notes"):
            content_summary.append(f"{len(content['notes'])} notes")
        
        summary_text = f"Content from {len(notebook_ids)} notebooks ({notebook_names}): {', '.join(content_summary) or 'No specific items found.'}"

        plan_prompt = f"""You are an AI planning assistant. Create a detailed plan for generating a comprehensive learning guide.

The guide will be based on the following user-provided notebook content:
{summary_text}

The user wants a guide with approximately {max_points} knowledge points.

Your plan should include:
- A clear title for the plan
- A brief description of the overall goal
- A list of sequential steps, each with:
    - A description of the action
    - An estimated time (e.g., "1-2 minutes")
    - Key outcomes
- An overall estimated total time
- A list of key topics/concepts that will likely be covered.

Return the plan as a JSON object:
{{
  "title": "Plan for Learning Guide Generation",
  "description": "Generate a personalized learning guide based on selected notebook content.",
  "steps": [
    {{
      "action": "Extract and consolidate content from selected notebooks",
      "estimated_time": "30 seconds",
      "outcome": "All relevant notes, questions, and research items are gathered."
    }},
    {{
      "action": "Analyze extracted content to identify core concepts and learning objectives",
      "estimated_time": "1 minute",
      "outcome": "Key themes and a logical learning progression are determined."
    }},
    {{
      "action": "Generate {max_points} structured knowledge points with in-depth explanations",
      "estimated_time": "2-3 minutes",
      "outcome": "A comprehensive learning guide structure is created, focusing on WHAT, WHY, and HOW."
    }},
    {{
      "action": "Match existing questions from notebooks to each knowledge point",
      "estimated_time": "30 seconds",
      "outcome": "Relevant practice questions are integrated for interactive learning."
    }},
    {{
      "action": "Finalize guide content and prepare for display",
      "estimated_time": "15 seconds",
      "outcome": "The complete learning guide is ready for the student."
    }}
  ],
  "total_estimated_time": "5-7 minutes",
  "key_topics_covered": ["Topic 1", "Topic 2", "Topic 3"]
}}
"""
        
        http_client = create_http_client(timeout=60.0) if create_http_client else None
        client = OpenAI(http_client=http_client) if http_client else OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI planning assistant. Generate plans in valid JSON format. Return only the JSON object, no additional text."
                },
                {
                    "role": "user",
                    "content": plan_prompt
                }
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        
        plan_text = response.choices[0].message.content.strip()
        
        import json
        import re
        
        try:
            plan = json.loads(plan_text)
        except json.JSONDecodeError:
            json_match = re.search(r'\{[\s\S]*\}', plan_text, re.MULTILINE)
            if json_match:
                try:
                    plan = json.loads(json_match.group())
                except:
                    plan = {
                        "title": "Fallback Plan",
                        "description": "Could not parse plan. Proceeding with standard guide generation.",
                        "steps": [],
                        "total_estimated_time": "Unknown",
                        "key_topics_covered": []
                    }
            else:
                plan = {
                    "title": "Fallback Plan",
                    "description": plan_text[:500] if plan_text else "Could not generate plan.",
                    "steps": [],
                    "total_estimated_time": "Unknown",
                    "key_topics_covered": []
                }
        
        plan.setdefault("title", "Generated Plan")
        plan.setdefault("description", "A plan for generating content.")
        plan.setdefault("steps", [])
        plan.setdefault("total_estimated_time", "Unknown")
        plan.setdefault("key_topics_covered", [])

        return {
            "success": True,
            "plan": plan
        }
    except Exception as e:
        print(f"[ERROR] Failed to generate guide plan: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": f"Failed to generate plan: {str(e)}",
            "plan": None
        }
    
    try:
        knowledge_points = content.get("knowledge_points") or content.get("steps", [])
        answer_history = content.get("answer_history", [])
        understanding_gaps = content.get("understanding_gaps", {})
        
        # Calculate overall understanding
        total_scores = []
        for kp in knowledge_points:
            kp_num = kp.get("knowledge_point_number") or kp.get("step_number", 0)
            kp_key = f"knowledge_point_{kp_num}"
            step_key = f"step_{kp_num}"
            gap_info = understanding_gaps.get(kp_key) or understanding_gaps.get(step_key)
            if gap_info and gap_info.get("total_questions", 0) > 0:
                avg_score = gap_info["score"] / gap_info["total_questions"]
                total_scores.append(avg_score)
        
        overall_score = sum(total_scores) / len(total_scores) if total_scores else 0.0
        
        summary_prompt = f"""You are an expert educator creating a learning summary for a student who has completed a guided learning session.

LEARNING CONTENT:
{chr(10).join(f"{i+1}. {kp.get('knowledge_title') or kp.get('title', '')}: {kp.get('description', '')}" for i, kp in enumerate(knowledge_points[:10]))}

KNOWLEDGE POINTS COVERED: {len(knowledge_points)}
QUESTIONS ANSWERED: {len(answer_history)}
OVERALL UNDERSTANDING SCORE: {overall_score:.0%}

Create a comprehensive, encouraging learning summary that:
1. Celebrates the student's completion
2. Summarizes what they learned (all knowledge points)
3. Highlights their strengths based on understanding scores
4. Provides gentle suggestions for areas that need more practice
5. Encourages continued learning

Format as markdown with clear sections. Be warm, encouraging, and educational.

Generate the summary now:"""

        if OPENAI_API_KEY and "OPENAI_API_KEY" not in os.environ:
            os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        
        http_client = create_http_client(timeout=60.0) if create_http_client else None
        if http_client:
            client = OpenAI(http_client=http_client)
        else:
            client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert educator. Generate warm, encouraging learning summaries in markdown format."
                },
                {
                    "role": "user",
                    "content": summary_prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        
        summary = response.choices[0].message.content.strip()
        return summary
        
    except Exception as e:
        print(f"[ERROR] Failed to generate summary: {e}")
        import traceback
        traceback.print_exc()
        # Return basic fallback summary
        knowledge_points = content.get("knowledge_points") or content.get("steps", [])
        return f"""# Learning Summary

## 🎉 Congratulations!

You have completed the guided learning session covering **{len(knowledge_points)} knowledge points**.

### What You Learned:
{chr(10).join(f"- {kp.get('knowledge_title') or kp.get('title', '')}" for kp in knowledge_points[:10])}

Keep up the great work! Continue practicing and exploring these concepts to deepen your understanding."""


"""
Problem Solver Service
Generates step-by-step solutions to problems using RAG
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


def is_solve_configured() -> bool:
    """Check if solve service is properly configured"""
    return OPENAI_AVAILABLE and OPENAI_API_KEY and RAG_AVAILABLE


async def solve_problem(
    question: str,
    knowledge_base_id: Optional[str] = None,
    use_web_search: bool = False,
    use_code_execution: bool = False
) -> Dict[str, Any]:
    """
    Solve a problem step-by-step using RAG and LLM
    
    Args:
        question: The problem/question to solve
        knowledge_base_id: Optional knowledge base ID for context
        use_web_search: Whether to use web search (not implemented yet)
        use_code_execution: Whether to use code execution (not implemented yet)
    
    Returns:
        Dictionary with solve_id, status, and solution steps
    """
    if not is_solve_configured():
        return {
            "success": False,
            "error": "Solve service not configured. OpenAI API key required."
        }
    
    try:
        # Use RAG to get context and answer (with optional web search)
        if knowledge_base_id:
            # ask_question is not async, so don't await it
            rag_result = ask_question(
                question=question,
                kb_id=knowledge_base_id,
                top_k=5,
                threshold=0.3,
                use_web_search=use_web_search
            )
            
            if not rag_result or not rag_result.get("success"):
                return {
                    "success": False,
                    "error": rag_result.get("error", "Failed to retrieve context") if rag_result else "RAG service unavailable"
                }
            
            # Build enhanced prompt for step-by-step solution
            context = rag_result.get("answer", "")
            citations = rag_result.get("citations", [])
            
            # Create a more detailed step-by-step prompt
            step_by_step_prompt = f"""You are a helpful tutor solving a problem step-by-step.

Problem: {question}

Context from knowledge base:
{context}

Please provide a detailed, step-by-step solution to this problem. Break it down into clear, numbered steps. For each step:
1. Explain what you're doing
2. Show the work/reasoning
3. Explain why this step is necessary

Format your response as:
Step 1: [Description]
[Explanation and work]

Step 2: [Description]
[Explanation and work]

...and so on.

End with a final answer or conclusion."""
        else:
            # No knowledge base, use general problem solving
            step_by_step_prompt = f"""You are a helpful tutor solving a problem step-by-step.

Problem: {question}

Please provide a detailed, step-by-step solution to this problem. Break it down into clear, numbered steps. For each step:
1. Explain what you're doing
2. Show the work/reasoning
3. Explain why this step is necessary

Format your response as:
Step 1: [Description]
[Explanation and work]

Step 2: [Description]
[Explanation and work]

...and so on.

End with a final answer or conclusion."""
            citations = []
        
        # Generate step-by-step solution using LLM
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
                    "content": "You are an expert tutor who explains problems step-by-step in a clear, educational manner."
                },
                {
                    "role": "user",
                    "content": step_by_step_prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        solution = response.choices[0].message.content
        
        # Parse solution into steps (simple parsing)
        steps = _parse_solution_steps(solution)
        
        return {
            "success": True,
            "solve_id": f"solve_{os.urandom(8).hex()}",
            "status": "completed",
            "question": question,
            "solution": solution,
            "steps": steps,
            "citations": citations,
            "answer": solution  # For compatibility
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error solving problem: {str(e)}"
        }


def _parse_solution_steps(solution: str) -> List[Dict[str, str]]:
    """
    Parse solution text into structured steps
    Simple implementation - can be enhanced
    """
    steps = []
    lines = solution.split('\n')
    current_step = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_step and current_content:
                steps.append({
                    "step": current_step,
                    "content": '\n'.join(current_content)
                })
                current_content = []
            continue
        
        # Check if this is a step header (Step 1:, Step 2:, etc.)
        if line.lower().startswith('step') and ':' in line:
            if current_step and current_content:
                steps.append({
                    "step": current_step,
                    "content": '\n'.join(current_content)
                })
            current_step = line
            current_content = []
        else:
            if current_step:
                current_content.append(line)
            else:
                # First line might be the step itself
                if not current_step:
                    current_step = line
                current_content.append(line)
    
    # Add last step
    if current_step and current_content:
        steps.append({
            "step": current_step,
            "content": '\n'.join(current_content)
        })
    
    # If no steps found, return the whole solution as one step
    if not steps:
        steps.append({
            "step": "Solution",
            "content": solution
        })
    
    return steps


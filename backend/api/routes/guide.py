"""
Guided Learning API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter()

# Try to import database functions and guide generator
try:
    from database.db import (
        create_guide_session as db_create_guide_session,
        get_guide_session as db_get_guide_session,
        update_guide_session as db_update_guide_session,
        is_supabase_configured
    )
    from services.guide_generator import generate_guide, generate_guide_plan
    USE_DATABASE = is_supabase_configured()
    GUIDE_GENERATOR_AVAILABLE = True
except ImportError:
    USE_DATABASE = False
    GUIDE_GENERATOR_AVAILABLE = False
    db_create_guide_session = None
    db_get_guide_session = None
    db_update_guide_session = None
    generate_guide = None
    generate_guide_plan = None


class GuideStartRequest(BaseModel):
    notebook_ids: List[str]
    max_points: int = 12


class AnswerSubmission(BaseModel):
    step_number: int  # Also represents knowledge_point_number
    question_index: int
    answer: str


class ChatMessage(BaseModel):
    message: str


@router.post("/plan")
async def generate_guide_plan_endpoint(request: GuideStartRequest):
    """Generate a plan for creating a learning guide"""
    if not GUIDE_GENERATOR_AVAILABLE or not generate_guide_plan:
        raise HTTPException(status_code=503, detail="Guide generator not available")
    
    if not request.notebook_ids:
        raise HTTPException(status_code=400, detail="At least one notebook ID is required")
    
    try:
        plan_result = generate_guide_plan(
            notebook_ids=request.notebook_ids,
            max_points=request.max_points
        )
        
        if not plan_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=plan_result.get("error", "Failed to generate guide plan")
            )
        
        return plan_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating guide plan: {str(e)}")


@router.post("/start")
async def start_guide(request: GuideStartRequest):
    """
    Start a guided learning session from notebooks
    
    Analyzes notebook content and generates a structured learning guide
    """
    if not USE_DATABASE or not db_create_guide_session:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    if not GUIDE_GENERATOR_AVAILABLE or not generate_guide:
        raise HTTPException(status_code=503, detail="Guide generator not available")
    
    if not request.notebook_ids:
        raise HTTPException(status_code=400, detail="At least one notebook ID is required")
    
    try:
        # Step 1: Generate guide content
        print(f"[GUIDE] Starting guide generation for {len(request.notebook_ids)} notebooks...")
        guide_result = generate_guide(
            notebook_ids=request.notebook_ids,
            max_points=request.max_points
        )
        
        if not guide_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=guide_result.get("error", "Failed to generate guide")
            )
        
        guide_content = guide_result.get("content", {})
        # Support both old "steps" and new "knowledge_points" format
        total_knowledge_points = guide_content.get("total_knowledge_points") or guide_content.get("total_steps", request.max_points)
        
        # Step 2: Create guide session in database
        session = db_create_guide_session(
            notebook_ids=request.notebook_ids,
            max_points=request.max_points
        )
        
        # Step 3: Update session with generated content
        session = db_update_guide_session(
            session.get("id"),
            total_steps=total_knowledge_points,  # Keep for backward compatibility
            content=guide_content
        )
        
        return {
            "session_id": session.get("id"),
            "status": "active",
            "notebook_ids": request.notebook_ids,
            "current_knowledge_point": 1,
            "total_knowledge_points": total_knowledge_points,
            "content": guide_content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to start guide: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error starting guide: {str(e)}")


@router.get("/{session_id}")
async def get_guide_session(session_id: str):
    """
    Get guided learning session
    
    If questions are missing from steps, generates them automatically
    """
    if not USE_DATABASE or not db_get_guide_session:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        session = db_get_guide_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Guide session not found")
        
        # Check if questions are missing and generate them
        content = session.get("content", {})
        # Support both old "steps" and new "knowledge_points" format
        knowledge_points = content.get("knowledge_points") or content.get("steps", [])
        needs_update = False
        
        for kp in knowledge_points:
            if "questions" not in kp or not kp.get("questions") or len(kp.get("questions", [])) == 0:
                if not GUIDE_GENERATOR_AVAILABLE:
                    print(f"[WARNING] Cannot generate questions - guide generator not available")
                    break
                
                kp_num = kp.get("knowledge_point_number") or kp.get("step_number", "?")
                print(f"[GUIDE] Knowledge point {kp_num} missing questions, generating...")
                
                try:
                    # Import here to avoid circular import issues
                    from services.guide_generator import match_questions_from_notebooks, extract_notebook_content, generate_questions_for_step
                    
                    # Extract content for context
                    notebook_ids = session.get("notebook_ids", [])
                    notebook_content = {}
                    if notebook_ids:
                        try:
                            notebook_content = extract_notebook_content(notebook_ids)
                        except Exception as e:
                            print(f"[WARNING] Could not extract notebook content: {e}")
                            notebook_content = {}
                    
                    # First try to match questions from notebooks
                    matched_questions = match_questions_from_notebooks(kp, notebook_content)
                    
                    if matched_questions and len(matched_questions) >= 2:
                        print(f"[GUIDE] Matched {len(matched_questions)} questions from notebooks")
                        kp["questions"] = matched_questions
                    else:
                        # Fallback: generate questions if none found in notebooks
                        print(f"[GUIDE] No questions found in notebooks, generating...")
                        kp["questions"] = generate_questions_for_step(
                            step=kp,
                            notebook_ids=notebook_ids,
                            content=notebook_content
                        )
                    needs_update = True
                except ImportError as e:
                    print(f"[WARNING] Could not import question generator: {e}")
                    break
                except Exception as e:
                    print(f"[ERROR] Failed to generate questions: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continue without questions rather than failing
                    break
        
        # Update session if questions were generated
        if needs_update:
            session = db_update_guide_session(session_id, content=content)
        
        return session
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to get guide session: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting guide session: {str(e)}")


@router.post("/{session_id}/answer")
async def submit_answer(session_id: str, answer: AnswerSubmission):
    """
    Submit an answer to a question and get feedback
    
    This evaluates the answer and provides adaptive feedback
    """
    if not USE_DATABASE or not db_get_guide_session or not db_update_guide_session:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        # Import guide answer evaluator
        from services.guide_generator import evaluate_answer
        
        session = db_get_guide_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Guide session not found")
        
        content = session.get("content", {})
        # Support both old "steps" and new "knowledge_points" format
        knowledge_points = content.get("knowledge_points") or content.get("steps", [])
        
        # Find the knowledge point (support both step_number and knowledge_point_number)
        kp = None
        for k in knowledge_points:
            if (k.get("knowledge_point_number") == answer.step_number or 
                k.get("step_number") == answer.step_number):
                kp = k
                break
        
        if not kp:
            raise HTTPException(status_code=404, detail="Knowledge point not found")
        
        # Get the question
        questions = kp.get("questions", [])
        if answer.question_index >= len(questions):
            raise HTTPException(status_code=404, detail="Question not found")
        
        question = questions[answer.question_index]
        
        # Evaluate the answer
        evaluation = evaluate_answer(
            question=question,
            user_answer=answer.answer,
            step_content=kp.get("content", ""),
            notebook_ids=session.get("notebook_ids", [])
        )
        
        # Update session with answer history
        session_content = session.get("content", {})
        if "answer_history" not in session_content:
            session_content["answer_history"] = []
        
        session_content["answer_history"].append({
            "knowledge_point_number": answer.step_number,  # Keep step_number for backward compat
            "step_number": answer.step_number,
            "question_index": answer.question_index,
            "answer": answer.answer,
            "evaluation": evaluation,
            "timestamp": None  # Will be set by database
        })
        
        # Track understanding gaps
        if "understanding_gaps" not in session_content:
            session_content["understanding_gaps"] = {}
        
        kp_key = f"knowledge_point_{answer.step_number}"
        kp_key = f"knowledge_point_{answer.step_number}"
        step_key = f"step_{answer.step_number}"  # Keep for backward compat
        
        # Use knowledge_point key, but also set step key for backward compat
        if kp_key not in session_content["understanding_gaps"]:
            session_content["understanding_gaps"][kp_key] = {
                "score": 0,
                "total_questions": 0,
                "needs_review": False
            }
        if step_key not in session_content["understanding_gaps"]:
            session_content["understanding_gaps"][step_key] = session_content["understanding_gaps"][kp_key]
        
        gap_tracker = session_content["understanding_gaps"][kp_key]
        gap_tracker["total_questions"] += 1
        gap_tracker["score"] += evaluation.get("score", 0)
        
        # Mark as needing review if score is low
        avg_score = gap_tracker["score"] / gap_tracker["total_questions"]
        gap_tracker["needs_review"] = avg_score < 0.6  # Below 60%
        
        # Update session
        db_update_guide_session(session_id, content=session_content)
        
        return {
            "session_id": session_id,
            "evaluation": evaluation,
            "understanding_score": avg_score,
            "needs_review": gap_tracker["needs_review"],
            "recommendation": "review_step" if gap_tracker["needs_review"] else "continue"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to evaluate answer: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error evaluating answer: {str(e)}")


@router.post("/{session_id}/next")
async def next_step(session_id: str):
    """
    Move to next knowledge point in the guide
    
    This now includes adaptive logic - if user has understanding gaps,
    it may suggest review or generate additional content
    """
    if not USE_DATABASE or not db_get_guide_session or not db_update_guide_session:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        session = db_get_guide_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Guide session not found")
        
        current_kp = session.get("current_step", 1)  # Keep for backward compat
        content = session.get("content", {})
        total_knowledge_points = content.get("total_knowledge_points") or session.get("total_steps", 1)
        
        # Check for understanding gaps before moving forward
        understanding_gaps = content.get("understanding_gaps", {})
        current_kp_key = f"knowledge_point_{current_kp}"
        current_step_key = f"step_{current_kp}"  # Backward compat
        
        needs_review = False
        gap_info = understanding_gaps.get(current_kp_key) or understanding_gaps.get(current_step_key)
        if gap_info:
            needs_review = gap_info.get("needs_review", False)
        
        if needs_review:
            # Generate additional content to help fill understanding gaps
            try:
                from services.guide_generator import generate_remedial_content
                
                # Get current knowledge point
                knowledge_points = content.get("knowledge_points") or content.get("steps", [])
                current_kp_data = None
                for kp in knowledge_points:
                    kp_num = kp.get("knowledge_point_number") or kp.get("step_number", 0)
                    if kp_num == current_kp:
                        current_kp_data = kp
                        break
                
                if current_kp_data:
                    # Generate remedial content
                    remedial_content = generate_remedial_content(
                        knowledge_point=current_kp_data,
                        understanding_gaps=gap_info,
                        notebook_ids=session.get("notebook_ids", [])
                    )
                    
                    # Add remedial content to knowledge point
                    if "remedial_content" not in current_kp_data:
                        current_kp_data["remedial_content"] = []
                    current_kp_data["remedial_content"].append(remedial_content)
                    
                    # Update session
                    content["knowledge_points"] = knowledge_points
                    db_update_guide_session(session_id, content=content)
                    
                    return {
                        "session_id": session_id,
                        "current_knowledge_point": current_kp,
                        "total_knowledge_points": total_knowledge_points,
                        "message": "Additional content has been generated to help you understand this topic better. Please review it before continuing.",
                        "needs_review": True,
                        "recommendation": "review",
                        "remedial_content": remedial_content
                    }
            except Exception as e:
                print(f"[WARNING] Failed to generate remedial content: {e}")
                import traceback
                traceback.print_exc()
            
            # Fallback: Suggest review before moving forward
            return {
                "session_id": session_id,
                "current_knowledge_point": current_kp,
                "total_knowledge_points": total_knowledge_points,
                "message": "Consider reviewing this knowledge point - your understanding score is below threshold",
                "needs_review": True,
                "recommendation": "review"
            }
        
        if current_kp >= total_knowledge_points:
            # Generate summary and mark as completed
            from services.guide_generator import generate_learning_summary
            
            summary = generate_learning_summary(
                session_id=session_id,
                notebook_ids=session.get("notebook_ids", []),
                content=content
            )
            
            # Update content with summary
            content["summary"] = summary
            session = db_update_guide_session(
                session_id,
                status="completed",
                content=content
            )
            
            return {
                "session_id": session_id,
                "current_knowledge_point": current_kp,
                "total_knowledge_points": total_knowledge_points,
                "message": "🎉 Congratulations! You have completed all knowledge points!",
                "completed": True,
                "summary": summary
            }
        
        # Move to next knowledge point
        new_kp = current_kp + 1
        session = db_update_guide_session(
            session_id,
            current_step=new_kp  # Keep for backward compat
        )
        
        return {
            "session_id": session_id,
            "current_knowledge_point": new_kp,
            "total_knowledge_points": total_knowledge_points,
            "message": f"Moving to knowledge point {new_kp}",
            "completed": False,
            "needs_review": False
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error moving to next knowledge point: {str(e)}")


@router.post("/{session_id}/chat")
async def guide_chat(session_id: str, chat_message: ChatMessage):
    """
    Chat Q&A during guided learning
    
    Uses existing chat service but stores messages in guide session
    """
    if not USE_DATABASE or not db_get_guide_session or not db_update_guide_session:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        # Import chat service
        from services.chat_service import send_chat_message
        
        session = db_get_guide_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Guide session not found")
        
        # Get current knowledge point for context
        current_kp = session.get("current_step", 1)
        content = session.get("content", {})
        knowledge_points = content.get("knowledge_points") or content.get("steps", [])
        
        # Find current knowledge point
        current_kp_data = None
        for kp in knowledge_points:
            kp_num = kp.get("knowledge_point_number") or kp.get("step_number", 0)
            if kp_num == current_kp:
                current_kp_data = kp
                break
        
        # Build context from current knowledge point
        kp_context = ""
        rag_context = ""
        citations = []
        
        if current_kp_data:
            kp_title = current_kp_data.get('knowledge_title') or current_kp_data.get('title', '')
            kp_content = current_kp_data.get('content', '')
            kp_description = current_kp_data.get('description', '')
            kp_key_points = current_kp_data.get('key_points', [])
            
            # Handle both old format (string) and new format (structured dict)
            if isinstance(kp_content, dict):
                # New structured format - convert to readable text
                content_parts = []
                if kp_content.get('intuition'):
                    content_parts.append(f"INTUITION: {kp_content['intuition']}")
                if kp_content.get('definition'):
                    content_parts.append(f"DEFINITION: {kp_content['definition']}")
                if kp_content.get('how_it_works'):
                    content_parts.append(f"HOW IT WORKS: {kp_content['how_it_works']}")
                if kp_content.get('why_it_matters'):
                    content_parts.append(f"WHY IT MATTERS: {kp_content['why_it_matters']}")
                if kp_content.get('examples'):
                    examples_text = "\n".join(f"- {ex}" for ex in kp_content['examples'])
                    content_parts.append(f"EXAMPLES:\n{examples_text}")
                if kp_content.get('common_mistakes'):
                    mistakes_text = "\n".join(f"- {mistake}" for mistake in kp_content['common_mistakes'])
                    content_parts.append(f"COMMON MISTAKES:\n{mistakes_text}")
                kp_content_text = "\n\n".join(content_parts)
            else:
                # Old format - string content
                kp_content_text = str(kp_content) if kp_content else ""
            
            # Limit content length for context
            kp_content_text = kp_content_text[:3000] if len(kp_content_text) > 3000 else kp_content_text
            
            # Try to get RAG context from notebook content if available
            try:
                from services.rag import ask_question
                from services.guide_generator import extract_notebook_content
                
                # Extract notebook content and create a temporary search
                notebook_ids = session.get("notebook_ids", [])
                if notebook_ids:
                    # Use the user's question to search notebook content
                    # For now, we'll use the knowledge point content directly
                    # TODO: When notebook chunking is implemented, use vector search here
                    pass
            except Exception as e:
                print(f"[GUIDE CHAT] RAG not available: {e}")
            
            kp_context = f"""You are a strict tutor helping a student learn about: {kp_title}

CURRENT LEARNING TOPIC: {kp_title}

LEARNING CONTENT (ONLY SOURCE OF INFORMATION):
{kp_content_text}

DESCRIPTION: {kp_description}

KEY POINTS:
{chr(10).join(f"- {point}" for point in kp_key_points[:5])}

CRITICAL RULES:
1. **ONLY answer questions about "{kp_title}" and the learning content provided above**
2. **DO NOT answer questions about unrelated topics** (e.g., if learning about "heat budget", do NOT answer questions about Russia/Ukraine, history, politics, or any other unrelated topics)
3. **If the student asks about something unrelated**, politely redirect them: "I'm here to help you learn about {kp_title}. Your question seems to be about a different topic. Could you ask something about {kp_title} instead? For example: [suggest a relevant question based on the content]"
4. **If the question is partially related**, clarify the connection to the current topic or redirect if it's too far off
5. **Stay focused** - only use information from the learning content above. Do not bring in external knowledge unless it directly relates to the current topic

EXAMPLES:
- If student asks "tell me about Russia and Ukraine" while learning about "heat budget": 
  Response: "I'm here to help you learn about heat budget and the Earth's energy balance. Your question about Russia and Ukraine is not related to our current topic. Could you ask something about heat budget instead? For example, you could ask about how solar radiation affects Earth's temperature or how the heat budget is balanced."

- If student asks "what is insolation?" while learning about "heat budget":
  Response: "Great question! Insolation (incoming solar radiation) is a key part of the heat budget. [Explain using the learning content]"

Remember: Your ONLY job is to help the student understand "{kp_title}" using the learning content provided. Stay on topic!"""
        
        # Get chat history for this knowledge point
        session_content = session.get("content", {})
        chat_history = session_content.get("chat_history", [])
        kp_chat_history = [
            msg for msg in chat_history 
            if msg.get("knowledge_point_number") == current_kp
        ][-5:]  # Last 5 messages for this knowledge point
        
        # Build messages with context
        from services.guide_generator import is_guide_configured
        from openai import OpenAI
        import os
        
        if not is_guide_configured():
            raise HTTPException(status_code=503, detail="OpenAI API not configured")
        
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
        
        # Build messages
        messages = [
            {
                "role": "system",
                "content": kp_context if kp_context else "You are a helpful AI tutor. Answer questions clearly and conversationally."
            }
        ]
        
        # Add chat history
        for msg in kp_chat_history:
            if msg.get("role") in ["user", "assistant"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg.get("message", "")
                })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": chat_message.message
        })
        
        # Generate response
        http_client = None
        try:
            from services.embeddings import create_http_client
            http_client = create_http_client(timeout=60.0) if create_http_client else None
        except:
            pass
        
        if http_client:
            client = OpenAI(http_client=http_client)
        else:
            client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
        )
        
        assistant_response = response.choices[0].message.content.strip()
        
        chat_result = {
            "success": True,
            "response": assistant_response,
            "citations": []
        }
        
        if not chat_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=chat_result.get("error", "Failed to generate response")
            )
        
        # Store chat message in guide session
        session_content = session.get("content", {})
        if "chat_history" not in session_content:
            session_content["chat_history"] = []
        
        session_content["chat_history"].append({
            "knowledge_point_number": current_kp,
            "role": "user",
            "message": chat_message.message,
            "timestamp": None
        })
        
        session_content["chat_history"].append({
            "knowledge_point_number": current_kp,
            "role": "assistant",
            "message": chat_result.get("response", ""),
            "timestamp": None
        })
        
        # Update session
        db_update_guide_session(session_id, content=session_content)
        
        return {
            "success": True,
            "answer": chat_result.get("response", ""),
            "knowledge_point_number": current_kp,
            "citations": chat_result.get("citations", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to handle chat: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error handling chat: {str(e)}")








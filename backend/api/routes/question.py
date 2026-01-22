"""
Question Generator API Routes
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter()


class QuestionGenerateRequest(BaseModel):
    knowledge_base_id: str
    topic: str  # Also accepts "knowledge_point" - same thing
    difficulty: str = "medium"
    question_type: str = "multiple_choice"
    count: int = 5


class MimicRequest(BaseModel):
    knowledge_base_id: str
    exam_paper_id: Optional[str] = None


class EvaluateAnswerRequest(BaseModel):
    question: Dict[str, Any]  # The question object
    user_answer: str
    knowledge_point: Optional[str] = None
    knowledge_base_id: Optional[str] = None
    auto_save_to_notebook: bool = True  # Auto-save wrong answers


@router.post("/generate")
async def generate_questions(request: QuestionGenerateRequest):
    """
    Generate practice questions from knowledge base using RAG
    
    Uses RAG to retrieve relevant content, then generates questions
    matching the specified requirements (topic, difficulty, type)
    """
    try:
        # Import question generator service
        from services.question_generator import generate_questions as gen_questions
        
        # Verify knowledge base exists
        from database.db import get_knowledge_base
        kb = get_knowledge_base(request.knowledge_base_id)
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        # Generate questions
        result = gen_questions(
            kb_id=request.knowledge_base_id,
            knowledge_point=request.topic,
            difficulty=request.difficulty,
            question_type=request.question_type,
            count=request.count
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to generate questions")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/mimic")
async def mimic_questions(request: MimicRequest, file: UploadFile = File(...)):
    """Generate questions mimicking exam paper style"""
    # TODO: Implement actual logic
    return {
        "question_id": "q_mimic_001",
        "questions": [],
        "status": "generated",
        "message": f"Questions generated from {file.filename}"
    }


@router.get("/{question_id}")
async def get_questions(question_id: str):
    """Get generated questions"""
    # TODO: Implement actual logic
    return {
        "question_id": question_id,
        "questions": []
    }


@router.post("/evaluate")
async def evaluate_answer(request: EvaluateAnswerRequest):
    """
    Evaluate a user's answer to a question
    
    If the answer is wrong (score < 0.6), automatically saves to a "Learning Gaps" notebook
    for tracking what the user needs to review.
    """
    try:
        from services.guide_generator import evaluate_answer as eval_answer
        
        # Build context for evaluation
        # Include knowledge point and question text for better evaluation
        context_parts = []
        if request.knowledge_point:
            context_parts.append(f"Topic: {request.knowledge_point}")
        context_parts.append(f"Question: {request.question.get('question', '')}")
        step_content = "\n".join(context_parts)
        
        # Evaluate the answer
        evaluation = eval_answer(
            question=request.question,
            user_answer=request.user_answer,
            step_content=step_content,
            notebook_ids=[]  # Not needed for evaluation
        )
        
        # Auto-save wrong answers to notebook if enabled
        saved_to_notebook = False
        notebook_item_id = None
        
        if request.auto_save_to_notebook and evaluation.get("score", 1.0) < 0.6:
            # Score below 60% - save to notebook for learning gap tracking
            try:
                from database.db import list_notebooks, create_notebook, create_notebook_item
                from database.db import USE_DATABASE
                
                if USE_DATABASE:
                    # Find or create "Learning Gaps" notebook
                    notebooks = list_notebooks()
                    learning_gaps_notebook = None
                    
                    for nb in notebooks:
                        if nb.get("name", "").lower() in ["learning gaps", "learning gaps notebook", "wrong answers"]:
                            learning_gaps_notebook = nb
                            break
                    
                    if not learning_gaps_notebook:
                        # Create "Learning Gaps" notebook
                        learning_gaps_notebook = create_notebook(
                            name="Learning Gaps",
                            description="Automatically saved questions you got wrong - review these to improve!",
                            color="#ef4444",  # Red color
                            icon="📝"
                        )
                    
                    # Save wrong answer as a "solve" item (question + wrong answer + correct answer)
                    question_text = request.question.get("question", "")
                    correct_answer = request.question.get("answer", "")
                    
                    item = create_notebook_item(
                        notebook_id=learning_gaps_notebook.get("id"),
                        item_type="solve",
                        title=f"Question: {question_text[:100]}",
                        content={
                            "question": question_text,
                            "user_answer": request.user_answer,
                            "correct_answer": correct_answer,
                            "evaluation": evaluation,
                            "knowledge_point": request.knowledge_point,
                            "knowledge_base_id": request.knowledge_base_id,
                            "question_type": request.question.get("type", ""),
                            "difficulty": request.question.get("difficulty", ""),
                            "auto_saved": True  # Mark as auto-saved
                        }
                    )
                    
                    saved_to_notebook = True
                    notebook_item_id = item.get("id")
                    
            except Exception as e:
                print(f"[WARNING] Failed to auto-save wrong answer to notebook: {e}")
                import traceback
                traceback.print_exc()
                # Continue even if save fails
        
        return {
            "success": True,
            "evaluation": evaluation,
            "saved_to_notebook": saved_to_notebook,
            "notebook_item_id": notebook_item_id,
            "message": "Answer evaluated successfully" + (
                ". Saved to Learning Gaps notebook for review." if saved_to_notebook else ""
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to evaluate answer: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error evaluating answer: {str(e)}")







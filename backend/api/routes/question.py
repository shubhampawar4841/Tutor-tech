"""
Question Generator API Routes
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, List

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







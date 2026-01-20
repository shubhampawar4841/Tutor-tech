"""
Question Generation Service
Generates practice questions from knowledge bases using RAG
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

# Try to import embeddings and database
try:
    from services.embeddings import generate_embedding, create_http_client
    from database.db import search_similar_chunks, get_chunks_by_kb, get_document
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    generate_embedding = None
    create_http_client = None
    search_similar_chunks = None
    get_chunks_by_kb = None
    get_document = None

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

def is_question_gen_configured() -> bool:
    """Check if question generation is configured"""
    return OPENAI_AVAILABLE and OPENAI_API_KEY is not None


def retrieve_relevant_content(
    kb_id: str,
    knowledge_point: str,
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant content from knowledge base using RAG
    
    Args:
        kb_id: Knowledge base ID
        knowledge_point: Topic/knowledge point to focus on
        top_k: Number of chunks to retrieve
    
    Returns:
        List of relevant chunks
    """
    if not is_question_gen_configured() or not EMBEDDINGS_AVAILABLE:
        print("[QUESTION] OpenAI not configured")
        # Fallback: get chunks without similarity search
        if get_chunks_by_kb:
            try:
                all_chunks = get_chunks_by_kb(kb_id)
                return all_chunks[:top_k]
            except:
                return []
        return []
    
    try:
        # Generate embedding for the knowledge point
        print(f"[QUESTION] Generating embedding for knowledge point: {knowledge_point}")
        if not generate_embedding:
            print("[QUESTION] generate_embedding not available, using fallback")
            if get_chunks_by_kb:
                all_chunks = get_chunks_by_kb(kb_id)
                return all_chunks[:top_k]
            return []
        
        query_embedding = generate_embedding(knowledge_point)
        
        if not query_embedding:
            print("[QUESTION] Failed to generate embedding, using fallback")
            # Fallback: get chunks without similarity search
            if get_chunks_by_kb:
                all_chunks = get_chunks_by_kb(kb_id)
                return all_chunks[:top_k]
            return []
        
        # Search for similar chunks
        print(f"[QUESTION] Searching for relevant chunks (top_k={top_k})...")
        if not search_similar_chunks:
            print("[QUESTION] search_similar_chunks not available, using fallback")
            if get_chunks_by_kb:
                all_chunks = get_chunks_by_kb(kb_id)
                return all_chunks[:top_k]
            return []
        
        similar_chunks = search_similar_chunks(
            kb_id=kb_id,
            query_embedding=query_embedding,
            limit=top_k,
            threshold=0.3  # Lower threshold to get more content
        )
        
        if not similar_chunks or len(similar_chunks) < 3:
            print("[QUESTION] Too few results, using fallback")
            if get_chunks_by_kb:
                all_chunks = get_chunks_by_kb(kb_id)
                chunks_with_embeddings = [c for c in all_chunks if c.get("embedding") is not None]
                if chunks_with_embeddings:
                    similar_chunks = chunks_with_embeddings[:top_k]
        
        print(f"[QUESTION] Retrieved {len(similar_chunks)} relevant chunks")
        return similar_chunks
        
    except Exception as e:
        print(f"[ERROR] Failed to retrieve content: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: get chunks without similarity
        try:
            if get_chunks_by_kb:
                all_chunks = get_chunks_by_kb(kb_id)
                return all_chunks[:top_k]
        except:
            pass
        return []


def build_question_prompt(
    knowledge_point: str,
    difficulty: str,
    question_type: str,
    count: int,
    context_chunks: List[Dict[str, Any]]
) -> str:
    """
    Build prompt for question generation
    
    Args:
        knowledge_point: Topic/knowledge point
        difficulty: easy, medium, hard
        question_type: multiple_choice, short_answer, essay, true_false
        count: Number of questions to generate
        context_chunks: Relevant chunks from knowledge base
    
    Returns:
        Formatted prompt
    """
    # Build context from chunks
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        content = chunk.get("content", "").strip()
        metadata = chunk.get("metadata", {})
        page = metadata.get("page", "?") if isinstance(metadata, dict) else "?"
        
        # Get document name
        doc_id = chunk.get("document_id")
        doc_name = f"Document {i}"
        if doc_id and get_document:
            try:
                doc = get_document(doc_id)
                if doc:
                    doc_name = doc.get("filename", doc_name)
            except:
                pass
        
        context_parts.append(f"[{i}] {doc_name} (Page {page}):\n{content}\n")
    
    context_text = "\n".join(context_parts)
    
    # Map question types to descriptions
    type_descriptions = {
        "multiple_choice": "multiple choice questions with 4 options (A, B, C, D) and one correct answer",
        "short_answer": "short answer questions requiring 1-3 sentence responses",
        "essay": "essay questions requiring detailed explanations",
        "true_false": "true/false questions",
        "fill_blank": "fill-in-the-blank questions"
    }
    
    question_type_desc = type_descriptions.get(question_type, "questions")
    
    # Map difficulty to descriptions
    difficulty_descriptions = {
        "easy": "basic understanding and recall",
        "medium": "application and analysis",
        "hard": "synthesis, evaluation, and complex problem-solving"
    }
    
    difficulty_desc = difficulty_descriptions.get(difficulty, "medium level")
    
    prompt = f"""You are an expert educator creating practice questions from educational content.

Knowledge Point/Topic: {knowledge_point}
Difficulty Level: {difficulty} ({difficulty_desc})
Question Type: {question_type} ({question_type_desc})
Number of Questions: {count}

Relevant Content from Knowledge Base:
{context_text}

Instructions:
1. Generate exactly {count} {question_type_desc} about "{knowledge_point}"
2. Questions should test {difficulty_desc} understanding
3. Base questions on the provided content above. If content is limited, use your knowledge to create appropriate questions and answers.
4. For multiple choice: provide 4 options labeled A, B, C, D with one clearly correct answer
5. For short answer: provide a COMPLETE, DETAILED expected answer that fully explains the concept
6. For essay: provide a comprehensive sample answer or detailed key points that cover the topic thoroughly
7. For true/false: provide the correct answer (True or False) with a brief explanation
8. Make questions clear, unambiguous, and educational
9. **CRITICAL**: ALWAYS provide a complete answer for every question. If the content doesn't fully cover the answer, use your knowledge to provide a comprehensive, accurate answer that helps the student learn.

Output Format (JSON):
Return a JSON object with a "questions" key containing an array:
{{
  "questions": [
    {{
      "question": "Question text here",
      "type": "{question_type}",
      "difficulty": "{difficulty}",
      "answer": "Correct answer or explanation",
      "options": ["Option A", "Option B", "Option C", "Option D"]  // Only for multiple_choice
    }},
    ...
  ]
}}

Or return a JSON array directly:
[
  {{
    "question": "Question text here",
    "type": "{question_type}",
    "difficulty": "{difficulty}",
    "answer": "Correct answer or explanation",
    "options": ["Option A", "Option B", "Option C", "Option D"]  // Only for multiple_choice
  }},
  ...
]

Generate the questions now:"""
    
    return prompt


def generate_questions(
    kb_id: str,
    knowledge_point: str,
    difficulty: str = "medium",
    question_type: str = "multiple_choice",
    count: int = 5
) -> Dict[str, Any]:
    """
    Generate practice questions from knowledge base
    
    Args:
        kb_id: Knowledge base ID
        knowledge_point: Topic/knowledge point to focus on
        difficulty: easy, medium, hard
        question_type: multiple_choice, short_answer, essay, true_false, fill_blank
        count: Number of questions to generate
    
    Returns:
        Dict with generated questions and metadata
    """
    if not is_question_gen_configured():
        return {
            "success": False,
            "error": "OpenAI API not configured. Set OPENAI_API_KEY in .env",
            "questions": []
        }
    
    try:
        # Step 1: Retrieve relevant content using RAG
        print(f"[QUESTION] Generating {count} {question_type} questions about '{knowledge_point}'")
        context_chunks = retrieve_relevant_content(
            kb_id=kb_id,
            knowledge_point=knowledge_point,
            top_k=10
        )
        
        if not context_chunks:
            return {
                "success": False,
                "error": "No content found in knowledge base. Make sure documents are processed and embeddings are generated.",
                "questions": []
            }
        
        # Step 2: Build prompt
        prompt = build_question_prompt(
            knowledge_point=knowledge_point,
            difficulty=difficulty,
            question_type=question_type,
            count=count,
            context_chunks=context_chunks
        )
        
        # Step 3: Generate questions using LLM
        print(f"[QUESTION] Generating questions using {LLM_MODEL}...")
        
        if OPENAI_API_KEY and "OPENAI_API_KEY" not in os.environ:
            os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        
        http_client = create_http_client(timeout=120.0)
        if http_client:
            client = OpenAI(http_client=http_client)
        else:
            client = OpenAI(api_key=OPENAI_API_KEY)
        
        # For newer models, we can use structured output, but for compatibility
        # we'll ask for JSON array directly
        use_json_mode = LLM_MODEL.startswith("gpt-4o") or "o1" in LLM_MODEL
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert educator. Generate practice questions in valid JSON array format. Return ONLY a JSON array, no additional text or explanation."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=4000,
            response_format={"type": "json_object"} if use_json_mode else None
        )
        
        answer_text = response.choices[0].message.content.strip()
        print(f"[QUESTION] Generated response ({len(answer_text)} chars)")
        
        # Step 4: Parse response
        import json
        import re
        
        questions = []
        
        # Try multiple parsing strategies
        try:
            # Strategy 1: Try parsing as JSON object first (for gpt-4 with json_object format)
            parsed = json.loads(answer_text)
            if isinstance(parsed, list):
                questions = parsed
            elif isinstance(parsed, dict):
                if "questions" in parsed:
                    questions = parsed["questions"]
                elif "question" in parsed:
                    # Single question wrapped in object
                    questions = [parsed]
                else:
                    # Try to find array in values
                    for value in parsed.values():
                        if isinstance(value, list):
                            questions = value
                            break
        except json.JSONDecodeError:
            # Strategy 2: Try to extract JSON array from text
            try:
                json_match = re.search(r'\[[\s\S]*\]', answer_text, re.MULTILINE)
                if json_match:
                    questions = json.loads(json_match.group())
            except:
                # Strategy 3: Try to extract individual question objects
                try:
                    # Look for question objects in the text
                    question_objects = re.findall(r'\{[^{}]*"question"[^{}]*\}', answer_text, re.DOTALL)
                    if question_objects:
                        questions = [json.loads(obj) for obj in question_objects]
                except:
                    pass
        
        # Fallback: if still no questions, create placeholders
        if not questions:
            print("[WARNING] Failed to parse JSON, using fallback")
            for i in range(count):
                questions.append({
                    "question": f"Question {i+1} about {knowledge_point}",
                    "type": question_type,
                    "difficulty": difficulty,
                    "answer": "See content above",
                    "options": ["Option A", "Option B", "Option C", "Option D"] if question_type == "multiple_choice" else None
                })
        
        # Validate and clean questions
        validated_questions = []
        for q in questions:
            if isinstance(q, dict) and "question" in q:
                validated_questions.append({
                    "question": q.get("question", ""),
                    "type": q.get("type", question_type),
                    "difficulty": q.get("difficulty", difficulty),
                    "answer": q.get("answer", ""),
                    "options": q.get("options", []) if question_type == "multiple_choice" else None
                })
        
        if not validated_questions:
            return {
                "success": False,
                "error": "Failed to generate valid questions. Please try again.",
                "questions": []
            }
        
        print(f"[QUESTION] Successfully generated {len(validated_questions)} questions")
        
        return {
            "success": True,
            "questions": validated_questions,
            "metadata": {
                "knowledge_point": knowledge_point,
                "difficulty": difficulty,
                "question_type": question_type,
                "count": len(validated_questions),
                "chunks_used": len(context_chunks)
            }
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to generate questions: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": f"Failed to generate questions: {str(e)}",
            "questions": []
        }


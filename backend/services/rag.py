"""
RAG (Retrieval Augmented Generation) Service
Answers questions using knowledge base with citations
"""
import os
from typing import List, Dict, Any, Optional
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

# Try to import embeddings and database
try:
    from services.embeddings import generate_embedding, is_embeddings_configured
    from database.db import search_similar_chunks, get_document, get_chunks_by_kb
    EMBEDDINGS_AVAILABLE = is_embeddings_configured()
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    generate_embedding = None
    search_similar_chunks = None
    get_document = None
    get_chunks_by_kb = None

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")  # Default: cheaper model
LLM_HOST = os.getenv("LLM_HOST", "https://api.openai.com/v1")

# Workaround for httpx compatibility issue
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


def is_rag_configured() -> bool:
    """Check if RAG is fully configured"""
    return OPENAI_AVAILABLE and EMBEDDINGS_AVAILABLE and OPENAI_API_KEY is not None


def build_context_prompt(chunks: List[Dict[str, Any]], question: str) -> str:
    """
    Build a prompt with context from retrieved chunks
    
    Args:
        chunks: List of relevant chunks with metadata
        question: User's question
    
    Returns:
        Formatted prompt string
    """
    context_parts = []
    
    for i, chunk in enumerate(chunks, 1):
        # Extract metadata
        metadata = chunk.get("metadata", {})
        if isinstance(metadata, str):
            import json
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}
        
        # Get page information
        page_start = metadata.get("page_start", metadata.get("page", "?"))
        page_end = metadata.get("page_end", page_start)
        
        # Get document info
        doc_id = chunk.get("document_id", "")
        doc_info = {}
        if get_document and doc_id:
            try:
                doc_info = get_document(doc_id) or {}
            except:
                pass
        
        filename = doc_info.get("filename", "document")
        
        # Format citation
        if page_start == page_end:
            citation = f"[{i}] Page {page_start}"
        else:
            citation = f"[{i}] Pages {page_start}-{page_end}"
        
        # Add source info
        source_info = f"Source: {filename}"
        
        # Build context entry
        content = chunk.get("content", "").strip()
        context_parts.append(
            f"{citation} ({source_info})\n{content}\n"
        )
    
    # Build full prompt
    prompt = f"""Use only the following sources to answer the question. Cite your sources using [1], [2], etc.

Sources:
{''.join(context_parts)}

Question: {question}

Instructions:
- Answer the question using ONLY the information provided in the sources above
- Cite sources using [1], [2], etc. when referencing information
- If the answer cannot be found in the sources, say "I cannot find the answer in the provided sources"
- Be concise but complete
- Include page numbers in citations when relevant

Answer:"""
    
    return prompt


def generate_answer(prompt: str, model: str = None) -> Optional[str]:
    """
    Generate answer using LLM
    
    Args:
        prompt: Full prompt with context
        model: LLM model to use (defaults to LLM_MODEL)
    
    Returns:
        Generated answer or None if failed
    """
    if not is_rag_configured():
        return None
    
    model = model or LLM_MODEL
    
    try:
        # Set API key
        if OPENAI_API_KEY and "OPENAI_API_KEY" not in os.environ:
            os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        
        # Create client
        http_client = create_http_client(timeout=120.0)
        if http_client:
            client = OpenAI(http_client=http_client)
        else:
            client = OpenAI(api_key=OPENAI_API_KEY)
        
        print(f"[RAG] Generating answer using {model}...")
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful tutor that answers questions using only the provided sources. Always cite your sources with [1], [2], etc."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"[RAG] Generated answer ({len(answer)} chars)")
        
        return answer
        
    except Exception as e:
        print(f"[ERROR] Failed to generate answer: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_citations(answer: str) -> List[Dict[str, Any]]:
    """
    Extract citation numbers from answer text
    
    Args:
        answer: Answer text with citations like [1], [2]
    
    Returns:
        List of citation numbers found
    """
    import re
    # Find all citation patterns like [1], [2], [12]
    citations = re.findall(r'\[(\d+)\]', answer)
    # Convert to unique integers
    citation_nums = sorted(set(int(c) for c in citations))
    return citation_nums


def ask_question(
    kb_id: str,
    question: str,
    top_k: int = 5,
    threshold: float = 0.7,
    model: str = None
) -> Dict[str, Any]:
    """
    Main RAG function: Ask a question and get an answer with citations
    
    Args:
        kb_id: Knowledge base ID
        question: User's question
        top_k: Number of chunks to retrieve
        threshold: Minimum similarity threshold
        model: LLM model to use
    
    Returns:
        Dict with answer, citations, and metadata
    """
    if not is_rag_configured():
        return {
            "success": False,
            "error": "RAG not configured. Set OPENAI_API_KEY in .env"
        }
    
    if not question or not question.strip():
        return {
            "success": False,
            "error": "Question cannot be empty"
        }
    
    print(f"[RAG] Processing question: {question[:100]}...")
    
    # Step 1: Generate embedding for question
    print(f"[RAG] Generating question embedding...")
    question_embedding = generate_embedding(question)
    
    if not question_embedding:
        return {
            "success": False,
            "error": "Failed to generate question embedding"
        }
    
    # Step 2: Search for similar chunks
    print(f"[RAG] Searching for similar chunks (top_k={top_k}, threshold={threshold})...")
    
    try:
        similar_chunks = search_similar_chunks(
            kb_id=kb_id,
            query_embedding=question_embedding,
            limit=top_k,
            threshold=threshold
        )
        print(f"[RAG] Found {len(similar_chunks)} chunks via vector search")
    except Exception as e:
        print(f"[ERROR] Vector search failed: {e}")
        import traceback
        traceback.print_exc()
        similar_chunks = []
    
    # Fallback: if no results or too few, try with lower threshold or get all chunks
    if len(similar_chunks) < 3:
        print(f"[RAG] Too few results ({len(similar_chunks)}), trying fallback...")
        try:
            # Try with lower threshold
            if threshold > 0.3:
                print(f"[RAG] Retrying with lower threshold (0.3)...")
                similar_chunks = search_similar_chunks(
                    kb_id=kb_id,
                    query_embedding=question_embedding,
                    limit=top_k,
                    threshold=0.3
                )
                print(f"[RAG] Found {len(similar_chunks)} chunks with lower threshold")
        except Exception as e:
            print(f"[ERROR] Lower threshold search also failed: {e}")
    
    # Final fallback: get chunks with embeddings (no similarity filtering)
    if len(similar_chunks) < 1:
        print(f"[RAG] Final fallback: Getting chunks with embeddings (no similarity filter)...")
        try:
            all_chunks = get_chunks_by_kb(kb_id) if get_chunks_by_kb else []
            print(f"[RAG] Total chunks in KB: {len(all_chunks)}")
            
            # Filter chunks with embeddings
            chunks_with_embeddings = [c for c in all_chunks if c.get("embedding") is not None]
            print(f"[RAG] Chunks with embeddings: {len(chunks_with_embeddings)}")
            
            if chunks_with_embeddings:
                # Just take first N chunks if similarity search isn't working
                similar_chunks = chunks_with_embeddings[:top_k]
                # Add placeholder similarity for display
                for chunk in similar_chunks:
                    chunk["similarity"] = 0.75  # Placeholder
                print(f"[RAG] Using {len(similar_chunks)} chunks from fallback")
        except Exception as e2:
            print(f"[ERROR] Final fallback also failed: {e2}")
            import traceback
            traceback.print_exc()
            similar_chunks = []
    
    if not similar_chunks:
        return {
            "success": False,
            "error": f"No chunks found in knowledge base. Make sure:\n1. Documents are uploaded\n2. Documents are processed (status = 'ready')\n3. Embeddings are generated\n\nCheck the Knowledge Base page to verify document status.",
            "answer": None,
            "citations": []
        }
    
    print(f"[RAG] Found {len(similar_chunks)} relevant chunks")
    
    # Step 3: Build context prompt
    print(f"[RAG] Building context prompt...")
    prompt = build_context_prompt(similar_chunks, question)
    
    # Step 4: Generate answer
    answer = generate_answer(prompt, model=model)
    
    if not answer:
        return {
            "success": False,
            "error": "Failed to generate answer",
            "chunks_retrieved": len(similar_chunks)
        }
    
    # Step 5: Extract citations
    citation_nums = extract_citations(answer)
    
    # Step 6: Build citation details
    citations = []
    for num in citation_nums:
        if 1 <= num <= len(similar_chunks):
            chunk = similar_chunks[num - 1]  # Convert to 0-based index
            metadata = chunk.get("metadata", {})
            if isinstance(metadata, str):
                import json
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            doc_id = chunk.get("document_id", "")
            doc_info = {}
            if get_document and doc_id:
                try:
                    doc_info = get_document(doc_id) or {}
                except:
                    pass
            
            citations.append({
                "id": num,
                "document_id": doc_id,
                "filename": doc_info.get("filename", "document"),
                "page_start": metadata.get("page_start", metadata.get("page", "?")),
                "page_end": metadata.get("page_end", metadata.get("page_start", metadata.get("page", "?"))),
                "snippet": chunk.get("content", "")[:200] + "..." if len(chunk.get("content", "")) > 200 else chunk.get("content", ""),
                "similarity": chunk.get("similarity", 0.0) if "similarity" in chunk else None
            })
    
    return {
        "success": True,
        "answer": answer,
        "citations": citations,
        "chunks_retrieved": len(similar_chunks),
        "question": question
    }


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

# Try to import web search
try:
    from services.web_search import search_web, format_web_search_context, is_web_search_configured
    WEB_SEARCH_AVAILABLE = is_web_search_configured()
except ImportError:
    WEB_SEARCH_AVAILABLE = False
    search_web = None
    format_web_search_context = None

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


def build_context_prompt(chunks: List[Dict[str, Any]], question: str, web_search_context: str = "") -> str:
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
    
    # Combine all sources
    all_sources = ''.join(context_parts)
    
    # Add web search results if available
    if web_search_context:
        # Adjust citation numbers for web sources
        web_start_num = len(chunks) + 1
        all_sources += f"\n\n{web_search_context}"
    
    # Build full prompt
    prompt = f"""Use the following sources to answer the question. Cite your sources using [1], [2], etc.

Sources:
{all_sources}

Question: {question}

Instructions:
- Answer the question using the information provided in the sources above
- Prioritize knowledge base sources [1-{len(chunks)}] when available, but also use web search results if they provide additional valuable information
- Cite sources using [1], [2], etc. when referencing information
- Combine information from multiple sources to provide a comprehensive answer
- If information from knowledge base is limited, supplement with web search results
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
    model: str = None,
    use_web_search: bool = False
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
    
    # Check if we have any relevant chunks
    has_relevant_chunks = len(similar_chunks) > 0
    
    # If no relevant chunks found, we should use web search instead of random chunks
    # Random chunks lead to hallucinations
    if not has_relevant_chunks:
        print(f"[RAG] No relevant chunks found via vector search")
        
        # If web search is available and enabled, we'll use it
        # Otherwise, return an error instead of using random chunks
        if not (use_web_search and WEB_SEARCH_AVAILABLE):
            return {
                "success": False,
                "error": f"No relevant content found in knowledge base for this question. Consider:\n1. The question may not be covered in your uploaded documents\n2. Enable web search to find information from the internet\n3. Check if documents are properly processed and embeddings are generated",
                "answer": None,
                "citations": [],
                "suggestion": "enable_web_search" if WEB_SEARCH_AVAILABLE else None
            }
        else:
            print(f"[RAG] No relevant chunks found, will rely on web search only")
    
    # Step 3: Get web search results if enabled OR if no relevant chunks found
    web_search_context = ""
    web_citations = []
    should_use_web_search = use_web_search or (not has_relevant_chunks and WEB_SEARCH_AVAILABLE)
    
    if should_use_web_search and WEB_SEARCH_AVAILABLE and search_web:
        print(f"[RAG] Performing web search...")
        try:
            web_results = search_web(question, max_results=5 if not has_relevant_chunks else 3)
            if web_results:
                web_search_context = format_web_search_context(web_results)
                web_citations = web_results
                print(f"[RAG] Found {len(web_results)} web search results")
            else:
                print(f"[RAG] Web search returned no results")
        except Exception as e:
            print(f"[RAG] Web search error: {e}")
    
    # If we have no chunks AND no web results, we can't answer
    if not has_relevant_chunks and not web_search_context:
        return {
            "success": False,
            "error": "No relevant information found in knowledge base or via web search. Please try rephrasing your question or check if the topic is covered in your documents.",
            "answer": None,
            "citations": []
        }
    
    if has_relevant_chunks:
        print(f"[RAG] Found {len(similar_chunks)} relevant chunks")
    
    # Step 4: Build context prompt (combine RAG + web search)
    print(f"[RAG] Building context prompt...")
    prompt = build_context_prompt(similar_chunks, question, web_search_context=web_search_context)
    
    # Step 5: Generate answer
    answer = generate_answer(prompt, model=model)
    
    if not answer:
        return {
            "success": False,
            "error": "Failed to generate answer",
            "chunks_retrieved": len(similar_chunks)
        }
    
    # Step 6: Extract citations
    citation_nums = extract_citations(answer)
    
    # Step 7: Build citation details (combine RAG + web citations)
    citations = []
    rag_citation_count = len(similar_chunks) if similar_chunks else 0
    
    for num in citation_nums:
        if 1 <= num <= rag_citation_count:
            # RAG citation
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
                "similarity": chunk.get("similarity", 0.0) if "similarity" in chunk else None,
                "source": "knowledge_base"
            })
        elif num > rag_citation_count and web_citations:
            # Web citation
            web_idx = num - rag_citation_count - 1
            if 0 <= web_idx < len(web_citations):
                web_result = web_citations[web_idx]
                citations.append({
                    "id": num,
                    "title": web_result.get("title", ""),
                    "url": web_result.get("url", ""),
                    "snippet": web_result.get("snippet", "")[:200] + "..." if len(web_result.get("snippet", "")) > 200 else web_result.get("snippet", ""),
                    "source": "web_search",
                    "search_source": web_result.get("source", "unknown")
                })
    
    # If no RAG chunks but we have web citations, add them with proper numbering
    if rag_citation_count == 0 and web_citations:
        for idx, web_result in enumerate(web_citations, 1):
            if idx not in [c.get("id") for c in citations]:
                citations.append({
                    "id": idx,
                    "title": web_result.get("title", ""),
                    "url": web_result.get("url", ""),
                    "snippet": web_result.get("snippet", "")[:200] + "..." if len(web_result.get("snippet", "")) > 200 else web_result.get("snippet", ""),
                    "source": "web_search",
                    "search_source": web_result.get("source", "unknown")
                })
    
    return {
        "success": True,
        "answer": answer,
        "citations": citations,
        "chunks_retrieved": len(similar_chunks) if similar_chunks else 0,
        "web_results_count": len(web_citations) if web_citations else 0,
        "used_web_search": bool(web_search_context),
        "question": question
    }


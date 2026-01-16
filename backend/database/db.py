"""
Database connection and utilities for Supabase
Simple database operations without auth
"""
import os
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Supabase connection
SUPABASE_URL = os.getenv("SUPABASE_URL")
# Try service role key first (for admin operations), then anon key
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    # Fallback to None if not configured - will use file storage instead
    supabase: Optional[Client] = None
    print(f"[WARNING] Supabase not configured. SUPABASE_URL: {'SET' if SUPABASE_URL else 'NOT SET'}, SUPABASE_KEY: {'SET' if SUPABASE_KEY else 'NOT SET'}")
else:
    supabase: Optional[Client] = create_client(SUPABASE_URL, SUPABASE_KEY)
    print(f"[INFO] Supabase connected successfully. URL: {SUPABASE_URL[:30]}...")


def get_supabase() -> Optional[Client]:
    """Get Supabase client"""
    return supabase


def is_supabase_configured() -> bool:
    """Check if Supabase is configured"""
    return supabase is not None


# Knowledge Base Operations
def create_knowledge_base(name: str, description: str = "") -> Dict[str, Any]:
    """Create a new knowledge base"""
    if not supabase:
        raise ValueError("Supabase not configured")
    
    result = supabase.table("knowledge_bases").insert({
        "name": name,
        "description": description,
        "status": "created"
    }).execute()
    
    return result.data[0] if result.data else {}


def list_knowledge_bases() -> List[Dict[str, Any]]:
    """List all knowledge bases"""
    if not supabase:
        return []
    
    result = supabase.table("knowledge_bases").select("*").order("created_at", desc=True).execute()
    return result.data if result.data else []


def get_knowledge_base(kb_id: str) -> Optional[Dict[str, Any]]:
    """Get knowledge base by ID"""
    if not supabase:
        return None
    
    result = supabase.table("knowledge_bases").select("*").eq("id", kb_id).execute()
    return result.data[0] if result.data else None


def update_knowledge_base(kb_id: str, **kwargs) -> Dict[str, Any]:
    """Update knowledge base"""
    if not supabase:
        raise ValueError("Supabase not configured")
    
    result = supabase.table("knowledge_bases").update(kwargs).eq("id", kb_id).execute()
    return result.data[0] if result.data else {}


def delete_knowledge_base(kb_id: str) -> bool:
    """Delete knowledge base"""
    if not supabase:
        return False
    
    result = supabase.table("knowledge_bases").delete().eq("id", kb_id).execute()
    return True


# Document Operations
def create_document(
    kb_id: str,
    filename: str,
    file_type: str,
    file_size: int,
    file_path: str,
    metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """Create a document record"""
    if not supabase:
        raise ValueError("Supabase not configured")
    
    result = supabase.table("documents").insert({
        "knowledge_base_id": kb_id,
        "filename": filename,
        "file_type": file_type,
        "file_size": file_size,
        "file_path": file_path,
        "status": "processing",
        "metadata": metadata or {}
    }).execute()
    
    return result.data[0] if result.data else {}


def list_documents(kb_id: str) -> List[Dict[str, Any]]:
    """List documents in a knowledge base"""
    if not supabase:
        return []
    
    result = supabase.table("documents").select("*").eq("knowledge_base_id", kb_id).order("uploaded_at", desc=True).execute()
    return result.data if result.data else []


def get_document(doc_id: str) -> Optional[Dict[str, Any]]:
    """Get document by ID"""
    if not supabase:
        return None
    
    result = supabase.table("documents").select("*").eq("id", doc_id).execute()
    return result.data[0] if result.data else None


def update_document(doc_id: str, **kwargs) -> Dict[str, Any]:
    """Update document"""
    if not supabase:
        raise ValueError("Supabase not configured")
    
    result = supabase.table("documents").update(kwargs).eq("id", doc_id).execute()
    return result.data[0] if result.data else {}


def delete_document(doc_id: str) -> bool:
    """Delete document"""
    if not supabase:
        return False
    
    result = supabase.table("documents").delete().eq("id", doc_id).execute()
    return True


# Chunk Operations
def create_chunk(
    doc_id: str,
    kb_id: str,
    chunk_index: int,
    content: str,
    metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """Create a document chunk"""
    if not supabase:
        raise ValueError("Supabase not configured")
    
    try:
        result = supabase.table("document_chunks").insert({
            "document_id": doc_id,
            "knowledge_base_id": kb_id,
            "chunk_index": chunk_index,
            "content": content,
            "metadata": metadata or {}
        }).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        else:
            print(f"[WARNING] Chunk insert returned no data. Response: {result}")
            return {}
    except Exception as e:
        print(f"[ERROR] Failed to create chunk in database: {e}")
        raise


def get_chunks_by_document(doc_id: str) -> List[Dict[str, Any]]:
    """Get all chunks for a document"""
    if not supabase:
        return []
    
    result = supabase.table("document_chunks").select("*").eq("document_id", doc_id).order("chunk_index").execute()
    return result.data if result.data else []


def get_chunks_by_kb(kb_id: str) -> List[Dict[str, Any]]:
    """Get all chunks for a knowledge base"""
    if not supabase:
        return []
    
    result = supabase.table("document_chunks").select("*").eq("knowledge_base_id", kb_id).order("chunk_index").execute()
    return result.data if result.data else []


def update_chunk_embedding(chunk_id: str, embedding: List[float]) -> bool:
    """Update chunk with embedding vector"""
    if not supabase:
        raise ValueError("Supabase not configured")
    
    try:
        # Supabase pgvector expects the embedding as a list directly
        # The Python client handles the conversion automatically
        result = supabase.table("document_chunks").update({
            "embedding": embedding  # Pass as list, Supabase handles conversion
        }).eq("id", chunk_id).execute()
        
        return result.data is not None and len(result.data) > 0
    except Exception as e:
        print(f"[ERROR] Failed to update chunk embedding: {e}")
        import traceback
        traceback.print_exc()
        return False


def search_similar_chunks(
    kb_id: str,
    query_embedding: List[float],
    limit: int = 10,
    threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Search for similar chunks using vector similarity
    
    Args:
        kb_id: Knowledge base ID
        query_embedding: Query embedding vector
        limit: Maximum number of results
        threshold: Minimum similarity score (0-1)
    
    Returns:
        List of similar chunks with similarity scores
    """
    if not supabase:
        return []
    
    try:
        # Supabase pgvector expects embedding as a list/array
        # The RPC function expects vector type, so pass as list
        result = supabase.rpc(
            "find_similar_chunks",
            {
                "query_embedding": query_embedding,  # Pass as list, not string
                "kb_id_param": kb_id,
                "match_threshold": threshold,
                "match_count": limit
            }
        ).execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        # Fallback: if RPC doesn't work, try direct query
        print(f"[WARNING] RPC search failed: {e}, trying direct query...")
        try:
            # Direct query using cosine distance operator (<=>)
            # Note: This requires pgvector extension
            embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
            
            # Get all chunks with embeddings
            all_chunks = supabase.table("document_chunks").select(
                "id, document_id, chunk_index, content, metadata, embedding"
            ).eq("knowledge_base_id", kb_id).not_.is_("embedding", "null").execute()
            
            if not all_chunks.data:
                return []
            
            # Calculate similarity for each chunk (client-side fallback)
            # Note: For production, use the database function for better performance
            try:
                import numpy as np
                USE_NUMPY = True
            except ImportError:
                USE_NUMPY = False
                print("[WARNING] numpy not available, using simplified similarity calculation")
            
            results = []
            
            if USE_NUMPY:
                query_vec = np.array(query_embedding)
                
                for chunk in all_chunks.data:
                    chunk_embedding = chunk.get("embedding")
                    if chunk_embedding:
                        try:
                            # Convert to numpy array if it's a list
                            if isinstance(chunk_embedding, list):
                                chunk_vec = np.array(chunk_embedding)
                            else:
                                chunk_vec = np.array(chunk_embedding)
                            
                            # Calculate cosine similarity
                            dot_product = np.dot(query_vec, chunk_vec)
                            norm_query = np.linalg.norm(query_vec)
                            norm_chunk = np.linalg.norm(chunk_vec)
                            
                            if norm_query > 0 and norm_chunk > 0:
                                similarity = dot_product / (norm_query * norm_chunk)
                                # Cosine similarity is between -1 and 1, normalize to 0-1
                                similarity = (similarity + 1) / 2
                                
                                if similarity >= threshold:
                                    chunk["similarity"] = float(similarity)
                                    results.append(chunk)
                        except Exception as calc_error:
                            print(f"[WARNING] Failed to calculate similarity: {calc_error}")
                            # Include chunk with placeholder similarity
                            chunk["similarity"] = 0.5
                            if threshold <= 0.5:
                                results.append(chunk)
            else:
                # Simplified fallback without numpy - just return all chunks
                print("[WARNING] Using simplified fallback - returning chunks without similarity filtering")
                for chunk in all_chunks.data:
                    if chunk.get("embedding"):
                        chunk["similarity"] = 0.75  # Placeholder
                        results.append(chunk)
            
            # Sort by similarity and limit
            results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
            return results[:limit]
            
        except Exception as e2:
            print(f"[ERROR] Direct search also failed: {e2}")
            return []


# Notebook Operations
def create_notebook(name: str, description: str = "", color: str = "#3b82f6", icon: str = "📓") -> Dict[str, Any]:
    """Create a new notebook"""
    if not supabase:
        raise ValueError("Supabase not configured")
    
    result = supabase.table("notebooks").insert({
        "name": name,
        "description": description,
        "color": color,
        "icon": icon,
        "item_count": 0
    }).execute()
    
    return result.data[0] if result.data else {}


def list_notebooks() -> List[Dict[str, Any]]:
    """List all notebooks"""
    if not supabase:
        return []
    
    result = supabase.table("notebooks").select("*").order("created_at", desc=True).execute()
    return result.data if result.data else []


def get_notebook(notebook_id: str) -> Optional[Dict[str, Any]]:
    """Get notebook by ID"""
    if not supabase:
        return None
    
    result = supabase.table("notebooks").select("*").eq("id", notebook_id).execute()
    return result.data[0] if result.data else None


def update_notebook(notebook_id: str, **kwargs) -> Dict[str, Any]:
    """Update notebook"""
    if not supabase:
        raise ValueError("Supabase not configured")
    
    result = supabase.table("notebooks").update(kwargs).eq("id", notebook_id).execute()
    return result.data[0] if result.data else {}


def delete_notebook(notebook_id: str) -> bool:
    """Delete notebook"""
    if not supabase:
        return False
    
    result = supabase.table("notebooks").delete().eq("id", notebook_id).execute()
    return True


# Notebook Item Operations
def create_notebook_item(
    notebook_id: str,
    item_type: str,
    title: str,
    content: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a notebook item"""
    if not supabase:
        raise ValueError("Supabase not configured")
    
    result = supabase.table("notebook_items").insert({
        "notebook_id": notebook_id,
        "type": item_type,
        "title": title,
        "content": content
    }).execute()
    
    return result.data[0] if result.data else {}


def list_notebook_items(notebook_id: str) -> List[Dict[str, Any]]:
    """List all items in a notebook"""
    if not supabase:
        return []
    
    result = supabase.table("notebook_items").select("*").eq("notebook_id", notebook_id).order("created_at", desc=True).execute()
    return result.data if result.data else []


def get_notebook_item(item_id: str) -> Optional[Dict[str, Any]]:
    """Get notebook item by ID"""
    if not supabase:
        return None
    
    result = supabase.table("notebook_items").select("*").eq("id", item_id).execute()
    return result.data[0] if result.data else None


def delete_notebook_item(item_id: str) -> bool:
    """Delete notebook item"""
    if not supabase:
        return False
    
    result = supabase.table("notebook_items").delete().eq("id", item_id).execute()
    return True


# Guide Session Operations
def create_guide_session(notebook_ids: List[str], max_points: int = 5) -> Dict[str, Any]:
    """Create a new guide session"""
    if not supabase:
        raise ValueError("Supabase not configured")
    
    result = supabase.table("guide_sessions").insert({
        "notebook_ids": notebook_ids,
        "current_step": 1,
        "status": "active",
        "content": {}  # Will be populated by guide generator
    }).execute()
    
    return result.data[0] if result.data else {}


def get_guide_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get guide session by ID"""
    if not supabase:
        return None
    
    result = supabase.table("guide_sessions").select("*").eq("id", session_id).execute()
    return result.data[0] if result.data else None


def update_guide_session(session_id: str, **kwargs) -> Dict[str, Any]:
    """Update guide session"""
    if not supabase:
        raise ValueError("Supabase not configured")
    
    result = supabase.table("guide_sessions").update(kwargs).eq("id", session_id).execute()
    return result.data[0] if result.data else {}


def list_guide_sessions() -> List[Dict[str, Any]]:
    """List all guide sessions"""
    if not supabase:
        return []
    
    result = supabase.table("guide_sessions").select("*").order("created_at", desc=True).execute()
    return result.data if result.data else []


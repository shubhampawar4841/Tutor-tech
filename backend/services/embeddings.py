"""
Embeddings Service
Generates vector embeddings for text chunks using OpenAI or other providers
"""
import os
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

# Try to import OpenAI and httpx
try:
    from openai import OpenAI
    import httpx
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    httpx = None

# Workaround for httpx compatibility issue
# Create a custom httpx client that doesn't use proxies parameter
def create_http_client(timeout=60.0):
    """Create an httpx client compatible with OpenAI library"""
    if not httpx:
        return None
    try:
        # Try to create client without proxies parameter
        return httpx.Client(timeout=timeout)
    except Exception:
        # Fallback: try with minimal parameters
        try:
            return httpx.Client()
        except Exception:
            return None

# Workaround for httpx compatibility issue
# Create a custom httpx client that doesn't use proxies parameter
def create_http_client(timeout=60.0):
    """Create an httpx client compatible with OpenAI library"""
    if not httpx:
        return None
    try:
        # Try to create client without proxies parameter
        return httpx.Client(timeout=timeout)
    except Exception:
        # Fallback: try with minimal parameters
        try:
            return httpx.Client()
        except Exception:
            return None

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")  # Default: cheaper, 1536 dims
# Alternative: "text-embedding-ada-002" (1536 dims, older) or "text-embedding-3-large" (3072 dims)

# Embedding dimensions based on model
EMBEDDING_DIMS = {
    "text-embedding-ada-002": 1536,
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072
}

DEFAULT_DIMS = EMBEDDING_DIMS.get(EMBEDDING_MODEL, 1536)


def is_embeddings_configured() -> bool:
    """Check if embeddings are configured"""
    return OPENAI_AVAILABLE and OPENAI_API_KEY is not None


def get_embedding_dimensions() -> int:
    """Get the embedding dimensions for the current model"""
    return DEFAULT_DIMS


def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate embedding for a single text
    
    Args:
        text: Text to embed
    
    Returns:
        List of floats (embedding vector) or None if failed
    """
    if not is_embeddings_configured():
        print("[EMBEDDING] OpenAI not configured. Set OPENAI_API_KEY in .env")
        return None
    
    if not text or not text.strip():
        print("[EMBEDDING] Empty text provided")
        return None
    
    try:
        # Set API key via environment variable
        if OPENAI_API_KEY and "OPENAI_API_KEY" not in os.environ:
            os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        
        # Create custom http client to avoid proxies compatibility issue
        http_client = create_http_client(timeout=60.0)
        if http_client:
            client = OpenAI(http_client=http_client)
        else:
            # Fallback: use default initialization
            client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Clean text (remove extra whitespace, limit length)
        clean_text = text.strip().replace("\n", " ")[:8000]  # Limit to 8000 chars
        
        print(f"[EMBEDDING] Generating embedding for {len(clean_text)} chars using {EMBEDDING_MODEL}...")
        
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=clean_text
        )
        
        embedding = response.data[0].embedding
        
        print(f"[EMBEDDING] Generated embedding: {len(embedding)} dimensions")
        return embedding
        
    except Exception as e:
        print(f"[ERROR] Failed to generate embedding: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_embeddings_batch(texts: List[str], batch_size: int = 100) -> List[Optional[List[float]]]:
    """
    Generate embeddings for multiple texts in batches
    
    Args:
        texts: List of texts to embed
        batch_size: Number of texts to process per batch
    
    Returns:
        List of embeddings (same order as input texts, None for failed ones)
    """
    if not is_embeddings_configured():
        print("[EMBEDDING] OpenAI not configured")
        return [None] * len(texts)
    
    if not texts:
        return []
    
    try:
        # Set API key via environment variable
        if OPENAI_API_KEY and "OPENAI_API_KEY" not in os.environ:
            os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        
        # Create custom http client to avoid proxies compatibility issue
        http_client = create_http_client(timeout=120.0)
        if http_client:
            client = OpenAI(http_client=http_client)
        else:
            # Fallback: use default initialization
            client = OpenAI(api_key=OPENAI_API_KEY)
        
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Clean texts
            clean_batch = [t.strip().replace("\n", " ")[:8000] if t else "" for t in batch]
            
            print(f"[EMBEDDING] Processing batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1} ({len(batch)} texts)...")
            
            try:
                response = client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=clean_batch
                )
                
                # Extract embeddings in order
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                
                print(f"[EMBEDDING] Generated {len(batch_embeddings)} embeddings")
                
            except Exception as e:
                print(f"[ERROR] Batch embedding failed: {e}")
                import traceback
                traceback.print_exc()
                # Add None for each failed item
                all_embeddings.extend([None] * len(batch))
        
        return all_embeddings
        
    except Exception as e:
        print(f"[ERROR] Failed to generate batch embeddings: {e}")
        import traceback
        traceback.print_exc()
        return [None] * len(texts)



"""
Web Search Service
Provides web search capabilities using DuckDuckGo (free) or SerpAPI (optional)
"""
import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()

# Try to import DuckDuckGo
try:
    from duckduckgo_search import DDGS
    DDG_AVAILABLE = True
except ImportError:
    DDG_AVAILABLE = False
    DDGS = None

# Try to import SerpAPI (optional, premium)
try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False
    GoogleSearch = None

# Configuration
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
USE_SERPAPI = SERPAPI_AVAILABLE and SERPAPI_KEY is not None


def is_web_search_configured() -> bool:
    """Check if web search is available"""
    return DDG_AVAILABLE or USE_SERPAPI


def search_web(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search the web for information
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
    
    Returns:
        List of search results with title, snippet, and url
    """
    if not is_web_search_configured():
        return []
    
    results = []
    
    # Try SerpAPI first if available (better quality)
    if USE_SERPAPI:
        try:
            search = GoogleSearch({
                "q": query,
                "api_key": SERPAPI_KEY,
                "num": max_results
            })
            serp_results = search.get_dict()
            
            if "organic_results" in serp_results:
                for result in serp_results["organic_results"][:max_results]:
                    results.append({
                        "title": result.get("title", ""),
                        "snippet": result.get("snippet", ""),
                        "url": result.get("link", ""),
                        "source": "serpapi"
                    })
            
            if results:
                return results
        except Exception as e:
            print(f"[WEB_SEARCH] SerpAPI error: {e}, falling back to DuckDuckGo")
    
    # Fallback to DuckDuckGo (free)
    if DDG_AVAILABLE:
        try:
            with DDGS() as ddgs:
                ddg_results = list(ddgs.text(query, max_results=max_results))
                
                for result in ddg_results:
                    results.append({
                        "title": result.get("title", ""),
                        "snippet": result.get("body", ""),
                        "url": result.get("href", ""),
                        "source": "duckduckgo"
                    })
        except Exception as e:
            print(f"[WEB_SEARCH] DuckDuckGo error: {e}")
    
    return results


def format_web_search_context(search_results: List[Dict[str, Any]]) -> str:
    """
    Format web search results into context for LLM
    
    Args:
        search_results: List of search results
    
    Returns:
        Formatted context string
    """
    if not search_results:
        return ""
    
    context_parts = ["## Web Search Results:"]
    
    for i, result in enumerate(search_results, 1):
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        url = result.get("url", "")
        
        context_parts.append(f"\n[{i}] {title}")
        context_parts.append(f"   {snippet}")
        if url:
            context_parts.append(f"   Source: {url}")
    
    return "\n".join(context_parts)


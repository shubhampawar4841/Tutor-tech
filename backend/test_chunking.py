"""
Test script to manually process a document and verify chunking works
Run: python test_chunking.py <kb_id> <doc_id>
"""
import asyncio
import sys
from services.document_processor import process_document

async def test_processing(kb_id: str, doc_id: str):
    print(f"Testing document processing...")
    print(f"KB ID: {kb_id}")
    print(f"Doc ID: {doc_id}")
    print("-" * 60)
    
    result = await process_document(doc_id, kb_id)
    
    print("-" * 60)
    if result.get("success"):
        print(f"✅ SUCCESS!")
        print(f"   Chunks created: {result.get('chunk_count')}")
        print(f"   Message: {result.get('message')}")
    else:
        print(f"❌ FAILED!")
        print(f"   Error: {result.get('error')}")
    
    return result

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test_chunking.py <kb_id> <doc_id>")
        sys.exit(1)
    
    kb_id = sys.argv[1]
    doc_id = sys.argv[2]
    
    result = asyncio.run(test_processing(kb_id, doc_id))
    sys.exit(0 if result.get("success") else 1)








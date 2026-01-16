"""Quick script to check document status"""
from database.db import get_document, get_supabase, get_chunks_by_document
from pathlib import Path
import json

doc_id = "9dfa9172-af14-4b85-8426-48e8df8a1929"

print(f"Checking document: {doc_id}\n")

# Check database
supabase = get_supabase()
if supabase:
    doc = get_document(doc_id)
    if doc:
        print("[OK] Document found in DATABASE")
        print(f"  - Filename: {doc.get('filename')}")
        print(f"  - Status: {doc.get('status')}")
        print(f"  - Chunks count: {doc.get('chunks_count')}")
        
        # Check chunks
        chunks = get_chunks_by_document(doc_id)
        print(f"  - Chunks in DB: {len(chunks)}")
        if chunks:
            first_chunk = chunks[0]
            print(f"  - First chunk metadata keys: {list(first_chunk.get('metadata', {}).keys())}")
            print(f"  - First chunk metadata: {first_chunk.get('metadata', {})}")
    else:
        print("[X] Document NOT found in DATABASE")
        
        # Check if any documents exist
        result = supabase.table("documents").select("id, filename").limit(5).execute()
        if result.data:
            print(f"\nFound {len(result.data)} documents in database:")
            for d in result.data:
                print(f"  - {d['id']}: {d['filename']}")
        else:
            print("\n[WARNING] No documents found in database at all!")
else:
    print("[X] Supabase not configured")

# Check file storage
print("\n" + "="*50)
print("Checking FILE STORAGE...")
data_dir = Path("data/knowledge_bases")
if data_dir.exists():
    found = False
    for kb_dir in data_dir.iterdir():
        if kb_dir.is_dir():
            docs_dir = kb_dir / "documents"
            if docs_dir.exists():
                doc_file = docs_dir / f"{doc_id}.json"
                if doc_file.exists():
                    print(f"[OK] Document found in FILE STORAGE")
                    print(f"  - KB: {kb_dir.name}")
                    with open(doc_file) as f:
                        doc_data = json.load(f)
                    print(f"  - Filename: {doc_data.get('filename')}")
                    print(f"  - Status: {doc_data.get('status')}")
                    found = True
                    break
    
    if not found:
        print("[X] Document NOT found in file storage either")
else:
    print("[X] Data directory doesn't exist")


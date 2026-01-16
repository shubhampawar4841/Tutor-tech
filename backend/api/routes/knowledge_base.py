"""
Knowledge Base API Routes
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import os
import uuid
from pathlib import Path
from datetime import datetime
import asyncio

# Try to import database functions
try:
    from database.db import (
        create_knowledge_base as db_create_kb,
        list_knowledge_bases as db_list_kbs,
        get_knowledge_base as db_get_kb,
        update_knowledge_base as db_update_kb,
        delete_knowledge_base as db_delete_kb,
        create_document as db_create_doc,
        list_documents as db_list_docs,
        get_document as db_get_doc,
        update_document as db_update_doc,
        delete_document as db_delete_doc,
        is_supabase_configured
    )
    USE_DATABASE = is_supabase_configured()
except ImportError:
    USE_DATABASE = False

# Try to import storage functions
try:
    from database.storage import (
        upload_file_to_storage,
        delete_file_from_storage,
        get_storage_path_from_url,
        is_storage_configured
    )
    USE_STORAGE = is_storage_configured()
except ImportError:
    USE_STORAGE = False

router = APIRouter()

# File storage directory
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
KB_DIR = DATA_DIR / "knowledge_bases"
KB_DIR.mkdir(parents=True, exist_ok=True)


class KnowledgeBaseCreate(BaseModel):
    name: str
    description: str = ""


class KnowledgeBaseResponse(BaseModel):
    id: str
    name: str
    description: str
    status: str
    document_count: int = 0


@router.get("/")
async def list_knowledge_bases():
    """List all knowledge bases"""
    if USE_DATABASE:
        kbs = db_list_kbs()
        return {
            "knowledge_bases": kbs,
            "total": len(kbs)
        }
    else:
        # File-based storage fallback
        kbs = []
        if KB_DIR.exists():
            for kb_folder in KB_DIR.iterdir():
                if kb_folder.is_dir():
                    metadata_file = kb_folder / "metadata.json"
                    if metadata_file.exists():
                        import json
                        with open(metadata_file) as f:
                            kb_data = json.load(f)
                            # Count documents
                            docs_dir = kb_folder / "documents"
                            doc_count = len(list(docs_dir.glob("*.json"))) if docs_dir.exists() else 0
                            kb_data["document_count"] = doc_count
                            kbs.append(kb_data)
        return {
            "knowledge_bases": kbs,
            "total": len(kbs)
        }


@router.post("/")
async def create_knowledge_base(data: KnowledgeBaseCreate):
    """Create a new knowledge base"""
    if USE_DATABASE:
        kb = db_create_kb(data.name, data.description)
        return {
            "id": kb["id"],
            "name": kb["name"],
            "description": kb["description"],
            "status": kb["status"],
            "message": "Knowledge base created successfully"
        }
    else:
        # File-based storage
        kb_id = str(uuid.uuid4())
        kb_dir = KB_DIR / kb_id
        kb_dir.mkdir(parents=True, exist_ok=True)
        (kb_dir / "documents").mkdir(exist_ok=True)
        (kb_dir / "chunks").mkdir(exist_ok=True)
        
        metadata = {
            "id": kb_id,
            "name": data.name,
            "description": data.description,
            "status": "created",
            "document_count": 0,
            "chunk_count": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        import json
        with open(kb_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        return {
            "id": kb_id,
            "name": data.name,
            "description": data.description,
            "status": "created",
            "message": "Knowledge base created successfully"
        }


@router.get("/{kb_id}")
async def get_knowledge_base(kb_id: str):
    """Get knowledge base details"""
    if USE_DATABASE:
        kb = db_get_kb(kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        # Get document count
        docs = db_list_docs(kb_id)
        kb["document_count"] = len(docs)
        return kb
    else:
        kb_dir = KB_DIR / kb_id
        if not kb_dir.exists():
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        import json
        metadata_file = kb_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file) as f:
                kb_data = json.load(f)
                # Count documents
                docs_dir = kb_dir / "documents"
                kb_data["document_count"] = len(list(docs_dir.glob("*.json"))) if docs_dir.exists() else 0
                return kb_data
        
        raise HTTPException(status_code=404, detail="Knowledge base not found")


@router.post("/{kb_id}/upload")
async def upload_documents(kb_id: str, files: List[UploadFile] = File(...)):
    """Upload documents to knowledge base - Uses Supabase Storage in production"""
    # Verify KB exists
    if USE_DATABASE:
        kb = db_get_kb(kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
    else:
        kb_dir = KB_DIR / kb_id
        if not kb_dir.exists():
            raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    uploaded_files = []
    
    for file in files:
        # Read file content
        content = await file.read()
        file_size = len(content)
        file_ext = Path(file.filename).suffix
        file_type = file_ext[1:].lower() if file_ext else "unknown"
        
        # Determine content type
        content_type_map = {
            "pdf": "application/pdf",
            "txt": "text/plain",
            "md": "text/markdown",
            "doc": "application/msword",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        content_type = content_type_map.get(file_type, "application/octet-stream")
        
        # Upload to Supabase Storage (production) or local disk (development)
        if USE_STORAGE:
            # Production: Upload to Supabase Storage
            storage_url = upload_file_to_storage(
                kb_id=kb_id,
                file_content=content,
                filename=file.filename,
                content_type=content_type
            )
            
            if not storage_url:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload {file.filename} to storage"
                )
            
            file_path = storage_url  # Store URL instead of local path
            storage_type = "supabase_storage"
        else:
            # Development: Save to local disk
            kb_dir = KB_DIR / kb_id
            docs_dir = kb_dir / "documents"
            docs_dir.mkdir(parents=True, exist_ok=True)
            
            file_id = str(uuid.uuid4())
            file_path_local = docs_dir / f"{file_id}{file_ext}"
            
            with open(file_path_local, "wb") as f:
                f.write(content)
            
            file_path = str(file_path_local.relative_to(DATA_DIR))
            storage_type = "local_disk"
        
        # Create document record in database
        if USE_DATABASE:
            try:
                print(f"[UPLOAD] Creating document record in database for {file.filename}...")
                doc = db_create_doc(
                    kb_id=kb_id,
                    filename=file.filename,
                    file_type=file_type,
                    file_size=file_size,
                    file_path=file_path,
                    metadata={
                        "original_filename": file.filename,
                        "storage_type": storage_type,
                        "content_type": content_type
                    }
                )
                if not doc or "id" not in doc:
                    print(f"[ERROR] Document record creation failed - no ID returned")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to create document record for {file.filename}"
                    )
                doc_id = doc["id"]
                print(f"[UPLOAD] Document record created: {doc_id}")
            except Exception as e:
                print(f"[ERROR] Failed to create document record: {e}")
                import traceback
                traceback.print_exc()
                raise HTTPException(
                    status_code=500,
                    detail=f"Database error: {str(e)}"
                )
        else:
            # File-based storage fallback
            doc_id = str(uuid.uuid4())
            kb_dir = KB_DIR / kb_id
            docs_dir = kb_dir / "documents"
            docs_dir.mkdir(parents=True, exist_ok=True)
            
            doc_metadata = {
                "id": doc_id,
                "filename": file.filename,
                "file_type": file_type,
                "file_size": file_size,
                "file_path": file_path,
                "status": "processing",
                "chunks_count": 0,
                "uploaded_at": datetime.now().isoformat(),
                "storage_type": storage_type
            }
            import json
            with open(docs_dir / f"{doc_id}.json", "w") as f:
                json.dump(doc_metadata, f, indent=2)
        
        uploaded_files.append({
            "id": doc_id,
            "filename": file.filename,
            "status": "processing",
            "storage_type": storage_type
        })
    
    # Trigger background processing (chunking, embedding, vector storage)
    async def process_uploaded_documents():
        """Process documents in background after a short delay to ensure DB is ready"""
        await asyncio.sleep(2)  # Wait 2 seconds for DB to be ready
        
        try:
            from services.document_processor import process_document
            
            # Process each uploaded document
            for file_info in uploaded_files:
                doc_id = file_info["id"]
                print(f"\n{'='*60}")
                print(f"[PROCESSING] Starting chunking for document {doc_id} in KB {kb_id}")
                print(f"{'='*60}\n")
                
                try:
                    result = await process_document(doc_id, kb_id)
                    if result.get("success"):
                        chunk_count = result.get("chunk_count", 0)
                        print(f"\n{'='*60}")
                        print(f"[SUCCESS] Document {doc_id} processed: {chunk_count} chunks created")
                        print(f"{'='*60}\n")
                    else:
                        error_msg = result.get("error", "Unknown error")
                        print(f"\n{'='*60}")
                        print(f"[ERROR] Document {doc_id} processing failed: {error_msg}")
                        print(f"{'='*60}\n")
                except Exception as e:
                    print(f"\n{'='*60}")
                    print(f"[ERROR] Exception processing document {doc_id}: {e}")
                    print(f"{'='*60}\n")
                    import traceback
                    traceback.print_exc()
        except ImportError as e:
            print(f"[ERROR] Document processor not available: {e}")
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"[ERROR] Error in background processing: {e}")
            import traceback
            traceback.print_exc()
    
    # Start background processing task
    asyncio.create_task(process_uploaded_documents())
    print(f"[UPLOAD] Background processing scheduled for {len(uploaded_files)} document(s)")
    
    return {
        "message": f"Uploaded {len(files)} file(s) to knowledge base {kb_id}. Processing started.",
        "files": uploaded_files,
        "status": "processing",
        "storage_type": "supabase_storage" if USE_STORAGE else "local_disk"
    }


@router.post("/{kb_id}/documents/{doc_id}/process")
async def process_document_manual(kb_id: str, doc_id: str):
    """Manually trigger document processing (for testing/debugging)"""
    try:
        from services.document_processor import process_document
        
        print(f"[MANUAL PROCESS] Starting processing for document {doc_id}")
        result = await process_document(doc_id, kb_id)
        
        if result.get("success"):
            return {
                "success": True,
                "message": f"Document processed successfully",
                "chunk_count": result.get("chunk_count", 0)
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Processing failed: {result.get('error', 'Unknown error')}"
            )
    except ImportError:
        raise HTTPException(status_code=500, detail="Document processor not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/{kb_id}/documents")
async def list_documents(kb_id: str):
    """List all documents in a knowledge base"""
    if USE_DATABASE:
        docs = db_list_docs(kb_id)
        return {
            "documents": docs,
            "total": len(docs)
        }
    else:
        docs_dir = KB_DIR / kb_id / "documents"
        documents = []
        
        if docs_dir.exists():
            import json
            for doc_file in docs_dir.glob("*.json"):
                with open(doc_file) as f:
                    doc_data = json.load(f)
                    documents.append(doc_data)
        
        return {
            "documents": documents,
            "total": len(documents)
        }


@router.get("/{kb_id}/documents/{doc_id}/chunks")
async def get_document_chunks(kb_id: str, doc_id: str):
    """Get chunks for a specific document"""
    try:
        from database.db import get_chunks_by_document, is_supabase_configured
        
        if is_supabase_configured():
            chunks = get_chunks_by_document(doc_id)
            return {
                "chunks": chunks,
                "total": len(chunks),
                "document_id": doc_id
            }
        else:
            # File-based storage
            kb_dir = KB_DIR / kb_id
            chunks_dir = kb_dir / "chunks"
            chunks = []
            
            if chunks_dir.exists():
                import json
                for chunk_file in sorted(chunks_dir.glob(f"{doc_id}_chunk_*.json")):
                    with open(chunk_file) as f:
                        chunk_data = json.load(f)
                        chunks.append(chunk_data)
            
            return {
                "chunks": chunks,
                "total": len(chunks),
                "document_id": doc_id
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading chunks: {str(e)}")


class AskRequest(BaseModel):
    question: str
    top_k: int = 5
    threshold: float = 0.7
    model: Optional[str] = None


@router.post("/{kb_id}/ask")
async def ask_question(kb_id: str, request: AskRequest):
    """
    Ask a question about the knowledge base (RAG endpoint)
    
    Returns answer with citations from relevant document chunks
    """
    try:
        # Verify knowledge base exists
        if USE_DATABASE:
            kb = db_get_kb(kb_id)
            if not kb:
                raise HTTPException(status_code=404, detail="Knowledge base not found")
        else:
            kb_dir = KB_DIR / kb_id
            if not kb_dir.exists():
                raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        # Import RAG service
        from services.rag import ask_question as rag_ask_question
        
        # Call RAG service
        result = rag_ask_question(
            kb_id=kb_id,
            question=request.question,
            top_k=request.top_k,
            threshold=request.threshold,
            model=request.model
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to generate answer")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/{kb_id}/documents/{doc_id}")
async def delete_document(kb_id: str, doc_id: str):
    """Delete document from knowledge base - Removes from Supabase Storage or local disk"""
    # Get document to find storage path
    if USE_DATABASE:
        doc = db_get_doc(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = doc.get("file_path")
        storage_type = doc.get("metadata", {}).get("storage_type", "local_disk")
        
        # Delete from storage
        if storage_type == "supabase_storage" and USE_STORAGE:
            storage_path = get_storage_path_from_url(file_path)
            if storage_path:
                delete_file_from_storage(storage_path)
        elif storage_type == "local_disk":
            # Delete local file
            kb_dir = KB_DIR / kb_id
            docs_dir = kb_dir / "documents"
            for file in docs_dir.glob(f"{doc_id}*"):
                if file.suffix != ".json":  # Don't delete metadata yet
                    file.unlink()
        
        # Delete from database
        db_delete_doc(doc_id)
    else:
        # File-based storage
        kb_dir = KB_DIR / kb_id
        docs_dir = kb_dir / "documents"
        
        # Load metadata to get file path
        metadata_file = docs_dir / f"{doc_id}.json"
        if metadata_file.exists():
            import json
            with open(metadata_file) as f:
                doc_data = json.load(f)
                file_path = doc_data.get("file_path")
                storage_type = doc_data.get("storage_type", "local_disk")
                
                # Delete from storage if Supabase
                if storage_type == "supabase_storage" and USE_STORAGE:
                    storage_path = get_storage_path_from_url(file_path)
                    if storage_path:
                        delete_file_from_storage(storage_path)
                elif storage_type == "local_disk" and file_path:
                    # Delete local file
                    local_file = DATA_DIR / file_path
                    if local_file.exists():
                        local_file.unlink()
        
        # Delete metadata file
        if metadata_file.exists():
            metadata_file.unlink()
    
    return {"message": f"Document {doc_id} deleted from knowledge base {kb_id}"}


@router.delete("/{kb_id}")
async def delete_knowledge_base(kb_id: str):
    """Delete a knowledge base"""
    if USE_DATABASE:
        db_delete_kb(kb_id)
        # Also delete files
        kb_dir = KB_DIR / kb_id
        if kb_dir.exists():
            import shutil
            shutil.rmtree(kb_dir)
    else:
        kb_dir = KB_DIR / kb_id
        if kb_dir.exists():
            import shutil
            shutil.rmtree(kb_dir)
    
    return {"message": f"Knowledge base {kb_id} deleted"}

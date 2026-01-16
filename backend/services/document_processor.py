"""
Document Processing Service
Handles chunking, text extraction, and processing of uploaded documents
"""
import os
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid
from datetime import datetime

# Try to import PDF processing libraries
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

# Try to import token counting
try:
    import tiktoken
    TOKEN_COUNTING_AVAILABLE = True
except ImportError:
    TOKEN_COUNTING_AVAILABLE = False

try:
    from database.db import (
        get_document,
        update_document,
        create_chunk,
        update_chunk_embedding,
        is_supabase_configured
    )
    from database.storage import download_file_from_storage, get_storage_path_from_url, is_storage_configured
    USE_DATABASE = is_supabase_configured()
    USE_STORAGE = is_storage_configured()
except ImportError:
    USE_DATABASE = False
    USE_STORAGE = False

# Try to import embeddings service
try:
    from services.embeddings import (
        generate_embedding,
        is_embeddings_configured,
        generate_embeddings_batch
    )
    EMBEDDINGS_AVAILABLE = is_embeddings_configured()
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    generate_embedding = None
    generate_embeddings_batch = None

# Configuration
# Token-based chunking (better for LLMs)
CHUNK_SIZE_TOKENS = 1000  # Tokens per chunk (~700-1200 is ideal)
CHUNK_OVERLAP_TOKENS = 200  # Overlap in tokens
# Fallback character-based chunking
CHUNK_SIZE_CHARS = 3000  # Characters per chunk (roughly 1000 tokens)
CHUNK_OVERLAP_CHARS = 600  # Overlap in characters
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens in text using tiktoken"""
    if not TOKEN_COUNTING_AVAILABLE:
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4
    
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback estimate
        return len(text) // 4


def extract_text_from_pdf(file_path: str, return_pages: bool = False) -> Any:
    """
    Extract text from PDF file - tries PyMuPDF first, falls back to PyPDF2
    
    Args:
        file_path: Path to PDF file
        return_pages: If True, returns List[Dict] with page info. If False, returns string (backward compatible)
    
    Returns:
        If return_pages=True: List[{"page": int, "text": str}]
        If return_pages=False: str (concatenated text)
    """
    print(f"[EXTRACT_PDF] Opening PDF: {file_path}")
    if not Path(file_path).exists():
        print(f"[ERROR] PDF file does not exist: {file_path}")
        return [] if return_pages else ""
    
    file_size = Path(file_path).stat().st_size
    print(f"[EXTRACT_PDF] File size: {file_size} bytes")
    
    pages_data = []
    
    # Try PyMuPDF first (better extraction)
    if PYMUPDF_AVAILABLE:
        try:
            print(f"[EXTRACT_PDF] Using PyMuPDF (fitz) for extraction...")
            doc = fitz.open(file_path)
            num_pages = len(doc)
            print(f"[EXTRACT_PDF] PDF has {num_pages} pages")
            
            for page_num in range(num_pages):
                try:
                    page = doc[page_num]
                    page_text = page.get_text()
                    if page_text and page_text.strip():
                        pages_data.append({
                            "page": page_num + 1,  # 1-indexed
                            "text": page_text
                        })
                        print(f"[EXTRACT_PDF] Page {page_num + 1}: Extracted {len(page_text)} characters")
                    else:
                        print(f"[WARNING] Page {page_num + 1}: No text extracted (might be image-based)")
                        # Still add empty page to maintain page numbering
                        pages_data.append({
                            "page": page_num + 1,
                            "text": ""
                        })
                except Exception as e:
                    print(f"[ERROR] Error extracting page {page_num + 1}: {e}")
                    pages_data.append({
                        "page": page_num + 1,
                        "text": ""
                    })
            
            doc.close()
            
            if return_pages:
                print(f"[EXTRACT_PDF] Extracted {len(pages_data)} pages")
                return pages_data
            else:
                # Backward compatibility: return concatenated string
                text = "\n\n".join([f"--- Page {p['page']} ---\n\n{p['text']}" for p in pages_data if p['text']])
                print(f"[EXTRACT_PDF] Total extracted: {len(text)} characters")
                return text if text.strip() else ""
        except Exception as e:
            print(f"[ERROR] PyMuPDF extraction failed: {e}, trying PyPDF2...")
    
    # Fallback to PyPDF2
    if PDF_AVAILABLE:
        try:
            print(f"[EXTRACT_PDF] Using PyPDF2 for extraction...")
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                print(f"[EXTRACT_PDF] PDF has {num_pages} pages")
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            pages_data.append({
                                "page": page_num + 1,  # 1-indexed
                                "text": page_text
                            })
                            print(f"[EXTRACT_PDF] Page {page_num + 1}: Extracted {len(page_text)} characters")
                        else:
                            print(f"[WARNING] Page {page_num + 1}: No text extracted (might be image-based)")
                            pages_data.append({
                                "page": page_num + 1,
                                "text": ""
                            })
                    except Exception as e:
                        print(f"[ERROR] Error extracting page {page_num + 1}: {e}")
                        pages_data.append({
                            "page": page_num + 1,
                            "text": ""
                        })
            
            if return_pages:
                print(f"[EXTRACT_PDF] Extracted {len(pages_data)} pages")
                return pages_data
            else:
                # Backward compatibility: return concatenated string
                text = "\n\n".join([f"--- Page {p['page']} ---\n\n{p['text']}" for p in pages_data if p['text']])
                print(f"[EXTRACT_PDF] Total extracted: {len(text)} characters")
                return text
        except Exception as e:
            print(f"[ERROR] PyPDF2 extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return [] if return_pages else ""
    else:
        print(f"[ERROR] No PDF library available. Install: pip install pymupdf or pip install PyPDF2")
        return [] if return_pages else ""


def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file"""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        print(f"Error reading text file: {e}")
        return ""


def chunk_pages(pages: List[Dict[str, Any]], use_tokens: bool = True) -> List[Dict[str, Any]]:
    """
    Chunk text from pages while preserving page numbers
    
    Args:
        pages: List of {"page": int, "text": str}
        use_tokens: Whether to use token-based chunking
    
    Returns:
        List of chunks with page_start, page_end metadata
    """
    if not pages:
        return []
    
    # Combine all pages into one text with page markers
    all_text = ""
    page_boundaries = []  # Track where each page starts in the combined text
    char_offset = 0
    
    for page_data in pages:
        page_num = page_data["page"]
        page_text = page_data.get("text", "")
        if page_text.strip():
            page_boundaries.append({
                "page": page_num,
                "start_char": char_offset,
                "end_char": char_offset + len(page_text)
            })
            all_text += page_text + "\n\n"
            char_offset += len(page_text) + 2  # +2 for "\n\n"
    
    if not all_text.strip():
        return []
    
    # Chunk the combined text
    if use_tokens and TOKEN_COUNTING_AVAILABLE:
        chunks = chunk_text_by_tokens(all_text)
    else:
        chunks = chunk_text_by_chars(all_text)
    
    # Map chunks back to page numbers
    for chunk in chunks:
        start_char = chunk.get("start_char", 0)
        end_char = chunk.get("end_char", start_char + len(chunk.get("content", "")))
        
        # Find all pages this chunk spans
        pages_spanned = []
        for boundary in page_boundaries:
            # Check if chunk overlaps with this page
            chunk_overlaps_page = not (end_char <= boundary["start_char"] or start_char >= boundary["end_char"])
            if chunk_overlaps_page:
                pages_spanned.append(boundary["page"])
        
        if pages_spanned:
            page_start = min(pages_spanned)
            page_end = max(pages_spanned)
        else:
            # Fallback: find closest pages
            if not page_boundaries:
                page_start = page_end = 1
            else:
                # Find page where chunk starts
                page_start = page_boundaries[0]["page"]
                for boundary in page_boundaries:
                    if start_char < boundary["end_char"]:
                        page_start = boundary["page"]
                        break
                
                # Find page where chunk ends
                page_end = page_boundaries[-1]["page"]
                for boundary in reversed(page_boundaries):
                    if end_char > boundary["start_char"]:
                        page_end = boundary["page"]
                        break
        
        chunk["page_start"] = page_start
        chunk["page_end"] = page_end
        chunk["page"] = page_start  # Primary page for citation
    
    return chunks


def chunk_text(text: str, use_tokens: bool = True) -> List[Dict[str, Any]]:
    """
    Split text into chunks with overlap
    Uses token-based chunking if available, falls back to character-based
    
    Returns:
        List of chunks with metadata
    """
    if not text or len(text.strip()) == 0:
        return []
    
    # Try token-based chunking first
    if use_tokens and TOKEN_COUNTING_AVAILABLE:
        return chunk_text_by_tokens(text)
    else:
        return chunk_text_by_chars(text)


def chunk_text_by_tokens(text: str) -> List[Dict[str, Any]]:
    """Chunk text by tokens (better for LLMs)"""
    try:
        encoding = tiktoken.encoding_for_model("gpt-4")
        tokens = encoding.encode(text)
        total_tokens = len(tokens)
        
        print(f"[CHUNK] Text has {total_tokens} tokens, chunking by {CHUNK_SIZE_TOKENS} tokens with {CHUNK_OVERLAP_TOKENS} overlap...")
        
        chunks = []
        start_token = 0
        chunk_index = 0
        max_iterations = (total_tokens // (CHUNK_SIZE_TOKENS - CHUNK_OVERLAP_TOKENS)) + 10  # Safety limit
        
        iteration = 0
        while start_token < total_tokens and iteration < max_iterations:
            iteration += 1
            end_token = min(start_token + CHUNK_SIZE_TOKENS, total_tokens)
            
            # Decode tokens to get text chunk
            chunk_tokens = tokens[start_token:end_token]
            chunk_text = encoding.decode(chunk_tokens)
            
            # Try to break at sentence boundary (find last sentence end in chunk)
            if end_token < total_tokens:
                # Look backwards for sentence endings
                chunk_text_lower = chunk_text.lower()
                for break_pattern in ['. ', '.\n', '! ', '!\n', '? ', '?\n', '\n\n']:
                    last_break = chunk_text.rfind(break_pattern)
                    if last_break > len(chunk_text) * 0.5:  # Only break if not too early
                        chunk_text = chunk_text[:last_break + 2]
                        # Re-encode to get actual token count
                        chunk_tokens = encoding.encode(chunk_text)
                        end_token = start_token + len(chunk_tokens)
                        break
            
            if chunk_text.strip():
                chunk_content = chunk_text.strip()
                char_count = len(chunk_content)
                
                # Calculate actual character positions in the original text
                # Find where this chunk appears in the original text
                text_before_chunk = encoding.decode(tokens[:start_token])
                start_char_actual = len(text_before_chunk)
                end_char_actual = start_char_actual + char_count
                
                chunks.append({
                    "chunk_index": chunk_index,
                    "content": chunk_content,
                    "start_token": start_token,
                    "end_token": end_token,
                    "token_count": len(chunk_tokens),  # Use already encoded tokens
                    "char_count": char_count,
                    # Add actual character positions for page mapping
                    "start_char": start_char_actual,
                    "end_char": end_char_actual,
                    "length": char_count
                })
                chunk_index += 1
            
            # Move start position with overlap
            new_start = end_token - CHUNK_OVERLAP_TOKENS if CHUNK_OVERLAP_TOKENS > 0 and end_token < total_tokens else end_token
            
            # Prevent infinite loop - ensure we always advance
            if new_start <= start_token:
                new_start = end_token
                if new_start <= start_token:
                    # Force advance by at least 1 token
                    new_start = start_token + 1
            
            start_token = new_start
            
            # Safety check: if we've processed all tokens, break
            if start_token >= total_tokens:
                break
            
            # Additional safety: prevent infinite loops
            if chunk_index > 10000:  # Sanity check
                print(f"[WARNING] Too many chunks ({chunk_index}), breaking to prevent infinite loop")
                break
        
        if iteration >= max_iterations:
            print(f"[WARNING] Reached max iterations ({max_iterations}), breaking loop")
        
        print(f"[CHUNK] Created {len(chunks)} chunks (token-based) after {iteration} iterations")
        return chunks
    except Exception as e:
        print(f"[WARNING] Token-based chunking failed: {e}, falling back to character-based")
        return chunk_text_by_chars(text)


def chunk_text_by_chars(text: str) -> List[Dict[str, Any]]:
    """Chunk text by characters (fallback)"""
    print(f"[CHUNK] Chunking by characters: {CHUNK_SIZE_CHARS} chars per chunk...")
    
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(text):
        end = start + CHUNK_SIZE_CHARS
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            for break_char in ['. ', '.\n', '! ', '!\n', '? ', '?\n', '\n\n']:
                last_break = text.rfind(break_char, start, end)
                if last_break != -1 and last_break > start + CHUNK_SIZE_CHARS * 0.5:
                    end = last_break + 2
                    break
        
        chunk_text = text[start:end].strip()
        
        if chunk_text:
            # Estimate token count
            token_count = count_tokens(chunk_text)
            chunks.append({
                "chunk_index": chunk_index,
                "content": chunk_text,
                "start_char": start,
                "end_char": end,
                "char_count": len(chunk_text),
                "token_count": token_count
            })
            chunk_index += 1
        
        # Move start position with overlap
        start = end - CHUNK_OVERLAP_CHARS if CHUNK_OVERLAP_CHARS > 0 else end
        
        # Prevent infinite loop
        if start >= end:
            start = end
    
    print(f"[CHUNK] Created {len(chunks)} chunks (character-based)")
    return chunks


async def process_document(doc_id: str, kb_id: str) -> Dict[str, Any]:
    """
    Process a document: extract text, chunk it, and store chunks
    
    Args:
        doc_id: Document ID
        kb_id: Knowledge base ID
    
    Returns:
        Processing result with chunk count
    """
    print(f"[PROCESS_DOCUMENT] Starting processing for doc_id={doc_id}, kb_id={kb_id}")
    
    try:
        # Get document info
        if USE_DATABASE:
            print(f"[PROCESS_DOCUMENT] Using database, fetching document {doc_id}")
            doc = get_document(doc_id)
            if not doc:
                print(f"[ERROR] Document {doc_id} not found in database")
                return {"success": False, "error": "Document not found"}
            
            print(f"[PROCESS_DOCUMENT] Document found: {doc.get('filename')}")
            file_path = doc.get("file_path")
            file_type = doc.get("file_type", "").lower()
            storage_type = doc.get("metadata", {}).get("storage_type", "local_disk")
            print(f"[PROCESS_DOCUMENT] File path: {file_path}, type: {file_type}, storage: {storage_type}")
        else:
            # File-based storage
            kb_dir = DATA_DIR / "knowledge_bases" / kb_id
            docs_dir = kb_dir / "documents"
            metadata_file = docs_dir / f"{doc_id}.json"
            
            if not metadata_file.exists():
                return {"success": False, "error": "Document not found"}
            
            import json
            with open(metadata_file) as f:
                doc = json.load(f)
            
            file_path = doc.get("file_path")
            file_type = doc.get("file_type", "").lower()
            storage_type = doc.get("storage_type", "local_disk")
        
        # Download or read file
        if storage_type == "supabase_storage" and USE_STORAGE:
            # Download from Supabase Storage
            print(f"[PROCESS_DOCUMENT] Downloading from Supabase Storage...")
            storage_path = get_storage_path_from_url(file_path)
            if not storage_path:
                print(f"[ERROR] Invalid storage path from URL: {file_path}")
                return {"success": False, "error": "Invalid storage path"}
            
            print(f"[PROCESS_DOCUMENT] Storage path: {storage_path}")
            file_content = download_file_from_storage(storage_path)
            if not file_content:
                print(f"[ERROR] Failed to download file from storage")
                return {"success": False, "error": "Failed to download from storage"}
            
            print(f"[PROCESS_DOCUMENT] Downloaded {len(file_content)} bytes from storage")
            
            # Save temporarily for processing (with correct extension)
            temp_dir = DATA_DIR / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            file_ext = Path(doc.get("filename", "")).suffix or f".{file_type}"
            temp_file = temp_dir / f"{doc_id}{file_ext}"
            
            print(f"[PROCESS_DOCUMENT] Saving to temp file: {temp_file}")
            with open(temp_file, "wb") as f:
                f.write(file_content)
            
            # Verify file exists and has content
            if not temp_file.exists():
                return {"success": False, "error": "Temp file was not created"}
            
            file_size = temp_file.stat().st_size
            print(f"[PROCESS_DOCUMENT] Temp file created: {file_size} bytes")
            
            local_file_path = str(temp_file)
        else:
            # Local file
            local_file_path = str(DATA_DIR / file_path) if not Path(file_path).is_absolute() else file_path
            print(f"[PROCESS_DOCUMENT] Using local file: {local_file_path}")
            
            if not Path(local_file_path).exists():
                return {"success": False, "error": f"Local file not found: {local_file_path}"}
        
        # Extract text based on file type (page-aware for PDFs)
        print(f"[PROCESS_DOCUMENT] Extracting text from {file_type} file...")
        pages_data = None
        text = ""
        
        if file_type == "pdf":
            # Try PyMuPDF first, then PyPDF2
            if not PYMUPDF_AVAILABLE and not PDF_AVAILABLE:
                return {"success": False, "error": "No PDF library installed. Run: pip install pymupdf or pip install PyPDF2"}
            
            # Extract with page tracking (Phase 1: Page Tracking)
            pages_data = extract_text_from_pdf(local_file_path, return_pages=True)
            if not pages_data:
                return {"success": False, "error": "No pages extracted from PDF"}
            
            # Calculate total text length
            total_chars = sum(len(p.get("text", "")) for p in pages_data)
            print(f"[PROCESS_DOCUMENT] Extracted {len(pages_data)} pages, {total_chars} characters from PDF")
            
        elif file_type in ["txt", "md"]:
            text = extract_text_from_txt(local_file_path)
            print(f"[PROCESS_DOCUMENT] Extracted {len(text)} characters from text file")
        else:
            return {"success": False, "error": f"Unsupported file type: {file_type}"}
        
        # Validate extraction
        if file_type == "pdf":
            if not pages_data or not any(p.get("text", "").strip() for p in pages_data):
                print(f"[ERROR] No text extracted from PDF. File exists: {Path(local_file_path).exists()}")
                return {"success": False, "error": "No text extracted from document. The PDF might be image-based or corrupted."}
        else:
            if not text or len(text.strip()) == 0:
                print(f"[ERROR] No text extracted. File exists: {Path(local_file_path).exists()}")
                return {"success": False, "error": "No text extracted from document."}
        
        # Clean up temp file if used
        if storage_type == "supabase_storage" and USE_STORAGE:
            try:
                os.remove(local_file_path)
            except:
                pass
        
        # Chunk the text (page-aware for PDFs, regular for others)
        print(f"[PROCESS_DOCUMENT] Chunking text into pieces...")
        use_token_chunking = TOKEN_COUNTING_AVAILABLE
        
        if file_type == "pdf" and pages_data:
            # Use page-aware chunking (Phase 1: preserves page numbers)
            chunks = chunk_pages(pages_data, use_tokens=use_token_chunking)
            print(f"[PROCESS_DOCUMENT] Created {len(chunks)} chunks with page tracking ({'token-based' if use_token_chunking else 'character-based'})")
        else:
            # Regular chunking for non-PDF files
            chunks = chunk_text(text, use_tokens=use_token_chunking)
            print(f"[PROCESS_DOCUMENT] Created {len(chunks)} chunks ({'token-based' if use_token_chunking else 'character-based'})")
        
        if not chunks:
            return {"success": False, "error": "No chunks created from document"}
        
        # Store chunks in database
        print(f"[PROCESS_DOCUMENT] Storing {len(chunks)} chunks in database...")
        stored_chunks = []
        for i, chunk_data in enumerate(chunks):
            if i % 10 == 0 or i == 0:
                print(f"[PROCESS_DOCUMENT] Storing chunk {i+1}/{len(chunks)}...")
            if USE_DATABASE:
                try:
                    # Prepare metadata - handle both token-based and char-based chunking
                    chunk_metadata = {
                        "char_count": chunk_data.get("char_count", len(chunk_data["content"])),
                        "token_count": chunk_data.get("token_count", 0)
                    }
                    
                    # Add page numbers (Phase 1: Page Tracking for citations)
                    if "page" in chunk_data:
                        chunk_metadata["page"] = chunk_data["page"]
                    if "page_start" in chunk_data:
                        chunk_metadata["page_start"] = chunk_data["page_start"]
                    if "page_end" in chunk_data:
                        chunk_metadata["page_end"] = chunk_data["page_end"]
                    
                    # Add character positions if available (character-based chunking)
                    if "start_char" in chunk_data:
                        chunk_metadata["start_char"] = chunk_data["start_char"]
                        chunk_metadata["end_char"] = chunk_data["end_char"]
                        chunk_metadata["length"] = chunk_data.get("length", chunk_data["char_count"])
                    
                    # Add token positions if available (token-based chunking)
                    if "start_token" in chunk_data:
                        chunk_metadata["start_token"] = chunk_data["start_token"]
                        chunk_metadata["end_token"] = chunk_data["end_token"]
                        # Estimate character positions from token positions
                        if "start_char" not in chunk_data:
                            chunk_metadata["start_char"] = 0  # Approximate
                            chunk_metadata["end_char"] = chunk_data["char_count"]
                            chunk_metadata["length"] = chunk_data["char_count"]
                    
                    chunk = create_chunk(
                        doc_id=doc_id,
                        kb_id=kb_id,
                        chunk_index=chunk_data["chunk_index"],
                        content=chunk_data["content"],
                        metadata=chunk_metadata
                    )
                    if chunk:
                        stored_chunks.append(chunk)
                    else:
                        print(f"[WARNING] Chunk {i} was not stored (returned None)")
                except Exception as e:
                    print(f"[ERROR] Failed to store chunk {i}: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                # File-based storage for chunks
                kb_dir = DATA_DIR / "knowledge_bases" / kb_id
                chunks_dir = kb_dir / "chunks"
                chunks_dir.mkdir(parents=True, exist_ok=True)
                
                chunk_file = chunks_dir / f"{doc_id}_chunk_{chunk_data['chunk_index']}.json"
                import json
                with open(chunk_file, "w") as f:
                    json.dump(chunk_data, f, indent=2)
                
                stored_chunks.append(chunk_data)
        
        # Phase 2: Generate embeddings for chunks (if configured)
        if EMBEDDINGS_AVAILABLE and USE_DATABASE and stored_chunks:
            print(f"[PROCESS_DOCUMENT] Generating embeddings for {len(stored_chunks)} chunks...")
            embeddings_generated = 0
            
            # Generate embeddings in batches for efficiency
            chunk_contents = [chunk.get("content", "") if isinstance(chunk, dict) else chunk_data["content"] 
                            for chunk, chunk_data in zip(stored_chunks, chunks)]
            
            embeddings = generate_embeddings_batch(chunk_contents, batch_size=50)
            
            # Store embeddings back to chunks
            for i, (chunk, embedding) in enumerate(zip(stored_chunks, embeddings)):
                if embedding and isinstance(chunk, dict) and "id" in chunk:
                    try:
                        chunk_id = chunk["id"]
                        success = update_chunk_embedding(chunk_id, embedding)
                        if success:
                            embeddings_generated += 1
                            if (i + 1) % 10 == 0:
                                print(f"[PROCESS_DOCUMENT] Stored embeddings for {i + 1}/{len(stored_chunks)} chunks...")
                    except Exception as e:
                        print(f"[ERROR] Failed to store embedding for chunk {i}: {e}")
            
            print(f"[PROCESS_DOCUMENT] Generated and stored {embeddings_generated}/{len(stored_chunks)} embeddings")
        elif not EMBEDDINGS_AVAILABLE:
            print(f"[PROCESS_DOCUMENT] Embeddings not configured (set OPENAI_API_KEY in .env)")
        
        # Update document status
        chunk_count = len(stored_chunks)
        print(f"[PROCESS_DOCUMENT] Updating document status: {chunk_count} chunks stored")
        
        if USE_DATABASE:
            update_document(
                doc_id,
                status="ready",
                chunks_count=chunk_count,
                processed_at=datetime.now().isoformat()
            )
            print(f"[PROCESS_DOCUMENT] Document {doc_id} updated in database: status=ready, chunks={chunk_count}")
        else:
            # Update metadata file
            kb_dir = DATA_DIR / "knowledge_bases" / kb_id
            docs_dir = kb_dir / "documents"
            metadata_file = docs_dir / f"{doc_id}.json"
            
            if metadata_file.exists():
                import json
                with open(metadata_file) as f:
                    doc_data = json.load(f)
                
                doc_data["status"] = "ready"
                doc_data["chunks_count"] = chunk_count
                doc_data["processed_at"] = datetime.now().isoformat()
                
                with open(metadata_file, "w") as f:
                    json.dump(doc_data, f, indent=2)
        
        return {
            "success": True,
            "chunk_count": chunk_count,
            "message": f"Processed document into {chunk_count} chunks"
        }
        
    except Exception as e:
        print(f"Error processing document {doc_id}: {e}")
        import traceback
        traceback.print_exc()
        
        # Update status to failed
        try:
            if USE_DATABASE:
                update_document(doc_id, status="failed")
            else:
                kb_dir = DATA_DIR / "knowledge_bases" / kb_id
                docs_dir = kb_dir / "documents"
                metadata_file = docs_dir / f"{doc_id}.json"
                if metadata_file.exists():
                    import json
                    with open(metadata_file) as f:
                        doc_data = json.load(f)
                    doc_data["status"] = "failed"
                    with open(metadata_file, "w") as f:
                        json.dump(doc_data, f, indent=2)
        except:
            pass
        
        return {"success": False, "error": str(e)}


# Background processing is handled by asyncio.create_task in the route


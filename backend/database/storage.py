"""
Supabase Storage utilities for file uploads
Handles PDF storage in Supabase Storage buckets
"""
import os
import uuid
from typing import Optional, BinaryIO
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Supabase connection
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Service key for storage operations

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    supabase_storage: Optional[Client] = None
else:
    supabase_storage: Optional[Client] = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Storage bucket name
STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "knowledge-base-documents")


def is_storage_configured() -> bool:
    """Check if Supabase Storage is configured"""
    return supabase_storage is not None


def upload_file_to_storage(
    kb_id: str,
    file_content: bytes,
    filename: str,
    content_type: str = "application/pdf"
) -> Optional[str]:
    """
    Upload file to Supabase Storage
    
    Returns:
        Public URL of the uploaded file, or None if upload failed
    """
    if not supabase_storage:
        return None
    
    try:
        # Generate unique file path: knowledge-bases/{kb_id}/{file_id}_{filename}
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(filename)[1]
        storage_path = f"knowledge-bases/{kb_id}/{file_id}{file_ext}"
        
        # Upload to Supabase Storage
        response = supabase_storage.storage.from_(STORAGE_BUCKET).upload(
            path=storage_path,
            file=file_content,
            file_options={
                "content-type": content_type,
                "upsert": False
            }
        )
        
        # Get public URL
        public_url = supabase_storage.storage.from_(STORAGE_BUCKET).get_public_url(storage_path)
        return public_url
        
    except Exception as e:
        print(f"Error uploading to Supabase Storage: {e}")
        return None


def download_file_from_storage(storage_path: str) -> Optional[bytes]:
    """
    Download file from Supabase Storage
    
    Args:
        storage_path: Path in storage bucket (e.g., "knowledge-bases/{kb_id}/{file_id}.pdf")
    
    Returns:
        File content as bytes, or None if download failed
    """
    if not supabase_storage:
        print("[STORAGE] Supabase storage not configured")
        return None
    
    try:
        print(f"[STORAGE] Downloading from path: {storage_path}")
        response = supabase_storage.storage.from_(STORAGE_BUCKET).download(storage_path)
        
        if response:
            print(f"[STORAGE] Downloaded {len(response)} bytes")
            # Verify it's actually PDF content
            if len(response) > 0:
                # Check PDF magic bytes
                if response[:4] == b'%PDF':
                    print(f"[STORAGE] Valid PDF file detected")
                else:
                    print(f"[WARNING] File doesn't start with PDF magic bytes: {response[:20]}")
        else:
            print(f"[ERROR] Download returned None/empty")
        
        return response
    except Exception as e:
        print(f"[ERROR] Error downloading from Supabase Storage: {e}")
        import traceback
        traceback.print_exc()
        return None


def delete_file_from_storage(storage_path: str) -> bool:
    """
    Delete file from Supabase Storage
    
    Args:
        storage_path: Path in storage bucket
    
    Returns:
        True if deleted successfully, False otherwise
    """
    if not supabase_storage:
        return False
    
    try:
        supabase_storage.storage.from_(STORAGE_BUCKET).remove([storage_path])
        return True
    except Exception as e:
        print(f"Error deleting from Supabase Storage: {e}")
        return False


def get_storage_path_from_url(url: str) -> Optional[str]:
    """
    Extract storage path from public URL
    
    Args:
        url: Public URL from Supabase Storage
    
    Returns:
        Storage path or None
    
    Example URLs:
    - https://xxx.supabase.co/storage/v1/object/public/knowledge-base-documents/knowledge-bases/{kb_id}/{file_id}.pdf
    - https://xxx.supabase.co/storage/v1/object/sign/knowledge-base-documents/knowledge-bases/{kb_id}/{file_id}.pdf?token=...
    """
    if not url:
        print(f"[STORAGE] Empty URL provided")
        return None
    
    print(f"[STORAGE] Extracting path from URL: {url[:100]}...")
    
    # Remove query parameters first
    if "?" in url:
        url = url.split("?")[0]
        print(f"[STORAGE] Removed query params, URL: {url[:100]}...")
    
    # Extract path from URL like: https://xxx.supabase.co/storage/v1/object/public/bucket/path
    try:
        # Handle both public and signed URLs
        if "/storage/v1/object/public/" in url:
            parts = url.split("/storage/v1/object/public/")
        elif "/storage/v1/object/sign/" in url:
            parts = url.split("/storage/v1/object/sign/")
        else:
            print(f"[STORAGE] URL doesn't match expected pattern (no /storage/v1/object/public/ or /sign/)")
            return None
        
        if len(parts) < 2:
            print(f"[STORAGE] URL split failed, got {len(parts)} parts")
            return None
        
        path_with_bucket = parts[1]
        print(f"[STORAGE] Path with bucket: {path_with_bucket}")
        
        # Remove bucket name from path (first segment)
        if "/" not in path_with_bucket:
            print(f"[STORAGE] No path segments found after bucket")
            return None
        
        # Split and skip first part (bucket name)
        path_parts = path_with_bucket.split("/")
        if len(path_parts) < 2:
            print(f"[STORAGE] No path after bucket name (only {len(path_parts)} parts)")
            return None
        
        path = "/".join(path_parts[1:])  # Everything after bucket name
        print(f"[STORAGE] Extracted path: {path}")
        return path
        
    except Exception as e:
        print(f"[ERROR] Error extracting path from URL: {e}")
        import traceback
        traceback.print_exc()
        return None


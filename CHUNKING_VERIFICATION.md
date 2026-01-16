# Chunking Verification Guide

## How to Verify Chunks Are Being Created in Supabase

### 1. Check FastAPI Console Logs

After uploading a PDF, you should see logs like:
```
[UPLOAD] Background processing scheduled for 1 document(s)
============================================================
[PROCESSING] Starting chunking for document {doc_id} in KB {kb_id}
============================================================

[PROCESS_DOCUMENT] Using database, fetching document {doc_id}
[PROCESS_DOCUMENT] Document found: filename.pdf
[PROCESS_DOCUMENT] File path: https://..., type: pdf, storage: supabase_storage
[PROCESS_DOCUMENT] Extracting text from pdf file...
[PROCESS_DOCUMENT] Extracted 5000 characters from PDF
[PROCESS_DOCUMENT] Chunking text into pieces...
[PROCESS_DOCUMENT] Created 5 chunks
[PROCESS_DOCUMENT] Storing 5 chunks in database...
[PROCESS_DOCUMENT] Storing chunk 1/5...
[PROCESS_DOCUMENT] Updating document status: 5 chunks stored
[PROCESS_DOCUMENT] Document {doc_id} updated in database: status=ready, chunks=5

============================================================
[SUCCESS] Document {doc_id} processed: 5 chunks created
============================================================
```

### 2. Check Supabase Tables

Go to Supabase Dashboard → Table Editor:

#### Check `documents` table:
- Find your document by `id` or `filename`
- Verify `status` = "ready" (not "processing")
- Check `chunks_count` > 0

#### Check `document_chunks` table:
- Filter by `document_id` = your document ID
- You should see multiple rows (one per chunk)
- Each row has:
  - `chunk_index`: 0, 1, 2, ...
  - `content`: The actual text chunk
  - `metadata`: JSON with start_char, end_char, length

### 3. Use Manual Processing Endpoint

If chunks aren't being created automatically, trigger manually:

```bash
POST http://localhost:8001/api/v1/knowledge-base/{kb_id}/documents/{doc_id}/process
```

This will:
- Process the document immediately
- Return chunk count
- Show any errors

### 4. Use Test Script

```bash
cd backend
python test_chunking.py {kb_id} {doc_id}
```

This will:
- Process the document
- Show detailed logs
- Return success/failure

### 5. Check Frontend UI

- Document status should change from "processing" → "ready"
- Chunk count should appear (e.g., "5 chunks")
- Auto-refreshes every 3 seconds

## Common Issues

### Issue: Chunks not appearing in Supabase

**Check:**
1. Is Supabase configured? (`SUPABASE_URL` and `SUPABASE_ANON_KEY` in `.env`)
2. Does `document_chunks` table exist? (Run `schema.sql`)
3. Check FastAPI logs for errors
4. Try manual processing endpoint

### Issue: Processing never completes

**Check:**
1. Is PyPDF2 installed? (`pip install PyPDF2`)
2. Check FastAPI console for error messages
3. Verify document exists in `documents` table
4. Check file can be downloaded from Supabase Storage

### Issue: "Document not found" error

**Check:**
1. Wait 2-3 seconds after upload before processing
2. Verify document was created in database
3. Check document ID is correct

## Expected Behavior

1. **Upload PDF** → Document created in `documents` table, status="processing"
2. **2 seconds later** → Processing starts (check logs)
3. **Processing** → Text extracted, chunked, stored in `document_chunks`
4. **Complete** → Document status="ready", chunks_count updated
5. **UI updates** → Shows chunk count, status changes

## SQL Query to Check Chunks

```sql
-- Count chunks per document
SELECT 
    d.filename,
    d.chunks_count,
    COUNT(c.id) as actual_chunks
FROM documents d
LEFT JOIN document_chunks c ON c.document_id = d.id
GROUP BY d.id, d.filename, d.chunks_count;

-- View all chunks for a document
SELECT 
    chunk_index,
    LEFT(content, 100) as content_preview,
    metadata
FROM document_chunks
WHERE document_id = 'your-doc-id'
ORDER BY chunk_index;
```








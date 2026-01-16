# Phase 2: Embeddings + Vector Search - Setup Guide

## ✅ What's Been Implemented

1. **pgvector Schema** (`backend/database/schema_pgvector.sql`)
   - pgvector extension
   - `embedding` column on `document_chunks` table
   - Vector similarity search function

2. **Embeddings Service** (`backend/services/embeddings.py`)
   - OpenAI embeddings generation
   - Batch processing support
   - Configurable model (default: `text-embedding-3-small`)

3. **Database Functions** (`backend/database/db.py`)
   - `update_chunk_embedding()` - Store embeddings
   - `search_similar_chunks()` - Vector similarity search

4. **Document Processor** (`backend/services/document_processor.py`)
   - Auto-generates embeddings after chunking
   - Stores embeddings in database

## 📋 Setup Steps

### Step 1: Install Dependencies

```bash
cd backend
pip install openai==1.12.0
```

### Step 2: Add OpenAI API Key to `.env`

Add to `backend/.env`:
```env
OPENAI_API_KEY=sk-your-api-key-here
EMBEDDING_MODEL=text-embedding-3-small  # Optional, defaults to this
```

**Cost**: ~$0.02 per 1M tokens
- For 1000 chunks (~500K tokens): ~$0.01 per document
- Very cheap for testing!

### Step 3: Run pgvector Schema in Supabase

1. Go to **Supabase Dashboard** → **SQL Editor**
2. Open `backend/database/schema_pgvector.sql`
3. Copy and paste the SQL
4. Click **Run**

This will:
- Enable pgvector extension
- Add `embedding` column to `document_chunks`
- Create vector index for fast search
- Create `find_similar_chunks()` function

### Step 4: Restart FastAPI Server

```bash
# Stop current server (Ctrl+C)
# Then restart
cd backend
python main.py
```

## 🧪 Testing

### Test 1: Upload a New Document

1. Upload a PDF through the UI
2. Check FastAPI logs - you should see:
   ```
   [PROCESS_DOCUMENT] Generating embeddings for X chunks...
   [EMBEDDING] Processing batch 1/1 (X texts)...
   [EMBEDDING] Generated X embeddings
   [PROCESS_DOCUMENT] Generated and stored X/X embeddings
   ```

### Test 2: Verify Embeddings in Database

Run in Supabase SQL Editor:
```sql
-- Check if embeddings exist
SELECT 
    chunk_index,
    CASE 
        WHEN embedding IS NULL THEN 'No embedding'
        ELSE 'Has embedding'
    END as embedding_status,
    LENGTH(content) as content_length
FROM document_chunks
WHERE document_id = 'your-doc-id'
ORDER BY chunk_index
LIMIT 5;
```

### Test 3: Test Vector Search

We'll create a search endpoint in Phase 3, but you can test the function directly:

```sql
-- This will be available via API in Phase 3
SELECT * FROM find_similar_chunks(
    query_embedding := '[0.1, 0.2, ...]'::vector(1536),  -- Your query embedding
    kb_id_param := 'your-kb-id'::uuid,
    match_threshold := 0.7,
    match_count := 5
);
```

## 📊 What Happens Now

When you upload a document:

1. ✅ **Extract** text (page-aware)
2. ✅ **Chunk** text (with page numbers)
3. ✅ **Store** chunks in database
4. ✅ **Generate** embeddings (NEW!)
5. ✅ **Store** embeddings in database
6. ✅ **Update** document status to "ready"

## 🎯 Next: Phase 3 - RAG Endpoint

Once embeddings are working, we'll create:
- `/api/v1/knowledge-base/{kb_id}/ask` endpoint
- Query embedding generation
- Similar chunk retrieval
- LLM answer generation with citations

## ⚠️ Troubleshooting

### "Embeddings not configured"
- Check `OPENAI_API_KEY` is set in `.env`
- Restart FastAPI server

### "Failed to update chunk embedding"
- Check pgvector extension is enabled in Supabase
- Check `embedding` column exists: `SELECT column_name FROM information_schema.columns WHERE table_name = 'document_chunks';`

### "No embeddings generated"
- Check OpenAI API key is valid
- Check API quota/limits
- Check FastAPI logs for error messages

## 💰 Cost Estimate

**Embeddings**:
- `text-embedding-3-small`: $0.02 per 1M tokens
- Average document (1000 chunks): ~$0.01
- 100 documents: ~$1.00

**Very affordable for testing!**






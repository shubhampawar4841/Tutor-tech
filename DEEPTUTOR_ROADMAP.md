# DeepTutor Implementation Roadmap

## 🎯 What's REQUIRED vs OPTIONAL

### ✅ **REQUIRED for Basic DeepTutor (Minimum Viable)**
1. **Page-based extraction with page tracking** ⚠️ (Partially done - we extract pages but don't track per chunk)
2. **Embeddings + Vector Search** ❌ (Critical - enables semantic search)
3. **RAG Answering with Citations** ❌ (Core feature - the "tutor" part)

### 📋 **OPTIONAL (Nice to Have)**
1. **Pipeline States** (UPLOADED → EXTRACTING → CHUNKING → EMBEDDING → READY)
   - Current: Just "processing" → "ready"
   - Benefit: Better progress tracking, but not essential
2. **WebSocket/SSE Progress Updates** 
   - Current: Polling works fine
   - Benefit: Real-time updates, but polling is acceptable
3. **Advanced Citation Formatting**
   - Current: Can add basic citations
   - Benefit: Better UX, but basic citations work

---

## 📊 Current Status

### ✅ What We Have
- [x] Upload route with Supabase Storage
- [x] PDF text extraction (PyMuPDF)
- [x] Token-based chunking
- [x] Chunk storage in database
- [x] Basic document status (processing/ready)
- [x] Page extraction (but page numbers lost in chunking)

### ❌ What We're Missing
- [ ] **Page tracking per chunk** (chunks don't know which page they came from)
- [ ] **Embeddings generation** (no vector search yet)
- [ ] **pgvector setup** (no vector database)
- [ ] **RAG query endpoint** (can't ask questions yet)
- [ ] **Citation generation** (no answer + citation format)

---

## 🚀 Implementation Priority (Fastest Path)

### **Phase 1: Page Tracking** (30 min) ⚡ CRITICAL
**Why**: Without page numbers, citations are useless ("PDF X, page ?")

**What to do**:
1. Modify `extract_text_from_pdf()` to return `List[Dict[str, str]]` instead of single string
   ```python
   [
       {"page": 1, "text": "..."},
       {"page": 2, "text": "..."}
   ]
   ```
2. Modify `chunk_text()` to accept page-aware input
3. Store `page_start` and `page_end` in chunk metadata

**Files to modify**:
- `backend/services/document_processor.py` - `extract_text_from_pdf()`, `chunk_text()`, `process_document()`

---

### **Phase 2: Embeddings + Vector Search** (2-3 hours) ⚡ CRITICAL
**Why**: This is what makes "search" work. Without it, you can only do keyword search.

**What to do**:

#### 2a. Add pgvector extension to Supabase
```sql
-- Run in Supabase SQL Editor
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to document_chunks
ALTER TABLE document_chunks 
ADD COLUMN IF NOT EXISTS embedding vector(1536); -- OpenAI ada-002 dimension

-- Create index for fast similarity search
CREATE INDEX IF NOT EXISTS idx_chunks_embedding 
ON document_chunks 
USING ivfflat (embedding vector_cosine_ops);
```

#### 2b. Generate embeddings during chunking
- Add embedding generation step after chunking
- Use OpenAI `text-embedding-ada-002` or `text-embedding-3-small` (cheaper)
- Store embedding in `document_chunks.embedding` column

#### 2c. Create search function
- Embed user query
- Find top K chunks by cosine similarity
- Return chunks with metadata

**Files to create/modify**:
- `backend/services/embeddings.py` (new)
- `backend/services/document_processor.py` (add embedding step)
- `backend/database/schema.sql` (add pgvector)
- `backend/api/routes/knowledge_base.py` (add search endpoint)

**Dependencies**:
```bash
pip install openai  # or sentence-transformers for free embeddings
```

---

### **Phase 3: RAG Answering** (1-2 hours) ⚡ CRITICAL
**Why**: This is the "tutor" - answering questions with citations.

**What to do**:

#### 3a. Create "Ask" endpoint
```
POST /api/v1/knowledge-base/{kb_id}/ask
{
  "question": "What is photosynthesis?",
  "top_k": 5
}
```

#### 3b. RAG Pipeline
1. Embed user question
2. Find top K relevant chunks (from Phase 2)
3. Build prompt with context:
   ```
   Use only the following sources to answer:
   
   [Source 1] Page 17: "..."
   [Source 2] Page 23: "..."
   
   Question: {question}
   
   Answer with citations like [1], [2]
   ```
4. Call LLM (OpenAI GPT-4 or Claude)
5. Parse citations from response
6. Return:
   ```json
   {
     "answer": "Photosynthesis is... [1] [2]",
     "citations": [
       {"id": 1, "doc": "bio.pdf", "page": 17, "snippet": "..."},
       {"id": 2, "doc": "bio.pdf", "page": 23, "snippet": "..."}
     ]
   }
   ```

**Files to create/modify**:
- `backend/services/rag.py` (new)
- `backend/api/routes/knowledge_base.py` (add `/ask` endpoint)
- `backend/services/llm.py` (new - LLM client)

**Dependencies**:
```bash
pip install openai  # or anthropic for Claude
```

---

### **Phase 4: Pipeline States** (Optional - 1 hour)
**Why**: Better UX, but not essential for MVP

**What to do**:
1. Update `documents.status` enum:
   - `uploaded` → `extracting` → `chunking` → `embedding` → `ready` (or `failed`)
2. Add progress tracking:
   ```python
   update_document(doc_id, status="extracting", progress={"pages_done": 5, "total_pages": 20})
   ```
3. Update frontend to show progress

**Files to modify**:
- `backend/services/document_processor.py` (add status updates)
- `backend/database/schema.sql` (update status enum)
- `my-app/src/app/knowledge-base/page.tsx` (show progress)

---

## 🎯 Minimum Viable DeepTutor

**To get a working "Ask" feature, you need:**

1. ✅ Page tracking (Phase 1)
2. ✅ Embeddings (Phase 2)
3. ✅ RAG endpoint (Phase 3)

**Total time**: ~4-6 hours

**What you can skip for MVP**:
- ❌ Pipeline states (just use "processing" → "ready")
- ❌ WebSocket (polling is fine)
- ❌ Advanced citation formatting (basic [1], [2] works)

---

## 📝 Implementation Checklist

### Phase 1: Page Tracking
- [ ] Modify `extract_text_from_pdf()` to return page-aware structure
- [ ] Update `chunk_text()` to preserve page numbers
- [ ] Store `page_start`, `page_end` in chunk metadata
- [ ] Test: Verify chunks have page numbers in database

### Phase 2: Embeddings
- [ ] Add pgvector extension to Supabase
- [ ] Add `embedding` column to `document_chunks` table
- [ ] Create `embeddings.py` service
- [ ] Generate embeddings during chunking
- [ ] Create search function (embed query + find similar chunks)
- [ ] Test: Verify embeddings are stored, search returns relevant chunks

### Phase 3: RAG
- [ ] Create `/ask` endpoint
- [ ] Implement RAG pipeline (retrieve → prompt → LLM → parse)
- [ ] Format citations with page numbers
- [ ] Test: Ask a question, verify answer + citations

### Phase 4: Polish (Optional)
- [ ] Add pipeline states
- [ ] Add progress tracking
- [ ] Add WebSocket/SSE for real-time updates
- [ ] Improve citation formatting

---

## 🔧 Quick Start: Which Phase First?

**If you want to test RAG ASAP:**
1. Start with **Phase 2 (Embeddings)** - this is the bottleneck
2. Then **Phase 1 (Page Tracking)** - needed for citations
3. Then **Phase 3 (RAG)** - puts it all together

**If you want to build incrementally:**
1. **Phase 1** first (easiest, 30 min)
2. Then **Phase 2** (hardest, 2-3 hours)
3. Then **Phase 3** (ties it together, 1-2 hours)

---

## 💰 Cost Estimates

**Embeddings**:
- OpenAI `text-embedding-3-small`: ~$0.02 per 1M tokens
- For 1000 chunks (~500K tokens): ~$0.01 per document
- **Free alternative**: `sentence-transformers` (runs locally, slower)

**LLM (for RAG)**:
- OpenAI GPT-4: ~$0.03 per question (expensive)
- OpenAI GPT-3.5-turbo: ~$0.002 per question (cheap)
- **Free alternative**: Local LLM (Ollama, slower but free)

---

## 🎓 Summary

**Required for MVP**:
1. Page tracking ✅ (30 min)
2. Embeddings + Vector Search ✅ (2-3 hours)
3. RAG Answering ✅ (1-2 hours)

**Total**: ~4-6 hours of work

**Optional**:
- Pipeline states (1 hour)
- WebSocket progress (1-2 hours)
- Advanced formatting (30 min)

**You can skip the optional stuff and still have a working DeepTutor!**






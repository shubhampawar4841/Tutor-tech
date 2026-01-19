# Where Are Chunks Stored?

Based on your configuration, chunks are stored in **one of two places**:

## ✅ If Supabase is Configured (`USE_DATABASE=True`)

**Location**: **Supabase Database** → `document_chunks` table

### How to View:
1. Go to **Supabase Dashboard**
2. Navigate to **Table Editor**
3. Click on **`document_chunks`** table
4. Filter by `document_id` = your document ID

### What You'll See:
- Each row = one chunk
- Columns:
  - `id`: Chunk UUID
  - `document_id`: Links to your document
  - `knowledge_base_id`: Links to your KB
  - `chunk_index`: 0, 1, 2, ... (order)
  - `content`: The actual text chunk
  - `metadata`: JSON with start_char, end_char, length, token_count

### SQL Query to Check:
```sql
-- Count chunks for a document
SELECT COUNT(*) as chunk_count
FROM document_chunks
WHERE document_id = '4be8e135-4a4c-4f30-b94c-b2f07f01fa07';

-- View all chunks
SELECT 
    chunk_index,
    LEFT(content, 200) as content_preview,
    LENGTH(content) as char_count,
    metadata->>'token_count' as tokens
FROM document_chunks
WHERE document_id = '4be8e135-4a4c-4f30-b94c-b2f07f01fa07'
ORDER BY chunk_index;
```

---

## 📁 If Supabase NOT Configured (`USE_DATABASE=False`)

**Location**: **Local File System**

### Path:
```
backend/data/knowledge_bases/{kb_id}/chunks/{doc_id}_chunk_{index}.json
```

### Example:
For document `4be8e135-4a4c-4f30-b94c-b2f07f01fa07` in KB `ecf005aa-f991-444d-9fc8-e714f0ff774e`:

```
backend/data/knowledge_bases/ecf005aa-f991-444d-9fc8-e714f0ff774e/chunks/
  ├── 4be8e135-4a4c-4f30-b94c-b2f07f01fa07_chunk_0.json
  ├── 4be8e135-4a4c-4f30-b94c-b2f07f01fa07_chunk_1.json
  └── 4be8e135-4a4c-4f30-b94c-b2f07f01fa07_chunk_2.json
```

### How to Check:
```bash
# List all chunk files
ls backend/data/knowledge_bases/{kb_id}/chunks/{doc_id}_chunk_*.json

# Count chunks
ls backend/data/knowledge_bases/{kb_id}/chunks/{doc_id}_chunk_*.json | wc -l

# View a chunk
cat backend/data/knowledge_bases/{kb_id}/chunks/{doc_id}_chunk_0.json
```

---

## 🔍 How to Check Which Mode You're Using

Look at your FastAPI console logs. You should see:

### If using Supabase:
```
[PROCESS_DOCUMENT] Storing 2 chunks in database...
[PROCESS_DOCUMENT] Storing chunk 1/2...
[PROCESS_DOCUMENT] Document updated in database: status=ready, chunks=2
```

### If using file system:
```
[PROCESS_DOCUMENT] Storing 2 chunks in database...
[PROCESS_DOCUMENT] Storing chunk 1/2...
```

(Note: It says "database" but actually saves to files if `USE_DATABASE=False`)

---

## 📊 For Your Current Document

Based on your logs:
- **Document ID**: `4be8e135-4a4c-4f30-b94c-b2f07f01fa07`
- **KB ID**: `ecf005aa-f991-444d-9fc8-e714f0ff774e`
- **Text extracted**: 9,689 characters
- **Tokens**: 1,908 tokens
- **Expected chunks**: ~2 chunks (at 1000 tokens/chunk)

### Check Supabase:
```sql
SELECT * FROM document_chunks 
WHERE document_id = '4be8e135-4a4c-4f30-b94c-b2f07f01fa07'
ORDER BY chunk_index;
```

### Check File System:
```bash
ls backend/data/knowledge_bases/ecf005aa-f991-444d-9fc8-e714f0ff774e/chunks/4be8e135-4a4c-4f30-b94c-b2f07f01fa07_chunk_*.json
```












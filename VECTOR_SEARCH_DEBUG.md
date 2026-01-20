# Vector Search Debugging Guide

## Issue
Vector search is returning 0 results even though chunks with embeddings exist in the database.

## Root Causes

### 1. **RPC Function Issues**
The `find_similar_chunks` PostgreSQL function might:
- Not be created in the database
- Have parameter type mismatches
- Be failing silently

### 2. **Threshold Too High**
The similarity threshold (0.3) might be too high for the actual similarity scores.
- Cosine similarity ranges from -1 to 1
- pgvector normalizes to 0-1 range
- A threshold of 0.3 means chunks need 30% similarity

### 3. **Embedding Mismatch**
- Question embeddings might be generated with a different model than chunk embeddings
- Dimension mismatch (e.g., 1536 vs 3072)
- Normalization differences

## Debugging Steps

### Check RPC Function Exists
```sql
SELECT proname, prosrc 
FROM pg_proc 
WHERE proname = 'find_similar_chunks';
```

### Check Embeddings Exist
```sql
SELECT COUNT(*) 
FROM document_chunks 
WHERE knowledge_base_id = 'YOUR_KB_ID' 
AND embedding IS NOT NULL;
```

### Test RPC Function Directly
```sql
-- Get a sample embedding
SELECT embedding 
FROM document_chunks 
WHERE knowledge_base_id = 'YOUR_KB_ID' 
AND embedding IS NOT NULL 
LIMIT 1;

-- Test the function with that embedding
SELECT * FROM find_similar_chunks(
    (SELECT embedding FROM document_chunks WHERE knowledge_base_id = 'YOUR_KB_ID' LIMIT 1),
    'YOUR_KB_ID',
    0.1,  -- Very low threshold
    10    -- Get 10 results
);
```

### Check Embedding Dimensions
```sql
SELECT 
    id,
    array_length(embedding::float[], 1) as dims
FROM document_chunks 
WHERE knowledge_base_id = 'YOUR_KB_ID' 
AND embedding IS NOT NULL 
LIMIT 5;
```

## Solutions Implemented

1. **Better Logging**: Added detailed logging to see what's happening
2. **Fallback Logic**: Python-based similarity calculation when RPC fails
3. **Threshold Adjustment**: Lower threshold if no results found
4. **Error Handling**: Better error messages and fallback paths

## Next Steps

1. Check the logs to see if RPC is being called
2. Verify the RPC function exists in your database
3. Test with a very low threshold (0.1) to see if any results appear
4. Check embedding dimensions match between questions and chunks


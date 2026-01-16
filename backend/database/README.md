# Database Setup

## Supabase Setup (Optional)

If you want to use Supabase for database storage:

1. **Create a Supabase project** at https://supabase.com

2. **Get your credentials:**
   - Go to Project Settings > API
   - Copy `Project URL` → `SUPABASE_URL`
   - Copy `anon public` key → `SUPABASE_ANON_KEY`
   - Copy `service_role` key → `SUPABASE_SERVICE_ROLE_KEY` (for admin operations)

3. **Run the SQL schema:**
   - Go to Supabase Dashboard > SQL Editor
   - Copy and paste the contents of `schema.sql`
   - Run the script

4. **Add to `.env`:**
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
   ```

## File-Based Storage (Default)

If Supabase is not configured, the system will automatically use file-based storage in `./data/knowledge_bases/`.

No setup required - it works out of the box!

## Schema Overview

- **knowledge_bases**: Stores knowledge base metadata
- **documents**: Stores document information and file paths
- **document_chunks**: Stores text chunks for vector search (reference)

Vector embeddings are stored separately in ChromaDB/FAISS (not in Supabase).








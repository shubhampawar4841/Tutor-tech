# Supabase Storage Setup

## Create Storage Bucket

1. Go to your Supabase Dashboard
2. Navigate to **Storage**
3. Click **New bucket**
4. Name: `knowledge-base-documents`
5. **Public bucket**: ✅ Yes (or No if you want private)
6. Click **Create bucket**

## Set Up Bucket Policies (if private)

If you made it private, you need to set up policies:

```sql
-- Allow authenticated users to upload
CREATE POLICY "Allow uploads"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'knowledge-base-documents');

-- Allow authenticated users to read
CREATE POLICY "Allow reads"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'knowledge-base-documents');

-- Allow authenticated users to delete
CREATE POLICY "Allow deletes"
ON storage.objects FOR DELETE
TO authenticated
USING (bucket_id = 'knowledge-base-documents');
```

## Environment Variables

Add to your `.env`:

```env
# Supabase Storage
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_STORAGE_BUCKET=knowledge-base-documents
```

**Important**: Use `SUPABASE_SERVICE_ROLE_KEY` (not anon key) for storage operations!

## How It Works

1. **Upload**: PDF → Supabase Storage → Returns public URL
2. **Store**: URL saved in database (not file on disk)
3. **Process**: FastAPI downloads from storage when needed
4. **Delete**: Removes from both storage and database

## Benefits

✅ Files persist across server restarts  
✅ Works with multiple server instances  
✅ Scalable storage (not limited by server disk)  
✅ Easy to share files across workers  
✅ Automatic backups via Supabase  

## Fallback

If Supabase Storage is not configured, the system automatically falls back to local disk storage for development.








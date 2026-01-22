# Notebook Feature Setup

## Database Setup

The notebook feature requires database tables to be created. Follow these steps:

### Step 1: Run the Schema in Supabase

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Copy and paste the contents of `backend/database/schema_notebook.sql`
4. Click **Run** to execute the SQL

### Step 2: Verify Tables Created

After running the schema, verify the tables exist:

```sql
-- Check if tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('notebooks', 'notebook_items');
```

### Step 3: Test the API

Once the tables are created, you can test the notebook feature:

1. Start the backend: `cd backend && python main.py`
2. Go to the Notebook page in the frontend
3. Try creating a notebook

## Troubleshooting

### Error: "null value in column 'id' violates not-null constraint"

This means the UUID extension is not enabled or the default value isn't working.

**Solution:**
1. Run this in Supabase SQL Editor:
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

2. If the table already exists, you may need to drop and recreate it:
```sql
DROP TABLE IF EXISTS notebook_items CASCADE;
DROP TABLE IF EXISTS notebooks CASCADE;
```

Then run the full `schema_notebook.sql` again.

### Error: "Database not configured"

Make sure your `.env` file has:
```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### Error: "relation 'notebooks' does not exist"

The schema hasn't been run yet. Follow Step 1 above.










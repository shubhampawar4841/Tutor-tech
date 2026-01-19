# Environment Variables Setup

## For Production (Supabase Storage)

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
SUPABASE_STORAGE_BUCKET=knowledge-base-documents

# LLM Configuration
LLM_MODEL=gpt-4o
LLM_API_KEY=your-api-key-here
LLM_HOST=https://api.openai.com/v1

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8001
```

## For Development (Local Storage)

```env
# LLM Configuration
LLM_MODEL=gpt-4o
LLM_API_KEY=your-api-key-here
LLM_HOST=https://api.openai.com/v1

# Data Directory (local file storage)
DATA_DIR=./data

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8001
```

## Storage Configuration

- **With Supabase**: Set `SUPABASE_SERVICE_ROLE_KEY` → Files stored in Supabase Storage
- **Without Supabase**: Leave unset → Files stored in `./data/` directory

The system automatically detects which storage to use!












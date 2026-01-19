# DeepTutor Backend

FastAPI backend for DeepTutor AI-powered learning assistant.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Update `.env` with your API keys and configuration.

4. Run the server:
```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --port 8001
```

## API Documentation

Once running, visit:
- API Docs: http://localhost:8001/docs
- Alternative Docs: http://localhost:8001/redoc

## Endpoints

- `/api/v1/knowledge-base` - Knowledge base management
- `/api/v1/solve` - Problem solving
- `/api/v1/question` - Question generation
- `/api/v1/research` - Deep research
- `/api/v1/notebook` - Notebook management
- `/api/v1/guide` - Guided learning
- `/api/v1/co-writer` - Writing assistance
- `/api/v1/chat` - Chat interface
- `/api/v1/dashboard` - Dashboard stats













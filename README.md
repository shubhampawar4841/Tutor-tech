# DeepTutor - AI-Powered Learning Assistant

A comprehensive AI-powered learning platform with knowledge base management, problem solving, research automation, and more.

## 🚀 Features

- **Knowledge Base**: Upload and manage documents
- **Problem Solver**: Get step-by-step solutions
- **Question Generator**: Create practice questions
- **Deep Research**: Generate comprehensive research reports
- **Notebook**: Organize your learning materials
- **Guided Learning**: Interactive learning guides
- **Co-Writer**: AI writing assistant
- **IdeaGen**: Generate research ideas
- **Chat**: Quick Q&A interface

## 🛠️ Tech Stack

### Frontend
- Next.js 16
- React 19
- TypeScript
- Tailwind CSS 4
- Lucide React (Icons)

### Backend
- FastAPI
- Python 3.10+
- WebSocket support
- CORS enabled

## 📦 Setup

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy environment file:
```bash
cp .env.example .env
```

4. Update `.env` with your configuration:
```env
LLM_MODEL=gpt-4o
LLM_API_KEY=your-api-key-here
LLM_HOST=https://api.openai.com/v1
DATA_DIR=./data
```

5. Run the server:
```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --reload --port 8001
```

The API will be available at `http://localhost:8001`
- API Docs: http://localhost:8001/docs

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd my-app
```

2. Install dependencies:
```bash
npm install
```

3. Copy environment file:
```bash
cp .env.local.example .env.local
```

4. Update `.env.local` if needed:
```env
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=ws://localhost:8001
```

5. Run the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## 📁 Project Structure

```
.
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── api/
│   │   └── routes/             # API route handlers
│   │       ├── knowledge_base.py
│   │       ├── solve.py
│   │       ├── question.py
│   │       ├── research.py
│   │       ├── notebook.py
│   │       ├── guide.py
│   │       ├── co_writer.py
│   │       ├── chat.py
│   │       └── dashboard.py
│   ├── requirements.txt
│   └── README.md
│
├── my-app/                     # Next.js frontend
│   ├── src/
│   │   ├── app/                # Next.js app router pages
│   │   │   ├── page.tsx        # Dashboard
│   │   │   ├── knowledge-base/
│   │   │   ├── solve/
│   │   │   ├── questions/
│   │   │   ├── research/
│   │   │   ├── notebook/
│   │   │   ├── guide/
│   │   │   ├── co-writer/
│   │   │   ├── ideagen/
│   │   │   └── chat/
│   │   ├── components/         # React components
│   │   │   └── Navigation.tsx
│   │   └── lib/                # Utilities
│   │       ├── api.ts          # API client
│   │       └── websocket.ts    # WebSocket client
│   ├── package.json
│   └── .env.local.example
│
└── README.md
```

## 🔌 API Endpoints

### Knowledge Base
- `GET /api/v1/knowledge-base/` - List all knowledge bases
- `POST /api/v1/knowledge-base/` - Create knowledge base
- `GET /api/v1/knowledge-base/{id}` - Get knowledge base
- `POST /api/v1/knowledge-base/{id}/upload` - Upload documents
- `DELETE /api/v1/knowledge-base/{id}` - Delete knowledge base

### Solve
- `POST /api/v1/solve/start` - Start solving a problem
- `GET /api/v1/solve/{id}/status` - Get solve status
- `GET /api/v1/solve/{id}/result` - Get solve result
- `WS /api/v1/solve/{id}/stream` - Real-time updates

### Research
- `POST /api/v1/research/start` - Start research
- `GET /api/v1/research/{id}/status` - Get research status
- `GET /api/v1/research/{id}/result` - Get research result
- `WS /api/v1/research/{id}/stream` - Real-time progress

### And more...

See full API documentation at `http://localhost:8001/docs` when the backend is running.

## 🎯 Next Steps

1. **Implement Backend Logic**: Add actual business logic to API routes
2. **Add LLM Integration**: Connect to OpenAI/Anthropic APIs
3. **Implement RAG**: Set up vector databases and retrieval
4. **Add Authentication**: User management and sessions
5. **File Upload**: Implement document processing
6. **WebSocket Streaming**: Real-time updates for long-running tasks

## 📝 License

MIT








# Tutor-tech





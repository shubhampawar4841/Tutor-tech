# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Start the Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
python main.py
```

Backend will run on `http://localhost:8001`

### Step 2: Start the Frontend

```bash
cd my-app
npm install
cp .env.local.example .env.local
npm run dev
```

Frontend will run on `http://localhost:3000`

### Step 3: Open Your Browser

Visit `http://localhost:3000` and start using DeepTutor!

## ✅ What's Included

### Backend (FastAPI)
- ✅ All API routes for 10 features
- ✅ WebSocket support for real-time updates
- ✅ CORS configured for Next.js
- ✅ Structured route handlers
- ✅ Ready for LLM integration

### Frontend (Next.js)
- ✅ Dashboard with stats
- ✅ Navigation component
- ✅ All feature pages:
  - Knowledge Base
  - Solve
  - Questions
  - Research (with progress tracking)
  - Notebook
  - Chat
  - Guide (placeholder)
  - Co-Writer (placeholder)
  - IdeaGen (placeholder)
- ✅ API client utilities
- ✅ WebSocket client
- ✅ Responsive design with dark mode

## 🔧 Next Steps

1. **Add Backend Logic**: Implement actual functionality in route handlers
2. **Connect LLM**: Add OpenAI/Anthropic API integration
3. **Add RAG**: Set up vector databases
4. **File Upload**: Implement document processing
5. **Authentication**: Add user management

## 📚 API Documentation

Once backend is running, visit:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## 🐛 Troubleshooting

### Backend won't start
- Check Python version (3.10+)
- Install dependencies: `pip install -r requirements.txt`
- Check port 8001 is available

### Frontend can't connect to backend
- Ensure backend is running on port 8001
- Check `.env.local` has correct API URL
- Check CORS settings in backend

### WebSocket not working
- Ensure backend WebSocket routes are implemented
- Check browser console for errors
- Verify WebSocket URL in `.env.local`

## 📝 Notes

- Backend routes currently return placeholder data
- Frontend is fully functional and ready for backend integration
- All UI components are responsive and support dark mode
- WebSocket client is ready for real-time updates
















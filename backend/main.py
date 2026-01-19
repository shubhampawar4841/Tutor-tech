"""
DeepTutor FastAPI Backend
Main application entry point
"""
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Add startup logging
print("=" * 60)
print("Starting DeepTutor FastAPI Backend...")
print("=" * 60)

try:
    from api.routes import (
        knowledge_base,
        solve,
        question,
        research,
        notebook,
        guide,
        co_writer,
        chat,
        dashboard,
        ideagen
    )
    print("[OK] All routes imported successfully")
except Exception as e:
    print(f"[ERROR] Failed to import routes: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

app = FastAPI(
    title="DeepTutor API",
    description="AI-powered learning assistant backend",
    version="1.0.0"
)

# CORS middleware
# Allow localhost for development and Vercel for production
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Add Vercel URL from environment variable if set
VERCEL_URL = os.getenv("VERCEL_URL")
if VERCEL_URL:
    # Handle both with and without https://
    if not VERCEL_URL.startswith("http"):
        ALLOWED_ORIGINS.append(f"https://{VERCEL_URL}")
    else:
        ALLOWED_ORIGINS.append(VERCEL_URL)

# Also allow any Vercel preview deployments
FRONTEND_URL = os.getenv("FRONTEND_URL")
if FRONTEND_URL:
    if FRONTEND_URL not in ALLOWED_ORIGINS:
        ALLOWED_ORIGINS.append(FRONTEND_URL)

# For Railway deployment, allow all origins
# Note: Can't use ["*"] with allow_credentials=True
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
if ENVIRONMENT == "production":
    # In production (Railway), allow all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins
        allow_credentials=False,  # Must be False when using ["*"]
        allow_methods=["*"],
        allow_headers=["*"],
    )
    print("[CORS] Production mode: Allowing all origins")
else:
    # Development - use specific origins
    print(f"[CORS] Development mode - Allowed origins: {ALLOWED_ORIGINS}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
try:
    app.include_router(knowledge_base.router, prefix="/api/v1/knowledge-base", tags=["Knowledge Base"])
    app.include_router(solve.router, prefix="/api/v1/solve", tags=["Solve"])
    app.include_router(question.router, prefix="/api/v1/question", tags=["Question"])
    app.include_router(research.router, prefix="/api/v1/research", tags=["Research"])
    app.include_router(notebook.router, prefix="/api/v1/notebook", tags=["Notebook"])
    app.include_router(guide.router, prefix="/api/v1/guide", tags=["Guide"])
    app.include_router(co_writer.router, prefix="/api/v1/co-writer", tags=["Co-Writer"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
    app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
    app.include_router(ideagen.router, prefix="/api/v1/ideagen", tags=["IdeaGen"])
    print("[OK] All routers included successfully")
except Exception as e:
    print(f"[ERROR] Failed to include routers: {e}")
    import traceback
    traceback.print_exc()


@app.get("/")
async def root():
    """Health check endpoint"""
    return JSONResponse({
        "status": "ok",
        "message": "DeepTutor API is running",
        "version": "1.0.0"
    })


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )









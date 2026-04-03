from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routes
from app.routes import auth, resume, github

# Initialize app
app = FastAPI(
    title="Resume AI",
    description="AI-powered Resume Builder using LLM + Pinecone",
    version="1.0.0"
)

# ✅ CORS (IMPORTANT for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # change to specific domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include routers
app.include_router(resume.router, prefix="/resume", tags=["Resume"])
app.include_router(github.router, prefix="/github", tags=["GitHub"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])

# ✅ Root endpoint
@app.get("/")
def root():
    return {
        "message": "🚀 Resume AI Backend Running",
        "docs": "http://127.0.0.1:8000/docs"
    }

# ✅ Health check (for deployment / debugging)
@app.get("/health")
def health_check():
    return {"status": "ok"}

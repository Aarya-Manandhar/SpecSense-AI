from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.api.endpoints import router as api_router

app = FastAPI(
    title="SpecSense AI API",
    description="AI-powered Requirements Intelligence Engine API",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API endpoints
app.include_router(api_router)

# Serve a minimal frontend example file for quick local testing
frontend_dir = Path(__file__).resolve().parents[2] / 'frontend'
if frontend_dir.exists():
    app.mount('/frontend', StaticFiles(directory=str(frontend_dir)), name='frontend')

@app.get('/evaluation_example')
def evaluation_example():
    html = frontend_dir / 'evaluation_example.html'
    if not html.exists():
        raise HTTPException(status_code=404, detail='example html not found')
    return FileResponse(str(html))

@app.get("/")
def read_root():
    return {
        "message": "Welcome to SpecSense AI Requirements Intelligence API",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SpecSense AI Backend Engine",
        "version": "1.0.0"
    }

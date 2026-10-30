import os
import sys
import time
import logging
from pathlib import Path

# Ensure backend root and workspace root are always on sys.path
backend_dir = Path(__file__).resolve().parent.parent
repo_root = backend_dir.parent
for directory in (backend_dir, repo_root):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

try:
    from app.api.endpoints import router as api_router
except ImportError:
    from backend.app.api.endpoints import router as api_router

# Setup structured logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("specsense.api")

app = FastAPI(
    title="SpecSense AI API",
    description="AI-powered Requirements Intelligence Engine API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurable CORS for production security
raw_origins = os.getenv("CORS_ORIGINS", "*")
if raw_origins.strip() == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = [orig.strip() for orig in raw_origins.split(",") if orig.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security and performance headers middleware
@app.middleware("http")
async def add_security_and_timing_headers(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Custom headers
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

from starlette.exceptions import HTTPException as StarletteHTTPException

# Global uncaught exception handler to prevent leaking stack traces while preserving standard HTTP errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, (HTTPException, StarletteHTTPException)):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    logger.error(f"Unhandled error processing {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please contact the administrator if this persists."}
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
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SpecSense AI Backend Engine",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


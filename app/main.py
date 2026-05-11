"""FastAPI application entry point."""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.config import API_TITLE, API_VERSION, API_DESCRIPTION, CORS_ORIGINS
from app.database import init_db
from app.scheduler import start_scheduler, stop_scheduler
import html


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    # Startup
    await init_db()
    await start_scheduler()
    
    yield
    
    # Shutdown
    await stop_scheduler()


# Create FastAPI app
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security middleware - sanitize inputs
@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Add security headers."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# Sanitize HTML to prevent XSS
def sanitize_html(content: str) -> str:
    """Sanitize HTML content."""
    dangerous = ['<script', 'javascript:', 'onerror=', 'onload=', 'onclick=']
    for tag in dangerous:
        if tag.lower() in content.lower():
            # Escape the tag
            content = content.replace('<', '&lt;').replace('>', '&gt;')
            break
    return content


# Include routers
from app.routers import auth, contacts, messages, users

app.include_router(auth.router)
app.include_router(contacts.router)
app.include_router(messages.router)
app.include_router(users.router)


# Mount static files
static_dir = Path("static")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve main page."""
    static_dir = Path("static")
    
    index_file = static_dir / "index.html"
    if index_file.exists():
        return HTMLResponse(index_file.read_text())
    
    return """<!DOCTYPE html>
<html>
<head>
    <title>WhatsApp Automation</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <h1>WhatsApp Automation</h1>
        <p>Loading...</p>
    </div>
    <script src="/static/app.js"></script>
</body>
</html>"""


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": API_VERSION}


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""FastAPI application entry point."""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.config import API_TITLE, API_VERSION, API_DESCRIPTION
from app.database import init_db
from app.scheduler import start_scheduler, stop_scheduler


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


# Include routers
from app.routers import auth, contacts, messages

app.include_router(auth.router)
app.include_router(contacts.router)
app.include_router(messages.router)


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve main page."""
    from pathlib import Path
    static_dir = Path("static")
    
    index_file = static_dir / "index.html"
    if index_file.exists():
        return HTMLResponse(index_file.read_text())
    
    # Fallback: return basic HTML
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
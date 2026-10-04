import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from backend.config import settings
from backend.database import engine, Base
from backend.routes import upload, summarize, chat, history, download

# Create database tables if they do not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Summarizerr AI Backend",
    description="Backend API for AI-powered document parsing, summarization, and analysis",
    version="1.0.0"
)

# Configure CORS to allow the frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local file testing and development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(upload.router)
app.include_router(summarize.router)
app.include_router(chat.router)
app.include_router(history.router)
app.include_router(download.router)

# Mount generated charts folder to serve them to the UI
charts_path = os.path.join(settings.UPLOAD_DIR, "charts")
os.makedirs(charts_path, exist_ok=True)
app.mount("/charts", StaticFiles(directory=charts_path), name="charts")

# Mount frontend files (HTML/CSS) and JS scripts as static endpoints
# This allows running the entire app on a single port (e.g. localhost:8000)
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend"))
# Wait, let's make sure the path is correct relative to main.py
# main.py is in s:\summarizerr\backend\main.py.
# So the root of the project is s:\summarizerr\.
# So frontend_dir relative to main.py is "../frontend", i.e. path.dirname(main.py) is backend/, so parent is root.
# Let's write robust absolute paths using Project Root.
# Since settings or os.path is used:
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dir = os.path.join(project_root, "frontend")
js_dir = os.path.join(project_root, "js")

if os.path.exists(frontend_dir):
    app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")
if os.path.exists(js_dir):
    app.mount("/js", StaticFiles(directory=js_dir), name="js")

def serve_frontend_file(filename: str) -> HTMLResponse:
    file_path = os.path.join(frontend_dir, filename)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(
        content="<h1>Summarizerr Backend is Running</h1><p>Frontend files are not found.</p>",
        status_code=404,
    )

@app.get("/", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
async def serve_index():
    """
    Serve index.html at root URL.
    """
    return serve_frontend_file("index.html")

@app.get("/upload", response_class=HTMLResponse)
@app.get("/upload.html", response_class=HTMLResponse)
async def serve_upload():
    """
    Serve upload.html at /upload and /upload.html.
    """
    return serve_frontend_file("upload.html")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "Summarizerr AI Backend"}

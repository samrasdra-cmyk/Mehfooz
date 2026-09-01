"""
Mehfooz FastAPI application entry point.

Run locally:
    uvicorn app.main:app --reload --port 8000
    or
    uvicorn main:app --reload --port 8000
"""
import os
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.pipeline import run_pipeline
from app.regions import REGIONS
from app.database import init_db, get_recent_records
from app.config import DATA_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mehfooz")

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_PATH = Path(DATA_DIR).resolve()

app = FastAPI(
    title="Mehfooz Early Warning System",
    description="AI-powered early warning system for floods and GLOFs in Northern Pakistan",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    # Ensure data directory exists
    os.makedirs(DATA_PATH, exist_ok=True)


# Mount static data directory for generated satellite images and voice files
if os.path.exists(DATA_PATH):
    app.mount("/data", StaticFiles(directory=str(DATA_PATH)), name="data")


@app.get("/status")
def status():
    return {
        "status": "ok",
        "service": "mehfooz",
        "regions": list(REGIONS.keys()),
        "version": "0.1.0"
    }


@app.get("/regions")
def list_regions():
    return REGIONS


@app.post("/trigger-analysis/{region_id}")
def trigger_analysis(region_id: str, run_date: str | None = None):
    """
    Synchronous on-demand run (good for demos). For scheduled production
    runs, use the Celery task in app/tasks.py instead so this doesn't block
    the request/response cycle.
    """
    if region_id not in REGIONS:
        raise HTTPException(status_code=404, detail=f"Unknown region_id '{region_id}'")
    try:
        result = run_pipeline(region_id, run_date)
    except Exception as e:
        logger.exception(f"Pipeline execution failed for region {region_id}")
        raise HTTPException(status_code=500, detail=str(e))
    return result


@app.get("/history/{region_id}")
def history(region_id: str, limit: int = 20):
    if region_id not in REGIONS:
        raise HTTPException(status_code=404, detail=f"Unknown region_id '{region_id}'")
    records = get_recent_records(region_id=region_id, limit=limit)
    return records


# Serve dashboard on root and /dashboard if frontend directory exists
@app.get("/")
async def index_or_root(request: Request):
    # If client accepts text/html, serve the dashboard
    accept = request.headers.get("accept", "")
    index_file = FRONTEND_DIR / "index.html"
    if "text/html" in accept and index_file.exists():
        return FileResponse(str(index_file))
    elif index_file.exists():
        return FileResponse(str(index_file))
    return {"status": "ok", "service": "mehfooz", "regions": list(REGIONS.keys())}


@app.get("/dashboard")
async def dashboard():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"status": "error", "message": "Frontend dashboard not found"}, status_code=404)


# Mount frontend directory for static assets (styles, scripts, images)
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

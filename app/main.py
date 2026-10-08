"""
Mehfooz FastAPI application entry point.

Run locally:
    uvicorn app.main:app --reload --port 8000
    or
    uvicorn main:app --reload --port 8000
"""
import os
import logging
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, Field

from app.pipeline import run_pipeline
from app.regions import REGIONS
from app.database import init_db, get_recent_records
from app.config import DATA_DIR
from app.tts import synthesize_audio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mehfooz")
speech_requests = defaultdict(deque)

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


class SpeechRequest(BaseModel):
    language_code: str = Field(min_length=2, max_length=5)
    text: str = Field(min_length=1, max_length=1500)


@app.post("/speech")
async def speech(payload: SpeechRequest, request: Request):
    """Generate a short multilingual alert audio clip."""
    if payload.language_code not in {"en", "ur", "sd", "ps"}:
        raise HTTPException(status_code=400, detail="Choose English, Urdu, Sindhi, or Pashto")
    if payload.language_code == "sd":
        raise HTTPException(
            status_code=501,
            detail="No server-side free Sindhi voice is configured; trying a voice installed on your device.",
        )

    # Keep the free TTS endpoint from being spammed from one client.
    client_ip = request.client.host if request.client else "unknown"
    recent = speech_requests[client_ip]
    now = time.monotonic()
    while recent and now - recent[0] > 60:
        recent.popleft()
    if len(recent) >= 12:
        raise HTTPException(status_code=429, detail="Please wait before requesting more audio")
    recent.append(now)

    try:
        audio, media_type = await synthesize_audio(payload.text, payload.language_code)
    except RuntimeError as exc:
        logger.exception("Speech generation failed")
        raise HTTPException(status_code=502, detail="Speech generation failed") from exc
    except Exception as exc:
        logger.exception("Speech generation failed")
        raise HTTPException(status_code=502, detail="Speech generation failed; try again") from exc

    return Response(content=audio, media_type=media_type)


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

"""
Mehfooz FastAPI app.

Run locally:
    uvicorn main:app --reload

All external services (Sentinel Hub, Qwen-VL, Google Cloud, Twilio) fall
back to mock implementations automatically when credentials/flags aren't
set -- see app/config.py. This means `uvicorn main:app --reload` followed
by a POST to /trigger-analysis/{region_id} works out of the box with no
setup beyond `pip install -r requirements.txt`.
"""
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.pipeline import run_pipeline
from app.regions import REGIONS
from app.database import init_db, get_recent_records

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Mehfooz",
    description="AI-powered early warning system for floods and GLOFs",
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


@app.get("/")
def root():
    return {"status": "ok", "service": "mehfooz", "regions": list(REGIONS.keys())}


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
        raise HTTPException(status_code=500, detail=str(e))
    return result


@app.get("/history/{region_id}")
def history(region_id: str, limit: int = 20):
    if region_id not in REGIONS:
        raise HTTPException(status_code=404, detail=f"Unknown region_id '{region_id}'")
    records = get_recent_records(region_id=region_id, limit=limit)
    return records

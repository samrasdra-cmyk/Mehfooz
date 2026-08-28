"""
Celery worker for scheduled (daily) pipeline runs.

Start the worker:
    celery -A app.tasks worker --loglevel=info

Start the beat scheduler (for the daily 06:00 PKT trigger):
    celery -A app.tasks beat --loglevel=info

Requires a running Redis instance at REDIS_URL (see app/config.py or
docker-compose.yml, which starts one for you).
"""
from celery import Celery
from celery.schedules import crontab

from app.config import REDIS_URL
from app.regions import REGIONS
from app.pipeline import run_pipeline

celery_app = Celery("mehfooz", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.beat_schedule = {
    "daily-glof-check": {
        "task": "app.tasks.process_daily_alert_all_regions",
        "schedule": crontab(hour=1, minute=0),  # 06:00 PKT = 01:00 UTC
    },
}
celery_app.conf.timezone = "UTC"


@celery_app.task(name="app.tasks.process_daily_alert")
def process_daily_alert(region_id: str):
    return run_pipeline(region_id)


@celery_app.task(name="app.tasks.process_daily_alert_all_regions")
def process_daily_alert_all_regions():
    results = {}
    for region_id in REGIONS:
        results[region_id] = run_pipeline(region_id)
    return results

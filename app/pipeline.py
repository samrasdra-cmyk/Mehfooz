"""
End-to-end pipeline: fetch image -> analyze -> score risk -> alert if critical.
Used by both the FastAPI on-demand endpoint and the Celery scheduled task.
"""
from datetime import date as date_cls
import logging

from app.satellite_ingest import fetch_satellite_image
from app.qwen_analyzer import analyze_image
from app.risk_engine import calculate_risk
from app.translator import translate_alert
from app.tts import synthesize_voice
from app.sms import send_alert_sms
from app.evacuation import get_evacuation_route
from app.regions import get_region
from app.database import AnalysisRecord, save_record, get_last_area, init_db

logger = logging.getLogger("mehfooz.pipeline")

ALERT_LANGUAGES = {"ur": "ur-IN", "sd": "sd-IN", "ps": "ps-AF"}


def run_pipeline(region_id: str, run_date: str | None = None) -> dict:
    init_db()
    region = get_region(region_id)
    run_date = run_date or date_cls.today().isoformat()

    # 1. Ingest
    image_path = fetch_satellite_image(region_id, region["bbox"], run_date)

    # 2. Analyze
    analysis = analyze_image(image_path)

    # 3. Risk
    historical_area = get_last_area(region_id)
    risk = calculate_risk(analysis, historical_area=historical_area)

    result = {
        "region_id": region_id,
        "region_name": region["name"],
        "date": run_date,
        "image_path": image_path,
        "analysis": analysis,
        "risk": risk,
        "alerts": [],
    }

    # 4. Alert if critical
    if risk["is_critical"]:
        base_message = (
            f"FLOOD/GLOF WARNING: {region['name']} shows elevated risk "
            f"(score {risk['risk_score']}). Lake area ~{analysis['lake_area_km2']} km2. "
            f"Please move to higher ground immediately."
        )
        evac = get_evacuation_route(region_id)
        if evac:
            base_message += f" Suggested route: {evac['route']} (toward {evac['village']})."

        for lang_code, tts_locale in ALERT_LANGUAGES.items():
            translated = translate_alert(base_message, lang_code)
            audio_path = synthesize_voice(
                translated, tts_locale, f"{region_id}_{run_date}_{lang_code}.mp3"
            )
            sms_results = [
                send_alert_sms(recipient, translated, region["lat"], region["lon"])
                for recipient in region["recipients"]
            ]
            result["alerts"].append(
                {
                    "language": lang_code,
                    "translated_message": translated,
                    "audio_path": audio_path,
                    "sms_results": sms_results,
                }
            )

    # 5. Log
    record = AnalysisRecord(
        region_id=region_id,
        image_path=image_path,
        lake_area_km2=analysis["lake_area_km2"],
        new_channels=analysis["new_channels"],
        snowmelt_acceleration=analysis["snowmelt_acceleration"],
        risk_score=risk["risk_score"],
        is_critical=risk["is_critical"],
        alert_sent=bool(result["alerts"]),
    )
    save_record(record)

    return result

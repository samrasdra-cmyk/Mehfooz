"""
Risk scoring engine.

Weights and threshold are configurable via app.config / .env; the defaults
mirror the values in the original design doc but are explicitly unvalidated
placeholders -- tune them against real historical GLOF events before relying
on this for anything beyond a demo.
"""
from app.config import RISK_WEIGHTS, RISK_CRITICAL_THRESHOLD

MELT_SCORE_MAP = {"low": 0.2, "medium": 0.6, "high": 1.0}


def calculate_risk(analysis_result: dict, historical_area: float | None = None) -> dict:
    area = analysis_result.get("lake_area_km2", 0.0)
    new_channels = analysis_result.get("new_channels", False)
    snowmelt = analysis_result.get("snowmelt_acceleration", "low")

    expansion_factor = 1.0
    if historical_area and historical_area > 0:
        expansion_factor = area / historical_area

    area_score = min(expansion_factor / 2.0, 1.0)  # 2x expansion = max area risk
    channel_score = 1.0 if new_channels else 0.0
    melt_score = MELT_SCORE_MAP.get(snowmelt, 0.0)

    risk = (
        area_score * RISK_WEIGHTS["area"]
        + channel_score * RISK_WEIGHTS["channel"]
        + melt_score * RISK_WEIGHTS["melt"]
    )
    risk = round(min(risk, 1.0), 4)

    return {
        "risk_score": risk,
        "is_critical": risk > RISK_CRITICAL_THRESHOLD,
        "components": {
            "area_score": round(area_score, 4),
            "channel_score": channel_score,
            "melt_score": melt_score,
            "expansion_factor": round(expansion_factor, 4),
        },
    }

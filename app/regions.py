"""
Sample region registry for the demo. In production this should be a proper
table (with recipient consent/opt-in tracking) rather than a constant.
"""

REGIONS = {
    "shishper_lake": {
        "name": "Shishper Glacial Lake",
        "bbox": [74.55, 36.15, 74.65, 36.25],  # min_lon, min_lat, max_lon, max_lat
        "lat": 36.2,
        "lon": 74.6,
        "recipients": ["+920000000001"],  # placeholder numbers
    },
    "passu_lake": {
        "name": "Passu Glacial Lake",
        "bbox": [74.85, 36.35, 74.95, 36.45],
        "lat": 36.4,
        "lon": 74.9,
        "recipients": ["+920000000002"],
    },
}


def get_region(region_id: str) -> dict:
    if region_id not in REGIONS:
        raise KeyError(f"Unknown region_id: {region_id}")
    return REGIONS[region_id]

"""
Evacuation route lookup.

Demo data only -- for a real deployment this should come from a maintained
database populated with NDMA/PDMA-verified routes, not hard-coded constants.
"""

EVACUATION_MAP = {
    "shishper_lake": {
        "village": "Hussainabad",
        "lat": 36.2,
        "lon": 74.6,
        "route": "Head east on KKH toward higher ground near Hussainabad.",
    },
    "passu_lake": {
        "village": "Passu",
        "lat": 36.4,
        "lon": 74.9,
        "route": "Move to higher ground away from the Passu glacier snout.",
    },
}


def get_evacuation_route(region_id: str) -> dict:
    return EVACUATION_MAP.get(region_id, {})

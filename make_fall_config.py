# -*- coding: utf-8 -*-
"""Generate fall-config.json: 10/25-11/30 开始、≥7 晚、无狗，湾区 90km。"""
import json, base64, os


def make_url(page):
    q = {
        "filters": {
            "activeMembership": True,
            "assignments": {
                "dateFrom": "2026-10-25",
                "dateTo": "2026-11-30",
                "reviewing": False,
                "confirmed": False,
                "durationInDays": {"minimum": 7},
            },
            "pets": [{"type": "dog", "exclude": True}],
            "sortBy": ["start_date"],
            "geoPoint": {"latitude": 37.77493, "longitude": -122.41942, "distance": "90km"},
        },
        "facets": [],
        "sort": [{"published": "desc"}],
        "page": page,
        "resultsPerPage": 24,
        "debug": False,
        "stats": [],
    }
    b64 = base64.b64encode(json.dumps(q).encode()).decode()
    return f"https://www.trustedhousesitters.com/house-and-pet-sitting-assignments/united-states/california/san-francisco/?q={b64}"


cfg = {
    "urls": [make_url(p) for p in (1, 2, 3)],
    "pages": 1,
    "center": {"lat": 37.77493, "lon": -122.41942},
    "radius_km": 90,
    "max_applications": 4,
    "max_alerts_per_run": 20,
    "start_windows": [
        {"from": "2026-10-25", "to": "2026-11-30", "min_nights": 7,
         "note": "10/25 Berkeley sit 结束后的下一段：10/25-11/30 开始、≥7 晚、无狗、湾区 90km"}
    ],
    "exclude_species": ["dog"],
}
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fall-config.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=1)
print("written", path)

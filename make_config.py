# -*- coding: utf-8 -*-
import json, base64

def make_url(page):
    q = {
        "filters": {
            "activeMembership": True,
            "assignments": {
                "dateFrom": "2026-09-13",
                "dateTo": "2026-09-20",
                "reviewing": False,
                "confirmed": False,
            },
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
        {"from": "2026-09-13", "to": "2026-09-20", "end_by": "2026-09-20", "min_nights": 0,
         "note": "9/13-9/20 gap housing window。不限宠物、不限天数。湾区 90km，按开始日排序，3页每轮。"}
    ],
    "exclude_species": [],
}

import os
here = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(here, "config.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=1)
print("written", path)

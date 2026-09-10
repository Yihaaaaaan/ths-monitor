# -*- coding: utf-8 -*-
"""Generate gap-config.json: 纯猫 sit，9/13-9/20，不限天数，湾区 90km。"""
import json, base64, os

NON_CAT = ["dog", "reptile", "horse", "fish", "bird", "poultry",
           "farm animal", "small pet"]


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
            "pets": [{"type": t, "exclude": True} for t in NON_CAT]
                    + [{"type": "cat", "exclude": False}],
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
    "urls": [make_url(p) for p in (1, 2)],
    "pages": 1,
    "center": {"lat": 37.77493, "lon": -122.41942},
    "radius_km": 90,
    "max_applications": 4,
    "max_alerts_per_run": 20,
    "start_windows": [
        {"from": "2026-09-13", "to": "2026-09-20", "end_by": "2026-09-20", "min_nights": 0,
         "note": "9/13-9/20 gap 纯猫监控：服务端排除全部非猫物种 + 本地 exclude_species 双保险，不限天数"}
    ],
    "exclude_species": NON_CAT,
}
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gap-config.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=1)
print("written", path)

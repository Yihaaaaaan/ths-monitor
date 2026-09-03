# -*- coding: utf-8 -*-
import json, base64

def make_url(page):
    q = {
        "filters": {
            "activeMembership": True,
            "assignments": {
                "dateFrom": "2026-09-12",
                "dateTo": "2026-10-06",
                "reviewing": False,
                "confirmed": False,
                "durationInDays": {"minimum": 4},
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
        {"from": "2026-09-12", "to": "2026-10-04", "end_by": "2026-10-06", "min_nights": 4,
         "note": "9/13-10/5 空窗。q= 搜索端点（湾区 90km、≥4 晚、按开始日排序），3 页每轮。改参数：改本文件重跑生成 config，再同步 ths-monitor repo"}
    ],
    "exclude_species": [],
}
path = r"d:\02 Projects\08 Personal OS\Personal-OS-v1.0\scripts\ths-monitor\config.json"
with open(path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=1)
print("written", path)

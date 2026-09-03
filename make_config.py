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
                "durationInDays": {"minimum": 3},
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
        {"from": "2026-09-12", "to": "2026-10-04", "end_by": "2026-10-06", "min_nights": 3,
         "note": "9/13-10/5 空窗。q= 搜索端点（湾区 90km、≥3 天、按开始日排序），3 页每轮。窗口过后改回城市页模式或更新 q 里的日期（q 是 base64 JSON，scripts/ths-monitor 下 make_config.py 思路重生成）"}
    ],
}
path = r"d:\02 Projects\08 Personal OS\Personal-OS-v1.0\scripts\ths-monitor\config.json"
with open(path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=1)
print("written", path)

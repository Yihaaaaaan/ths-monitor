# -*- coding: utf-8 -*-
"""TrustedHousesitters new-sit monitor.

Polls public search pages (no login, no cookies — account is never touched),
extracts embedded listing state, and pushes Telegram alerts for new open
assignments that still have application slots (< 5 applicants).

Safety design:
- Anonymous requests to robots.txt-allowed pages only
- Serial fetching, random jitter, browser User-Agent
- Exponential backoff on failures; never hammers on errors
- Discovery only — applying is always done manually by a human

Usage:
  python monitor.py --once --dry-run   # test: print alerts, no telegram, no state write
  python monitor.py --once             # single run (for Task Scheduler)
"""

import argparse
import json
import math
import os
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CONFIG_PATH = os.path.join(HERE, "config.json")
STATE_PATH = os.path.join(HERE, "state.json")
LOG_PATH = os.path.join(HERE, "monitor.log")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def log(msg):
    line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line)
    try:
        if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > 500_000:
            os.replace(LOG_PATH, LOG_PATH + ".old")
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def read_env():
    env = {}
    try:
        with open(os.path.join(ROOT, ".env"), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    except OSError:
        pass
    # real environment variables win (CI: GitHub Actions secrets)
    for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


def haversine_km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = (0.5 - math.cos((lat2 - lat1) * p) / 2
         + math.cos(lat1 * p) * math.cos(lat2 * p)
         * (1 - math.cos((lon2 - lon1) * p)) / 2)
    return 12742 * math.asin(math.sqrt(a))


LISTING_RE = re.compile(r'"(\d+)":\{"id":"\1","title":"')
ASSIGN_RE = re.compile(r'\{"id":"(\d+)","startDate":"([\d-]+)","endDate":"([\d-]+)"')


def parse_listings(html):
    """Extract listings from the embedded page state."""
    listings = []
    matches = list(LISTING_RE.finditer(html))
    for i, m in enumerate(matches):
        lid = m.group(1)
        end = matches[i + 1].start() if i + 1 < len(matches) else m.start() + 30_000
        seg = html[m.start():end]

        tm = re.search(r'"title":"((?:[^"\\]|\\.)*)"', seg)
        title = tm.group(1).replace('\\"', '"') if tm else "?"
        loc = re.search(r'"location":\{"name":"([^"]+)"', seg)
        coords = re.search(r'"coordinates":\{"lat":(-?[\d.]+),"lon":(-?[\d.]+)', seg)
        animals = list(dict.fromkeys(
            re.findall(r'\{"name":"([a-z ]+)","slug":"[a-z-]+","count":(\d+)\}', seg)))

        assigns = []
        amatches = list(ASSIGN_RE.finditer(seg))
        for j, am in enumerate(amatches):
            a_end = amatches[j + 1].start() if j + 1 < len(amatches) else len(seg)
            a_seg = seg[am.start():a_end]
            ac = re.search(r'"applicationsCount":(\d+)', a_seg)
            confirmed = '"isConfirmed":true' in a_seg
            assigns.append({
                "id": am.group(1),
                "start": am.group(2),
                "end": am.group(3),
                "apps": int(ac.group(1)) if ac else None,
                "confirmed": confirmed,
            })

        listings.append({
            "id": lid,
            "title": title,
            "location": loc.group(1) if loc else "?",
            "lat": float(coords.group(1)) if coords else None,
            "lon": float(coords.group(2)) if coords else None,
            "animals": ", ".join(f"{n}x{c}" for n, c in animals),
            "assignments": assigns,
        })
    return listings


def telegram_send(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": "true",
    }).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def run_once(dry_run=False):
    cfg = load_json(CONFIG_PATH, {})
    state = load_json(STATE_PATH, {"seen": {}, "failures": 0, "last_attempt": 0})
    env = read_env()
    token = env.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = env.get("TELEGRAM_CHAT_ID", "")

    # backoff: after 3 consecutive failures only retry every 30+ min
    now = time.time()
    if state.get("failures", 0) >= 3 and now - state.get("last_attempt", 0) < 1800:
        log(f"backoff active ({state['failures']} failures), skipping run")
        return
    state["last_attempt"] = now

    center = cfg.get("center", {"lat": 37.77493, "lon": -122.41942})
    radius = cfg.get("radius_km", 60)
    max_apps = cfg.get("max_applications", 4)
    urls = cfg.get("urls", [])

    today = date.today().isoformat()
    alerts = []
    any_success = False

    for i, url in enumerate(urls):
        if i > 0:
            time.sleep(random.uniform(5, 15))
        try:
            html = fetch(url)
            any_success = True
        except Exception as e:
            log(f"fetch failed {url}: {e}")
            continue

        listings = parse_listings(html)
        log(f"{url} -> {len(listings)} listings")

        for lst in listings:
            if lst["lat"] is not None:
                d = haversine_km(center["lat"], center["lon"], lst["lat"], lst["lon"])
                if d > radius:
                    continue
            for a in lst["assignments"]:
                key = a["id"]
                if key in state["seen"]:
                    continue
                state["seen"][key] = {"first_seen": today, "start": a["start"]}
                if a["confirmed"]:
                    continue
                if a["start"] < today:
                    continue
                if a["apps"] is None or a["apps"] > max_apps:
                    continue
                alerts.append(
                    f"🏠 {lst['location']} | {a['start']} → {a['end']}\n"
                    f"{lst['title'][:80]}\n"
                    f"🐾 {lst['animals'] or '?'} | 已申请 {a['apps']}/5\n"
                    f"https://www.trustedhousesitters.com/house-and-pet-sitting-assignments/l/{lst['id']}/"
                )

    # prune assignments whose start date has passed
    state["seen"] = {k: v for k, v in state["seen"].items()
                     if v.get("start", "9999") >= today}
    state["failures"] = 0 if any_success else state.get("failures", 0) + 1

    first_run = not os.path.exists(STATE_PATH)
    if alerts:
        log(f"{len(alerts)} new open sit(s)")
        # first run would flood with every existing listing — record silently
        if dry_run:
            for a in alerts:
                print("\n--- ALERT ---\n" + a)
        elif first_run:
            log("first run: seeding state, not sending alerts")
        elif not token:
            for a in alerts:
                print("\n--- ALERT ---\n" + a)
            if not token and not dry_run:
                log("no TELEGRAM_BOT_TOKEN in .env — printed only")
        else:
            for a in alerts[:8]:
                try:
                    telegram_send(token, chat_id, a)
                except Exception as e:
                    log(f"telegram send failed: {e}")
    else:
        log("no new open sits")

    if not dry_run:
        save_json(STATE_PATH, state)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--scheduled", action="store_true",
                    help="add random start jitter (for Task Scheduler)")
    args = ap.parse_args()

    if args.scheduled:
        time.sleep(random.uniform(0, 45))
    run_once(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()

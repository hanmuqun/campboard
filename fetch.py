"""
campboard / fetch.py

Pulls campsite availability from Recreation.gov's public JSON API and writes a
compact snapshot to data/snapshot.json.

Design notes
------------
* One request returns one campground's whole month (~500 KB of JSON). We throw
  the raw payload away immediately and keep only per-day status counts.
* Recreation.gov rate-limits hard. A burst of ~130 requests got us HTTP 429, so
  requests are paced, cached on disk, and 429 is treated as "back off, retry".
* Cache lives in data/cache/<facility_id>/<month>.json and is reused while it is
  younger than --ttl minutes, so a cron can run often without re-fetching all.

Usage:
    python fetch.py                 # curated campgrounds, current + next month
    python fetch.py --limit 5       # smoke test
    python fetch.py --no-cache      # force a full refetch
"""

import argparse
import json
import random
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path

import changelog

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CACHE = DATA / "cache"
CANDIDATES = DATA / "candidates.json"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

API = "https://www.recreation.gov/api/camps/availability/campground/{fid}/month?start_date={start}"

STATUS = {"Available": "available", "Reserved": "reserved", "Closed": "closed", "NYR": "nyr"}

PARKS = {
    "Yosemite National Park": [
        "upper pines", "lower pines", "north pines", "tuolumne meadows", "wawona",
        "crane flat", "hodgdon meadow", "bridalveil creek", "tamarack flat",
        "porcupine flat", "yosemite creek", "white wolf", "camp 4",
    ],
    "Zion National Park": ["watchman", "south campground"],
    "Grand Canyon National Park": ["mather", "desert view", "north rim"],
    "Arches National Park": ["devils garden"],
    "Bryce Canyon National Park": ["north campground", "sunset campground"],
    "Canyonlands National Park": ["needles"],
    "Capitol Reef National Park": ["fruita"],
    "Great Smoky Mountains National Park": ["elkmont", "cades cove", "smokemont", "cosby"],
    "Shenandoah National Park": ["big meadows", "loft mountain", "mathews arm"],
    "Joshua Tree National Park": ["jumbo rocks", "indian cove", "black rock", "cottonwood"],
    "Sequoia National Park": ["lodgepole", "dorst creek"],
    "Olympic National Park": ["kalaloch", "hoh rainforest", "sol duc", "fairholme", "staircase"],
    "Mount Rainier National Park": ["cougar rock", "ohanapecosh", "white river"],
    "Yellowstone National Park": [
        "mammoth", "lewis lake", "slough creek", "tower fall", "indian creek",
        "colter bay", "jenny lake", "signal mountain", "headwaters",
    ],
    "Death Valley National Park": ["furnace creek"],
    "Big Sur": ["kirk creek"],
    "Lake Tahoe": ["fallen leaf", "zephyr cove"],
}

DENY = ("group", "equestrian", "marina", "picnic", "day use", "cabin", "horse",
        "backcountry", "rv park", "rv &")


def fetch_availability(fid, month, delay=0.35, backoff=25):
    """Return {'YYYY-MM-DD': {available, reserved, closed, nyr}} for one month."""
    url = API.format(fid=fid, start=f"{month}-01T00%3A00%3A00.000Z")
    last = None
    for attempt in range(3):
        time.sleep(delay + random.uniform(0, 0.25))
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as r:
                payload = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 429:
                time.sleep(backoff * (attempt + 1))
                continue
            raise
        except Exception as e:  # noqa: BLE001 - transient network
            last = e
            time.sleep(3 * (attempt + 1))
            continue

        days = {}
        for site in (payload.get("campsites") or {}).values():
            for stamp, status in (site.get("availabilities") or {}).items():
                d = stamp[:10]
                row = days.setdefault(d, {"available": 0, "reserved": 0, "closed": 0, "nyr": 0})
                row[STATUS.get(status, "nyr")] += 1
        return days
    raise last


def load_month(fid, month, ttl_min, no_cache=False):
    path = CACHE / str(fid) / f"{month}.json"
    if not no_cache and path.exists():
        age = (time.time() - path.stat().st_mtime) / 60
        if age <= ttl_min:
            return json.loads(path.read_text(encoding="utf-8")), "cache"
    try:
        days = fetch_availability(fid, month)
    except Exception as e:  # noqa: BLE001
        print(f"  !! {fid} {month}: {e}")
        return None, "error"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(days, separators=(",", ":")), encoding="utf-8")
    return days, "net"


def months_to_cover(today, span=2):
    out, y, m = [], today.year, today.month
    for _ in range(span):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def select_campgrounds():
    if not CANDIDATES.exists():
        raise SystemExit("data/candidates.json missing - run discover.py first")
    cands = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    picked, seen = [], set()
    for park, patterns in PARKS.items():
        for c in cands.values():
            if c.get("query") != park or c["id"] in seen:
                continue
            name = (c.get("name") or "").lower()
            if any(d in name for d in DENY):
                continue
            if any(p in name for p in patterns):
                seen.add(c["id"])
                picked.append({**c, "park": park})
    return picked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--span", type=int, default=2, help="months to cover")
    ap.add_argument("--ttl", type=float, default=20.0, help="cache lifetime, minutes")
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()

    months = months_to_cover(date.today(), args.span)
    picks = select_campgrounds()
    if args.limit:
        picks = picks[: args.limit]
    print(f"covering {len(picks)} campgrounds x {len(months)} months")

    jobs = [(c, m) for c in picks for m in months]
    started = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        outcomes = list(ex.map(lambda j: load_month(j[0]["id"], j[1], args.ttl, args.no_cache), jobs))

    per_month = {}
    for (camp, month), (days, src) in zip(jobs, outcomes):
        if days:
            per_month.setdefault(camp["id"], {})[month] = days

    campgrounds, empty = [], 0
    for camp in picks:
        merged = {}
        for month_days in per_month.get(camp["id"], {}).values():
            merged.update(month_days)
        if not merged:
            empty += 1
            continue
        for row in merged.values():
            row["total"] = row["available"] + row["reserved"] + row["closed"] + row["nyr"]
        campgrounds.append({
            "id": camp["id"],
            "name": camp["name"],
            "park": camp["park"],
            "city": camp.get("city"),
            "state": camp.get("state"),
            "url": f"https://www.recreation.gov/camping/campgrounds/{camp['id']}",
            "sites": camp.get("sites"),
            "days": merged,
        })

    campgrounds.sort(key=lambda c: (c["park"], c["name"]))
    snapshot = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "months": months,
        "campgrounds": campgrounds,
    }
    DATA.mkdir(exist_ok=True)
    out = DATA / "snapshot.json"
    previous = None
    if out.exists():
        try:
            previous = json.loads(out.read_text(encoding="utf-8"))
        except ValueError:
            previous = None
    out.write_text(json.dumps(snapshot, separators=(",", ":")), encoding="utf-8")

    events = changelog.record(previous, snapshot)

    net = sum(1 for _, src in outcomes if src == "net")
    moved = [e for e in events if e["kind"] in ("opened", "released")]
    print(f"kept {len(campgrounds)} campgrounds ({empty} had no data); "
          f"{net} network fetches, {len(outcomes) - net} from cache; "
          f"{time.time() - started:.1f}s -> {out} ({out.stat().st_size / 1024:.0f} KB)")
    print(f"{len(events)} change events ({len(moved)} new openings) -> {changelog.JSONL}")


if __name__ == "__main__":
    main()

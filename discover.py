"""
campboard / discover.py

Finds the campgrounds worth tracking and ranks them by how many people have
rated them on Recreation.gov -- review volume is the closest public proxy for
"how hard this is to book", which is the only thing this board is for.

The old version used a hand-written list of campground names, so the board was
frozen at whatever was popular the day I wrote it. This one re-ranks from live
data, so it can be refreshed on a schedule.

Writes data/ranking.json:

    {"generated": "...", "pool": {...}, "ranking": [
        {"id", "name", "park", "state", "sites", "ratings", "rating"}, ...]}

Usage:
    python discover.py                # re-rank, keep top 40
    python discover.py --top 60
"""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
SEARCH = "https://www.recreation.gov/api/search?q={q}&size=100&start=0"

# Parks we look in. Popularity is ranked *within* this pool, so the pool has to
# cover the parks people actually try to book. Cheap to extend.
PARKS = [
    "Yosemite National Park", "Zion National Park", "Grand Canyon National Park",
    "Arches National Park", "Bryce Canyon National Park", "Canyonlands National Park",
    "Capitol Reef National Park", "Great Smoky Mountains National Park",
    "Shenandoah National Park", "Joshua Tree National Park", "Sequoia National Park",
    "Olympic National Park", "Mount Rainier National Park", "Yellowstone National Park",
    "Death Valley National Park", "Grand Teton National Park", "Glacier National Park",
    "Acadia National Park", "Rocky Mountain National Park", "Crater Lake National Park",
    "Badlands National Park", "Everglades National Park", "Theodore Roosevelt National Park",
    "Big Bend National Park", "Guadalupe Mountains National Park", "Mesa Verde National Park",
    "Black Canyon of the Gunnison National Park", "Great Sand Dunes National Park",
    "Lassen Volcanic National Park", "Pinnacles National Park", "Channel Islands National Park",
    "Virgin Islands National Park", "Mammoth Cave National Park", "Wind Cave National Park",
]

DENY = ("group", "equestrian", "marina", "picnic", "day use", "cabin", "horse",
        "backcountry", "rv park", "rv &", "permit", "tour")


def search(query, delay=0.4):
    url = SEARCH.format(q=urllib.parse.quote(query))
    for attempt in range(3):
        time.sleep(delay)
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            if attempt == 2:
                print(f"  !! {query}: {e}")
                return None
            time.sleep(4 * (attempt + 1))
    return None


def as_int(v, default=0):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--min-sites", type=int, default=10)
    args = ap.parse_args()

    pool = {}
    for park in PARKS:
        data = search(park)
        if not data:
            continue
        results = data.get("results") or []

        # A search for "Yosemite National Park" also returns campgrounds in
        # neighbouring national forests, so pin the park first and only keep
        # campgrounds that actually belong to it.
        park_id = None
        for r in results:
            if r.get("entity_type") == "recarea" and \
                    (r.get("name") or "").strip().lower() == park.lower():
                park_id = str(r.get("entity_id") or "")
                break
        if not park_id:
            print(f"  {park:45s} no recarea match, skipped")
            continue

        kept = 0
        for r in results:
            if r.get("entity_type") != "campground":
                continue
            if str(r.get("parent_id") or "") != park_id:
                continue
            name = (r.get("name") or "").strip()
            low = name.lower()
            if any(d in low for d in DENY):
                continue
            if not r.get("reservable", True):
                continue
            sites = as_int(r.get("campsites_count"))
            if sites < args.min_sites:
                continue
            fid = str(r.get("entity_id") or "")
            if not fid:
                continue
            pool[fid] = {
                "id": fid,
                "name": name,
                "park": r.get("parent_name") or park,
                "state": r.get("state_code"),
                "sites": sites,
                "ratings": as_int(r.get("number_of_ratings")),
                "rating": round(float(r.get("average_rating") or 0), 2),
            }
            kept += 1
        print(f"  {park:45s} {kept:3d} campgrounds")

    ranked = sorted(
        pool.values(),
        key=lambda c: (c["ratings"], c["sites"]),
        reverse=True,
    )[: args.top]

    DATA.mkdir(exist_ok=True)
    out = DATA / "ranking.json"
    out.write_text(json.dumps({
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pool": {"queries": len(PARKS), "campgrounds": len(pool)},
        "ranking": ranked,
    }, indent=1), encoding="utf-8")

    print(f"\n{len(pool)} campgrounds in pool -> kept top {len(ranked)} -> {out}")
    for i, c in enumerate(ranked[:23], 1):
        print(f"  {i:2d}. {c['name'][:40]:40s} {c['park'][:32]:32s} "
              f"ratings={c['ratings']:5d} sites={c['sites']}")


if __name__ == "__main__":
    main()

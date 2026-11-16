"""Throwaway check: does the diff produce the right events, and does the page render?"""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import build
import changelog

DAY = {"available": 0, "reserved": 0, "closed": 146, "nyr": 0, "total": 146}


def camp(rows):
    days = {}
    for d, (a, r) in rows.items():
        days[d] = {**DAY, "available": a, "reserved": r,
                   "closed": 146 - a - r, "total": 146}
    return {"id": 1, "name": "Upper Pines Campground", "park": "Yosemite National Park",
            "city": "Yosemite", "state": "CA", "sites": 235, "days": days}


old = {"generated": "2026-11-16T06:00:00+00:00", "campgrounds": [camp({
    "2026-11-20": (0, 89),    # bookable, sold out
    "2026-11-21": (0, 0),     # season closed
    "2026-11-22": (10, 20),   # some free
    "2026-11-23": (5, 0),     # all free
})]}
new = {"generated": "2026-11-16T07:00:00+00:00", "campgrounds": [camp({
    "2026-11-20": (4, 85),    # 4 freed up   -> opened
    "2026-11-21": (6, 0),     # season opened  -> released
    "2026-11-22": (3, 27),    # 7 taken        -> taken
    "2026-11-23": (0, 0),     # closed         -> season_closed
})]}

events = changelog.diff_snapshots(old, new, new["generated"])
got = [(e["date"], e["kind"], e["after"]) for e in events]
want = [
    ("2026-11-20", "opened", 4),
    ("2026-11-21", "released", 6),
    ("2026-11-22", "taken", 3),
    ("2026-11-23", "season_closed", 0),
]
print("events:", got)
assert got == want, f"expected {want}"

# a second run with identical data must be silent
assert changelog.diff_snapshots(new, new, "x") == [], "idempotency broken"

# one site coming and going on a big campground is noise, not news
quiet_old = {"generated": "a", "campgrounds": [camp({"2026-12-18": (65, 10)})]}
quiet_new = {"generated": "b", "campgrounds": [camp({"2026-12-18": (64, 11)})]}
assert changelog.diff_snapshots(quiet_old, quiet_new, "b") == [], "noise not filtered"

# render the page with these events, outside site/ so nothing ships
for e in events:
    e.update(id=1, name="Upper Pines Campground", park="Yosemite National Park")
html = build.render_changes(events, "2026-11-16 07:00:00")
out = Path(__file__).resolve().parent / "_preview-changes.html"
out.write_text(html, encoding="utf-8")
print("ok ->", out, len(html), "bytes")

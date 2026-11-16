"""
campboard / changelog.py

Compares the previous snapshot with the new one and records what actually moved:
a night that had zero free sites and now has some, a campground that just opened
for the season, a weekend that just sold out.

This is the one thing the big trackers do not publish for free, and it only
costs us one comparison per run. The log is append-only:

    data/changes.jsonl   one JSON object per event, never rewritten
    data/changes.json    the newest N events, for the site to render
"""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
JSONL = DATA / "changes.jsonl"
LATEST = DATA / "changes.json"
KEEP = 400
MIN_JUMP = 5  # single sites coming and going is noise; only log real swings


def bookable(row):
    return (row or {}).get("available", 0) + (row or {}).get("reserved", 0)


def diff_snapshots(old, new, ts):
    """Return the list of events between two snapshots."""
    if not old:
        return []
    old_map = {c["id"]: c for c in old.get("campgrounds", [])}
    events = []

    for camp in new.get("campgrounds", []):
        prev = old_map.get(camp["id"])
        if not prev:
            continue  # first time we see this campground; nothing to compare
        for day, row in camp["days"].items():
            before = prev["days"].get(day)
            if not before:
                continue
            pb, nb = bookable(before), bookable(row)
            base = {
                "ts": ts, "id": camp["id"], "name": camp["name"],
                "park": camp["park"], "date": day,
            }
            if pb == 0 and nb > 0:
                events.append({**base, "kind": "released",
                               "before": 0, "after": row["available"]})
            elif nb == 0 and pb > 0:
                events.append({**base, "kind": "season_closed",
                               "before": before["available"], "after": 0})
            elif before["available"] == 0 and row["available"] > 0:
                # a night that had nothing came back
                events.append({**base, "kind": "opened",
                               "before": 0, "after": row["available"],
                               "delta": row["available"]})
            elif before["available"] > 0 and row["available"] == 0:
                # a night that had room sold out
                events.append({**base, "kind": "sold_out",
                               "before": before["available"], "after": 0,
                               "delta": -before["available"]})
            elif abs(row["available"] - before["available"]) >= MIN_JUMP:
                delta = row["available"] - before["available"]
                events.append({**base,
                               "kind": "opened" if delta > 0 else "taken",
                               "before": before["available"],
                               "after": row["available"],
                               "delta": delta})
    return events


def record(old, new):
    ts = new["generated"]
    events = diff_snapshots(old, new, ts)
    DATA.mkdir(exist_ok=True)

    if events:
        with JSONL.open("a", encoding="utf-8") as fh:
            for e in events:
                fh.write(json.dumps(e, ensure_ascii=False) + "\n")

    recent = []
    if JSONL.exists():
        lines = JSONL.read_text(encoding="utf-8").splitlines()
        for line in lines[-KEEP:]:
            try:
                recent.append(json.loads(line))
            except ValueError:
                continue
    recent.reverse()
    LATEST.write_text(json.dumps(recent, ensure_ascii=False, separators=(",", ":")),
                      encoding="utf-8")
    return events

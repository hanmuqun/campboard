"""Probe: how often does the availability endpoint fail for the campgrounds we track?"""
import json
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
API = "https://www.recreation.gov/api/camps/availability/campground/{fid}/month?start_date={start}"


def months(today, span=2):
    out, y, m = [], today.year, today.month
    for _ in range(span):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def main():
    snap = json.loads((ROOT / "data" / "snapshot.json").read_text(encoding="utf-8"))
    ids = [(c["id"], c["name"]) for c in snap["campgrounds"]]
    print(f"probing {len(ids)} campgrounds x 2 months")
    bad = 0
    for fid, name in ids:
        for month in months(date.today()):
            url = API.format(fid=fid, start=f"{month}-01T00%3A00%3A00.000Z")
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": UA, "Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=45) as r:
                    payload = json.loads(r.read().decode("utf-8"))
                sites = payload.get("campsites") or {}
                days = len({s[:10] for site in sites.values()
                            for s in (site.get("availabilities") or {})})
                if not sites:
                    print(f"  EMPTY  {name[:38]:38s} {month}  campsites=0")
            except urllib.error.HTTPError as e:
                bad += 1
                print(f"  HTTP {e.code} {name[:38]:38s} {month}")
            except Exception as e:  # noqa: BLE001
                bad += 1
                print(f"  FAIL   {name[:38]:38s} {month}  {type(e).__name__}: {e}")
    print(f"\n{bad} failures out of {len(ids) * 2} requests")


if __name__ == "__main__":
    main()

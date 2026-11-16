"""Discover campgrounds for a list of park queries; print a curation table."""
import json
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

QUERIES = [
    "Yosemite National Park", "Zion National Park", "Grand Canyon National Park",
    "Yellowstone National Park", "Arches National Park", "Bryce Canyon National Park",
    "Glacier National Park", "Rocky Mountain National Park", "Acadia National Park",
    "Joshua Tree National Park", "Sequoia National Park", "Olympic National Park",
    "Great Smoky Mountains National Park", "Shenandoah National Park",
    "Mount Rainier National Park", "Death Valley National Park",
    "Canyonlands National Park", "Capitol Reef National Park",
    "Big Sur", "Lake Tahoe",
]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))


def search(q):
    url = ("https://www.recreation.gov/api/search?q=" + urllib.parse.quote(q) + "&size=100&start=0")
    try:
        return get(url).get("results") or []
    except Exception as e:
        print(f"  !! search failed {q}: {e}")
        return []


def main():
    found = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        for q, res in zip(QUERIES, ex.map(search, QUERIES)):
            n = 0
            for r in res:
                if r.get("entity_type") != "campground":
                    continue
                fid = str(r.get("entity_id"))
                if fid in found:
                    continue
                found[fid] = {
                    "id": fid,
                    "name": r.get("name"),
                    "city": r.get("city"),
                    "state": r.get("state_code"),
                    "sites": r.get("campsites_count"),
                    "reservable": r.get("reservable"),
                    "query": q,
                }
                n += 1
            print(f"{q:42s} results={len(res):3d} new_campgrounds={n}")

    print()
    print(f"TOTAL unique campgrounds: {len(found)}")
    print()
    hdr = f"{'id':>10}  {'sites':>5}  {'state':<14} {'name'}"
    print(hdr)
    print("-" * len(hdr))
    for c in sorted(found.values(), key=lambda x: (x["state"] or "", x["name"] or "")):
        print(f"{c['id']:>10}  {str(c['sites']):>5}  {(c['state'] or '')[:14]:<14} {c['name']}")

    with open(r"D:\SaaS开发\projects\campboard\data\candidates.json", "w", encoding="utf-8") as f:
        json.dump(found, f, indent=1, ensure_ascii=False)
    print()
    print("wrote data/candidates.json")


if __name__ == "__main__":
    main()

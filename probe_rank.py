"""Probe: what does Recreation.gov's search API expose for ranking/popularity?"""
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


def main():
    # 1. Does search accept a sort parameter, and what does the default rank look like?
    for q in ["campground", "yosemite", "national park camping"]:
        try:
            st, data = get(f"https://www.recreation.gov/api/search?q={urllib.parse.quote(q)}&size=8&start=0")
            print(f"\n=== q={q!r} HTTP {st} ===")
            print("top-level keys:", sorted(data.keys()))
            print("total:", data.get("total"))
            for i, r in enumerate(data.get("results", [])[:8]):
                print(f"  {i}: {r.get('entity_type'):12s} {str(r.get('name'))[:45]:45s} "
                      f"sites={(r.get('campsites_count'))} rating={r.get('rating')} "
                      f"reviews={r.get('num_reviews')} score={r.get('score')}")
        except Exception as e:  # noqa: BLE001
            print(f"q={q!r} FAILED: {e}")

    # 2. Full field list of one campground entity, to find any popularity signal.
    st, data = get("https://www.recreation.gov/api/search?q=yosemite&size=100&start=0")
    camps = [r for r in data["results"] if r.get("entity_type") == "campground"]
    if camps:
        one = camps[0]
        print("\n=== all fields of one campground entity ===")
        for k, v in sorted(one.items()):
            s = json.dumps(v, ensure_ascii=False)
            print(f"  {k:28s} {s[:110]}")

    # 3. Metadata endpoint: does it carry reviews/rating/popularity?
    if camps:
        fid = camps[0]["entity_id"]
        st, meta = get(f"https://www.recreation.gov/api/camps/campgrounds/{fid}")
        print(f"\n=== metadata {fid} HTTP {st}, keys={len(meta)} ===")
        for k, v in sorted(meta.items()):
            s = json.dumps(v, ensure_ascii=False)
            if any(t in k.lower() for t in ("review", "rating", "popular", "visit", "score", "rank", "stat")):
                print(f"  HIT {k:26s} {s[:120]}")
        print("  all keys:", ", ".join(sorted(meta.keys()))[:600])


if __name__ == "__main__":
    main()

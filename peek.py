import json
import sys
from datetime import date

sys.stdout.reconfigure(encoding="utf-8")

s = json.load(open("data/snapshot.json", encoding="utf-8"))
today = str(date.today())
print("generated", s["generated"], "months", s["months"], "n", len(s["campgrounds"]))
print()
hdr = f"{'id':>10} {'park':<32} {'name':<34} {'days':>4} {'next7':>6} {'all':>6}"
print(hdr)
print("-" * len(hdr))
for c in s["campgrounds"]:
    d = c["days"]
    nxt = sum(v["available"] for k, v in d.items() if today <= k <= "2026-11-22")
    print(f"{c['id']:>10} {c['park'][:32]:<32} {c['name'][:34]:<34} "
          f"{len(d):>4} {nxt:>6} {sum(v['available'] for v in d.values()):>6}")

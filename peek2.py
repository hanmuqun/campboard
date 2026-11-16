import json,sys
sys.stdout.reconfigure(encoding="utf-8")
s=json.load(open("data/snapshot.json",encoding="utf-8"))
for c in s["campgrounds"][:6]:
    n=sum(1 for d,r in c["days"].items() if r.get("unreleased"))
    print(f'{c["name"][:34]:34s} windowEnd={c["windowEnd"]} relDay={c["releaseDay"]} unreleasedDays={n}')

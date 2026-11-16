import json,sys,urllib.request
sys.stdout.reconfigure(encoding="utf-8")
UA={"User-Agent":"Mozilla/5.0","Accept":"application/json"}
for fid in ["232447","10083840"]:
    req=urllib.request.Request(f"https://www.recreation.gov/api/camps/campgrounds/{fid}",headers=UA)
    d=json.loads(urllib.request.urlopen(req,timeout=30).read().decode())["campground"]
    print(f"=== {fid} {d.get('facility_name','')[:35]} tz={d.get('time_zone')} season={d.get('season_start')}..{d.get('season_end')}")
    for k,v in d.get("facility_rules",{}).items():
        print(f"   {k:30s} value={v.get('value')!r} units={v.get('units')!r}")

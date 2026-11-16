"""
campboard / build.py

Turns data/snapshot.json into a static site under site/.

    site/index.html                  the board
    site/campground/<id>.html        one page per campground (the SEO surface)
    site/data.json                   the same data, free to consume
    site/sitemap.xml, site/robots.txt

No framework, no build step, no client-side JS. Everything renders from the
snapshot so the pages are pure static HTML.
"""

import html
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SITE = ROOT / "site"
SITE_URL = "https://campboard.example"

CSS = """
:root{--ink:#14181f;--muted:#6b7280;--line:#e5e7eb;--bg:#ffffff;--soft:#f8fafc;
--red:#fecaca;--amber:#fde68a;--green:#bbf7d0;--grey:#e5e7eb;--dark:#0f1115}
*{box-sizing:border-box}
body{margin:0;font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
color:var(--ink);background:var(--bg);-webkit-font-smoothing:antialiased}
.wrap{max-width:1040px;margin:0 auto;padding:0 20px}
header{background:var(--dark);color:#fff;padding:28px 0 26px}
header .wrap{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
header h1{margin:0;font-size:21px;letter-spacing:-.01em}
header h1 a{color:#fff;text-decoration:none}
header p{margin:0;color:#9aa4b2;font-size:13px}
main{padding:28px 0 64px}
h2{font-size:15px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);
font-weight:600;margin:34px 0 10px}
p.lede{font-size:18px;line-height:1.5;margin:0 0 6px;max-width:60ch}
p.sub{color:var(--muted);font-size:14px;margin:0 0 26px}
table{width:100%;border-collapse:collapse;font-size:15px}
th{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.06em;
color:var(--muted);font-weight:600;padding:0 10px 8px;border-bottom:1px solid var(--line)}
td{padding:11px 10px;border-bottom:1px solid var(--line);vertical-align:middle}
tr:hover td{background:var(--soft)}
.num{font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}
.camp a{color:var(--ink);text-decoration:none;font-weight:600}
.camp a:hover{text-decoration:underline}
.park{color:var(--muted);font-size:13px}
.pill{display:inline-block;padding:2px 9px;border-radius:99px;font-size:12px;font-weight:600}
.p-zero{background:var(--red);color:#7f1d1d}
.p-low{background:var(--amber);color:#78350f}
.p-ok{background:var(--green);color:#14532d}
.p-closed{background:var(--grey);color:#4b5563}
td .pill{min-width:44px;text-align:center}
.daygrid{display:grid;grid-template-columns:repeat(7,1fr);gap:5px;margin:6px 0 4px}
.day{padding:9px 4px;border-radius:6px;text-align:center;font-size:13px;
font-variant-numeric:tabular-nums;line-height:1.25}
.day .d{font-size:11px;color:#374151;opacity:.75}
.day .n{font-weight:600}
.day.gone{background:var(--grey);color:#6b7280}
.day.free0{background:var(--red);color:#7f1d1d}
.day.free1{background:var(--amber);color:#78350f}
.day.free2{background:var(--green);color:#14532d}
.legend{color:var(--muted);font-size:12px;margin:10px 0 0}
.legend span{display:inline-block;width:11px;height:11px;border-radius:3px;margin:0 5px -1px 12px}
.card{border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin:0 0 18px}
.card h3{margin:0 0 4px;font-size:17px}
.card .meta{color:var(--muted);font-size:13px;margin:0 0 12px}
a.btn{display:inline-block;margin-top:10px;background:var(--ink);color:#fff;text-decoration:none;
padding:9px 15px;border-radius:7px;font-size:14px;font-weight:600}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:12px;padding:22px 0 40px}
footer a{color:var(--muted)}
@media(max-width:640px){.hide-s{display:none}}
"""


def esc(s):
    return html.escape(str(s if s is not None else ""))


def slug(s):
    keep = [c.lower() if c.isalnum() else "-" for c in str(s)]
    out = "".join(keep)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")


def days_from(camp, start, n):
    out = []
    for i in range(n):
        d = (start + timedelta(days=i)).isoformat()
        out.append((d, camp["days"].get(d)))
    return out


def bookable(row):
    return row["available"] + row["reserved"] if row else 0


def ratio(row):
    b = bookable(row)
    return (row["available"] / b) if b else None


def pill_for(row):
    if not row or bookable(row) == 0:
        return '<span class="pill p-closed">closed</span>'
    n = row["available"]
    if n == 0:
        return '<span class="pill p-zero">0</span>'
    r = ratio(row)
    cls = "p-low" if r < 0.34 else "p-ok"
    return f'<span class="pill {cls}">{n}</span>'


def page(title, desc, body, canonical=""):
    can = f'\n<link rel="canonical" href="{esc(canonical)}">' if canonical else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">{can}
<style>{CSS}</style>
</head>
<body>
<header><div class="wrap">
<h1><a href="/">Campboard</a></h1>
<p>Campsite availability for US national parks &middot;
<a href="/changes.html" style="color:#fff">what just opened</a></p>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">
Not affiliated with Recreation.gov or the National Park Service. Availability is read from
public Recreation.gov data and may lag the real booking system by minutes. Book through the
official site. &middot; <a href="/data.json">data.json</a>
</div></footer>
</body>
</html>
"""


def load_changes():
    path = DATA / "changes.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return []


def when(ts):
    return ts[:16].replace("T", " ")


def n_sites(n):
    return f"{n} free site" + ("" if n == 1 else "s")


def change_line(e, show_camp=True):
    if e["kind"] == "released":
        what = f'went from closed to <b>{n_sites(e["after"])}</b>'
    elif e["kind"] == "season_closed":
        what = f'closed for the season (was {e["before"]} free)'
    elif e["kind"] == "sold_out":
        what = f'<b>sold out</b> (was {e["before"]} free)'
    elif e["kind"] == "taken":
        n = abs(e.get("delta", e["after"] - e["before"]))
        what = f'lost <b>{n}</b> free site{"" if n == 1 else "s"} &rarr; {e["after"]} left'
    else:
        n = e.get("delta", e["after"] - e["before"])
        what = f'gained <b>{n}</b> free site{"" if n == 1 else "s"} &rarr; {e["after"]} left'
    night = date.fromisoformat(e["date"]).strftime("%a %d %b")
    camp = (f'<a href="/campground/{e["id"]}.html">{esc(e["name"])}</a>'
            if show_camp else "")
    return (f'<tr><td class="num nowrap">{when(e["ts"])}</td>'
            f'<td class="num nowrap">{night}</td>'
            f'<td>{camp}</td><td>{what}</td></tr>'
            if show_camp else
            f'<tr><td class="num nowrap">{when(e["ts"])}</td>'
            f'<td class="num nowrap">{night}</td><td>{what}</td></tr>')


def render_changes(changes, generated):
    opens = [e for e in changes if e["kind"] in ("opened", "released")]
    body = f"""
<p class="lede" style="max-width:none">Every night that changed on this board, newest first. Logged by comparing each
refresh with the one before it &mdash; the only public record of campsites quietly coming back.</p>
<p class="sub">Last refreshed {esc(generated)} (UTC). {len(changes)} events logged so far,
{len(opens)} of them sites appearing.</p>
<h2>Changes</h2>
<table>
<thead><tr><th class="num">When</th><th class="num">Night</th><th>Campground</th><th>What</th></tr></thead>
<tbody>{''.join(change_line(e) for e in changes[:200]) or '<tr><td colspan="4">Nothing yet. The board has to be refreshed twice before anything can change.</td></tr>'}</tbody>
</table>
"""
    return page(
        "Campsite changes — what just opened on Campboard",
        "A running log of campsite availability changes across US national park campgrounds: "
        "nights that opened up, campgrounds that closed for the season, weekends that sold out.",
        body, SITE_URL + "/changes.html")


def render_index(camps, today, generated, changes=None):
    weekend = today + timedelta(days=(5 - today.weekday()) % 7 or 7)
    sat = weekend.isoformat()
    sun = (weekend + timedelta(days=1)).isoformat()

    rows, open_weekend, sold_out_weekend, closed_weekend = [], 0, 0, 0
    for c in camps:
        d7 = days_from(c, today, 7)
        avail7 = sum(r["available"] for _, r in d7 if r)
        wk = [c["days"].get(sat), c["days"].get(sun)]
        wk_avail = sum(r["available"] for r in wk if r)
        wk_book = sum(bookable(r) for r in wk if r)
        if wk_book == 0:
            closed_weekend += 1
        elif wk_avail == 0:
            sold_out_weekend += 1
        else:
            open_weekend += 1
        bar = "".join(
            f'<span class="pill {"p-zero" if (r and bookable(r) and r["available"] == 0) else ("p-ok" if (r and r["available"]) else "p-closed")}" '
            f'style="min-width:0;padding:2px 5px;font-size:11px">'
            f'{"" if not r or bookable(r) == 0 else r["available"]}</span>'
            for _, r in d7
        )
        rows.append(f"""<tr>
<td class="camp"><a href="/campground/{c['id']}.html">{esc(c['name'])}</a>
<div class="park">{esc(c['park'])}</div></td>
<td class="num">{pill_for(c['days'].get(today.isoformat()))}</td>
<td class="num">{pill_for(c['days'].get(sat))}</td>
<td class="num">{pill_for(c['days'].get(sun))}</td>
<td class="num">{avail7 if avail7 else '&mdash;'}</td>
<td class="hide-s" style="white-space:nowrap">{bar}</td>
</tr>""")

    fresh = [e for e in (changes or []) if e["kind"] in ("opened", "released")][:6]
    strip = ""
    if fresh:
        items = "".join(
            f'<li>{esc(when(e["ts"]))} UTC &middot; '
            f'<a href="/campground/{e["id"]}.html">{esc(e["name"])}</a> &middot; '
            f'{date.fromisoformat(e["date"]).strftime("%a %d %b")} &mdash; '
            f'{"opened with " if e["kind"] == "released" else "now has "}'
            f'<b>{e["after"]}</b> free</li>' for e in fresh)
        strip = (f'<h2>Just opened</h2>'
                 f'<ul style="margin:0 0 28px;padding-left:20px;line-height:1.75">{items}</ul>')

    body = f"""
<p class="lede">{len(camps)} of the busiest campgrounds in the US national parks, and how many
sites each one still has free &mdash; so you can stop opening 40 tabs.</p>
<p class="sub">Last refreshed {esc(generated)} (UTC). This weekend: {open_weekend} campgrounds
have space, {sold_out_weekend} are full, {closed_weekend} are closed for the season.</p>
{strip}
<h2>Availability, soonest first</h2>
<table>
<thead><tr>
<th>Campground</th><th class="num">Tonight</th><th class="num">Sat</th><th class="num">Sun</th>
<th class="num">7 days</th><th class="hide-s">Next 7 nights</th>
</tr></thead>
<tbody>
{''.join(rows)}
</tbody></table>
<p class="lede" style="margin-top:26px">Each number is free tent/RV sites for that night.
Closed means closed for the season, not booked.</p>
"""
    return page(
        "Campboard — live US campsite availability, one page",
        "How many campsites are still free tonight and this weekend at Yosemite, Zion, "
        "Joshua Tree, Yellowstone and more. Read straight from Recreation.gov.",
        body, SITE_URL + "/")


def render_camp(camp, today, generated, changes=None):
    start = today
    d21 = days_from(camp, start, 21)

    cells = []
    for d, row in d21:
        dt = date.fromisoformat(d)
        if not row or bookable(row) == 0:
            cls, val = "gone", "—"
        elif row["available"] == 0:
            cls, val = "free0", "0"
        elif ratio(row) < 0.34:
            cls, val = "free1", str(row["available"])
        else:
            cls, val = "free2", str(row["available"])
        cells.append(f'<div class="day {cls}"><div class="d">{dt.strftime("%b")} {dt.day}</div>'
                     f'<div class="n">{val}</div></div>')

    nxt = [r for _, r in d21 if r and bookable(r)]
    open_days = sum(1 for r in nxt if r["available"])
    total_avail = sum(r["available"] for r in nxt)
    if nxt:
        summary = (f"{open_days} of the next 21 nights have at least one free site. "
                   f"{total_avail} site-nights available in total.")
    else:
        summary = "This campground is closed for the season in the window shown."

    recent = []
    for d, row in d21[:7]:
        dt = date.fromisoformat(d)
        if not row or bookable(row) == 0:
            recent.append(f"<tr><td>{dt.strftime('%a %d %b')}</td><td class='num'>closed</td>"
                          f"<td class='num'>&mdash;</td><td class='num'>&mdash;</td></tr>")
        else:
            recent.append(f"<tr><td>{dt.strftime('%a %d %b')}</td>"
                          f"<td class='num'>{row['available']}</td>"
                          f"<td class='num'>{row['reserved']}</td>"
                          f"<td class='num'>{row['closed'] + row['nyr']}</td></tr>")

    mine = [e for e in (changes or []) if e["id"] == camp["id"]][:8]
    log = ""
    if mine:
        log = ('<h2>Recent changes here</h2><table><thead><tr>'
               '<th class="num">When</th><th class="num">Night</th><th>What</th></tr></thead>'
               '<tbody>' + "".join(change_line(e, show_camp=False) for e in mine) +
               '</tbody></table>')

    body = f"""
<p class="sub"><a href="/">&larr; all campgrounds</a></p>
<h2 style="margin-top:0">{esc(camp['park'])}</h2>
<p class="lede">{esc(camp['name'])}</p>
<p class="sub">{esc(summary)} Last refreshed {esc(generated)} (UTC).</p>

<h2>Next 21 nights</h2>
<div class="daygrid">{''.join(cells)}</div>
<p class="legend">Free sites per night:
<span style="background:var(--grey)"></span>closed
<span style="background:var(--red)"></span>0
<span style="background:var(--amber)"></span>few
<span style="background:var(--green)"></span>plenty</p>

<h2>First week, in detail</h2>
<table>
<thead><tr><th>Night</th><th class="num">Free</th><th class="num">Booked</th>
<th class="num">Closed / not yet released</th></tr></thead>
<tbody>{''.join(recent)}</tbody>
</table>

{log}

<div class="card" style="margin-top:30px">
<h3>Book it on Recreation.gov</h3>
<p class="meta">The official reservation page for {esc(camp['name'])}.</p>
<a class="btn" href="{esc(camp['url'])}" rel="nofollow">Open on Recreation.gov &rarr;</a>
</div>
"""
    return page(
        f"{camp['name']} availability — {camp['park']}",
        f"Live campsite availability for {camp['name']} in {camp['park']}: free sites per "
        f"night for the next three weeks, read from Recreation.gov.",
        body, f"{SITE_URL}/campground/{camp['id']}.html")


def main():
    snap = json.loads((DATA / "snapshot.json").read_text(encoding="utf-8"))
    camps = snap["campgrounds"]
    today = datetime.fromisoformat(snap["generated"]).date()
    generated = snap["generated"].replace("T", " ").replace("+00:00", "")

    SITE.mkdir(exist_ok=True)
    (SITE / "campground").mkdir(exist_ok=True)

    changes = load_changes()

    (SITE / "index.html").write_text(render_index(camps, today, generated, changes), encoding="utf-8")
    (SITE / "changes.html").write_text(render_changes(changes, generated), encoding="utf-8")

    for c in camps:
        (SITE / "campground" / f"{c['id']}.html").write_text(
            render_camp(c, today, generated, changes), encoding="utf-8")

    (SITE / "data.json").write_text(json.dumps(snap, indent=1), encoding="utf-8")

    urls = ([f"{SITE_URL}/", f"{SITE_URL}/changes.html"] +
            [f"{SITE_URL}/campground/{c['id']}.html" for c in camps])
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
               "".join(f"<url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    (SITE / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (SITE / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")

    print(f"built {len(camps) + 1} pages + sitemap -> {SITE}")


if __name__ == "__main__":
    main()

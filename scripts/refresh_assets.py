#!/usr/bin/env python3
"""Regenerate Taha-Mahmoodi's data-driven profile assets from LIVE GitHub data.

Committed to the profile repo and re-run on a schedule by
.github/workflows/refresh-profile.yml, so the contribution star-timeline stays
current instead of freezing on the day it was forged.

Forged with git-a-profile (https://github.com/PIIIX-org/git-a-profile).
"""
import subprocess, json, math, random, os

USER = "Taha-Mahmoodi"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "assets", "startimeline.svg")

def fetch_days():
    q = ('query{user(login:"%s"){contributionsCollection{contributionCalendar{'
         'totalContributions weeks{contributionDays{date contributionCount}}}}}}' % USER)
    out = subprocess.run(["gh", "api", "graphql", "-f", "query=" + q],
                         capture_output=True, text=True, check=True).stdout
    cal = json.loads(out)["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    return days, cal["totalContributions"]

def build_svg(days, total):
    n = len(days)
    max_count = max((d["contributionCount"] for d in days), default=1) or 1
    active = sum(1 for d in days if d["contributionCount"] > 0)
    W, H = 900, 260
    PAD_L, PAD_R = 40, 40
    plot_w = W - PAD_L - PAD_R
    baseline, ceiling = 205, 56
    CY = baseline
    FONT = "SFMono-Regular, Menlo, Consolas, monospace"
    MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

    def x_at(i): return PAD_L + (i / (n - 1)) * plot_w
    def h_for(c): return (baseline - ceiling) * (math.log(c + 1) / math.log(max_count + 1))
    def size_for(c): return 1.4 + 4.6 * (math.log(c + 1) / math.log(max_count + 1))
    def op_for(c): return 0.45 + 0.55 * (math.log(c + 1) / math.log(max_count + 1))

    p = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
         f'role="img" aria-label="A year of commits mapped to a night sky: {active} active days, '
         f'{total} contributions, peak {max_count} in a day">']
    p.append('<title>A year of commits, mapped to the night sky</title>')
    p.append('<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
             '<stop offset="0%" stop-color="#0c1022"/><stop offset="55%" stop-color="#080a14"/>'
             '<stop offset="100%" stop-color="#05060d"/></linearGradient>'
             '<filter id="g" x="-200%" y="-200%" width="500%" height="500%">'
             '<feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/>'
             '<feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
    p.append(f'<rect width="{W}" height="{H}" fill="url(#sky)"/>')

    rnd = random.Random(7)
    for _ in range(90):
        x, y = rnd.uniform(0, W), rnd.uniform(8, baseline - 6)
        r, o = rnd.uniform(0.3, 0.9), rnd.uniform(0.06, 0.22)
        d, b = rnd.uniform(3.0, 6.5), rnd.uniform(0, 5)
        p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="#93a3c9" opacity="{o:.2f}">'
                 f'<animate attributeName="opacity" values="{o:.2f};{o*0.3:.2f};{o:.2f}" '
                 f'dur="{d:.1f}s" begin="{b:.1f}s" repeatCount="indefinite"/></circle>')

    p.append(f'<line x1="{PAD_L}" y1="{baseline}" x2="{W-PAD_R}" y2="{baseline}" stroke="#262c38" stroke-width="1"/>')
    seen = set()
    for i, day in enumerate(days):
        mo, yr = day["date"][5:7], day["date"][:4]
        if (yr, mo) not in seen and day["date"][8:10] <= '07':
            seen.add((yr, mo)); x = x_at(i)
            p.append(f'<line x1="{x:.1f}" y1="{baseline}" x2="{x:.1f}" y2="{baseline+5}" stroke="#3a4152" stroke-width="1"/>')
            p.append(f'<text x="{x:.1f}" y="{baseline+18}" text-anchor="middle" font-family="{FONT}" font-size="9" fill="#5b6472">{MONTHS[int(mo)-1]}</text>')

    for i, day in enumerate(days):
        c = day["contributionCount"]
        if c == 0: continue
        x = x_at(i); h = h_for(c); sy = baseline - h
        size, op = size_for(c), op_for(c)
        color = "#ffffff" if c >= max_count*0.6 else "#c3bdff" if c >= max_count*0.18 else "#6C63FF"
        if h > 26:
            p.append(f'<line x1="{x:.1f}" y1="{baseline:.1f}" x2="{x:.1f}" y2="{sy:.1f}" stroke="{color}" stroke-width="0.7" opacity="{op*0.35:.2f}"/>')
        dur, beg = 2.4 + (i % 5)*0.6, (i % 11)*0.35
        p.append(f'<circle cx="{x:.1f}" cy="{sy:.1f}" r="{size:.2f}" fill="{color}" opacity="{op:.2f}" filter="url(#g)">'
                 f'<animate attributeName="opacity" values="{op:.2f};{op*0.4:.2f};{op:.2f}" dur="{dur:.1f}s" begin="{beg:.2f}s" repeatCount="indefinite"/></circle>')

    p.append(f'<text x="{W/2}" y="28" text-anchor="middle" font-family="{FONT}" font-size="14" fill="#c9d1d9">A year of commits, mapped to the night sky</text>')
    p.append(f'<text x="{W/2}" y="45" text-anchor="middle" font-family="{FONT}" font-size="10" fill="#5b6472">{total} commits &#183; {active} active days &#183; peak {max_count} in a day</text>')
    p.append('</svg>')
    return "\n".join(p)

if __name__ == "__main__":
    days, total = fetch_days()
    with open(OUT, "w") as f:
        f.write(build_svg(days, total))
    print(f"refreshed {OUT} ({total} contributions)")

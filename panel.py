#!/usr/bin/env python3
"""Generate contribution-panel.svg from the public GitHub contribution
calendar (the same source Sushmita's commit-log panel uses). Stdlib only.
Usage: panel.py [saved-contributions.html]  (fetches live when no file given)"""
import re, sys, urllib.request
from datetime import date, timedelta

USER = "abdullahafrididev"
SERIF = "Georgia, 'Iowan Old Style', 'Palatino Linotype', 'Times New Roman', serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
BG1, BG2, ACC, LIGHT, TXT, MUT = "#0A101F", "#060A14", "#7FB3FF", "#BCD7FF", "#F2F7FF", "#8FA6C4"
LEVELS = ["#101C33", "#0E4DA4", "#1F6FEB", "#4C9AFF", "#BCD7FF"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def fetch():
    if len(sys.argv) > 1:
        return open(sys.argv[1], encoding="utf-8").read()
    req = urllib.request.Request(f"https://github.com/users/{USER}/contributions",
                                 headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8")

def parse(html):
    days, id2date = {}, {}
    for tag in re.findall(r"<td[^>]*>", html):
        md = re.search(r'data-date="(\d{4}-\d{2}-\d{2})"', tag)
        mi = re.search(r'id="(contribution-day-component-[\d-]+)"', tag)
        ml = re.search(r'data-level="(\d)"', tag)
        if md and mi and ml:
            y, mo, d = map(int, md.group(1).split("-"))
            days[date(y, mo, d)] = (0, int(ml.group(1)))
            id2date[mi.group(1)] = date(y, mo, d)
    for tid, text in re.findall(r'<tool-tip[^>]*for="(contribution-day-component-[\d-]+)"[^>]*>([^<]*)</tool-tip>', html):
        m = re.match(r"(\d+) contribution", text.strip())
        if m and tid in id2date:
            d = id2date[tid]
            days[d] = (int(m.group(1)), days[d][1])
    return days

def main():
    days = parse(fetch())
    if not days:
        sys.exit("no calendar data parsed")
    dates = sorted(days)
    total = sum(c for c, _ in days.values())
    active = [d for d in dates if days[d][0] > 0]
    best, cur, best_end, prev = 0, 0, None, None
    for d in dates:
        if days[d][0] > 0:
            cur = cur + 1 if prev and (d - prev).days == 1 else 1
            if cur > best:
                best, best_end = cur, d
        else:
            cur = 0
        prev = d
    streak_start = best_end - timedelta(days=best - 1) if best_end else None
    busiest = max(dates, key=lambda d: days[d][0])
    bcount = days[busiest][0]
    latest_active = active[-1] if active else None

    start = dates[0] - timedelta(days=(dates[0].weekday() + 1) % 7)
    ncols = (dates[-1] - start).days // 7 + 1

    GX, GY, PITCH, SQ = 96, 262, 19, 14
    cells, month_labels, seen_months = "", "", set()
    for d in dates:
        col = (d - start).days // 7
        row = (d.weekday() + 1) % 7
        x, y = GX + col * PITCH, GY + row * PITCH
        cnt, lvl = days[d]
        cells += f'<rect x="{x}" y="{y}" width="{SQ}" height="{SQ}" rx="3" fill="{LEVELS[lvl]}"/>'
        if d.month not in seen_months and d.day <= 7:
            seen_months.add(d.month)
            month_labels += f'<text class="cp-mono" x="{x}" y="{GY - 12}" font-size="10" fill="{MUT}">{MONTHS[d.month-1]}</text>'
        if d == latest_active:
            cx, cy = x + SQ / 2, y + SQ / 2
            cells += (f'<circle cx="{cx}" cy="{cy}" r="8.5" fill="#F2F7FF"/>'
                      f'<circle cx="{cx-3}" cy="{cy-1}" r="1.7" fill="#0A101F"/>'
                      f'<circle cx="{cx+3}" cy="{cy-1}" r="1.7" fill="#0A101F"/>')
    for i, lab in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        cells += f'<text class="cp-mono" x="52" y="{GY + i * PITCH + 11}" font-size="10" fill="{MUT}">{lab}</text>'
    legend = "".join(f'<rect x="{i*17}" y="0" width="12" height="12" rx="2.5" fill="{LEVELS[i]}"/>' for i in range(5))
    rng = f"{MONTHS[dates[0].month-1]} {dates[0].year} \u2013 {MONTHS[dates[-1].month-1]} {dates[-1].year}"
    today = dates[-1]
    snap = f"{today.day} {MONTHS[today.month-1]} {today.year}"
    streak_line = (f"LONGEST STREAK \u00b7 {best} DAY{"S" if best != 1 else ""} \u00b7 {streak_start.day} {MONTHS[streak_start.month-1].upper()} {streak_start.year} \u2013 {best_end.day} {MONTHS[best_end.month-1].upper()} {best_end.year}"
                   if best_end else "LONGEST STREAK \u00b7 0 DAYS")

    def stat(x, label, value, sub):
        return (f'<text class="cp-mono" x="{x}" y="86" font-size="10" letter-spacing="2" fill="{MUT}">{label}</text>'
                f'<text class="cp-serif" x="{x}" y="128" font-size="40" font-weight="300" fill="{TXT}">{value}</text>'
                f'<text class="cp-sans" x="{x}" y="150" font-size="11" fill="{MUT}">{sub}</text>')

    W, H = 1200, 520
    P = 2 * (W + H); seg = int(P * 0.15)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img">
<defs>
  <linearGradient id="cp-bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG1}"/><stop offset="1" stop-color="{BG2}"/></linearGradient>
  <radialGradient id="cp-glow" cx="85%" cy="10%" r="70%"><stop offset="0" stop-color="#1F6FEB" stop-opacity=".45"/><stop offset="1" stop-color="#1F6FEB" stop-opacity="0"/></radialGradient>
  <linearGradient id="cp-trace" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{ACC}" stop-opacity="0"/><stop offset=".5" stop-color="{ACC}"/><stop offset=".75" stop-color="#E9C979"/><stop offset="1" stop-color="{ACC}" stop-opacity="0"/></linearGradient>
</defs>
<style>
  .cp-serif {{ font-family: {SERIF}; }} .cp-mono {{ font-family: {MONO}; }} .cp-sans {{ font-family: {SANS}; }}
  .cp-trace {{ stroke-dasharray: {seg} {P-seg}; stroke-dashoffset: {P}; animation: cp-trace 7s linear infinite; }}
  @keyframes cp-trace {{ to {{ stroke-dashoffset: 0; }} }}
  @media (prefers-reduced-motion: reduce) {{ .cp-trace {{ display: none; }} }}
</style>
<rect width="{W}" height="{H}" rx="20" fill="url(#cp-bg)"/>
<rect width="{W}" height="{H}" rx="20" fill="url(#cp-glow)"/>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="19.5" fill="none" stroke="{ACC}" stroke-opacity=".16"/>
<rect class="cp-trace" x=".5" y=".5" width="{W-1}" height="{H-1}" rx="19.5" fill="none" stroke="url(#cp-trace)" stroke-width="1.5" stroke-linecap="round"/>
<text class="cp-mono" x="48" y="92" font-size="11" letter-spacing="2.6" fill="{ACC}">COMMIT LOG \u00b7 REAL GITHUB ACTIVITY</text>
<text class="cp-serif" x="46" y="140" font-size="31" font-weight="300" fill="{TXT}">A year of building, <tspan font-style="italic" fill="{LIGHT}">one square</tspan> at a time.</text>
{stat(660, "CONTRIBUTIONS", f"{total:,}", rng)}
{stat(806, "ACTIVE DAYS", str(len(active)), f"of {len(dates)} days")}
{stat(922, "LONGEST STREAK", str(best), "consecutive days")}
{stat(1052, "BUSIEST DAY", str(bcount), f"{busiest.day} {MONTHS[busiest.month-1]} {busiest.year}")}
{month_labels}
{cells}
<text class="cp-mono" x="{GX + (ncols * PITCH)//2 - 130}" y="{GY + 7 * PITCH + 34}" font-size="10.5" letter-spacing="2" fill="{MUT}">{streak_line}</text>
<text class="cp-sans" x="48" y="{H - 26}" font-size="11" fill="{MUT}">Source: public GitHub contribution calendar for @{USER} \u00b7 snapshot {snap} \u00b7 refreshed daily</text>
<g transform="translate(1022 {H - 40})"><text class="cp-sans" x="-34" y="11" font-size="11" fill="{MUT}">Less</text>{legend}<text class="cp-sans" x="92" y="11" font-size="11" fill="{MUT}">More</text></g>
</svg>"""
    open("contribution-panel.svg", "w").write(svg)
    print(f"total={total} active={len(active)} streak={best} busiest={bcount} on {busiest} cols={ncols}")

if __name__ == "__main__":
    main()

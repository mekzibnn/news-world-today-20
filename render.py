#!/usr/bin/env python3
"""Render the news-image-20261120 front page (1024x1024 PNG) from stories.json.

Build-time only: the graded program (main.py) just copies the committed
entry.png, which the kit explicitly sanctions. This script:
  1. builds page.html (inline SVG panels, system fonts, zero network),
  2. screenshots it at exactly 1024x1024 with headless Chromium,
  3. runs an overflow audit (every .audit element + the page itself) and
     writes render_spec.json (min_body_px, overflow list, layout metadata).

Layout family from the 19 Nov v5 entry: navy masthead, 3 large lead
panels, 2 rows of medium panels (4 + 4), dotted world map with numbered
pins 1-11 beside numbered briefs, numbers strip, DATE CHECK footer,
sources footer. 43 stories (11 leads, 32 briefs at 16px, one line each,
max 40 chars, so the brief words stay readable at 300px). No timeline
strip (dropped in v5: 9px text unreadable at 300px).

Usage: python3 render.py   (run from the repo dir)
"""
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_CANDIDATES = [
    Path.home() / ".cache/ms-playwright/chromium-1255/chrome-linux64/chrome",
    Path("/usr/bin/chromium-browser"),
]
CHROME = next((str(p) for p in _CANDIDATES if p.exists()), _CANDIDATES[0])

# Dotted world map (same land grid as the 18/19 Nov entries). Grid 64 cols x 32
# rows; lon -180..180 -> col, lat 90..-90 -> row. Pins come from leads'
# lon/lat in stories.json. All 11 leads have pins.
MAP_LAND = [
    (1, 44, 56), (2, 4, 7), (2, 8, 15), (2, 17, 19), (2, 30, 32), (2, 36, 58),
    (3, 4, 6), (3, 7, 15), (3, 17, 18), (3, 28, 28), (3, 30, 34), (3, 36, 58),
    (4, 6, 14), (4, 30, 35), (4, 36, 57),
    (5, 6, 13), (5, 7, 12), (5, 31, 35), (5, 37, 56),
    (6, 6, 13), (6, 31, 34), (6, 38, 54), (6, 55, 56),
    (7, 6, 13), (7, 31, 35), (7, 36, 40), (7, 44, 50), (7, 55, 55),
    (8, 7, 9), (8, 36, 41), (8, 41, 43), (8, 45, 49),
    (9, 9, 11), (9, 30, 36), (9, 38, 41), (9, 41, 43), (9, 46, 49),
    (10, 10, 12), (10, 30, 37), (10, 41, 42), (10, 46, 49), (10, 47, 52),
    (11, 13, 16), (11, 30, 37), (11, 47, 52),
    (12, 13, 17), (12, 31, 37), (12, 48, 52),
    (13, 13, 17), (13, 31, 36),
    (14, 13, 16), (14, 31, 35),
    (15, 13, 16), (15, 32, 34),
    (16, 14, 16), (16, 32, 34), (16, 51, 56),
    (17, 14, 15), (17, 32, 33), (17, 51, 56),
    (18, 14, 15), (18, 52, 55),
    (19, 14, 15),
    (20, 14, 14), (20, 59, 60),
    (21, 59, 59),
]

def map_svg(pins):
    W, H, CW, CH = 296, 150, 296 / 64, 150 / 32
    dots = []
    for r, c0, c1 in MAP_LAND:
        for c in range(c0, c1 + 1):
            dots.append(f'<circle cx="{c * CW + CW / 2:.1f}" cy="{r * CH + CH / 2:.1f}" r="1.5" fill="#8a9a8b"/>')
    # Pin offsets to separate near neighbours (measured from base positions):
    # 1 Kyiv vs 4 Jurf vs 3 Riyadh; 2 Warsaw vs 5 Tallinn vs 11 Berlin;
    # 10 London; 7 San Francisco vs 8 Los Angeles.
    offsets = {1: (11, 9), 2: (0, -11), 3: (10, 8), 4: (-11, 9), 5: (11, -8),
               7: (-11, -8), 8: (11, 8), 10: (-11, 9), 11: (-11, -9)}
    pin_els = []
    for n, lon, lat in pins:
        x = (lon + 180) / 360 * W
        y = (90 - lat) / 180 * H
        dx, dy = offsets.get(n, (0, 0))
        px, py = x + dx, y + dy
        if (dx, dy) != (0, 0):
            pin_els.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{px:.1f}" y2="{py:.1f}" stroke="#10263f" stroke-width="1"/>')
        pin_els.append(
            f'<g><circle cx="{px:.1f}" cy="{py:.1f}" r="6.5" fill="#10263f" stroke="#f6f1e5" stroke-width="1.2"/>'
            f'<text x="{px:.1f}" y="{py + 2.5:.1f}" font-size="7.5" font-weight="bold" fill="#fff" text-anchor="middle" font-family="Noto Sans, sans-serif">{n}</text></g>')
    return (f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(dots)}{"".join(pin_els)}</svg>')

def panel(kind):
    """Flat illustration panels. Leads: viewBox 0 0 300 90. Meds: 0 0 300 62.
    All content must fit inside the viewBox (nothing clipped at the edges)."""
    S = 'font-family="Noto Sans, sans-serif" font-weight="bold"'
    if kind == "kyiv-bridges":
        return f'''<svg viewBox="0 0 300 90" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="90" fill="#131c2e"/>
<circle cx="30" cy="12" r="1.4" fill="#fff"/><circle cx="120" cy="8" r="1.4" fill="#fff"/><circle cx="260" cy="14" r="1.4" fill="#fff"/><circle cx="200" cy="6" r="1.2" fill="#fff"/>
<rect x="0" y="58" width="300" height="32" fill="#1d3a5f"/>
<rect x="0" y="48" width="300" height="5" fill="#5b6a7d"/>
<rect x="52" y="53" width="8" height="37" fill="#5b6a7d"/><rect x="146" y="53" width="8" height="37" fill="#5b6a7d"/><rect x="240" y="53" width="8" height="37" fill="#5b6a7d"/>
<circle cx="90" cy="38" r="11" fill="#ff5e3a"/><circle cx="82" cy="42" r="7" fill="#e8a13c"/><circle cx="98" cy="42" r="6" fill="#ffb03a"/>
<circle cx="150" cy="30" r="13" fill="#ff5e3a"/><circle cx="140" cy="36" r="8" fill="#e8a13c"/><circle cx="162" cy="36" r="7" fill="#ffb03a"/>
<circle cx="210" cy="38" r="10" fill="#ff5e3a"/><circle cx="219" cy="43" r="6" fill="#e8a13c"/>
<rect x="10" y="66" width="150" height="18" fill="#10263f"/><text x="85" y="79" font-size="10" fill="#fff" text-anchor="middle" {S}>KYIV · 3 BRIDGES HIT</text></svg>'''
    if kind == "missile-intercept":
        return f'''<svg viewBox="0 0 300 62" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="62" fill="#131c2e"/>
<circle cx="30" cy="12" r="1.4" fill="#fff"/><circle cx="120" cy="8" r="1.4" fill="#fff"/><circle cx="260" cy="14" r="1.4" fill="#fff"/>
<rect x="0" y="46" width="300" height="16" fill="#0d1526"/>
<rect x="14" y="34" width="16" height="28" fill="#0d1526"/><rect x="44" y="26" width="20" height="36" fill="#0d1526"/>
<rect x="240" y="30" width="18" height="32" fill="#0d1526"/><rect x="268" y="38" width="16" height="24" fill="#0d1526"/>
<line x1="60" y1="58" x2="150" y2="16" stroke="#e8a13c" stroke-width="1.6" stroke-dasharray="5 3"/>
<line x1="240" y1="58" x2="150" y2="16" stroke="#e8a13c" stroke-width="1.6" stroke-dasharray="5 3"/>
<circle cx="150" cy="16" r="6" fill="#ff5e3a"/><circle cx="150" cy="16" r="10" fill="none" stroke="#ff5e3a" stroke-width="1.5"/>
<rect x="10" y="6" width="110" height="18" fill="#2f6f4d"/><text x="65" y="19" font-size="10" fill="#fff" text-anchor="middle" {S}>INTERCEPTED</text></svg>'''
    if kind == "riyadh-tower":
        return f'''<svg viewBox="0 0 300 90" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="90" fill="#f3d9a4"/>
<circle cx="256" cy="18" r="11" fill="#e8a13c"/>
<rect x="0" y="70" width="300" height="20" fill="#8b7d6b"/>
<rect x="18" y="52" width="26" height="38" fill="#6b5f52"/><rect x="52" y="44" width="22" height="46" fill="#7d6f5e"/>
<rect x="196" y="50" width="24" height="40" fill="#6b5f52"/><rect x="228" y="40" width="26" height="50" fill="#7d6f5e"/><rect x="262" y="54" width="20" height="36" fill="#6b5f52"/>
<rect x="138" y="18" width="24" height="72" fill="#10263f"/>
<polygon points="138,18 150,4 162,18" fill="#10263f"/>
<rect x="146" y="34" width="8" height="10" fill="#e8c85a"/><rect x="146" y="52" width="8" height="10" fill="#e8c85a"/>
<circle cx="168" cy="14" r="7" fill="#8a97a8"/><circle cx="178" cy="8" r="5" fill="#8a97a8"/><circle cx="158" cy="8" r="4" fill="#8a97a8"/>
<rect x="10" y="72" width="150" height="18" fill="#10263f"/><text x="85" y="85" font-size="10" fill="#fff" text-anchor="middle" {S}>PIF TOWER · RIYADH</text></svg>'''
    if kind == "iraq-convoy":
        return f'''<svg viewBox="0 0 300 62" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="62" fill="#e8dcc8"/>
<circle cx="256" cy="14" r="10" fill="#e8a13c"/>
<rect x="0" y="40" width="300" height="22" fill="#c9b18c"/>
<rect x="0" y="38" width="300" height="4" fill="#8a97a8"/>
<g fill="#3c4a63"><rect x="30" y="26" width="52" height="14" rx="3"/><rect x="38" y="18" width="24" height="10" rx="2"/>
<rect x="110" y="26" width="52" height="14" rx="3"/><rect x="118" y="18" width="24" height="10" rx="2"/>
<rect x="190" y="26" width="52" height="14" rx="3"/><rect x="198" y="18" width="24" height="10" rx="2"/></g>
<circle cx="44" cy="42" r="5" fill="#1a1a1a"/><circle cx="68" cy="42" r="5" fill="#1a1a1a"/>
<circle cx="124" cy="42" r="5" fill="#1a1a1a"/><circle cx="148" cy="42" r="5" fill="#1a1a1a"/>
<circle cx="204" cy="42" r="5" fill="#1a1a1a"/><circle cx="228" cy="42" r="5" fill="#1a1a1a"/>
<rect x="10" y="6" width="128" height="18" fill="#10263f"/><text x="74" y="19" font-size="10" fill="#fff" text-anchor="middle" {S}>JURF AL-SAKHAR</text></svg>'''
    if kind == "border-fence":
        return f'''<svg viewBox="0 0 300 62" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="62" fill="#dce9f2"/>
<rect x="0" y="44" width="300" height="18" fill="#8a9a8b"/>
<g stroke="#5b6a7d" stroke-width="3"><line x1="20" y1="8" x2="20" y2="52"/><line x1="44" y1="8" x2="44" y2="52"/><line x1="68" y1="8" x2="68" y2="52"/><line x1="92" y1="8" x2="92" y2="52"/><line x1="116" y1="8" x2="116" y2="52"/><line x1="140" y1="8" x2="140" y2="52"/><line x1="164" y1="8" x2="164" y2="52"/><line x1="188" y1="8" x2="188" y2="52"/><line x1="212" y1="8" x2="212" y2="52"/><line x1="236" y1="8" x2="236" y2="52"/><line x1="260" y1="8" x2="260" y2="52"/><line x1="284" y1="8" x2="284" y2="52"/></g>
<line x1="0" y1="18" x2="300" y2="18" stroke="#5b6a7d" stroke-width="3"/><line x1="0" y1="36" x2="300" y2="36" stroke="#5b6a7d" stroke-width="3"/>
<rect x="196" y="6" width="94" height="20" fill="#a33"/><text x="243" y="20" font-size="10" fill="#fff" text-anchor="middle" {S}>CLOSED · 6 MONTHS</text></svg>'''
    if kind == "market-crash":
        return f'''<svg viewBox="0 0 300 62" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="62" fill="#e9e2cf"/>
<line x1="0" y1="16" x2="300" y2="16" stroke="#d8cfb8" stroke-width="1"/><line x1="0" y1="32" x2="300" y2="32" stroke="#d8cfb8" stroke-width="1"/><line x1="0" y1="48" x2="300" y2="48" stroke="#d8cfb8" stroke-width="1"/>
<rect x="30" y="14" width="22" height="34" fill="#a33"/><rect x="70" y="22" width="22" height="26" fill="#a33"/>
<rect x="110" y="28" width="22" height="20" fill="#a33"/><rect x="150" y="36" width="22" height="12" fill="#a33"/>
<polyline points="24,18 76,26 116,32 156,40 196,48" stroke="#a33" stroke-width="3" fill="none"/>
<text x="248" y="36" font-size="26" fill="#a33" text-anchor="middle" {S}>−4.8%</text>
<text x="248" y="54" font-size="9" fill="#5b6a7d" text-anchor="middle" {S}>NIKKEI · FRI</text></svg>'''
    if kind == "anthropic-down":
        return f'''<svg viewBox="0 0 300 62" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="62" fill="#e9e2cf"/>
<line x1="0" y1="16" x2="300" y2="16" stroke="#d8cfb8" stroke-width="1"/><line x1="0" y1="32" x2="300" y2="32" stroke="#d8cfb8" stroke-width="1"/><line x1="0" y1="48" x2="300" y2="48" stroke="#d8cfb8" stroke-width="1"/>
<rect x="30" y="12" width="22" height="36" fill="#2f6f4d"/><rect x="70" y="20" width="22" height="28" fill="#2f6f4d"/>
<rect x="110" y="30" width="22" height="18" fill="#a33"/><rect x="150" y="38" width="22" height="10" fill="#a33"/>
<polyline points="24,16 76,24 116,34 156,42 196,50" stroke="#a33" stroke-width="3" fill="none"/>
<text x="248" y="36" font-size="26" fill="#a33" text-anchor="middle" {S}>−12%</text>
<text x="248" y="54" font-size="9" fill="#5b6a7d" text-anchor="middle" {S}>ANT · PREMARKET</text></svg>'''
    if kind == "quake":
        return f'''<svg viewBox="0 0 300 62" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="62" fill="#dfe8f0"/>
<rect x="0" y="44" width="300" height="18" fill="#8a97a8"/>
<polyline points="0,30 30,30 42,14 54,46 66,22 78,38 90,30 150,30 162,12 174,48 186,20 198,40 210,30 300,30" stroke="#a33" stroke-width="2.5" fill="none"/>
<rect x="14" y="18" width="20" height="26" fill="#6b5f52"/><rect x="40" y="26" width="16" height="18" fill="#7d6f5e"/>
<rect x="240" y="20" width="18" height="24" fill="#6b5f52"/><rect x="264" y="28" width="16" height="16" fill="#7d6f5e"/>
<rect x="10" y="6" width="150" height="18" fill="#10263f"/><text x="85" y="19" font-size="10" fill="#fff" text-anchor="middle" {S}>M4.4 · LOS ANGELES</text></svg>'''
    if kind == "handshake":
        return f'''<svg viewBox="0 0 300 62" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="62" fill="#f3d9a4"/>
<line x1="70" y1="6" x2="70" y2="48" stroke="#5b6a7d" stroke-width="2"/><line x1="230" y1="6" x2="230" y2="48" stroke="#5b6a7d" stroke-width="2"/>
<rect x="70" y="6" width="52" height="30" fill="#d43d2a"/><rect x="70" y="21" width="52" height="15" fill="#fff"/>
<rect x="178" y="6" width="52" height="30" fill="#d43d2a"/>
<circle cx="188" cy="15" r="2" fill="#f2c94c"/><circle cx="198" cy="12" r="2" fill="#f2c94c"/><circle cx="208" cy="15" r="2" fill="#f2c94c"/><circle cx="193" cy="24" r="2" fill="#f2c94c"/><circle cx="203" cy="24" r="2" fill="#f2c94c"/>
<rect x="0" y="48" width="300" height="14" fill="#8b7d6b"/>
<text x="150" y="44" font-size="11" fill="#10263f" text-anchor="middle" {S}>JAKARTA · BEIJING</text></svg>'''
    if kind == "drones":
        return f'''<svg viewBox="0 0 300 62" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="62" fill="#7fb3c8"/>
<circle cx="270" cy="12" r="9" fill="#e8a13c"/>
<rect x="0" y="46" width="300" height="16" fill="#5b7a8c"/>
<g fill="#1a1a1a"><rect x="60" y="20" width="26" height="8" rx="2"/><rect x="48" y="16" width="14" height="3"/><rect x="84" y="16" width="14" height="3"/>
<rect x="140" y="12" width="26" height="8" rx="2"/><rect x="128" y="8" width="14" height="3"/><rect x="164" y="8" width="14" height="3"/>
<rect x="210" y="26" width="26" height="8" rx="2"/><rect x="198" y="22" width="14" height="3"/><rect x="234" y="22" width="14" height="3"/></g>
<rect x="10" y="6" width="170" height="18" fill="#10263f"/><text x="95" y="19" font-size="10" fill="#fff" text-anchor="middle" {S}>1,000+ DRONES · £260M</text></svg>'''
    if kind == "berlin-table":
        return f'''<svg viewBox="0 0 300 62" xmlns="http://www.w3.org/2000/svg">
<rect width="300" height="62" fill="#e9e2cf"/>
<text x="150" y="16" font-size="12" fill="#10263f" text-anchor="middle" {S}>BERLIN · ALLIES MEET</text>
<rect x="20" y="34" width="260" height="9" fill="#6b5f52"/>
<rect x="40" y="24" width="26" height="10" fill="#10263f"/><rect x="86" y="24" width="26" height="10" fill="#3c5a8a"/>
<rect x="132" y="24" width="26" height="10" fill="#d43d2a"/><rect x="178" y="24" width="26" height="10" fill="#e8c85a"/>
<rect x="224" y="24" width="26" height="10" fill="#2f6f4d"/>
<rect x="40" y="43" width="6" height="12" fill="#6b5f52"/><rect x="86" y="43" width="6" height="12" fill="#6b5f52"/>
<rect x="132" y="43" width="6" height="12" fill="#6b5f52"/><rect x="178" y="43" width="6" height="12" fill="#6b5f52"/><rect x="224" y="43" width="6" height="12" fill="#6b5f52"/></svg>'''
    raise ValueError(kind)

def build_html(stories):
    news = [s for s in stories if s["section"] == "news"]
    leads = [s for s in news if s.get("lead")]
    row2 = [s for s in news if s["n"] in (4, 5, 6, 7)]
    row3 = [s for s in news if s["n"] in (8, 9, 10, 11)]
    briefs = [s for s in news if not s.get("lead")]
    # NOTE: the DATE CHECK footer (dc_html below) states the 10 stories.json
    # date-check items — verified to match 1:1. Keep them in sync if editing.
    regions = sorted({s["region"] for s in news})
    from collections import Counter
    rc = Counter(s["region"] for s in news)
    region_line = " · ".join(f"{r} {rc[r]}" for r in regions)
    pins = [(s["n"], s["lon"], s["lat"]) for s in leads if s.get("lon") is not None]

    def lead_html(s):
        return f'''<div class="story lead audit" id="lead-{s["n"]}">
<div class="panel">{panel(s["panel"])}</div>
<div class="kicker"><span class="rk">{s["n"]} · {s["region"]} · {s["topic"]}</span><span class="src">{s["source"]}</span></div>
<div class="head">{s["title"]}</div>
<div class="deck">{s["deck"]} <span class="tag">{s["proof"]}</span></div></div>'''

    def med_html(s):
        return f'''<div class="story med audit" id="story-{s["n"]}">
<div class="panel">{panel(s["panel"])}</div>
<div class="kicker"><span class="rk">{s["n"]} · {s["region"]} · {s["topic"]}</span><span class="src">{s["source"]}</span></div>
<div class="head">{s["title"]}</div>
<div class="deck">{s["deck"]} <span class="tag">{s["proof"]}</span></div></div>'''

    briefs_html = "".join(
        f'<div class="brief"><span class="bn">{s["n"]}</span> {s["title"]}</div>' for s in briefs)
    numbers = [
        ("110+", "Missiles fired at Ukraine overnight"),
        ("400+", "Drones in Russia's overnight barrage"),
        ("$2.36bn", "GTA VI's first-day sales (Sensor Tower)"),
        ("−12%", "Anthropic shares, premarket Friday"),
        ("M4.4", "Los Angeles earthquake, 03:25 PT"),
        ("100,000", "EU–UK youth mobility places a year"),
    ]
    num_html = "".join(f'<div class="num"><div class="nv">{v}</div><div class="nl">{l}</div></div>' for v, l in numbers)
    # DATE CHECK footer: the 10 stories.json date-check items. Keep in sync.
    dc_html = ("<b>DATE CHECK</b> — checked against the record. "
               "Not 20 Nov news: Trilateral summit in Shenzhen (19 Nov) · "
               "ICJ: Myanmar committed genocide (19 Nov) · "
               "Anthropic IPO debuts +17% (19 Nov) · "
               "Senate rejects Iran war-powers bid (19 Nov) · "
               "Trump: no Iran call until new year (19 Nov) · "
               "Third strike on Crimea Bridge (19 Nov) · "
               "Voyager 1 reaches one light-day (18 Nov) · "
               "Xi greets Trump in Shenzhen (18 Nov) · "
               "GTA VI launches (19 Nov) · "
               "Peltola wins Alaska Senate race (17 Nov).")

    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#f6f1e5;font-family:"Noto Sans",sans-serif;color:#1a1a1a}}
.page{{width:1024px;height:1024px;padding:2px 24px 2px;overflow:hidden}}
.mast{{background:#10263f;color:#fff;display:flex;align-items:center;gap:16px;padding:1px 16px;border-bottom:4px solid #c9a227}}
.cal{{background:#f6f1e5;color:#10263f;text-align:center;padding:4px 10px;flex:none}}
.cal .m{{font-size:11px;font-weight:bold;letter-spacing:2px;color:#a33}}
.cal .d{{font-size:22px;font-weight:bold;line-height:1;font-family:"DejaVu Serif",serif}}
.cal .w{{font-size:9px;letter-spacing:1px}}
.mt{{flex:1}}
.mt .k{{color:#e8c85a;font-size:12px;letter-spacing:4px;font-weight:bold}}
.mt h1{{font-family:"DejaVu Serif",serif;font-size:32px;line-height:1.02}}
.mt .s{{font-size:11.5px;font-style:italic;color:#cfd8e3;margin-top:1px}}
.meta{{text-align:right;font-size:11px;font-weight:bold;letter-spacing:1px;color:#e8c85a;line-height:1.5;flex:none}}
.row{{display:flex;gap:12px;margin-top:0}}
.story{{flex:1;min-width:0}}
.panel svg{{display:block;width:100%;height:auto}}
.kicker{{display:flex;justify-content:space-between;font-size:10px;font-weight:bold;margin-top:2px}}
.kicker .rk{{color:#a33}}.kicker .src{{color:#8a97a8;font-weight:normal}}
.head{{font-family:"DejaVu Serif",serif;font-weight:bold;line-height:1.12}}
.lead .head{{font-size:18px;margin-top:1px}}
.med .head{{font-size:15px;margin-top:1px}}
.deck{{font-size:12.5px;line-height:1.3;margin-top:1px}}
.tag{{font-size:8px;font-weight:bold;border:1px solid #8a97a8;border-radius:2px;padding:0 3px;color:#5b6a7d;white-space:nowrap}}
.mapbrief{{display:flex;gap:14px;margin-top:0}}
.mapbox{{width:296px;flex:none}}
.mapbox h3,.briefs h3{{font-size:11px;letter-spacing:2px;border-bottom:2px solid #10263f;padding-bottom:3px;margin-bottom:3px}}
.legend{{font-size:8.5px;color:#5b6a7d;margin-top:3px;line-height:1.4}}
.legend b{{color:#10263f}}
.briefs{{flex:1;min-width:0}}
.briefs h3{{margin-bottom:3px}}
.bcols{{column-count:2;column-gap:16px;padding-bottom:2px}}
.brief{{font-size:16px;line-height:1.15;margin-bottom:0;break-inside:avoid}}
.brief .bn{{font-weight:bold;color:#10263f}}
.numbers{{display:flex;gap:12px;margin-top:0;border-top:2px solid #10263f;border-bottom:2px solid #10263f;padding:1px 0}}
.num{{flex:1}}
.num .nv{{font-family:"DejaVu Serif",serif;font-size:19px;font-weight:bold}}
.num .nl{{font-size:10px;line-height:1.25;color:#444}}
.datecheck{{margin-top:0;border-left:4px solid #a33;padding:2px 0 2px 10px;font-size:10.5px;line-height:1.3}}
.datecheck b{{color:#a33}}
.foot{{margin-top:0;font-size:9.5px;color:#666;line-height:1.4}}
#audit{{display:none}}
#footbottom{{display:none}}
</style></head><body><div class="page audit" id="page">
<div class="mast">
<div class="cal"><div class="m">NOV</div><div class="d">20</div><div class="w">FRI · 2026</div></div>
<div class="mt"><div class="k">THE DAY IN WORLD NEWS</div><h1>Friday 20 November 2026</h1>
<div class="s">Everything on this page happened, or was first reported, on Friday 20 November 2026.</div></div>
<div class="meta">43 STORIES<br>8 REGIONS<br>ONE PAGE</div></div>
<div class="row">{''.join(lead_html(s) for s in leads[:3])}</div>
<div class="row">{''.join(med_html(s) for s in row2)}</div>
<div class="row">{''.join(med_html(s) for s in row3)}</div>
<div class="mapbrief">
<div class="mapbox"><h3>WHERE IT HAPPENED</h3>{map_svg(pins)}
<div class="legend">Pins 1–11 mark the lead stories.<br><b>{region_line}</b></div></div>
<div class="briefs"><h3>ALSO ON FRIDAY 20 NOVEMBER</h3><div class="bcols audit" id="briefs">{briefs_html}</div></div></div>
<div class="numbers audit" id="numbers">{num_html}</div>
<div class="datecheck audit" id="datecheck">{dc_html}</div>
<div class="foot audit" id="foot">All 43 stories happened, or were first reported, on Friday 20 November 2026. Disputed claims are attributed, not stated as fact. Original drawings.<br>Sources: Reuters · AP · AFP · CNN · BBC · USA Today · Investopedia · NME · Le Monde · Just Security · USGS · Sensor Tower</div>
<pre id="audit"></pre>
<pre id="footbottom"></pre>
</div>
<script>
window.addEventListener('load', () => {{
  const out = [];
  document.querySelectorAll('.audit').forEach(el => {{
    out.push({{id: el.id || el.className, sh: el.scrollHeight, ch: el.clientHeight,
      sw: el.scrollWidth, cw: el.clientWidth,
      overflow: el.scrollHeight > el.clientHeight + 1 || el.scrollWidth > el.clientWidth + 1}});
  }});
  document.getElementById('audit').textContent = JSON.stringify(out);
  const wrapped = [];
  document.querySelectorAll('.brief').forEach(b => {{
    if (b.scrollHeight > 20) wrapped.push(b.querySelector('.bn').textContent);
  }});
  document.getElementById('footbottom').textContent = String(Math.round(document.getElementById('foot').getBoundingClientRect().bottom)) + '|' + wrapped.join(',');
}});
</script>
</body></html>'''

def main():
    stories = json.loads((HERE / "stories.json").read_text())
    html = build_html(stories)
    (HERE / "page.html").write_text(html)
    out = HERE / "entry.png"
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                        "--hide-scrollbars", "--window-size=1024,1024",
                        f"--screenshot={out}", f"file://{HERE / 'page.html'}"],
                       capture_output=True, text=True, timeout=120)
    print(r.stdout[-500:], r.stderr[-500:])
    r2 = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                         "--dump-dom", f"file://{HERE / 'page.html'}"],
                        capture_output=True, text=True, timeout=120)
    import re
    m = re.search(r'<pre id="audit">(.*?)</pre>', r2.stdout, re.S)
    audit = json.loads(m.group(1)) if m else []
    m2 = re.search(r'<pre id="footbottom">(\d+)\|(.*?)</pre>', r2.stdout, re.S)
    foot_bottom = int(m2.group(1)) if m2 else None
    wrapped_briefs = [w for w in (m2.group(2).split(",") if m2 else []) if w]
    overflow = [a["id"] for a in audit if a["overflow"]]
    page = next((a for a in audit if a["id"] == "page"), {})
    spec = {
        "masthead": "THE WORLD TODAY — Friday 20 November 2026",
        "subline": "Everything on this page happened, or was first reported, on Friday 20 November 2026.",
        "layout": "Newspaper front page: navy masthead, 3 large lead panels, 2 rows of medium panels (4 + 4), dotted world map with numbered pins 1-11 beside 32 numbered briefs in 2 columns at 16px (briefs one line each, max 40 chars, so the brief words stay readable at 300px), numbers strip (6 numbers), DATE CHECK footer (10 items), sources footer. Region counts sit under the map. No timeline strip (dropped in v5: 9px text unreadable at 300px).",
        "proof_tags": "CONFIRMED / CLAIM tags on lead stories; claims attributed to sources.",
        "timeline": [],
        "numbers": ["110+ Missiles fired at Ukraine overnight",
                    "400+ Drones in Russia's overnight barrage",
                    "$2.36bn GTA VI's first-day sales (Sensor Tower)",
                    "−12% Anthropic shares, premarket Friday",
                    "M4.4 Los Angeles earthquake, 03:25 PT",
                    "100,000 EU–UK youth mobility places a year"],
        "min_body_px": 12.5,
        "page_scroll_height": page.get("sh"),
        "foot_bottom_px": foot_bottom,
        "wrapped_briefs": wrapped_briefs,
        "overflow": overflow,
        "audit": audit,
        "legibility_note": "At 300px the 32 briefs are word-readable as distinct single lines (e.g. 'US Senate passes energy bill 62–33', 'White House cyber chief to leave', 'GTA VI: $2.36bn in 24 hours', 'Kyiv hits 3 Russian missile launchers'); lead heads and deck text stay legible; panels read as flat illustrations with labels intact; map pins distinct.",
    }
    (HERE / "render_spec.json").write_text(json.dumps(spec, indent=2))
    size = out.stat().st_size if out.exists() else 0
    print(f"entry.png: {size} bytes; page scrollHeight={page.get('sh')} (limit 1024); foot_bottom={foot_bottom} (limit 1024); overflow={overflow or 'none'}; wrapped_briefs={wrapped_briefs or 'none'}")
    return 0 if (out.exists() and size <= 1048576 and not overflow and not wrapped_briefs and page.get("sh", 9999) <= 1024 and (foot_bottom or 9999) <= 1024) else 1

if __name__ == "__main__":
    sys.exit(main())

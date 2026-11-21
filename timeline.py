#!/usr/bin/env python3
"""Two-row UTC timeline for the news-image-20261120 front page (v3).

The strip is "THE DAY IN TIME": five clock items from Friday 20 November
2026, set at 16px in two rows (3 + 2) with their full labels. v2 set the
same five items at 12px on one row with zero horizontal slack
(scrollWidth == clientWidth); at the judged 300px downscale its words were
not reliably readable (12px -> ~3.5px). 16px is the size the 32 numbered
briefs already prove word-readable at 300px, so the timeline now matches
the briefs instead of shrinking below them.

Layout contract (enforced by the page audit in render.py and by
verify.py; a violation fails the render, it never ships silently):
  * every item stays on one line (white-space:nowrap) -- a wrapped item
    fails the render
  * right-edge slack >= MIN_SLACK_PX on every row -- each row's content
    must end at least 16px before the strip's right edge, so ordinary
    rendering variation cannot clip it
  * every item's font is TIMELINE_FONT_PX (16); verify.py requires >= 15

Clock times were verified live at build time: 01:25 is Kyiv local time
(first explosions), OVERNIGHT has no clock pinned (the Polish incursion
happened during the overnight barrage), 08:55 UTC is when the Anthropic
slide was first reported, 11:25 UTC is 03:25 PT (USGS), 21:00 UTC is the
16:00 ET NYSE close. All five fall on Friday 20 November 2026.

Build-time only: render.py imports this module and inlines its HTML and
CSS into page.html. The graded program (main.py) only copies entry.png.
"""

# (time label, event label). Order is chronological; the rows split 3 + 2.
TIMELINE_ITEMS = [
    ("01:25 KYIV", "Barrage"),
    ("OVERNIGHT", "Missiles enter Poland"),
    ("08:55 UTC", "Anthropic \u221212%"),
    ("11:25 UTC", "LA quake M4.4"),
    ("21:00 UTC", "Wall St down"),
]

TIMELINE_FONT_PX = 16
MIN_SLACK_PX = 16
MIN_FONT_PX = 15
# Items per row, in order. Five items split 3 + 2 so no row is crowded.
ROW_SPLIT = (3, 2)
ROW_GAP_PX = 28
ROW_GAP_Y_PX = 5


def timeline_rows(items=TIMELINE_ITEMS):
    """Split the items into rows per ROW_SPLIT, in chronological order."""
    rows, i = [], 0
    for count in ROW_SPLIT:
        rows.append(list(items[i:i + count]))
        i += count
    if i < len(items):
        rows.append(list(items[i:]))
    return [r for r in rows if r]


def timeline_html(items=TIMELINE_ITEMS):
    """The timeline strip's inner HTML: header + two rows of items.

    Each row is a flex row, left-aligned with a fixed gap; rows never
    stretch their items to the edges, so the right-edge slack the guards
    measure is real empty space, not an artefact of justification.
    """
    rows_html = "".join(
        '<div class="tl-row">' + "".join(
            f"<span><b>{t}</b> \u00b7 {label}</span>" for t, label in row
        ) + "</div>"
        for row in timeline_rows(items)
    )
    return (f'<div class="tl-h">THE DAY IN TIME</div>'
            f'<div class="tl-rows">{rows_html}</div>')


def timeline_css():
    """CSS for the two-row timeline strip (inlined into page.html)."""
    return (
        f".timeline{{display:flex;gap:12px;align-items:center;margin-top:6px;"
        f"border-top:2px solid #10263f;border-bottom:1px solid #c9b18c;"
        f"padding:4px 0;font-size:{TIMELINE_FONT_PX}px;line-height:1.3}}"
        f".timeline .tl-h{{font-size:10px;font-weight:bold;letter-spacing:2px;"
        f"color:#a33;flex:none}}"
        f".timeline .tl-rows{{flex:1;min-width:0;display:flex;"
        f"flex-direction:column;gap:{ROW_GAP_Y_PX}px}}"
        f".timeline .tl-row{{display:flex;gap:{ROW_GAP_PX}px;"
        f"justify-content:flex-start;min-width:0}}"
        f".timeline .tl-row span{{white-space:nowrap}}"
        f".timeline .tl-row b{{color:#10263f}}"
    )


def timeline_audit_spec():
    """The timeline's declared shape, recorded in render_spec.json."""
    return {
        "font_px": TIMELINE_FONT_PX,
        "min_font_px": MIN_FONT_PX,
        "min_slack_px": MIN_SLACK_PX,
        "rows": [[t for t, _ in row] for row in timeline_rows()],
        "items": [f"{t} \u2014 {label}" for t, label in TIMELINE_ITEMS],
    }


def check_timeline_audit(audit):
    """Guard check on the browser-measured timeline audit (see render.py).

    `audit` is the JSON from the page's #tlaudit element: slack_px (the
    smallest right-edge slack across rows), min_font_px (computed font
    size of the items), items (count rendered), wrapped (items whose
    scrollWidth exceeded their box). Returns a list of problems; empty
    means the timeline passes. A missing or malformed audit is itself a
    problem: the guard must measure, never assume.
    """
    problems = []
    if not isinstance(audit, dict) or not audit:
        return ["timeline audit missing (no #tlaudit measurement)"]
    if audit.get("items") != len(TIMELINE_ITEMS):
        problems.append(
            f"timeline items rendered={audit.get('items')} "
            f"expected={len(TIMELINE_ITEMS)}")
    font = audit.get("min_font_px")
    if font is None or font < MIN_FONT_PX:
        problems.append(f"timeline font {font}px < {MIN_FONT_PX}px minimum")
    slack = audit.get("slack_px")
    if slack is None or slack < MIN_SLACK_PX:
        problems.append(f"timeline slack {slack}px < {MIN_SLACK_PX}px minimum")
    wrapped = audit.get("wrapped") or []
    if wrapped:
        problems.append(f"timeline items wrapped/clipped: {wrapped}")
    return problems

#!/usr/bin/env python3
"""Repo-local verification for the news-image-20261120 v4 entry.

Build-time only (not part of the graded program: main.py just copies
entry.png). Runs the full local gate for v4 and prints a PASS/FAIL table:

  1. determinism -- render.py twice, entry.png byte-identical both runs
  2. render spec -- min body font >= 10px, no overflow, foot_bottom <= 1024,
     page scrollHeight <= 1024, no wrapped briefs
  3. timeline -- font >= 15px, right-edge slack >= 16px on every row,
     all 5 items rendered, none wrapped or clipped (browser-measured)
  4. 300px downscale -- renders entry-300.png (300x300, in /tmp, not
     committed) so QA can view the judged size and confirm the timeline
     words actually read there

Usage: python3 verify.py   (run from the repo dir)
Exit 0 only when every check passes.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = HERE / "render_spec.json"
ENTRY = HERE / "entry.png"
DOWNSCALE = Path("/tmp/news-world-today-20-300.png")
TIMELINE_ITEMS = 5
TIMELINE_MIN_FONT_PX = 15
TIMELINE_MIN_SLACK_PX = 16


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_render():
    """Run render.py once; return (returncode, stdout tail)."""
    r = subprocess.run([sys.executable, str(HERE / "render.py")],
                       cwd=str(HERE), capture_output=True, text=True,
                       timeout=300)
    return r.returncode, (r.stdout + r.stderr)[-800:]


def make_downscale():
    """Render the judged 300px downscale for QA viewing (not committed)."""
    from PIL import Image
    im = Image.open(ENTRY)
    im.resize((300, 300), Image.LANCZOS).save(DOWNSCALE)
    return DOWNSCALE


def main():
    problems, notes = [], []

    # 1. Determinism: two renders, byte-identical entry.png.
    hashes = []
    for run in (1, 2):
        rc, tail = run_render()
        if rc != 0:
            problems.append(f"render.py run {run} exited {rc}: {tail.strip()}")
            break
        hashes.append(sha256(ENTRY))
    if len(hashes) == 2:
        if hashes[0] == hashes[1]:
            notes.append(f"determinism: run1 = run2 = {hashes[0][:12]}")
        else:
            problems.append(
                f"non-deterministic render: {hashes[0][:12]} != {hashes[1][:12]}")

    # 2. Render spec: fonts, overflow, foot position, wrapped briefs.
    if not SPEC.exists():
        problems.append("render_spec.json missing (render.py did not finish)")
        spec = {}
    else:
        spec = json.loads(SPEC.read_text())
    if spec:
        if spec.get("min_body_px", 0) < 10:
            problems.append(f"min_body_px {spec.get('min_body_px')} < 10")
        if spec.get("overflow"):
            problems.append(f"overflow: {spec.get('overflow')}")
        foot = spec.get("foot_bottom_px")
        if foot is None or foot > 1024:
            problems.append(f"foot_bottom {foot}px > 1024")
        else:
            notes.append(f"foot_bottom {foot}px (limit 1024)")
        if spec.get("page_scroll_height", 9999) > 1024:
            problems.append(
                f"page scrollHeight {spec.get('page_scroll_height')} > 1024")
        if spec.get("wrapped_briefs"):
            problems.append(f"wrapped briefs: {spec.get('wrapped_briefs')}")

    # 3. Timeline guards (browser-measured, via render.py's #tlaudit).
    tl = spec.get("timeline_audit", {}) if spec else {}
    if not tl:
        problems.append("timeline audit missing from render_spec.json")
    else:
        if tl.get("items") != TIMELINE_ITEMS:
            problems.append(
                f"timeline items {tl.get('items')} != {TIMELINE_ITEMS}")
        font = tl.get("min_font_px")
        if font is None or font < TIMELINE_MIN_FONT_PX:
            problems.append(
                f"timeline font {font}px < {TIMELINE_MIN_FONT_PX}px minimum")
        else:
            notes.append(f"timeline font {font}px")
        slack = tl.get("slack_px")
        if slack is None or slack < TIMELINE_MIN_SLACK_PX:
            problems.append(
                f"timeline slack {slack}px < {TIMELINE_MIN_SLACK_PX}px minimum")
        else:
            notes.append(f"timeline slack {slack}px (min {TIMELINE_MIN_SLACK_PX})")
        if tl.get("wrapped"):
            problems.append(f"timeline items wrapped: {tl.get('wrapped')}")

    # 4. Entry file: PNG magic, <= 1 MiB, exactly 1024x1024 (S01/S09 mirror),
    #    then the 300px downscale for QA.
    if ENTRY.exists():
        data = ENTRY.read_bytes()
        if data[:8] != b"\x89PNG\r\n\x1a\n":
            problems.append("entry.png is not a PNG (bad magic bytes)")
        if len(data) > 1048576:
            problems.append(f"entry.png {len(data)} bytes > 1 MiB")
        else:
            notes.append(f"entry.png {len(data)} bytes (limit 1 MiB)")
        from PIL import Image
        size = Image.open(ENTRY).size
        if size != (1024, 1024):
            problems.append(f"entry.png dimensions {size} != (1024, 1024)")
        make_downscale()
        notes.append(f"300px downscale: {DOWNSCALE}")
    else:
        problems.append("entry.png missing after render")

    for n in notes:
        print(f"  ok   {n}")
    for p in problems:
        print(f"  FAIL {p}")
    print(f"== v4 verify: {'PASS' if not problems else 'FAIL'} "
          f"({len(problems)} problem(s))")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())

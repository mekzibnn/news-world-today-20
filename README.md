[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/mekzibnn/news-world-today-20/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/mekzibnn/news-world-today-20/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

# The World Today — Friday 20 November 2026

A one-page newspaper front page summing up the world's news of
Friday 20 November 2026: 43 stories across 8 regions, with the day's
lead stories (Russia's biggest barrage hits Kyiv; Russian missiles
enter Polish airspace; a Houthi missile hits Riyadh's PIF tower), a
"Where it happened" world map with numbered pins, the day in numbers,
and a date check listing the stories that were first reported on
19 November and so were deliberately left out.

Entry for the [make.fun bounty](https://make.fun/bounty/news-image-20261120)
"Sum up 20 November's world news in one image".

## How the image was built

- `stories.json` — the 43 stories (11 lead stories with drawn panels, 32
  numbered briefs) plus the 10 date-check exclusions. Every lead story was
  checked against at least two independent sources; claims are attributed
  on the page (CONFIRMED / CLAIM tags with the source).
- `render.py` — builds `page.html` from `stories.json` (inline SVG panels,
  system fonts, no network) and screenshots it at exactly 1024x1024 with
  headless Chromium, with an overflow audit. Run it to regenerate
  `entry.png`.
- `main.py` — the entry program: a standard-library-only copy of
  `entry.png` to `/output/entry.png`. Deterministic by construction — two
  runs write identical bytes.

## Files

- `main.py` — entry program (Python 3.13, standard library only)
- `entry.png` — the image (1024x1024, PNG)
- `stories.json` — the news data
- `render.py`, `page.html` — the build pipeline
- `LICENSE` — MIT

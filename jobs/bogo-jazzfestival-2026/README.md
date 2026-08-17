# Bogø Jazzfestival 2026 — A5 program

Print-ready A5 program (148 × 210 mm) based on last year’s InDesign layout, with this year’s manuscript text.

The builder works in **raster** at **400 dpi** so type can be sheared to match last year’s bands (upright stems, baseline following the magenta rails — right side up). The print PDF embeds those images.

## Output

- `Bogo-Jazzfestival-2026-program.pdf` — 2 pages, A5 trim, 400 dpi
- `Bogo-Jazzfestival-2026-program-p1.png` / `-p2.png` — same pages as PNG

Rebuild:

```bash
pip install -r jobs/bogo-jazzfestival-2026/requirements.txt
python3 jobs/bogo-jazzfestival-2026/build_program.py
```

Fonts are Impact + Impress BT, extracted from the 2025 file.

## Sources

- `source-2025-design.pdf` — last year’s printed program (layout, colours, ticket boxes, logo)
- `source-2026-text.pdf` — this year’s Word manuscript (line-up, prices, sponsors)

Optional: drop a cleaner raster of last year’s pages into this folder as `source-2025-p1.png` and `source-2025-p2.png` (PNG/TIFF/JPEG). Chat-attached photos do not land in the repo; GitHub or a folder drop does. Any high-res A5 is fine; the script scales to 400 dpi. A manuscript raster is not needed.

## What changed vs 2025

- Dates: **3–5 September 2026** (Thursday–Saturday)
- Line-up: Jacob Fischer Trio, Baun on Beatles, Dynamic, Sophisticated Ladies
- No Børnejazz (ticket G is now Sophisticated Ladies; ticket H removed)
- Ticket prices A–G from the 2026 manuscript
- Saturday dinner copy and program sponsor list updated

## Date note

The Word manuscript header says **3.–5. september 2026**, which is Thursday–Saturday in 2026. The program body still had Friday as the 5th and Saturday as the 6th (last year’s day-of-month). Those were aligned to **Friday 4** and **Saturday 5** so weekday and date match. Confirm with the customer before print if they intended something else.

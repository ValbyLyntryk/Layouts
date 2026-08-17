# Bogø Jazzfestival 2026 — A5 program

Print-ready A5 program (148 × 210 mm) based on last year’s InDesign layout, with this year’s manuscript text.

## Output

`Bogo-Jazzfestival-2026-program.pdf` — 2 pages, same trim as 2025.

Rebuild:

```bash
python3 jobs/bogo-jazzfestival-2026/build_program.py
```

Requires PyMuPDF (`pip install pymupdf`). Fonts are extracted from the 2025 file (Impact + Impress BT).

## What changed vs 2025

- Dates: **3–5 September 2026** (Thursday–Saturday)
- Line-up: Jacob Fischer Trio, Baun on Beatles, Dynamic, Sophisticated Ladies
- No Børnejazz (ticket G is now Sophisticated Ladies; ticket H removed)
- Ticket prices A–G from the 2026 manuscript
- Saturday dinner copy and program sponsor list updated

## Date note

The Word manuscript header says **3.–5. september 2026**, which is Thursday–Saturday in 2026. The program body still had Friday as the 5th and Saturday as the 6th (last year’s day-of-month). Those were aligned to **Friday 4** and **Saturday 5** so weekday and date match. Confirm with the customer before print if they intended something else.

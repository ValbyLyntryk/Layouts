#!/usr/bin/env python3
"""Build the 2026 Bogø Jazzfestival A5 program from last year's InDesign layout."""

from __future__ import annotations

import math
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source-2025-design.pdf"
OUTPUT = ROOT / "Bogo-Jazzfestival-2026-program.pdf"
IMPACT_PATH = ROOT / "fonts" / "Impact.ttf"
IMPRESS_PATH = ROOT / "fonts" / "ImpressBT-Regular.ttf"

PAGE_W = 419.528
PAGE_H = 595.276

GREEN = (0.0, 0.721004068851471, 0.0)
YELLOW = (0.885999858379364, 0.9369955062866211, 0.10998702794313431)
MAGENTA = (0.9260395169258118, 0.0, 0.548180341720581)
BLUE = (0x40 / 255, 0x7D / 255, 0xC0 / 255)
YELLOW_TEXT = (0xE2 / 255, 0xEF / 255, 0x1C / 255)
WHITE = (1.0, 1.0, 1.0)
ORANGE_HEAD = (0xFA / 255, 0xA6 / 255, 0x19 / 255)
PRACTICAL_YELLOW = (0xFD / 255, 0xD9 / 255, 0x11 / 255)

ANGLE_DEG = -3.0
SLANT_K = -0.052336
MAX_LINE = PAGE_W - 24

FONT_FILES = {
    "impact": IMPACT_PATH,
    "impress": IMPRESS_PATH,
}

# Exact yellow-band polygons from the 2025 file
PAGE1_BANDS = [
    # welcome
    [(0.0, 116.62), (PAGE_W, 94.63), (PAGE_W, 155.79), (0.0, 177.77)],
    # mid (was Børnejazz; now Friday evening)
    [(0.0, 277.11), (PAGE_W, 248.65), (PAGE_W, 336.50), (0.0, 367.09)],
    # lower (Saturday afternoon musicians)
    [(0.0, 435.89), (PAGE_W, 419.69), (PAGE_W, 497.63), (0.0, 515.72)],
]


def rot_matrix(deg: float = ANGLE_DEG) -> pymupdf.Matrix:
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return pymupdf.Matrix(c, s, -s, c, 0, 0)


def register_fonts(page: pymupdf.Page) -> None:
    for name, path in FONT_FILES.items():
        page.insert_font(fontname=name, fontfile=str(path))


def text_width(fontname: str, text: str, size: float) -> float:
    font = pymupdf.Font(fontfile=str(FONT_FILES[fontname]))
    return font.text_length(text, fontsize=size)


def draw_text(
    page: pymupdf.Page,
    fontname: str,
    text: str,
    origin: tuple[float, float],
    size: float,
    color: tuple[float, float, float],
    slant: bool = True,
    angle: float = ANGLE_DEG,
) -> None:
    pt = pymupdf.Point(*origin)
    morph = (pt, rot_matrix(angle)) if slant else None
    page.insert_text(pt, text, fontname=fontname, fontsize=size, color=color, morph=morph)


def draw_centered(
    page: pymupdf.Page,
    fontname: str,
    text: str,
    y: float,
    size: float,
    color: tuple[float, float, float],
    slant: bool = True,
    x_center: float | None = None,
    angle: float = ANGLE_DEG,
) -> None:
    w = text_width(fontname, text, size)
    cx = PAGE_W / 2 if x_center is None else x_center
    draw_text(page, fontname, text, (cx - w / 2, y), size, color, slant=slant, angle=angle)


def wrap_parts(parts: list[str], fontname: str, size: float, max_width: float = MAX_LINE) -> list[str]:
    lines: list[str] = []
    current = ""
    for part in parts:
        trial = part if not current else f"{current}   {part}"
        if text_width(fontname, trial, size) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = part
    if current:
        lines.append(current)
    return lines


def draw_band(page: pymupdf.Page, pts: list[tuple[float, float]]) -> None:
    shape = page.new_shape()
    shape.draw_polyline([pymupdf.Point(*p) for p in pts])
    shape.finish(color=None, fill=YELLOW, closePath=True, width=0)
    shape.commit()
    top_l, top_r, bot_r, bot_l = pts
    dx = 20
    page.draw_line(
        pymupdf.Point(top_l[0] - dx, top_l[1] - SLANT_K * dx),
        pymupdf.Point(top_r[0] + dx, top_r[1] + SLANT_K * dx),
        color=MAGENTA,
        width=4,
    )
    page.draw_line(
        pymupdf.Point(bot_l[0] - dx, bot_l[1] - SLANT_K * dx),
        pymupdf.Point(bot_r[0] + dx, bot_r[1] + SLANT_K * dx),
        color=MAGENTA,
        width=4,
    )


def rounded_cover(page: pymupdf.Page, rect: pymupdf.Rect, fill, radius: float = 0.18) -> None:
    page.draw_rect(rect, color=None, fill=fill, width=0, radius=radius)


def redact_matching(page: pymupdf.Page, prefixes: tuple[str, ...]) -> None:
    for block in page.get_text("dict")["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                if text and any(text.startswith(p) or p in text for p in prefixes):
                    page.add_redact_annot(pymupdf.Rect(span["bbox"]), fill=False, text="")
    page.apply_redactions(images=2, graphics=0)


def build_page1(doc: pymupdf.Document) -> None:
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    register_fonts(page)
    page.draw_rect(page.rect + (-8, -8, 8, 8), color=None, fill=GREEN, width=0)
    for band in PAGE1_BANDS:
        draw_band(page, band)

    # Header — same positions/sizes as 2025
    draw_text(page, "impact", "BOGØ", (12.17, 64.94), 57.3, YELLOW_TEXT)
    draw_text(page, "impact", " JAZZFESTIVAL", (152.23, 57.60), 42.7, YELLOW_TEXT)
    # Same left origin as 2025 so "2026" is not pushed into the yellow band
    draw_text(page, "impact", "3-5. SEPTEMBER 2026", (31.43, 98.38), 37.9, YELLOW_TEXT)

    draw_centered(page, "impact", "Velkommen til en herlig koncert med noget", 143.19, 22.2, BLUE)
    draw_centered(page, "impact", "af det bedste og mest uforfalskede JAZZ!", 167.18, 22.2, BLUE)

    draw_centered(page, "impact", "program:", 199.57, 26.8, YELLOW_TEXT)

    # Thursday — green, same slot as 2025 (one musician line so it stays above the yellow)
    draw_centered(page, "impact", "Torsdag d. 3. sep. Kl. 20.00, Jacob Fischer Trio", 236.58, 21.2, WHITE)
    draw_centered(
        page,
        "impact",
        "Jacob Fischer: Guitar   Zier Romme Larsen: Piano   Rosa Salamon: Kontrabas/vokal",
        257.93,
        10.8,
        WHITE,
    )

    # Friday — middle yellow (was Børnejazz)
    draw_centered(page, "impact", "Fredag d. 4. sep. Kl. 20.00:", 299.98, 21.2, BLUE)
    draw_centered(page, "impact", "Baun on Beatles", 323.69, 21.2, BLUE)
    draw_centered(
        page,
        "impact",
        "Søren Baun: Piano/vocal   Andreas Møllerhøj: Kontrabas   Ulrik Brohuus: Trommer",
        344.22,
        10.8,
        BLUE,
    )

    # Saturday 16.00 — fill the 2025 Friday-evening green gap, musicians on the yellow
    draw_centered(page, "impact", "Lørdag d. 5. sep. Kl. 16.00:", 378.0, 21.6, WHITE)
    draw_centered(page, "impact", "Dynamic", 402.0, 21.6, WHITE)
    dyn_musicians = wrap_parts(
        [
            "Paul Kim: Bass/dirigent",
            "Kirstine Dahlberg: Sopran",
            "Katrine Aidt Rømhild: Mezzo",
            "Anne Rørbæk: Mezzo/alto",
            "Hasse Tang: Trommer",
            "Niels Willhelm Knudsen: Bass",
            "Frederik Rejle: Guitar",
        ],
        "impact",
        12.5,
    )
    y = 448.0
    for line in dyn_musicians:
        draw_centered(page, "impact", line, y, 12.5, BLUE, angle=-2.0)
        y += 16.5

    # Saturday 19.30 — bottom green, same slot as 2025
    draw_centered(
        page,
        "impact",
        "Lørdag d. 5. sep. Kl. 19.30: Sophisticated Ladies",
        545.08,
        20.2,
        WHITE,
        angle=-2.0,
    )
    sat_musicians = wrap_parts(
        [
            "Marie Louise Schmidt: Piano",
            "Helle Marstrand: Kontrabas",
            "Benita Haastrup: Percussion/trommer",
        ],
        "impact",
        12.5,
    )
    y = 565.72
    for line in sat_musicians:
        draw_centered(page, "impact", line, y, 12.5, WHITE, angle=-2.0)
        y += 14.2


def update_page2(page: pymupdf.Page) -> None:
    redact_matching(
        page,
        (
            "PRAKTISKE",
            "Dørene",
            "Torsdagens menu",
            "Lørdag åbnes",
            "SPONSORER",
            "ÅRETS FESTIVAL",
            "REALMÆGLERNE",
            "FILTENBORG",
            "MØNS BANK",
            "OVE ODDERMOSES",
            "ØERNES BILSYN",
            "Møns Auto",
            "BOGØ BILCENTER",
            "XL MØENS",
            "WÆHRENS",
            "PARTYLINE",
            "BARTOF",
            "Billet",
            "Hele festivalen",
            "Fredag og lørdag",
            "Lørdag med mad",
            "Torsdag med mad",
            "Fredag med mad",
            "Torsdag og fredag",
            "Børnejazz",
            "Michael Kwabena",
            "Jan Harbeck",
        ),
    )
    register_fonts(page)

    # Cover burned-in ticket prices with page green so magenta outlines remain
    boxes = [
        pymupdf.Rect(10, 136, 136, 171),   # A
        pymupdf.Rect(13, 187, 139, 221),   # B
        pymupdf.Rect(16, 234, 138, 269),   # C
        pymupdf.Rect(153, 129, 269, 163),  # D
        pymupdf.Rect(155, 177, 271, 211),  # E
        pymupdf.Rect(156, 227, 272, 261),  # F
        pymupdf.Rect(289, 121, 408, 160),  # G
    ]
    for rect in boxes:
        rounded_cover(page, rect, GREEN)

    # Remove Billet H (no eighth ticket this year)
    page.draw_rect(pymupdf.Rect(276, 160, PAGE_W + 6, 218), color=None, fill=GREEN, width=0)

    # Practical info — 2025 origins, Børnejazz line dropped
    draw_text(page, "impact", "PRAKTISKE OPLYSNINGER", (20.98, 55.23), 34.6, PRACTICAL_YELLOW, slant=False)
    draw_centered(
        page,
        "impact",
        "Dørene åbnes kl. 18.00 torsdag og fredag, vi spiser kl. 19.00 begge dage.",
        75.13,
        12.6,
        WHITE,
        slant=False,
    )
    draw_centered(
        page,
        "impact",
        "Torsdag: Chicken in Forest og fredag: Gumbo",
        85.93,
        12.6,
        WHITE,
        slant=False,
    )
    draw_centered(
        page,
        "impact",
        "Lørdag åbnes dørene kl. 15.00 og vores jazzthai middag",
        104.47,
        12.6,
        WHITE,
        slant=False,
    )
    draw_centered(
        page,
        "impact",
        "med græsk inspiration på grillen skal nydes fra kl. 18.00.",
        122.88,
        12.6,
        WHITE,
        slant=False,
    )

    tickets = [
        ((13.64, 155.50), (14.14, 165.70), "Billet A: ...................750,-", "Hele festivalen med mad alle dage", 8.12),
        ((16.17, 207.86), (16.67, 218.06), "Billet B: ...................645,-", "Fredag og lørdag, med mad begge dage", 8.12),
        ((18.51, 256.30), (19.01, 266.49), "Billet C: ...................450,-", "Lørdag med mad", 8.12),
        ((153.59, 150.12), (152.71, 160.39), "Billet D: .................250,-", "Torsdag med mad", 8.12),
        ((154.57, 198.76), (155.06, 208.96), "Billet E: ...................250,-", "Fredag med mad", 8.12),
        ((156.91, 247.33), (157.38, 256.92), "Billet F: ...................450,-", "Torsdag og fredag med mad begge dage", 7.64),
        ((289.70, 140.49), (290.19, 150.68), "Billet G: ...................175,-", "Sophisticated Ladies", 8.12),
    ]
    for (p1, p2, label, desc, dsize) in tickets:
        draw_text(page, "impact", label, p1, 14.22, WHITE)
        draw_text(page, "impact", desc, p2, dsize, WHITE)

    draw_text(page, "impact", "SPONSORER FOR", (16.15, 335.06), 29.2, ORANGE_HEAD, slant=False)
    draw_text(page, "impact", "ÅRETS FESTIVAL", (19.66, 363.44), 29.2, ORANGE_HEAD, slant=False)

    sponsors = [
        "REALMÆGLERNE STEGE, ARO MURER,",
        "BOGØ VARESERVICE,",
        "MØNS BANK, BRUGSEN PÅ BOGØ,",
        "MORTEN HØYER",
        "OVE ODDERMOSES EFTF. APS,",
        "ØERNES BILSYN STEGE,",
        "BOGØ BILCENTER,",
        "XL MØENS TØMMERHANDEL,",
        "WÆHRENS PIANO, TINA´S BINDERI,",
        "PARTYLINE-ABSOLUTFEST.DK,",
        "BARTOF CAFÉ, PIANO VÆRKSTEDET,",
        "MATTSSON & MCGEHEE",
    ]
    y = 392.32
    box_cx = 113.5
    step = 17.4
    for line in sponsors:
        w = text_width("impress", line, 12.8)
        x = max(12.0, box_cx - w / 2)
        draw_text(page, "impress", line, (x, y), 12.8, WHITE, slant=False)
        y += step


def main() -> None:
    src = pymupdf.open(SOURCE)
    out = pymupdf.open()
    build_page1(out)
    out.insert_pdf(src, from_page=1, to_page=1)
    update_page2(out[-1])
    out.save(OUTPUT, deflate=True, garbage=4)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()

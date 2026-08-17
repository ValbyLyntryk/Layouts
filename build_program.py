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
TICKET_FILL = (0.0, 159 / 255, 77 / 255)

ANGLE_DEG = -3.0
SLANT_K = -0.052336

FONT_FILES = {
    "impact": IMPACT_PATH,
    "impress": IMPRESS_PATH,
}

# Exact yellow-band polygons from the 2025 file
PAGE1_BANDS = [
    # welcome
    [(0.0, 116.62), (PAGE_W, 94.63), (PAGE_W, 155.79), (0.0, 177.77)],
    # mid (was Børnejazz)
    [(0.0, 277.11), (PAGE_W, 248.65), (PAGE_W, 336.50), (0.0, 367.09)],
    # lower (was Saturday afternoon)
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
) -> None:
    pt = pymupdf.Point(*origin)
    morph = (pt, rot_matrix()) if slant else None
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
) -> None:
    w = text_width(fontname, text, size)
    cx = PAGE_W / 2 if x_center is None else x_center
    draw_text(page, fontname, text, (cx - w / 2, y), size, color, slant=slant)


def draw_band(page: pymupdf.Page, pts: list[tuple[float, float]]) -> None:
    shape = page.new_shape()
    shape.draw_polyline([pymupdf.Point(*p) for p in pts])
    shape.finish(color=None, fill=YELLOW, closePath=True, width=0)
    shape.commit()
    # Magenta rails along the top and bottom edges, extended past trim
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
    draw_text(page, "impact", "BOGØ", (12.2, 64.9), 57.3, YELLOW_TEXT)
    draw_text(page, "impact", " JAZZFESTIVAL", (152.2, 57.6), 42.7, YELLOW_TEXT)
    draw_centered(page, "impact", "3-5. SEPTEMBER 2026", 88.0, 34.0, YELLOW_TEXT)

    # Welcome
    draw_centered(page, "impact", "Velkommen til en herlig koncert med noget", 143.2, 20.4, BLUE)
    draw_centered(page, "impact", "af det bedste og mest uforfalskede JAZZ!", 167.2, 20.4, BLUE)

    draw_centered(page, "impact", "program:", 199.6, 26.8, YELLOW_TEXT)

    # Thursday (green)
    draw_centered(page, "impact", "Torsdag d. 3. sep. Kl. 20.00, Jacob Fischer Trio", 232.0, 18.4, WHITE)
    draw_centered(
        page,
        "impact",
        "Jacob Fischer: Guitar   Zier Romme Larsen: Piano   Rosa Salamon: Kontrabas/vokal",
        252.0,
        10.4,
        WHITE,
    )

    # Friday (middle yellow)
    draw_centered(page, "impact", "Fredag d. 4. sep. Kl. 20.00:", 300.0, 20.0, BLUE)
    draw_centered(page, "impact", "Baun on Beatles", 324.0, 22.0, BLUE)
    draw_centered(
        page,
        "impact",
        "Søren Baun: Piano/vocal   Andreas Møllerhøj: Kontrabas   Ulrik Brohuus: Trommer",
        334.0,
        10.6,
        BLUE,
    )

    # Saturday 16.00 Dynamic (lower yellow)
    draw_centered(page, "impact", "Lørdag d. 5. sep. Kl. 16.00: Dynamic", 456.0, 17.4, BLUE)
    draw_centered(
        page,
        "impact",
        "Paul Kim: Bass/dirigent   Kirstine Dahlberg: Sopran   Katrine Aidt Rømhild: Mezzo",
        474.0,
        10.0,
        BLUE,
    )
    draw_centered(
        page,
        "impact",
        "Anne Rørbæk: Mezzo/alto   Hasse Tang: Trommer",
        488.0,
        10.0,
        BLUE,
    )
    draw_centered(
        page,
        "impact",
        "Niels Willhelm Knudsen: Bass   Frederik Rejle: Guitar",
        502.0,
        10.0,
        BLUE,
    )

    # Saturday 19.30 (bottom green)
    draw_centered(page, "impact", "Lørdag d. 5. sep. Kl. 19.30: Sophisticated Ladies", 545.0, 17.6, WHITE)
    draw_centered(
        page,
        "impact",
        "Marie Louise Schmidt: Piano   Helle Marstrand: Kontrabas",
        564.0,
        11.2,
        WHITE,
    )
    draw_centered(page, "impact", "Benita Haastrup: Percussion/trommer", 580.0, 11.2, WHITE)


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

    # Hide burned-in ticket prices inside the photo boxes; keep the pink outlines
    boxes = [
        pymupdf.Rect(8, 134, 138, 173),   # A
        pymupdf.Rect(11, 185, 141, 223),  # B
        pymupdf.Rect(14, 232, 140, 271),  # C
        pymupdf.Rect(151, 127, 271, 165),  # D
        pymupdf.Rect(153, 175, 273, 213),  # E
        pymupdf.Rect(154, 225, 274, 263),  # F
        pymupdf.Rect(287, 119, 410, 162),  # G
    ]
    for rect in boxes:
        rounded_cover(page, rect, TICKET_FILL)

    # Remove Billet H entirely (no kids/evening split this year)
    page.draw_rect(pymupdf.Rect(276, 160, PAGE_W + 6, 218), color=None, fill=GREEN, width=0)

    # Practical info — same origins as 2025, without Børnejazz
    draw_centered(page, "impact", "PRAKTISKE OPLYSNINGER", 50.0, 30.0, YELLOW_TEXT)
    draw_centered(
        page,
        "impact",
        "Dørene åbnes kl. 18.00 torsdag og fredag, vi spiser kl. 19.00 begge dage.",
        70.0,
        11.3,
        WHITE,
    )
    draw_centered(page, "impact", "Torsdag: Chicken in Forest og fredag: Gumbo", 85.0, 11.3, WHITE)
    draw_centered(
        page,
        "impact",
        "Lørdag åbnes dørene kl. 15.00 og vores jazzthai middag",
        100.0,
        10.8,
        WHITE,
    )
    draw_centered(
        page,
        "impact",
        "med græsk inspiration på grillen skal nydes fra kl. 18.00.",
        114.0,
        10.8,
        WHITE,
    )

    tickets = [
        ((13.6, 155.5), (14.1, 165.7), "Billet A: ...................750,-", "Hele festivalen med mad alle dage", 8.12),
        ((16.2, 207.9), (16.7, 218.1), "Billet B: ...................645,-", "Fredag og lørdag, med mad begge dage", 8.12),
        ((18.5, 256.3), (19.0, 266.5), "Billet C: ...................450,-", "Lørdag med mad", 8.12),
        ((153.6, 150.1), (152.7, 160.4), "Billet D: .................250,-", "Torsdag med mad", 8.12),
        ((154.6, 198.8), (155.1, 209.0), "Billet E: ...................250,-", "Fredag med mad", 8.12),
        ((156.9, 247.3), (157.4, 256.9), "Billet F: ...................450,-", "Torsdag og fredag med mad begge dage", 7.64),
        ((289.7, 140.5), (290.2, 154.0), "Billet G: ...................175,-", "Sophisticated Ladies", 8.12),
    ]
    for (p1, p2, label, desc, dsize) in tickets:
        draw_text(page, "impact", label, p1, 14.22, WHITE)
        draw_text(page, "impact", desc, p2, dsize, WHITE)

    # Sponsors — keep the original pink gradient, rewrite the program list
    draw_centered(page, "impact", "SPONSORER FOR", 335.1, 26.0, ORANGE_HEAD, slant=False, x_center=111)
    draw_centered(page, "impact", "ÅRETS FESTIVAL", 360.0, 26.0, ORANGE_HEAD, slant=False, x_center=111)

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
        "BARTOF CAFÉ,",
        "PIANO VÆRKSTEDET",
        "MATTSSON & MCGEHEE",
    ]
    y = 392.0
    for line in sponsors:
        draw_centered(page, "impress", line, y, 11.2, WHITE, slant=False, x_center=111)
        y += 15.4


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

#!/usr/bin/env python3
"""Build the 2026 Bogø Jazzfestival A5 program as a print-resolution raster.

Last year's PDF is rendered (or an optional PNG/TIFF is used). New type is
sheared in image space so stems stay upright and the baseline follows the
yellow bands and ticket boxes — the same treatment as the 2025 InDesign file.
"""

from __future__ import annotations

import io
import math
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SOURCE_PDF = ROOT / "source-2025-design.pdf"
OUTPUT_PDF = ROOT / "Bogo-Jazzfestival-2026-program.pdf"
OUTPUT_P1 = ROOT / "Bogo-Jazzfestival-2026-program-p1.png"
OUTPUT_P2 = ROOT / "Bogo-Jazzfestival-2026-program-p2.png"
IMPACT_PATH = ROOT / "fonts" / "Impact.ttf"
IMPRESS_PATH = ROOT / "fonts" / "ImpressBT-Regular.ttf"

# A5 trim in PDF points (1/72 in). 400 dpi is enough for print of this type size.
PAGE_W = 419.528
PAGE_H = 595.276
DPI = 400
SCALE = DPI / 72.0
PX_W = round(PAGE_W * SCALE)
PX_H = round(PAGE_H * SCALE)

# Colours sampled from a 400 dpi render of the 2025 PDF (after flattening).
GREEN = (0, 162, 79)
YELLOW = (223, 227, 37)
MAGENTA = (236, 0, 140)
BLUE = (64, 125, 192)
YELLOW_TEXT = (226, 239, 28)
WHITE = (255, 255, 255)
ORANGE_HEAD = (250, 166, 25)
PRACTICAL_YELLOW = (253, 218, 17)

# 2025 type is sheared, not rotated: letter stems stay vertical, the baseline
# follows the bands (dy/dx). Negative k = right side of the line goes up.
SHEAR_TOP = math.tan(math.radians(-3.0))
SHEAR_MID = math.tan(math.radians(-3.8))
SHEAR_LOW = math.tan(math.radians(-2.2))
SHEAR_BOT = math.tan(math.radians(-2.0))
SHEAR_TICKET = math.tan(math.radians(-3.3))

PAGE1_BANDS = [
    [(0.0, 116.62), (PAGE_W, 94.63), (PAGE_W, 155.79), (0.0, 177.77)],
    [(0.0, 277.11), (PAGE_W, 248.65), (PAGE_W, 336.50), (0.0, 367.09)],
    [(0.0, 435.89), (PAGE_W, 419.69), (PAGE_W, 497.63), (0.0, 515.72)],
]

SLANT_K = -0.052336
MAX_LINE = PAGE_W - 24

FONT_FILES = {
    "impact": IMPACT_PATH,
    "impress": IMPRESS_PATH,
}

_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def pt(value: float) -> float:
    return value * SCALE


def pt_xy(x: float, y: float) -> tuple[float, float]:
    return (x * SCALE, y * SCALE)


def load_font(name: str, size_pt: float) -> ImageFont.FreeTypeFont:
    px = max(1, round(size_pt * SCALE))
    key = (name, px)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(str(FONT_FILES[name]), px)
    return _font_cache[key]


def text_width_pt(name: str, text: str, size_pt: float) -> float:
    font = load_font(name, size_pt)
    return font.getlength(text) / SCALE


def wrap_parts(parts: list[str], fontname: str, size: float, max_width: float = MAX_LINE) -> list[str]:
    lines: list[str] = []
    current = ""
    for part in parts:
        trial = part if not current else f"{current}   {part}"
        if text_width_pt(fontname, trial, size) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = part
    if current:
        lines.append(current)
    return lines


def shear_layer(layer: Image.Image, k: float, origin: tuple[float, float]) -> Image.Image:
    """Vertical shear around origin: stems stay upright, baseline slope is k (dy/dx)."""
    x0, _y0 = origin
    # PIL AFFINE maps output -> input: y_in = -k * x_out + y_out + k * x0
    data = (1, 0, 0, -k, 1, k * x0)
    return layer.transform(layer.size, Image.Transform.AFFINE, data, resample=Image.Resampling.BICUBIC)


def draw_text(
    im: Image.Image,
    text: str,
    origin_pt: tuple[float, float],
    fontname: str,
    size_pt: float,
    fill: tuple[int, int, int],
    shear: float = 0.0,
    anchor: str = "ls",
) -> None:
    """Draw text. origin_pt is PDF-space; anchor ls/ms is baseline left/center."""
    font = load_font(fontname, size_pt)
    pos = pt_xy(*origin_pt)
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(pos, text, font=font, fill=fill + (255,), anchor=anchor)
    if shear:
        layer = shear_layer(layer, shear, pos)
    if im.mode != "RGBA":
        rgba = im.convert("RGBA")
        rgba.alpha_composite(layer)
        im.paste(rgba.convert(im.mode))
    else:
        im.alpha_composite(layer)


def draw_centered(
    im: Image.Image,
    text: str,
    y_pt: float,
    fontname: str,
    size_pt: float,
    fill: tuple[int, int, int],
    shear: float = 0.0,
    x_center_pt: float | None = None,
) -> None:
    cx = PAGE_W / 2 if x_center_pt is None else x_center_pt
    draw_text(im, text, (cx, y_pt), fontname, size_pt, fill, shear=shear, anchor="ms")


def poly_px(pts: list[tuple[float, float]]) -> list[tuple[int, int]]:
    return [(round(x * SCALE), round(y * SCALE)) for x, y in pts]


def draw_band(draw: ImageDraw.ImageDraw, pts: list[tuple[float, float]]) -> None:
    draw.polygon(poly_px(pts), fill=YELLOW)
    top_l, top_r, bot_r, bot_l = pts
    dx = 20
    width = max(2, round(4 * SCALE))

    def edge(p0: tuple[float, float], p1: tuple[float, float], sign: float) -> None:
        x0, y0 = p0
        x1, y1 = p1
        a = pt_xy(x0 - dx, y0 - SLANT_K * dx * sign)
        b = pt_xy(x1 + dx, y1 + SLANT_K * dx * sign)
        draw.line([a, b], fill=MAGENTA, width=width)

    edge(top_l, top_r, 1)
    edge(bot_l, bot_r, 1)


def load_source_page(index: int) -> Image.Image:
    """Prefer a user-supplied raster; otherwise render the 2025 PDF at DPI."""
    for ext in ("png", "tif", "tiff", "jpg", "jpeg"):
        path = ROOT / f"source-2025-p{index + 1}.{ext}"
        if path.exists():
            im = Image.open(path).convert("RGB")
            if im.size != (PX_W, PX_H):
                im = im.resize((PX_W, PX_H), Image.Resampling.LANCZOS)
            print(f"Using {path.name} ({im.size[0]}×{im.size[1]})")
            return im
    src = pymupdf.open(SOURCE_PDF)
    pix = src[index].get_pixmap(matrix=pymupdf.Matrix(SCALE, SCALE), alpha=False)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    if im.size != (PX_W, PX_H):
        im = im.resize((PX_W, PX_H), Image.Resampling.LANCZOS)
    return im


def cover_rect(im: Image.Image, rect_pt: tuple[float, float, float, float], color: tuple[int, int, int], pad_pt: float = 1.2) -> None:
    x0, y0, x1, y1 = rect_pt
    box = [
        round((x0 - pad_pt) * SCALE),
        round((y0 - pad_pt) * SCALE),
        round((x1 + pad_pt) * SCALE),
        round((y1 + pad_pt) * SCALE),
    ]
    ImageDraw.Draw(im).rectangle(box, fill=color)


def _is_green(rgb: tuple[int, ...]) -> bool:
    r, g, b = rgb[:3]
    return r < 50 and 130 < g < 210 and 40 < b < 130


def _is_sponsor_purple(rgb: tuple[int, ...]) -> bool:
    r, g, b = rgb[:3]
    return r > 90 and b > 70 and g < r - 10 and r < 250


def cover_spans_local(im: Image.Image, page: pymupdf.Page, prefixes: tuple[str, ...], pad_pt: float = 2.0) -> None:
    """Paint out matching 2025 text. Tickets/practical use page green; sponsors keep the gradient."""
    px = im.load()
    w, h = im.size
    practical_bottom = int(130 * SCALE)
    ticket_bottom = int(280 * SCALE)
    sponsor_left = int(230 * SCALE)
    for block in page.get_text("dict")["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                if not text or not any(text.startswith(p) or p in text for p in prefixes):
                    continue
                x0, y0, x1, y1 = span["bbox"]
                ix0 = max(0, int((x0 - pad_pt) * SCALE))
                iy0 = max(0, int((y0 - pad_pt) * SCALE))
                ix1 = min(w, int((x1 + pad_pt) * SCALE))
                iy1 = min(h, int((y1 + pad_pt) * SCALE))
                cy = (iy0 + iy1) // 2
                if cy < ticket_bottom:
                    ImageDraw.Draw(im).rectangle([ix0, iy0, ix1, iy1], fill=GREEN)
                    continue
                for y in range(iy0, iy1):
                    sample = GREEN
                    for sx in (max(0, ix0 - 24), 40, 70, min(w - 1, ix1 + 24)):
                        cand = px[sx, y]
                        if cy > ticket_bottom and ix0 < sponsor_left and _is_sponsor_purple(cand):
                            sample = cand
                            break
                        if _is_green(cand):
                            sample = cand
                            break
                    for x in range(ix0, ix1):
                        px[x, y] = sample


def build_page1() -> Image.Image:
    im = Image.new("RGB", (PX_W, PX_H), GREEN)
    draw = ImageDraw.Draw(im)
    for band in PAGE1_BANDS:
        draw_band(draw, band)

    draw_text(im, "BOGØ", (12.17, 64.94), "impact", 57.3, YELLOW_TEXT, shear=SHEAR_TOP)
    draw_text(im, " JAZZFESTIVAL", (152.23, 57.60), "impact", 42.7, YELLOW_TEXT, shear=SHEAR_TOP)
    draw_text(im, "3-5. SEPTEMBER 2026", (31.43, 98.38), "impact", 37.9, YELLOW_TEXT, shear=SHEAR_TOP)

    draw_centered(im, "Velkommen til en herlig koncert med noget", 143.19, "impact", 22.2, BLUE, shear=SHEAR_TOP)
    draw_centered(im, "af det bedste og mest uforfalskede JAZZ!", 167.18, "impact", 22.2, BLUE, shear=SHEAR_TOP)
    draw_centered(im, "program:", 199.57, "impact", 26.8, YELLOW_TEXT, shear=SHEAR_TOP)

    draw_centered(im, "Torsdag d. 3. sep. Kl. 20.00, Jacob Fischer Trio", 236.58, "impact", 21.2, WHITE, shear=SHEAR_TOP)
    draw_centered(
        im,
        "Jacob Fischer: Guitar   Zier Romme Larsen: Piano   Rosa Salamon: Kontrabas/vokal",
        257.93,
        "impact",
        10.8,
        WHITE,
        shear=SHEAR_TOP,
    )

    draw_centered(im, "Fredag d. 4. sep. Kl. 20.00:", 299.98, "impact", 21.2, BLUE, shear=SHEAR_MID)
    draw_centered(im, "Baun on Beatles", 323.69, "impact", 21.2, BLUE, shear=SHEAR_MID)
    draw_centered(
        im,
        "Søren Baun: Piano/vocal   Andreas Møllerhøj: Kontrabas   Ulrik Brohuus: Trommer",
        344.22,
        "impact",
        10.8,
        BLUE,
        shear=SHEAR_MID,
    )

    draw_centered(im, "Lørdag d. 5. sep. Kl. 16.00:", 378.0, "impact", 21.6, WHITE, shear=SHEAR_TOP)
    draw_centered(im, "Dynamic", 402.0, "impact", 21.6, WHITE, shear=SHEAR_TOP)
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
        draw_centered(im, line, y, "impact", 12.5, BLUE, shear=SHEAR_LOW)
        y += 16.5

    draw_centered(
        im,
        "Lørdag d. 5. sep. Kl. 19.30: Sophisticated Ladies",
        545.08,
        "impact",
        20.2,
        WHITE,
        shear=SHEAR_BOT,
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
        draw_centered(im, line, y, "impact", 12.5, WHITE, shear=SHEAR_BOT)
        y += 14.2

    return im


PAGE2_PREFIXES = (
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
    "NORDEA",
)


def build_page2() -> Image.Image:
    im = load_source_page(1)
    src = pymupdf.open(SOURCE_PDF)
    cover_spans_local(im, src[1], PAGE2_PREFIXES, pad_pt=2.2)

    # Remove Billet H (no eighth ticket this year), including its magenta outline.
    cover_rect(im, (276, 160, PAGE_W + 6, 218), GREEN, pad_pt=0.8)

    draw_text(im, "PRAKTISKE OPLYSNINGER", (20.98, 55.23), "impact", 34.6, PRACTICAL_YELLOW)
    draw_centered(im, "Dørene åbnes kl. 18.00 torsdag og fredag, vi spiser kl. 19.00 begge dage.", 75.13, "impact", 12.6, WHITE)
    draw_centered(im, "Torsdag: Chicken in Forest og fredag: Gumbo", 85.93, "impact", 12.6, WHITE)
    draw_centered(im, "Lørdag åbnes dørene kl. 15.00 og vores jazzthai middag", 104.47, "impact", 12.6, WHITE)
    draw_centered(im, "med græsk inspiration på grillen skal nydes fra kl. 18.00.", 122.88, "impact", 12.6, WHITE)

    tickets = [
        ((13.64, 155.50), (14.14, 165.70), "Billet A: ...................750,-", "Hele festivalen med mad alle dage", 8.12),
        ((16.17, 207.86), (16.67, 218.06), "Billet B: ...................645,-", "Fredag og lørdag, med mad begge dage", 8.12),
        ((18.51, 256.30), (19.01, 266.49), "Billet C: ...................450,-", "Lørdag med mad", 8.12),
        ((153.59, 150.12), (152.71, 160.39), "Billet D: .................250,-", "Torsdag med mad", 8.12),
        ((154.57, 198.76), (155.06, 208.96), "Billet E: ...................250,-", "Fredag med mad", 8.12),
        ((156.91, 247.33), (157.38, 256.92), "Billet F: ...................450,-", "Torsdag og fredag med mad begge dage", 7.64),
        ((289.70, 140.49), (290.19, 150.68), "Billet G: ...................175,-", "Sophisticated Ladies", 8.12),
    ]
    for p1, p2, label, desc, dsize in tickets:
        draw_text(im, label, p1, "impact", 14.22, WHITE, shear=SHEAR_TICKET)
        draw_text(im, desc, p2, "impact", dsize, WHITE, shear=SHEAR_TICKET)

    draw_text(im, "SPONSORER FOR", (16.15, 335.06), "impact", 29.2, ORANGE_HEAD)
    draw_text(im, "ÅRETS FESTIVAL", (19.66, 363.44), "impact", 29.2, ORANGE_HEAD)

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
    for line in sponsors:
        w = text_width_pt("impress", line, 12.8)
        x = max(12.0, box_cx - w / 2)
        draw_text(im, line, (x, y), "impress", 12.8, WHITE)
        y += 17.4

    return im


def save_print_pdf(pages: list[Image.Image], path: Path) -> None:
    doc = pymupdf.open()
    for im in pages:
        page = doc.new_page(width=PAGE_W, height=PAGE_H)
        buf = io.BytesIO()
        im.save(buf, format="PNG", dpi=(DPI, DPI))
        page.insert_image(page.rect, stream=buf.getvalue())
    doc.save(path, deflate=True)
    print(f"Wrote {path}")


def main() -> None:
    p1 = build_page1()
    p2 = build_page2()
    p1.save(OUTPUT_P1, dpi=(DPI, DPI))
    p2.save(OUTPUT_P2, dpi=(DPI, DPI))
    print(f"Wrote {OUTPUT_P1} and {OUTPUT_P2} ({PX_W}×{PX_H} px @ {DPI} dpi)")
    save_print_pdf([p1, p2], OUTPUT_PDF)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the 2026 Bogø Jazzfestival A5 program as a print-resolution raster.

Last year's PDF is rendered (or an optional PNG/TIFF is used). New type is
sheared in image space so stems stay upright and the baseline follows the
yellow bands and ticket boxes — the same treatment as the 2025 InDesign file.
"""

from __future__ import annotations

import io
import math
from dataclasses import dataclass
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

# 2025 shears every band the same way: right side up (image dy/dx < 0).
# Letter stems stay vertical; the baseline follows the magenta rails.
SHEAR = math.tan(math.radians(-3.0))
SHEAR_TICKET = math.tan(math.radians(-3.25))
CX = PAGE_W / 2.0

# Padding is the air from ink to the band edge (or to the neighbouring magenta).
PAD_YELLOW = 13.0
PAD_GREEN = 11.0
MARGIN_MIN_TOP = 16.0
MARGIN_MIN_BOT = 12.0
# Heavy Impact caps read high in a band; sit the block a hair lower.
OPTICAL_DOWN = 2.2

MAX_LINE = PAGE_W - 28

# Kept for page 2 overlays that still use the old names.
SHEAR_GREEN = SHEAR
SHEAR_GREEN_BOT = SHEAR
SHEAR_YELLOW = SHEAR
SHEAR_YELLOW_MID = SHEAR
SHEAR_YELLOW_LOW = SHEAR

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


@dataclass
class LineSpec:
    text: str
    size: float
    fill: tuple[int, int, int]
    font: str = "impact"
    leading: float | None = None
    gap_after: float = 0.0


@dataclass
class Section:
    name: str
    kind: str  # "yellow" | "green" | "header"
    lines: list[LineSpec]
    pad: float
    y0: float = 0.0
    y1: float = 0.0
    first_baseline: float = 0.0
    baselines: list[float] | None = None


def ink_ls(fontname: str, text: str, size: float) -> tuple[float, float]:
    """Ink top/bottom relative to baseline, in pt (top is negative)."""
    font = load_font(fontname, size)
    _x0, y0, _x1, y1 = font.getbbox(text or "H", anchor="ls")
    return y0 / SCALE, y1 / SCALE


def measure_lines(lines: list[LineSpec]) -> tuple[float, float, list[float]]:
    """Return (ink height, first baseline from ink top, baselines from first)."""
    if not lines:
        return 0.0, 0.0, []
    bases = [0.0]
    for i, line in enumerate(lines[:-1]):
        nxt = lines[i + 1]
        lead = line.leading if line.leading is not None else max(line.size, nxt.size) * 1.12
        bases.append(bases[-1] + lead + line.gap_after)
    top0, _ = ink_ls(lines[0].font, lines[0].text, lines[0].size)
    _, botn = ink_ls(lines[-1].font, lines[-1].text, lines[-1].size)
    ink_top = bases[0] + top0
    ink_bot = bases[-1] + botn
    return ink_bot - ink_top, -ink_top, bases


def band_poly(y_top: float, y_bot: float, k: float = SHEAR) -> list[tuple[float, float]]:
    """Parallelogram whose top/bottom sit at y_top/y_bot on the page centre."""

    def yat(yc: float, x: float) -> float:
        return yc + k * (x - CX)

    return [
        (0.0, yat(y_top, 0.0)),
        (PAGE_W, yat(y_top, PAGE_W)),
        (PAGE_W, yat(y_bot, PAGE_W)),
        (0.0, yat(y_bot, 0.0)),
    ]


def layout_sections(sections: list[Section]) -> None:
    """Stack sections, keep equal pad in each band, dump leftover into page margins."""

    def pack() -> tuple[list[float], list[float], list[list[float]], float]:
        heights: list[float] = []
        firsts: list[float] = []
        bases_all: list[list[float]] = []
        for sec in sections:
            h, first, bases = measure_lines(sec.lines)
            heights.append(h)
            firsts.append(first)
            bases_all.append(bases)
        content = sum(h + 2 * sec.pad for h, sec in zip(heights, sections))
        room = PAGE_H - MARGIN_MIN_TOP - MARGIN_MIN_BOT - content
        return heights, firsts, bases_all, room

    heights, firsts, bases_all, room = pack()
    if room < -0.5:
        scale = (PAGE_H - MARGIN_MIN_TOP - MARGIN_MIN_BOT) / sum(
            h + 2 * sec.pad for h, sec in zip(heights, sections)
        )
        for sec in sections:
            sec.pad = max(7.0, sec.pad * scale)
        heights, firsts, bases_all, room = pack()
    elif room > 1.0:
        extra = room / (2 * len(sections))
        for sec in sections:
            sec.pad += extra
        heights, firsts, bases_all, room = pack()

    y = MARGIN_MIN_TOP + max(0.0, room) * 0.45
    for sec, h, first, bases in zip(sections, heights, firsts, bases_all):
        sec.y0 = y
        sec.y1 = y + sec.pad + h + sec.pad
        nudge = 0.0 if sec.kind == "header" else OPTICAL_DOWN
        sec.first_baseline = y + sec.pad + first + nudge
        sec.baselines = [sec.first_baseline + b for b in bases]
        y = sec.y1
    last = sections[-1]
    trim_bot = PAGE_H - 6.0
    if last.y1 > trim_bot:
        last.y1 = trim_bot
        h = measure_lines(last.lines)[0]
        last.pad = (last.y1 - last.y0 - h) / 2
        first = measure_lines(last.lines)[1]
        nudge = 0.0 if last.kind == "header" else OPTICAL_DOWN
        last.first_baseline = last.y0 + last.pad + first + nudge
        last.baselines = [last.first_baseline + b for b in measure_lines(last.lines)[2]]


def draw_section_text(im: Image.Image, sec: Section) -> None:
    assert sec.baselines is not None
    for line, y in zip(sec.lines, sec.baselines):
        draw_centered(im, line.text, y, line.font, line.size, line.fill, shear=SHEAR)


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
    shear_x: float | None = None,
) -> None:
    """Draw text. origin_pt is PDF-space; anchor ls/ms is baseline left/center.

    shear_x is the page-x (pt) the shear is taken around. Page 1 bands are
    defined about the centre, so body type should shear about CX too.
    """
    font = load_font(fontname, size_pt)
    pos = pt_xy(*origin_pt)
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(pos, text, font=font, fill=fill + (255,), anchor=anchor)
    if shear:
        sx = pt(shear_x) if shear_x is not None else pos[0]
        layer = shear_layer(layer, shear, (sx, pos[1]))
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
    draw_text(im, text, (cx, y_pt), fontname, size_pt, fill, shear=shear, anchor="ms", shear_x=CX)


def poly_px(pts: list[tuple[float, float]]) -> list[tuple[int, int]]:
    return [(round(x * SCALE), round(y * SCALE)) for x, y in pts]


def draw_band(draw: ImageDraw.ImageDraw, pts: list[tuple[float, float]]) -> None:
    draw.polygon(poly_px(pts), fill=YELLOW)
    top_l, top_r, bot_r, bot_l = pts
    dx = 20
    width = max(2, round(4 * SCALE))

    def edge(p0: tuple[float, float], p1: tuple[float, float]) -> None:
        x0, y0 = p0
        x1, y1 = p1
        k = (y1 - y0) / (x1 - x0)
        a = pt_xy(x0 - dx, y0 - k * dx)
        b = pt_xy(x1 + dx, y1 + k * dx)
        draw.line([a, b], fill=MAGENTA, width=width)

    edge(top_l, top_r)
    edge(bot_l, bot_r)


def load_source_page(index: int) -> Image.Image:
    """Prefer a user-supplied raster; otherwise render the 2025 PDF at DPI."""
    for name in (f"source-2025-p{index + 1}", f"source-2025-page{index + 1}", f"last-year-p{index + 1}"):
        for ext in ("png", "tif", "tiff", "jpg", "jpeg"):
            path = ROOT / f"{name}.{ext}"
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


def header_lockup_x() -> tuple[float, float, float, float, float]:
    """BOGØ / JAZZFESTIVAL / date sizes and x positions, 2025-style left lockup."""
    bogo_size, jazz_size, date_size = 56.0, 41.5, 35.5
    left = 14.0
    bogo_w = text_width_pt("impact", "BOGØ", bogo_size)
    jazz_x = left + bogo_w + 4.0
    return left, jazz_x, bogo_size, jazz_size, date_size


def draw_header(im: Image.Image, sec: Section) -> None:
    left, jazz_x, bogo_size, jazz_size, date_size = header_lockup_x()
    bogo_y = sec.first_baseline
    bogo_top, _ = ink_ls("impact", "BOGØ", bogo_size)
    jazz_top, _ = ink_ls("impact", "JAZZFESTIVAL", jazz_size)
    jazz_y = bogo_y + bogo_top - jazz_top  # cap-tops aligned
    date_y = sec.baselines[1] if sec.baselines and len(sec.baselines) > 1 else bogo_y + 36
    draw_text(im, "BOGØ", (left, bogo_y), "impact", bogo_size, YELLOW_TEXT, shear=SHEAR, shear_x=CX)
    draw_text(im, "JAZZFESTIVAL", (jazz_x, jazz_y), "impact", jazz_size, YELLOW_TEXT, shear=SHEAR, shear_x=CX)
    draw_text(im, "3-5. SEPTEMBER 2026", (left, date_y), "impact", date_size, YELLOW_TEXT, shear=SHEAR, shear_x=CX)


def build_page1() -> Image.Image:
    dyn_mus = wrap_parts(
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
        12.0,
    )
    ladies_mus = wrap_parts(
        [
            "Marie Louise Schmidt: Piano",
            "Helle Marstrand: Kontrabas",
            "Benita Haastrup: Percussion/trommer",
        ],
        "impact",
        12.0,
    )

    _, _, bogo_size, _, date_size = header_lockup_x()

    # Yellow / green / yellow / green / yellow: each yellow wraps one block
    # of copy with equal air above and below the ink.
    sections = [
        Section(
            "header",
            "header",
            [
                LineSpec("BOGØ", bogo_size, YELLOW_TEXT, leading=35.0),
                LineSpec("3-5. SEPTEMBER 2026", date_size, YELLOW_TEXT),
            ],
            pad=PAD_GREEN + 3,
        ),
        Section(
            "welcome",
            "yellow",
            [
                LineSpec("Velkommen til en herlig koncert med noget", 21.2, BLUE, leading=23.5),
                LineSpec("af det bedste og mest uforfalskede JAZZ!", 21.2, BLUE),
            ],
            pad=PAD_YELLOW,
        ),
        Section(
            "thursday",
            "green",
            [
                LineSpec("program:", 23.5, YELLOW_TEXT, leading=26.5, gap_after=3.0),
                LineSpec(
                    "Torsdag d. 3. sep. Kl. 20.00, Jacob Fischer Trio",
                    20.4,
                    WHITE,
                    leading=20.0,
                    gap_after=3.5,
                ),
                LineSpec(
                    "Jacob Fischer: Guitar   Zier Romme Larsen: Piano   Rosa Salamon: Kontrabas/vokal",
                    10.8,
                    WHITE,
                ),
            ],
            pad=PAD_GREEN,
        ),
        Section(
            "friday",
            "yellow",
            [
                LineSpec("Fredag d. 4. sep. Kl. 20.00:", 20.8, BLUE, leading=22.8),
                LineSpec("Baun on Beatles", 20.8, BLUE, leading=20.5, gap_after=3.0),
                LineSpec(
                    "Søren Baun: Piano/vocal   Andreas Møllerhøj: Kontrabas   Ulrik Brohuus: Trommer",
                    10.8,
                    BLUE,
                ),
            ],
            pad=PAD_YELLOW,
        ),
        Section(
            "dynamic",
            "green",
            [
                LineSpec("Lørdag d. 5. sep. Kl. 16.00:", 20.8, WHITE, leading=22.8),
                LineSpec("Dynamic", 20.8, WHITE, leading=20.5, gap_after=3.5),
                *[LineSpec(line, 12.0, WHITE, leading=15.2) for line in dyn_mus],
            ],
            pad=PAD_GREEN,
        ),
        Section(
            "ladies",
            "yellow",
            [
                LineSpec("Lørdag d. 5. sep. Kl. 19.30:", 20.2, BLUE, leading=22.2),
                LineSpec("Sophisticated Ladies", 20.2, BLUE, leading=20.0, gap_after=3.0),
                *[LineSpec(line, 12.0, BLUE, leading=15.2) for line in ladies_mus],
            ],
            pad=PAD_YELLOW,
        ),
    ]
    layout_sections(sections)

    im = Image.new("RGB", (PX_W, PX_H), GREEN)
    draw = ImageDraw.Draw(im)
    for sec in sections:
        if sec.kind == "yellow":
            draw_band(draw, band_poly(sec.y0, sec.y1))

    for sec in sections:
        if sec.kind == "header":
            draw_header(im, sec)
        else:
            draw_section_text(im, sec)

    for sec in sections:
        print(f"  p1 {sec.name:14} {sec.kind:6} {sec.y0:6.1f}–{sec.y1:6.1f}  pad={sec.pad:.1f}")

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

    draw_text(im, "PRAKTISKE OPLYSNINGER", (20.98, 55.23), "impact", 34.6, PRACTICAL_YELLOW, shear=SHEAR_GREEN)
    draw_centered(im, "Dørene åbnes kl. 18.00 torsdag og fredag, vi spiser kl. 19.00 begge dage.", 75.13, "impact", 12.6, WHITE, shear=SHEAR_GREEN)
    draw_centered(im, "Torsdag: Chicken in Forest og fredag: Gumbo", 85.93, "impact", 12.6, WHITE, shear=SHEAR_GREEN)
    draw_centered(im, "Lørdag åbnes dørene kl. 15.00 og vores jazzthai middag", 104.47, "impact", 12.6, WHITE, shear=SHEAR_GREEN)
    draw_centered(im, "med græsk inspiration på grillen skal nydes fra kl. 18.00.", 122.88, "impact", 12.6, WHITE, shear=SHEAR_GREEN)

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

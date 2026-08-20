#!/usr/bin/env python3
"""Print-ready A4 check cards for AB Molbech driftsplan 2026 (udkast)."""

from __future__ import annotations

from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "AB-Molbech-tjekkort-2026-udkast.pdf"
PREVIEW_DIR = ROOT / "preview"

A4_W, A4_H = 595.28, 841.89
MM = 72 / 25.4

FONTDIR = ROOT / "fonts"
if not (FONTDIR / "Inter-Regular.ttf").exists():
    FONTDIR = Path("/usr/share/fonts/truetype/macos")
FONT_FILES = {
    "r": FONTDIR / "Inter-Regular.ttf",
    "m": FONTDIR / "Inter-Medium.ttf",
    "sb": FONTDIR / "Inter-SemiBold.ttf",
    "b": FONTDIR / "Inter-Bold.ttf",
    "i": FONTDIR / "Inter-Italic.ttf",
}

# Warm paper / pine / copper — courtyard association, not corporate blue.
PINE = (0.110, 0.239, 0.196)
PINE_MID = (0.165, 0.345, 0.286)
COPPER = (0.722, 0.361, 0.220)
INK = (0.102, 0.102, 0.094)
MUTED = (0.380, 0.365, 0.345)
RULE = (0.780, 0.745, 0.700)
HAIR = (0.860, 0.835, 0.800)
PAPER = (0.973, 0.957, 0.925)
ROW_ALT = (0.945, 0.925, 0.890)
WHITE = (1, 1, 1)
CREAM = (0.988, 0.976, 0.957)

FREQ_COLOR = {
    "daglig": (0.239, 0.494, 0.651),
    "ugentlig": (0.184, 0.435, 0.306),
    "månedlig": COPPER,
    "kvartal": (0.165, 0.478, 0.463),
    "halvår": (0.651, 0.486, 0.176),
    "årlig": PINE,
    "bygning": (0.420, 0.325, 0.267),
    "oversigt": PINE,
    "kloak": (0.310, 0.365, 0.420),
}


def rgb(t: tuple[float, float, float]) -> tuple[float, float, float]:
    return t


def font(name: str) -> pymupdf.Font:
    return pymupdf.Font(fontfile=str(FONT_FILES[name]))


def tw(name: str, text: str, size: float) -> float:
    return font(name).text_length(text, fontsize=size)


def wrap(name: str, text: str, size: float, width: float) -> list[str]:
    words = text.replace("\n", " ").split()
    if not words:
        return [""]
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = word if not cur else f"{cur} {word}"
        if tw(name, trial, size) <= width:
            cur = trial
            continue
        if cur:
            lines.append(cur)
        cur = word
    if cur:
        lines.append(cur)
    return lines or [""]


def register(page: pymupdf.Page) -> None:
    for key, path in FONT_FILES.items():
        page.insert_font(fontname=f"i{key}", fontfile=str(path))


def txt(
    page: pymupdf.Page,
    name: str,
    text: str,
    x: float,
    y: float,
    size: float,
    color=INK,
) -> None:
    page.insert_text(
        pymupdf.Point(x, y),
        text,
        fontname=f"i{name}",
        fontsize=size,
        color=color,
    )


def fill_rect(page: pymupdf.Page, r: pymupdf.Rect, color) -> None:
    page.draw_rect(r, color=None, fill=color, width=0)


class CardBook:
    def __init__(self) -> None:
        self.doc = pymupdf.open()
        self.page_no = 0
        self.toc: list[tuple[str, int]] = []
        self.ml = 20 * MM  # binder holes
        self.mr = 16 * MM  # clears the colour thumb
        self.mt = 12 * MM
        self.mb = 14 * MM

    @property
    def xr(self) -> float:
        return A4_W - self.mr

    def new_page(self, paper=PAPER) -> pymupdf.Page:
        page = self.doc.new_page(width=A4_W, height=A4_H)
        register(page)
        fill_rect(page, page.rect, paper)
        self.page_no += 1
        return page

    def footer(self, page: pymupdf.Page, label: str) -> None:
        y = A4_H - 9 * MM
        page.draw_line(
            pymupdf.Point(self.ml, y - 4),
            pymupdf.Point(self.xr, y - 4),
            color=RULE,
            width=0.4,
        )
        txt(page, "r", "AB Molbech  ·  Driftsplan 2026  ·  Udkast til gennemsyn", self.ml, y + 8, 7, MUTED)
        num = f"{label}   {self.page_no}"
        txt(page, "m", num, self.xr - tw("m", num, 7), y + 8, 7, MUTED)

    def thumb(self, page: pymupdf.Page, kind: str) -> None:
        color = FREQ_COLOR[kind]
        fill_rect(page, pymupdf.Rect(A4_W - 5.5 * MM, 0, A4_W, A4_H), color)

    def header_bar(self, page: pymupdf.Page, kind: str, title: str, subtitle: str) -> float:
        color = FREQ_COLOR[kind]
        top = pymupdf.Rect(0, 0, A4_W, 28 * MM)
        fill_rect(page, top, color)
        txt(page, "m", "AB MOLBECH  ·  DRIFTSPLAN 2026", self.ml, 10 * MM, 8, (0.92, 0.90, 0.86))
        txt(page, "b", title, self.ml, 18.5 * MM, 16, WHITE)
        txt(page, "r", subtitle, self.ml, 24.5 * MM, 8.5, (0.93, 0.91, 0.86))
        self.thumb(page, kind)
        return 32 * MM

    def field(self, page: pymupdf.Page, x: float, y: float, label: str, w: float, h: float = 16) -> None:
        txt(page, "m", label.upper(), x, y - 3, 6.2, MUTED)
        page.draw_rect(
            pymupdf.Rect(x, y, x + w, y + h),
            color=RULE,
            fill=WHITE,
            width=0.6,
        )

    def write_box(self, page: pymupdf.Page, r: pymupdf.Rect, hint: str = "") -> None:
        page.draw_rect(r, color=RULE, fill=WHITE, width=0.5)
        if hint:
            txt(page, "r", hint, r.x0 + 3, r.y1 - 4, 5.4, (0.72, 0.70, 0.66))

    def checkbox(self, page: pymupdf.Page, x: float, y: float, size: float = 9) -> None:
        page.draw_rect(
            pymupdf.Rect(x, y, x + size, y + size),
            color=PINE,
            fill=WHITE,
            width=0.8,
        )

    def save(self) -> None:
        self.doc.set_metadata(
            {
                "title": "AB Molbech — Driftsplan 2026 — Tjekkort (udkast)",
                "author": "Valby Lyntryk",
                "subject": "Tjekkort til dokumentation af driftsopgaver",
            }
        )
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(OUTPUT, deflate=True, garbage=4)
        print(f"Wrote {OUTPUT} ({self.page_no} pages)")


# ---------------------------------------------------------------------------
# Task lists (curated from Molbech_Driftsplan 2026.xlsx)
# ---------------------------------------------------------------------------

DAILY = [
    ("Tilgængelig alle hverdage kl. 07–16. Herefter akut vagttelefon hele døgnet.", "Total Ejendomsservice", ""),
    ("Vanding i tørre perioder (kun i sæson / efter behov).", "Total Ejendomsservice", "sæson"),
    ("Snerydning: fortov, gangarealer, kældertrapper og trin. Opstart inden kl. 07.", "Total Ejendomsservice (hele ugen)", "sæson"),
]

WEEKLY_A = [
    ("Tilstede mindst 3 × ugentligt på ejendommen (daglig vagttelefon).", "TE", ""),
    ("Græsplæner, klip.", "TE", ""),
    ("Ukrudt 6 × årligt (apr/maj/jun/aug/sep/okt). TE assisterer.", "Køge Bugt", "sæson"),
    ("Renhold af gangarealer, trapper, skakter m.m.", "TE", ""),
    ("Navneskilte, dørtelefon og postkasser.", "TE", ""),
    ("Sikre opdaterede opslagstavler.", "TE", ""),
    ("Lyskilder, dørpumper, lås og brikker — indstil/smør efter behov.", "TE", ""),
    ("Lyskilder på trapper og fællesarealer — udskift ved behov.", "TE", ""),
    ("Vaskeri: beboerbrikker.", "TE", ""),
    ("Vaskeri: indkøb og påfyldning af sæbe.", "TE", ""),
    ("Vaskeri: maskiner kontrolleres 3 × ugentligt. Bestil installatør ved fejl.", "TE", ""),
    ("Skralderum: renhold. Bestil tømning af glas, pap m.m.", "TE", ""),
    ("Porte: kontrol og dialog med portleverandør / vedligehold.", "TE", ""),
    ("Tjek at rengøring er gennemført af ABC.", "TE", ""),
    ("Motion: kontrollér rengøring.", "TE", ""),
]

WEEKLY_B = [
    ("Assistere beboere om driftsforhold. Hjælp til at bestille håndværker til mindre beboeropgaver.", "TE", ""),
    ("Assistere med adgang for håndværkere (via opbevarede beboernøgler).", "TE", ""),
    ("Information om driftsforhold via opslagstavler og SMS.", "TE", ""),
    ("Flyttesyn: sikre rapport til vurderingsmand / administrator.", "TE", "efter behov"),
    ("Festlokale: udleje, lejekontrakt, webkalender, udlevering af nøgler og tjek ved aflevering.", "TE", "efter behov"),
    ("Motion: opret/slet medlemsskab.", "TE", "efter behov"),
    ("Håndværkere: bestil opgaver, assistér og sikre adgang.", "TE", "efter behov"),
    ("Forsikringssager: dialog med mægler/selskab. Bestyrelse og administrator holdes orienteret.", "TE", "efter behov"),
    ("Forsikringssager: beboerinformation, hvis beboer er berørt.", "TE", "efter behov"),
]

MONTHLY = [
    ("Græsplæner, kanter", "TE"),
    ("Varmecentral — adgang for Bentsen VVS", "TE"),
    ("Bestille varer (toiletter, festlokale …)", "TE"),
    ("Fjerne graffiti", "TE"),
]

QUARTERLY = [
    ("Plæner: gødskning 2 × årligt (apr/aug) + eftersåning 1 × årligt (apr).", "Køge Bugt", "apr / aug"),
    ("Vaskeri: løbende service, så vaskerierne er driftssikre.", "TE", ""),
    ("Kontrollere dykpumper.", "TE?", ""),
]

HALFYEAR = [
    ("Klippe hæk (1 × årligt).", "Køge Bugt", "sommer"),
    ("Træ- og buskpleje, beskæring (feb + aug).", "Køge Bugt", "feb / aug"),
    ("Kældre: renhold — fejning / evt. støvsugning.", "TE", ""),
    ("Storskrald — bestil afhentning.", "TE", ""),
    ("Havemøbler: vedligehold + ud/ind af opbevaring.", "TE", "forår / efterår"),
    ("Legeplads: eftersyn + bestil udskiftning af sand efter behov.", "TE", ""),
]

YEARLY_DRIFT = [
    ("Fjerne løvfald (efterår).", "TE", "efterår"),
    ("Algebehandling af trappeskakter og gårdbelægning (maj).", "Køge Bugt", "maj"),
    ("Assistere foreningen med cykel- og barnevognsoprydning efter behov.", "TE", ""),
]

BUILDING = [
    (
        "01 — Tag",
        [
            ("Inspektion af tag fra loftsrum: utætheder og renhed af tagrender.", "Hvem?", "hvert år"),
            ("Inspektion fra loft af rygningsbånd mellem rygningsten og øverste række tegl.", "Hvem?", "hvert år"),
            ("Rensning af tagrender fra lift, hvis inspektion giver anledning.", "Hvem?", "2024 / 2026 / 2028"),
            ("Tagvinduer i trapperum og på tørrelofter/fællesrum smøres.", "Hvem?", "2024 / 2026 / 2028"),
            ("Rens og inspektion af paptag under tagaltaner.", "Hvem?", "2025 (næste efter behov)"),
        ],
    ),
    (
        "02 — Kælder / fundament",
        [
            ("Inspektion af kælder for vandindtrængen, utætte installationer og defekt puds.", "Hvem?", "hvert år"),
            ("Krybekælder: åbn lem, tjek for kloak-/skimmellugt og tegn på rotter.", "Hvem?", "hvert år"),
        ],
    ),
    (
        "03 — Facader / sokkel",
        [
            ("Inspektion af facader for sætningsrevner, revner i gesims/betonbånd og defekter ved tagnedløb.", "Hvem?", "hvert år"),
        ],
    ),
    (
        "04 — Vinduer",
        [
            ("Smøring og justering af hængsler og beslag på alle vinduer.", "Hvem?", "2024 / 2026 / 2028"),
        ],
    ),
    (
        "05 — Udvendige døre",
        [
            ("Smøring af dørpumper, cylindre og gående dele på døre til trapper og kældre.", "Hvem?", "hvert år"),
            ("Justering af dørpumper og slutblik. Udskift defekte dørpumper efter behov.", "Hvem?", "hvert år"),
        ],
    ),
    (
        "06 — Trapper",
        [
            ("Inspektion af terrazzo på indgangsreposer. Reparation inden vinter ved revner/skader.", "Hvem?", "hvert år"),
            ("Døre til lofter og kælder eftergås (samme som udvendige døre).", "Hvem?", "hvert år"),
        ],
    ),
    (
        "07 — Porte / gennemgange",
        [
            ("Portdøre eftergås (samme som udvendige døre).", "Valport", "hvert år"),
        ],
    ),
    (
        "11 — Varmeanlæg",
        [
            ("Udslamning af varmtvandsbeholder. (Frekvens afventer Bentsen VVS.)", "Bentsen VVS", "afventer"),
            ("Afkalkning af varmtvandsbeholder.", "Bentsen VVS", "hvert år"),
            ("Afkalkning af varmeveksler efter behov.", "Bentsen VVS", "2024 / 2027"),
            ("Aktivering af sikkerhedsventiler.", "Bentsen VVS", "hvert år"),
            ("Kontrol af temperaturer i varmecentral, herunder returtemperatur på brugsvand.", "Bentsen VVS", "hvert år"),
        ],
    ),
    (
        "12 — Brugsvand",
        [
            ("Trykhold- og trykøgningsanlæg.", "Bentsen VVS", "hvert år"),
        ],
    ),
    (
        "13 — Kloak",
        [
            ("Spuling af kloak. Interval justeres efter erfaring.", "Hvem?", "2024 / 2026 / 2028"),
            ("Spuling af dræn. Interval justeres efter erfaring.", "Hvem?", "2024 / 2027"),
            ("Oprensning af rensebrønde. Inspektion af meterbrønde. Rens/smør højvandslukker.", "Hvem?", "hvert år"),
            ("Kontrol af alarm og niveauvippe i drænpumpebrønde. Udskift batteri efter behov.", "Hvem?", "hvert år"),
        ],
    ),
    (
        "14 — Afløb",
        [
            ("Rensning af køkkenfaldstammer efter behov (anslået hvert 10. år).", "Bentsen VVS", "efter behov"),
            ("Kontrol af højvandslukker i vaskerier m.m.", "Bentsen VVS?", "hvert år"),
        ],
    ),
    (
        "16 — Ventilation",
        [
            ("Rensning af ventilationskanaler ved specialfirma. Sidst udført 4. kvartal 2025.", "specialfirma", "næste 2027"),
        ],
    ),
    (
        "17 — El / svagstrøm",
        [
            ("Test af fejlstrømsrelæ på fællesinstallationer.", "Hvem?", "hvert år"),
            ("Stikprøvekontrol af isolation (mærkning) på trappelys.", "Hvem?", "2026"),
        ],
    ),
]


def draw_cover(book: CardBook) -> None:
    page = book.new_page(paper=PINE)
    book.toc.append(("Forside", book.page_no))

    fill_rect(page, pymupdf.Rect(0, 0, 8 * MM, A4_H), COPPER)
    txt(page, "m", "ANDELSBOLIGFORENINGEN", 22 * MM, 38 * MM, 10, (0.78, 0.86, 0.82))
    txt(page, "b", "AB Molbech", 22 * MM, 58 * MM, 36, WHITE)
    page.draw_line(
        pymupdf.Point(22 * MM, 66 * MM),
        pymupdf.Point(118 * MM, 66 * MM),
        color=COPPER,
        width=2.2,
    )
    txt(page, "sb", "Driftsplan 2026", 22 * MM, 82 * MM, 22, (0.93, 0.91, 0.86))
    txt(page, "r", "Tjekkort til dokumentation", 22 * MM, 94 * MM, 16, WHITE)

    box = pymupdf.Rect(22 * MM, 118 * MM, A4_W - 22 * MM, 188 * MM)
    fill_rect(page, box, (0.090, 0.200, 0.165))
    intro = [
        "Kortene omsætter driftsplanen til et simpelt log-system:",
        "viceværten og leverandørerne kvitterer, når en opgave er udført.",
        "Bestyrelsen kan til enhver tid slå op og se dato for seneste udførelse.",
        "",
        "Dette er et udkast til gennemsyn — ret gerne inden tryk.",
    ]
    y = 130 * MM
    for line in intro:
        txt(page, "r", line, 28 * MM, y, 11, (0.90, 0.92, 0.88))
        y += 11.5

    y = 210 * MM
    items = [
        ("01", "Sådan bruges kortene"),
        ("02", "Oversigt — senest udført"),
        ("03", "Dagligt tjekkort (ugevis)"),
        ("04", "Ugentligt tjekkort"),
        ("05", "Måned · kvartal · halvår · år"),
        ("06", "Bygningsvedligehold + kloak/rottespærre"),
    ]
    txt(page, "m", "INDHOLD", 22 * MM, y, 8.5, (0.78, 0.86, 0.82))
    y += 10 * MM
    for num, label in items:
        txt(page, "sb", num, 22 * MM, y, 12, COPPER)
        txt(page, "r", label, 36 * MM, y, 12, WHITE)
        y += 9 * MM

    txt(page, "r", "Udkast  ·  august 2026  ·  sat op af Valby Lyntryk", 22 * MM, A4_H - 18 * MM, 9, (0.70, 0.80, 0.75))


def draw_howto(book: CardBook) -> None:
    page = book.new_page()
    book.toc.append(("Sådan bruges kortene", book.page_no))
    y = book.header_bar(
        page,
        "oversigt",
        "Sådan bruges kortene",
        "Til vicevært, leverandører og bestyrelse",
    )
    book.footer(page, "Vejledning")

    steps = [
        (
            "1",
            "Udfyld når opgaven er udført",
            "Sæt kryds, skriv dato og initialer. Ved gentagne opgaver opdateres feltet Senest udført hver gang.",
        ),
        (
            "2",
            "Læg kortene frem",
            "Kortene ligger i ringbindet på ejendommen, så bestyrelsen kan se dokumentationen uden at spørge.",
        ),
        (
            "3",
            "Sæson og «ikke aktuelt»",
            "Snerydning, vanding og ukrudt er sæson. Er opgaven ikke aktuel i perioden, skriv et tankestreg (–) — ikke blankt.",
        ),
        (
            "4",
            "Efter behov",
            "Nogle ugentlige linjer er status (flyttesyn, forsikring, festlokale). Er der intet aktuelt, skriv «ingen».",
        ),
        (
            "5",
            "Mangler i planen",
            "Flere bygningsopgaver har endnu ingen ansvarlig (Hvem?). Udfyldes når Bentsen VVS, gartner og øvrige har kommenteret.",
        ),
    ]
    for num, title, body in steps:
        fill_rect(page, pymupdf.Rect(book.ml, y, book.ml + 9 * MM, y + 9 * MM), PINE)
        txt(page, "b", num, book.ml + 2.8 * MM, y + 6.4 * MM, 12, WHITE)
        txt(page, "sb", title, book.ml + 13 * MM, y + 4.2 * MM, 12, PINE)
        lines = wrap("r", body, 9.5, A4_W - book.ml - book.mr - 13 * MM)
        by = y + 11 * MM
        for line in lines:
            txt(page, "r", line, book.ml + 13 * MM, by, 9.5, INK)
            by += 12
        y = by + 7 * MM

    note = pymupdf.Rect(book.ml, y + 2 * MM, book.xr, y + 38 * MM)
    fill_rect(page, note, ROW_ALT)
    page.draw_rect(note, color=COPPER, width=1.2)
    txt(page, "sb", "Hvad kortene ikke erstatter", note.x0 + 8, note.y0 + 14, 10, COPPER)
    body = (
        "Driftsplanen i Excel er stadig overblikket over frekvens. Kortene er kvitteringen. "
        "Servicebesøg fra leverandører (fx rottespærre) kan vedlægges som bilag bag det relevante årskort."
    )
    yy = note.y0 + 28
    for line in wrap("r", body, 9, note.width - 16):
        txt(page, "r", line, note.x0 + 8, yy, 9, INK)
        yy += 12


def draw_master(book: CardBook) -> None:
    """Board-facing 'last done' overview for everything less frequent than weekly."""
    page = book.new_page()
    book.toc.append(("Oversigt — senest udført", book.page_no))
    y = book.header_bar(
        page,
        "oversigt",
        "Oversigt — senest udført",
        "Opdateres løbende. Bestyrelsens hurtige overblik.",
    )
    book.footer(page, "Oversigt")

    rows: list[tuple[str, str, str]] = []
    for t, a in MONTHLY:
        rows.append((t, a, "måned"))
    for t, a, n in QUARTERLY:
        rows.append((t, a, "kvartal" + (f" · {n}" if n else "")))
    for t, a, n in HALFYEAR:
        rows.append((t, a, "halvår" + (f" · {n}" if n else "")))
    for t, a, n in YEARLY_DRIFT:
        rows.append((t, a, "år" + (f" · {n}" if n else "")))
    rows.append(("Rottespærre — rensning af 8 udløb (3 Lillegård, 5 Storegård).", "KBA Gartner", "servicebesøg"))
    rows.append(("Spuling af hovedkloak fra brønde til offentlig kloak.", "Hvem?", "før næste service"))

    x0 = book.ml
    x1 = book.xr
    usable = x1 - x0
    cols = [
        ("Opgave", 0, 68 * MM),
        ("Ansvarlig", 68 * MM, 26 * MM),
        ("Frekvens", 94 * MM, 32 * MM),
        ("Senest udført", 126 * MM, 28 * MM),
        ("Init.", 154 * MM, usable - 154 * MM),
    ]

    def head(y0: float) -> float:
        fill_rect(page, pymupdf.Rect(x0, y0, x1, y0 + 14), PINE)
        for label, dx, _w in cols:
            txt(page, "m", label.upper(), x0 + dx + 4, y0 + 10, 6.5, WHITE)
        return y0 + 14

    y = head(y)
    inner_w = cols[0][2] - 10
    for i, (task, owner, freq) in enumerate(rows):
        lines = wrap("r", task, 7.6, inner_w)
        h = max(16, 6 + 10 * len(lines))
        if y + h > A4_H - 22 * MM:
            page = book.new_page()
            y = book.header_bar(page, "oversigt", "Oversigt — senest udført", "Fortsættelse")
            book.footer(page, "Oversigt")
            y = head(y)
        bg = ROW_ALT if i % 2 == 0 else CREAM
        fill_rect(page, pymupdf.Rect(x0, y, x1, y + h), bg)
        page.draw_line(pymupdf.Point(x0, y + h), pymupdf.Point(x1, y + h), color=HAIR, width=0.4)
        ty = y + 11
        for line in lines:
            txt(page, "r", line, x0 + 4, ty, 7.6, INK)
            ty += 10
        txt(page, "m", owner, x0 + cols[1][1] + 4, y + 11, 7.2, INK)
        txt(page, "r", freq, x0 + cols[2][1] + 4, y + 11, 7, MUTED)
        # write boxes
        for dx, w in ((cols[3][1], cols[3][2] - 6), (cols[4][1], cols[4][2] - 6)):
            page.draw_rect(
                pymupdf.Rect(x0 + dx + 2, y + 3, x0 + dx + w, y + h - 3),
                color=RULE,
                fill=WHITE,
                width=0.5,
            )
        y += h


def draw_period_fields(book: CardBook, page: pymupdf.Page, y: float, fields: list[tuple[str, float]]) -> float:
    x = book.ml
    for label, w in fields:
        book.field(page, x, y, label, w)
        x += w + 6 * MM
    return y + 22


def draw_weekly_table(
    book: CardBook,
    page: pymupdf.Page,
    y: float,
    tasks: list[tuple[str, str, str]],
    note_label: str,
) -> None:
    x0, x1 = book.ml, book.xr
    usable = x1 - x0
    c_box, c_task, c_own, c_date, c_init = 5 * MM, 72 * MM, 24 * MM, 22 * MM, 14 * MM
    c_rem_x = c_box + c_task + c_own + c_date + c_init
    headers = [
        (0, ""),
        (c_box, "Opgave"),
        (c_box + c_task, "Ansvarlig"),
        (c_box + c_task + c_own, "Udført"),
        (c_box + c_task + c_own + c_date, "Init."),
        (c_rem_x, "Bemærkning / ikke aktuelt"),
    ]
    notes_h = 32 * MM
    wrapped: list[tuple[list[str], str]] = []
    for task, owner, tag in tasks:
        label = task if not tag else f"{task}  [{tag}]"
        wrapped.append((wrap("r", label, 8, c_task - 8), owner))
    body = A4_H - 22 * MM - y - 13 - notes_h - 10
    min_needed = sum(max(22, 10 + 11 * len(lines)) for lines, _ in wrapped)
    extra = max(0, body - min_needed) / max(1, len(wrapped))

    fill_rect(page, pymupdf.Rect(x0, y, x1, y + 13), PINE_MID)
    for dx, label in headers:
        if label:
            txt(page, "m", label.upper(), x0 + dx + 3, y + 9.5, 6.2, WHITE)
    y += 13

    for i, (lines, owner) in enumerate(wrapped):
        h = max(22, 10 + 11 * len(lines)) + extra
        bg = ROW_ALT if i % 2 == 0 else CREAM
        fill_rect(page, pymupdf.Rect(x0, y, x1, y + h), bg)
        page.draw_line(pymupdf.Point(x0, y + h), pymupdf.Point(x1, y + h), color=HAIR, width=0.4)
        book.checkbox(page, x0 + 3.5, y + h / 2 - 4.5, 9)
        ty = y + 13
        for line in lines:
            txt(page, "r", line, x0 + c_box + 3, ty, 8, INK)
            ty += 11
        txt(page, "m", owner, x0 + c_box + c_task + 3, y + 13, 7.4, INK)
        for dx, w in (
            (c_box + c_task + c_own, c_date - 4),
            (c_box + c_task + c_own + c_date, c_init - 4),
            (c_rem_x, usable - c_rem_x - 4),
        ):
            page.draw_rect(
                pymupdf.Rect(x0 + dx + 2, y + 4, x0 + dx + w, y + h - 4),
                color=RULE,
                fill=WHITE,
                width=0.45,
            )
        y += h

    y += 6
    txt(page, "m", note_label.upper(), book.ml, y, 6.5, MUTED)
    y += 3
    page.draw_rect(pymupdf.Rect(x0, y, x1, A4_H - 20 * MM), color=RULE, fill=WHITE, width=0.6)
    for gy in range(int(y + 14), int(A4_H - 24 * MM), 14):
        page.draw_line(pymupdf.Point(x0 + 6, gy), pymupdf.Point(x1 - 6, gy), color=HAIR, width=0.3)


def draw_daily(book: CardBook) -> None:
    page = book.new_page()
    book.toc.append(("Dagligt tjekkort", book.page_no))
    y = book.header_bar(page, "daglig", "Dagligt tjekkort", "Én seddel pr. uge. Sæt initialer i dagens felt — eller «–» hvis ikke aktuelt.")
    book.footer(page, "Daglig")
    y = draw_period_fields(
        book,
        page,
        y,
        [("Uge nr.", 26 * MM), ("Fra dato", 40 * MM), ("Til dato", 40 * MM), ("Udfyldt af", 46 * MM)],
    )

    days = ["Man", "Tir", "Ons", "Tor", "Fre", "Lør", "Søn"]
    x0, x1 = book.ml, book.xr
    task_w = 62 * MM
    day_w = (x1 - x0 - task_w) / 7
    row_h = 38 * MM

    fill_rect(page, pymupdf.Rect(x0, y, x1, y + 12), FREQ_COLOR["daglig"])
    txt(page, "m", "OPGAVE", x0 + 4, y + 8.5, 6.5, WHITE)
    for i, d in enumerate(days):
        tx = x0 + task_w + i * day_w
        txt(page, "m", d.upper(), tx + day_w / 2 - tw("m", d.upper(), 6.5) / 2, y + 8.5, 6.5, WHITE)
    y += 12

    for ti, (task, owner, tag) in enumerate(DAILY):
        h = row_h
        bg = ROW_ALT if ti % 2 == 0 else CREAM
        fill_rect(page, pymupdf.Rect(x0, y, x1, y + h), bg)
        lines = wrap("sb", task, 8.2, task_w - 10)
        ty = y + 14
        for line in lines:
            txt(page, "sb", line, x0 + 5, ty, 8.2, INK)
            ty += 11
        meta = owner if not tag else f"{owner}  ·  {tag}"
        txt(page, "r", meta, x0 + 5, y + h - 8, 7, MUTED)
        for i in range(7):
            tx = x0 + task_w + i * day_w
            page.draw_line(pymupdf.Point(tx, y), pymupdf.Point(tx, y + h), color=HAIR, width=0.4)
            box = pymupdf.Rect(tx + 4, y + 10, tx + day_w - 4, y + h - 10)
            page.draw_rect(box, color=RULE, fill=WHITE, width=0.6)
        page.draw_line(pymupdf.Point(x0, y + h), pymupdf.Point(x1, y + h), color=RULE, width=0.5)
        y += h

    y += 8
    txt(page, "m", "BEMÆRKNINGER TIL UGEN", book.ml, y, 6.5, MUTED)
    y += 3
    page.draw_rect(pymupdf.Rect(x0, y, x1, y + 42 * MM), color=RULE, fill=WHITE, width=0.6)
    for gy in range(int(y + 14), int(y + 40 * MM), 14):
        page.draw_line(pymupdf.Point(x0 + 6, gy), pymupdf.Point(x1 - 6, gy), color=HAIR, width=0.3)

    y += 48 * MM
    txt(page, "i", "Print 52 kopier om året — eller kopier blankt kort efter behov. Læg den afsluttede uge bagerst i fanen.", book.ml, y, 8, MUTED)


def draw_weekly(book: CardBook) -> None:
    specs = [
        ("Ugentligt tjekkort  ·  ejendom", WEEKLY_A, "Faste ugentlige rutiner. Sæt kryds når tjekket er sket.", "Bemærkninger, afvigelser, bestillinger"),
        ("Ugentligt tjekkort  ·  beboer & status", WEEKLY_B, "Ugentlig status. Skriv «ingen» hvis intet aktuelt.", "Aktuelle sager denne uge"),
    ]
    first = True
    for title, tasks, sub, note in specs:
        page = book.new_page()
        if first:
            book.toc.append(("Ugentligt tjekkort", book.page_no))
            first = False
        y = book.header_bar(page, "ugentlig", title, sub)
        book.footer(page, "Ugentlig")
        y = draw_period_fields(
            book,
            page,
            y,
            [("Uge nr.", 26 * MM), ("Uge fra", 38 * MM), ("Uge til", 38 * MM), ("Udfyldt af", 48 * MM)],
        )
        draw_weekly_table(book, page, y, tasks, note)


def draw_monthly(book: CardBook) -> None:
    page = book.new_page()
    book.toc.append(("Månedligt tjekkort", book.page_no))
    y = book.header_bar(
        page,
        "månedlig",
        "Månedligt tjekkort  ·  2026",
        "Skriv dato + initialer i månedens felt, når opgaven er udført.",
    )
    book.footer(page, "Månedlig")

    months = [
        "Januar", "Februar", "Marts", "April", "Maj", "Juni",
        "Juli", "August", "September", "Oktober", "November", "December",
    ]
    x0, x1 = book.ml, book.xr
    m_w = 28 * MM
    col_w = (x1 - x0 - m_w) / len(MONTHLY)
    head_h = 28 * MM

    fill_rect(page, pymupdf.Rect(x0, y, x1, y + head_h), FREQ_COLOR["månedlig"])
    txt(page, "m", "MÅNED", x0 + 4, y + 16, 7, WHITE)
    for i, (task, owner) in enumerate(MONTHLY):
        tx = x0 + m_w + i * col_w
        page.draw_line(pymupdf.Point(tx, y), pymupdf.Point(tx, y + head_h), color=(0.85, 0.55, 0.38), width=0.4)
        lines = wrap("m", task, 7.2, col_w - 8)
        ty = y + 10
        for line in lines[:3]:
            txt(page, "m", line, tx + 4, ty, 7.2, WHITE)
            ty += 9
        txt(page, "r", owner, tx + 4, y + head_h - 6, 6.5, (0.96, 0.90, 0.84))
    y += head_h

    row_h = (A4_H - 22 * MM - y) / 12
    for i, month in enumerate(months):
        bg = ROW_ALT if i % 2 == 0 else CREAM
        fill_rect(page, pymupdf.Rect(x0, y, x1, y + row_h), bg)
        txt(page, "sb", month, x0 + 5, y + row_h / 2 + 3, 9, PINE)
        for c in range(len(MONTHLY)):
            tx = x0 + m_w + c * col_w
            page.draw_line(pymupdf.Point(tx, y), pymupdf.Point(tx, y + row_h), color=HAIR, width=0.4)
            box = pymupdf.Rect(tx + 4, y + 5, tx + col_w - 4, y + row_h - 5)
            page.draw_rect(box, color=RULE, fill=WHITE, width=0.5)
        page.draw_line(pymupdf.Point(x0, y + row_h), pymupdf.Point(x1, y + row_h), color=HAIR, width=0.4)
        y += row_h


def draw_period_log(
    book: CardBook,
    kind: str,
    title: str,
    subtitle: str,
    periods: list[str],
    tasks: list[tuple[str, str, str]],
    toc: str,
) -> None:
    page = book.new_page()
    book.toc.append((toc, book.page_no))
    y = book.header_bar(page, kind, title, subtitle)
    book.footer(page, toc)
    y = draw_period_fields(book, page, y, [("År", 28 * MM), ("Udfyldt af", 70 * MM)])

    x0, x1 = book.ml, book.xr
    task_w = 78 * MM
    own_w = 28 * MM
    p_w = (x1 - x0 - task_w - own_w) / len(periods)
    head_h = 14
    fill_rect(page, pymupdf.Rect(x0, y, x1, y + head_h), FREQ_COLOR[kind])
    txt(page, "m", "OPGAVE", x0 + 4, y + 10, 6.5, WHITE)
    txt(page, "m", "ANSVARLIG", x0 + task_w + 4, y + 10, 6.5, WHITE)
    for i, p in enumerate(periods):
        tx = x0 + task_w + own_w + i * p_w
        txt(page, "m", p.upper(), tx + 4, y + 10, 6.5, WHITE)
    y += head_h

    row_h = min(36, (A4_H - 48 * MM - y) / max(1, len(tasks)))
    for i, (task, owner, note) in enumerate(tasks):
        bg = ROW_ALT if i % 2 == 0 else CREAM
        fill_rect(page, pymupdf.Rect(x0, y, x1, y + row_h), bg)
        lines = wrap("r", task, 8, task_w - 10)
        ty = y + 12
        for line in lines[:2]:
            txt(page, "r", line, x0 + 5, ty, 8, INK)
            ty += 11
        if note:
            txt(page, "i", note, x0 + 5, y + row_h - 7, 6.5, MUTED)
        txt(page, "m", owner, x0 + task_w + 4, y + 14, 8, INK)
        for p in range(len(periods)):
            tx = x0 + task_w + own_w + p * p_w
            page.draw_line(pymupdf.Point(tx, y), pymupdf.Point(tx, y + row_h), color=HAIR, width=0.4)
            box = pymupdf.Rect(tx + 4, y + 6, tx + p_w - 4, y + row_h - 6)
            page.draw_rect(box, color=RULE, fill=WHITE, width=0.5)
            txt(page, "r", "dato / init.", tx + 6, y + row_h - 8, 5.5, (0.72, 0.70, 0.66))
        page.draw_line(pymupdf.Point(x0, y + row_h), pymupdf.Point(x1, y + row_h), color=HAIR, width=0.4)
        y += row_h

    y += 8
    txt(page, "m", "SENEST UDFØRT  ·  samlet notat", book.ml, y, 6.5, MUTED)
    y += 3
    page.draw_rect(pymupdf.Rect(x0, y, x1, A4_H - 20 * MM), color=RULE, fill=WHITE, width=0.6)


def draw_yearly_drift(book: CardBook) -> None:
    page = book.new_page()
    book.toc.append(("Årlige driftsopgaver", book.page_no))
    y = book.header_bar(
        page,
        "årlig",
        "Årlige driftsopgaver  ·  2026",
        "Dato for seneste udførelse er det, bestyrelsen skal kunne slå op.",
    )
    book.footer(page, "Årlig")
    y = draw_period_fields(book, page, y, [("År", 28 * MM), ("Udfyldt af", 70 * MM)])

    x0, x1 = book.ml, book.xr
    for i, (task, owner, note) in enumerate(YEARLY_DRIFT):
        h = 28 * MM
        bg = ROW_ALT if i % 2 == 0 else CREAM
        fill_rect(page, pymupdf.Rect(x0, y, x1, y + h), bg)
        page.draw_rect(pymupdf.Rect(x0, y, x1, y + h), color=HAIR, width=0.4)
        lines = wrap("sb", task, 10, 105 * MM)
        ty = y + 12
        for line in lines:
            txt(page, "sb", line, x0 + 6, ty, 10, INK)
            ty += 13
        txt(page, "r", f"{owner}" + (f"  ·  {note}" if note else ""), x0 + 6, y + h - 8, 8, MUTED)
        book.field(page, x1 - 58 * MM, y + 10, "Senest udført", 32 * MM, 16)
        book.field(page, x1 - 22 * MM, y + 10, "Init.", 22 * MM, 16)
        y += h + 4

    y += 6
    txt(page, "m", "ANDRE ÅRLIGE OBSERVATIONER", book.ml, y, 6.5, MUTED)
    y += 3
    page.draw_rect(pymupdf.Rect(x0, y, x1, A4_H - 20 * MM), color=RULE, fill=WHITE, width=0.6)
    for gy in range(int(y + 14), int(A4_H - 24 * MM), 14):
        page.draw_line(pymupdf.Point(x0 + 6, gy), pymupdf.Point(x1 - 6, gy), color=HAIR, width=0.3)


def draw_building(book: CardBook) -> None:
    page = book.new_page()
    book.toc.append(("Bygningsvedligehold", book.page_no))
    y = book.header_bar(
        page,
        "bygning",
        "Bygningsvedligehold",
        "Fra driftsplanens bygningsdele. «Hvem?» = ansvarlig mangler stadig i planen.",
    )
    book.footer(page, "Bygning")

    x0, x1 = book.ml, book.xr
    usable = x1 - x0
    c_task, c_own, c_when, c_date = 78 * MM, 28 * MM, 28 * MM, 24 * MM
    c_init = usable - (c_task + c_own + c_when + c_date)
    first_on_page = True

    def col_head(y0: float) -> float:
        fill_rect(page, pymupdf.Rect(x0, y0, x1, y0 + 12), PINE_MID)
        for label, dx in (
            ("Opgave", 0),
            ("Ansvarlig", c_task),
            ("Interval", c_task + c_own),
            ("Senest udført", c_task + c_own + c_when),
            ("Init.", c_task + c_own + c_when + c_date),
        ):
            txt(page, "m", label.upper(), x0 + dx + 4, y0 + 8.8, 6.2, WHITE)
        return y0 + 12

    def ensure(h: float, section: str) -> None:
        nonlocal page, y, first_on_page
        if y + h < A4_H - 22 * MM:
            return
        page = book.new_page()
        y = book.header_bar(page, "bygning", "Bygningsvedligehold", f"Fortsættelse · {section}")
        book.footer(page, "Bygning")
        y = col_head(y)
        first_on_page = True

    y = col_head(y)

    for section, tasks in BUILDING:
        ensure(14 + 22 * len(tasks), section)
        if not first_on_page:
            y += 3
        fill_rect(page, pymupdf.Rect(x0, y, x1, y + 12), FREQ_COLOR["bygning"])
        txt(page, "sb", section, x0 + 5, y + 8.8, 9, WHITE)
        y += 12
        first_on_page = False
        for i, (task, owner, when) in enumerate(tasks):
            lines = wrap("r", task, 7.8, c_task - 10)
            h = max(22, 8 + 10.5 * len(lines))
            ensure(h, section)
            bg = ROW_ALT if i % 2 == 0 else CREAM
            fill_rect(page, pymupdf.Rect(x0, y, x1, y + h), bg)
            page.draw_line(pymupdf.Point(x0, y + h), pymupdf.Point(x1, y + h), color=HAIR, width=0.35)
            ty = y + 12
            for line in lines:
                txt(page, "r", line, x0 + 5, ty, 7.8, INK)
                ty += 10.5
            txt(page, "m", owner, x0 + c_task + 4, y + 13, 7.4, INK)
            txt(page, "r", when, x0 + c_task + c_own + 4, y + 13, 6.8, MUTED)
            book.write_box(
                page,
                pymupdf.Rect(
                    x0 + c_task + c_own + c_when + 3,
                    y + 4,
                    x0 + c_task + c_own + c_when + c_date - 3,
                    y + h - 4,
                ),
            )
            book.write_box(
                page,
                pymupdf.Rect(
                    x0 + c_task + c_own + c_when + c_date + 3,
                    y + 4,
                    x1 - 3,
                    y + h - 4,
                ),
            )
            y += h


def draw_rats(book: CardBook) -> None:
    page = book.new_page()
    book.toc.append(("Kloak og rottespærre", book.page_no))
    y = book.header_bar(
        page,
        "kloak",
        "Kloak og rottespærre",
        "Stedliste + kvittering. Udløbene var ikke navngivet i driftsplanen — udfyld gerne stederne.",
    )
    book.footer(page, "Kloak")

    x0, x1 = book.ml, book.xr
    info = (
        "Ved servicebesøg 16. juli 2026 blev 8 rottespærre renset (3 i Lillegård, 5 i Storegård). "
        "Der blev konstateret hårde kalk- og fedtaflejringer i hovedkloakkerne. "
        "Spuling anbefales inden næste service — ellers kan ikke alle spærre serviceres."
    )
    box = pymupdf.Rect(x0, y, x1, y + 28 * MM)
    fill_rect(page, box, ROW_ALT)
    yy = y + 10
    for line in wrap("r", info, 8.5, box.width - 14):
        txt(page, "r", line, x0 + 7, yy, 8.5, INK)
        yy += 11
    y = box.y1 + 8

    y = draw_period_fields(
        book,
        page,
        y,
        [
            ("Seneste rensning af rottespærre", 62 * MM),
            ("Seneste spuling", 48 * MM),
            ("Udført af", 48 * MM),
        ],
    )

    places = [f"Lillegård  {i}" for i in range(1, 4)] + [f"Storegård  {i}" for i in range(1, 6)]
    usable = x1 - x0
    cols = [
        ("Sted", 0, 28 * MM),
        ("Placering (brønd / hvor)", 28 * MM, 52 * MM),
        ("Renset", 80 * MM, 22 * MM),
        ("Spulet", 102 * MM, 22 * MM),
        ("Init.", 124 * MM, 16 * MM),
        ("Bemærkning", 140 * MM, usable - 140 * MM),
    ]
    fill_rect(page, pymupdf.Rect(x0, y, x1, y + 12), FREQ_COLOR["kloak"])
    for label, dx, _w in cols:
        txt(page, "m", label.upper(), x0 + dx + 3, y + 8.8, 6, WHITE)
    y += 12
    row_h = 16 * MM
    for i, place in enumerate(places):
        bg = ROW_ALT if i % 2 == 0 else CREAM
        fill_rect(page, pymupdf.Rect(x0, y, x1, y + row_h), bg)
        txt(page, "sb", place, x0 + 5, y + 11, 9, INK)
        for dx, w in (
            (cols[1][1], cols[1][2] - 4),
            (cols[2][1], cols[2][2] - 4),
            (cols[3][1], cols[3][2] - 4),
            (cols[4][1], cols[4][2] - 4),
            (cols[5][1], cols[5][2] - 4),
        ):
            page.draw_rect(
                pymupdf.Rect(x0 + dx + 2, y + 4, x0 + dx + w, y + row_h - 4),
                color=RULE,
                fill=WHITE,
                width=0.5,
            )
        page.draw_line(pymupdf.Point(x0, y + row_h), pymupdf.Point(x1, y + row_h), color=HAIR, width=0.4)
        y += row_h

    y += 8
    txt(page, "m", "ANBEFALING / NÆSTE SKRIDT", book.ml, y, 6.5, MUTED)
    y += 3
    page.draw_rect(pymupdf.Rect(x0, y, x1, A4_H - 20 * MM), color=RULE, fill=WHITE, width=0.6)


def draw_dividers(book: CardBook) -> None:
    page = book.new_page()
    book.toc.append(("Faner til ringbind", book.page_no))
    y = book.header_bar(
        page,
        "oversigt",
        "Faner til ringbind",
        "Klip ud og tape på skilleblade. Farven matcher den farvede kant på kortene.",
    )
    book.footer(page, "Faner")

    tabs = [
        ("Daglig", "daglig"),
        ("Ugentlig", "ugentlig"),
        ("Månedlig", "månedlig"),
        ("Kvartal", "kvartal"),
        ("Halvår", "halvår"),
        ("Årlig", "årlig"),
        ("Bygning", "bygning"),
        ("Kloak", "kloak"),
        ("Oversigt", "oversigt"),
    ]
    x0 = book.ml
    w, h = 56 * MM, 22 * MM
    gap = 6 * MM
    for i, (label, kind) in enumerate(tabs):
        col = i % 3
        row = i // 3
        x = x0 + col * (w + gap)
        yy = y + row * (h + gap)
        r = pymupdf.Rect(x, yy, x + w, yy + h)
        fill_rect(page, r, FREQ_COLOR[kind])
        page.draw_rect(r, color=PINE, width=0.3, dashes="[2 2]")
        txt(page, "b", label.upper(), x + 6, yy + 14, 11, WHITE)

    txt(
        page,
        "i",
        "Stiplet linje = klip. Sæt fanerne i samme rækkefølge som indholdsfortegnelsen.",
        book.ml,
        y + 3 * (h + gap) + 8,
        8.5,
        MUTED,
    )


def render_previews(doc: pymupdf.Document) -> None:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    zoom = 1.6
    mat = pymupdf.Matrix(zoom, zoom)
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=mat, alpha=False)
        path = PREVIEW_DIR / f"side-{i + 1:02d}.png"
        pix.save(str(path))
    print(f"Wrote {len(doc)} previews to {PREVIEW_DIR}")


def main() -> None:
    book = CardBook()
    draw_cover(book)
    draw_howto(book)
    draw_master(book)
    draw_daily(book)
    draw_weekly(book)
    draw_monthly(book)
    draw_period_log(
        book,
        "kvartal",
        "Kvartalskort  ·  2026",
        "Skriv dato og initialer i kvartalets felt. Opdatér også oversigten forrest i bindet.",
        ["1. kvt.", "2. kvt.", "3. kvt.", "4. kvt."],
        QUARTERLY,
        "Kvartal",
    )
    draw_period_log(
        book,
        "halvår",
        "Halvårskort  ·  2026",
        "Skriv dato og initialer. Hæk klippes 1 × årligt — sæt kryds i det halvår, det sker.",
        ["1. halvår", "2. halvår"],
        HALFYEAR,
        "Halvår",
    )
    draw_yearly_drift(book)
    draw_building(book)
    draw_rats(book)
    draw_dividers(book)
    book.save()
    render_previews(book.doc)


if __name__ == "__main__":
    main()

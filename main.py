#!/usr/bin/env python3
"""Render a newspaper-style infographic summing up the world news of
Tuesday 24 November 2026 as a single 1024x1024 PNG.

Pure Python 3 standard library: a small 5x7 bitmap font, simple shape
drawing on an RGB bytearray, and a minimal PNG encoder (zlib).
No network, no files read, no randomness: both runs write identical bytes.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py   ->  out/entry.png
"""

import binascii
import os
import struct
import zlib

# ---------------------------------------------------------------- font
# 5x7 bitmap glyphs. Each glyph is 7 rows of 5 bits, '1' = ink.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "11110", "10001", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
}

CHAR_W = 6  # 5 px glyph + 1 px gap, at scale 1
CHAR_H = 7


def text_width(text, scale):
    """Width in pixels of `text` drawn at `scale`."""
    return len(text) * CHAR_W * scale


def wrap_text(text, scale, max_w):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    lines = []
    for para in text.split("\n"):
        words = para.split(" ")
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if text_width(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def _off(self, x, y):
        return (y * self.w + x) * 3

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            o = self._off(x, y)
            self.px[o:o + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            o = self._off(x0, yy)
            self.px[o:o + len(row)] = row

    def hline(self, x, y, w, color, t=1):
        self.fill_rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.fill_rect(x, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        """Bresenham line with square thickness t."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.fill_rect(x0 - t // 2, y0 - t // 2, t, t, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, fill=False, t=2):
        """Midpoint circle; outline (thickness t) or filled."""
        x = 0
        y = r
        d = 1 - r
        pts = []

        def plot(px, py):
            pts.append((px, py))

        while x <= y:
            for sx, sy in ((x, y), (y, x), (-x, y), (-y, x),
                           (x, -y), (y, -x), (-x, -y), (-y, -x)):
                plot(cx + sx, cy + sy)
            if d < 0:
                d += 2 * x + 3
            else:
                d += 2 * (x - y) + 5
                y -= 1
            x += 1
        if fill:
            rows = {}
            for px, py in pts:
                rows.setdefault(py, [px, px])
                rows[py][0] = min(rows[py][0], px)
                rows[py][1] = max(rows[py][1], px)
            for py, (a, b) in rows.items():
                self.fill_rect(a, py, b - a + 1, 1, color)
        else:
            for px, py in pts:
                self.fill_rect(px - t // 2, py - t // 2, t, t, color)

    def ellipse(self, cx, cy, rx, ry, color, t=2):
        """Outline ellipse drawn as a scaled circle sample."""
        import math
        steps = max(48, int(2 * math.pi * max(rx, ry)))
        prev = None
        for i in range(steps + 1):
            a = 2 * math.pi * i / steps
            px = int(round(cx + rx * math.cos(a)))
            py = int(round(cy + ry * math.sin(a)))
            if prev is not None:
                self.line(prev[0], prev[1], px, py, color, t)
            prev = (px, py)

    def triangle(self, p1, p2, p3, color):
        """Filled triangle, scanline fill."""
        pts = sorted((p1, p2, p3), key=lambda p: p[1])
        (x1, y1), (x2, y2), (x3, y3) = pts

        def interp(xa, ya, xb, yb, y):
            if yb == ya:
                return xa
            return xa + (xb - xa) * (y - ya) / (yb - ya)

        for y in range(y1, y3 + 1):
            if y < y2:
                xa = interp(x1, y1, x2, y2, y)
                xb = interp(x1, y1, x3, y3, y)
            else:
                xa = interp(x2, y2, x3, y3, y)
                xb = interp(x1, y1, x3, y3, y)
            a, b = int(min(xa, xb)), int(max(xa, xb))
            self.fill_rect(a, y, b - a + 1, 1, color)

    # ---------------------------------------------------------------- text
    def draw_glyph(self, x, y, ch, scale, color):
        glyph = FONT.get(ch)
        if glyph is None:
            glyph = FONT["?"] if ch != " " else FONT[" "]
        for row, bits in enumerate(glyph):
            for col, bit in enumerate(bits):
                if bit == "1":
                    self.fill_rect(x + col * scale, y + row * scale,
                                   scale, scale, color)

    def draw_text(self, x, y, text, scale, color):
        """Draw text (upper-cased; unknown chars become space)."""
        cx = x
        for ch in text.upper():
            if ch not in FONT:
                ch = " "
            self.draw_glyph(cx, y, ch, scale, color)
            cx += CHAR_W * scale
        return cx

    def draw_text_centered(self, cx, y, text, scale, color):
        w = text_width(text, scale)
        return self.draw_text(cx - w // 2, y, text, scale, color)

    def draw_lines(self, x, y, lines, scale, color, leading=None):
        if leading is None:
            leading = CHAR_H * scale + 4
        for line in lines:
            self.draw_text(x, y, line, scale, color)
            y += leading
        return y


# ---------------------------------------------------------------- PNG out
def write_png(path, canvas):
    w, h = canvas.w, canvas.h
    raw = bytearray()
    rowlen = w * 3
    for y in range(h):
        raw.append(0)  # filter: none
        raw += canvas.px[y * rowlen:(y + 1) * rowlen]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        out += struct.pack(">I", binascii.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", comp) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 232)   # newsprint off-white
INK = (26, 26, 30)        # near-black
RED = (163, 22, 33)       # headline red
NAVY = (31, 58, 95)       # deep blue
TEAL = (15, 107, 92)      # green-teal
OCHRE = (176, 116, 28)    # warm ochre
SLATE = (90, 96, 110)     # grey for rules / captions
TINT_RED = (244, 224, 220)
TINT_NAVY = (222, 231, 240)
TINT_TEAL = (214, 235, 229)
TINT_OCHRE = (244, 233, 209)
TINT_SLATE = (232, 232, 228)
WHITE = (255, 255, 255)

W, H = 1024, 1024
MARGIN = 36


# ---------------------------------------------------------------- icons
def icon_globe(c, x, y, s, color, accent):
    """Cracked globe: circle, latitude/longitude arcs, red crack."""
    cx, cy, r = x + s // 2, y + s // 2, s // 2 - 4
    c.ellipse(cx, cy, r, r, color, 3)
    c.ellipse(cx, cy, r, int(r * 0.45), color, 2)
    c.ellipse(cx, cy, int(r * 0.45), r, color, 2)
    c.line(cx - r, cy, cx + r, cy, color, 2)
    # red crack zig-zag across the globe
    c.line(cx - r // 2, cy - r, cx - r // 4, cy - r // 3, accent, 3)
    c.line(cx - r // 4, cy - r // 3, cx + r // 6, cy, accent, 3)
    c.line(cx + r // 6, cy, cx - r // 6, cy + r // 3, accent, 3)
    c.line(cx - r // 6, cy + r // 3, cx + r // 3, cy + r, accent, 3)


def icon_ship(c, x, y, s, color, accent):
    """Warship on waves with a small blast."""
    cx = x + s // 2
    hull_y = y + s // 2 + 6
    c.triangle((x + 8, hull_y), (x + s - 8, hull_y),
               (x + s - 22, hull_y + 16), color)
    c.fill_rect(x + 8, hull_y, s - 16, 14, color)
    c.fill_rect(cx - 12, hull_y - 18, 24, 18, color)
    c.vline(cx, hull_y - 34, 18, color, 3)
    c.fill_rect(cx - 14, hull_y - 38, 28, 5, accent)
    # waves
    for wy in (hull_y + 26, hull_y + 34):
        for k in range(4):
            wx = x + 6 + k * (s - 12) // 4
            c.line(wx, wy, wx + 8, wy - 4, color, 2)
            c.line(wx + 8, wy - 4, wx + 16, wy, color, 2)
    # blast star
    bx, by = x + s - 16, y + 12
    c.line(bx - 8, by, bx + 8, by, accent, 3)
    c.line(bx, by - 8, bx, by + 8, accent, 3)
    c.line(bx - 6, by - 6, bx + 6, by + 6, accent, 2)
    c.line(bx - 6, by + 6, bx + 6, by - 6, accent, 2)


def icon_chip(c, x, y, s, color, accent):
    """Microchip with pins and a rising arrow."""
    m = 14
    c.fill_rect(x + m, y + m + 8, s - 2 * m, s - 2 * m - 8, color)
    c.fill_rect(x + m + 10, y + m + 18, s - 2 * m - 20, s - 2 * m - 28,
                PAPER)
    for i in range(4):
        px = x + m + 8 + i * ((s - 2 * m - 16) // 3)
        c.fill_rect(px, y + 4, 6, 10, color)
        c.fill_rect(px, y + s - 14, 6, 10, color)
        py = y + m + 8 + i * ((s - 2 * m - 16) // 3)
        c.fill_rect(x + 4, py, 10, 6, color)
        c.fill_rect(x + s - 14, py, 10, 6, color)
    # rising arrow
    ax = x + s - 26
    c.line(ax, y + 22, ax, y + 2, accent, 3)
    c.line(ax - 6, y + 8, ax, y + 2, accent, 3)
    c.line(ax + 6, y + 8, ax, y + 2, accent, 3)


def icon_tanker(c, x, y, s, color, accent):
    """Oil tanker with a flame and sea mines."""
    hy = y + s // 2 + 2
    c.fill_rect(x + 6, hy, s - 12, 16, color)
    c.fill_rect(x + s - 30, hy - 20, 20, 20, color)
    c.fill_rect(x + s - 26, hy - 30, 12, 10, accent)
    # flame above the bow
    fx = x + s - 20
    c.triangle((fx - 8, hy - 30), (fx + 8, hy - 30), (fx, hy - 52), accent)
    # mines in the water
    for mx, my in ((x + 16, hy + 28), (x + 40, hy + 34), (x + 64, hy + 28)):
        c.circle(mx, my, 4, color, fill=True)
        c.line(mx - 6, my, mx + 6, my, color, 2)
        c.line(mx, my - 6, mx, my + 6, color, 2)
    c.line(x + 6, hy + 44, x + s - 6, hy + 44, color, 2)


def icon_scales(c, x, y, s, color, accent):
    """Scales of justice."""
    cx = x + s // 2
    top = y + 10
    c.vline(cx, top + 6, s - 34, color, 3)
    c.line(x + 12, top + 6, x + s - 12, top + 6, color, 3)
    for px in (x + 16, x + s - 16):
        c.line(px, top + 6, px, top + 26, color, 2)
        c.triangle((px - 14, top + 26), (px + 14, top + 26),
                   (px, top + 44), color)
    c.fill_rect(cx - 16, y + s - 16, 32, 6, color)
    c.circle(cx, top, 5, accent, fill=True)


def icon_plane(c, x, y, s, color, accent):
    """Jet with radar arcs."""
    cx, cy = x + s // 2, y + s // 2
    # radar arcs
    for r in (18, 30):
        c.ellipse(cx, cy, r, r, accent, 2)
    # jet: fuselage + wings + tail
    c.triangle((cx - 34, cy + 6), (cx + 30, cy - 4), (cx + 30, cy + 10),
               color)
    c.triangle((cx - 6, cy), (cx + 6, cy - 22), (cx + 14, cy), color)
    c.triangle((cx - 6, cy + 4), (cx + 6, cy + 24), (cx + 14, cy + 4),
               color)
    c.triangle((cx - 30, cy + 2), (cx - 22, cy - 12), (cx - 16, cy + 2),
               color)


ICONS = {
    "globe": icon_globe,
    "ship": icon_ship,
    "chip": icon_chip,
    "tanker": icon_tanker,
    "scales": icon_scales,
    "plane": icon_plane,
}


def icon_box(c, x, y, s, tint, icon, color, accent):
    """Tinted square with a thin outline, icon drawn inside."""
    c.fill_rect(x, y, s, s, tint)
    c.fill_rect(x, y, s, 2, color)
    c.fill_rect(x, y + s - 2, s, 2, color)
    c.fill_rect(x, y, 2, s, color)
    c.fill_rect(x + s - 2, y, 2, s, color)
    ICONS[icon](c, x + 6, y + 6, s - 12, color, accent)

# ---------------------------------------------------------------- stories
LEAD = {
    "kicker": "CLIMATE",
    "color": RED,
    "tint": TINT_RED,
    "icon": "globe",
    "headline": ["COP31 CLIMATE TALKS", "COLLAPSE IN ANTALYA"],
    "summary": ("TALKS IN ANTALYA RUN NEARLY 50 HOURS INTO OVERTIME, THEN "
                "MORE THAN 90 NATIONS REJECT A DRAFT THAT NEVER NAMES "
                "FOSSIL FUELS. CLIMATE DIPLOMACY'S DARKEST MOMENT, "
                "GRIST CALLS IT."),
    "stat": "90+ NATIONS REJECT THE DRAFT - 50 HOURS OVERTIME",
}

GRID = [
    {
        "kicker": "WAR",
        "color": NAVY,
        "tint": TINT_NAVY,
        "icon": "ship",
        "headline": "UKRAINE SINKS RUSSIAN WARSHIP OFF LIBYA",
        "summary": ("KYIV SAYS NAVAL DRONES SANK THE CORVETTE MERKURY AT "
                    "BENGHAZI. THE UN SEEKS A PROBE AS THE BLACK SEA FIGHT "
                    "REACHES THE MEDITERRANEAN."),
    },
    {
        "kicker": "TECH",
        "color": TEAL,
        "tint": TINT_TEAL,
        "icon": "chip",
        "headline": "NVIDIA BRINGS BACK HUANG AS CEO",
        "summary": ("HUANG RETURNS AFTER TRUMP PRESSED THE BOARD. HIS "
                    "FORTUNE JUMPED ABOUT $34 BILLION IN A DAY, "
                    "FORBES SAYS."),
    },
    {
        "kicker": "ENERGY",
        "color": OCHRE,
        "tint": TINT_OCHRE,
        "icon": "tanker",
        "headline": "MINES HIT TANKERS IN HORMUZ STRAIT",
        "summary": ("THREE OIL TANKERS CATCH FIRE AFTER HITTING SEA MINES, "
                    "IRAN'S GUARD SAYS, AS GULF TENSIONS RISE."),
    },
    {
        "kicker": "LAW",
        "color": RED,
        "tint": TINT_RED,
        "icon": "scales",
        "headline": "US STATES SUE MUSK FIRMS OVER GROK IMAGES",
        "summary": ("OREGON AND VIRGINIA SUE SPACEX OVER ALLEGED "
                    "GROK-MADE SEXUALISED IMAGES OF CHILDREN."),
    },
]

ALSO = [
    "SEOUL: SUSPECTED NORTH KOREAN JET BREACHES SOUTH'S AIRSPACE; ISLANDERS TOLD TO SHELTER.",
    "SPORT: US, MEXICO, COSTA RICA AND JAMAICA TO HOST THE 2031 WOMEN'S WORLD CUP; UK GETS 2035.",
    "DENMARK TO BAN SCHOOL PHONES UP TO 10TH GRADE AFTER POOR PISA RESULTS.",
    "HONDA RECALLS 810,000 VEHICLES IN THE US OVER AIRBAG RUPTURE RISK.",
]


# ---------------------------------------------------------------- layout
def render():
    c = Canvas(W, H, PAPER)

    # ---- masthead
    c.draw_text_centered(W // 2, 30, "THE WORLD IN ONE DAY", 6, INK)
    c.hline(MARGIN, 82, W - 2 * MARGIN, INK, 2)
    c.hline(MARGIN, 86, W - 2 * MARGIN, INK, 1)
    c.draw_text_centered(W // 2, 98, "TUESDAY, 24 NOVEMBER 2026", 4, RED)
    c.hline(MARGIN, 134, W - 2 * MARGIN, INK, 3)
    c.draw_text_centered(W // 2, 144,
                         "THE DAY'S NEWS FROM EVERY CORNER OF THE EARTH",
                         2, SLATE)

    # ---- lead story
    ly = 172
    c.draw_text(MARGIN, ly, LEAD["kicker"], 2, LEAD["color"])
    icon_box(c, W - MARGIN - 170, ly, 170, LEAD["tint"], LEAD["icon"],
             LEAD["color"], RED)
    hy = ly + 26
    for line in LEAD["headline"]:
        c.draw_text(MARGIN, hy, line, 4, INK)
        hy += 32
    sy = hy + 8
    lines = wrap_text(LEAD["summary"], 2, W - MARGIN - 170 - MARGIN - 24)
    sy = c.draw_lines(MARGIN, sy, lines, 2, INK, leading=18)
    c.draw_text(MARGIN, sy + 12, LEAD["stat"], 2, LEAD["color"])
    c.hline(MARGIN, 372, W - 2 * MARGIN, INK, 2)

    # ---- 2x2 grid of stories
    cell_w = (W - 2 * MARGIN - 24) // 2
    cell_h = 176
    grid_top = 392
    for i, story in enumerate(GRID):
        cx = MARGIN + (i % 2) * (cell_w + 24)
        cy = grid_top + (i // 2) * (cell_h + 16)
        icon_box(c, cx, cy, 92, story["tint"], story["icon"],
                 story["color"], RED)
        c.draw_text(cx + 104, cy + 4, story["kicker"], 2, story["color"])
        hl = wrap_text(story["headline"], 3, cell_w - 104)
        yy = c.draw_lines(cx + 104, cy + 24, hl, 3, INK, leading=25)
        sl = wrap_text(story["summary"], 2, cell_w)
        c.draw_lines(cx, cy + 102, sl, 2, INK, leading=18)

    # ---- also today
    ay = 776
    c.draw_text(MARGIN, ay, "ALSO TODAY", 3, INK)
    c.hline(MARGIN, ay + 26, W - 2 * MARGIN, INK, 2)
    for i, item in enumerate(ALSO):
        ix = MARGIN + (i % 2) * (cell_w + 24)
        iy = ay + 44 + (i // 2) * 62
        c.fill_rect(ix, iy + 2, 10, 10, RED)
        lines = wrap_text(item, 2, cell_w - 20)
        c.draw_lines(ix + 20, iy, lines, 2, INK, leading=18)

    # ---- footer
    c.hline(MARGIN, 948, W - 2 * MARGIN, SLATE, 1)
    c.draw_text_centered(W // 2, 962,
                         "MAKE.FUN - THE WORLD IN ONE IMAGE - 24 NOVEMBER 2026",
                         2, SLATE)
    return c


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(path, render())
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()

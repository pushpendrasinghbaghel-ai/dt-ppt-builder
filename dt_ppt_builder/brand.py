"""Dynatrace brand colors and font constants."""
from pptx.dml.color import RGBColor
from pptx.util import Pt

# ── Brand palette ─────────────────────────────────────────────────────────────
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
TEAL    = RGBColor(0x00, 0xA9, 0xE0)   # DT primary blue/teal
GREEN   = RGBColor(0x73, 0xBE, 0x28)   # "Now / Available"
ORANGE  = RGBColor(0xF5, 0x82, 0x1F)   # "Partial"
PURPLE  = RGBColor(0x9B, 0x59, 0xB6)   # AppEngine / GCC accent
GRAY    = RGBColor(0xAA, 0xAA, 0xAA)   # muted text
LGRAY   = RGBColor(0xCC, 0xCC, 0xCC)   # lighter muted text
DGRAY   = RGBColor(0x1E, 0x2A, 0x3A)   # table row even
DDGRAY  = RGBColor(0x12, 0x1E, 0x2E)   # table row odd
DTDARK  = RGBColor(0x0B, 0x17, 0x26)   # table header bg

# Status symbol→color mapping
STATUS_COLOR = {
    "\u2705": GREEN,    # ✅ Now
    "\u26a1": ORANGE,   # ⚡ Partial
    "\U0001f5fa": GRAY, # 🗺 Roadmap
}

def status_color(val: str) -> RGBColor:
    for sym, color in STATUS_COLOR.items():
        if sym in val:
            return color
    return WHITE

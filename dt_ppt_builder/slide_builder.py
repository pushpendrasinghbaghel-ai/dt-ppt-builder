"""
Slide factory functions.

Every function signature:
    func(prs, SL, cfg, ...)  →  slide
where
    prs  = Presentation object
    SL   = slide-layout lookup dict  (populated by builder._layout_map)
    cfg  = config dict from YAML

Layout keys used (names approximate, matched by builder._layout_map):
    'title_center'  — Title + eyebrow only, centered  (idx 11 in Perform26 template)
    'title_content' — Title + eyebrow + content        (idx 2)
    'two_img'       — 2 images + captions               (idx 19)
"""
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN

from .brand import WHITE, TEAL, GREEN, ORANGE, PURPLE, GRAY, DTDARK, RGBColor
from .helpers import (set_ph, txb, para_block, status_bar,
                      req_table, add_img, coverage_table)

import os


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _new(prs, SL, key):
    """Append a new slide using the named layout."""
    return prs.slides.add_slide(SL[key])


def _img_path(cfg, key):
    """Resolve an image key to an absolute path using config."""
    shots_dir = cfg.get("screenshots_dir", "")
    mapping   = cfg.get("images", {})
    filename  = mapping.get(key, "")
    if not filename:
        return None
    return os.path.join(shots_dir, filename)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Title / cover slide
# ─────────────────────────────────────────────────────────────────────────────
def title_slide(prs, SL, cfg):
    sl = _new(prs, SL, "title_center")
    set_ph(sl, 0, cfg.get("deck_title", "AI Observability"),
           size=36, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    set_ph(sl, 1, cfg.get("deck_subtitle", ""), size=20, color=TEAL,
           align=PP_ALIGN.CENTER)
    # Optional customer logo
    logo = cfg.get("customer_logo")
    if logo and os.path.exists(logo):
        add_img(sl, logo, 10.8, 6.8, 2.2, 0.55)
    return sl


# ─────────────────────────────────────────────────────────────────────────────
# 2. Agenda / section-overview slide
# ─────────────────────────────────────────────────────────────────────────────
def agenda_slide(prs, SL, cfg, items):
    """
    items: list of (emoji_or_icon, label) tuples
    """
    sl = _new(prs, SL, "title_center")
    set_ph(sl, 0, "Agenda", size=32, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    lines = [f"{icon}  {label}" for icon, label in items]
    para_block(sl, lines, 3.5, 2.0, 6.5, 4.5, size=14, color=WHITE)
    return sl


# ─────────────────────────────────────────────────────────────────────────────
# 3. Coverage matrix (summary table of all domains)
# ─────────────────────────────────────────────────────────────────────────────
def coverage_slide(prs, SL, cfg, domains):
    """
    domains: list of dicts — keys: name, total, now, partial, roadmap
    """
    sl = _new(prs, SL, "title_content")
    set_ph(sl, 0, cfg.get("coverage_title", "AI Observability Coverage Summary"),
           size=22, bold=True, color=WHITE)
    set_ph(sl, 1, cfg.get("coverage_eyebrow", cfg.get("customer", "")),
           size=10, color=TEAL, italic=True)
    coverage_table(sl, domains, l=0.7, t=2.3, w=11.94, h=4.6)
    return sl


# ─────────────────────────────────────────────────────────────────────────────
# 4. Instrumentation / landing-page screenshot slide
# ─────────────────────────────────────────────────────────────────────────────
def instrumentation_slide(prs, SL, cfg, img_key="landing",
                           title="AI Observability — Landing Page",
                           bullets=None):
    sl    = _new(prs, SL, "title_content")
    set_ph(sl, 0, title, size=20, bold=True, color=WHITE)
    set_ph(sl, 1, cfg.get("customer", ""), size=10, color=TEAL, italic=True)
    # one large screenshot on the right
    add_img(sl, _img_path(cfg, img_key), 7.0, 1.7, 6.0, 5.5)
    # bullet points on the left
    if bullets:
        para_block(sl, bullets, 0.5, 2.0, 6.2, 5.2, size=11)
    return sl


# ─────────────────────────────────────────────────────────────────────────────
# 5. Domain requirements slide  (main workhorse)
# ─────────────────────────────────────────────────────────────────────────────
def domain_slide(prs, SL, cfg, domain_label, reqs,
                 description="", show_bar=True):
    """
    domain_label : e.g. "Domain 1 — Cost Allocation & Showback"
    reqs         : list of (Requirement, Description, Status, Signal)
    description  : short subtitle / scope text (optional)
    show_bar     : draw the ✅/⚡/🗺 count bar
    """
    sl = _new(prs, SL, "title_content")
    set_ph(sl, 0, domain_label, size=18, bold=True, color=WHITE)
    set_ph(sl, 1, cfg.get("customer", ""), size=10, color=TEAL, italic=True)
    if description:
        txb(sl, description, 0.5, 1.55, 12.5, 0.4, size=10, color=GRAY)

    if show_bar:
        now      = sum(1 for r in reqs if "✅" in r[2] or "Now" in r[2])
        partial  = sum(1 for r in reqs if "⚡" in r[2] or "Partial" in r[2])
        roadmap  = sum(1 for r in reqs if "🗺" in r[2] or "Roadmap" in r[2])
        status_bar(sl, now, partial, roadmap, len(reqs), left=0.5, top=2.0)
        table_top = 2.42
    else:
        table_top = 2.0

    req_table(sl, reqs, l=0.5, t=table_top, w=12.84,
              h=7.5 - table_top - 0.1)
    return sl


# ─────────────────────────────────────────────────────────────────────────────
# 6. Two-image comparison / screenshot slide
# ─────────────────────────────────────────────────────────────────────────────
def two_image_slide(prs, SL, cfg, title,
                    left_key, left_caption,
                    right_key, right_caption,
                    eyebrow=None):
    sl = _new(prs, SL, "two_img")
    set_ph(sl, 0, title, size=18, bold=True, color=WHITE)
    set_ph(sl, 1, eyebrow or cfg.get("customer", ""),
           size=10, color=TEAL, italic=True)
    # images
    add_img(sl, _img_path(cfg, left_key),  0.36, 1.75, 6.22, 5.2)
    add_img(sl, _img_path(cfg, right_key), 6.78, 1.75, 6.22, 5.2)
    # captions
    txb(sl, left_caption,  0.36, 6.95, 6.22, 0.4, size=9, color=GRAY, align=PP_ALIGN.CENTER)
    txb(sl, right_caption, 6.78, 6.95, 6.22, 0.4, size=9, color=GRAY, align=PP_ALIGN.CENTER)
    return sl


# ─────────────────────────────────────────────────────────────────────────────
# 7. Generic section-divider / chapter-header slide
# ─────────────────────────────────────────────────────────────────────────────
def chapter_slide(prs, SL, cfg, heading, subheading="", color=TEAL):
    sl = _new(prs, SL, "title_center")
    set_ph(sl, 0, heading, size=30, bold=True, color=color, align=PP_ALIGN.CENTER)
    if subheading:
        set_ph(sl, 1, subheading, size=14, color=WHITE, align=PP_ALIGN.CENTER)
    return sl


# ─────────────────────────────────────────────────────────────────────────────
# 8. GCC / regulatory-highlight slide
# ─────────────────────────────────────────────────────────────────────────────
def gcc_slide(prs, SL, cfg, reqs, title=None, eyebrow=None):
    lbl = title or "GCC / Regulatory Highlights"
    return domain_slide(prs, SL, cfg, lbl, reqs,
                        description=eyebrow or "", show_bar=True)


# ─────────────────────────────────────────────────────────────────────────────
# 9. Closing / Q&A slide
# ─────────────────────────────────────────────────────────────────────────────
def closing_slide(prs, SL, cfg, message=None):
    sl = _new(prs, SL, "title_center")
    set_ph(sl, 0, message or "Thank you", size=36, bold=True,
           color=WHITE, align=PP_ALIGN.CENTER)
    contact = cfg.get("contact", "")
    if contact:
        txb(sl, contact, 3.5, 5.6, 7.0, 0.5, size=11, color=TEAL,
            align=PP_ALIGN.CENTER)
    return sl

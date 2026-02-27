"""
Generic slide renderer — content-driven slide generation.

Each function takes a Presentation + layout dict + a slide spec dict
and renders one slide. The slide spec is a JSON-friendly dict that
Copilot (or any caller) provides.

Supported slide types:
  title      —  Title + subtitle + optional contact
  section    —  Bold section-divider / chapter header
  bullets    —  Title + bullet points
  table      —  Title + arbitrary table (headers + rows)
  two_column —  Title + two columns of bullets
  text       —  Title + free-form body text
  image      —  Title + image + optional caption
  comparison —  Title + two side-by-side comparison blocks
  closing    —  Closing message + contact
"""
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN

from .brand import WHITE, TEAL, GREEN, ORANGE, GRAY, DGRAY, DDGRAY, DTDARK, RGBColor
from .helpers import set_ph, txb, para_block


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _new(prs, SL, key):
    return prs.slides.add_slide(SL[key])


# Map user-friendly color names → RGBColor
_NAMED_COLORS = {
    "white": WHITE, "teal": TEAL, "green": GREEN,
    "orange": ORANGE, "gray": GRAY,
}

def _resolve_color(val, default=WHITE):
    if val is None:
        return default
    if isinstance(val, str):
        return _NAMED_COLORS.get(val.lower(), default)
    return default


# ─────────────────────────────────────────────────────────────────────────────
# 1. Title slide
# ─────────────────────────────────────────────────────────────────────────────
def render_title(prs, SL, spec):
    sl = _new(prs, SL, "title_center")
    set_ph(sl, 0, spec.get("title", ""),
           size=36, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    set_ph(sl, 1, spec.get("subtitle", ""),
           size=20, color=TEAL, align=PP_ALIGN.CENTER)
    contact = spec.get("contact", "")
    if contact:
        txb(sl, contact, 3.5, 5.6, 7.0, 0.5,
            size=11, color=TEAL, align=PP_ALIGN.CENTER)
    return sl


# ─────────────────────────────────────────────────────────────────────────────
# 2. Section / chapter divider
# ─────────────────────────────────────────────────────────────────────────────
def render_section(prs, SL, spec):
    sl = _new(prs, SL, "title_center")
    set_ph(sl, 0, spec.get("title", ""),
           size=30, bold=True, color=TEAL, align=PP_ALIGN.CENTER)
    sub = spec.get("subtitle", "")
    if sub:
        set_ph(sl, 1, sub, size=14, color=WHITE, align=PP_ALIGN.CENTER)
    return sl


# ─────────────────────────────────────────────────────────────────────────────
# 3. Bullet-point slide
# ─────────────────────────────────────────────────────────────────────────────
def render_bullets(prs, SL, spec):
    sl = _new(prs, SL, "title_content")
    set_ph(sl, 0, spec.get("title", ""),
           size=22, bold=True, color=WHITE)
    eyebrow = spec.get("eyebrow", "")
    if eyebrow:
        set_ph(sl, 1, eyebrow, size=10, color=TEAL, italic=True)
    bullets = spec.get("bullets", [])
    para_block(sl, bullets, 0.7, 2.0, 11.5, 5.2, size=12, color=WHITE)
    return sl


# ─────────────────────────────────────────────────────────────────────────────
# 4. Table slide
# ─────────────────────────────────────────────────────────────────────────────
def render_table(prs, SL, spec):
    sl = _new(prs, SL, "title_content")
    set_ph(sl, 0, spec.get("title", ""),
           size=22, bold=True, color=WHITE)
    eyebrow = spec.get("eyebrow", "")
    if eyebrow:
        set_ph(sl, 1, eyebrow, size=10, color=TEAL, italic=True)

    columns = spec.get("columns", [])
    rows    = spec.get("rows", [])
    if not columns or not rows:
        return sl

    n_cols = len(columns)
    n_rows = len(rows)
    col_w = 12.0 / n_cols

    tbl_shape = sl.shapes.add_table(
        n_rows + 1, n_cols,
        Inches(0.7), Inches(2.2), Inches(12.0), Inches(5.0))
    tbl = tbl_shape.table

    for c in range(n_cols):
        tbl.columns[c].width = Inches(col_w)

    # Header
    for c, h_txt in enumerate(columns):
        cell = tbl.cell(0, c)
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = str(h_txt)
        r.font.size = Pt(10); r.font.bold = True; r.font.color.rgb = TEAL
        cell.fill.solid(); cell.fill.fore_color.rgb = DTDARK

    # Data
    for ri, row in enumerate(rows):
        bg = DGRAY if ri % 2 == 0 else DDGRAY
        for c in range(min(n_cols, len(row))):
            cell = tbl.cell(ri + 1, c)
            p = cell.text_frame.paragraphs[0]
            r = p.add_run(); r.text = str(row[c])
            r.font.size = Pt(9); r.font.color.rgb = WHITE
            cell.fill.solid(); cell.fill.fore_color.rgb = bg
    return sl


# ─────────────────────────────────────────────────────────────────────────────
# 5. Two-column slide
# ─────────────────────────────────────────────────────────────────────────────
def render_two_column(prs, SL, spec):
    sl = _new(prs, SL, "title_content")
    set_ph(sl, 0, spec.get("title", ""),
           size=22, bold=True, color=WHITE)
    eyebrow = spec.get("eyebrow", "")
    if eyebrow:
        set_ph(sl, 1, eyebrow, size=10, color=TEAL, italic=True)

    # Left column
    left_hdr     = spec.get("left_header", "")
    left_bullets = spec.get("left_bullets", [])
    para_block(sl, left_bullets, 0.5, 2.2, 5.8, 4.8,
               size=11, color=WHITE, hdr=left_hdr, hdr_color=TEAL, hdr_size=13)

    # Right column
    right_hdr     = spec.get("right_header", "")
    right_bullets = spec.get("right_bullets", [])
    para_block(sl, right_bullets, 6.8, 2.2, 5.8, 4.8,
               size=11, color=WHITE, hdr=right_hdr, hdr_color=TEAL, hdr_size=13)
    return sl


# ─────────────────────────────────────────────────────────────────────────────
# 6. Free-text slide
# ─────────────────────────────────────────────────────────────────────────────
def render_text(prs, SL, spec):
    sl = _new(prs, SL, "title_content")
    set_ph(sl, 0, spec.get("title", ""),
           size=22, bold=True, color=WHITE)
    eyebrow = spec.get("eyebrow", "")
    if eyebrow:
        set_ph(sl, 1, eyebrow, size=10, color=TEAL, italic=True)
    body = spec.get("body", "")
    txb(sl, body, 0.7, 2.0, 11.5, 5.2, size=12, color=WHITE)
    return sl


# ─────────────────────────────────────────────────────────────────────────────
# 7. Image slide
# ─────────────────────────────────────────────────────────────────────────────
def render_image(prs, SL, spec):
    import os
    sl = _new(prs, SL, "title_content")
    set_ph(sl, 0, spec.get("title", ""),
           size=22, bold=True, color=WHITE)
    img_path = spec.get("image_path", "")
    caption  = spec.get("caption", "")
    if img_path and os.path.exists(img_path):
        sl.shapes.add_picture(img_path,
                              Inches(1.5), Inches(1.8), Inches(10.0), Inches(5.0))
    if caption:
        txb(sl, caption, 1.5, 6.9, 10.0, 0.4,
            size=9, color=GRAY, align=PP_ALIGN.CENTER)
    return sl


# ─────────────────────────────────────────────────────────────────────────────
# 8. Comparison slide (side-by-side)
# ─────────────────────────────────────────────────────────────────────────────
def render_comparison(prs, SL, spec):
    sl = _new(prs, SL, "title_content")
    set_ph(sl, 0, spec.get("title", ""),
           size=22, bold=True, color=WHITE)

    items = spec.get("items", [])  # list of {label, bullets}
    n = len(items) or 1
    col_w = 12.0 / n
    for i, item in enumerate(items):
        x = 0.5 + i * col_w
        para_block(sl, item.get("bullets", []),
                   x, 2.2, col_w - 0.3, 4.8,
                   size=11, color=WHITE,
                   hdr=item.get("label", ""), hdr_color=TEAL, hdr_size=13)
    return sl


# ─────────────────────────────────────────────────────────────────────────────
# 9. Closing slide
# ─────────────────────────────────────────────────────────────────────────────
def render_closing(prs, SL, spec):
    sl = _new(prs, SL, "title_center")
    set_ph(sl, 0, spec.get("message", "Thank you"),
           size=36, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    contact = spec.get("contact", "")
    if contact:
        txb(sl, contact, 3.5, 5.6, 7.0, 0.5,
            size=11, color=TEAL, align=PP_ALIGN.CENTER)
    return sl


# ─────────────────────────────────────────────────────────────────────────────
# Dispatcher — given a slide spec dict, call the right renderer
# ─────────────────────────────────────────────────────────────────────────────
_RENDERERS = {
    "title":      render_title,
    "section":    render_section,
    "bullets":    render_bullets,
    "table":      render_table,
    "two_column": render_two_column,
    "text":       render_text,
    "image":      render_image,
    "comparison": render_comparison,
    "closing":    render_closing,
}

def render_slide(prs, SL, spec: dict):
    """Render a single slide from a spec dict. Returns the slide object."""
    slide_type = spec.get("type", "bullets")
    renderer = _RENDERERS.get(slide_type)
    if renderer is None:
        raise ValueError(f"Unknown slide type: '{slide_type}'. "
                         f"Valid types: {list(_RENDERERS.keys())}")
    return renderer(prs, SL, spec)


def render_all(prs, SL, slides: list[dict]):
    """Render a list of slide specs, returning all slide objects."""
    results = []
    for spec in slides:
        results.append(render_slide(prs, SL, spec))
    return results

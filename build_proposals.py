#!/usr/bin/env python3
"""
Build 3 proposal slides (one per pipeline option) for Pact3D.
Style matches existing slide deck (white/tan palette, Calibri).
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# Palette (matching existing deck)
BG       = RGBColor(0xFF, 0xFF, 0xFF)
TEXT     = RGBColor(0x1A, 0x1A, 0x1A)
DIM      = RGBColor(0x99, 0x99, 0x99)
ACCENT   = RGBColor(0x7B, 0x1E, 0x1E)
TAN      = RGBColor(0xF0, 0xE6, 0xD3)
TAN_DARK = RGBColor(0xD4, 0xC4, 0xA8)
TEAL     = RGBColor(0x00, 0x88, 0x80)
WHITE    = RGBColor(0xFF, 0xFF, 0xFF)
BLUE     = RGBColor(0x2B, 0x57, 0x97)
GREEN    = RGBColor(0x2D, 0x7D, 0x46)
ORANGE   = RGBColor(0xC4, 0x6A, 0x10)
LIGHT_BLUE = RGBColor(0xE8, 0xF0, 0xFE)
LIGHT_GREEN = RGBColor(0xE8, 0xF5, 0xE9)
LIGHT_ORANGE = RGBColor(0xFE, 0xF3, 0xE5)

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
blank = prs.slide_layouts[6]


def bg(slide):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG


def tx(slide, l, t, w, h, text, sz=16, color=TEXT, bold=False,
       align=PP_ALIGN.LEFT, name="Calibri"):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(sz)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = name
    p.alignment = align
    return box


def rich_box(slide, l, t, w, h, lines):
    """lines: [(text, size, color, bold, indent), ...]
    indent is in inches from left edge of box."""
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(lines):
        text, sz, col, bld = item[0], item[1], item[2], item[3]
        indent = item[4] if len(item) > 4 else 0
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = text
        p.font.size = Pt(sz)
        p.font.color.rgb = col
        p.font.bold = bld
        p.font.name = "Calibri"
        p.space_after = Pt(2)
        p.line_spacing = Pt(sz * 1.35)
        if indent:
            p.level = 1
    return box


def rounded_box(slide, l, t, w, h, fill_color, border_color, border_width=1.5):
    rect = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    rect.fill.solid()
    rect.fill.fore_color.rgb = fill_color
    rect.line.color.rgb = border_color
    rect.line.width = Pt(border_width)
    # Smaller corner radius
    rect.adjustments[0] = 0.05
    return rect


def arrow_down(slide, cx, y, length=Inches(0.35), color=DIM):
    """Draw a downward arrow at center x, starting y."""
    tx(slide, cx - Inches(0.15), y, Inches(0.3), Inches(0.35),
       "▼", sz=14, color=color, align=PP_ALIGN.CENTER)


def arrow_right(slide, x, cy, color=DIM):
    tx(slide, x, cy - Inches(0.1), Inches(0.3), Inches(0.3),
       "▶", sz=12, color=color, align=PP_ALIGN.CENTER)


def slide_num(slide, n):
    sz = Inches(0.4)
    rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                   SLIDE_W - Inches(0.55),
                                   SLIDE_H - Inches(0.55), sz, sz)
    rect.fill.solid()
    rect.fill.fore_color.rgb = ACCENT
    rect.line.fill.background()
    tf = rect.text_frame
    tf.paragraphs[0].text = str(n)
    tf.paragraphs[0].font.size = Pt(12)
    tf.paragraphs[0].font.color.rgb = WHITE
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.name = "Calibri"
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE


def option_header(slide, letter, title, subtitle, accent_color):
    """Standard header for all three option slides."""
    # Option badge
    badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                    Inches(0.4), Inches(0.3),
                                    Inches(0.7), Inches(0.5))
    badge.fill.solid()
    badge.fill.fore_color.rgb = accent_color
    badge.line.fill.background()
    badge.adjustments[0] = 0.15
    tf = badge.text_frame
    tf.paragraphs[0].text = letter
    tf.paragraphs[0].font.size = Pt(20)
    tf.paragraphs[0].font.color.rgb = WHITE
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.name = "Calibri"
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE

    tx(slide, Inches(1.3), Inches(0.25), Inches(8), Inches(0.5),
       title, sz=26, bold=True, color=TEXT)
    tx(slide, Inches(1.3), Inches(0.7), Inches(10), Inches(0.35),
       subtitle, sz=14, color=DIM)


# ════════════════════════════════════════════════════════════════
# SLIDE 1 — Option A: Optimization-Based
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
option_header(s, "A", "Optimization-Based Correction",
              "GVHMR + DA3 + L-BFGS energy minimization  •  Inspired by LEMO/PROX  •  6 weeks",
              BLUE)

# --- Left: Pipeline diagram ---
# Video input
bx = Inches(0.5)
by = Inches(1.3)

rounded_box(s, bx, by, Inches(2.2), Inches(0.5), TAN, TAN_DARK)
tx(s, bx + Inches(0.1), by + Inches(0.05), Inches(2.0), Inches(0.4),
   "Input Video", sz=13, bold=True, color=TEXT, align=PP_ALIGN.CENTER)

# Two branches
arrow_down(s, bx + Inches(0.7), by + Inches(0.55))
arrow_down(s, bx + Inches(1.5), by + Inches(0.55))

# GVHMR box
gy = by + Inches(0.95)
rounded_box(s, bx, gy, Inches(2.2), Inches(0.7), LIGHT_BLUE, BLUE)
tx(s, bx + Inches(0.1), gy + Inches(0.02), Inches(2.0), Inches(0.25),
   "GVHMR", sz=12, bold=True, color=BLUE, align=PP_ALIGN.CENTER)
tx(s, bx + Inches(0.1), gy + Inches(0.28), Inches(2.0), Inches(0.4),
   "SMPL poses + contacts\nin gravity-view coords", sz=9, color=TEXT, align=PP_ALIGN.CENTER)

arrow_down(s, bx + Inches(1.1), gy + Inches(0.75))

# DA3 box
dy = gy + Inches(1.15)
rounded_box(s, bx, dy, Inches(2.2), Inches(0.7), LIGHT_BLUE, BLUE)
tx(s, bx + Inches(0.1), dy + Inches(0.02), Inches(2.0), Inches(0.25),
   "DA3-Metric-Large", sz=12, bold=True, color=BLUE, align=PP_ALIGN.CENTER)
tx(s, bx + Inches(0.1), dy + Inches(0.28), Inches(2.0), Inches(0.4),
   "Metric point cloud\n+ camera poses", sz=9, color=TEXT, align=PP_ALIGN.CENTER)

arrow_down(s, bx + Inches(1.1), dy + Inches(0.75))

# Scene proxy
sy = dy + Inches(1.15)
rounded_box(s, bx, sy, Inches(2.2), Inches(0.7), TAN, TAN_DARK)
tx(s, bx + Inches(0.1), sy + Inches(0.02), Inches(2.0), Inches(0.25),
   "Scene Proxy", sz=12, bold=True, color=TEXT, align=PP_ALIGN.CENTER)
tx(s, bx + Inches(0.1), sy + Inches(0.28), Inches(2.0), Inches(0.4),
   "Ground plane (RANSAC)\nCollision mesh + SDF", sz=9, color=TEXT, align=PP_ALIGN.CENTER)

# Arrow right to optimization
arrow_right(s, bx + Inches(2.3), sy + Inches(0.35), color=BLUE)

# --- Center: Optimization box (the core) ---
ox = Inches(3.2)
oy = Inches(1.3)
rounded_box(s, ox, oy, Inches(4.7), Inches(5.3), RGBColor(0xF0, 0xF4, 0xFE), BLUE, 2.0)

tx(s, ox + Inches(0.2), oy + Inches(0.15), Inches(4.3), Inches(0.35),
   "Energy Minimization (L-BFGS)", sz=16, bold=True, color=BLUE, align=PP_ALIGN.CENTER)

tx(s, ox + Inches(0.2), oy + Inches(0.55), Inches(4.3), Inches(0.3),
   "Optimize Δθ (pose) + Δt (translation) per frame", sz=10, color=DIM, align=PP_ALIGN.CENTER)

# Energy terms
terms = [
    ("E_contact", "Pin feet to surface during contact"),
    ("E_penetration", "SDF non-intersection with scene"),
    ("E_friction", "No horizontal sliding during contact"),
    ("E_smooth", "Temporal jerk penalty"),
    ("E_stability", "CoM inside support polygon"),
    ("E_prior", "VPoser body prior (stay near GVHMR)"),
]
ey = oy + Inches(1.0)
for name, desc in terms:
    rounded_box(s, ox + Inches(0.2), ey, Inches(4.3), Inches(0.55), WHITE, TAN_DARK, 0.75)
    tx(s, ox + Inches(0.35), ey + Inches(0.05), Inches(1.5), Inches(0.25),
       name, sz=11, bold=True, color=BLUE)
    tx(s, ox + Inches(1.8), ey + Inches(0.05), Inches(2.5), Inches(0.45),
       desc, sz=10, color=TEXT)
    ey += Inches(0.63)

# MuJoCo validation
ey += Inches(0.1)
rounded_box(s, ox + Inches(0.2), ey, Inches(4.3), Inches(0.45), TAN, ACCENT, 1.0)
tx(s, ox + Inches(0.35), ey + Inches(0.05), Inches(4.0), Inches(0.35),
   "MuJoCo Validation (forward sim → verify stability)", sz=11, bold=True, color=ACCENT,
   align=PP_ALIGN.CENTER)

# --- Right: Targets + Timeline ---
rx = Inches(8.4)

# Targets
tx(s, rx, Inches(1.3), Inches(4.5), Inches(0.35),
   "Targets", sz=18, bold=True, color=TEXT)

rounded_box(s, rx, Inches(1.7), Inches(4.4), Inches(1.9), WHITE, TAN_DARK, 0.75)

rich_box(s, rx + Inches(0.2), Inches(1.8), Inches(4.0), Inches(1.7), [
    ("Foot sliding", 13, TEXT, True),
    ("  3.0mm (GVHMR) → < 1mm", 12, BLUE, False),
    ("", 6, DIM, False),
    ("Ground penetration", 13, TEXT, True),
    ("  ~2-5mm → < 1mm", 12, BLUE, False),
    ("", 6, DIM, False),
    ("PA-MPJPE", 13, TEXT, True),
    ("  36.2mm → no degradation (< 38mm)", 12, BLUE, False),
])

# Timeline
tx(s, rx, Inches(3.9), Inches(4.5), Inches(0.35),
   "6-Week Plan", sz=18, bold=True, color=TEXT)

rounded_box(s, rx, Inches(4.3), Inches(4.4), Inches(2.6), WHITE, TAN_DARK, 0.75)

rich_box(s, rx + Inches(0.2), Inches(4.4), Inches(4.0), Inches(2.4), [
    ("Wk 1   Environment + GVHMR/DA3 baselines", 11, TEXT, False),
    ("Wk 2   Scene proxy + contact detection", 11, TEXT, False),
    ("Wk 3   Energy function + L-BFGS optimizer", 11, BLUE, True),
    ("Wk 4   MuJoCo validation + ablations", 11, TEXT, False),
    ("Wk 5   Eval: RICH, EMDB-2, 3DPW", 11, TEXT, False),
    ("Wk 6   Polish + report + CLI", 11, TEXT, False),
    ("", 6, DIM, False),
    ("Risk: loss weight tuning, coord alignment", 10, DIM, False),
    ("Strength: principled, tunable, full scene aware", 10, ACCENT, True),
])

slide_num(s, 1)


# ════════════════════════════════════════════════════════════════
# SLIDE 2 — Option B: Feed-Forward Geometric
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
option_header(s, "B", "Feed-Forward Geometric Correction",
              "GVHMR + DA3 + closed-form geometric ops  •  No iterative solver  •  4 weeks",
              GREEN)

# --- Left: Pipeline diagram ---
bx = Inches(0.5)
by = Inches(1.3)

rounded_box(s, bx, by, Inches(2.2), Inches(0.5), TAN, TAN_DARK)
tx(s, bx + Inches(0.1), by + Inches(0.05), Inches(2.0), Inches(0.4),
   "Input Video", sz=13, bold=True, color=TEXT, align=PP_ALIGN.CENTER)

arrow_down(s, bx + Inches(1.1), by + Inches(0.55))

# GVHMR
gy = by + Inches(0.95)
rounded_box(s, bx, gy, Inches(2.2), Inches(0.7), LIGHT_GREEN, GREEN)
tx(s, bx + Inches(0.1), gy + Inches(0.02), Inches(2.0), Inches(0.25),
   "GVHMR", sz=12, bold=True, color=GREEN, align=PP_ALIGN.CENTER)
tx(s, bx + Inches(0.1), gy + Inches(0.28), Inches(2.0), Inches(0.4),
   "SMPL poses + contacts\nin gravity-view coords", sz=9, color=TEXT, align=PP_ALIGN.CENTER)

arrow_down(s, bx + Inches(1.1), gy + Inches(0.75))

# DA3
dy = gy + Inches(1.15)
rounded_box(s, bx, dy, Inches(2.2), Inches(0.7), LIGHT_GREEN, GREEN)
tx(s, bx + Inches(0.1), dy + Inches(0.02), Inches(2.0), Inches(0.25),
   "DA3-Metric-Large", sz=12, bold=True, color=GREEN, align=PP_ALIGN.CENTER)
tx(s, bx + Inches(0.1), dy + Inches(0.28), Inches(2.0), Inches(0.4),
   "Ground plane\n(RANSAC on point cloud)", sz=9, color=TEXT, align=PP_ALIGN.CENTER)

# Arrow right
arrow_right(s, bx + Inches(2.3), dy + Inches(0.35), color=GREEN)

# --- Center: Sequential correction steps ---
cx = Inches(3.2)
cy = Inches(1.3)
rounded_box(s, cx, cy, Inches(4.7), Inches(5.3), RGBColor(0xEE, 0xF7, 0xEF), GREEN, 2.0)

tx(s, cx + Inches(0.2), cy + Inches(0.15), Inches(4.3), Inches(0.35),
   "Sequential Geometric Corrections", sz=16, bold=True, color=GREEN, align=PP_ALIGN.CENTER)

tx(s, cx + Inches(0.2), cy + Inches(0.55), Inches(4.3), Inches(0.3),
   "Each step: closed-form, O(1) per frame, no iteration", sz=10, color=DIM, align=PP_ALIGN.CENTER)

steps = [
    ("1", "Ground Snap", "Translate root so contact feet\nlie on ground plane", "Δt_y = plane − min(foot_y)"),
    ("2", "Penetration Resolve", "Project sub-surface vertices\nalong plane normal", "O(V) per frame, V=6890"),
    ("3", "Contact Freeze (IK)", "Analytical 2-joint IK keeps\nfeet stationary during contact", "Closed-form leg chain solve"),
    ("4", "Temporal Smooth", "Savitzky-Golay filter on\njoint angle trajectories", "scipy, window=11, order=3"),
]

sy = cy + Inches(1.0)
for num, title, desc, detail in steps:
    # Step number circle
    circ = s.shapes.add_shape(MSO_SHAPE.OVAL,
                               cx + Inches(0.25), sy + Inches(0.1),
                               Inches(0.35), Inches(0.35))
    circ.fill.solid()
    circ.fill.fore_color.rgb = GREEN
    circ.line.fill.background()
    tf = circ.text_frame
    tf.paragraphs[0].text = num
    tf.paragraphs[0].font.size = Pt(12)
    tf.paragraphs[0].font.color.rgb = WHITE
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.name = "Calibri"
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE

    # Title + description
    tx(s, cx + Inches(0.7), sy + Inches(0.02), Inches(2.0), Inches(0.25),
       title, sz=12, bold=True, color=GREEN)
    tx(s, cx + Inches(0.7), sy + Inches(0.28), Inches(2.0), Inches(0.5),
       desc, sz=9, color=TEXT)

    # Detail (right side)
    tx(s, cx + Inches(2.8), sy + Inches(0.15), Inches(1.7), Inches(0.5),
       detail, sz=9, color=DIM)

    # Arrow between steps
    if num != "4":
        arrow_down(s, cx + Inches(0.42), sy + Inches(0.7), color=GREEN)

    sy += Inches(0.95)

# Bottom note
sy += Inches(0.2)
rounded_box(s, cx + Inches(0.2), sy, Inches(4.3), Inches(0.55), WHITE, GREEN, 1.0)
tx(s, cx + Inches(0.35), sy + Inches(0.05), Inches(4.0), Inches(0.45),
   "~1-2s / 1K frames  •  Deterministic  •  No hyperparameters", sz=11, bold=True,
   color=GREEN, align=PP_ALIGN.CENTER)

# --- Right: Targets + Timeline ---
rx = Inches(8.4)

tx(s, rx, Inches(1.3), Inches(4.5), Inches(0.35),
   "Targets", sz=18, bold=True, color=TEXT)

rounded_box(s, rx, Inches(1.7), Inches(4.4), Inches(1.9), WHITE, TAN_DARK, 0.75)

rich_box(s, rx + Inches(0.2), Inches(1.8), Inches(4.0), Inches(1.7), [
    ("Foot sliding", 13, TEXT, True),
    ("  3.0mm (GVHMR) → < 2mm", 12, GREEN, False),
    ("", 6, DIM, False),
    ("Ground penetration", 13, TEXT, True),
    ("  ~2-5mm → < 1mm", 12, GREEN, False),
    ("", 6, DIM, False),
    ("PA-MPJPE", 13, TEXT, True),
    ("  36.2mm → no degradation (< 37mm)", 12, GREEN, False),
])

tx(s, rx, Inches(3.9), Inches(4.5), Inches(0.35),
   "4-Week Plan", sz=18, bold=True, color=TEXT)

rounded_box(s, rx, Inches(4.3), Inches(4.4), Inches(2.6), WHITE, TAN_DARK, 0.75)

rich_box(s, rx + Inches(0.2), Inches(4.4), Inches(4.0), Inches(2.4), [
    ("Wk 1   Environment + GVHMR/DA3 baselines", 11, TEXT, False),
    ("Wk 2   Geometric corrections pipeline", 11, GREEN, True),
    ("Wk 3   Eval: RICH, EMDB-2, 3DPW", 11, TEXT, False),
    ("Wk 4   Multi-surface + edge cases + CLI", 11, TEXT, False),
    ("", 6, DIM, False),
    ("Fastest to first results (2 weeks)", 10, GREEN, True),
    ("Establishes baseline for Option A", 10, DIM, False),
    ("", 6, DIM, False),
    ("Risk: limited correction (ground only)", 10, DIM, False),
    ("Strength: simple, fast, debuggable", 10, ACCENT, True),
])

slide_num(s, 2)


# ════════════════════════════════════════════════════════════════
# SLIDE 3 — Option C: MuJoCo Simulation
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
option_header(s, "C", "Simulation-in-the-Loop (MuJoCo)",
              "GVHMR + DA3 + MultiPhys-style MuJoCo forward simulation  •  5 weeks",
              ORANGE)

# --- Left: Pipeline diagram ---
bx = Inches(0.5)
by = Inches(1.3)

rounded_box(s, bx, by, Inches(2.2), Inches(0.5), TAN, TAN_DARK)
tx(s, bx + Inches(0.1), by + Inches(0.05), Inches(2.0), Inches(0.4),
   "Input Video", sz=13, bold=True, color=TEXT, align=PP_ALIGN.CENTER)

arrow_down(s, bx + Inches(1.1), by + Inches(0.55))

# GVHMR
gy = by + Inches(0.95)
rounded_box(s, bx, gy, Inches(2.2), Inches(0.7), LIGHT_ORANGE, ORANGE)
tx(s, bx + Inches(0.1), gy + Inches(0.02), Inches(2.0), Inches(0.25),
   "GVHMR", sz=12, bold=True, color=ORANGE, align=PP_ALIGN.CENTER)
tx(s, bx + Inches(0.1), gy + Inches(0.28), Inches(2.0), Inches(0.4),
   "Reference motion\n(SMPL in world coords)", sz=9, color=TEXT, align=PP_ALIGN.CENTER)

arrow_down(s, bx + Inches(1.1), gy + Inches(0.75))

# DA3
dy = gy + Inches(1.15)
rounded_box(s, bx, dy, Inches(2.2), Inches(0.7), LIGHT_ORANGE, ORANGE)
tx(s, bx + Inches(0.1), dy + Inches(0.02), Inches(2.0), Inches(0.25),
   "DA3-Metric-Large", sz=12, bold=True, color=ORANGE, align=PP_ALIGN.CENTER)
tx(s, bx + Inches(0.1), dy + Inches(0.28), Inches(2.0), Inches(0.4),
   "Scene geometry\n→ MuJoCo collision bodies", sz=9, color=TEXT, align=PP_ALIGN.CENTER)

# Arrow right
arrow_right(s, bx + Inches(2.3), dy + Inches(0.35), color=ORANGE)

# --- Center: MuJoCo simulation loop ---
cx = Inches(3.2)
cy = Inches(1.3)
rounded_box(s, cx, cy, Inches(4.7), Inches(5.3), RGBColor(0xFE, 0xF7, 0xEE), ORANGE, 2.0)

tx(s, cx + Inches(0.2), cy + Inches(0.15), Inches(4.3), Inches(0.35),
   "MuJoCo Forward Simulation", sz=16, bold=True, color=ORANGE, align=PP_ALIGN.CENTER)

tx(s, cx + Inches(0.2), cy + Inches(0.55), Inches(4.3), Inches(0.3),
   "Based on MultiPhys (CVPR'24) — 7x less penetration", sz=10, color=DIM, align=PP_ALIGN.CENTER)

# Scene setup
sy = cy + Inches(1.0)
rounded_box(s, cx + Inches(0.2), sy, Inches(4.3), Inches(0.9), WHITE, TAN_DARK, 0.75)
tx(s, cx + Inches(0.35), sy + Inches(0.05), Inches(4.0), Inches(0.25),
   "Scene Setup", sz=12, bold=True, color=ORANGE)
tx(s, cx + Inches(0.35), sy + Inches(0.3), Inches(4.0), Inches(0.55),
   "Ground plane → MuJoCo geom\nDA3 mesh → V-HACD → collision bodies", sz=10, color=TEXT)

arrow_down(s, cx + Inches(2.35), sy + Inches(0.95), color=ORANGE)

# Humanoid setup
sy += Inches(1.25)
rounded_box(s, cx + Inches(0.2), sy, Inches(4.3), Inches(0.9), WHITE, TAN_DARK, 0.75)
tx(s, cx + Inches(0.35), sy + Inches(0.05), Inches(4.0), Inches(0.25),
   "Humanoid (SMPLSim)", sz=12, bold=True, color=ORANGE)
tx(s, cx + Inches(0.35), sy + Inches(0.3), Inches(4.0), Inches(0.55),
   "SMPL params → MuJoCo XML (capsule body)\nPD controllers on each joint", sz=10, color=TEXT)

arrow_down(s, cx + Inches(2.35), sy + Inches(0.95), color=ORANGE)

# Tracking loop
sy += Inches(1.25)
rounded_box(s, cx + Inches(0.2), sy, Inches(4.3), Inches(1.2), WHITE, ORANGE, 1.5)
tx(s, cx + Inches(0.35), sy + Inches(0.05), Inches(4.0), Inches(0.25),
   "Tracking Loop (per frame)", sz=12, bold=True, color=ORANGE)
tx(s, cx + Inches(0.35), sy + Inches(0.3), Inches(4.0), Inches(0.85),
   "Target: GVHMR pose at frame t\n"
   "PD controller + learned residual → torques\n"
   "MuJoCo steps physics (contacts, friction, gravity)\n"
   "Record: actual pose + contact forces",
   sz=10, color=TEXT)

# Output
arrow_down(s, cx + Inches(2.35), sy + Inches(1.25), color=ORANGE)

sy += Inches(1.55)
rounded_box(s, cx + Inches(0.2), sy, Inches(4.3), Inches(0.45), TAN, ACCENT, 1.0)
tx(s, cx + Inches(0.35), sy + Inches(0.05), Inches(4.0), Inches(0.35),
   "Physics-valid SMPL + contact forces + stability", sz=11, bold=True, color=ACCENT,
   align=PP_ALIGN.CENTER)

# --- Right: Targets + Timeline ---
rx = Inches(8.4)

tx(s, rx, Inches(1.3), Inches(4.5), Inches(0.35),
   "Targets", sz=18, bold=True, color=TEXT)

rounded_box(s, rx, Inches(1.7), Inches(4.4), Inches(1.9), WHITE, TAN_DARK, 0.75)

rich_box(s, rx + Inches(0.2), Inches(1.8), Inches(4.0), Inches(1.7), [
    ("Foot sliding", 13, TEXT, True),
    ("  3.0mm (GVHMR) → < 2mm", 12, ORANGE, False),
    ("", 6, DIM, False),
    ("Ground penetration", 13, TEXT, True),
    ("  ~2-5mm → < 0.5mm (hard constraint)", 12, ORANGE, False),
    ("", 6, DIM, False),
    ("Interpenetration (multi-person)", 13, TEXT, True),
    ("  7x reduction (MultiPhys published)", 12, ORANGE, False),
])

tx(s, rx, Inches(3.9), Inches(4.5), Inches(0.35),
   "5-Week Plan", sz=18, bold=True, color=TEXT)

rounded_box(s, rx, Inches(4.3), Inches(4.4), Inches(2.6), WHITE, TAN_DARK, 0.75)

rich_box(s, rx + Inches(0.2), Inches(4.4), Inches(4.0), Inches(2.4), [
    ("Wk 1   Env + MultiPhys demo running", 11, TEXT, False),
    ("Wk 2   DA3 scene → MuJoCo + first sim", 11, ORANGE, True),
    ("Wk 3   Controller adaptation / fine-tune", 11, TEXT, False),
    ("Wk 4   Eval: RICH, EMDB-2, 3DPW, Hi4D", 11, TEXT, False),
    ("Wk 5   Long video + report + CLI", 11, TEXT, False),
    ("", 6, DIM, False),
    ("Native multi-person support", 10, ORANGE, True),
    ("Full rigid-body dynamics (not heuristics)", 10, DIM, False),
    ("", 6, DIM, False),
    ("Risk: controller domain gap", 10, DIM, False),
    ("Strength: real physics, contact forces free", 10, ACCENT, True),
])

slide_num(s, 3)


# ════════════════════════════════════════════════════════════════
# SAVE
# ════════════════════════════════════════════════════════════════
out = "/home/user/Pact3D/Proposal_Options.pptx"
prs.save(out)
print(f"Saved → {out}")

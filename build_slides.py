#!/usr/bin/env python3
"""
Build tracking slides — simple, presentable, minimal text.
White/tan palette matching tracking(1).pdf style.
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import os

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

BG       = RGBColor(0xFF, 0xFF, 0xFF)
TEXT     = RGBColor(0x1A, 0x1A, 0x1A)
DIM      = RGBColor(0x99, 0x99, 0x99)
ACCENT   = RGBColor(0x7B, 0x1E, 0x1E)
TAN      = RGBColor(0xF0, 0xE6, 0xD3)
TAN_DARK = RGBColor(0xD4, 0xC4, 0xA8)
TEAL     = RGBColor(0x00, 0x88, 0x80)
WHITE    = RGBColor(0xFF, 0xFF, 0xFF)
TBL_HEAD = RGBColor(0xF5, 0xF0, 0xE8)
TBL_ALT  = RGBColor(0xFA, 0xF7, 0xF2)

FIGS = "/home/user/Pact3D/figures"

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
blank = prs.slide_layouts[6]


def bg(slide):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG


def tx(slide, l, t, w, h, text, sz=16, color=TEXT, bold=False,
       align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(sz)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = "Calibri"
    p.alignment = align
    return box


def bullets(slide, l, t, w, h, lines):
    """lines: [(text, size, color, bold), ...]"""
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    for i, (text, sz, col, bld) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = text
        p.font.size = Pt(sz)
        p.font.color.rgb = col
        p.font.bold = bld
        p.font.name = "Calibri"
        p.space_after = Pt(4)
        p.line_spacing = Pt(sz * 1.4)
    return box


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


def header(slide, subtitle=""):
    tx(slide, Inches(0.5), Inches(0.3), Inches(4), Inches(0.5),
       "Tracking", sz=28, bold=True, color=TEXT)
    if subtitle:
        tx(slide, Inches(0.5), Inches(0.75), Inches(8), Inches(0.4),
           subtitle, sz=18, color=TEXT)


def fig(slide, path, l, t, w, h=None):
    full = os.path.join(FIGS, path) if not path.startswith("/") else path
    if not os.path.exists(full) or os.path.getsize(full) < 100:
        rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h or Inches(2))
        rect.fill.solid()
        rect.fill.fore_color.rgb = TAN
        rect.line.color.rgb = TAN_DARK
        rect.line.width = Pt(1)
        return rect
    if h:
        return slide.shapes.add_picture(full, l, t, w, h)
    return slide.shapes.add_picture(full, l, t, width=w)


def tan_box(slide, l, t, w, h):
    rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    rect.fill.solid()
    rect.fill.fore_color.rgb = TAN
    rect.line.color.rgb = TAN_DARK
    rect.line.width = Pt(0.5)
    return rect


def arch_box(slide, l, t, w, h, title, sub="", border=TAN_DARK):
    rect = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    rect.fill.solid()
    rect.fill.fore_color.rgb = TAN
    rect.line.color.rgb = border
    rect.line.width = Pt(1.5)
    tx(slide, l + Inches(0.15), t + Inches(0.1), w - Inches(0.3), Inches(0.3),
       title, sz=14, bold=True, color=TEXT)
    if sub:
        tx(slide, l + Inches(0.15), t + Inches(0.45), w - Inches(0.3), Inches(0.3),
           sub, sz=11, color=DIM)


# ════════════════════════════════════════════════════════════════
# 1 — TITLE
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank)
s.background.fill.solid()
s.background.fill.fore_color.rgb = TEAL
tx(s, Inches(2), Inches(2.8), Inches(9), Inches(1.0),
   "Tracking", sz=72, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
tx(s, Inches(2), Inches(4.0), Inches(9), Inches(0.6),
   "3D Human Pose/Motion Tracking", sz=24, color=WHITE, align=PP_ALIGN.CENTER)
slide_num(s, 1)


# ════════════════════════════════════════════════════════════════
# 2 — WHERE THIS FITS (taxonomy, like PDF p3)
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "3D Human Pose/Motion Tracking")

bullets(s, Inches(0.5), Inches(1.4), Inches(12), Inches(5.0), [
    ("Local tracking (camera coordinates)", 22, DIM, False),
    ("", 10, DIM, False),
    ("Global tracking (world coordinates)", 22, DIM, False),
    ("", 10, DIM, False),
    ("Joint Human-Scene Tracking", 26, TEXT, True),
    ("    Track the person and the scene together", 18, TEXT, False),
    ("    Make it physically realistic", 18, TEXT, False),
    ("", 16, DIM, False),
    ("→  This is our direction", 22, ACCENT, True),
])
slide_num(s, 2)


# ════════════════════════════════════════════════════════════════
# 3 — THE PROBLEM (simple)
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "The Problem")

bullets(s, Inches(0.5), Inches(1.4), Inches(6.0), Inches(5.0), [
    ("Current methods track people well,", 22, TEXT, False),
    ("but the results aren't physical.", 22, TEXT, True),
    ("", 14, DIM, False),
    ("Feet slide on the ground", 20, TEXT, False),
    ("Bodies go through floors", 20, TEXT, False),
    ("Motion looks jittery", 20, TEXT, False),
    ("Can't use it in a physics simulator", 20, TEXT, False),
    ("", 14, DIM, False),
    ("Fix: add physics constraints", 22, ACCENT, True),
])

fig(s, "multiphys_teaser.png", Inches(7.0), Inches(1.4), Inches(5.8))
tx(s, Inches(7.0), Inches(4.5), Inches(5.8), Inches(0.4),
   "MultiPhys (CVPR'24) — adding physics fixes artifacts",
   sz=13, color=DIM)
slide_num(s, 3)


# ════════════════════════════════════════════════════════════════
# 4 — WHAT EXISTS (landscape with figures, like PDF p4-5)
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "Recent Methods")

bullets(s, Inches(0.5), Inches(1.2), Inches(5.5), Inches(5.5), [
    ("Body trackers (video → 3D body):", 18, TEXT, True),
    ("  GVHMR (SigAsia'24) — best accuracy, fast", 16, TEXT, False),
    ("  Human3R (arxiv'25) — real-time, multi-person", 16, TEXT, False),
    ("", 10, DIM, False),
    ("Scene reconstruction (video → 3D scene):", 18, TEXT, True),
    ("  Depth Anything 3 — depth + geometry from video", 16, TEXT, False),
    ("  CUT3R — underlies Human3R", 16, TEXT, False),
    ("", 10, DIM, False),
    ("Physics-aware methods:", 18, TEXT, True),
    ("  MultiPhys (CVPR'24) — physics simulator loop", 16, TEXT, False),
    ("  PhysHMR (SigAsia'25) — end-to-end physics", 16, TEXT, False),
    ("", 10, DIM, False),
    ("Nobody combines all three yet.", 20, ACCENT, True),
])

fig(s, "pdf_gvhmr_methods.png", Inches(6.3), Inches(1.0), Inches(6.5), Inches(4.5))
tx(s, Inches(6.3), Inches(5.6), Inches(6.5), Inches(0.4),
   "GVHMR, MultiPhys, CRISP — recent physics-aware trackers",
   sz=12, color=DIM)
slide_num(s, 4)


# ════════════════════════════════════════════════════════════════
# 5 — KEY TOOLS: GVHMR + HUMAN3R (with figures)
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "Key Tools")

# Left: GVHMR
bullets(s, Inches(0.5), Inches(1.2), Inches(5.8), Inches(2.5), [
    ("GVHMR (SigAsia'24)", 20, TEXT, True),
    ("Video in → 3D body in world coordinates", 16, TEXT, False),
    ("Very fast, very accurate", 16, TEXT, False),
    ("Single-person only", 16, DIM, False),
])
fig(s, "gvhmr_teaser.png", Inches(0.5), Inches(3.5), Inches(5.5))

# Right: Human3R
bullets(s, Inches(6.8), Inches(1.2), Inches(6.0), Inches(2.5), [
    ("Human3R (arxiv'25)", 20, TEXT, True),
    ("Video in → 3D people + scene, real-time", 16, TEXT, False),
    ("Multi-person, MIT license", 16, TEXT, False),
    ("Known issues: penetration, no physics", 16, DIM, False),
])
fig(s, "human3r_pipeline.png", Inches(6.8), Inches(3.5), Inches(5.8))

slide_num(s, 5)


# ════════════════════════════════════════════════════════════════
# 6 — EVIDENCE: PHYSICS HELPS (simple)
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "Physics Helps — Evidence")

bullets(s, Inches(0.5), Inches(1.4), Inches(12), Inches(4.5), [
    ("Multiple papers show: adding physics improves results", 22, TEXT, True),
    ("", 12, DIM, False),
    ("MultiPhys: 7x less body-ground penetration", 18, TEXT, False),
    ("CRISP: 8x lower failure rate", 18, TEXT, False),
    ("PhysDiff: 86% less physical error", 18, TEXT, False),
    ("LEMO: eliminates foot skating", 18, TEXT, False),
    ("", 12, DIM, False),
    ("Physics doesn't just look better — it improves accuracy too.", 20, ACCENT, True),
])

slide_num(s, 6)


# ════════════════════════════════════════════════════════════════
# 7 — PROPOSED APPROACH (simple pipeline)
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "Proposed Approach")

# Input box
arch_box(s, Inches(4.5), Inches(1.3), Inches(4.0), Inches(0.7),
         "Input: Video", border=ACCENT)

# Arrow
tx(s, Inches(5.5), Inches(2.1), Inches(2), Inches(0.4),
   "↓", sz=28, color=DIM, align=PP_ALIGN.CENTER)

# Two parallel boxes
arch_box(s, Inches(0.8), Inches(2.7), Inches(5.0), Inches(1.2),
         "Body Tracker",
         "GVHMR or Human3R → 3D body poses")

arch_box(s, Inches(7.2), Inches(2.7), Inches(5.0), Inches(1.2),
         "Scene Reconstruction",
         "Depth Anything 3 → 3D geometry")

# Arrows down
tx(s, Inches(2.8), Inches(4.0), Inches(1), Inches(0.4),
   "↓", sz=28, color=DIM, align=PP_ALIGN.CENTER)
tx(s, Inches(9.2), Inches(4.0), Inches(1), Inches(0.4),
   "↓", sz=28, color=DIM, align=PP_ALIGN.CENTER)

# Physics box (big, accented)
rect = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                           Inches(0.8), Inches(4.6), Inches(11.4), Inches(1.5))
rect.fill.solid()
rect.fill.fore_color.rgb = TAN
rect.line.color.rgb = ACCENT
rect.line.width = Pt(2)

tx(s, Inches(1.0), Inches(4.7), Inches(11), Inches(0.4),
   "Physics Refinement", sz=18, bold=True, color=ACCENT)
bullets(s, Inches(1.0), Inches(5.2), Inches(11), Inches(0.8), [
    ("Keep feet on ground  •  No body-floor penetration  •  Smooth motion  •  Stable balance", 15, TEXT, False),
])

# Arrow down to output
tx(s, Inches(5.5), Inches(6.2), Inches(2), Inches(0.4),
   "↓", sz=28, color=DIM, align=PP_ALIGN.CENTER)

tan_box(s, Inches(3.5), Inches(6.5), Inches(6), Inches(0.6))
tx(s, Inches(3.7), Inches(6.55), Inches(5.6), Inches(0.4),
   "Output: Physically realistic 3D motion + scene", sz=15, bold=True, color=ACCENT,
   align=PP_ALIGN.CENTER)

slide_num(s, 7)


# ════════════════════════════════════════════════════════════════
# 8 — WHAT MAKES THIS FEASIBLE
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "Why This Is Feasible")

bullets(s, Inches(0.5), Inches(1.4), Inches(6.0), Inches(5.0), [
    ("No training needed", 24, TEXT, True),
    ("    Use existing pretrained models", 18, DIM, False),
    ("    Just add physics on top", 18, DIM, False),
    ("", 14, DIM, False),
    ("Runs on 1 GPU", 24, TEXT, True),
    ("    < 16 GB VRAM", 18, DIM, False),
    ("", 14, DIM, False),
    ("Fully open-source stack", 24, TEXT, True),
    ("    Human3R (MIT), DA3 (Apache-2.0)", 18, DIM, False),
    ("    MuJoCo (Apache-2.0)", 18, DIM, False),
    ("", 14, DIM, False),
    ("7+ papers prove the approach works", 24, TEXT, True),
    ("    We're combining, not inventing", 18, DIM, False),
])

bullets(s, Inches(7.0), Inches(1.4), Inches(5.5), Inches(5.5), [
    ("8-week plan:", 22, TEXT, True),
    ("", 10, DIM, False),
    ("1–2  Setup + run existing models", 18, TEXT, False),
    ("3–4  Add physics constraints", 18, ACCENT, True),
    ("5     Human-object interaction (stretch)", 18, DIM, False),
    ("6–7  Evaluate on benchmarks", 18, TEXT, False),
    ("8     Demo + writeup", 18, TEXT, False),
])

slide_num(s, 8)


# ════════════════════════════════════════════════════════════════
# 9 — POSSIBLE DIRECTIONS (like PDF p20)
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "Possible Directions")

bullets(s, Inches(0.5), Inches(1.4), Inches(6.0), Inches(5.0), [
    ("Physics-aware tracking", 22, TEXT, True),
    ("    Terrain-aware ground contact", 18, TEXT, False),
    ("    Body non-penetration", 18, TEXT, False),
    ("    Contact estimation", 18, TEXT, False),
    ("", 14, DIM, False),
    ("Human-object interaction", 22, TEXT, True),
    ("    Rigid objects", 18, TEXT, False),
    ("    Deformable objects", 18, TEXT, False),
    ("", 14, DIM, False),
    ("Simulation-ready output", 22, TEXT, True),
    ("    Direct use in physics engines", 18, TEXT, False),
])

# Right: compact reference table
from pptx.util import Emu
nr, nc = 8, 3
rows = [
    ["Method", "Venue", "Note"],
    ["JOSH", "ICLR'26", "Best offline"],
    ["Human3R", "arxiv'25", "Real-time, multi-person"],
    ["DA3", "arxiv'25", "Scene geometry"],
    ["MultiPhys", "CVPR'24", "Physics simulator"],
    ["CRISP", "arxiv'25", "Physics + scene"],
    ["PhysHMR", "SigAsia'25", "End-to-end physics"],
    ["GVHMR", "SigAsia'24", "Best single-person"],
]
sh = s.shapes.add_table(nr, nc, Inches(7.0), Inches(1.4), Inches(5.5), Inches(3.0))
table = sh.table
table.columns[0].width = Inches(1.5)
table.columns[1].width = Inches(1.3)
table.columns[2].width = Inches(2.7)
for r in range(nr):
    for c in range(nc):
        cell = table.cell(r, c)
        cell.text = rows[r][c]
        for p in cell.text_frame.paragraphs:
            p.font.size = Pt(12)
            p.font.name = "Calibri"
            p.font.bold = (r == 0)
            p.font.color.rgb = TEXT
        cell.fill.solid()
        cell.fill.fore_color.rgb = TBL_HEAD if r == 0 else (TBL_ALT if r % 2 == 0 else BG)
        cell.margin_left = Inches(0.06)
        cell.margin_right = Inches(0.06)
        cell.margin_top = Inches(0.03)
        cell.margin_bottom = Inches(0.03)

slide_num(s, 9)


# ════════════════════════════════════════════════════════════════
# 10 — SUMMARY
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank)
s.background.fill.solid()
s.background.fill.fore_color.rgb = TEAL

bullets(s, Inches(1.5), Inches(1.5), Inches(10), Inches(5.0), [
    ("Track people in 3D from video", 28, WHITE, True),
    ("", 14, WHITE, False),
    ("Reconstruct the scene around them", 28, WHITE, True),
    ("", 14, WHITE, False),
    ("Add physics so it looks and acts real", 28, WHITE, True),
    ("", 20, WHITE, False),
    ("No training. One GPU. Open-source.", 24, WHITE, False),
])
slide_num(s, 10)


# ── Save ──
out = "/home/user/Pact3D/Pact3D_Presentation.pptx"
prs.save(out)
print(f"Saved {len(prs.slides)} slides to {out}")

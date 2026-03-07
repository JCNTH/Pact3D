#!/usr/bin/env python3
"""
Build Pact3D slides — white/tan palette matching tracking(1).pdf style.

Style reference (tracking(1).pdf):
- White background
- Bold black header top-left ("Tracking") repeated each slide
- Method/section subtitle below header
- Two-column: text/bullets left, paper figures right
- Dark maroon slide numbers in filled square, bottom-right
- Simple thin-border tables
- Light gray for de-emphasized text
- Very figure-heavy, academic, dense
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import os

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# ── Palette: white + tan (Cursor-inspired) ──
BG       = RGBColor(0xFF, 0xFF, 0xFF)  # white
TEXT     = RGBColor(0x1A, 0x1A, 0x1A)  # near-black
DIM      = RGBColor(0x99, 0x99, 0x99)  # gray (de-emphasized)
DIM2     = RGBColor(0xCC, 0xCC, 0xCC)  # lighter gray
ACCENT   = RGBColor(0x7B, 0x1E, 0x1E)  # dark maroon (slide numbers, like PDF)
TAN      = RGBColor(0xF0, 0xE6, 0xD3)  # warm tan (highlights/cards)
TAN_DARK = RGBColor(0xD4, 0xC4, 0xA8)  # darker tan (borders)
TBL_HEAD = RGBColor(0xF5, 0xF0, 0xE8)  # table header bg
TBL_ALT  = RGBColor(0xFA, 0xF7, 0xF2)  # table alternate row

FIGS = "/home/user/Pact3D/figures"

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
blank = prs.slide_layouts[6]


def bg(slide):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG


def tx(slide, l, t, w, h, text, sz=16, color=TEXT, bold=False,
       align=PP_ALIGN.LEFT, font="Calibri"):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(sz)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font
    p.alignment = align
    p.space_after = Pt(0)
    return box


def multi(slide, l, t, w, h, lines, font="Calibri"):
    """lines: [(text, size, color, bold), ...]"""
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(lines):
        text, sz, col, bld = item[0], item[1], item[2], item[3]
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = text
        p.font.size = Pt(sz)
        p.font.color.rgb = col
        p.font.bold = bld
        p.font.name = font
        p.space_after = Pt(2)
        p.line_spacing = Pt(sz * 1.3)
    return box


def slide_num(slide, n):
    """Dark maroon square with white number, bottom-right (like PDF)."""
    sz = Inches(0.4)
    x = SLIDE_W - Inches(0.55)
    y = SLIDE_H - Inches(0.55)
    rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, sz, sz)
    rect.fill.solid()
    rect.fill.fore_color.rgb = ACCENT
    rect.line.fill.background()
    tf = rect.text_frame
    tf.paragraphs[0].text = str(n)
    tf.paragraphs[0].font.size = Pt(12)
    tf.paragraphs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.name = "Calibri"
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE


def header(slide, subtitle=""):
    """Consistent header: bold 'Tracking' top-left + subtitle."""
    tx(slide, Inches(0.5), Inches(0.3), Inches(4), Inches(0.5),
       "Tracking", sz=28, bold=True, color=TEXT)
    if subtitle:
        tx(slide, Inches(0.5), Inches(0.75), Inches(8), Inches(0.4),
           subtitle, sz=18, color=TEXT)


def fig(slide, path, l, t, w, h=None):
    """Add an image, scaling to width. Returns shape or None."""
    full = os.path.join(FIGS, path) if not path.startswith("/") else path
    if not os.path.exists(full) or os.path.getsize(full) < 100:
        # Placeholder tan box
        rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h or Inches(2))
        rect.fill.solid()
        rect.fill.fore_color.rgb = TAN
        rect.line.color.rgb = TAN_DARK
        rect.line.width = Pt(1)
        tf = rect.text_frame
        tf.paragraphs[0].text = f"[{os.path.basename(path)}]"
        tf.paragraphs[0].font.size = Pt(10)
        tf.paragraphs[0].font.color.rgb = DIM
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        return rect
    if h:
        return slide.shapes.add_picture(full, l, t, w, h)
    else:
        return slide.shapes.add_picture(full, l, t, width=w)


def tbl(slide, l, t, w, rows, col_ws=None, highlights=None):
    nr, nc = len(rows), len(rows[0])
    sh = slide.shapes.add_table(nr, nc, l, t, w, Inches(0.35 * nr))
    table = sh.table
    if col_ws:
        for i, cw in enumerate(col_ws):
            table.columns[i].width = cw
    for r in range(nr):
        for c in range(nc):
            cell = table.cell(r, c)
            cell.text = str(rows[r][c])
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(11)
                p.font.name = "Calibri"
                p.alignment = PP_ALIGN.CENTER if c > 0 else PP_ALIGN.LEFT
                if r == 0:
                    p.font.bold = True
                    p.font.color.rgb = TEXT
                elif highlights and r in highlights:
                    p.font.bold = True
                    p.font.color.rgb = ACCENT
                else:
                    p.font.color.rgb = TEXT
            cell.fill.solid()
            if r == 0:
                cell.fill.fore_color.rgb = TBL_HEAD
            elif highlights and r in highlights:
                cell.fill.fore_color.rgb = TAN
            else:
                cell.fill.fore_color.rgb = TBL_ALT if r % 2 == 0 else BG
            cell.margin_left = Inches(0.06)
            cell.margin_right = Inches(0.06)
            cell.margin_top = Inches(0.03)
            cell.margin_bottom = Inches(0.03)
    return sh


def tan_box(slide, l, t, w, h):
    rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    rect.fill.solid()
    rect.fill.fore_color.rgb = TAN
    rect.line.color.rgb = TAN_DARK
    rect.line.width = Pt(0.5)
    return rect


# ════════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE (teal bg like PDF page 1)
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank)
s.background.fill.solid()
s.background.fill.fore_color.rgb = RGBColor(0x00, 0x88, 0x80)  # teal like PDF
tx(s, Inches(2), Inches(2.8), Inches(9), Inches(1.0),
   "Tracking", sz=72, bold=True,
   color=RGBColor(0xFF, 0xFF, 0xFF), align=PP_ALIGN.CENTER)
tx(s, Inches(2), Inches(4.0), Inches(9), Inches(0.6),
   "3D Human Pose/Motion Tracking",
   sz=24, color=RGBColor(0xFF, 0xFF, 0xFF), align=PP_ALIGN.CENTER)
slide_num(s, 1)


# ════════════════════════════════════════════════════════════════
# SLIDE 2 — OVERVIEW / TAXONOMY (like PDF page 3)
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "3D Human Pose/Motion Tracking")

multi(s, Inches(0.5), Inches(1.3), Inches(12), Inches(5.5), [
    ("Local Human Mesh Reconstruction/Tracking (in camera coords.)", 22, DIM, False),
    ("    • Single image / Monocular video", 16, DIM, False),
    ("    • Single-person / Multi-person", 16, DIM, False),
    ("", 10, DIM, False),
    ("Global Human Motion Tracking (in world coords.)", 22, DIM, False),
    ("    • Optimization / Regression", 16, DIM, False),
    ("    • Physics-aware", 16, DIM, False),
    ("", 10, DIM, False),
    ("Joint Human-Scene Tracking", 22, TEXT, True),
    ("    • Global human motion estimation", 16, TEXT, False),
    ("    • Generic scene reconstruction", 16, TEXT, False),
    ("    • Interaction (scene/objects)", 16, TEXT, False),
    ("    • Physics-aware, simulation-ready", 16, TEXT, False),
    ("", 14, DIM, False),
    ("→  Our focus: physics-aware joint human-scene tracking", 18, ACCENT, True),
])
slide_num(s, 2)


# ════════════════════════════════════════════════════════════════
# SLIDE 3 — LANDSCAPE TABLE (like PDF page 7)
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "3D Human Pose/Motion Tracking")
tx(s, Inches(0.5), Inches(1.0), Inches(5), Inches(0.4),
   "• Global Human Motion Tracking (in world coords.)", sz=16, bold=True)

tbl(s, Inches(0.5), Inches(1.6), Inches(12.3), [
    ["Method", "Venue", "Note"],
    ["Yu et al.", "TOG'21", "Physics"],
    ["GLAMR", "CVPR'22", ""],
    ["D&D", "ECCV'22", "Physics"],
    ["TRACE", "CVPR'23", ""],
    ["SLAHMR", "CVPR'23", "Optimization"],
    ["WHAM", "CVPR'24", ""],
    ["MultiPhys", "CVPR'24", "Physics"],
    ["TRAM", "ECCV'24", ""],
    ["GVHMR", "SigAsia'24", "Gravity-view coords"],
    ["PhysHMR", "SigAsia'25", "End-to-end physics"],
    ["CRISP", "arxiv'25", "Physics + scene"],
], col_ws=[Inches(2.0), Inches(2.0), Inches(8.3)],
   highlights={9, 10, 11})

# Right side: method figures from PDF
fig(s, "pdf_gvhmr_methods.png", Inches(6.5), Inches(1.6), Inches(6.3), Inches(4.3))

slide_num(s, 3)


# ════════════════════════════════════════════════════════════════
# SLIDE 4 — THE PROBLEM
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "The Problem")

multi(s, Inches(0.5), Inches(1.3), Inches(6.0), Inches(5.0), [
    ("Current trackers are good — but not physical.", 20, TEXT, True),
    ("", 10, DIM, False),
    ("Even the best (GVHMR, SigAsia'24) still has:", 16, TEXT, False),
    ("", 8, DIM, False),
    ("• Foot skating: 3.0–4.4mm sliding", 16, TEXT, False),
    ("• Ground penetration: bodies clip through floors", 16, TEXT, False),
    ("• Temporal jitter: 12.8–22.5 units", 16, TEXT, False),
    ("• No simulation readiness", 16, TEXT, False),
    ("", 12, DIM, False),
    ("The missing piece:", 18, TEXT, True),
    ("Physics constraints — gravity, contact,", 18, ACCENT, True),
    ("friction, and collision.", 18, ACCENT, True),
    ("", 12, DIM, False),
    ("Approach = body tracker + scene geometry", 16, TEXT, False),
    ("             + physics refinement layer", 16, TEXT, False),
])

# MultiPhys figure showing physics correction
fig(s, "multiphys_teaser.png", Inches(7.0), Inches(1.3), Inches(5.8))

tx(s, Inches(7.0), Inches(4.2), Inches(5.8), Inches(0.3),
   "MultiPhys (CVPR'24): physics simulator corrects body motion", sz=11, color=DIM)

slide_num(s, 4)


# ════════════════════════════════════════════════════════════════
# SLIDE 5 — EVIDENCE: PHYSICS WORKS
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "Evidence: Physics Constraints Work")

tbl(s, Inches(0.5), Inches(1.3), Inches(12.3), [
    ["Study", "What Was Added", "Key Result"],
    ["MultiPhys (CVPR'24)", "MuJoCo simulation loop", "7x less penetration"],
    ["MultiPhys", "Ground plane contact", "5x less ground pen."],
    ["CRISP (arxiv'25)", "Planar scene + RL tracking", "8x lower failure rate"],
    ["PhysDiff (ICCV'23)", "Physics in diffusion", "86% less physical error"],
    ["PROX (ICCV'19)", "SDF + contact terms", "24% better V2V"],
    ["LEMO (ICCV'21)", "Friction + smoothness", "Eliminates skating + jitter"],
    ["PhysHMR (SigAsia'25)", "End-to-end visual→physics", "Best accuracy + physics"],
], col_ws=[Inches(3.2), Inches(4.5), Inches(4.6)])

tan_box(s, Inches(0.5), Inches(5.2), Inches(12.3), Inches(1.0))
multi(s, Inches(0.7), Inches(5.3), Inches(11.9), Inches(0.8), [
    ("Key insight: physics doesn't just look better — it improves accuracy.", 16, TEXT, True),
    ("MultiPhys: W-MPJPE 177.1 → 174.7mm after physics correction.", 14, DIM, False),
])

slide_num(s, 5)


# ════════════════════════════════════════════════════════════════
# SLIDE 6 — DESIGN LESSON: TWO-STAGE HURTS
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "PhysHMR (SIGGRAPH Asia'25)")

multi(s, Inches(0.5), Inches(1.3), Inches(6.5), Inches(3.0), [
    ("Critical finding: two-stage RL post-correction can hurt.", 18, TEXT, True),
    ("", 10, DIM, False),
    ("GVHMR alone:                          5.65mm foot sliding", 15, TEXT, False),
    ("GVHMR + RL post-correction:    12.71mm foot sliding (2.2x worse)", 15, ACCENT, True),
    ("PhysHMR (end-to-end):              4.60mm foot sliding (best)", 15, TEXT, False),
    ("", 10, DIM, False),
    ("Why? Balance-recovery creates new limb artifacts.", 15, DIM, False),
    ("", 10, DIM, False),
    ("Our approach: optimization-based energy minimization", 16, TEXT, True),
    ("(PROX/LEMO style). No balance artifacts.", 16, TEXT, False),
])

# Placeholder for PhysHMR comparison figure
tan_box(s, Inches(7.3), Inches(1.3), Inches(5.5), Inches(3.5))
multi(s, Inches(7.5), Inches(1.5), Inches(5.1), Inches(3.0), [
    ("[PhysHMR comparison figure]", 12, DIM, False),
    ("", 8, DIM, False),
    ("Two-stage pipeline:", 14, TEXT, True),
    ("  Kinematic → RL correction", 13, DIM, False),
    ("  Balance recovery → arm flailing", 13, DIM, False),
    ("", 8, DIM, False),
    ("Optimization pipeline (ours):", 14, TEXT, True),
    ("  Kinematic → energy minimization", 13, DIM, False),
    ("  Direct constraint satisfaction", 13, DIM, False),
])

slide_num(s, 6)


# ════════════════════════════════════════════════════════════════
# SLIDE 7 — BODY TRACKER: GVHMR (like PDF page 4 style)
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "GVHMR (SIGGRAPH Asia'24)")

multi(s, Inches(0.5), Inches(1.2), Inches(5.5), Inches(3.0), [
    ("Input: monocular video", 14, ACCENT, True),
    ("Output: SMPL in world coordinates + global trajectory", 14, ACCENT, True),
    ("", 8, DIM, False),
    ("• Gravity-View coordinate system", 15, TEXT, False),
    ("    (defined by world gravity + camera view direction)", 13, DIM, False),
    ("• Per-frame estimation → no error accumulation", 15, TEXT, False),
    ("• Relative transformer with RoPE", 15, TEXT, False),
    ("• Camera rotations from visual odometry / gyroscope", 15, TEXT, False),
    ("", 8, DIM, False),
    ("Speed: ~5000 FPS core network", 15, TEXT, True),
    ("Best on 3DPW: PA-MPJPE 36.2, MPJPE 55.6", 14, TEXT, False),
    ("Best on EMDB-2: WA-MPJPE 111.0", 14, TEXT, False),
    ("Lowest foot sliding: 3.0mm (RICH)", 14, TEXT, False),
])

# Figures
fig(s, "gvhmr_teaser.png", Inches(6.5), Inches(1.0), Inches(6.3))

slide_num(s, 7)


# ════════════════════════════════════════════════════════════════
# SLIDE 8 — BODY TRACKER: HUMAN3R (like PDF page 17)
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "Human3R (arxiv'25)")

tx(s, Inches(0.5), Inches(0.95), Inches(12), Inches(0.3),
   "Inference with One model, One stage; Training in One day using One GPU", sz=12, color=DIM)

multi(s, Inches(0.5), Inches(1.4), Inches(5.5), Inches(3.5), [
    ("Input: a stream of RGB images", 14, ACCENT, True),
    ("Output: 4D human-scene in real time", 14, ACCENT, True),
    ("   Multi-person meshes, camera params, dense 3D", 13, DIM, False),
    ("", 8, DIM, False),
    ("• CUT3R + Multi-HMR (fine-tune human params only)", 15, TEXT, False),
    ("• Real-time: 15 FPS, 8 GB GPU", 15, TEXT, False),
    ("• MIT License", 15, TEXT, True),
    ("", 8, DIM, False),
    ("Limitations (from paper):", 15, TEXT, True),
    ("    1. Penetration", 14, ACCENT, False),
    ("    2. HOI", 14, ACCENT, False),
    ("", 8, DIM, False),
    ("→ These are exactly what our physics layer fixes.", 16, ACCENT, True),
])

# Human3R pipeline figure
fig(s, "human3r_pipeline.png", Inches(6.2), Inches(1.0), Inches(6.8))

# Lower: extracted Human3R figure from PDF
fig(s, "pdf_human3r.png", Inches(6.2), Inches(3.5), Inches(6.8))

slide_num(s, 8)


# ════════════════════════════════════════════════════════════════
# SLIDE 9 — COMPARISON TABLE (like PDF page 16 JOSH table style)
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "Body Tracker Comparison")

# Main comparison table — simplified
tbl(s, Inches(0.5), Inches(1.3), Inches(12.3), [
    ["Method", "Venue", "PA-MPJPE↓", "WA-MPJPE↓", "Foot Slide↓", "World?", "Multi?", "Speed"],
    ["GLAMR", "CVPR'22", "51.1", "280.8", "20.7", "Yes", "No", "Slow"],
    ["SLAHMR", "CVPR'23", "55.9", "326.9", "14.5", "Yes", "Yes", "~4 hrs"],
    ["WHAM", "CVPR'24", "35.9", "135.6", "4.4", "Yes", "No", "~5s/1K"],
    ["GVHMR", "SigAsia'24", "36.2", "111.0", "3.5", "Yes", "No", "0.28s/1.4K"],
    ["Human3R", "arxiv'25", "44.1", "112.2", "—", "Yes", "Yes", "15 FPS"],
    ["JOSH", "ICLR'26", "—", "68.9", "1.8", "Yes", "Yes", "Offline"],
], col_ws=[Inches(1.5), Inches(1.5), Inches(1.6), Inches(1.8), Inches(1.6), Inches(1.0), Inches(1.0), Inches(2.3)],
   highlights={4, 5})

# JOSH results figure from PDF
fig(s, "pdf_josh_results.png", Inches(0.5), Inches(4.3), Inches(6.0), Inches(3.0))

multi(s, Inches(6.8), Inches(4.5), Inches(5.8), Inches(2.5), [
    ("Recommendation:", 16, TEXT, True),
    ("", 6, DIM, False),
    ("Primary: GVHMR", 16, ACCENT, True),
    ("  Best accuracy + speed. Single-person.", 14, DIM, False),
    ("", 6, DIM, False),
    ("Alternative: Human3R", 16, ACCENT, True),
    ("  Multi-person + scene. MIT license.", 14, DIM, False),
    ("  Physics layer fixes its weaknesses.", 14, DIM, False),
])

slide_num(s, 9)


# ════════════════════════════════════════════════════════════════
# SLIDE 10 — SCENE GEOMETRY: DA3 (like PDF page 10)
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "Depth Anything 3 (arxiv'25)")

multi(s, Inches(0.5), Inches(1.2), Inches(5.5), Inches(2.5), [
    ("Recovers geometry & 3DGS from", 15, TEXT, False),
    ("*Depth-ray representation", 15, TEXT, False),
    ("", 8, DIM, False),
    ("Input: any number of images (unknown cameras)", 14, ACCENT, True),
    ("Output: depth, raymaps, pointmaps, 3DGS", 14, ACCENT, True),
    ("", 8, DIM, False),
    ("• 78 FPS (DA3-Large)", 15, TEXT, False),
    ("• < 12 GB VRAM with streaming", 15, TEXT, False),
    ("• Any video length", 15, TEXT, False),
    ("• Apache-2.0 license", 15, TEXT, True),
])

# DA3 figures
fig(s, "da3_teaser.png", Inches(6.2), Inches(0.8), Inches(6.8))

fig(s, "pdf_da3.png", Inches(0.5), Inches(4.5), Inches(6.0), Inches(2.5))

multi(s, Inches(7.0), Inches(4.5), Inches(5.5), Inches(2.5), [
    ("Why DA3 over alternatives:", 14, TEXT, True),
    ("", 4, DIM, False),
    ("1. Only method: metric depth + camera", 13, TEXT, False),
    ("   poses + pointmaps + streaming", 13, TEXT, False),
    ("2. GPU feasible: 78 FPS, <12 GB", 13, TEXT, False),
    ("3. Depth sufficient — physics corrects", 13, TEXT, False),
    ("   residual errors", 13, TEXT, False),
    ("4. Apache-2.0 → fully open stack", 13, TEXT, False),
])

slide_num(s, 10)


# ════════════════════════════════════════════════════════════════
# SLIDE 11 — SCENE COMPARISON TABLE (like PDF page 7)
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "Scene Geometry Comparison")

tbl(s, Inches(0.5), Inches(1.3), Inches(12.3), [
    ["Method", "Venue", "Metric Depth", "Camera Poses", "Streaming", "License", "Note"],
    ["DUSt3R", "CVPR'24", "Yes", "Yes", "No (quadratic)", "CC BY-NC-SA", "Static (2 images)"],
    ["VGGT", "CVPR'25", "Yes", "Yes", "No (quadratic)", "Custom", "Static"],
    ["CUT3R", "CVPR'25", "Yes", "Yes", "Yes (8 GB)", "CC BY-NC-SA", "Dynamic, online"],
    ["DA3", "arxiv'25", "Yes", "Yes", "Yes (<12 GB)", "Apache-2.0", "Dynamic (vs. VGGT)"],
    ["Metric3D v2", "", "Best", "No", "No", "Apache-2.0", "Per-frame only"],
    ["MoGe-2", "", "Yes", "No", "No", "MIT", "Per-frame only"],
], col_ws=[Inches(1.5), Inches(1.2), Inches(1.5), Inches(1.7), Inches(2.0), Inches(2.0), Inches(2.4)],
   highlights={4, 5})

# CUT3R figure from PDF
fig(s, "pdf_cut3r.png", Inches(3.5), Inches(4.5), Inches(6.0), Inches(2.5))

multi(s, Inches(0.5), Inches(4.5), Inches(3.0), Inches(2.5), [
    ("Selected: DA3", 16, ACCENT, True),
    ("• Metric depth + poses", 14, TEXT, False),
    ("• Streaming (any length)", 14, TEXT, False),
    ("• Apache-2.0", 14, TEXT, False),
    ("", 8, DIM, False),
    ("Fallback: CUT3R", 14, DIM, False),
    ("(underlies Human3R)", 14, DIM, False),
])

slide_num(s, 11)


# ════════════════════════════════════════════════════════════════
# SLIDE 12 — JOINT HUMAN-SCENE (like PDF page 16)
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "Joint Human-Scene Tracking")

tbl(s, Inches(0.5), Inches(1.3), Inches(12.3), [
    ["Method", "Venue", "Online?", "Multi-Person?", "Scene?", "Note"],
    ["HOSNeRF", "ICCV'23", "No", "No", "NeRF", "Per-video training (5 days)"],
    ["VGGT", "CVPR'25", "No", "No", "Dense", "Static scenes only"],
    ["Easi3R", "ICCV'25", "No", "No", "Dynamic", "Training-free (ext DUSt3R)"],
    ["JOSH", "ICLR'26", "No", "Yes", "Yes", "Best offline: WA-MPJPE 68.9"],
    ["Human3R", "arxiv'25", "Yes", "Yes", "Dense", "Best online: WA-MPJPE 112.2"],
    ["SHARE", "arxiv'25", "No", "No", "Pointmap", "TRAM + MoGe-2"],
], col_ws=[Inches(1.5), Inches(1.2), Inches(1.0), Inches(1.6), Inches(1.2), Inches(5.8)],
   highlights={5, 6})

multi(s, Inches(0.5), Inches(4.5), Inches(6.0), Inches(2.5), [
    ("Possible directions:", 18, ACCENT, True),
    ("• Physics-aware (terrain, ground contact)", 16, TEXT, False),
    ("• Simulation-ready output", 16, TEXT, False),
    ("• Multi-person contact handling", 16, TEXT, False),
    ("• Human-object interaction", 16, TEXT, False),
])

multi(s, Inches(7.0), Inches(4.5), Inches(5.5), Inches(2.5), [
    ("Why Human3R as base:", 16, TEXT, True),
    ("", 4, DIM, False),
    ("• Only online, real-time, unified system", 14, TEXT, False),
    ("• MIT licensed", 14, TEXT, False),
    ("• Explicit failure modes =", 14, TEXT, False),
    ("  exactly what physics fixes", 14, ACCENT, True),
    ("• Adding physics could close gap", 14, TEXT, False),
    ("  vs. JOSH while staying real-time", 14, TEXT, False),
])

slide_num(s, 12)


# ════════════════════════════════════════════════════════════════
# SLIDE 13 — ARCHITECTURE
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "Proposed Pipeline")

# Draw architecture as boxes with arrows
def arch_box(slide, l, t, w, h, title, items, border_col=TAN_DARK):
    rect = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    rect.fill.solid()
    rect.fill.fore_color.rgb = TAN
    rect.line.color.rgb = border_col
    rect.line.width = Pt(1.5)
    lines = [(title, 13, TEXT, True)]
    for item in items:
        lines.append((f"  {item}", 11, DIM, False))
    multi(slide, l + Inches(0.1), t + Inches(0.05), w - Inches(0.2), h - Inches(0.1), lines)

# Input
arch_box(s, Inches(4.8), Inches(1.2), Inches(3.5), Inches(0.6),
         "Monocular RGB Video", [], ACCENT)

# Body tracker
arch_box(s, Inches(0.5), Inches(2.4), Inches(4.5), Inches(1.6),
         "Body Tracker (GVHMR / Human3R)", [
             "→ SMPL(-X) poses per frame",
             "→ Global root trajectory",
             "→ World coordinates",
         ])

# Scene backbone
arch_box(s, Inches(8.3), Inches(2.4), Inches(4.5), Inches(1.6),
         "Scene Backbone (DA3-Metric-Large)", [
             "→ Metric depth + pointmaps",
             "→ Camera poses",
             "→ Streaming (<12 GB)",
         ])

# Physics layer — larger box
rect = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                           Inches(0.5), Inches(4.6), Inches(12.3), Inches(2.5))
rect.fill.solid()
rect.fill.fore_color.rgb = TAN
rect.line.color.rgb = ACCENT
rect.line.width = Pt(2)

tx(s, Inches(0.7), Inches(4.7), Inches(11.9), Inches(0.3),
   "Physics Refinement Layer (optimization-based, training-free)", sz=14, bold=True, color=ACCENT)

# Energy terms
energies_left = [
    "Ground Plane — RANSAC on pointmap",
    "Collision Mesh — pointmap → mesh",
    "Contact Detection — foot velocity + proximity",
]
energies_right = [
    "E_contact — pin feet to surface (PROX)",
    "E_penetration — SDF non-intersection (PROX)",
    "E_friction — no sliding during contact (LEMO)",
    "E_stability — CoM/CoP balance (IPMAN)",
    "E_smooth — temporal jerk penalty",
]

multi(s, Inches(0.7), Inches(5.1), Inches(5.5), Inches(1.8), [
    ("Scene proxy:", 12, TEXT, True),
] + [(f"  • {e}", 11, TEXT, False) for e in energies_left] + [
    ("", 6, DIM, False),
    ("MuJoCo validation (verify, don't correct)", 12, DIM, False),
])

multi(s, Inches(6.5), Inches(5.1), Inches(6.0), Inches(1.8), [
    ("Energy minimization:", 12, TEXT, True),
] + [(f"  • {e}", 11, TEXT, False) for e in energies_right])

# Arrows (simple text arrows)
tx(s, Inches(5.8), Inches(1.55), Inches(1.5), Inches(0.3), "↓              ↓", sz=20, color=DIM, align=PP_ALIGN.CENTER)
tx(s, Inches(2.2), Inches(4.1), Inches(1), Inches(0.3), "↓", sz=20, color=DIM, align=PP_ALIGN.CENTER)
tx(s, Inches(10.0), Inches(4.1), Inches(1), Inches(0.3), "↓", sz=20, color=DIM, align=PP_ALIGN.CENTER)

slide_num(s, 13)


# ════════════════════════════════════════════════════════════════
# SLIDE 14 — EVALUATION
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "Evaluation Strategy & Targets")

tbl(s, Inches(0.5), Inches(1.3), Inches(6.5), [
    ["Metric", "Current SOTA", "Our Target"],
    ["Foot Sliding", "3.0 mm (GVHMR)", "< 1 mm"],
    ["Ground Pen.", "2.4 mm (MultiPhys)", "< 1 mm"],
    ["Inter-body Pen.", "18.7 mm (MultiPhys)", "< 20 mm"],
    ["PA-MPJPE", "36.2 mm (GVHMR)", "No degradation"],
], col_ws=[Inches(2.0), Inches(2.3), Inches(2.2)],
   highlights={1, 2})

multi(s, Inches(7.5), Inches(1.3), Inches(5.3), Inches(3.0), [
    ("Datasets:", 16, TEXT, True),
    ("", 6, DIM, False),
    ("RICH (primary)", 15, TEXT, True),
    ("  Scene scans + vertex contact GT", 13, DIM, False),
    ("  + reliable global coordinates", 13, DIM, False),
    ("", 6, DIM, False),
    ("EMDB-2", 15, TEXT, True),
    ("  2.3cm pose accuracy · moving cameras", 13, DIM, False),
    ("", 6, DIM, False),
    ("3DPW", 15, TEXT, True),
    ("  Standard benchmark", 13, DIM, False),
    ("", 6, DIM, False),
    ("Hi4D", 15, TEXT, True),
    ("  Multi-person close interaction", 13, DIM, False),
])

tan_box(s, Inches(0.5), Inches(4.9), Inches(12.3), Inches(0.7))
tx(s, Inches(0.7), Inches(5.0), Inches(11.9), Inches(0.5),
   "RICH is primary: uniquely provides scene scans + vertex contact GT + global coords.",
   sz=14, color=TEXT, bold=True)

slide_num(s, 14)


# ════════════════════════════════════════════════════════════════
# SLIDE 15 — TIMELINE
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "8-Week Plan")

weeks = [
    ("1", "Setup", "Run GVHMR + DA3 on test videos"),
    ("2", "Scene", "Ground plane RANSAC, gravity alignment"),
    ("3", "Contact", "Foot contact detection, loss terms"),
    ("4", "Physics", "MuJoCo integration, root + feet optim."),
    ("5", "HOI", "Hand/object non-penetration (stretch)"),
    ("6", "Eval", "RICH, EMDB-2, 3DPW + ablations"),
    ("7", "Robustness", "Chunking, stitching, edge cases"),
    ("8", "Demo", "Side-by-side renders, technical report"),
]

for i, (wk, title, desc) in enumerate(weeks):
    y = Inches(1.3) + i * Inches(0.7)

    # Tan highlight for core weeks (1-4)
    if i < 4:
        tan_box(s, Inches(0.5), y, Inches(8.0), Inches(0.55))

    tx(s, Inches(0.7), y + Inches(0.08), Inches(0.4), Inches(0.35),
       wk, sz=16, bold=True, color=ACCENT if i < 4 else DIM)
    tx(s, Inches(1.3), y + Inches(0.08), Inches(1.5), Inches(0.35),
       title, sz=15, bold=True, color=TEXT)
    tx(s, Inches(3.0), y + Inches(0.08), Inches(5.5), Inches(0.35),
       desc, sz=14, color=TEXT if i < 4 else DIM)

multi(s, Inches(9.0), Inches(1.3), Inches(3.8), Inches(3.5), [
    ("Compute:", 16, TEXT, True),
    ("", 6, DIM, False),
    ("< 16 GB peak VRAM", 20, ACCENT, True),
    ("< 2 min per 1K frames", 20, ACCENT, True),
    ("1 GPU (RTX 3090/4090)", 20, ACCENT, True),
    ("", 10, DIM, False),
    ("No training required.", 15, TEXT, True),
    ("Compose pretrained models", 14, DIM, False),
    ("+ optimization.", 14, DIM, False),
])

multi(s, Inches(9.0), Inches(5.0), Inches(3.8), Inches(1.5), [
    ("License stack:", 16, TEXT, True),
    ("Human3R — MIT", 14, TEXT, False),
    ("DA3 — Apache-2.0", 14, TEXT, False),
    ("MuJoCo — Apache-2.0", 14, TEXT, False),
    ("Fully open.", 14, ACCENT, True),
])

slide_num(s, 15)


# ════════════════════════════════════════════════════════════════
# SLIDE 16 — RISKS
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "Risks & Mitigations")

risks = [
    ("DA3 depth too noisy", "Plane-only proxy; physics corrects residual errors"),
    ("MuJoCo integration complex", "Start ground-only; MultiPhys as reference impl."),
    ("GVHMR license restricts publication", "Fall back to Human3R (MIT) — modular swap"),
    ("Physics degrades accuracy", "7+ papers show it helps; ablate each energy term"),
    ("Week 5 HOI too ambitious", "HOI is stretch goal; core value is weeks 1-4"),
]

for i, (risk, mit) in enumerate(risks):
    y = Inches(1.3) + i * Inches(1.1)
    tx(s, Inches(0.5), y, Inches(5.5), Inches(0.35),
       f"• {risk}", sz=15, bold=True, color=TEXT)
    tx(s, Inches(0.7), y + Inches(0.4), Inches(5.3), Inches(0.35),
       f"→ {mit}", sz=13, color=DIM)

multi(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(5.0), [
    ("Why this is low-hanging fruit:", 16, TEXT, True),
    ("", 8, DIM, False),
    ("1. No training — compose pretrained models", 14, TEXT, False),
    ("", 4, DIM, False),
    ("2. Physics engines (MuJoCo) are mature,", 14, TEXT, False),
    ("   Apache-2.0, well-documented", 14, DIM, False),
    ("", 4, DIM, False),
    ("3. Biomechanics constraints are", 14, TEXT, False),
    ("   well-established from literature", 14, DIM, False),
    ("", 4, DIM, False),
    ("4. Clear, measurable improvements", 14, TEXT, False),
    ("   on standard benchmarks", 14, DIM, False),
    ("", 4, DIM, False),
    ("5. 7+ papers prove the approach works —", 14, TEXT, False),
    ("   we're combining, not inventing", 14, DIM, False),
])

slide_num(s, 16)


# ════════════════════════════════════════════════════════════════
# SLIDE 17 — SUMMARY / DIRECTIONS (like PDF page 20)
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
header(s, "3D Human Pose/Motion Tracking")
tx(s, Inches(0.5), Inches(1.0), Inches(5), Inches(0.4),
   "• Joint Human-Scene Tracking", sz=16, bold=True)

multi(s, Inches(0.7), Inches(1.5), Inches(5.5), Inches(3.5), [
    ("Global human motion estimation", 15, TEXT, False),
    ("Generic scene reconstruction", 15, TEXT, False),
    ("Interaction (scene/objects)", 15, TEXT, False),
    ("Physics-aware", 15, TEXT, False),
    ("", 10, DIM, False),
    ("Possible directions:", 18, ACCENT, True),
    ("• Physics-aware, simulation-ready", 16, TEXT, True),
    ("    • Terrain, ground contact", 14, TEXT, False),
    ("    • Non-penetration", 14, TEXT, False),
    ("    • Contact estimation", 14, TEXT, False),
    ("• Human-object interaction", 16, TEXT, True),
    ("    • Rigid object", 14, TEXT, False),
    ("    • Deformable object", 14, TEXT, False),
])

# Right side — compact method table
tbl(s, Inches(6.5), Inches(1.3), Inches(6.3), [
    ["Method", "Venue", "Note"],
    ["JOSH", "ICLR'26", "opt; dynamic; best offline"],
    ["Human3R", "arxiv'25", "ff; dynamic online; (CUT3R+SMPL)"],
    ["DA3", "arxiv'25", "ff; 3D GT; dynamic; (vs. VGGT)"],
    ["SHARE", "arxiv'25", "opt; dynamic"],
    ["MultiPhys", "CVPR'24", "Physics simulator"],
    ["CRISP", "arxiv'25", "Physics + scene"],
    ["PhysHMR", "SigAsia'25", "End-to-end physics"],
], col_ws=[Inches(1.5), Inches(1.3), Inches(3.5)],
   highlights={1, 2, 3})

tan_box(s, Inches(6.5), Inches(5.3), Inches(6.3), Inches(1.2))
multi(s, Inches(6.7), Inches(5.4), Inches(5.9), Inches(1.0), [
    ("Combine Human3R + DA3 + physics layer", 15, ACCENT, True),
    ("to produce simulation-ready motion from video.", 15, ACCENT, False),
    ("Training-free. Single GPU. 8 weeks.", 14, TEXT, True),
])

slide_num(s, 17)


# ── Save ──
out = "/home/user/Pact3D/Pact3D_Presentation.pptx"
prs.save(out)
print(f"Saved {len(prs.slides)} slides to {out}")

#!/usr/bin/env python3
"""Build Pact3D presentation — minimal two-color design."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.chart import XL_CHART_TYPE

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# ── Two colors only ──
BG    = RGBColor(0x0A, 0x0A, 0x0A)   # near-black
FG    = RGBColor(0xF5, 0xF5, 0xF5)   # off-white primary
DIM   = RGBColor(0x6B, 0x6B, 0x6B)   # muted secondary
DIMMER = RGBColor(0x3A, 0x3A, 0x3A)  # very muted (lines, borders)
ACCENT = RGBColor(0xF5, 0xF5, 0xF5)  # same as FG — emphasis via bold/size only

# Table colors
TBL_HEAD_BG = RGBColor(0x18, 0x18, 0x18)
TBL_ROW_BG  = RGBColor(0x0F, 0x0F, 0x0F)
TBL_ALT_BG  = RGBColor(0x14, 0x14, 0x14)

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
blank = prs.slide_layouts[6]


def bg(slide):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG


def tx(slide, l, t, w, h, text, sz=16, color=FG, bold=False, align=PP_ALIGN.LEFT, spacing=1.15):
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
    p.space_after = Pt(0)
    p.space_before = Pt(0)
    return box


def multi(slide, l, t, w, h, lines, spacing=1.2):
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
        p.space_after = Pt(2)
        p.line_spacing = Pt(sz * spacing)
    return box


def line(slide, l, t, w, color=DIMMER, h=Pt(1)):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = color
    s.line.fill.background()


def slide_num(slide, n, total=16):
    tx(slide, Inches(12.5), Inches(7.1), Inches(0.7), Inches(0.3),
       f"{n}", sz=10, color=DIMMER, align=PP_ALIGN.RIGHT)


def tbl(slide, l, t, w, rows, col_ws=None, highlights=None):
    nr, nc = len(rows), len(rows[0])
    sh = slide.shapes.add_table(nr, nc, l, t, w, Inches(0.36 * nr))
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
                    p.font.color.rgb = FG
                elif highlights and r in highlights:
                    p.font.bold = True
                    p.font.color.rgb = FG
                else:
                    p.font.color.rgb = DIM
            cell.fill.solid()
            if r == 0:
                cell.fill.fore_color.rgb = TBL_HEAD_BG
            else:
                cell.fill.fore_color.rgb = TBL_ALT_BG if r % 2 == 0 else TBL_ROW_BG
            cell.margin_left = Inches(0.08)
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.04)
            cell.margin_bottom = Inches(0.04)
    return sh


# Left margin and content width
M = Inches(1.2)
CW = Inches(10.9)

# ════════════════════════════════════════════════════════════════
# 1. TITLE
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
tx(s, M, Inches(2.2), CW, Inches(1.0),
   "Pact3D", sz=64, bold=True, color=FG)
line(s, M, Inches(3.3), Inches(3.0), FG, Pt(2))
tx(s, M, Inches(3.6), CW, Inches(0.5),
   "Physics-Aware Contact Tracking in 3D", sz=22, color=DIM)
tx(s, M, Inches(4.5), CW, Inches(0.8),
   "Take a strong body tracker. Add a lightweight physics layer.\nGet simulation-ready human motion from monocular video.", sz=16, color=DIM)
tx(s, M, Inches(5.8), CW, Inches(0.3),
   "No training  ·  Single GPU  ·  8 weeks", sz=14, color=DIMMER)
slide_num(s, 1)

# ════════════════════════════════════════════════════════════════
# 2. THE PROBLEM
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
tx(s, M, Inches(0.6), CW, Inches(0.3), "THE PROBLEM", sz=11, color=DIM, bold=True)
tx(s, M, Inches(1.1), CW, Inches(0.6),
   "Current trackers are good — but not physical", sz=36, bold=True)
line(s, M, Inches(1.85), Inches(2.0), DIMMER)

multi(s, M, Inches(2.3), CW, Inches(4.0), [
    ("Foot skating", 20, FG, True),
    ("3.0–4.4mm sliding — bodies glide across the ground during contact", 15, DIM, False),
    ("", 10, DIM, False),
    ("Ground penetration", 20, FG, True),
    ("Bodies clip through floors, chairs, and objects", 15, DIM, False),
    ("", 10, DIM, False),
    ("Temporal jitter", 20, FG, True),
    ("12.8–22.5 units — twitchy, unstable motion output", 15, DIM, False),
    ("", 10, DIM, False),
    ("No simulation readiness", 20, FG, True),
    ("Raw SMPL parameters can't be loaded into physics engines", 15, DIM, False),
])

line(s, M, Inches(6.2), CW, DIMMER)
tx(s, M, Inches(6.5), CW, Inches(0.4),
   "The missing piece: physics constraints.", sz=18, color=FG, bold=True)
slide_num(s, 2)

# ════════════════════════════════════════════════════════════════
# 3. EVIDENCE
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
tx(s, M, Inches(0.6), CW, Inches(0.3), "EVIDENCE", sz=11, color=DIM, bold=True)
tx(s, M, Inches(1.1), CW, Inches(0.6),
   "Physics consistently improves results", sz=36, bold=True)
line(s, M, Inches(1.85), Inches(2.0), DIMMER)

tbl(s, M, Inches(2.2), CW, [
    ["Study", "Method", "Key Result"],
    ["MultiPhys (CVPR'24)", "MuJoCo simulation loop", "7x less penetration"],
    ["MultiPhys", "Ground plane contact", "5x less ground penetration"],
    ["CRISP (arXiv'25)", "Planar scene + RL tracking", "8x lower failure rate"],
    ["PhysDiff (ICCV'23)", "Physics in diffusion denoising", "86% less physical error"],
    ["PROX (ICCV'19)", "SDF + contact energy terms", "24% better V2V error"],
    ["LEMO (ICCV'21)", "Friction + smoothness prior", "Eliminates skating + jitter"],
    ["SimPoE (CVPR'21)", "Sim-based pose estimation", "SOTA accuracy + physics jointly"],
], col_ws=[Inches(2.8), Inches(4.2), Inches(3.9)])

line(s, M, Inches(5.8), CW, DIMMER)
multi(s, M, Inches(6.0), CW, Inches(0.8), [
    ("Physics doesn't just look better — it improves reconstruction accuracy.", 16, FG, True),
    ("MultiPhys: W-MPJPE 177.1 → 174.7mm after physics correction.", 14, DIM, False),
])
slide_num(s, 3)

# ════════════════════════════════════════════════════════════════
# 4. DESIGN LESSON
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
tx(s, M, Inches(0.6), CW, Inches(0.3), "DESIGN LESSON", sz=11, color=DIM, bold=True)
tx(s, M, Inches(1.1), CW, Inches(0.6),
   "Two-stage RL post-correction can hurt", sz=36, bold=True)
line(s, M, Inches(1.85), Inches(2.0), DIMMER)

tx(s, M, Inches(2.2), CW, Inches(0.3),
   "PhysHMR (SIGGRAPH Asia 2025) found a critical negative result:", sz=15, color=DIM)

# Three numbers inline
multi(s, M, Inches(3.0), Inches(3.2), Inches(1.5), [
    ("5.65mm", 40, FG, True),
    ("GVHMR alone", 13, DIM, False),
])
multi(s, Inches(4.8), Inches(3.0), Inches(3.2), Inches(1.5), [
    ("12.71mm", 40, FG, True),
    ("+ RL post-correction", 13, DIM, False),
    ("2.2x worse", 13, FG, True),
])
multi(s, Inches(8.6), Inches(3.0), Inches(3.2), Inches(1.5), [
    ("< 1mm", 40, FG, True),
    ("our target", 13, DIM, False),
    ("optimization-based", 13, FG, True),
])

# Arrows between
tx(s, Inches(3.9), Inches(3.1), Inches(0.5), Inches(0.6), "→", sz=28, color=DIMMER, align=PP_ALIGN.CENTER)
tx(s, Inches(7.7), Inches(3.1), Inches(0.5), Inches(0.6), "→", sz=28, color=DIMMER, align=PP_ALIGN.CENTER)

line(s, M, Inches(5.0), CW, DIMMER)

multi(s, M, Inches(5.3), CW, Inches(1.5), [
    ("Why RL fails: balance-recovery actions create new limb artifacts.", 15, DIM, False),
    ("", 8, DIM, False),
    ("Our approach: optimization-based energy minimization (PROX/LEMO style).", 16, FG, True),
    ("Directly minimize contact, penetration, friction, smoothness energies. No balance artifacts.", 15, DIM, False),
])
slide_num(s, 4)

# ════════════════════════════════════════════════════════════════
# 5. BODY TRACKER — CAMERA SPACE
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
tx(s, M, Inches(0.6), CW, Inches(0.3), "BODY TRACKER", sz=11, color=DIM, bold=True)
tx(s, M, Inches(1.1), CW, Inches(0.5),
   "Camera-space accuracy (3DPW, mm ↓)", sz=28, bold=True)
line(s, M, Inches(1.7), Inches(2.0), DIMMER)

tbl(s, M, Inches(2.0), CW, [
    ["Method", "Year", "PA-MPJPE", "MPJPE", "PVE", "World?", "Multi?", "License"],
    ["GLAMR", "2022", "51.1", "—", "—", "Yes", "No", "NVIDIA NC"],
    ["SLAHMR", "2023", "55.9", "—", "—", "Yes", "Yes", "MIT"],
    ["HMR 2.0", "2023", "44.4", "69.8", "82.2", "No", "No", "MIT"],
    ["WHAM", "2024", "35.9", "57.8", "68.7", "Yes", "No", "Custom"],
    ["GVHMR", "2024", "36.2", "55.6", "67.2", "Yes", "No", "Custom"],
    ["Multi-HMR", "2024", "45.9", "73.1", "87.1", "No", "Yes", "CC BY-NC-SA"],
    ["PromptHMR", "2025", "35.5", "—", "67.3", "Yes", "No", "Available"],
    ["Human3R", "2025", "44.1", "71.2", "84.9", "Yes", "Yes", "MIT"],
], col_ws=[Inches(1.6), Inches(0.7), Inches(1.5), Inches(1.2), Inches(1.0),
           Inches(1.0), Inches(1.0), Inches(2.9)],
   highlights={5, 9})

tx(s, M, Inches(6.2), CW, Inches(0.3),
   "Highlighted: GVHMR (best accuracy) · Human3R (multi-person, MIT)", sz=13, color=DIM)
slide_num(s, 5)

# ════════════════════════════════════════════════════════════════
# 6. BODY TRACKER — WORLD
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
tx(s, M, Inches(0.6), CW, Inches(0.3), "BODY TRACKER", sz=11, color=DIM, bold=True)
tx(s, M, Inches(1.1), CW, Inches(0.5),
   "World-grounded accuracy (EMDB-2, mm ↓)", sz=28, bold=True)
line(s, M, Inches(1.7), Inches(2.0), DIMMER)

tbl(s, M, Inches(2.0), CW, [
    ["Method", "WA-MPJPE", "W-MPJPE", "Jitter", "Foot Slide", "Speed"],
    ["GLAMR", "280.8", "726.6", "46.3", "20.7", "Slow"],
    ["SLAHMR", "326.9", "776.1", "31.3", "14.5", "~4 hrs/1K fr"],
    ["TRACE", "529.0", "1702.3", "2987.6", "370.7", "—"],
    ["WHAM", "135.6", "354.8", "22.5", "4.4", "~5s/1K fr"],
    ["GVHMR", "111.0", "276.5", "16.7", "3.5", "0.28s/1.4K fr"],
    ["WATCH", "106.4", "269.3", "14.4", "—", "—"],
    ["Human3R", "112.2", "267.9", "—", "—", "15 FPS e2e"],
], col_ws=[Inches(1.6), Inches(1.8), Inches(1.8), Inches(1.8), Inches(1.8), Inches(2.1)],
   highlights={5, 7, 8})

line(s, M, Inches(5.4), CW, DIMMER)
multi(s, M, Inches(5.6), CW, Inches(1.2), [
    ("World metrics matter most for physics — this is what we build on.", 16, FG, True),
    ("GVHMR and Human3R are within 1% of each other on world trajectory.", 14, DIM, False),
])
slide_num(s, 6)

# ════════════════════════════════════════════════════════════════
# 7. RECOMMENDATION
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
tx(s, M, Inches(0.6), CW, Inches(0.3), "RECOMMENDATION", sz=11, color=DIM, bold=True)
tx(s, M, Inches(1.1), CW, Inches(0.5),
   "Two-track body backbone", sz=36, bold=True)
line(s, M, Inches(1.85), Inches(2.0), DIMMER)

# Left column — GVHMR
lx = M
multi(s, lx, Inches(2.3), Inches(5.0), Inches(4.0), [
    ("Primary — GVHMR", 22, FG, True),
    ("", 6, DIM, False),
    ("Best accuracy", 15, FG, True),
    ("PA-MPJPE 36.2 · MPJPE 55.6 · PVE 67.2", 13, DIM, False),
    ("", 6, DIM, False),
    ("Lowest artifacts", 15, FG, True),
    ("Foot sliding 3.0mm · Jitter 12.8", 13, DIM, False),
    ("", 6, DIM, False),
    ("Fastest", 15, FG, True),
    ("~5000 FPS core · 0.28s for 1430 frames", 13, DIM, False),
    ("", 6, DIM, False),
    ("Physics-friendly", 15, FG, True),
    ("Gravity-view coords align with real-world gravity", 13, DIM, False),
    ("", 8, DIM, False),
    ("Single-person only · research-only license", 13, DIMMER, False),
])

# Divider
line(s, Inches(6.6), Inches(2.3), Pt(1), DIMMER, Inches(4.2))

# Right column — Human3R
rx = Inches(7.0)
multi(s, rx, Inches(2.3), Inches(5.0), Inches(4.0), [
    ("Alternative — Human3R", 22, FG, True),
    ("", 6, DIM, False),
    ("Unified output", 15, FG, True),
    ("Multi-person SMPL-X + scene + camera in one pass", 13, DIM, False),
    ("", 6, DIM, False),
    ("Real-time", 15, FG, True),
    ("15 FPS end-to-end · 8 GB VRAM", 13, DIM, False),
    ("", 6, DIM, False),
    ("MIT licensed", 15, FG, True),
    ("Publication-safe · commercial-safe", 13, DIM, False),
    ("", 6, DIM, False),
    ("Perfect physics target", 15, FG, True),
    ("Paper lists penetration + no-physics as limitations", 13, DIM, False),
    ("", 8, DIM, False),
    ("Lower per-person accuracy (PA-MPJPE 44.1 vs 36.2)", 13, DIMMER, False),
])

slide_num(s, 7)

# ════════════════════════════════════════════════════════════════
# 8. SCENE GEOMETRY
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
tx(s, M, Inches(0.6), CW, Inches(0.3), "SCENE GEOMETRY", sz=11, color=DIM, bold=True)
tx(s, M, Inches(1.1), CW, Inches(0.5),
   "Depth Anything 3", sz=36, bold=True)
line(s, M, Inches(1.85), Inches(2.0), DIMMER)

tbl(s, M, Inches(2.1), Inches(7.0), [
    ["Feature", "DA3", "Metric3D v2", "CUT3R", "VGGT"],
    ["Metric depth", "Yes", "Best", "Yes", "Yes"],
    ["Camera poses", "Yes", "No", "Yes", "Yes"],
    ["Pointmaps", "Yes", "No", "Yes", "Yes"],
    ["Streaming", "<12 GB", "No", "8 GB", "No"],
    ["License", "Apache-2.0", "Apache-2.0", "CC BY-NC-SA", "Custom"],
], col_ws=[Inches(1.5), Inches(1.4), Inches(1.4), Inches(1.4), Inches(1.3)],
   highlights={1, 2, 3, 4})

# Stats on right
multi(s, Inches(8.8), Inches(2.2), Inches(3.5), Inches(3.5), [
    ("78 FPS", 36, FG, True),
    ("DA3-Large throughput", 12, DIM, False),
    ("", 12, DIM, False),
    ("< 12 GB", 36, FG, True),
    ("VRAM with streaming", 12, DIM, False),
    ("", 12, DIM, False),
    ("Any length", 36, FG, True),
    ("Video duration", 12, DIM, False),
])

line(s, M, Inches(5.5), CW, DIMMER)
multi(s, M, Inches(5.7), CW, Inches(1.5), [
    ("Only method with metric depth + camera poses + pointmaps + streaming from one model.", 15, FG, True),
    ("Depth quality (AbsRel 0.070) is sufficient — physics optimizer corrects residual errors.", 14, DIM, False),
    ("Apache-2.0 license completes the fully permissive stack.", 14, DIM, False),
])
slide_num(s, 8)

# ════════════════════════════════════════════════════════════════
# 9. ARCHITECTURE
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
tx(s, M, Inches(0.6), CW, Inches(0.3), "ARCHITECTURE", sz=11, color=DIM, bold=True)
tx(s, M, Inches(1.1), CW, Inches(0.5),
   "Pipeline", sz=36, bold=True)
line(s, M, Inches(1.85), Inches(2.0), DIMMER)

# Render architecture as styled text (monospace feel)
arch_lines = [
    ("Monocular RGB Video", 16, FG, True),
    ("        │", 14, DIMMER, False),
    ("        ├── Body Tracker  (GVHMR / Human3R)", 14, FG, False),
    ("        │     → SMPL(-X) poses  +  global root trajectory", 13, DIM, False),
    ("        │", 14, DIMMER, False),
    ("        ├── Scene Backbone  (DA3-Metric-Large)", 14, FG, False),
    ("        │     → Metric depth  +  pointmaps  +  camera poses", 13, DIM, False),
    ("        │", 14, DIMMER, False),
    ("        └── Physics Refinement  (optimization-based)", 14, FG, True),
    ("              │", 14, DIMMER, False),
    ("              ├── Ground Plane          RANSAC on pointmap", 13, DIM, False),
    ("              ├── Collision Mesh        pointmap → mesh", 13, DIM, False),
    ("              ├── Contact Detection     foot velocity + proximity", 13, DIM, False),
    ("              │", 14, DIMMER, False),
    ("              ├── E_contact              pin feet to surface", 13, FG, False),
    ("              ├── E_penetration          SDF non-intersection", 13, FG, False),
    ("              ├── E_friction              no sliding during contact", 13, FG, False),
    ("              ├── E_stability             CoM / CoP balance", 13, FG, False),
    ("              ├── E_smooth               temporal jerk penalty", 13, FG, False),
    ("              │", 14, DIMMER, False),
    ("              └── MuJoCo Validation     verify, don't correct", 13, DIM, False),
]

box = s.shapes.add_textbox(M, Inches(2.1), CW, Inches(5.0))
tf = box.text_frame
tf.word_wrap = True
for i, (text, sz, col, bld) in enumerate(arch_lines):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.text = text
    p.font.size = Pt(sz)
    p.font.color.rgb = col
    p.font.bold = bld
    p.font.name = "Consolas"
    p.space_after = Pt(0)
    p.line_spacing = Pt(sz * 1.25)

slide_num(s, 9)

# ════════════════════════════════════════════════════════════════
# 10. WHAT MAKES THIS DIFFERENT
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
tx(s, M, Inches(0.6), CW, Inches(0.3), "NOVELTY", sz=11, color=DIM, bold=True)
tx(s, M, Inches(1.1), CW, Inches(0.5),
   "What makes Pact3D different", sz=36, bold=True)
line(s, M, Inches(1.85), Inches(2.0), DIMMER)

blocks = [
    ("vs. MultiPhys", "(RL post-correction)", [
        "Optimization, not RL — no balance-recovery artifacts",
        "Scene geometry (not just ground plane)",
        "Modern trackers (GVHMR, not SLAHMR)",
    ]),
    ("vs. PROX / LEMO", "(optimization-based)", [
        "State-of-the-art body trackers (not old SMPLify)",
        "Metric depth for real-world scale",
        "Video, not single frames",
    ]),
    ("vs. PhysHMR", "(end-to-end RL)", [
        "Training-free — compose pretrained models",
        "Swap any component as better ones emerge",
        "Lower barrier, faster iteration",
    ]),
]

for i, (title, sub, points) in enumerate(blocks):
    y = Inches(2.3) + i * Inches(1.6)
    line(s, M, y, CW, DIMMER)
    lines = [(f"{title}  {sub}", 18, FG, True)]
    for pt in points:
        lines.append((f"    {pt}", 14, DIM, False))
    multi(s, M, y + Inches(0.15), CW, Inches(1.4), lines, spacing=1.15)

slide_num(s, 10)

# ════════════════════════════════════════════════════════════════
# 11. EVALUATION
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
tx(s, M, Inches(0.6), CW, Inches(0.3), "EVALUATION", sz=11, color=DIM, bold=True)
tx(s, M, Inches(1.1), CW, Inches(0.5),
   "Targets & datasets", sz=36, bold=True)
line(s, M, Inches(1.85), Inches(2.0), DIMMER)

tbl(s, M, Inches(2.2), Inches(6.0), [
    ["Metric", "Current SOTA", "Our Target"],
    ["Foot Sliding", "3.0 mm (GVHMR)", "< 1 mm"],
    ["Ground Pen.", "2.4 mm (MultiPhys)", "< 1 mm"],
    ["Inter-body Pen.", "18.7 mm (MultiPhys)", "< 20 mm"],
    ["PA-MPJPE", "36.2 mm (GVHMR)", "No degradation"],
], col_ws=[Inches(1.8), Inches(2.2), Inches(2.0)],
   highlights={1, 2})

multi(s, Inches(7.8), Inches(2.2), Inches(4.5), Inches(3.5), [
    ("Datasets", 18, FG, True),
    ("", 6, DIM, False),
    ("RICH  (primary)", 15, FG, True),
    ("Scene scans + vertex contact GT + global coords", 12, DIM, False),
    ("", 6, DIM, False),
    ("EMDB-2", 15, FG, True),
    ("2.3cm pose accuracy · moving cameras · drift", 12, DIM, False),
    ("", 6, DIM, False),
    ("3DPW", 15, FG, True),
    ("Standard benchmark · every method reports on it", 12, DIM, False),
    ("", 6, DIM, False),
    ("Hi4D", 15, FG, True),
    ("Multi-person close interaction · contact GT", 12, DIM, False),
])

line(s, M, Inches(5.8), CW, DIMMER)
tx(s, M, Inches(6.0), CW, Inches(0.5),
   "RICH is primary: uniquely provides scene scans + vertex contact GT + reliable global coordinates.",
   sz=14, color=DIM)
slide_num(s, 11)

# ════════════════════════════════════════════════════════════════
# 12. TIMELINE
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
tx(s, M, Inches(0.6), CW, Inches(0.3), "TIMELINE", sz=11, color=DIM, bold=True)
tx(s, M, Inches(1.1), CW, Inches(0.5),
   "8-week plan", sz=36, bold=True)
line(s, M, Inches(1.85), Inches(2.0), DIMMER)

weeks = [
    ("1", "Setup", "Run GVHMR + DA3 on test videos"),
    ("2", "Scene", "Ground plane RANSAC, gravity alignment"),
    ("3", "Contact", "Foot contact detection, loss terms"),
    ("4", "Physics", "MuJoCo integration, root + feet optimization"),
    ("5", "HOI", "Hand/object non-penetration"),
    ("6", "Eval", "RICH, EMDB-2, 3DPW + ablations"),
    ("7", "Robustness", "Chunking, stitching, edge cases"),
    ("8", "Demo", "Side-by-side renders, technical report"),
]

for i, (wk, title, desc) in enumerate(weeks):
    y = Inches(2.2) + i * Inches(0.58)
    # Week number
    tx(s, M, y, Inches(0.5), Inches(0.4),
       wk, sz=16, color=FG if i < 4 else DIM, bold=True, align=PP_ALIGN.RIGHT)
    # Dot
    dot_y = y + Inches(0.08)
    sh = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(2.0), dot_y, Inches(0.12), Inches(0.12))
    sh.fill.solid()
    sh.fill.fore_color.rgb = FG if i < 4 else DIMMER
    sh.line.fill.background()
    # Vertical line
    if i < 7:
        line(s, Inches(2.045), dot_y + Inches(0.12), Pt(1), DIMMER, Inches(0.46))
    # Title + desc
    tx(s, Inches(2.3), y, Inches(1.5), Inches(0.35),
       title, sz=15, color=FG, bold=True)
    tx(s, Inches(4.0), y, Inches(7.0), Inches(0.35),
       desc, sz=14, color=DIM)

line(s, M, Inches(6.6), CW, DIMMER)
multi(s, M, Inches(6.8), CW, Inches(0.5), [
    ("Weeks 1–4: core value (ground contact + physics)    ·    Weeks 5–8: stretch goals (HOI, robustness, polish)", 13, DIM, False),
])
slide_num(s, 12)

# ════════════════════════════════════════════════════════════════
# 13. COMPUTE
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
tx(s, M, Inches(0.6), CW, Inches(0.3), "COMPUTE", sz=11, color=DIM, bold=True)
tx(s, M, Inches(1.1), CW, Inches(0.5),
   "Single consumer GPU", sz=36, bold=True)
line(s, M, Inches(1.85), Inches(2.0), DIMMER)

# Three big numbers
for i, (num, label) in enumerate([("< 16 GB", "peak VRAM"), ("< 2 min", "per 1K frames"), ("1 GPU", "RTX 3090 / 4090")]):
    x = M + i * Inches(3.7)
    tx(s, x, Inches(2.4), Inches(3.2), Inches(0.7), num, sz=40, color=FG, bold=True)
    tx(s, x, Inches(3.1), Inches(3.2), Inches(0.3), label, sz=14, color=DIM)

line(s, M, Inches(3.8), CW, DIMMER)

tbl(s, M, Inches(4.1), CW, [
    ["Component", "VRAM", "Time / 1K frames", "Notes"],
    ["GVHMR (core)", "~4 GB", "~0.2 sec", "5000 FPS core network"],
    ["Human3R", "~8 GB", "~67 sec", "15 FPS end-to-end"],
    ["DA3-Metric-L", "<12 GB", "~13 sec", "78 FPS, streaming"],
    ["MuJoCo optim.", "CPU", "~10-30 sec", "Optimization loop"],
], col_ws=[Inches(2.5), Inches(2.2), Inches(3.0), Inches(3.2)])

slide_num(s, 13)

# ════════════════════════════════════════════════════════════════
# 14. LICENSING
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
tx(s, M, Inches(0.6), CW, Inches(0.3), "LICENSING", sz=11, color=DIM, bold=True)
tx(s, M, Inches(1.1), CW, Inches(0.5),
   "Fully permissive stack", sz=36, bold=True)
line(s, M, Inches(1.85), Inches(2.0), DIMMER)

tbl(s, Inches(2.5), Inches(2.3), Inches(8.3), [
    ["Component", "License", "Role"],
    ["Human3R", "MIT", "Body + scene backbone"],
    ["Depth Anything 3", "Apache-2.0", "Depth / pointmaps"],
    ["MuJoCo", "Apache-2.0", "Physics engine"],
    ["Open3D", "MIT", "Point cloud processing"],
    ["trimesh", "MIT", "Collision mesh generation"],
    ["PyTorch", "BSD", "Optimization backend"],
], col_ws=[Inches(2.5), Inches(2.0), Inches(3.8)],
   highlights={1, 2, 3})

line(s, Inches(2.5), Inches(5.6), Inches(8.3), DIMMER)
tx(s, Inches(2.5), Inches(5.8), Inches(8.3), Inches(0.5),
   "Human3R (MIT) + DA3 (Apache-2.0) + MuJoCo (Apache-2.0) = fully open.",
   sz=16, color=FG, bold=True, align=PP_ALIGN.CENTER)
slide_num(s, 14)

# ════════════════════════════════════════════════════════════════
# 15. RISKS
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)
tx(s, M, Inches(0.6), CW, Inches(0.3), "RISKS", sz=11, color=DIM, bold=True)
tx(s, M, Inches(1.1), CW, Inches(0.5),
   "Risk analysis", sz=36, bold=True)
line(s, M, Inches(1.85), Inches(2.0), DIMMER)

risks = [
    ("Low", "DA3 depth too noisy", "Plane-only proxy; physics corrects residual errors"),
    ("Med", "MuJoCo integration complex", "Start ground-only; MultiPhys as reference impl."),
    ("Med", "GVHMR license restricts publication", "Fall back to Human3R (MIT) — modular swap"),
    ("Low", "Physics degrades accuracy", "7+ papers show it helps; ablate each term"),
    ("Med", "Week 5 HOI too ambitious", "HOI is stretch goal; core value is weeks 1–4"),
]

for i, (level, risk, mitigation) in enumerate(risks):
    y = Inches(2.2) + i * Inches(1.0)
    line(s, M, y, CW, DIMMER)
    level_col = FG if level == "Low" else DIM
    multi(s, M, y + Inches(0.1), CW, Inches(0.85), [
        (f"{level}    {risk}", 15, level_col, True),
        (f"          {mitigation}", 13, DIM, False),
    ])

slide_num(s, 15)

# ════════════════════════════════════════════════════════════════
# 16. CLOSING
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank); bg(s)

tx(s, M, Inches(1.5), CW, Inches(0.8),
   "Pact3D", sz=56, bold=True, color=FG, align=PP_ALIGN.CENTER)
line(s, Inches(5.5), Inches(2.4), Inches(2.3), FG, Pt(2))
tx(s, M, Inches(2.7), CW, Inches(0.4),
   "Body Tracker  +  Scene Geometry  +  Physics Layer", sz=20, color=DIM, align=PP_ALIGN.CENTER)

pillars = [
    ("Feasible", "No training. Pretrained models. 8 weeks. Single GPU."),
    ("Impactful", "Targets the #1 gap in trackers: physical plausibility."),
    ("Evidence-backed", "7+ papers: physics improves plausibility AND accuracy."),
    ("Publication-ready", "MIT / Apache stack. Clear benchmarks. Novel integration."),
    ("Extensible", "Modular. Swap any component as better ones emerge."),
]

for i, (title, desc) in enumerate(pillars):
    y = Inches(3.5) + i * Inches(0.6)
    tx(s, Inches(2.5), y, Inches(2.5), Inches(0.4), title, sz=15, color=FG, bold=True, align=PP_ALIGN.RIGHT)
    tx(s, Inches(5.2), y, Inches(6.0), Inches(0.4), desc, sz=14, color=DIM)

line(s, M, Inches(6.7), CW, DIMMER)

slide_num(s, 16)


# ── Save ──
out = "/home/user/Pact3D/Pact3D_Presentation.pptx"
prs.save(out)
print(f"Saved {len(prs.slides)} slides to {out}")

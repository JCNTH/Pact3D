#!/usr/bin/env python3
"""
Build literature review slides — one slide per paper, clean and readable.
Same style as main deck (white/tan, Tracking header).
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

BG       = RGBColor(0xFF, 0xFF, 0xFF)
TEXT     = RGBColor(0x1A, 0x1A, 0x1A)
DIM      = RGBColor(0x99, 0x99, 0x99)
ACCENT   = RGBColor(0x7B, 0x1E, 0x1E)
TAN      = RGBColor(0xF0, 0xE6, 0xD3)
TAN_DARK = RGBColor(0xD4, 0xC4, 0xA8)
WHITE    = RGBColor(0xFF, 0xFF, 0xFF)
TEAL     = RGBColor(0x00, 0x88, 0x80)
CAT_BODY = RGBColor(0x2B, 0x6C, 0x8A)     # blue-teal for body tracker
CAT_SCENE = RGBColor(0x5A, 0x7D, 0x3A)    # green for scene
CAT_PHYS = RGBColor(0x7B, 0x1E, 0x1E)     # maroon for physics

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
blank = prs.slide_layouts[6]


def bg(slide):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG


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
    box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(4), Inches(0.5))
    tf = box.text_frame
    p = tf.paragraphs[0]
    p.text = "Tracking"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = TEXT
    p.font.name = "Calibri"
    if subtitle:
        box2 = slide.shapes.add_textbox(Inches(0.5), Inches(0.75), Inches(10), Inches(0.4))
        tf2 = box2.text_frame
        p2 = tf2.paragraphs[0]
        p2.text = subtitle
        p2.font.size = Pt(18)
        p2.font.color.rgb = TEXT
        p2.font.name = "Calibri"


def tag(slide, l, t, text, color):
    """Small colored tag showing category."""
    w = Inches(len(text) * 0.11 + 0.3)
    rect = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, Inches(0.32))
    rect.fill.solid()
    rect.fill.fore_color.rgb = color
    rect.line.fill.background()
    tf = rect.text_frame
    tf.paragraphs[0].text = text
    tf.paragraphs[0].font.size = Pt(11)
    tf.paragraphs[0].font.color.rgb = WHITE
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.name = "Calibri"
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE


def paper_slide(n, title, venue, category, cat_color, points, takeaway):
    """One literature review slide per paper."""
    s = prs.slides.add_slide(blank); bg(s)
    header(s, "Literature Review")

    # Paper title
    box = s.shapes.add_textbox(Inches(0.5), Inches(1.2), Inches(10), Inches(0.5))
    tf = box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = TEXT
    p.font.name = "Calibri"

    # Venue
    box2 = s.shapes.add_textbox(Inches(0.5), Inches(1.7), Inches(6), Inches(0.3))
    tf2 = box2.text_frame
    p2 = tf2.paragraphs[0]
    p2.text = venue
    p2.font.size = Pt(14)
    p2.font.color.rgb = DIM
    p2.font.name = "Calibri"

    # Category tag
    tag(s, Inches(0.5), Inches(2.15), category, cat_color)

    # Bullet points
    box3 = s.shapes.add_textbox(Inches(0.5), Inches(2.7), Inches(12), Inches(3.5))
    tf3 = box3.text_frame
    tf3.word_wrap = True
    for i, pt in enumerate(points):
        p = tf3.paragraphs[0] if i == 0 else tf3.add_paragraph()
        p.text = f"• {pt}"
        p.font.size = Pt(16)
        p.font.color.rgb = TEXT
        p.font.name = "Calibri"
        p.space_after = Pt(6)
        p.line_spacing = Pt(24)

    # Takeaway box at bottom
    rect = s.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                               Inches(0.5), Inches(6.3), Inches(12), Inches(0.7))
    rect.fill.solid()
    rect.fill.fore_color.rgb = TAN
    rect.line.color.rgb = TAN_DARK
    rect.line.width = Pt(0.5)
    box4 = s.shapes.add_textbox(Inches(0.7), Inches(6.4), Inches(11.6), Inches(0.5))
    tf4 = box4.text_frame
    p4 = tf4.paragraphs[0]
    p4.text = takeaway
    p4.font.size = Pt(14)
    p4.font.bold = True
    p4.font.color.rgb = cat_color
    p4.font.name = "Calibri"

    slide_num(s, n)


# ════════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank)
s.background.fill.solid()
s.background.fill.fore_color.rgb = TEAL
box = s.shapes.add_textbox(Inches(2), Inches(2.5), Inches(9), Inches(1.0))
tf = box.text_frame
p = tf.paragraphs[0]
p.text = "Literature Review"
p.font.size = Pt(56)
p.font.bold = True
p.font.color.rgb = WHITE
p.font.name = "Calibri"
p.alignment = PP_ALIGN.CENTER

box2 = s.shapes.add_textbox(Inches(2), Inches(3.7), Inches(9), Inches(1.5))
tf2 = box2.text_frame
for i, (label, col) in enumerate([
    ("Body Trackers", CAT_BODY),
    ("Scene Reconstruction", CAT_SCENE),
    ("Physics-Aware Methods", CAT_PHYS),
]):
    p = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
    p.text = label
    p.font.size = Pt(22)
    p.font.color.rgb = WHITE
    p.font.name = "Calibri"
    p.alignment = PP_ALIGN.CENTER
    p.space_after = Pt(8)
slide_num(s, 1)


# ════════════════════════════════════════════════════════════════
# BODY TRACKERS
# ════════════════════════════════════════════════════════════════

paper_slide(2,
    "GVHMR", "SIGGRAPH Asia 2024",
    "Body Tracker", CAT_BODY,
    [
        "Recovers 3D body motion in world coordinates from a single video",
        'Defines a "gravity-view" coordinate system — uses gravity direction + camera angle to place the person in the real world',
        "Estimates each frame independently, then a transformer refines the sequence — avoids error accumulation",
        "Gets camera rotation from visual odometry or phone gyroscope",
        "State-of-the-art: PA-MPJPE 36.2mm (3DPW), WA-MPJPE 111.0mm (EMDB-2)",
        "Very fast: ~5000 FPS for the core network",
        "Single-person only, no scene reconstruction",
    ],
    "Our top pick for single-person body tracking — best accuracy and speed"
)

paper_slide(3,
    "Human3R", "arxiv 2025",
    "Body Tracker + Scene", CAT_BODY,
    [
        "Recovers multi-person 3D bodies and the scene simultaneously from a stream of images",
        "Built on CUT3R (scene) + Multi-HMR (bodies), fine-tuned together",
        '"One model, one stage, trained in one day on one GPU"',
        "Real-time: 15 FPS, 8 GB VRAM",
        "Handles multiple people, unknown cameras, varying layouts",
        "MIT licensed",
        "Authors note limitations: body-scene penetration and no human-object interaction",
    ],
    "Our pick for multi-person — its known weaknesses are exactly what physics refinement fixes"
)

paper_slide(4,
    "WHAM", "CVPR 2024",
    "Body Tracker", CAT_BODY,
    [
        "Recovers global 3D human motion from video using learned motion context",
        "Recurrent architecture that integrates visual + motion features over time",
        "Can optionally use phone IMU data (accelerometer/gyroscope) for better trajectory",
        "Fast: ~5 seconds per 1000 frames",
        "Good accuracy (PA-MPJPE 35.9mm) but more foot sliding than GVHMR (4.4mm vs 3.0mm)",
        "Single-person only",
    ],
    "Strong alternative to GVHMR — slightly worse on foot sliding, comparable otherwise"
)

paper_slide(5,
    "JOSH", "ICLR 2026",
    "Body Tracker + Scene", CAT_BODY,
    [
        "Jointly optimizes 3D bodies and scene reconstruction from video",
        "Multi-stage: estimates per-frame, then jointly optimizes with contact + scene consistency losses",
        "Multi-person capable",
        "Best offline accuracy: WA-MPJPE 68.9mm — much better than real-time methods",
        "Tradeoff: offline optimization, not real-time",
        "Shows that jointly reasoning about humans and scenes improves both",
    ],
    "Best results overall but too slow for real-time — proves joint human+scene reasoning helps"
)


# ════════════════════════════════════════════════════════════════
# SCENE RECONSTRUCTION
# ════════════════════════════════════════════════════════════════

paper_slide(6,
    "Depth Anything 3", "arxiv 2025",
    "Scene Reconstruction", CAT_SCENE,
    [
        "Estimates metric depth, camera poses, and 3D point clouds from video",
        '"Depth-ray" representation: predicts depth + camera ray direction per pixel — recovers camera parameters without needing them as input',
        "Streaming: processes frames one at a time, works on any video length",
        "Memory efficient: < 12 GB VRAM",
        "78 FPS (DA3-Large)",
        "Compared favorably to VGGT (CVPR'25 Best Paper) while being more practical",
        "Apache-2.0 licensed",
    ],
    "Our pick for scene geometry — streams any-length video, gives us depth + camera poses for the physics layer"
)

paper_slide(7,
    "CUT3R", "CVPR 2025",
    "Scene Reconstruction", CAT_SCENE,
    [
        "Reconstructs 3D scenes from image sequences in a streaming, online fashion",
        "Successor to DUSt3R (CVPR'24), which needed all image pairs at once (quadratic cost)",
        "CUT3R processes frames one at a time — much more scalable",
        "Outputs dense point maps, depth, and camera poses",
        "8 GB VRAM, works on dynamic scenes",
        "Forms the backbone of Human3R — Human3R adds human mesh recovery on top",
        "CC BY-NC-SA license (non-commercial)",
    ],
    "We don't use this directly, but it's what Human3R is built on"
)


# ════════════════════════════════════════════════════════════════
# PHYSICS-AWARE METHODS
# ════════════════════════════════════════════════════════════════

paper_slide(8,
    "MultiPhys", "CVPR 2024",
    "Physics", CAT_PHYS,
    [
        "Takes existing body motion estimates and refines them using MuJoCo (physics simulator)",
        "Each person simulated as a separate articulated body — collisions resolved by physics engine",
        "Trains an RL policy to control each body so it tracks the original motion while obeying physics",
        "Results: 7x less body-ground penetration",
        "First method to handle multi-person physics-aware correction",
        "Limitation: RL policy can create artifacts (arm flailing for balance recovery)",
    ],
    "Physics simulation dramatically reduces artifacts — but the RL approach can backfire"
)

paper_slide(9,
    "PhysHMR", "SIGGRAPH Asia 2025",
    "Physics", CAT_PHYS,
    [
        "End-to-end: goes directly from video to physically plausible 3D motion",
        "Key finding: two-stage pipelines (track then correct) can make things worse",
        "GVHMR alone: 5.65mm foot sliding",
        "GVHMR + RL post-correction: 12.71mm foot sliding (2.2x worse!)",
        "PhysHMR end-to-end: 4.60mm foot sliding (best)",
        "Physics awareness must be integrated, not bolted on as a post-process",
    ],
    "Proves physics helps accuracy — and warns us that RL post-correction is the wrong approach"
)

paper_slide(10,
    "CRISP", "arxiv 2025",
    "Physics + Scene", CAT_PHYS,
    [
        "Combines physics simulation with scene-aware tracking",
        "Uses a planar scene representation (flat ground plane) + RL-based body control",
        "8x lower failure rate compared to methods without scene awareness",
        "Even a simple flat ground plane significantly helps physics-based tracking",
        "Suggests richer scene geometry (like from DA3) could help even more",
    ],
    "Even a flat ground plane helps a lot — motivates using real scene geometry from DA3"
)

paper_slide(11,
    "PROX", "ICCV 2019",
    "Physics", CAT_PHYS,
    [
        "Pioneering work: use scene constraints to improve body pose estimation",
        "Given a 3D scene scan, optimizes body parameters to avoid penetrating the scene",
        "Uses signed distance fields (SDFs) to measure body-scene penetration",
        "24% improvement in vertex-to-vertex accuracy with scene constraints",
        "Limitation: requires a pre-scanned 3D scene — not applicable to in-the-wild video alone",
    ],
    "The original proof that scene constraints improve body estimation — the optimization style we'd follow"
)

paper_slide(12,
    "LEMO", "ICCV 2021",
    "Physics", CAT_PHYS,
    [
        "Adds physics-inspired losses to smooth and correct body motion sequences",
        "Friction loss: feet shouldn't slide when touching the ground",
        "Temporal smoothness: penalize sudden jerky changes",
        "Ground contact consistency",
        "Eliminates foot skating and jitter — no physics simulator needed, just loss terms",
        "Optimization-based, simple, proven",
    ],
    "Our main reference for the optimization approach — simple loss terms, no simulator, proven results"
)

paper_slide(13,
    "PhysDiff", "ICCV 2023",
    "Physics", CAT_PHYS,
    [
        "Integrates physics into a diffusion model for human motion generation",
        "Applies physics-based corrections during each denoising step",
        "86% reduction in physical errors vs. non-physics diffusion models",
        "Different domain (motion generation, not tracking)",
        "Shows physics constraints help even in very different architectures",
    ],
    "Different domain but further evidence: adding physics consistently improves results"
)


# ── Save ──
out = "/home/user/Pact3D/Literature_Review.pptx"
prs.save(out)
print(f"Saved {len(prs.slides)} slides to {out}")

#!/usr/bin/env python3
"""
Build deep-dive slides for 5 papers:
  GVHMR · ZipMap · SAM-Body4D · PhysHMR · MultiPhys

Each paper gets 3–4 slides answering:
  How it works / Main components / Why good / Where it fails / How we use it

Same white/tan palette as the main deck.
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
TEAL     = RGBColor(0x00, 0x88, 0x80)
WHITE    = RGBColor(0xFF, 0xFF, 0xFF)

# Paper accent colors
C_GVHMR  = RGBColor(0x2B, 0x6C, 0x8A)
C_ZIPMAP = RGBColor(0x5A, 0x7D, 0x3A)
C_SAM4D  = RGBColor(0x8B, 0x5C, 0x2A)
C_PHYS   = RGBColor(0x7B, 0x1E, 0x1E)
C_MULTI  = RGBColor(0x5B, 0x3A, 0x7A)

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
blank = prs.slide_layouts[6]
N = [0]  # mutable slide counter


def next_n():
    N[0] += 1
    return N[0]


def _bg(slide):
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


def tag(slide, l, t, text, color):
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
    tx(slide, l + Inches(0.15), t + Inches(0.08), w - Inches(0.3), Inches(0.3),
       title, sz=13, bold=True, color=TEXT)
    if sub:
        tx(slide, l + Inches(0.15), t + Inches(0.38), w - Inches(0.3), Inches(0.5),
           sub, sz=10, color=DIM)


def section_header(slide, paper, subtitle, color):
    """Top bar: paper name + subtitle."""
    rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                   Inches(0), Inches(0), SLIDE_W, Inches(1.0))
    rect.fill.solid()
    rect.fill.fore_color.rgb = color
    rect.line.fill.background()
    tx(slide, Inches(0.6), Inches(0.15), Inches(10), Inches(0.4),
       paper, sz=26, bold=True, color=WHITE)
    tx(slide, Inches(0.6), Inches(0.55), Inches(10), Inches(0.3),
       subtitle, sz=15, color=WHITE)


def takeaway_bar(slide, text, color):
    """Bottom takeaway bar."""
    tan_box(slide, Inches(0.5), Inches(6.3), Inches(12), Inches(0.7))
    tx(slide, Inches(0.7), Inches(6.4), Inches(11.6), Inches(0.5),
       text, sz=14, bold=True, color=color)


def arrow_down(slide, x, y):
    tx(slide, x, y, Inches(0.5), Inches(0.4),
       "\u2193", sz=24, color=DIM, align=PP_ALIGN.CENTER)


# ════════════════════════════════════════════════════════════════
# TITLE SLIDE
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank)
s.background.fill.solid()
s.background.fill.fore_color.rgb = TEAL
tx(s, Inches(2), Inches(2.5), Inches(9), Inches(1.0),
   "Paper Deep Dives", sz=56, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
tx(s, Inches(2), Inches(3.7), Inches(9), Inches(0.6),
   "How they work  \u00b7  Why they matter  \u00b7  Where they fail",
   sz=22, color=WHITE, align=PP_ALIGN.CENTER)
bullets(s, Inches(3), Inches(4.8), Inches(7), Inches(2.0), [
    ("GVHMR \u2014 World-grounded body tracking", 18, WHITE, False),
    ("ZipMap \u2014 Linear-time 3D reconstruction", 18, WHITE, False),
    ("SAM-Body4D \u2014 Temporally consistent mesh recovery", 18, WHITE, False),
    ("PhysHMR \u2014 Unified visual-to-physics motion", 18, WHITE, False),
    ("MultiPhys \u2014 Multi-person physics correction", 18, WHITE, False),
])
slide_num(s, next_n())


# ════════════════════════════════════════════════════════════════════
#  GVHMR — 4 slides
# ════════════════════════════════════════════════════════════════════

# --- GVHMR 1: Overview + What it solves ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "GVHMR", "Overview \u2014 What it solves", C_GVHMR)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.8), Inches(4.8), [
    ("Problem", 20, C_GVHMR, True),
    ("  Recovering world-grounded 3D human motion", 16, TEXT, False),
    ("  from monocular video", 16, TEXT, False),
    ("", 10, DIM, False),
    ("Prior approaches fail because:", 16, TEXT, True),
    ("  Autoregressive models accumulate drift", 16, TEXT, False),
    ("  Gravity direction rotates over time", 16, TEXT, False),
    ("  Camera-to-world transforms are noisy", 16, TEXT, False),
    ("", 10, DIM, False),
    ("Key insight", 20, C_GVHMR, True),
    ("  Define a coordinate system anchored", 16, TEXT, False),
    ("  to gravity + camera view direction", 16, TEXT, False),
    ("  \u2192 each frame estimated independently,", 16, TEXT, False),
    ("  no error accumulation", 16, TEXT, False),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(4.5), [
    ("Specs", 20, C_GVHMR, True),
    ("", 6, DIM, False),
    ("Feed-forward transformer (not recurrent)", 16, TEXT, False),
    ("Single person", 16, TEXT, False),
    ("280 ms for 1430 frames on RTX 4090", 16, TEXT, False),
    ("", 10, DIM, False),
    ("Coordinate spaces", 18, C_GVHMR, True),
    ("", 6, DIM, False),
    ("SMPL space: what the person sees", 14, DIM, False),
    ("Camera space: what the camera sees", 14, DIM, False),
    ("World space: global fixed reference", 14, DIM, False),
    ("", 6, DIM, False),
    ("Extrinsics [R|t] = camera position/orientation", 14, DIM, False),
    ("Intrinsics K = 3D \u2192 2D projection", 14, DIM, False),
])

takeaway_bar(s, "Feed-forward, gravity-aware body tracking \u2014 no drift, no error accumulation", C_GVHMR)
slide_num(s, next_n())


# --- GVHMR 2: How it works (architecture) ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "GVHMR", "How It Works \u2014 Architecture", C_GVHMR)

# Pipeline as boxes
arch_box(s, Inches(0.5), Inches(1.3), Inches(2.5), Inches(1.0),
         "Input Features", "BBoxes, 2D keypoints,\nimage features, camera rotations")
arrow_down(s, Inches(1.5), Inches(2.35))

arch_box(s, Inches(0.5), Inches(2.8), Inches(2.5), Inches(0.9),
         "Early Fusion", "Map to same dim \u2192 per-frame tokens")
arrow_down(s, Inches(1.5), Inches(3.75))

arch_box(s, Inches(0.5), Inches(4.2), Inches(2.5), Inches(1.0),
         "Relative Transformer", "12 layers, 8 heads\nRotary positional encoding")
arrow_down(s, Inches(1.5), Inches(5.25))

arch_box(s, Inches(0.5), Inches(5.7), Inches(2.5), Inches(0.8),
         "Multi-task MLP Heads", "Pose, shape, camera,\ntrajectory, stationary labels")

# Right side: GV coordinate system explanation
bullets(s, Inches(3.8), Inches(1.3), Inches(4.5), Inches(5.5), [
    ("Gravity-View Coordinate System", 18, C_GVHMR, True),
    ("", 6, DIM, False),
    ("Y = gravity direction (up)", 15, TEXT, False),
    ("X = Y \u00d7 camera view (perpendicular)", 15, TEXT, False),
    ("Z = X \u00d7 Y (roughly camera forward)", 15, TEXT, False),
    ("", 8, DIM, False),
    ("Static camera:", 15, TEXT, True),
    ("  GV coord identical every frame", 14, TEXT, False),
    ("  Accumulate velocities directly", 14, TEXT, False),
    ("", 6, DIM, False),
    ("Moving camera:", 15, TEXT, True),
    ("  Compute rotation between GV systems", 14, TEXT, False),
    ("  Transform camera view into GV coord", 14, TEXT, False),
    ("", 8, DIM, False),
    ("No initialization needed", 15, ACCENT, True),
    ("Parallel prediction (no autoregression)", 15, ACCENT, True),
])

# Far right: post-processing
bullets(s, Inches(8.8), Inches(1.3), Inches(4.0), Inches(5.5), [
    ("Post-Processing", 18, C_GVHMR, True),
    ("", 6, DIM, False),
    ("Predict stationary probability per joint", 15, TEXT, False),
    ("Update global translation frame-by-frame", 15, TEXT, False),
    ("Fine-grained stationary contact points", 15, TEXT, False),
    ("Inverse kinematics (CCD solver)", 15, TEXT, False),
    ("", 10, DIM, False),
    ("Weak \u2192 Full Perspective", 18, C_GVHMR, True),
    ("", 6, DIM, False),
    ("Weak perspective = same depth assumed", 14, TEXT, False),
    ("Full perspective = real depth + focal len", 14, TEXT, False),
    ("CLIFF conversion recovers depth", 14, TEXT, False),
    ("from simplified camera params", 14, TEXT, False),
])

slide_num(s, next_n())


# --- GVHMR 3: Why good + Where it fails ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "GVHMR", "Why Good \u00b7 Where It Fails", C_GVHMR)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.5), Inches(4.8), [
    ("Why good", 22, C_GVHMR, True),
    ("", 6, DIM, False),
    ("Gravity-View anchors each frame independently", 16, TEXT, False),
    ("  \u2192 no drift on long videos (WHAM drifts)", 15, DIM, False),
    ("", 6, DIM, False),
    ("Transformer generalizes to long sequences", 16, TEXT, False),
    ("  Rotary embeddings encode relative position", 15, DIM, False),
    ("  \"how far apart\" not \"which position\"", 15, DIM, False),
    ("", 6, DIM, False),
    ("Multi-task learning boosts camera-space too", 16, TEXT, False),
    ("  Global motion info improves local estimates", 15, DIM, False),
    ("", 6, DIM, False),
    ("Best on all global metrics", 16, ACCENT, True),
    ("  Much lower error than WHAM on long videos", 15, DIM, False),
    ("  Other methods can't achieve gravity-aligned results", 15, DIM, False),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(4.8), [
    ("Where it fails", 22, ACCENT, True),
    ("", 6, DIM, False),
    ("Single person only", 16, TEXT, False),
    ("No scene awareness / no contact with ground", 16, TEXT, False),
    ("No physics constraints", 16, TEXT, False),
    ("Poorer PA-MPJPE vs WHAM on some benchmarks", 16, TEXT, False),
    ("  (may be SMPL vs SMPLX parameter mismatch)", 15, DIM, False),
    ("", 10, DIM, False),
    ("Runtime breakdown", 22, C_GVHMR, True),
    ("", 6, DIM, False),
    ("Preprocessing: 46.0 s (1430 frames)", 15, TEXT, False),
    ("  Detection: 4.9 s", 14, DIM, False),
    ("  Pose estimation: 20.0 s", 14, DIM, False),
    ("  Feature extraction: 10.1 s", 14, DIM, False),
    ("  Visual odometry: 11.0 s", 14, DIM, False),
    ("Inference: 0.28 s", 15, ACCENT, True),
    ("Bottleneck is preprocessing, not the model", 15, DIM, False),
])

takeaway_bar(s, "For us: best single-person body backbone \u2014 fast, accurate, gravity-aligned. Needs physics + scene on top.", C_GVHMR)
slide_num(s, next_n())


# ════════════════════════════════════════════════════════════════════
#  ZipMap — 4 slides
# ════════════════════════════════════════════════════════════════════

# --- ZipMap 1: Overview ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "ZipMap", "Overview \u2014 Linear-Time 3D Reconstruction", C_ZIPMAP)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.8), Inches(4.8), [
    ("Problem", 20, C_ZIPMAP, True),
    ("  3D reconstruction from image collections", 16, TEXT, False),
    ("  Existing feed-forward models scale quadratically", 16, TEXT, False),
    ("  (every image attends to every other image)", 16, TEXT, False),
    ("", 10, DIM, False),
    ("Key insight", 20, C_ZIPMAP, True),
    ("  Replace global attention with test-time training", 16, TEXT, False),
    ("  \u2192 compress all images into learned fast weights", 16, TEXT, False),
    ("  \u2192 linear scaling instead of quadratic", 16, TEXT, False),
    ("", 10, DIM, False),
    ("Result", 20, C_ZIPMAP, True),
    ("  700 frames in <10 seconds (1 GPU)", 16, TEXT, False),
    ("  Quadratic methods: 200+ seconds", 16, TEXT, False),
    ("  3\u00d7 faster than previous linear methods", 16, TEXT, False),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(4.8), [
    ("Outputs", 20, C_ZIPMAP, True),
    ("", 6, DIM, False),
    ("Camera poses (4D quaternion + 3D translation)", 16, TEXT, False),
    ("Point maps (x, y, z per pixel in camera space)", 16, TEXT, False),
    ("Depth maps + confidence scores", 16, TEXT, False),
    ("Queryable implicit scene representation", 16, TEXT, False),
    ("", 10, DIM, False),
    ("Core concept: Fast Weights", 20, C_ZIPMAP, True),
    ("", 6, DIM, False),
    ("Standard: weights fixed after training", 15, TEXT, False),
    ("Fast weights: change at test time", 15, TEXT, False),
    ("  Training: learn how to update weights", 14, DIM, False),
    ("  Inference: weights adapt per input", 14, DIM, False),
    ("", 6, DIM, False),
    ("Like studying flashcards and absorbing them", 15, TEXT, False),
    ("vs carrying all cards around", 15, DIM, False),
])

takeaway_bar(s, "Linear-time 3D reconstruction that matches/beats quadratic methods \u2014 enables scaling to long videos", C_ZIPMAP)
slide_num(s, next_n())


# --- ZipMap 2: How it works ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "ZipMap", "How It Works \u2014 Architecture", C_ZIPMAP)

# Left: pipeline
arch_box(s, Inches(0.5), Inches(1.3), Inches(3.8), Inches(0.9),
         "Input Tokenization",
         "DINOv2 encoder \u2192 2D feature maps\nRay maps from camera params (9-dim per pixel)")
arrow_down(s, Inches(2.2), Inches(2.25))

arch_box(s, Inches(0.5), Inches(2.7), Inches(3.8), Inches(1.4),
         "Feature Backbone (24 blocks)",
         "Local Window Attention\n  + rotary pos. encoding\n  + spatial relationships within each view\n"
         "Global TTT Layers\n  + compress all tokens into fast weights")
arrow_down(s, Inches(2.2), Inches(4.15))

arch_box(s, Inches(0.5), Inches(4.6), Inches(3.8), Inches(1.6),
         "Prediction Heads",
         "Camera: quaternion + translation + intrinsics\n"
         "Point: (x,y,z) per pixel\n"
         "Depth: distance + confidence\n"
         "Query: novel viewpoint synthesis")

# Right: TTT block explanation
bullets(s, Inches(5.0), Inches(1.3), Inches(7.5), Inches(5.5), [
    ("Test-Time Training (TTT) Block", 20, C_ZIPMAP, True),
    ("", 6, DIM, False),
    ("The core innovation that makes it linear:", 16, TEXT, False),
    ("", 6, DIM, False),
    ("Attention approach (quadratic):", 16, TEXT, True),
    ("  Store all tokens, attend to all of them every time", 14, TEXT, False),
    ("  Cost grows with number of images squared", 14, DIM, False),
    ("", 6, DIM, False),
    ("TTT approach (linear):", 16, C_ZIPMAP, True),
    ("  Each token has key-value pairs", 14, TEXT, False),
    ("  Compute gradient of reconstruction loss", 14, TEXT, False),
    ("  Update fast-weight MLP: fw(x) = W\u2082(SiLU(W\u2081x) \u2299 W\u2083x)", 14, TEXT, False),
    ("  MLP absorbs all context \u2192 throw away raw tokens", 14, TEXT, False),
    ("", 8, DIM, False),
    ("Two modes:", 16, TEXT, True),
    ("  Bidirectional: see everything at once (more accurate)", 14, TEXT, False),
    ("     image 50 can inform image 1", 13, DIM, False),
    ("  Streaming: process sequentially (causal)", 14, TEXT, False),
    ("     each image does one gradient step", 13, DIM, False),
    ("     image 1 can't benefit from image 50", 13, DIM, False),
    ("", 8, DIM, False),
    ("Dynamic per-token learning rate > fixed global rate", 14, ACCENT, False),
])

slide_num(s, next_n())


# --- ZipMap 3: Why good + Where it fails ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "ZipMap", "Why Good \u00b7 Where It Fails \u00b7 How We Use It", C_ZIPMAP)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.5), Inches(2.5), [
    ("Why good", 22, C_ZIPMAP, True),
    ("", 6, DIM, False),
    ("State-of-the-art camera pose accuracy", 16, TEXT, False),
    ("Dense point maps match/exceed quadratic models", 16, TEXT, False),
    ("Implicit scene rep queryable at ~100 FPS", 16, TEXT, False),
    ("Bidirectional AND streaming support", 16, TEXT, False),
    ("24 layers local attention + TTT, trained on 64 H100s", 16, TEXT, False),
])

bullets(s, Inches(0.6), Inches(3.9), Inches(5.5), Inches(2.0), [
    ("Where it fails / Limitations", 22, ACCENT, True),
    ("", 6, DIM, False),
    ("Streaming mode less accurate than bidirectional", 16, TEXT, False),
    ("Requires DINOv2 features (heavyweight encoder)", 16, TEXT, False),
    ("No explicit human modeling", 16, TEXT, False),
    ("Trained on 64 H100s (not easy to retrain)", 16, TEXT, False),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(5.0), [
    ("How we can use this", 22, C_ZIPMAP, True),
    ("", 6, DIM, False),
    ("Scene backbone for physics-aware pipeline:", 16, TEXT, False),
    ("  \u2192 Dense geometry for contact surfaces", 15, TEXT, False),
    ("  \u2192 Camera poses for world-grounding", 15, TEXT, False),
    ("  \u2192 Real-time querying for novel views", 15, TEXT, False),
    ("", 8, DIM, False),
    ("Alternative to Depth Anything 3:", 16, TEXT, True),
    ("  ZipMap: full 3D reconstruction, heavier", 15, TEXT, False),
    ("  DA3: depth + poses, lighter, streaming", 15, TEXT, False),
    ("", 8, DIM, False),
    ("Implicit rep lets us:", 16, TEXT, True),
    ("  Query ground plane geometry", 15, TEXT, False),
    ("  Build SDF for penetration constraints", 15, TEXT, False),
    ("  Back-project into colored point cloud", 15, TEXT, False),
])

takeaway_bar(s, "Linear-time scene reconstruction \u2014 potential scene backbone, especially for dense contact geometry", C_ZIPMAP)
slide_num(s, next_n())


# ════════════════════════════════════════════════════════════════════
#  SAM-Body4D — 4 slides
# ════════════════════════════════════════════════════════════════════

# --- SAM-Body4D 1: Overview ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "SAM-Body4D", "Overview \u2014 Temporally Consistent Mesh Recovery", C_SAM4D)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.8), Inches(4.8), [
    ("Problem", 20, C_SAM4D, True),
    ("  Per-frame 3D body estimation is temporally inconsistent", 16, TEXT, False),
    ("  Occlusions cause degraded/hallucinated predictions", 16, TEXT, False),
    ("  Optimization-based video methods need large annotated data", 16, TEXT, False),
    ("", 10, DIM, False),
    ("Key insight", 20, C_SAM4D, True),
    ("  Videos have inherent human continuity", 16, TEXT, False),
    ("  Track identity-consistent masks across frames", 16, TEXT, False),
    ("  Transfer temporal coherence to 3D mesh output", 16, TEXT, False),
    ("", 10, DIM, False),
    ("Uses decoupled body representation:", 16, TEXT, True),
    ("  Skeleton (joint positions) predicted separately", 15, TEXT, False),
    ("  Shape (body surface) predicted separately", 15, TEXT, False),
    ("  Then combined \u2192 each branch can specialize", 15, TEXT, False),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(4.8), [
    ("Why better than standard parametric models?", 18, C_SAM4D, True),
    ("", 6, DIM, False),
    ("Scalable data engine:", 16, TEXT, True),
    ("  Augmented + generated + multi-view data", 15, TEXT, False),
    ("", 6, DIM, False),
    ("Separate body/hand optimization:", 16, TEXT, True),
    ("  Different strategies per body part", 15, TEXT, False),
    ("", 6, DIM, False),
    ("Decoupled skeleton/shape:", 16, TEXT, True),
    ("  Standard: shape affects joint positions (coupled)", 15, TEXT, False),
    ("  This: predict separately, then combine", 15, TEXT, False),
    ("  Skeleton = easier, shape = varies across people", 15, TEXT, False),
    ("  but shape doesn't change within a video", 15, TEXT, False),
    ("", 10, DIM, False),
    ("Single GPU inference", 16, TEXT, False),
])

takeaway_bar(s, "Brings temporal consistency to body mesh recovery via video segmentation \u2014 handles occlusions", C_SAM4D)
slide_num(s, next_n())


# --- SAM-Body4D 2: How it works ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "SAM-Body4D", "How It Works \u2014 Pipeline", C_SAM4D)

# Three-stage pipeline
arch_box(s, Inches(0.5), Inches(1.3), Inches(3.5), Inches(1.6),
         "1. Masklet Generator",
         "Promptable video segmentation\n"
         "Propagate: spatial-temporal\n"
         "  correspondences across frames\n"
         "Detect: semantic associations\n"
         "  between prompt and objects")

arch_box(s, Inches(4.5), Inches(1.3), Inches(4.2), Inches(1.6),
         "2. Occlusion-Aware Refiner",
         "Diffusion-based inpainting predicts\n"
         "  full body mask (even occluded parts)\n"
         "Compare with original \u2192 detect occlusion\n"
         "Group flagged frames into chunks\n"
         "Inpaint actual RGB pixels behind occluder")

arch_box(s, Inches(9.2), Inches(1.3), Inches(3.5), Inches(1.6),
         "3. Mask-Guided HMR",
         "Per-frame mesh estimation\n"
         "Guided by consistent masklets\n"
         "Temporal coherence naturally\n"
         "  propagated to output meshes")

# Details below
bullets(s, Inches(0.6), Inches(3.3), Inches(5.5), Inches(3.5), [
    ("Masklet = per-object mask tracked across frames", 16, TEXT, True),
    ("", 6, DIM, False),
    ("Propagation carries mask labels through time", 15, TEXT, False),
    ("  preserving identity and continuity", 14, DIM, False),
    ("", 8, DIM, False),
    ("Occlusion handling is the key differentiator:", 16, C_SAM4D, True),
    ("", 6, DIM, False),
    ("1. Predict full body mask (diffusion model)", 15, TEXT, False),
    ("2. Compare with actual visible mask", 15, TEXT, False),
    ("3. If mismatch \u2192 occlusion detected", 15, TEXT, False),
    ("4. Inpaint missing RGB pixels", 15, TEXT, False),
    ("5. Feed clean image to mesh estimator", 15, TEXT, False),
])

bullets(s, Inches(7.0), Inches(3.3), Inches(5.5), Inches(3.5), [
    ("Prior HMR approaches", 16, C_SAM4D, True),
    ("", 6, DIM, False),
    ("Regression-based:", 15, TEXT, True),
    ("  Regress parametric model params from features", 14, TEXT, False),
    ("  No occlusion handling", 14, DIM, False),
    ("", 6, DIM, False),
    ("Token-based:", 15, TEXT, True),
    ("  Joints/vertices as learnable tokens", 14, TEXT, False),
    ("  Transformer reasons over relationships", 14, TEXT, False),
    ("  Still no occlusion handling", 14, DIM, False),
    ("", 6, DIM, False),
    ("Temporal smoothness methods:", 15, TEXT, True),
    ("  GRU / transformer over frame features", 14, TEXT, False),
    ("  Feature-level only, don't recover occluded pixels", 14, DIM, False),
])

slide_num(s, next_n())


# --- SAM-Body4D 3: Why good + Failures + Usage ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "SAM-Body4D", "Why Good \u00b7 Where It Fails \u00b7 How We Use It", C_SAM4D)

bullets(s, Inches(0.6), Inches(1.3), Inches(3.8), Inches(5.0), [
    ("Why good", 20, C_SAM4D, True),
    ("", 6, DIM, False),
    ("Occlusion-robust: recovers hidden", 15, TEXT, False),
    ("  body parts via inpainting", 14, DIM, False),
    ("Temporally consistent across", 15, TEXT, False),
    ("  entire video (not per-frame)", 14, DIM, False),
    ("No optimization / no large", 15, TEXT, False),
    ("  annotated video datasets needed", 14, DIM, False),
    ("Modular: swap in better", 15, TEXT, False),
    ("  components as they appear", 14, DIM, False),
    ("Body + hands + face", 15, TEXT, False),
    ("  (full body, not just skeleton)", 14, DIM, False),
])

bullets(s, Inches(4.8), Inches(1.3), Inches(3.8), Inches(5.0), [
    ("Where it fails", 20, ACCENT, True),
    ("", 6, DIM, False),
    ("Relies on diffusion inpainting", 15, TEXT, False),
    ("  quality \u2192 can hallucinate badly", 14, DIM, False),
    ("Segmentation errors cascade", 15, TEXT, False),
    ("  to mesh predictions", 14, DIM, False),
    ("No physics constraints", 15, TEXT, False),
    ("  (floating, penetration still possible)", 14, DIM, False),
    ("Multi-person interactions", 15, TEXT, False),
    ("  not explicitly handled", 14, DIM, False),
    ("Depends on quality of initial", 15, TEXT, False),
    ("  video segmentation prompt", 14, DIM, False),
])

bullets(s, Inches(9.0), Inches(1.3), Inches(3.8), Inches(5.0), [
    ("How we use this", 20, C_SAM4D, True),
    ("", 6, DIM, False),
    ("Better body backbone for", 15, TEXT, False),
    ("  occluded scenarios", 14, DIM, False),
    ("", 6, DIM, False),
    ("Sports applications:", 15, TEXT, True),
    ("  Players often occlude each other", 14, TEXT, False),
    ("  (soccer, basketball)", 14, DIM, False),
    ("", 6, DIM, False),
    ("ASICS partnership:", 15, C_SAM4D, True),
    ("  Analyze running / soccer from", 14, TEXT, False),
    ("  internet game footage", 14, TEXT, False),
    ("  where occlusion is frequent", 14, DIM, False),
    ("", 6, DIM, False),
    ("Combine with physics layer", 15, TEXT, False),
    ("  for contact-aware output", 14, DIM, False),
])

takeaway_bar(s, "Temporal consistency + occlusion handling \u2014 critical for sports / multi-person scenarios", C_SAM4D)
slide_num(s, next_n())


# ════════════════════════════════════════════════════════════════════
#  PhysHMR — 3 slides
# ════════════════════════════════════════════════════════════════════

# --- PhysHMR 1: Overview ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "PhysHMR", "Overview \u2014 Unified Visual-to-Physics Motion", C_PHYS)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.8), Inches(4.8), [
    ("Problem", 20, C_PHYS, True),
    ("  Post-physics optimization is fundamentally limited:", 16, TEXT, False),
    ("  Motion reconstructed from vision alone, then refined", 16, TEXT, False),
    ("  by a separate physics module", 16, TEXT, False),
    ("", 8, DIM, False),
    ("  Once the vision model picks one interpretation,", 15, DIM, False),
    ("  the physics module can't access the full visual context", 15, DIM, False),
    ("  \u2192 suboptimal corrections", 15, DIM, False),
    ("", 10, DIM, False),
    ("Evidence (foot sliding):", 20, C_PHYS, True),
    ("  GVHMR alone: 5.65 mm", 16, TEXT, False),
    ("  GVHMR + RL post-correction: 12.71 mm (worse!)", 16, ACCENT, True),
    ("  PhysHMR end-to-end: 4.60 mm (best)", 16, C_PHYS, True),
    ("", 8, DIM, False),
    ("RL post-correction makes foot sliding 2.2\u00d7 worse", 16, ACCENT, False),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(4.8), [
    ("Key insight", 20, C_PHYS, True),
    ("  Unify motion estimation + physical reasoning", 16, TEXT, False),
    ("  in a single framework", 16, TEXT, False),
    ("", 10, DIM, False),
    ("Main contributions", 20, C_PHYS, True),
    ("", 6, DIM, False),
    ("First unified perception + control framework", 16, TEXT, False),
    ("", 6, DIM, False),
    ("Knowledge distillation from", 16, TEXT, False),
    ("  mocap-trained imitation expert", 15, DIM, False),
    ("  (stabilizes learning, faster convergence)", 15, DIM, False),
    ("", 6, DIM, False),
    ("2D keypoints \u2192 3D rays as soft global reference", 16, TEXT, False),
    ("  (not hard positional targets)", 15, DIM, False),
    ("", 6, DIM, False),
    ("Prior RL methods have low sample efficiency", 16, TEXT, False),
    ("  Distillation solves this", 15, DIM, False),
])

takeaway_bar(s, "Physics must be integrated, not bolted on \u2014 post-correction makes things worse", C_PHYS)
slide_num(s, next_n())


# --- PhysHMR 2: How it works ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "PhysHMR", "How It Works \u2014 Architecture", C_PHYS)

# Pipeline
arch_box(s, Inches(0.5), Inches(1.3), Inches(3.0), Inches(1.2),
         "Video Encoder (from GVHMR)",
         "Extract image features,\nbboxes, 2D keypoints,\nrelative camera rotations")

arch_box(s, Inches(4.0), Inches(1.3), Inches(4.5), Inches(1.2),
         "Pixel-As-Ray Strategy",
         "Back-project 2D keypoints into 3D rays\nusing camera intrinsics K\n\u2192 soft global pose reference, no hard targets")

arch_box(s, Inches(9.0), Inches(1.3), Inches(3.8), Inches(1.2),
         "Multi-task MLP Head",
         "Regress future root orientation\nfrom visual features\n\u2192 forward-looking estimate")

# Bottom: RL + distillation
arch_box(s, Inches(0.5), Inches(3.0), Inches(5.5), Inches(1.8),
         "Markov Decision Process (RL)",
         "M = <S, A, T, R, \u03b3>\n"
         "State: simulation pose + velocity\n"
         "Action: joint torques\n"
         "Reference: trajectory from video encoder\n"
         "  (local pose + global translation/rotation)")

arch_box(s, Inches(6.5), Inches(3.0), Inches(6.0), Inches(1.8),
         "Distillation from MoCap Expert",
         "Problem: RL from scratch has low sample efficiency\n"
         "Solution: pre-train imitation policy on mocap data\n"
         "  then distill knowledge into visual-to-action policy\n"
         "\u2192 accelerates convergence, stabilizes learning")

bullets(s, Inches(0.6), Inches(5.2), Inches(12), Inches(1.5), [
    ("Pixel-as-Ray: encodes global guidance without enforcing explicit positional targets", 15, C_PHYS, True),
    ("  Given keypoint (u, v) + intrinsics K \u2192 back-project to 3D ray in camera coords", 14, TEXT, False),
    ("  Local pose: SMPL joint rotations relative to parents (captures articulation)", 14, TEXT, False),
    ("  3D root prediction from monocular video is noisy \u2192 rays give soft spatial grounding instead", 14, DIM, False),
])

slide_num(s, next_n())


# --- PhysHMR 3: Why good + Failures ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "PhysHMR", "Why Good \u00b7 Where It Fails \u00b7 How We Use It", C_PHYS)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.5), Inches(4.8), [
    ("Why good", 22, C_PHYS, True),
    ("", 6, DIM, False),
    ("Proves physics and vision must be unified", 16, TEXT, False),
    ("  not cascaded in two stages", 15, DIM, False),
    ("", 6, DIM, False),
    ("Best foot sliding (4.60 mm)", 16, TEXT, False),
    ("  beating both GVHMR alone and GVHMR+RL", 15, DIM, False),
    ("", 6, DIM, False),
    ("Distillation makes RL practical", 16, TEXT, False),
    ("  (no massive exploration needed)", 15, DIM, False),
    ("", 6, DIM, False),
    ("Pixel-as-ray is elegant", 16, TEXT, False),
    ("  soft constraint, not hard target", 15, DIM, False),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(4.8), [
    ("Where it fails", 22, ACCENT, True),
    ("", 6, DIM, False),
    ("Single person only", 16, TEXT, False),
    ("Requires physics simulator in the loop", 16, TEXT, False),
    ("  (slower than pure feed-forward)", 15, DIM, False),
    ("Still relies on GVHMR encoder quality", 16, TEXT, False),
    ("No scene-aware contact", 16, TEXT, False),
    ("", 10, DIM, False),
    ("How we use it", 22, C_PHYS, True),
    ("", 6, DIM, False),
    ("Architecture reference for end-to-end", 16, TEXT, False),
    ("  physics integration", 15, DIM, False),
    ("Pixel-as-ray strategy reusable", 16, TEXT, False),
    ("", 6, DIM, False),
    ("Warning: don't bolt physics on as", 16, ACCENT, True),
    ("  post-processing \u2014 it backfires", 15, ACCENT, False),
])

takeaway_bar(s, "For us: validates end-to-end physics. Pixel-as-ray reusable. Post-correction is the wrong approach.", C_PHYS)
slide_num(s, next_n())


# ════════════════════════════════════════════════════════════════════
#  MultiPhys — 3 slides
# ════════════════════════════════════════════════════════════════════

# --- MultiPhys 1: Overview ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "MultiPhys", "Overview \u2014 Multi-Person Physics Correction", C_MULTI)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.8), Inches(4.8), [
    ("Problem", 20, C_MULTI, True),
    ("  Kinematic poses look good visually but violate physics:", 16, TEXT, False),
    ("  people float, penetrate each other, slide on ground", 16, TEXT, False),
    ("", 8, DIM, False),
    ("  Limited methods address multi-person contacts", 15, DIM, False),
    ("  and penetration issues", 15, DIM, False),
    ("", 10, DIM, False),
    ("Approach", 20, C_MULTI, True),
    ("  Take kinematic poses (from any body tracker)", 16, TEXT, False),
    ("  Simulate them as articulated bodies in physics engine", 16, TEXT, False),
    ("  RL policy drives each body toward target pose", 16, TEXT, False),
    ("  while obeying physical laws", 16, TEXT, False),
    ("", 10, DIM, False),
    ("First method for multi-person physics correction", 16, ACCENT, True),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(4.8), [
    ("Results", 20, C_MULTI, True),
    ("", 6, DIM, False),
    ("7\u00d7 less body-ground penetration", 16, TEXT, False),
    ("Physically plausible multi-person motion", 16, TEXT, False),
    ("", 10, DIM, False),
    ("Penetration metric: SDF", 18, C_MULTI, True),
    ("", 6, DIM, False),
    ("Signed Distance Field gives not just", 15, TEXT, False),
    ("  whether vertices penetrate, but how deep", 14, DIM, False),
    ("Sum over penetrating vertices \u2192 single scalar", 15, TEXT, False),
    ("  captures count AND depth (better than", 14, DIM, False),
    ("  just counting penetrating vertices)", 14, DIM, False),
    ("", 10, DIM, False),
    ("Input: any kinematic tracker output", 16, TEXT, True),
    ("  (tested with SLAHMR)", 15, DIM, False),
])

takeaway_bar(s, "Physics simulation dramatically reduces artifacts \u2014 first multi-person approach", C_MULTI)
slide_num(s, next_n())


# --- MultiPhys 2: How it works ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "MultiPhys", "How It Works \u2014 Pipeline", C_MULTI)

# Pipeline as numbered stages
arch_box(s, Inches(0.3), Inches(1.3), Inches(2.3), Inches(1.0),
         "1. Kinematic Poses",
         "Input from body tracker\n(e.g. SLAHMR)")

arch_box(s, Inches(2.9), Inches(1.3), Inches(2.5), Inches(1.0),
         "2. Humanoid Agents",
         "Each person \u2192 articulated\nbody in physics engine")

arch_box(s, Inches(5.7), Inches(1.3), Inches(3.5), Inches(1.0),
         "3. Universal Controller",
         "Neural network policy:\nstate + target \u2192 joint torques")

arch_box(s, Inches(9.5), Inches(1.3), Inches(3.3), Inches(1.0),
         "4. Physics Simulation",
         "Step engine, resolve\ncollisions + contacts")

# Loop-N detail
arch_box(s, Inches(0.3), Inches(2.8), Inches(12.5), Inches(0.8),
         "5. Loop-N Fix: for extreme poses (gymnastics, dancing, fighting) \u2192 loop N times on same target pose",
         "Instead of stepping once per frame, repeat simulation steps until convergence on challenging poses")

# Controller detail
bullets(s, Inches(0.6), Inches(4.0), Inches(5.5), Inches(3.0), [
    ("Universal Humanoid Controller (UHC)", 18, C_MULTI, True),
    ("", 6, DIM, False),
    ("Input:", 15, TEXT, True),
    ("  Current simulation state (pose + velocity)", 14, TEXT, False),
    ("  Target kinematic pose (where tracker says)", 14, TEXT, False),
    ("  Body shape parameters", 14, TEXT, False),
    ("", 6, DIM, False),
    ("Output:", 15, TEXT, True),
    ("  Joint torques that drive simulated body", 14, TEXT, False),
    ("  toward target while obeying physics", 14, TEXT, False),
    ("", 6, DIM, False),
    ("Each person has independent controller", 15, TEXT, False),
    ("  but they share the physics world", 14, DIM, False),
])

bullets(s, Inches(7.0), Inches(4.0), Inches(5.5), Inches(3.0), [
    ("Input tracker: SLAHMR", 18, C_MULTI, True),
    ("", 6, DIM, False),
    ("Simultaneous Localization + HMR", 15, TEXT, False),
    ("  Camera trajectory + human 3D poses", 14, DIM, False),
    ("  in shared world coordinates", 14, DIM, False),
    ("", 6, DIM, False),
    ("SLAHMR output is visually good but:", 15, TEXT, True),
    ("  Sliding feet", 14, ACCENT, False),
    ("  Body-body penetration", 14, ACCENT, False),
    ("  Floating / ground penetration", 14, ACCENT, False),
    ("  Not usable in physics simulators", 14, ACCENT, False),
    ("", 6, DIM, False),
    ("MultiPhys fixes all of these", 15, C_MULTI, True),
])

slide_num(s, next_n())


# --- MultiPhys 3: Why good + Failures + Usage ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "MultiPhys", "Why Good \u00b7 Where It Fails \u00b7 How We Use It", C_MULTI)

bullets(s, Inches(0.6), Inches(1.3), Inches(3.8), Inches(5.0), [
    ("Why good", 20, C_MULTI, True),
    ("", 6, DIM, False),
    ("7\u00d7 less penetration", 16, TEXT, False),
    ("Multi-person (first of its kind)", 16, TEXT, False),
    ("Agnostic to input tracker", 16, TEXT, False),
    ("  (plug in any body tracker)", 14, DIM, False),
    ("Resolves body-body collisions", 16, TEXT, False),
    ("  automatically via physics engine", 14, DIM, False),
    ("", 6, DIM, False),
    ("Feed-forward HMR methods:", 15, DIM, True),
    ("  Regression = all frames at once", 14, DIM, False),
    ("  Autoregressive = sequential", 14, DIM, False),
    ("  MultiPhys works with either", 14, DIM, False),
])

bullets(s, Inches(4.8), Inches(1.3), Inches(3.8), Inches(5.0), [
    ("Where it fails", 20, ACCENT, True),
    ("", 6, DIM, False),
    ("RL policy can create artifacts:", 16, TEXT, False),
    ("  Arm flailing for balance recovery", 15, ACCENT, False),
    ("", 6, DIM, False),
    ("Post-correction approach:", 16, TEXT, False),
    ("  PhysHMR showed this can backfire", 15, ACCENT, False),
    ("  (2.2\u00d7 worse foot sliding)", 15, ACCENT, False),
    ("", 6, DIM, False),
    ("Depends on SLAHMR quality", 16, TEXT, False),
    ("  as kinematic input", 14, DIM, False),
    ("", 6, DIM, False),
    ("No scene geometry", 16, TEXT, False),
    ("  (flat ground only)", 14, DIM, False),
])

bullets(s, Inches(9.0), Inches(1.3), Inches(3.8), Inches(5.0), [
    ("How we use it", 20, C_MULTI, True),
    ("", 6, DIM, False),
    ("Reference for physics simulation", 16, TEXT, False),
    ("  integration approach", 14, DIM, False),
    ("", 6, DIM, False),
    ("UHC controller design is", 16, TEXT, False),
    ("  reusable for our pipeline", 14, DIM, False),
    ("", 6, DIM, False),
    ("SDF penetration metric", 16, TEXT, True),
    ("  for our evaluation", 14, DIM, False),
    ("", 6, DIM, False),
    ("ASICS application:", 16, C_MULTI, True),
    ("  Multi-person sports footage", 14, TEXT, False),
    ("  Basketball, soccer interactions", 14, TEXT, False),
    ("  Person-to-person contact", 14, TEXT, False),
    ("  ACL injury analysis", 14, TEXT, False),
])

takeaway_bar(s, "For us: multi-person physics pipeline + SDF metrics. But beware RL post-correction pitfalls.", C_MULTI)
slide_num(s, next_n())


# ════════════════════════════════════════════════════════════════════
#  SUMMARY SLIDE
# ════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank)
s.background.fill.solid()
s.background.fill.fore_color.rgb = TEAL

tx(s, Inches(1.5), Inches(0.8), Inches(10), Inches(0.6),
   "Summary", sz=36, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

# Paper summaries in columns
bullets(s, Inches(0.8), Inches(1.8), Inches(5.5), Inches(5.0), [
    ("GVHMR", 20, WHITE, True),
    ("  Gravity-anchored body tracking, no drift", 15, WHITE, False),
    ("  Best single-person accuracy", 15, WHITE, False),
    ("", 10, WHITE, False),
    ("ZipMap", 20, WHITE, True),
    ("  Linear-time 3D reconstruction via fast weights", 15, WHITE, False),
    ("  Dense scene geometry for contact surfaces", 15, WHITE, False),
    ("", 10, WHITE, False),
    ("SAM-Body4D", 20, WHITE, True),
    ("  Temporal consistency + occlusion recovery", 15, WHITE, False),
    ("  Critical for sports / multi-person scenarios", 15, WHITE, False),
])

bullets(s, Inches(7.0), Inches(1.8), Inches(5.5), Inches(5.0), [
    ("PhysHMR", 20, WHITE, True),
    ("  Proves physics must be end-to-end, not bolted on", 15, WHITE, False),
    ("  Post-correction makes things worse", 15, WHITE, False),
    ("", 10, WHITE, False),
    ("MultiPhys", 20, WHITE, True),
    ("  Multi-person physics via simulation", 15, WHITE, False),
    ("  SDF metrics, but RL can backfire", 15, WHITE, False),
    ("", 14, WHITE, False),
    ("Common thread:", 20, WHITE, True),
    ("  Vision proposes, physics refines", 16, WHITE, False),
    ("  but integration beats cascade", 16, WHITE, False),
])

slide_num(s, next_n())


# ── Save ──
out = "/home/user/Pact3D/Paper_DeepDives.pptx"
prs.save(out)
print(f"Saved {N[0]} slides to {out}")

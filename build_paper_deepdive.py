#!/usr/bin/env python3
"""
Build deep-dive slides for 5 papers:
  GVHMR · ZipMap · SAM-Body4D · PhysHMR · MultiPhys

Each paper gets exactly 4 slides:
  1. How it works / What makes it work + Why good
  2. Where it fails + Edge cases / Success cases
  3. Main Components
  4. How can we use this

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
N = [0]


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
    tan_box(slide, Inches(0.5), Inches(6.3), Inches(12), Inches(0.7))
    tx(slide, Inches(0.7), Inches(6.4), Inches(11.6), Inches(0.5),
       text, sz=14, bold=True, color=color)


def arrow_down(slide, x, y):
    tx(slide, x, y, Inches(0.5), Inches(0.4),
       "\u2193", sz=24, color=DIM, align=PP_ALIGN.CENTER)


def arrow_right(slide, x, y):
    tx(slide, x, y, Inches(0.5), Inches(0.4),
       "\u2192", sz=24, color=DIM, align=PP_ALIGN.CENTER)


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


# ╔══════════════════════════════════════════════════════════════════╗
# ║  GVHMR — 4 slides                                              ║
# ╚══════════════════════════════════════════════════════════════════╝

# --- GVHMR 1/4: How it works + Why good ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "GVHMR", "How It Works  \u00b7  Why Good", C_GVHMR)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.8), Inches(5.0), [
    ("How it works", 22, C_GVHMR, True),
    ("", 6, DIM, False),
    ("Defines Gravity-View (GV) coordinate system:", 16, TEXT, True),
    ("  Y = gravity direction (up)", 15, TEXT, False),
    ("  X = Y \u00d7 camera view (perpendicular)", 15, TEXT, False),
    ("  Z = X \u00d7 Y (roughly camera forward)", 15, TEXT, False),
    ("", 6, DIM, False),
    ("Recover gravity-aware pose per frame,", 16, TEXT, False),
    ("then compose into global trajectory", 16, TEXT, False),
    ("", 6, DIM, False),
    ("Static camera: GV identical across frames", 15, TEXT, False),
    ("  \u2192 accumulate velocities directly", 14, DIM, False),
    ("  world_pos[t] = world_pos[0] + \u03a3(orient[i] \u00b7 vel[i])", 14, DIM, False),
    ("Moving camera: compute rotation between", 15, TEXT, False),
    ("  consecutive GV systems, transform accordingly", 14, DIM, False),
    ("", 6, DIM, False),
    ("No initialization, fully parallel prediction", 15, ACCENT, True),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(5.0), [
    ("Why good", 22, C_GVHMR, True),
    ("", 6, DIM, False),
    ("GV anchors each frame independently", 16, TEXT, False),
    ("  \u2192 no drift on long videos", 15, DIM, False),
    ("  Autoregressive methods slowly rotate \"up\"", 15, DIM, False),
    ("  away from gravity. GV prevents this.", 15, DIM, False),
    ("", 6, DIM, False),
    ("Transformer generalizes to arbitrary lengths", 16, TEXT, False),
    ("  Rotary embeddings = relative position encoding", 15, DIM, False),
    ("  \"how far apart\" not \"which absolute position\"", 15, DIM, False),
    ("", 6, DIM, False),
    ("Multi-task learning boosts camera-space too", 16, TEXT, False),
    ("  Global motion info improves local estimates", 15, DIM, False),
    ("", 6, DIM, False),
    ("Best on all global motion recovery metrics", 16, ACCENT, True),
    ("Much lower error than alternatives on long vids", 16, TEXT, False),
    ("Other methods cannot achieve gravity-aligned results", 15, DIM, False),
])

takeaway_bar(s, "Feed-forward, gravity-aware body tracking \u2014 no drift, no error accumulation, best global metrics", C_GVHMR)
slide_num(s, next_n())


# --- GVHMR 2/4: Where it fails + Edge/Success cases ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "GVHMR", "Where It Fails  \u00b7  Edge Cases & Success Cases", C_GVHMR)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.8), Inches(5.0), [
    ("Where it fails", 22, ACCENT, True),
    ("", 6, DIM, False),
    ("Single person only \u2014 no multi-person support", 16, TEXT, False),
    ("No scene awareness / no ground contact", 16, TEXT, False),
    ("No physics constraints (floating, penetration)", 16, TEXT, False),
    ("", 6, DIM, False),
    ("Poorer PA-MPJPE vs some methods", 16, TEXT, False),
    ("  Likely SMPL vs SMPLX parameter mismatch", 15, DIM, False),
    ("  (predicts SMPLX but evaluated on SMPL joints)", 15, DIM, False),
    ("", 6, DIM, False),
    ("Preprocessing is the real bottleneck:", 16, TEXT, True),
    ("  Detection: 4.9 s", 14, DIM, False),
    ("  Pose estimation: 20.0 s", 14, DIM, False),
    ("  Feature extraction: 10.1 s", 14, DIM, False),
    ("  Visual odometry: 11.0 s", 14, DIM, False),
    ("  Total preprocessing: 46.0 s", 14, ACCENT, False),
    ("  Actual inference: 0.28 s", 14, ACCENT, False),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(5.0), [
    ("Success cases", 20, C_GVHMR, True),
    ("", 6, DIM, False),
    ("Long videos (1430+ frames)", 16, TEXT, False),
    ("  Where autoregressive methods drift badly", 15, DIM, False),
    ("Videos with moving cameras", 16, TEXT, False),
    ("  GV system handles camera rotation naturally", 15, DIM, False),
    ("Single-person sports/motion capture", 16, TEXT, False),
    ("", 10, DIM, False),
    ("Edge cases / What makes it fail", 20, ACCENT, True),
    ("", 6, DIM, False),
    ("Ambiguity in X-Z plane:", 16, TEXT, True),
    ("  Any rotation around Y (gravity) is valid", 15, TEXT, False),
    ("  GV resolves by anchoring X to camera view", 15, DIM, False),
    ("  \u2192 but camera view estimation errors propagate", 15, ACCENT, False),
    ("", 6, DIM, False),
    ("Visual odometry failure \u2192 wrong camera rotations", 16, TEXT, False),
    ("  \u2192 GV system misaligned \u2192 trajectory drifts", 15, ACCENT, False),
    ("Occlusion: no handling at all", 16, TEXT, False),
])

slide_num(s, next_n())


# --- GVHMR 3/4: Main Components ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "GVHMR", "Main Components", C_GVHMR)

# Left column: architecture pipeline
arch_box(s, Inches(0.5), Inches(1.3), Inches(3.0), Inches(0.9),
         "Input Features",
         "Bounding boxes, 2D keypoints,\nimage features, relative camera rotations")
arrow_down(s, Inches(1.75), Inches(2.25))

arch_box(s, Inches(0.5), Inches(2.7), Inches(3.0), Inches(0.9),
         "Early Fusion Module",
         "Map all features to same dim\n\u2192 per-frame tokens")
arrow_down(s, Inches(1.75), Inches(3.65))

arch_box(s, Inches(0.5), Inches(4.1), Inches(3.0), Inches(0.9),
         "Relative Transformer",
         "12 layers, 8 attention heads\nRotary positional embedding")
arrow_down(s, Inches(1.75), Inches(5.05))

arch_box(s, Inches(0.5), Inches(5.5), Inches(3.0), Inches(0.9),
         "Multi-task MLP Heads",
         "Pose, shape, camera params,\ntrajectory, stationary labels")

# Middle column: component details
bullets(s, Inches(4.0), Inches(1.3), Inches(4.5), Inches(5.5), [
    ("Transformer details", 18, C_GVHMR, True),
    ("", 6, DIM, False),
    ("12 encoder layers", 15, TEXT, False),
    ("8 attention heads per layer", 15, TEXT, False),
    ("  Each learns different temporal patterns:", 14, DIM, False),
    ("  nearby frames, distant frames, etc.", 14, DIM, False),
    ("Rotary positional embeddings (RoPE)", 15, TEXT, False),
    ("  Relative, not absolute position", 14, DIM, False),
    ("  \u2192 generalizes to any video length", 14, DIM, False),
    ("", 8, DIM, False),
    ("MLP: two linear layers + GELU activation", 15, TEXT, False),
    ("  (GELU = soft gating to zero)", 14, DIM, False),
    ("", 8, DIM, False),
    ("Multi-task outputs:", 15, TEXT, True),
    ("  Weak-perspective camera params", 14, TEXT, False),
    ("  Human orientation in camera frame", 14, TEXT, False),
    ("  SMPL local pose + shape", 14, TEXT, False),
    ("  Stationary label (contact prob)", 14, TEXT, False),
    ("  Global trajectory representation", 14, TEXT, False),
])

# Right column: post-processing + training
bullets(s, Inches(9.0), Inches(1.3), Inches(3.8), Inches(5.5), [
    ("Post-Processing", 18, C_GVHMR, True),
    ("", 6, DIM, False),
    ("Weak \u2192 full perspective via CLIFF", 15, TEXT, False),
    ("  Recovers depth from simplified params", 14, DIM, False),
    ("", 6, DIM, False),
    ("Stationary prob per joint", 15, TEXT, False),
    ("Update global translation per frame", 15, TEXT, False),
    ("IK solver (CCD-based)", 15, TEXT, False),
    ("  Fine-grained stationary contact points", 14, DIM, False),
    ("", 10, DIM, False),
    ("Training", 18, C_GVHMR, True),
    ("", 6, DIM, False),
    ("Trained from scratch, mixed dataset", 15, TEXT, False),
    ("Augment 2D keypoints", 15, TEXT, False),
    ("Simulate static/dynamic camera", 15, TEXT, False),
    ("  trajectories", 14, DIM, False),
    ("Normalize keypoints [-1, 1]", 15, TEXT, False),
    ("Image feature dropout (set to 0)", 15, TEXT, False),
])

slide_num(s, next_n())


# --- GVHMR 4/4: How can we use this ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "GVHMR", "How Can We Use This", C_GVHMR)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.8), Inches(5.0), [
    ("Primary body tracking backbone", 22, C_GVHMR, True),
    ("", 6, DIM, False),
    ("Best single-person accuracy + speed", 16, TEXT, False),
    ("Gravity-aligned output ready for physics layer", 16, TEXT, False),
    ("Feed-forward = no sequential bottleneck", 16, TEXT, False),
    ("", 10, DIM, False),
    ("In our pipeline:", 20, C_GVHMR, True),
    ("", 6, DIM, False),
    ("Video \u2192 GVHMR \u2192 world-grounded SMPL poses", 16, TEXT, False),
    ("  + scene reconstruction (ZipMap / DA3)", 15, DIM, False),
    ("  \u2192 physics refinement layer", 15, DIM, False),
    ("  \u2192 physically realistic 3D motion", 15, DIM, False),
    ("", 10, DIM, False),
    ("GVHMR is also the encoder backbone for PhysHMR", 16, TEXT, True),
    ("  \u2192 proven to work as visual frontend", 15, DIM, False),
    ("  for physics-aware downstream tasks", 15, DIM, False),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(5.0), [
    ("What we get from it", 20, C_GVHMR, True),
    ("", 6, DIM, False),
    ("Per-frame SMPL body meshes", 16, TEXT, False),
    ("World-grounded trajectory", 16, TEXT, False),
    ("Stationary contact labels per joint", 16, TEXT, False),
    ("Camera parameters", 16, TEXT, False),
    ("", 10, DIM, False),
    ("What we still need to add", 20, ACCENT, True),
    ("", 6, DIM, False),
    ("Scene geometry (ground plane, obstacles)", 16, TEXT, False),
    ("Physics constraints (penetration, sliding)", 16, TEXT, False),
    ("Multi-person support", 16, TEXT, False),
    ("Occlusion handling", 16, TEXT, False),
    ("", 10, DIM, False),
    ("Code available, 280 ms inference", 16, DIM, False),
])

takeaway_bar(s, "Our body backbone: fast, accurate, gravity-aligned. Layer scene + physics on top.", C_GVHMR)
slide_num(s, next_n())


# ╔══════════════════════════════════════════════════════════════════╗
# ║  ZipMap — 4 slides                                              ║
# ╚══════════════════════════════════════════════════════════════════╝

# --- ZipMap 1/4: How it works + Why good ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "ZipMap", "How It Works  \u00b7  Why Good", C_ZIPMAP)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.8), Inches(5.0), [
    ("How it works", 22, C_ZIPMAP, True),
    ("", 6, DIM, False),
    ("Replace global attention with test-time training:", 16, TEXT, True),
    ("", 6, DIM, False),
    ("Attention (quadratic):", 15, TEXT, True),
    ("  Carry all flashcards around", 14, TEXT, False),
    ("  Every question = flip through all of them", 14, DIM, False),
    ("", 6, DIM, False),
    ("TTT (linear):", 15, C_ZIPMAP, True),
    ("  Study all flashcards once, absorb into MLP weights", 14, TEXT, False),
    ("  Throw away cards, recall from memory", 14, TEXT, False),
    ("  Speed doesn't depend on number of cards", 14, DIM, False),
    ("", 6, DIM, False),
    ("Fast weights: adapt at test time", 16, TEXT, True),
    ("  fw(x) = W\u2082(SiLU(W\u2081x) \u2299 W\u2083x)", 14, TEXT, False),
    ("  Each token split into key + value", 14, DIM, False),
    ("  Compute gradient loss across all tokens", 14, DIM, False),
    ("  MLP absorbs context \u2192 discard raw tokens", 14, DIM, False),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(5.0), [
    ("Why good", 22, C_ZIPMAP, True),
    ("", 6, DIM, False),
    ("700 frames in <10 seconds (1 H100 GPU)", 16, TEXT, False),
    ("  Quadratic methods: 200+ seconds", 15, DIM, False),
    ("  3\u00d7 faster than prior linear methods", 15, DIM, False),
    ("", 6, DIM, False),
    ("State-of-the-art camera pose accuracy", 16, TEXT, False),
    ("  while maintaining linear time complexity", 15, DIM, False),
    ("", 6, DIM, False),
    ("Dense point maps match/exceed quadratic models", 16, TEXT, False),
    ("", 6, DIM, False),
    ("Implicit scene rep queryable at ~100 FPS", 16, TEXT, False),
    ("  Compress entire scene into hidden state", 15, DIM, False),
    ("  Query in real-time for RGB + depth", 15, DIM, False),
    ("  Back-project into colored point clouds", 15, DIM, False),
    ("", 6, DIM, False),
    ("Bidirectional AND streaming modes", 16, TEXT, False),
    ("  Bidirectional = more accurate (sees everything)", 15, DIM, False),
    ("  Streaming = causal, process sequentially", 15, DIM, False),
])

takeaway_bar(s, "Linear-time 3D reconstruction matching quadratic quality \u2014 test-time training replaces global attention", C_ZIPMAP)
slide_num(s, next_n())


# --- ZipMap 2/4: Where it fails + Edge/Success cases ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "ZipMap", "Where It Fails  \u00b7  Edge Cases & Success Cases", C_ZIPMAP)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.8), Inches(5.0), [
    ("Where it fails", 22, ACCENT, True),
    ("", 6, DIM, False),
    ("Streaming mode less accurate than bidirectional", 16, TEXT, False),
    ("  Image 1 can't benefit from image 50", 15, DIM, False),
    ("  (causal: each image does one gradient step)", 15, DIM, False),
    ("", 6, DIM, False),
    ("No explicit human modeling", 16, TEXT, False),
    ("  Reconstructs scene geometry, not body meshes", 15, DIM, False),
    ("  Needs separate body tracker on top", 15, DIM, False),
    ("", 6, DIM, False),
    ("Requires DINOv2 features (heavyweight encoder)", 16, TEXT, False),
    ("", 6, DIM, False),
    ("Trained on 64 H100 GPUs in three stages", 16, TEXT, False),
    ("  Not easy to retrain or fine-tune", 15, DIM, False),
    ("", 6, DIM, False),
    ("Removing reference view degrades quality", 16, TEXT, False),
    ("  (shown in ablation studies)", 15, DIM, False),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(5.0), [
    ("Success cases", 20, C_ZIPMAP, True),
    ("", 6, DIM, False),
    ("Long video sequences (700+ frames)", 16, TEXT, False),
    ("  Where quadratic methods become infeasible", 15, DIM, False),
    ("Large-scale structure-from-motion", 16, TEXT, False),
    ("Dense reconstruction with camera estimation", 16, TEXT, False),
    ("Real-time novel viewpoint querying", 16, TEXT, False),
    ("", 10, DIM, False),
    ("Edge cases / What makes it fail", 20, ACCENT, True),
    ("", 6, DIM, False),
    ("Fixed global TTT learning rate", 16, TEXT, False),
    ("  \u2192 dynamic per-token rate significantly better", 15, ACCENT, False),
    ("  (ablation: fixed rate = worse reconstruction)", 15, DIM, False),
    ("", 6, DIM, False),
    ("Prior linear methods (CUT3R, TTT3R)", 16, TEXT, False),
    ("  reconstruct frames sequentially", 15, DIM, False),
    ("  \u2192 lower GPU utilization at inference", 15, DIM, False),
    ("  ZipMap processes in parallel \u2192 3\u00d7 faster", 15, C_ZIPMAP, False),
])

slide_num(s, next_n())


# --- ZipMap 3/4: Main Components ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "ZipMap", "Main Components", C_ZIPMAP)

# Left: backbone
arch_box(s, Inches(0.5), Inches(1.3), Inches(3.8), Inches(1.0),
         "Input Tokenization",
         "DINOv2 encoder \u2192 2D spatial feature maps\n"
         "Camera params \u2192 ray maps (9-dim: origin, dir, ro\u00d7rd)")

arch_box(s, Inches(0.5), Inches(2.6), Inches(3.8), Inches(2.0),
         "Feature Backbone (24 blocks)",
         "Each block:\n"
         "  Local Window Attention\n"
         "    self-attention + rotary pos encoding\n"
         "    spatial relationships within each view\n"
         "  Global Large-Chunk TTT Layer\n"
         "    updates nonlinear fast-weight function\n"
         "    over all input image tokens")

arch_box(s, Inches(0.5), Inches(4.9), Inches(3.8), Inches(1.4),
         "Prediction Heads",
         "Camera: 4D quaternion + 3D trans + 2 intrinsics\n"
         "Point: (x,y,z) per pixel in camera space\n"
         "Depth: distance + confidence score\n"
         "Query: novel viewpoint synthesis")

# Right: TTT details + training
bullets(s, Inches(5.0), Inches(1.3), Inches(7.5), Inches(5.5), [
    ("Core: TTT Block", 20, C_ZIPMAP, True),
    ("", 6, DIM, False),
    ("In-context-adapted fast-weight function", 16, TEXT, False),
    ("  fw(x) = W\u2082(SiLU(W\u2081x) \u2299 (W\u2083x))", 15, TEXT, False),
    ("", 6, DIM, False),
    ("Each token \u2192 key + value", 15, TEXT, False),
    ("Compute gradient of loss across all tokens", 15, TEXT, False),
    ("  from all input images", 14, DIM, False),
    ("MLP accumulates knowledge over time", 15, TEXT, False),
    ("", 8, DIM, False),
    ("Bidirectional: all images processed at once", 15, TEXT, False),
    ("  image 50 can inform image 1 (more accurate)", 14, DIM, False),
    ("Streaming: one gradient step per new image", 15, TEXT, False),
    ("  causal, image 1 can't benefit from image 50", 14, DIM, False),
    ("", 10, DIM, False),
    ("Training", 18, C_ZIPMAP, True),
    ("", 6, DIM, False),
    ("64 H100 GPUs, three training stages", 15, TEXT, False),
    ("Losses: point, depth, camera, smooth, query", 15, TEXT, False),
    ("Dynamic per-token learning rate (from ablation)", 15, TEXT, False),
])

slide_num(s, next_n())


# --- ZipMap 4/4: How can we use this ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "ZipMap", "How Can We Use This", C_ZIPMAP)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.8), Inches(5.0), [
    ("Scene backbone for physics-aware pipeline", 22, C_ZIPMAP, True),
    ("", 6, DIM, False),
    ("Dense geometry for contact surfaces", 16, TEXT, False),
    ("  Ground plane, obstacles, terrain", 15, DIM, False),
    ("", 6, DIM, False),
    ("Camera poses for world-grounding", 16, TEXT, False),
    ("  Feed to GVHMR or other body tracker", 15, DIM, False),
    ("", 6, DIM, False),
    ("Real-time querying for novel views", 16, TEXT, False),
    ("  ~100 FPS implicit scene representation", 15, DIM, False),
    ("", 10, DIM, False),
    ("Implicit representation enables:", 20, C_ZIPMAP, True),
    ("", 6, DIM, False),
    ("Query ground plane geometry under feet", 16, TEXT, False),
    ("Build signed distance field for penetration", 16, TEXT, False),
    ("Back-project into colored point clouds", 16, TEXT, False),
    ("Extend to streaming reconstruction", 16, TEXT, False),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(5.0), [
    ("ZipMap vs Depth Anything 3", 20, C_ZIPMAP, True),
    ("", 6, DIM, False),
    ("ZipMap:", 16, TEXT, True),
    ("  Full 3D reconstruction + implicit scene", 15, TEXT, False),
    ("  Heavier compute (but still linear-time)", 15, DIM, False),
    ("  Queryable scene representation", 15, TEXT, False),
    ("  Better for dense contact geometry", 15, TEXT, False),
    ("", 6, DIM, False),
    ("DA3:", 16, TEXT, True),
    ("  Depth + camera poses, lighter weight", 15, TEXT, False),
    ("  Streaming native, 78 FPS", 15, TEXT, False),
    ("  Simpler output (no implicit rep)", 15, TEXT, False),
    ("", 10, DIM, False),
    ("Recommendation:", 18, ACCENT, True),
    ("  Use ZipMap when dense scene geometry", 15, TEXT, False),
    ("  matters (contact, penetration constraints)", 15, DIM, False),
    ("  Use DA3 for speed / lightweight deployment", 15, TEXT, False),
])

takeaway_bar(s, "Scene reconstruction backbone \u2014 dense contact geometry via queryable implicit representation", C_ZIPMAP)
slide_num(s, next_n())


# ╔══════════════════════════════════════════════════════════════════╗
# ║  SAM-Body4D — 4 slides                                         ║
# ╚══════════════════════════════════════════════════════════════════╝

# --- SAM-Body4D 1/4: How it works + Why good ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "SAM-Body4D", "How It Works  \u00b7  Why Good", C_SAM4D)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.8), Inches(5.0), [
    ("How it works", 22, C_SAM4D, True),
    ("", 6, DIM, False),
    ("1. Track & segment target pixels with promptable", 16, TEXT, False),
    ("   video segmentation \u2192 identity-consistent masklets", 16, TEXT, False),
    ("", 6, DIM, False),
    ("2. Occlusion-aware refiner recovers missing/corrupted", 16, TEXT, False),
    ("   regions caused by occlusions", 16, TEXT, False),
    ("   Prevents hallucinated predictions", 15, DIM, False),
    ("", 6, DIM, False),
    ("3. Guide body mesh estimator with refined masklets", 16, TEXT, False),
    ("   Temporal coherence from video segmentation transfers", 15, DIM, False),
    ("   directly to reconstructed 4D human meshes", 15, DIM, False),
    ("", 8, DIM, False),
    ("4D mesh = 3D mesh + time", 15, TEXT, True),
    ("Body + hands optimized separately, then fused", 15, TEXT, False),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(5.0), [
    ("Why good", 22, C_SAM4D, True),
    ("", 6, DIM, False),
    ("Inherent human continuity in videos", 16, TEXT, False),
    ("  \u2192 temporally consistent, occlusion-robust", 15, DIM, False),
    ("", 6, DIM, False),
    ("Decoupled skeleton/shape representation:", 16, TEXT, True),
    ("  Standard SMPL: shape affects joint positions", 15, TEXT, False),
    ("  This: predict skeleton + shape separately", 15, TEXT, False),
    ("  Skeleton = easier to estimate accurately", 15, DIM, False),
    ("  Shape varies across people but not within video", 15, DIM, False),
    ("  Network can specialize on each", 15, DIM, False),
    ("", 6, DIM, False),
    ("Scalable data engine", 16, TEXT, False),
    ("  Augmented + generated + multi-view data", 15, DIM, False),
    ("", 6, DIM, False),
    ("No optimization-based objectives needed", 16, TEXT, False),
    ("  (other methods demand large annotated video data", 15, DIM, False),
    ("  and carefully crafted objectives)", 15, DIM, False),
])

takeaway_bar(s, "Temporal consistency via video segmentation \u2014 occlusion-robust without optimization-based objectives", C_SAM4D)
slide_num(s, next_n())


# --- SAM-Body4D 2/4: Where it fails + Edge/Success cases ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "SAM-Body4D", "Where It Fails  \u00b7  Edge Cases & Success Cases", C_SAM4D)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.8), Inches(5.0), [
    ("Where it fails", 22, ACCENT, True),
    ("", 6, DIM, False),
    ("Diffusion inpainting can hallucinate:", 16, TEXT, True),
    ("  If occluder covers most of the body,", 15, TEXT, False),
    ("  inpainting must \"guess\" body configuration", 15, DIM, False),
    ("  \u2192 hallucinated poses, especially limbs", 15, ACCENT, False),
    ("", 6, DIM, False),
    ("Segmentation errors cascade:", 16, TEXT, True),
    ("  Bad masklet \u2192 bad occlusion detection", 15, TEXT, False),
    ("  \u2192 bad inpainting \u2192 bad mesh", 15, ACCENT, False),
    ("  Error propagates through entire pipeline", 15, DIM, False),
    ("", 6, DIM, False),
    ("No physics constraints:", 16, TEXT, True),
    ("  Floating, ground penetration still possible", 15, TEXT, False),
    ("  Temporal consistency \u2260 physical plausibility", 15, DIM, False),
    ("", 6, DIM, False),
    ("Depends on quality of initial prompt", 16, TEXT, False),
    ("  (who to track in the video)", 15, DIM, False),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(5.0), [
    ("Success cases", 20, C_SAM4D, True),
    ("", 6, DIM, False),
    ("Partial occlusion (person behind object)", 16, TEXT, False),
    ("  Recovers visible parts + inpaints missing", 15, DIM, False),
    ("Consistent identity tracking across video", 16, TEXT, False),
    ("  Same person keeps same mesh params", 15, DIM, False),
    ("Full body: hands + face + body together", 16, TEXT, False),
    ("", 10, DIM, False),
    ("Edge cases / What makes it fail", 20, ACCENT, True),
    ("", 6, DIM, False),
    ("Full-body occlusion (person fully hidden):", 16, TEXT, True),
    ("  Masklet generator loses track entirely", 15, ACCENT, False),
    ("  Must re-detect when person reappears", 15, DIM, False),
    ("", 6, DIM, False),
    ("Multi-person close interaction:", 16, TEXT, True),
    ("  Masklets can merge/swap between people", 15, ACCENT, False),
    ("  Identity consistency breaks", 15, DIM, False),
    ("", 6, DIM, False),
    ("Fast motion + motion blur:", 16, TEXT, True),
    ("  Segmentation quality degrades", 15, ACCENT, False),
])

slide_num(s, next_n())


# --- SAM-Body4D 3/4: Main Components ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "SAM-Body4D", "Main Components", C_SAM4D)

# Three-stage pipeline boxes
arch_box(s, Inches(0.5), Inches(1.3), Inches(3.8), Inches(1.8),
         "1. Masklet Generator",
         "Based on promptable video segmentation\n\n"
         "Propagate: spatial-temporal correspondences\n"
         "  between past predictions + current frame\n"
         "  \u2192 reliable mask label transfer across time\n\n"
         "Detect: semantic associations between\n"
         "  prompt and objects in current frame")

arch_box(s, Inches(4.7), Inches(1.3), Inches(4.0), Inches(1.8),
         "2. Occlusion-Aware Refiner",
         "Diffusion-based visual appearance synthesis\n\n"
         "a. Predict full body mask (even occluded)\n"
         "b. Compare with actual visible mask\n"
         "c. Mismatch \u2192 occlusion detected\n"
         "d. Group flagged frames into temporal chunks\n"
         "e. Inpaint actual RGB pixels behind occluder")

arch_box(s, Inches(9.1), Inches(1.3), Inches(3.7), Inches(1.8),
         "3. Mask-Guided HMR",
         "Per-frame mesh parameter prediction\n\n"
         "Temporal coherence from masklets\n"
         "  naturally propagated to meshes\n\n"
         "Body + hand optimized separately\n"
         "  (different optimization strategies)\n"
         "  then fused together")

# Bottom: key definitions
bullets(s, Inches(0.6), Inches(3.5), Inches(5.8), Inches(3.0), [
    ("Key concepts", 18, C_SAM4D, True),
    ("", 6, DIM, False),
    ("Masklet: small per-object segmentation mask", 15, TEXT, False),
    ("  tracked across all video frames", 14, DIM, False),
    ("", 6, DIM, False),
    ("Momentum Human Rig (MHR):", 15, TEXT, True),
    ("  Decoupled skeleton + shape representation", 14, TEXT, False),
    ("  Performs better than coupled SMPL/SMPL-X", 14, DIM, False),
    ("", 6, DIM, False),
    ("Video Object Segmentation:", 15, TEXT, True),
    ("  Traditional: memory-based paradigm", 14, TEXT, False),
    ("  This: promptable + occlusion-aware refinement", 14, TEXT, False),
])

bullets(s, Inches(7.0), Inches(3.5), Inches(5.5), Inches(3.0), [
    ("Prior HMR approaches (what this replaces)", 18, C_SAM4D, True),
    ("", 6, DIM, False),
    ("Regression-based:", 15, TEXT, True),
    ("  Regress body model params from image features", 14, TEXT, False),
    ("  No occlusion handling, no temporal consistency", 14, DIM, False),
    ("", 6, DIM, False),
    ("Token-based:", 15, TEXT, True),
    ("  Joints/vertices as learnable tokens + transformer", 14, TEXT, False),
    ("  Better reasoning but still no occlusion recovery", 14, DIM, False),
    ("", 6, DIM, False),
    ("Temporal smoothness:", 15, TEXT, True),
    ("  GRU/transformer over frame features", 14, TEXT, False),
    ("  Feature-level only, can't recover occluded pixels", 14, DIM, False),
])

slide_num(s, next_n())


# --- SAM-Body4D 4/4: How can we use this ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "SAM-Body4D", "How Can We Use This", C_SAM4D)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.8), Inches(5.0), [
    ("Body backbone for occluded scenarios", 22, C_SAM4D, True),
    ("", 6, DIM, False),
    ("When GVHMR fails (occlusion, multi-person),", 16, TEXT, False),
    ("SAM-Body4D handles it via tracked masklets", 16, TEXT, False),
    ("", 8, DIM, False),
    ("Sports applications:", 20, C_SAM4D, True),
    ("", 6, DIM, False),
    ("Players constantly occlude each other", 16, TEXT, False),
    ("  Soccer: tackles, crowded penalty box", 15, DIM, False),
    ("  Basketball: screens, post play, drives", 15, DIM, False),
    ("", 6, DIM, False),
    ("Internet game footage (not controlled capture)", 16, TEXT, False),
    ("  Single camera, variable quality", 15, DIM, False),
    ("  Occlusion is the norm, not exception", 15, DIM, False),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(5.0), [
    ("ASICS partnership", 20, C_SAM4D, True),
    ("", 6, DIM, False),
    ("Running shoes + soccer shoes", 16, TEXT, False),
    ("  How can soccer shoes reduce injuries?", 15, DIM, False),
    ("", 6, DIM, False),
    ("Analyze athlete interactions from game video", 16, TEXT, False),
    ("  Person-to-person contact \u2192 ACL injury risk", 15, DIM, False),
    ("  When does tracking succeed vs fail?", 15, DIM, False),
    ("", 10, DIM, False),
    ("Combine with our physics layer:", 20, C_SAM4D, True),
    ("", 6, DIM, False),
    ("SAM-Body4D \u2192 consistent body meshes", 16, TEXT, False),
    ("+ ZipMap/DA3 \u2192 scene geometry", 16, TEXT, False),
    ("+ physics refinement \u2192 contact-aware output", 16, TEXT, False),
    ("", 6, DIM, False),
    ("Single GPU inference", 16, DIM, False),
])

takeaway_bar(s, "Occlusion-robust body tracking for sports footage \u2014 critical for ASICS injury analysis pipeline", C_SAM4D)
slide_num(s, next_n())


# ╔══════════════════════════════════════════════════════════════════╗
# ║  PhysHMR — 4 slides                                            ║
# ╚══════════════════════════════════════════════════════════════════╝

# --- PhysHMR 1/4: How it works + Why good ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "PhysHMR", "How It Works  \u00b7  Why Good", C_PHYS)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.8), Inches(5.0), [
    ("How it works", 22, C_PHYS, True),
    ("", 6, DIM, False),
    ("Visual-to-action policy that directly predicts", 16, TEXT, False),
    ("control signals from visual input", 16, TEXT, False),
    ("", 6, DIM, False),
    ("1. Pretrained visual encoder extracts per-frame features", 15, TEXT, False),
    ("2. Pixel-as-ray: lift 2D keypoints into 3D rays", 15, TEXT, False),
    ("   using camera intrinsics K (back-projection)", 14, DIM, False),
    ("   \u2192 soft global pose reference, no hard targets", 14, DIM, False),
    ("3. Multi-task MLP regresses future root orientation", 15, TEXT, False),
    ("4. RL policy in physics simulator produces joint torques", 15, TEXT, False),
    ("", 6, DIM, False),
    ("Distillation from mocap-trained expert:", 16, TEXT, True),
    ("  Pre-train imitation policy on motion capture data", 15, TEXT, False),
    ("  Distill into visual-to-action policy", 15, TEXT, False),
    ("  \u2192 accelerates convergence, stabilizes learning", 15, DIM, False),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(5.0), [
    ("Why good", 22, C_PHYS, True),
    ("", 6, DIM, False),
    ("Proves physics must be integrated, not bolted on:", 16, TEXT, True),
    ("", 6, DIM, False),
    ("Foot sliding comparison:", 16, C_PHYS, True),
    ("  GVHMR alone: 5.65 mm", 15, TEXT, False),
    ("  GVHMR + RL post-correction: 12.71 mm", 15, ACCENT, True),
    ("  PhysHMR end-to-end: 4.60 mm", 15, C_PHYS, True),
    ("", 6, DIM, False),
    ("Post-correction makes it 2.2\u00d7 WORSE", 16, ACCENT, True),
    ("", 8, DIM, False),
    ("Why post-correction fails:", 16, TEXT, True),
    ("  Vision picks one interpretation of ambiguous input", 15, TEXT, False),
    ("  Physics module can't access full visual context", 15, DIM, False),
    ("  \u2192 suboptimal corrections, inconsistent w/ evidence", 15, DIM, False),
    ("", 6, DIM, False),
    ("Distillation makes RL practical", 16, TEXT, False),
    ("  Prior RL methods: low sample efficiency", 15, DIM, False),
])

takeaway_bar(s, "Physics integrated end-to-end beats two-stage by 2.2\u00d7 on foot sliding \u2014 post-correction backfires", C_PHYS)
slide_num(s, next_n())


# --- PhysHMR 2/4: Where it fails + Edge/Success cases ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "PhysHMR", "Where It Fails  \u00b7  Edge Cases & Success Cases", C_PHYS)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.8), Inches(5.0), [
    ("Where it fails", 22, ACCENT, True),
    ("", 6, DIM, False),
    ("Single person only", 16, TEXT, False),
    ("  No multi-person interaction handling", 15, DIM, False),
    ("", 6, DIM, False),
    ("Requires physics simulator in the loop", 16, TEXT, False),
    ("  Slower than pure feed-forward methods", 15, DIM, False),
    ("  MDP simulation adds latency", 15, DIM, False),
    ("", 6, DIM, False),
    ("Still depends on GVHMR encoder quality", 16, TEXT, False),
    ("  Bad visual features \u2192 bad policy input", 15, DIM, False),
    ("", 6, DIM, False),
    ("No scene-aware contact", 16, TEXT, False),
    ("  Flat ground assumption only", 15, DIM, False),
    ("  No terrain, no obstacles, no objects", 15, DIM, False),
    ("", 6, DIM, False),
    ("Noisy 3D root prediction from monocular video", 16, TEXT, False),
    ("  Local pose says forward, root pulls backward", 15, DIM, False),
    ("  \u2192 jitter (pixel-as-ray mitigates this)", 15, DIM, False),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(5.0), [
    ("Success cases", 20, C_PHYS, True),
    ("", 6, DIM, False),
    ("Walking, running, general locomotion", 16, TEXT, False),
    ("  Where ground contact matters most", 15, DIM, False),
    ("Single-person sports movements", 16, TEXT, False),
    ("  Clear visual features, one subject", 15, DIM, False),
    ("Long sequences with consistent physics", 16, TEXT, False),
    ("", 10, DIM, False),
    ("Edge cases / What makes it fail", 20, ACCENT, True),
    ("", 6, DIM, False),
    ("Monocular depth ambiguity:", 16, TEXT, True),
    ("  Multiple plausible motions explain same 2D obs", 15, TEXT, False),
    ("  Two-stage picks one wrong \u2192 physics can't fix", 15, ACCENT, False),
    ("  End-to-end jointly reasons over both", 15, C_PHYS, False),
    ("", 6, DIM, False),
    ("Root jitter (noisy 3D prediction):", 16, TEXT, True),
    ("  Fixed by pixel-as-ray: soft reference", 15, TEXT, False),
    ("  not hard positional target", 15, DIM, False),
    ("", 6, DIM, False),
    ("Extreme / acrobatic motions:", 16, TEXT, True),
    ("  RL policy may not have seen in training", 15, ACCENT, False),
])

slide_num(s, next_n())


# --- PhysHMR 3/4: Main Components ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "PhysHMR", "Main Components", C_PHYS)

# Pipeline boxes
arch_box(s, Inches(0.3), Inches(1.3), Inches(3.2), Inches(1.5),
         "Video Encoder (from GVHMR)",
         "Per-frame preprocessing:\n"
         "  Image features\n"
         "  Bounding boxes\n"
         "  2D keypoints\n"
         "  Relative camera rotations\n"
         "Aggregated across frames by encoder")

arch_box(s, Inches(3.8), Inches(1.3), Inches(3.2), Inches(1.5),
         "Pixel-As-Ray Strategy",
         "Given keypoint (u,v) + intrinsics K:\n"
         "  Back-project to 3D ray in camera coords\n\n"
         "Encodes global guidance without\n"
         "  enforcing explicit positional targets\n"
         "\u2192 soft spatial grounding")

arch_box(s, Inches(7.3), Inches(1.3), Inches(2.5), Inches(1.5),
         "Multi-task MLP Head",
         "Regresses future root\n"
         "orientation from visual\n"
         "features\n\n"
         "Forward-looking estimate\n"
         "in camera coord system")

arch_box(s, Inches(10.1), Inches(1.3), Inches(2.5), Inches(1.5),
         "Local Motion Features",
         "SMPL joint rotations\n"
         "relative to parent joints\n\n"
         "Captures relative joint\n"
         "articulation")

# Bottom: RL + distillation details
arch_box(s, Inches(0.3), Inches(3.3), Inches(6.0), Inches(2.0),
         "Markov Decision Process (RL)",
         "M = <S, A, T, R, \u03b3>\n\n"
         "State: simulation pose + velocity\n"
         "Action: joint torques (control signals)\n"
         "Transition: physics engine steps simulation\n"
         "Reward: match reference trajectory\n"
         "Reference: local pose + global translation/rotation\n"
         "  extracted from visual encoder output")

arch_box(s, Inches(6.6), Inches(3.3), Inches(6.0), Inches(2.0),
         "Distillation from MoCap Expert",
         "Problem: RL from scratch = low sample efficiency\n\n"
         "Solution:\n"
         "  1. Train imitation policy on motion capture data\n"
         "     (learns physically plausible control)\n"
         "  2. Distill knowledge into visual-to-action policy\n"
         "     (transfer: mocap domain \u2192 video domain)\n"
         "\u2192 faster convergence, more stable learning")

bullets(s, Inches(0.6), Inches(5.7), Inches(12), Inches(0.8), [
    ("Built on pretrained GVHMR \u2014 uses its encoder as visual frontend, adds physics-aware policy on top", 15, C_PHYS, True),
])

slide_num(s, next_n())


# --- PhysHMR 4/4: How can we use this ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "PhysHMR", "How Can We Use This", C_PHYS)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.8), Inches(5.0), [
    ("Architecture reference", 22, C_PHYS, True),
    ("", 6, DIM, False),
    ("End-to-end physics integration pattern:", 16, TEXT, False),
    ("  Visual encoder \u2192 physics policy \u2192 motion", 15, TEXT, False),
    ("  (not: visual encoder \u2192 motion \u2192 physics fix)", 15, ACCENT, False),
    ("", 8, DIM, False),
    ("Pixel-as-ray strategy is reusable:", 16, TEXT, True),
    ("  Elegant solution to noisy 3D root prediction", 15, TEXT, False),
    ("  Soft constraint vs hard positional target", 15, DIM, False),
    ("  Works with any camera intrinsics", 15, DIM, False),
    ("", 8, DIM, False),
    ("Distillation approach is reusable:", 16, TEXT, True),
    ("  Train expert on clean mocap data", 15, TEXT, False),
    ("  Distill into video-conditioned policy", 15, TEXT, False),
    ("  Avoids RL sample inefficiency problem", 15, DIM, False),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(5.0), [
    ("Critical design lesson", 22, ACCENT, True),
    ("", 6, DIM, False),
    ("DO NOT bolt physics on as post-processing", 16, ACCENT, True),
    ("", 6, DIM, False),
    ("Evidence:", 16, TEXT, True),
    ("  GVHMR alone: 5.65 mm foot sliding", 15, TEXT, False),
    ("  + RL post-correction: 12.71 mm (2.2\u00d7 worse)", 15, ACCENT, False),
    ("  PhysHMR end-to-end: 4.60 mm (best)", 15, C_PHYS, False),
    ("", 8, DIM, False),
    ("Implication for our pipeline:", 16, TEXT, True),
    ("  Physics must see visual evidence", 15, TEXT, False),
    ("  not just kinematic output", 15, DIM, False),
    ("", 8, DIM, False),
    ("What PhysHMR doesn't give us:", 16, TEXT, True),
    ("  Multi-person support", 15, TEXT, False),
    ("  Scene-aware contact (terrain, objects)", 15, TEXT, False),
    ("  \u2192 these are our contributions", 15, DIM, False),
])

takeaway_bar(s, "Validates end-to-end physics design. Pixel-as-ray + distillation are reusable. Never post-process.", C_PHYS)
slide_num(s, next_n())


# ╔══════════════════════════════════════════════════════════════════╗
# ║  MultiPhys — 4 slides                                          ║
# ╚══════════════════════════════════════════════════════════════════╝

# --- MultiPhys 1/4: How it works + Why good ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "MultiPhys", "How It Works  \u00b7  Why Good", C_MULTI)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.8), Inches(5.0), [
    ("How it works", 22, C_MULTI, True),
    ("", 6, DIM, False),
    ("1. Start with kinematic poses (from any body tracker)", 16, TEXT, False),
    ("   Visually good but physically implausible", 15, DIM, False),
    ("", 6, DIM, False),
    ("2. Create humanoid agents in physics engine", 16, TEXT, False),
    ("   Each person \u2192 separate articulated body", 15, DIM, False),
    ("", 6, DIM, False),
    ("3. Universal Humanoid Controller (UHC):", 16, TEXT, False),
    ("   Trained neural net that takes:", 15, DIM, False),
    ("     current state (pose + velocity)", 14, DIM, False),
    ("     target kinematic pose", 14, DIM, False),
    ("     body shape parameters", 14, DIM, False),
    ("   Outputs: joint torques \u2192 drives body toward target", 15, DIM, False),
    ("", 6, DIM, False),
    ("4. Physics simulation resolves collisions + contacts", 16, TEXT, False),
    ("5. Loop-N: repeat N times per frame for extreme poses", 16, TEXT, False),
    ("   (gymnastics, dancing, fighting)", 15, DIM, False),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(5.0), [
    ("Why good", 22, C_MULTI, True),
    ("", 6, DIM, False),
    ("7\u00d7 less body-ground penetration", 16, TEXT, False),
    ("", 6, DIM, False),
    ("First method for multi-person physics correction", 16, ACCENT, True),
    ("  Each person has independent controller", 15, DIM, False),
    ("  but they share the physics world", 15, DIM, False),
    ("  \u2192 collisions between people resolved automatically", 15, DIM, False),
    ("", 6, DIM, False),
    ("Agnostic to input tracker", 16, TEXT, False),
    ("  Plug in any body tracker (SLAHMR, GVHMR, etc)", 15, DIM, False),
    ("  Works with regression or autoregressive input", 15, DIM, False),
    ("", 6, DIM, False),
    ("SDF penetration metric:", 16, TEXT, True),
    ("  Not just whether vertices penetrate,", 15, TEXT, False),
    ("  but how deep they go", 15, DIM, False),
    ("  Sum = scalar capturing count AND depth", 15, DIM, False),
    ("  (better than counting vertices alone)", 15, DIM, False),
])

takeaway_bar(s, "First multi-person physics correction \u2014 7\u00d7 less penetration, agnostic to input tracker", C_MULTI)
slide_num(s, next_n())


# --- MultiPhys 2/4: Where it fails + Edge/Success cases ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "MultiPhys", "Where It Fails  \u00b7  Edge Cases & Success Cases", C_MULTI)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.8), Inches(5.0), [
    ("Where it fails", 22, ACCENT, True),
    ("", 6, DIM, False),
    ("RL policy creates its own artifacts:", 16, TEXT, True),
    ("  Arm flailing for balance recovery", 15, ACCENT, False),
    ("  Unnatural compensatory movements", 15, ACCENT, False),
    ("  Policy optimizes physics, not visual realism", 15, DIM, False),
    ("", 6, DIM, False),
    ("Post-correction approach fundamentally limited:", 16, TEXT, True),
    ("  PhysHMR showed this makes foot sliding 2.2\u00d7 worse", 15, ACCENT, False),
    ("  Physics module can't access visual context", 15, DIM, False),
    ("", 6, DIM, False),
    ("Depends entirely on input tracker quality:", 16, TEXT, True),
    ("  SLAHMR provides kinematic input", 15, TEXT, False),
    ("  SLAHMR errors \u2192 MultiPhys can't fully correct", 15, DIM, False),
    ("", 6, DIM, False),
    ("No scene geometry:", 16, TEXT, True),
    ("  Flat ground plane only", 15, TEXT, False),
    ("  No terrain, stairs, uneven surfaces", 15, DIM, False),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(5.0), [
    ("Success cases", 20, C_MULTI, True),
    ("", 6, DIM, False),
    ("Multi-person scenes with close interaction", 16, TEXT, False),
    ("  Body-body penetration resolved by physics engine", 15, DIM, False),
    ("Walking/standing on flat ground", 16, TEXT, False),
    ("  Ground contact resolved well", 15, DIM, False),
    ("Moderate motion (no extreme gymnastics)", 16, TEXT, False),
    ("", 10, DIM, False),
    ("Edge cases / What makes it fail", 20, ACCENT, True),
    ("", 6, DIM, False),
    ("Extreme poses (gymnastics, dancing, fighting):", 16, TEXT, True),
    ("  Need Loop-N fix (repeat simulation steps)", 15, TEXT, False),
    ("  Without it: controller can't reach target pose", 15, ACCENT, False),
    ("  With it: slower but converges", 15, DIM, False),
    ("", 6, DIM, False),
    ("Input tracker sliding/floating:", 16, TEXT, True),
    ("  If SLAHMR says person is floating,", 15, TEXT, False),
    ("  physics corrects but may overshoot", 15, ACCENT, False),
    ("  \u2192 ground slam artifacts", 15, DIM, False),
])

slide_num(s, next_n())


# --- MultiPhys 3/4: Main Components ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "MultiPhys", "Main Components", C_MULTI)

# Pipeline
arch_box(s, Inches(0.3), Inches(1.3), Inches(2.8), Inches(1.3),
         "1. Kinematic Input",
         "Any body tracker output\n"
         "(tested with SLAHMR:\n"
         " Simultaneous Localization\n"
         " + Human Mesh Recovery)")

arch_box(s, Inches(3.4), Inches(1.3), Inches(2.8), Inches(1.3),
         "2. Humanoid Agents",
         "Each person becomes an\n"
         "articulated rigid body\n"
         "in physics engine\n"
         "Independent controllers")

arch_box(s, Inches(6.5), Inches(1.3), Inches(3.2), Inches(1.3),
         "3. Universal Humanoid\n   Controller (UHC)",
         "Neural net policy:\n"
         "  Input: state + target + shape\n"
         "  Output: joint torques")

arch_box(s, Inches(10.0), Inches(1.3), Inches(2.8), Inches(1.3),
         "4. Physics Engine",
         "MuJoCo simulation\n"
         "Resolve collisions\n"
         "Ground contact\n"
         "Body-body interaction")

# Loop-N
arch_box(s, Inches(0.3), Inches(3.0), Inches(12.5), Inches(0.7),
         "5. Loop-N Fix",
         "For extreme poses: loop N times on same target pose instead of stepping once. Ensures convergence on challenging motions.")

# Bottom details
bullets(s, Inches(0.6), Inches(4.1), Inches(5.5), Inches(2.5), [
    ("UHC Controller Details", 18, C_MULTI, True),
    ("", 6, DIM, False),
    ("Input:", 15, TEXT, True),
    ("  Current simulation state (pose + velocity)", 14, TEXT, False),
    ("  Target kinematic pose from tracker", 14, TEXT, False),
    ("  Body shape parameters", 14, TEXT, False),
    ("", 6, DIM, False),
    ("Output:", 15, TEXT, True),
    ("  Joint torques driving simulated body", 14, TEXT, False),
    ("  toward target while obeying physics", 14, TEXT, False),
    ("", 6, DIM, False),
    ("Each person: independent controller", 15, TEXT, False),
    ("  Shared physics world for interactions", 14, DIM, False),
])

bullets(s, Inches(7.0), Inches(4.1), Inches(5.5), Inches(2.5), [
    ("Input Tracker: SLAHMR", 18, C_MULTI, True),
    ("", 6, DIM, False),
    ("Simultaneous Localization + HMR", 15, TEXT, False),
    ("  Camera trajectory + human 3D poses", 14, DIM, False),
    ("  in shared world coordinates", 14, DIM, False),
    ("", 6, DIM, False),
    ("Output is visually good but:", 15, TEXT, True),
    ("  Sliding feet", 14, ACCENT, False),
    ("  Body-body penetration", 14, ACCENT, False),
    ("  Floating / ground penetration", 14, ACCENT, False),
    ("  Not usable in physics simulators", 14, ACCENT, False),
    ("", 6, DIM, False),
    ("MultiPhys fixes all of these", 15, C_MULTI, True),
])

slide_num(s, next_n())


# --- MultiPhys 4/4: How can we use this ---
s = prs.slides.add_slide(blank); _bg(s)
section_header(s, "MultiPhys", "How Can We Use This", C_MULTI)

bullets(s, Inches(0.6), Inches(1.3), Inches(5.8), Inches(5.0), [
    ("Physics simulation reference", 22, C_MULTI, True),
    ("", 6, DIM, False),
    ("UHC controller design is reusable:", 16, TEXT, True),
    ("  State + target \u2192 torques pattern", 15, TEXT, False),
    ("  Works with any body tracker input", 15, DIM, False),
    ("", 6, DIM, False),
    ("MuJoCo integration pattern:", 16, TEXT, True),
    ("  How to set up humanoid agents", 15, TEXT, False),
    ("  How to handle collisions between people", 15, TEXT, False),
    ("  How to step simulation per frame", 15, TEXT, False),
    ("", 6, DIM, False),
    ("SDF penetration metric:", 16, TEXT, True),
    ("  Use for our evaluation pipeline", 15, TEXT, False),
    ("  Better than vertex counting alone", 15, DIM, False),
    ("", 6, DIM, False),
    ("Loop-N strategy for hard poses:", 16, TEXT, True),
    ("  Repeat simulation steps for convergence", 15, TEXT, False),
])

bullets(s, Inches(7.0), Inches(1.3), Inches(5.5), Inches(5.0), [
    ("ASICS application", 22, C_MULTI, True),
    ("", 6, DIM, False),
    ("Multi-person sports footage:", 16, TEXT, True),
    ("  Basketball: screens, post play, drives", 15, TEXT, False),
    ("  Soccer: tackles, crowded penalty box", 15, TEXT, False),
    ("  Person-to-person contact analysis", 15, TEXT, False),
    ("", 6, DIM, False),
    ("ACL injury analysis:", 16, TEXT, True),
    ("  How athletes interact during high-risk moments", 15, TEXT, False),
    ("  Physics-plausible contact forces", 15, TEXT, False),
    ("", 10, DIM, False),
    ("Caveat from PhysHMR:", 20, ACCENT, True),
    ("", 6, DIM, False),
    ("Post-correction approach has limits", 16, TEXT, False),
    ("  RL artifacts (arm flailing)", 15, ACCENT, False),
    ("  2.2\u00d7 worse foot sliding in some cases", 15, ACCENT, False),
    ("  Consider end-to-end integration instead", 15, DIM, False),
])

takeaway_bar(s, "Multi-person physics + SDF metrics for our pipeline. But prefer end-to-end over post-correction.", C_MULTI)
slide_num(s, next_n())


# ════════════════════════════════════════════════════════════════════
#  SUMMARY SLIDE
# ════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank)
s.background.fill.solid()
s.background.fill.fore_color.rgb = TEAL

tx(s, Inches(1.5), Inches(0.6), Inches(10), Inches(0.6),
   "Summary", sz=36, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

bullets(s, Inches(0.8), Inches(1.5), Inches(5.5), Inches(5.5), [
    ("GVHMR", 20, WHITE, True),
    ("  Gravity-anchored body tracking, no drift", 14, WHITE, False),
    ("  Best single-person, 280 ms inference", 14, WHITE, False),
    ("  Fails: single-person only, no physics", 14, WHITE, False),
    ("", 8, WHITE, False),
    ("ZipMap", 20, WHITE, True),
    ("  Linear-time 3D via test-time training", 14, WHITE, False),
    ("  700 frames in <10 s, queryable scene rep", 14, WHITE, False),
    ("  Fails: no human modeling, heavy encoder", 14, WHITE, False),
    ("", 8, WHITE, False),
    ("SAM-Body4D", 20, WHITE, True),
    ("  Temporal consistency + occlusion recovery", 14, WHITE, False),
    ("  Decoupled skeleton/shape, full body", 14, WHITE, False),
    ("  Fails: diffusion hallucination, cascading errors", 14, WHITE, False),
])

bullets(s, Inches(7.0), Inches(1.5), Inches(5.5), Inches(5.5), [
    ("PhysHMR", 20, WHITE, True),
    ("  End-to-end physics + vision", 14, WHITE, False),
    ("  Post-correction makes it 2.2\u00d7 worse", 14, WHITE, False),
    ("  Fails: single-person, no scene awareness", 14, WHITE, False),
    ("", 8, WHITE, False),
    ("MultiPhys", 20, WHITE, True),
    ("  Multi-person physics via simulation", 14, WHITE, False),
    ("  7\u00d7 less penetration, SDF metrics", 14, WHITE, False),
    ("  Fails: RL artifacts, flat ground only", 14, WHITE, False),
    ("", 14, WHITE, False),
    ("Common thread:", 20, WHITE, True),
    ("  Vision proposes, physics refines", 16, WHITE, False),
    ("  Integration beats cascade", 16, WHITE, False),
    ("  Scene geometry is the missing piece", 16, WHITE, False),
])

slide_num(s, next_n())


# ── Save ──
out = "/home/user/Pact3D/Paper_DeepDives.pptx"
prs.save(out)
print(f"Saved {N[0]} slides to {out}")

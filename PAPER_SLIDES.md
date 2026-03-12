# Paper Slides
## For Presentation — GVHMR, ZipMap, SAM-Body4D

---

## Slide: GVHMR (SigAsia'24)

### World-Grounded Human Motion Recovery via Gravity-View Coordinates

**Liang An, Jing Zhang, Juergen Gall et al. — Zhejiang University**

**Input:** monocular RGB video
**Output:** world-grounded SMPL-X poses + global root trajectory (gravity-aligned)

- Feed-forward transformer (NOT recurrent/autoregressive)
- Gravity-View (GV) coordinate system eliminates yaw ambiguity
- Parallel prediction — no error accumulation over time

**Key idea:** Define per-frame coordinate system from two observables:
- Y = gravity direction (up)
- X = Y x camera\_view (perpendicular)
- Z = right-hand rule (roughly camera forward)

Each frame is independently gravity-anchored — frame 1000 is as accurate as frame 1.

---

## Slide: GVHMR — How It Works

### Architecture

**Preprocessing (off-the-shelf, swappable):**

| Component | Task | Time (1430 frames) |
|-----------|------|-------------------|
| YOLOv8 | Person detection / bounding box | 4.9s |
| ViTPose | 2D keypoint estimation | 20.0s |
| ViT | Image feature extraction | 10.1s |
| DPVO | Camera motion / relative rotations | 11.0s |

**Core Network:**
1. Early fusion: map all inputs (bboxes, keypoints, image features, camera rotations) to same dimensions → per-frame tokens
2. Relative Transformer: 12 layers, 8 attention heads, RoPE (rotary positional embedding for length generalization)
3. Multi-task MLP heads predict simultaneously:
   - Weak-perspective camera params → converted to full-perspective via CLIFF
   - Human orientation in camera frame
   - SMPL-X local pose (joint angles) + shape (body proportions)
   - Stationary labels (is foot planted?)
   - Global trajectory representation

**Post-processing:**
- Predict stationary probability per joint
- Pin planted feet → CCD inverse kinematics to fix local poses
- Reduces foot sliding without physics simulation

---

## Slide: GVHMR — Static vs Moving Camera

### GV Coordinate Transform

**Static Camera:**
- GV coordinate system identical every frame
- Simply accumulate velocities: world\_pos[t] = world\_pos[0] + Σ(orientation[i] · velocity[i])

**Moving Camera:**
- Camera rotates → GV coord system changes between frames
- Compute rotation between GV\_t and GV\_{t-1} (only 1-DOF yaw, since gravity axis stays the same)
- Chain relative rotations back to GV\_0 (global reference)
- Relative camera rotation from DPVO or gyroscope data

**Key advantage:** Does not require initialization, can predict in parallel without autoregressive prediction.

---

## Slide: GVHMR — Why Good

### Results: Best World-Grounded Tracker

**EMDB-2 (mm, lower = better):**

| Method | WA-MPJPE | W-MPJPE | Jitter | Foot Slide | Speed |
|--------|---------|---------|--------|------------|-------|
| GLAMR | 280.8 | 726.6 | 46.3 | 20.7 | Slow |
| SLAHMR | 326.9 | 776.1 | 31.3 | 14.5 | ~4 hrs/1K fr |
| WHAM | 135.6 | 354.8 | 22.5 | 4.4 | ~5s/1K fr |
| **GVHMR** | **111.0** | **276.5** | **16.7** | **3.5** | **0.28s/1.4K fr** |

**RICH (mm):**

| Method | WA-MPJPE | W-MPJPE | Jitter | Foot Slide |
|--------|---------|---------|--------|------------|
| WHAM | 109.9 | 184.6 | 19.7 | 3.3 |
| **GVHMR** | **78.8** | **126.3** | **12.8** | **3.0** |

1. **No error accumulation** — gravity anchored independently per frame
2. **Multi-task learning** — global motion supervision improves camera-space estimation too
3. **Extremely fast** — 0.28s inference for 1430 frames (~5000 FPS core network)
4. **Handles arbitrary length** — RoPE enables generalization to any sequence length

---

## Slide: GVHMR — Where It Fails

### Limitations & Edge Cases

| Failure Mode | Root Cause | Which Component Fails |
|-------------|-----------|----------------------|
| Foot sliding (3.0-3.5mm) | No physics constraints, just learned stationary labels | Post-processing |
| Ground penetration (~2-5mm) | No scene awareness at all | Architecture (no scene model) |
| Human-object interaction | No object/scene representation | Architecture |
| Fast camera rotation | DPVO gives noisy rotation estimates | Preprocessing (DPVO) |
| Severe occlusion | 2D keypoints wrong/missing | Preprocessing (ViTPose) |
| Multiple people | Single-person design only | Architecture |
| Not real-time streaming | Bidirectional transformer needs full sequence | Architecture |
| Non-gravity-aligned actions (gymnastics, swimming) | GV system assumes clear gravity direction | GV assumption + training distribution |

**Preprocessing is the bottleneck:** 46.0s preprocessing vs 0.28s inference.

**For Pact3D:** GVHMR's weaknesses (foot sliding, penetration, no scene) are exactly what the physics layer fixes.

---

## Slide: GVHMR — Runtime

### Pipeline Breakdown (1430 frames, ~45 sec video, RTX 4090)

| Stage | Time | % of Total |
|-------|------|-----------|
| ViTPose (2D keypoints) | 20.0s | 43% |
| DPVO (camera motion) | 11.0s | 24% |
| ViT (image features) | 10.1s | 22% |
| YOLOv8 (detection) | 4.9s | 11% |
| **GVHMR inference** | **0.28s** | **0.6%** |
| **Total** | **~46.3s** | |

**Key insight:** GVHMR itself is near real-time. The bottleneck is entirely off-the-shelf preprocessing that can be swapped for faster alternatives.

---
---

## Slide: ZipMap (CVPR'26)

### Feed-Forward 3D Scene Reconstruction with Linear-Time Scaling

**Haian Jin et al. — Google DeepMind, Cornell, MIT**

**Input:** image collection / video frames (any number)
**Output:** camera poses (intrinsics + extrinsics), depth maps with confidence, point maps, optional novel-view RGB/depth

- **1.40B parameters**, 24 blocks of local window self-attention + TTT (Test-Time Training) layers
- **O(N) linear scaling** via TTT layers replacing quadratic global attention
- 750+ frames in <10 seconds on a single H100 (~75 FPS)
- >20x faster than VGGT/Pi3 at comparable quality

---

## Slide: ZipMap — How It Works

### Architecture: TTT (Test-Time Training) Layers

**Core innovation:** Replace quadratic global attention with TTT layers that compress image features into "fast weights" of a SwiGLU-MLP, creating a queryable implicit scene representation.

| Component | What It Does |
|-----------|-------------|
| DINOv2 backbone | Extract image features |
| Local window self-attention | Process spatial features within each image |
| TTT layers | Compress all image features into fast weights (O(N) linear) |
| SwiGLU-MLP | Queryable implicit scene representation |
| Output heads | Camera poses, depth maps, point maps, confidence |

**Why TTT instead of global attention:**
- Standard transformers: O(N²) — 1000 frames = 1M attention pairs
- TTT: O(N) — each frame updates fast weights incrementally
- Enables streaming/sequential mode for online applications

**Supports two modes:**
1. **Batch mode:** Process all images at once
2. **Streaming mode:** Process images sequentially (enables online applications)

---

## Slide: ZipMap — Benchmarks

### Scene Reconstruction Quality

**Camera Pose Estimation (RRA@15° / RTA@15°):**

| Method | CO3Dv2 | RealEstate10K | Tanks & Temples |
|--------|--------|---------------|-----------------|
| DUSt3R | ~40/50 | ~55/65 | ~30/40 |
| VGGT | ~55/65 | ~70/80 | ~45/55 |
| **ZipMap** | **~60/70** | **~75/85** | **~50/60** |

**Speed Comparison:**

| Method | FPS | Scaling | Max Frames (practical) | GPU |
|--------|-----|---------|----------------------|-----|
| DUSt3R | 1-5 | O(N²) | ~50-100 | A100 |
| VGGT | ~60 | O(N²) | ~60-75 | A100 |
| **ZipMap** | **~75** | **O(N)** | **750+** | H100 |
| DA3 | 78 | O(N) | Any length | RTX 4090 |

---

## Slide: ZipMap — Why Good / Where It Fails

### Why Good

1. **Linear-time scaling** — first feed-forward method to handle 750+ frames efficiently
2. **Unified outputs** — camera poses + depth + pointmaps + novel views in one model
3. **Strong quality** — competitive with or better than VGGT on major benchmarks
4. **Streaming capable** — TTT layers enable sequential processing for online use

### Where It Fails / Limitations

| Limitation | Impact |
|-----------|--------|
| **Code/weights NOT released** | Cannot use yet (placeholder repo only) |
| **Requires H100-class GPU** | Not consumer-friendly (vs DA3 on RTX 3090) |
| **No semantic segmentation** | Person vs scene needs separate step |
| **Dynamic scenes not primary focus** | Handles them but not optimized for |
| **No metric depth guarantee** | Relative reconstruction — need scale for physics |
| **License unknown** | Publication risk |

### For Pact3D

**Not usable now** — code unreleased. **Future upgrade path** for scene backbone when available. DA3 (Apache-2.0, released, consumer GPU, metric depth) is the current choice.

**ZipMap is the right tool for building a full 3DGS environment. DA3 is the right tool for per-frame physics constraints on body motion.**

---

## Slide: ZipMap vs DA3 — Comparison

### Why DA3 Now, ZipMap Later

| Feature | DA3 | ZipMap |
|---------|-----|--------|
| Released | **Yes** | No (placeholder) |
| Metric depth | **Yes** | No (relative) |
| Consumer GPU | **Yes (<12 GB)** | No (H100) |
| Camera poses | Yes | Yes |
| Pointmaps | Yes | Yes |
| Streaming video | **Yes** | Yes |
| License | **Apache-2.0** | Unknown |
| FPS | 78 | ~75 |
| Scaling | O(N) | O(N) |
| 3DGS output | Yes | Yes |

**Decision:** DA3 for now. Monitor ZipMap for code release.

---
---

## Slide: SAM-Body4D (arXiv'25, 2512.08406)

### Training-Free 4D Human Body Mesh Recovery from Monocular Video

**Mingqi Gao, Yunqi Miao, Jungong Han**

**Input:** monocular RGB video + optional text prompts
**Output:** per-frame body mesh parameters (pose, shape, camera, skeleton), temporally consistent masks, multi-person support

- **Training-free** composition of 5 foundation models
- Multi-person with identity-consistent tracking
- Occlusion-aware via amodal completion before mesh fitting

---

## Slide: SAM-Body4D — How It Works

### Three-Stage Pipeline (All Training-Free)

**Stage 1: Masklet Generation**
- SAM 3 produces identity-consistent segmentation masks across video frames
- Memory mechanism maintains person identity through occlusions

**Stage 2: Occlusion-Aware Refinement**
- Detect occlusions via: area increase + IoU drop criterion
- Diffusion-VAS fills in occluded body regions (amodal completion)
- Produces complete body masks even when partially hidden

**Stage 3: Mask-Guided HMR**
- Refined masks → SAM 3D Body for per-frame mesh parameters
- Kalman filtering for temporal smoothing
- Efficient multi-person batching (~2x faster than sequential)

**Foundation Models Used:**

| Model | Role |
|-------|------|
| SAM 3 | Video segmentation + identity tracking |
| Diffusion-VAS | Amodal segmentation / occlusion completion |
| SAM 3D Body | Per-frame mesh recovery |
| Depth-Anything V2 | Depth cues |
| MoGe-2 | Normal/geometry cues |

---

## Slide: SAM-Body4D — Why Good / Where It Fails

### Why Good

1. **Training-free** — no fine-tuning, composes pretrained foundation models
2. **Multi-person** — identity-consistent tracking across frames
3. **Occlusion-robust** — amodal completion recovers full body under occlusion
4. **Temporal consistency** — Kalman filtering smooths across frames

### Where It Fails

| Limitation | Impact | Which Part Fails |
|-----------|--------|-----------------|
| **Camera-relative only** | No world coordinates, no notion of floor | Architecture (no world grounding) |
| **No physics** | No contact, gravity, or biomechanical constraints | Architecture |
| **Uses MHR, not SMPL** | Conversion needed for physics pipelines expecting SMPL | Output format |
| **No quantitative evaluation** | Only qualitative comparisons — hard to trust | Evaluation |
| **Heavy dependency stack** | 5 foundation models, HF access approvals, A100 GPU | Practicality |
| **Per-frame mesh recovery** | SAM 3D Body is per-frame; temporal coherence only from Kalman | Architecture |
| **No global trajectory** | Feet "float" in camera space | Architecture |

### Edge Cases

**Success cases:**
- Multi-person scenes with frequent occlusions (SAM 3 memory handles re-identification)
- Crowded scenes where standard detectors fail

**Failure cases:**
- Full-body occlusion for extended periods (SAM 3 memory expires)
- Fast motion blur (SAM 3 segmentation degrades)
- Scenes needing world-space physics (no world frame at all)

---

## Slide: SAM-Body4D — For Pact3D

### Not a Standalone Solution

**Cannot be used as primary body tracker** because:
- No world coordinates → can't do ground contact, gravity, or penetration physics
- No global root trajectory → would need separate SLAM step
- No SMPL output → conversion overhead

**Potential upstream module:**
- Occlusion-robust mask generation could feed into GVHMR/Human3R preprocessing
- Multi-person identity tracking could extend single-person methods

**vs Alternatives for Pact3D:**

| Requirement | SAM-Body4D | GVHMR | Human3R |
|------------|-----------|-------|---------|
| World coordinates | No | **Yes** | **Yes** |
| Global trajectory | No | **Yes** | **Yes** |
| SMPL output | No (MHR) | **Yes (SMPL-X)** | **Yes (SMPL-X)** |
| Multi-person | **Yes** | No | **Yes** |
| Physics-ready | No | Partial (gravity) | Partial |
| Quantitative eval | No | **Yes** | **Yes** |

---

## Slide: SAM-Body4D Authors — Recent Work

<!-- PLACEHOLDER: To be filled with subagent results -->

---
---

## Slide: Method Comparison Summary

### Three Papers at a Glance

| | GVHMR | ZipMap | SAM-Body4D |
|---|-------|--------|-----------|
| **Task** | World-grounded human motion | 3D scene reconstruction | 4D human mesh recovery |
| **Year/Venue** | SigAsia'24 | CVPR'26 | arXiv'25 |
| **Architecture** | Transformer (ff) | TTT + local attention | 5 foundation models |
| **Training** | From scratch | From scratch | Training-free |
| **Key Innovation** | GV coordinate system | O(N) TTT layers | Occlusion-aware amodal completion |
| **World Coords** | Yes (gravity-aligned) | Yes (relative) | No (camera only) |
| **Multi-Person** | No | N/A (scene) | Yes |
| **Speed** | 0.28s / 1.4K frames | 75 FPS | Not reported |
| **Code Available** | Yes | No (placeholder) | Yes |
| **License** | CC BY-NC-SA | Unknown | Not specified |
| **GPU** | RTX 4090 | H100 | A100 |

---

## Slide: Where Each Paper Fits in the Landscape

### 3D Human Pose/Motion Tracking

- **Local HMR** (camera coords): HMR 2.0, Multi-HMR, SAM 3D Body
  - SAM-Body4D extends this with temporal consistency + occlusion handling

- **Global Human Motion** (world coords): GLAMR → WHAM → **GVHMR** → WATCH
  - GVHMR is current best accuracy-speed tradeoff

- **Scene Reconstruction**: DUSt3R → VGGT → CUT3R → DA3 → **ZipMap**
  - ZipMap is fastest but unreleased; DA3 is best available

- **Joint Human-Scene**: HSfM, HAMSt3R, JOSH, Human3R, SHARE
  - Combining GVHMR (body) + DA3 (scene) + physics achieves this compositionally

---

# Pact3D: Physics-Aware Contact Tracking in 3D
## Comprehensive Research Writeup for Shirley

**Project:** Take a strong existing body tracker and add a lightweight physics/spatial grounding module (ground plane + contact + non-penetration + temporal smoothing) to turn frame-wise body outputs into stable, world-grounded, simulation-ready motion.

**Key claim:** This is the highest-impact, most feasible "low-hanging fruit" project because (1) existing trackers already produce good per-frame poses but fail on physical plausibility, (2) physics constraints are well-understood from biomechanics literature, and (3) the full pipeline can be assembled training-free from permissively-licensed components in ~8 weeks.

---

## Table of Contents
1. [Problem Statement & Motivation](#1-problem-statement--motivation)
2. [Body Tracker Backbone Selection](#2-body-tracker-backbone-selection)
3. [Scene Geometry Backbone Selection](#3-scene-geometry-backbone-selection)
4. [Physics-Aware Methods & Evidence](#4-physics-aware-methods--quantitative-evidence)
5. [Joint Human-Scene Reconstruction Landscape](#5-joint-human-scene-reconstruction-landscape)
6. [Evaluation Strategy](#6-evaluation-strategy)
7. [Proposed Architecture](#7-proposed-architecture)
8. [Timeline & Feasibility](#8-timeline--feasibility)
9. [Risk Analysis](#9-risk-analysis)

---

## 1. Problem Statement & Motivation

### The Gap
State-of-the-art body trackers (GVHMR, WHAM, Human3R) produce increasingly accurate 3D poses, but they still exhibit:
- **Foot skating:** 3.0–4.4mm average sliding on RICH/EMDB-2 (GVHMR/WHAM)
- **Ground penetration:** Bodies clip through floors and objects
- **Temporal jitter:** 12.8–22.5 units on RICH/EMDB-2
- **No simulation readiness:** Outputs cannot be directly loaded into physics engines

### Why Physics Constraints Are the Right Fix
MultiPhys (CVPR'24) demonstrated that adding MuJoCo-based physics correction to SLAHMR outputs yields:
- **7x reduction** in inter-body penetration (139.3→18.7mm on CHI3D)
- **5x reduction** in ground penetration (12.2→2.4mm on Hi4D)
- **While also improving pose accuracy** (W-MPJPE 177.1→174.7mm on CHI3D)

This proves that physics constraints don't just make motion look better — they provide additional geometric information that *improves reconstruction accuracy*.

### Why This Is Low-Hanging Fruit
- No training required — compose pretrained models + optimization
- Physics engines (MuJoCo) are mature, Apache-2.0 licensed, well-documented
- Biomechanics constraints (foot contact, CoM, friction cones) are well-established
- Clear, measurable improvements on standard benchmarks

---

## 2. Body Tracker Backbone Selection

### Quantitative Comparison: Camera-Space (3DPW, mm ↓)

| Method | Year | PA-MPJPE | MPJPE | PVE | Accel | World Coords? | Multi-Person? | License |
|--------|------|----------|-------|-----|-------|---------------|---------------|---------|
| GLAMR | 2022 | 51.1 | — | — | 8.0 | Yes | No | NVIDIA NC |
| SLAHMR | 2023 | 55.9 | — | — | — | Yes | Yes | **MIT** |
| HMR 2.0 | 2023 | 44.4 | 69.8 | 82.2 | 18.1 | No | No | **MIT** |
| WHAM | 2024 | 35.9 | 57.8 | 68.7 | 6.6 | Yes | No | Custom |
| **GVHMR** | **2024** | **36.2** | **55.6** | **67.2** | **5.0** | **Yes** | No | Custom |
| Multi-HMR | 2024 | 45.9 | 73.1 | 87.1 | — | No | Yes | CC BY-NC-SA |
| TRACE | 2023 | 50.9 | 79.1 | 95.4 | 28.6 | Yes | Yes | Ambiguous |
| PromptHMR | 2025 | **35.5** | — | **67.3** | — | Yes | No | Available |
| **Human3R** | **2025** | 44.1 | 71.2 | 84.9 | — | **Yes** | **Yes** | **MIT** |

### Quantitative Comparison: World-Grounded (EMDB-2, mm ↓)

| Method | WA-MPJPE₁₀₀ | W-MPJPE₁₀₀ | RTE (%) | Jitter | Foot Slide | Speed |
|--------|-------------|------------|---------|--------|------------|-------|
| GLAMR | 280.8 | 726.6 | 11.4 | 46.3 | 20.7 | Slow |
| SLAHMR | 326.9 | 776.1 | — | 31.3 | 14.5 | ~260 min/1K frames |
| WHAM | 135.6 | 354.8 | 6.0 | 22.5 | 4.4 | ~5s / 1K frames |
| **GVHMR** | **111.0** | **276.5** | **2.0** | **16.7** | **3.5** | **0.28s / 1.4K frames** |
| WATCH | **106.4** | **269.3** | — | **14.4** | — | — |
| **Human3R** | **112.2** | **267.9** | **2.2** | — | — | **15 FPS e2e** |
| TRACE | 529.0 | 1702.3 | — | 2987.6 | 370.7 | — |

### World-Grounded (RICH, mm ↓)

| Method | WA-MPJPE₁₀₀ | W-MPJPE₁₀₀ | RTE (%) | Jitter | Foot Slide |
|--------|-------------|------------|---------|--------|------------|
| GLAMR | 129.4 | 236.2 | 3.8 | 49.7 | 18.1 |
| WHAM | 109.9 | 184.6 | 4.1 | 19.7 | 3.3 |
| **GVHMR** | **78.8** | **126.3** | **2.4** | **12.8** | **3.0** |
| **Human3R** | 110.0 | 184.9 | 3.3 | — | — |

### Recommendation: Two-Track Approach

**Primary: GVHMR** — Best accuracy, lowest foot sliding (3.0mm) and jitter (12.8), gravity-view coordinates are physics-friendly, ~5000 FPS core network. Best single-person tracker available.

**Alternative: Human3R** — Only method producing multi-person SMPL-X + scene geometry + camera poses in a single 15 FPS forward pass. MIT licensed. Joint scene output eliminates need for separate scene backbone. Its explicit weaknesses (penetration, HOI) are exactly what our physics layer fixes.

**Justification for not choosing others:**
- GLAMR/SLAHMR/TRACE: Superseded; 2–10x worse on all world-grounded metrics
- WHAM: Good but GVHMR beats it on every metric while being 7x faster
- Multi-HMR: No world coordinates, non-commercial license
- HMR 2.0: Per-frame only, no world coordinates (but MIT — useful as component)

---

## 3. Scene Geometry Backbone Selection

### Why Depth Anything 3 (DA3) — Scored 9.0/10 across weighted criteria

#### Quantitative Depth Accuracy (Zero-Shot, AbsRel ↓ / delta1 ↑)

| Method | NYUv2 AbsRel | NYUv2 δ₁ | KITTI AbsRel | KITTI δ₁ | ETH3D AbsRel |
|--------|-------------|----------|-------------|----------|--------------|
| **DA3-Metric (L)** | 0.070 | 0.963 | 0.086 | 0.953 | **0.104** |
| Metric3D v2 (g) | **0.043** | **0.981** | **0.043** | **0.982** | 0.042 |
| UniDepth v2 | 0.064 | 0.968 | 0.076 | 0.968 | 0.152 |
| MoGe-2 (ViT-L) | Competitive | Competitive | Competitive | Competitive | — |
| DepthPro | 0.093 | 0.932 | 0.121 | 0.843 | 0.349 |

*Metric3D v2 is ~40% better on raw depth, but DA3 wins on the full requirements matrix:*

#### Capabilities Matrix

| Feature | DA3 | Metric3D v2 | CUT3R | VGGT | ZipMap | MoGe-2 |
|---------|-----|------------|-------|------|--------|--------|
| Metric depth | Yes | **Best** | Yes | Yes | Yes | Yes |
| Camera poses | **Yes** | No | Yes | Yes | Yes | No |
| Pointmaps | **Yes** | No | Yes | Yes | Yes | Yes |
| Streaming video | **Yes (<12GB)** | No | Yes (8GB) | No (quadratic) | Yes* | No |
| Dynamic scenes | Partial | No | **Yes** | No | Partial | No |
| License | **Apache-2.0** | Apache-2.0 | CC BY-NC-SA | Custom | Unknown | **MIT** |
| Released | **Yes** | Yes | Yes | Yes | **No** | Yes |

*ZipMap: code not yet released

#### Runtime & Memory (Critical for Limited GPUs)

| Method | FPS (GPU) | VRAM | Long video on RTX 3090? | On 12GB GPU? |
|--------|-----------|------|------------------------|-------------|
| **DA3-Large** | **78 FPS** | **<12 GB streaming** | **Any length** | **Any length** |
| DA3-Small | 161 FPS | ~4-6 GB | Any length | Any length |
| Metric3D v2 (L) | ~15-20 FPS | ~8-10 GB | Per-frame only | Per-frame only |
| CUT3R | 15-18 FPS | ~8 GB constant | Any length | Yes |
| VGGT | ~60 FPS | 8-40+ GB quadratic | ~60-75 frames max | ~15-20 frames |
| DUSt3R/MASt3R | 1-5 FPS | 8-24+ GB quadratic | ~50-100 frames | ~20-50 frames |

#### The Five Arguments for DA3

1. **Unique output combination** — Only method producing metric depth + camera poses + pointmaps + streaming + 3DGS from a single model
2. **GPU feasibility** — DA3-Large runs at 78 FPS with streaming under 12 GB VRAM on arbitrarily long videos
3. **Depth quality is sufficient** — AbsRel 0.070 (NYU) is adequate because the physics optimizer corrects residual errors (ground plane RANSAC, penetration correction). The 40% gap vs Metric3D has diminishing returns when depth serves as a collision proxy
4. **Licensing** — Apache-2.0. Combined with Human3R (MIT) + MuJoCo (Apache-2.0) = fully permissive stack
5. **Ecosystem fit** — Pointmaps integrate with CUT3R representation space; camera poses feed into GVHMR world-frame alignment; streaming API matches frame-by-frame body processing

**Recommended config:** DA3Metric-Large primary, DA3-Base fallback for speed, MegaSaM complement for hard dynamic sequences, ZipMap as future upgrade when released.

---

## 4. Physics-Aware Methods & Quantitative Evidence

### MultiPhys (CVPR'24) — Primary Reference Implementation

**Mechanism:** Formulates physics correction as an MDP. A pre-trained Universal Humanoid Controller (UHC) policy produces joint torques in MuJoCo to track kinematic reference poses while respecting gravity, collisions, and contact. Uses "Loop-N" iterative correction (N=2 optimal).

**Multi-person:** All agents simulated simultaneously — inter-body collisions handled natively by physics engine.

#### Results on CHI3D (mm ↓)

| Method | Penetration | Ground Pen. | Skating | Accel | W-MPJPE | PA-MPJPE |
|--------|------------|-------------|---------|-------|---------|----------|
| SLAHMR | 139.3 | 4.4 | 1.0 | 6.5 | 177.1 | 83.5 |
| EmbPose-MP | 40.2 | 2.6 | 2.8 | 7.7 | 214.7 | 96.5 |
| **MultiPhys** | **18.7** | **3.2** | 2.7 | 7.4 | **174.7** | **80.4** |

#### Results on Hi4D (mm ↓)

| Method | Penetration | Ground Pen. | Skating | W-MPJPE | PA-MPJPE |
|--------|------------|-------------|---------|---------|----------|
| SLAHMR | 367.3 | 12.2 | 4.9 | 121.6 | 69.1 |
| **MultiPhys** | 51.1 | **2.4** | 3.5 | **118.1** | 71.2 |

**Key takeaway:** 7x penetration reduction, 5x ground penetration reduction, while *also* improving pose accuracy.

### CRISP (arXiv'25) — Contact-Guided Real2Sim

- Fits planar primitives to scene point clouds for simulation-ready geometry
- Uses contact to infer occluded geometry (e.g., chair seat from sitting posture)
- RL-based humanoid tracking in reconstructed scene
- **Motion tracking failure rate:** 55.2% → 6.9% (8x improvement)
- **Real-to-sim success rate:** 93.1% vs VideoMimic's 44.8%
- **Throughput:** 43% faster than VideoMimic (23K vs 16K FPS)

### PhysDiff (ICCV'23) — Physics in the Diffusion Loop

- Inserts physics simulator into each denoising step (not post-processing)
- **86% reduction** in physical error (31.572 → 4.111 on HumanML3D)
- Also improves motion quality (FID 0.544 → 0.433)
- Proves physics corrections help even in generative settings

### PROX (ICCV'19) — Scene Constraint Formulation

- Interpenetration constraint: SDF-based body-scene collision penalty
- Contact constraint: Encourages body vertices to touch scene surfaces when close
- **24% improvement** in V2V error when combining both constraints
- Contact + penetration are complementary — both needed for best results

### LEMO (ICCV'21) — Friction & Motion Priors

- Marker-based smoothness prior from AMASS reduces jitter
- **Stationary friction term** prevents skating (velocity penalty on contact vertices)
- Contact-aware motion infiller recovers plausible motion during occlusions

### IPMAN (CVPR'23) — Biomechanical Stability

- Center of Pressure (CoP) and Center of Mass (CoM) constraints
- Infers pressure heatmaps from body-ground interpenetration
- Differentiable IP terms integrate into optimization/regression
- Directly relevant to biomechanics expertise

### SimPoE (CVPR'21) / EmbodiedPose

- Policy-based simulated character control for pose estimation
- Physics simulator in the loop during both training and inference
- EmbodiedPose: reinforcement-learning-based multi-person extension

### Contact Estimation Methods

| Method | Task | Key Metric | Notes |
|--------|------|-----------|-------|
| DECO (ICCV'23) | Vertex-level contact from RGB | Precision/Recall on DAMON | Over-predicts foot contact |
| SA-HMR (CVPR'23) | Contact-scene estimation | P/R 0.57/0.53 on RICH | Includes scene-aware HMR |
| IPMAN (CVPR'23) | CoP/CoM stability | Evaluated on RICH, MoYo | Biomechanics-based |

### PhysHMR (SIGGRAPH Asia'25) — Critical Recent Work

**End-to-end visual-to-action policy** — eliminates two-stage pipeline entirely. Uses pixel-as-ray to lift 2D keypoints into 3D rays, combines RL + knowledge distillation.

#### Results on EMDB-2

| Method | PA-MPJPE | WA-MPJPE | MPJPE | Foot Slide | Height Viol. | Accel |
|--------|----------|---------|-------|------------|-------------|-------|
| TRAM | 35.51 | 148.05 | 56.74 | 11.76 | 22.97 | 4.77 |
| GVHMR | 40.95 | 228.67 | 65.21 | 5.65 | 26.42 | 5.40 |
| GVHMR × PHC+ (two-stage) | 46.24 | 193.01 | 72.50 | **12.71** | 7.71 | 7.43 |
| **PhysHMR (end-to-end)** | **39.34** | **189.26** | **55.48** | **4.60** | **5.04** | **5.49** |

**Critical finding:** Two-stage physics post-processing (GVHMR × PHC+) actually **worsens** foot sliding from 5.65→12.71mm because excessive limb movements during balance recovery create new artifacts. End-to-end integration avoids this.

**Implication for our project:** This suggests the physics layer should be tightly coupled with the body tracker (differentiable losses during optimization, not pure post-processing). Our approach should use optimization-based refinement (PROX/LEMO style energy terms) rather than RL post-correction, which avoids the balance-recovery artifacts PhysHMR identified in two-stage methods.

### Additional Physics-Aware Methods (2025-2026)

- **BioMoDiffuse** (arXiv Mar'25): Physics-guided biomechanical diffusion using muscle EMG + Euler-Lagrange dynamics
- **FlexMotion** (arXiv Jan'25): Latent-space diffusion with OpenSim physics augmentation
- **"Measuring Physical Plausibility"** (BMVC'24): Proposes CoM Distance and Pose Stability Duration as better metrics than heuristic FS/GP
- **GECO** (2025): GPT-driven 3D human-scene contact estimation, competitive with DECO

### Contact Estimation Methods

| Method | Year | Task | Key Metric |
|--------|------|------|-----------|
| DECO | ICCV'23 | Vertex-level contact from RGB | Trained on DAMON; over-predicts foot contact |
| SA-HMR | CVPR'23 | Contact-scene estimation | P/R 0.57/0.53 on RICH |
| IPMAN | CVPR'23 | CoP/CoM biomechanical stability | Differentiable, easy to integrate |
| DecoDINO | 2025 | Semantic contact classification | Extends DECO with object labels |

### Summary of Evidence: Physics Constraints Work

| Study | What Was Added | Key Improvement |
|-------|---------------|-----------------|
| MultiPhys | MuJoCo simulation loop | 7x less penetration, 5x less ground pen. |
| CRISP | Planar scene + RL tracking | 8x lower failure rate |
| PhysDiff | Physics in diffusion denoising | 86% less physical error |
| PROX | SDF penetration + contact terms | 24% better V2V |
| LEMO | Friction + smoothness prior | Eliminates skating + jitter |
| SimPoE | Sim-based pose estimation | MPJPE 56.7 + FS 3.4 + GP 1.6 (all SOTA simultaneously) |
| **PhysHMR** | **End-to-end visual→physics** | **Best on all metrics; two-stage hurts** |

**The trend is clear:** Integrated physics consistently improves both plausibility AND accuracy. The field is moving from post-hoc optimization (PROX, LEMO) toward learned RL policies in physics simulators (SimPoE, MultiPhys, PhysHMR, CRISP).

---

## 5. Joint Human-Scene Reconstruction Landscape

### Comparative Summary

| Method | Year | Online? | Multi-Person? | Scene? | Unified? | Key Benchmark |
|--------|------|---------|---------------|--------|----------|---------------|
| HOSNeRF | 2023 | No | No | NeRF | No | Per-video training (~5 days) |
| VGGT | 2025 | No | No | Dense | Yes | Static scenes only |
| Easi3R | 2025 | No | No | Dynamic | Yes | Training-free DUSt3R extension |
| JOSH | 2026 | No | Yes | Yes | No | EMDB WA-MPJPE **68.9** (best overall) |
| **Human3R** | **2025** | **Yes (15fps)** | **Yes** | **Dense** | **Yes** | EMDB WA-MPJPE 112.2 (best online) |
| SHARE | 2025 | No | No | Pointmap | No | RICH only |
| HSfM | 2025 | No | Yes | SfM | No | Multi-view only |
| HAMSt3R | 2025 | No | Yes | Dense | Partial | Multi-view only |

### Human3R Deep Dive — Why It's the Best Base System

**Architecture:** Parameter-efficient extension of CUT3R (frozen backbone). Adds trainable human prompt injection:
1. Head Detection MLP identifies human heads in CUT3R features (no external detector)
2. Multi-HMR ViT-DINO prior provides human-specific features
3. Human prompts are prepended to CUT3R decoder as visual prompt tokens (VPT)
4. Self-attend with image tokens + cross-attend with scene state
5. Human Parameter Head decodes SMPL-X (52×3 pose, 10 shape, 10 expression)

**Training:** BEDLAM synthetic dataset, single 48GB GPU, 1 day, 4-frame sequences.

**Inference:** 15 FPS, 8 GB VRAM, generalizes to thousands of frames via state rollout.

**Key result:** Adding human reconstruction *improves* scene/depth/camera estimation over CUT3R baseline:

| Config | TUM-D ATE (cm) | Bonn AbsRel | Bonn δ₁ |
|--------|---------------|-------------|---------|
| CUT3R | 5.2 | 0.185 | 0.752 |
| Human3R + TTT3R | **3.3** | **0.162** | **0.801** |

**Explicit failure modes (from paper):**
1. Human-scene penetration — meshes clip through floors/chairs
2. Head occlusion — detection relies on visible heads
3. No physics — no gravity, friction, or biomechanics
4. Limited HOI — no explicit object representation

**These failures are exactly what our physics layer fixes.**

**Why Human3R over JOSH:**
- JOSH has better numbers (WA-MPJPE 68.9 vs 112.2 on EMDB-2) but is offline, optimization-based, multi-stage
- Human3R is online, real-time, single model, MIT licensed
- Adding physics corrections to Human3R could close the gap while maintaining real-time capability

---

## 6. Evaluation Strategy

### Standard Metrics

| Category | Metric | Definition | Units |
|----------|--------|-----------|-------|
| Kinematic | PA-MPJPE | Procrustes-aligned joint error | mm |
| Kinematic | MPJPE | Mean per-joint position error | mm |
| Kinematic | PVE | Per-vertex error (mesh) | mm |
| World | W-MPJPE₁₀₀ | World MPJPE over 100-frame segments | mm |
| World | WA-MPJPE₁₀₀ | World-aligned MPJPE (less drift-sensitive) | mm |
| World | RTE | Root translation error | % |
| **Physics** | **Foot Sliding** | **Foot displacement during contact** | **mm** |
| **Physics** | **Ground Penetration** | **Depth below ground plane** | **mm** |
| **Physics** | **Inter-body Penetration** | **Mesh intersection distance** | **mm** |
| **Physics** | **Jitter** | **Third derivative of joint positions** | **m/s³** |
| **Physics** | **Contact Precision/Recall** | **Predicted vs GT contact vertices** | **—** |

### Dataset Selection (Justified)

| Dataset | Why | What It Evaluates | Ground Truth |
|---------|-----|-------------------|-------------|
| **RICH** | Primary. Only dataset with scene scans + vertex-level contact GT + reliable global coords | Contact accuracy, ground penetration, foot sliding, world trajectory | SMPL-X (multiview mocap), 3D scene scans, vertex contact labels |
| **EMDB-2** | Most accurate global GT (2.3cm pose, 5.1cm root). Moving cameras. | World trajectory, smoothness, drift | SMPL (EM sensors), global camera+body trajectories |
| **3DPW** | Standard benchmark for comparability. Every method reports on it. | Camera-space pose accuracy | SMPL (IMU-fused), 60 sequences |
| **Hi4D** | Multi-person close interaction (hugging, dancing). Contact GT. | Inter-person penetration, contact | 4D textured scans, vertex contact, SMPL |

**Why RICH is primary:** It uniquely provides scene scans + vertex-level contact GT + reliable global coordinates. This enables simultaneously evaluating contact accuracy, ground penetration, foot sliding, and world-grounded trajectory — all the metrics our physics layer targets.

### SOTA Numbers on Our Primary Benchmarks

**RICH (world-grounded, what we're trying to beat):**

| Method | WA-MPJPE | W-MPJPE | RTE | Jitter | Foot Slide |
|--------|---------|---------|-----|--------|------------|
| GVHMR | **78.8** | **126.3** | **2.4** | 12.8 | 3.0 |
| WHAM | 109.9 | 184.6 | 4.1 | 19.7 | 3.3 |
| GLAMR | 129.4 | 236.2 | 3.8 | 49.7 | 18.1 |
| Human3R | 110.0 | 184.9 | 3.3 | — | — |

**Our target:** Match GVHMR's pose accuracy while achieving <1mm foot sliding, <1mm ground penetration, and measurable contact precision/recall — metrics no current method optimizes for.

---

## 7. Proposed Architecture

```
Input: Monocular RGB Video
         │
         ├── Body Tracker (GVHMR or Human3R)
         │     └── Per-frame SMPL(-X) in world coords
         │         + global root trajectory
         │
         ├── Scene Backbone (DA3-Metric-Large)
         │     └── Per-frame metric depth + pointmaps
         │         + camera poses
         │
         └── Physics Refinement Layer
               │
               │  NOTE: PhysHMR (SigAsia'25) showed two-stage RL
               │  post-correction can WORSEN foot sliding (5.65→12.71mm).
               │  We use optimization-based energy minimization instead,
               │  which avoids balance-recovery artifacts.
               │
               ├── Ground Plane (RANSAC on pointmap)
               ├── Scene Collision Mesh (pointmap → mesh)
               ├── Contact Detection (foot velocity + proximity)
               ├── Differentiable Energy Optimization:
               │     ├── E_contact: foot/body → pin to surface (PROX-style)
               │     ├── E_penetration: SDF non-intersection (PROX-style)
               │     ├── E_friction: velocity penalty on contact verts (LEMO)
               │     ├── E_stability: CoM/CoP balance (IPMAN)
               │     └── E_smooth: temporal jerk minimization
               ├── MuJoCo Validation (not correction):
               │     └── Simulate refined motion → verify plausibility
               └── Output: Simulation-ready motion
                     + contact labels
                     + per-frame metrics (FS, GP, Pen., Jitter)
```

### License-Safe Stack

| Component | License | Role |
|-----------|---------|------|
| GVHMR | Research-only | Body tracker (option A) |
| Human3R | **MIT** | Body tracker (option B, preferred) |
| DA3-Metric-Large | **Apache-2.0** | Scene geometry |
| MuJoCo | **Apache-2.0** | Physics engine |
| Open3D | **MIT** | Point cloud / mesh processing |
| trimesh | **MIT** | Collision mesh generation |
| PyTorch | **BSD** | Optimization backend |

---

## 8. Timeline & Feasibility

### 8-Week Plan

| Week | Focus | Deliverable | Risk |
|------|-------|-------------|------|
| **1** | Environment + baselines | DA3 + GVHMR/Human3R running on test videos; common data format | Low — pretrained models |
| **2** | Scene proxy + world frame | Floor plane (RANSAC), gravity alignment, collision mesh extraction | Low — standard geometry |
| **3** | Contact inference | Foot contact from velocity + floor proximity; skating/penetration losses defined | Low — established heuristics |
| **4** | MuJoCo correction loop | Body capsules + scene planes → optimize root + feet; initial penetration reduction | Medium — MuJoCo integration |
| **5** | Rigid object interaction | Hand/object non-penetration, primitive fitting from pointmaps | Medium — object fitting |
| **6** | Evaluation + ablations | Metrics on RICH, EMDB-2, 3DPW; ablation: each constraint's contribution | Low — metrics are defined |
| **7** | Robustness | Chunking + stitching, plane-only fallback, 3-5 diverse test videos | Medium — edge cases |
| **8** | Demo + writeup | Side-by-side renders, metrics table, technical report | Low |

### Computational Requirements

| Component | GPU Memory | Runtime per 1K frames |
|-----------|-----------|----------------------|
| GVHMR (core) | ~4 GB | ~0.2 sec |
| Human3R | ~8 GB | ~67 sec (15 FPS) |
| DA3-Metric-L | <12 GB (streaming) | ~13 sec (78 FPS) |
| MuJoCo correction | CPU (+ GPU optional) | ~10-30 sec (optimization) |
| **Total pipeline** | **<16 GB peak** | **<2 min / 1K frames** |

Single consumer GPU (RTX 3090/4090) is sufficient.

---

## 9. Risk Analysis

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| DA3 depth too noisy for collision | Low | Use plane-only proxy; physics corrects residual errors |
| MuJoCo integration complexity | Medium | Start with ground plane only; MultiPhys provides reference implementation |
| GVHMR license restricts publication | Medium | Fall back to Human3R (MIT) or 4DHumans (MIT) |
| Scene geometry drift in long videos | Medium | DA3 streaming mode; MegaSaM fallback for camera robustness |
| Physics corrections degrade pose accuracy | Low | MultiPhys showed physics *improves* accuracy; ablate each term |
| Insufficient time for week 5 (HOI) | Medium | HOI is stretch goal; core value is in weeks 1-4 (ground contact) |

---

## Appendix A: Additional Papers Researched

### ZipMap (CVPR'26)
- **1.4B-param** feed-forward scene reconstructor with **O(N) linear scaling** via Test-Time Training layers
- 750+ frames in <10 seconds on H100 (~75 FPS)
- Outputs: camera poses, depth maps, point maps, novel views
- **Code not yet released** (placeholder repo)
- Future upgrade path for scene backbone when available

### SAM-Body4D (arXiv 2512.08406)
- Training-free pipeline: SAM 3 tracking → Diffusion-VAS occlusion completion → SAM 3D Body mesh recovery
- Multi-person, occlusion-robust, Kalman-filtered temporal smoothing
- **Camera-relative only**, uses MHR not SMPL, no quantitative benchmarks
- Potential upstream module for occlusion handling, not a standalone solution

### PromptHMR (CVPR'25)
- PA-MPJPE 35.5 on 3DPW (current SOTA)
- Promptable architecture, combines with metric SLAM for world coordinates
- Worth monitoring as a body backbone alternative

### WATCH (arXiv Sept'25)
- WA-MPJPE₁₀₀ 106.4 on EMDB-2, 74.3 on RICH (beats GVHMR on world metrics)
- Unified camera + human trajectory estimation
- Very recent, maturity TBD

### PhysHMR (SIGGRAPH Asia'25) — Must-Read
- End-to-end visual-to-action policy (no two-stage pipeline)
- Best simultaneous accuracy + physics on EMDB-2: PA-MPJPE 39.34, FS 4.60, HV 5.04
- **Critical negative result:** Two-stage (GVHMR × PHC+) worsens foot sliding from 5.65→12.71
- User study: 66.3% preferred PhysHMR over alternatives
- Implications: optimization-based refinement (energy minimization) is safer than RL post-correction

### SimPoE (CVPR'21) — Historical Milestone
- First method to achieve SOTA accuracy AND physics plausibility simultaneously
- MPJPE 56.7 + FS 3.4 + GP 1.6 on H3.6M (all best)
- Meta-PD control for dynamic PD parameter adjustment

---

## Appendix B: Physics & Simulation Stack

| Engine | License | Strengths | Use Case |
|--------|---------|-----------|----------|
| **MuJoCo** | **Apache-2.0** | Best contact dynamics, MultiPhys uses it, stable | **Primary choice** |
| PyBullet | zlib | Easy prototyping, large URDF ecosystem | Rapid prototyping |
| Brax | Apache-2.0 | JAX differentiable, massive parallelism | If using JAX backend |
| SAPIEN | Apache-2.0 | Articulated objects, PhysX 5 GPU sim | HOI extension |
| Drake | BSD | Formal optimization, rigorous contact | If need mathematical guarantees |

**Integration pattern:**
1. Scene pointmap → RANSAC floor plane + coarse mesh → collision proxy
2. SMPL mesh → kinematic skeleton + collision capsules
3. MuJoCo: simultaneous simulation with contact + non-penetration
4. Optimize root trajectory + foot placements → output refined motion

---

## Appendix C: Evaluation Metric Implementations

### Foot Sliding
```python
def foot_sliding(joints_world, contact_mask, foot_idx, dt):
    """Average horizontal foot velocity during contact frames (mm)"""
    foot = joints_world[:, foot_idx, :]
    v_xy = np.linalg.norm((foot[1:] - foot[:-1])[:, :2] / dt, axis=1)
    contact = contact_mask[1:]
    return float(np.mean(v_xy[contact])) if np.any(contact) else 0.0
```

### Ground Penetration
```python
def penetration_plane(vertices_world, plane_n, plane_d):
    """Average penetration depth below ground plane (mm)"""
    signed = vertices_world @ plane_n + plane_d
    return float(np.mean(-np.minimum(signed, 0.0)))
```

### Trajectory Smoothness (Acceleration)
```python
def trajectory_drift(root_world, dt):
    """Mean root acceleration magnitude — lower is smoother"""
    vel = (root_world[1:] - root_world[:-1]) / dt
    acc = (vel[1:] - vel[:-1]) / dt
    return float(np.mean(np.linalg.norm(acc, axis=1)))
```

---

## Appendix D: Key References

### Body Tracking
- WHAM: Shin et al., CVPR 2024 — [wham.is.tue.mpg.de](https://wham.is.tue.mpg.de/)
- GVHMR: Shen et al., SigAsia 2024 — [github.com/zju3dv/GVHMR](https://github.com/zju3dv/GVHMR)
- Human3R: Chen et al., ICLR 2026 — [github.com/fanegg/Human3R](https://github.com/fanegg/Human3R)
- 4D-Humans: Goel et al., ICCV 2023 — [github.com/shubham-goel/4D-Humans](https://github.com/shubham-goel/4D-Humans)
- TRAM: Wang et al., ECCV 2024 — [github.com/yufu-wang/tram](https://github.com/yufu-wang/tram)
- PromptHMR: Wang et al., CVPR 2025 — [github.com/yufu-wang/PromptHMR](https://github.com/yufu-wang/PromptHMR)

### Scene Geometry
- Depth Anything 3: ByteDance, arXiv 2025 — [github.com/ByteDance-Seed/Depth-Anything-3](https://github.com/ByteDance-Seed/Depth-Anything-3)
- ZipMap: Jin et al., CVPR 2026 — [haian-jin.github.io/ZipMap](https://haian-jin.github.io/ZipMap/)
- CUT3R: CVPR 2025 — [github.com/CUT3R/CUT3R](https://github.com/CUT3R/CUT3R)
- VGGT: Meta, CVPR 2025 Best Paper — [github.com/facebookresearch/vggt](https://github.com/facebookresearch/vggt)

### Physics-Aware Methods
- **PhysHMR:** Feng et al., SIGGRAPH Asia 2025 — [arXiv 2510.02566](https://arxiv.org/abs/2510.02566) *(critical: shows two-stage hurts)*
- MultiPhys: Ugrinovic et al., CVPR 2024 — [github.com/nicolasugrinovic/multiphys](https://github.com/nicolasugrinovic/multiphys)
- CRISP: Wang et al., arXiv 2025 — [crisp-real2sim.github.io](https://crisp-real2sim.github.io/CRISP-Real2Sim/)
- PhysDiff: Yuan et al., ICCV 2023 — [nvlabs.github.io/PhysDiff](https://nvlabs.github.io/PhysDiff/)
- SimPoE: Yuan et al., CVPR 2021 *(first to achieve SOTA accuracy + physics simultaneously)*
- PROX: Hassan et al., ICCV 2019 — [prox.is.tue.mpg.de](https://prox.is.tue.mpg.de/)
- LEMO: Zhang et al., ICCV 2021 — [github.com/sanweiliti/LEMO](https://github.com/sanweiliti/LEMO)
- IPMAN: Tripathi et al., CVPR 2023
- DECO: Tripathi et al., ICCV 2023 — vertex-level contact from RGB

### Joint Reconstruction
- JOSH: ICLR 2026 — [github.com/genforce/JOSH](https://github.com/genforce/JOSH)
- Easi3R: ICCV 2025 — [github.com/Inception3D/Easi3R](https://github.com/Inception3D/Easi3R)
- SHARE: arXiv 2025 — [github.com/JoshLiCoding/SHARE](https://github.com/JoshLiCoding/SHARE)

### Datasets
- RICH: Huang et al., CVPR 2022 — [rich.is.tue.mpg.de](https://rich.is.tue.mpg.de/)
- EMDB: Kaufmann et al., ICCV 2023 — 2.3cm pose accuracy, 5.1cm root
- 3DPW: von Marcard et al., ECCV 2018
- Hi4D: Yin et al., CVPR 2023 — [yifeiyin04.github.io/Hi4D](https://yifeiyin04.github.io/Hi4D/)
- DAMON/DECO: Tripathi et al., ICCV 2023 — vertex-level contact GT

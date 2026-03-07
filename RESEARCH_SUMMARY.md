# Pact3D Research Summary
## Physics-Aware Contact Tracking in 3D — Paper & Project Landscape

**Focus:** Take a strong existing body tracker (SAM 3D Body / 4D-Humans / WHAM / etc.), then add a lightweight physics/spatial grounding module (ground plane + contact + non-penetration + temporal smoothing) to turn frame-wise body outputs into stable world-grounded motion.

---

## Table of Contents
1. [Project Thesis](#project-thesis)
2. [Global Human Motion Tracking / Physics-Aware](#cluster-1-global-human-motion-tracking--physics-aware)
3. [Joint Human-Scene Tracking / Reconstruction](#cluster-2-joint-human-scene-tracking--reconstruction)
4. [Additional Papers (ZipMap, SAM-Body4D)](#additional-papers)
5. [Building Blocks & Components](#building-blocks--components)
6. [Physics & Simulation Stack](#physics--simulation-stack)
7. [Recommended Pipeline & Timeline](#recommended-pipeline--timeline)
8. [Evaluation Metrics](#evaluation-metrics)

---

## Project Thesis

**Goal:** World-grounded, physics-aware human tracking from monocular video.

**Core insight:** The best "physics enablement" wins are often not new networks, but constraints that remove degenerate solutions — floating feet, drift, scale ambiguity, interpenetration. Biomechanics knowledge (contact dynamics, gait/foot constraints) is the differentiator.

**Architecture:** Vision proposes → Physics refines.
- **Body backbone:** SAM 3D Body / 4DHumans / WHAM / Multi-HMR (per-frame meshes)
- **Scene backbone:** Depth Anything 3 / CUT3R / MegaSaM (depth + pointmaps + cameras)
- **Physics layer:** MuJoCo/PyBullet (contact + penetration + slip correction)
- **Output:** World-frame body trajectory + contact labels + penetration/slip metrics

---

## Cluster 1: Global Human Motion Tracking / Physics-Aware

### Yu et al. (TOG'21)
- **What:** Global human motion tracking with a *given* environment (scene assumed/provided)
- **Key idea:** Fit body motion into a known world coordinate system
- **Limitation:** Requires known scene geometry — not suitable for jointly inferring scene + human from unconstrained video
- **Relevance:** Reference for world-coordinate tracking formulation; your project removes the "given scene" assumption

### D&D (ECCV'22)
- **What:** Global tracking **without optimization** — feed-forward / less expensive inference
- **Key idea:** Avoids heavy optimization loops common in global tracking pipelines
- **Relevance:** Demonstrates that practical, fast global tracking is possible; design reference for keeping your pipeline lightweight

### MultiPhys (CVPR'24)
- **What:** Physics simulator (MuJoCo) for correcting vision-based human motion estimates
- **Key idea:** Vision proposes → physics refines. Uses MuJoCo to enforce contact/penetration plausibility
- **Why it matters:** **Directly aligned** with the project. Provides:
  - MuJoCo correction loop reference implementation
  - SDF penetration metrics and evaluation scripts
  - EGL headless rendering for server-side evaluation
- **License:** No LICENSE file found (treat as restricted)
- **Repo:** `github.com/nicolasugrinovic/multiphys`

### GVHMR (SigAsia'24)
- **What:** Gravity-aware global human motion recovery
- **Key idea:** Introduces gravity/vertical consistency as a lightweight physical prior
- **Why it matters:** "Lightweight physics" reference — gravity/orientation priors are cheap and effective before full simulation. Bridge to contact reasoning.
- **License:** CC BY-NC-SA 4.0
- **Repo:** `github.com/zju3dv/GVHMR`

### CRISP (arXiv'25)
- **What:** Contact-guided Real2Sim — monocular video → simulatable human + planar scene primitives
- **Key idea:** Uses explicit physics simulation for motion realism; contact constraints guide the sim setup
- **Why it matters:** Highly relevant if adding terrain/contact constraints to body tracker outputs. Conceptually closest to the project goal.
- **Limitation:** Heavy dependencies (pytorch3d, chumpy), no LICENSE file, "code beta" status
- **Repo:** `github.com/Z1hanW/CRISP-Real2Sim`

---

## Cluster 2: Joint Human-Scene Tracking / Reconstruction

### HOSNeRF (ICCV'23)
- **What:** 4D dynamic human-object-scene NeRF from monocular video + calibrated pose
- **Uses:** SMPL (via ROMP) + human/object masks (Mask R-CNN)
- **Cost:** ~5 days on 4 V100s per video — too slow for fast iteration
- **Relevance:** Conceptual baseline for joint human-object-scene modeling; too heavy for 2-month timeline
- **License:** MIT

### VGGT (CVPR'25)
- **What:** Feed-forward visual geometry model for static scenes (multiple input modes)
- **Outputs:** Camera intrinsics/extrinsics, pointmaps, depthmaps, tracks
- **Relevance:** Scene-geometry prior provider; doesn't solve dynamic human-scene interaction or physics alone
- **License:** VGGT License v1 (custom)
- **Repo:** `github.com/facebookresearch/vggt`

### Depth Anything 3 (arXiv'25)
- **What:** Geometry recovery via depth-ray representation from arbitrary inputs
- **Outputs:** Depth, raymaps, pointmaps, 3DGS; infers camera poses from raymaps
- **Key strength:** Streaming inference for long videos with <12GB VRAM
- **Training cost:** 128 H100s (use pretrained only)
- **License:** Apache-2.0 (permissive!)
- **Relevance:** **Best scene geometry backbone** for semi-limited GPU budgets. Use pretrained, don't retrain.
- **Repo:** `github.com/ByteDance-Seed/Depth-Anything-3`

### CUT3R (CVPR'25)
- **What:** Continuous 3D perception with online updating for dynamic scenes
- **Key strength:** Feed-forward, persistent state, supports dynamic scene updates
- **Relevance:** Strong sequential geometry model for drift control; Human3R builds on it. Use as backbone, don't retrain.
- **License:** CC BY-NC-SA 4.0
- **Repo:** `github.com/CUT3R/CUT3R`

### HSfM (CVPR'25)
- **What:** Human-scene SfM for static scene / single-frame multiview, with post-optimization
- **Relevance:** Quality upper bound for reconstruction in controlled settings; less suitable for unconstrained monocular + dynamics
- **License:** MIT

### HAMSt3R (ICCV'25)
- **What:** Human-aware multi-view stereo 3D reconstruction (static, single-frame multiview)
- **Key idea:** Injects human awareness into reconstruction; feed-forward core, SMPL fitting afterward
- **Relevance:** Ideas for human-scene coupling and decomposition; doesn't solve dynamic monocular tracking directly
- **Status:** Paper only — code not publicly found

### Easi3R (ICCV'25)
- **What:** Training-free extension of DUSt3R to dynamic scenes
- **Key mechanism:** Leverages DUSt3R cross-attention to disentangle motion, support scene/human decomposition
- **Why it matters:** **Extremely practical** — training-free, dynamic scenes, limited GPU friendly. One of the most actionable inspirations for fast experimentation.
- **License:** CC BY-NC-SA 4.0
- **Repo:** `github.com/Inception3D/Easi3R`

### JOSH (ICLR'26 submission)
- **What:** Multi-stage, multi-person, post-optimization joint human-scene reconstruction
- **Relevance:** Reference for what extra gains optimization buys (multi-person, contact consistency). Too heavy to fully reproduce in 2 months.
- **License:** No LICENSE found
- **Repo:** `github.com/genforce/JOSH`

### Human3R (arXiv'25)
- **What:** "One model, one stage" — real-time (15 fps) 4D human-scene reconstruction
- **Architecture:** CUT3R + Multi-HMR, feed-forward, trains in 1 day on 1 GPU
- **Outputs:** Multi-person meshes, cameras, dense 3D geometry (world frame)
- **Explicit limitations:** Penetration failures, HOI failures
- **Why it matters:** **Arguably the strongest "base system + your improvement layer" match.** Its stated weaknesses (penetration, HOI) are exactly what your physics layer would fix.
- **License:** MIT
- **Repo:** `github.com/fanegg/Human3R`

### Uni3C (SigAsia'25)
- **What:** 3D-enhanced framework for joint camera + human motion control in video generation
- **Cost:** 64 H100 for 40 hours (training heavy)
- **Relevance:** Future extension toward world models / controllable avatar video; not first implementation target
- **License:** Apache-2.0

### RealisDance (arXiv'24)
- **What:** Video generation / human animation prior (referenced within Uni3C)
- **Relevance:** Output/control side, not reconstruction. Useful for "world model" extensions.

### SHARE (arXiv'25)
- **What:** Video → SMPL + scene point map via multi-stage + optimization (TRAM + MoGe-2 init)
- **Relevance:** Produces aligned human + scene — core requirement before adding physics/contact. Strong reference for alignment and refinement alongside JOSH.
- **License:** No LICENSE found
- **Repo:** `github.com/JoshLiCoding/SHARE`

---

## Additional Papers

### ZipMap (CVPR'26)
- **What:** Feed-forward transformer for 3D scene reconstruction from image collections with **linear-time scaling**
- **Authors:** Haian Jin et al. (Google DeepMind, Cornell, MIT)
- **Architecture:** 1.40B params, 24 blocks of local window self-attention + Test-Time Training (TTT) layers. TTT compresses image features into "fast weights" of a SwiGLU-MLP, creating a queryable implicit scene representation.
- **Inputs:** Image collection / video frames
- **Outputs:** Camera poses (intrinsics + extrinsics), depth maps with confidence, point maps, optional novel-view RGB/depth
- **Performance:** 750+ frames in <10 seconds on a single H100 (~75 FPS), >20x faster than VGGT/Pi3
- **Key contribution:** O(N) scaling via TTT layers replacing quadratic global attention; supports streaming/sequential mode for online applications
- **Relevance to project:**
  - Excellent camera pose estimation for world-grounding body estimates
  - Scene depth/pointmaps for ground plane detection and collision surfaces
  - Streaming mode enables online body tracking pipelines
  - Linear scaling critical for long monocular videos
- **Limitations:** Code/weights **not yet released** (placeholder repo only), requires H100-class GPU, no semantic segmentation (person vs. scene needs separate step), dynamic scene handling exists but is not primary focus
- **License:** Not yet specified
- **Repo:** `github.com/Haian-Jin/ZipMap` (placeholder)

### SAM-Body4D (arXiv'25, paper 2512.08406)
- **What:** Training-free 4D human body mesh recovery from monocular video
- **Authors:** Mingqi Gao, Yunqi Miao, Jungong Han
- **Architecture:** Three-stage training-free pipeline:
  1. **Masklet Generation:** SAM 3 produces identity-consistent segmentation masks across video frames
  2. **Occlusion-Aware Refinement:** Diffusion-VAS detects and fills occluded body regions (area increase + IoU drop criterion)
  3. **Mask-Guided HMR:** Refined masks → SAM 3D Body for per-frame mesh params; Kalman filtering for temporal smoothing
- **Inputs:** Monocular RGB video + optional text prompts
- **Outputs:** Per-frame MHR body mesh parameters (pose, shape, camera, skeleton), temporally consistent masks, multi-person support
- **Key contributions:**
  - Training-free composition of foundation models
  - Occlusion-aware amodal completion before mesh fitting
  - Identity-consistent tracking via SAM 3 memory mechanism
  - Efficient multi-person batching (~2x faster than sequential)
- **Relevance to project:**
  - Strong mesh estimation frontend with occlusion robustness
  - Multi-person support out of the box
  - Integrates Depth-Anything V2 and MoGe-2 (useful depth/normal cues)
- **Limitations:**
  - **No world-coordinate estimation** — camera-relative only
  - **No physics awareness** — no contact, gravity, or biomechanical constraints
  - **Uses MHR, not SMPL** — conversion needed if physics pipeline expects SMPL
  - **No quantitative evaluation** — only qualitative comparisons
  - Heavy dependency stack (5 foundation models, HF access approvals, A100 GPU)
- **vs. alternatives:** WHAM or TRAM that directly estimate global trajectories with quantitative benchmarks may be more immediately applicable as starting body trackers
- **Repo:** `github.com/gaomingqi/sam-body4d`

---

## Building Blocks & Components

| Component | Used By | Role | License |
|-----------|---------|------|---------|
| **DUSt3R** | Easi3R, MonST3R | Pointmap regression + global alignment; foundation for dynamic extensions | CC BY-NC-SA 4.0 |
| **MonST3R** | Easi3R ecosystem | DUSt3R extended to dynamic scenes; time-varying point clouds + cameras | CC BY-NC-SA 4.0 |
| **TRAM + MoGe-2** | SHARE | Initialize human + scene estimates before joint optimization | — |
| **ROMP** | HOSNeRF | SMPL estimation module | — |
| **Multi-HMR** | Human3R | Multi-person mesh recovery; non-commercial license | Non-commercial |
| **Mask R-CNN** | HOSNeRF | Human/object segmentation masks | — |
| **SAM 3** | SAM-Body4D | Video segmentation with identity tracking | SAM License |
| **Diffusion-VAS** | SAM-Body4D | Amodal segmentation / occlusion completion | — |
| **DINOv2** | ZipMap | Image feature backbone | Apache-2.0 |

**Design pattern:** Don't reinvent every subproblem — compose existing robust modules, then focus novelty on world alignment + contact/physics consistency.

---

## Physics & Simulation Stack

| Tool | License | Best For | Integration Pattern |
|------|---------|----------|-------------------|
| **MuJoCo** | Apache-2.0 | Contact dynamics, stable tooling, MultiPhys uses it | Body as capsule skeleton + scene as collision mesh/planes |
| **PyBullet** | zlib | Rapid prototyping, large URDF ecosystem | Easy integration, good for quick demos |
| **Brax** | Apache-2.0 | Massive parallel rollouts (JAX), differentiable | Optimization-friendly if using JAX |
| **SAPIEN** | Apache-2.0 | Articulated objects, PhysX 5 GPU sim | Rich sensor sim + robotics-style interaction |
| **Drake** | BSD | Formal optimization-based control + contact | Best for rigorous contact reasoning |

**Integration pattern:**
1. Convert scene recon → collision proxy (watertight mesh / SDF / planes)
2. Convert body model (SMPL/MHR) → kinematic skeleton + collision capsules
3. Run contact + non-penetration constraints to refine root trajectory
4. Use engine rollouts to validate plausibility and compute metrics

---

## Recommended Pipeline & Timeline

### Tech Stack (all permissive licenses)
- **Body:** SAM 3D Body → SAM-Body4D for temporal consistency, or WHAM/4DHumans (MIT)
- **Scene:** Depth Anything 3 (Apache-2.0); optional CUT3R/MegaSaM for robustness
- **Physics:** MuJoCo (Apache-2.0)
- **3D Processing:** Open3D, trimesh
- **Optimization:** PyTorch autograd or SciPy
- **Future scene backbone:** ZipMap (when released) — linear-time, streaming, 75 FPS

### 8-Week Plan

| Week | Focus | Deliverable |
|------|-------|-------------|
| 1 | Baselines & data contracts | Per-frame body mesh + depth/pointmap runners; common export format |
| 2 | Scene proxy & coordinate unification | Floor plane (RANSAC), gravity alignment, world frame |
| 3 | Contact inference & biomechanics | Foot contact from velocity + floor proximity; skating/penetration/smoothness losses |
| 4 | Physics correction loop | MuJoCo integration: body capsules + scene collision → optimize root + feet |
| 5 | Object interaction (rigid primitives) | Hand/object non-penetration, stable grasp constraints |
| 6 | Evaluation & ablations | Metrics on 3DPW, RICH; foot sliding, penetration, trajectory drift |
| 7 | Robustness engineering | Chunking + overlap stitching, fallback to plane-only, 3-5 diverse videos |
| 8 | Demo packaging & write-up | Side-by-side renders, metrics table, technical report |

---

## Evaluation Metrics

### Foot Sliding (world-frame)
Penalize horizontal foot velocity during contact frames:
```python
def foot_sliding(joints_world, contact_mask, foot_idx, dt):
    foot = joints_world[:, foot_idx, :]
    v_xy = np.linalg.norm((foot[1:] - foot[:-1])[:, :2] / dt, axis=1)
    return float(np.mean(v_xy[contact_mask[1:]])) if np.any(contact_mask[1:]) else 0.0
```

### Penetration vs. Ground Plane
```python
def penetration_plane(vertices_world, plane_n, plane_d):
    signed = vertices_world @ plane_n + plane_d
    return float(np.mean(-np.minimum(signed, 0.0)))
```

### Root Trajectory Drift (smoothness)
```python
def trajectory_drift(root_world, dt):
    vel = (root_world[1:] - root_world[:-1]) / dt
    acc = (vel[1:] - vel[:-1]) / dt
    return float(np.mean(np.linalg.norm(acc, axis=1)))
```

---

## Key Takeaways

1. **Human3R** is the strongest "base + your physics layer" match — fast, feed-forward, MIT licensed, and its explicit weaknesses (penetration, HOI) are exactly what physics constraints fix.

2. **Depth Anything 3** is the best scene geometry backbone for limited GPUs (Apache-2.0, streaming, <12GB VRAM). **ZipMap** will be even better when released (linear-time, 75 FPS).

3. **SAM-Body4D** adds occlusion robustness and temporal consistency on top of SAM 3D Body, but outputs camera-relative coords and has no physics — it's a potential upstream module, not a complete solution.

4. **MultiPhys + CRISP** are the strongest references for the physics correction loop design. MultiPhys provides MuJoCo integration patterns and penetration metrics.

5. **Easi3R** is the most practical "training-free dynamic reconstruction" option for fast experimentation with limited GPUs.

6. **The project is feasible in 8 weeks** using a training-free approach: pretrained body + pretrained geometry + lightweight optimization/physics layer. No large-scale training needed.

7. **License-safe stack:** DA3 (Apache-2.0) + 4DHumans/WHAM (MIT) + MuJoCo (Apache-2.0) + Human3R (MIT) = fully permissive core.

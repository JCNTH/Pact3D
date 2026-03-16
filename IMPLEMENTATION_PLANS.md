# Pact3D Implementation Plans

Three verified, end-to-end feasible pipeline options. All use **GVHMR + DA3** as the shared vision backbone. They differ only in the **physics correction method**: geometric, optimization-based, or simulation-based.

Each component has been checked for actual code availability as of March 2026.

---

## Component Verification Summary

### Body Tracker: GVHMR (used in all options)

| | |
|---|---|
| **Repo** | [zju3dv/GVHMR](https://github.com/zju3dv/GVHMR) |
| **Status** | Released, actively maintained (last update 2025-03-08) |
| **Outputs** | SMPL body pose + shape, world trajectory (gravity-view coords), foot contact probabilities (hands, toes, heels) |
| **Inference** | `python tools/demo/demo.py --video=input.mp4` — 0.28s for 1.4K frames on RTX 4090 |
| **VRAM** | ~4 GB |
| **License** | Non-commercial (ZJU) |
| **World-grounding** | Yes — gravity-view coordinate system from visual odometry (DPVO or SimpleVO) |
| **Deps** | Python 3.10, PyTorch 2.3, CUDA 12.1, YOLO + ViTPose + HMR2 + DPVO/SimpleVO |
| **Benchmarks** | PA-MPJPE 36.2mm (3DPW), WA-MPJPE 109mm (EMDB-2), foot sliding 3.0mm |

### Scene Backbone: DA3-Metric-Large (used in all options)

| | |
|---|---|
| **Repo** | [ByteDance-Seed/Depth-Anything-3](https://github.com/ByteDance-Seed/Depth-Anything-3) |
| **Status** | Released Nov 2025, actively updated |
| **Outputs** | Metric depth maps (meters), camera extrinsics/intrinsics, point clouds (PLY), meshes (GLB), 3DGS |
| **Inference** | `da3 predict --input video.mp4 --output out/ --export ply` |
| **VRAM** | <12 GB, streaming mode for long video |
| **License** | Apache-2.0 (Large weights), CC BY-NC 4.0 (Giant/Nested weights) |
| **FPS** | 78 FPS (Large), ~10 FPS (streaming) |

### Shared Tools

| Component | Install | Purpose | License |
|-----------|---------|---------|---------|
| **Open3D** | `pip install open3d` | RANSAC ground plane, point cloud ops | MIT |
| **trimesh** | `pip install trimesh python-fcl` | Mesh collision queries (FCL backend) | MIT |
| **MuJoCo** | `pip install mujoco` | Physics engine | Apache-2.0 |
| **SMPLSim** | [ZhengyiLuo/SMPLSim](https://github.com/ZhengyiLuo/SMPLSim) | SMPL → MuJoCo XML conversion | Research |

### Physics Reference Codebases (released, verified runnable)

| Component | Repo | What We Use From It |
|-----------|------|-------------------|
| **LEMO** | [sanweiliti/LEMO](https://github.com/sanweiliti/LEMO) | Energy term design: scene SDF, friction, smoothness prior |
| **PROX** | [mohamedhassanmus/prox](https://github.com/mohamedhassanmus/prox) | SDF penetration + contact loss functions |
| **MultiPhys** | [nicolasugrinovic/multiphys](https://github.com/nicolasugrinovic/multiphys) | MuJoCo simulation loop + PD controller architecture |
| **PHC+** | [ZhengyiLuo/PHC](https://github.com/ZhengyiLuo/PHC) | Reference only — evidence shows RL post-correction hurts |

### NOT Released (do NOT depend on)

| Component | Status |
|-----------|--------|
| **PhysHMR** | Paper only. Best end-to-end approach but no code. |
| **ZipMap** | Placeholder repo since Jan 2026. |
| **SimPoE** | Never released. |
| **PACE** | No public repo. |

---

## Option A: Optimization-Based (LEMO-Style Energy Minimization)

**Approach:** Run GVHMR + DA3, then iteratively optimize SMPL corrections via differentiable energy terms (contact pinning, SDF penetration, friction, smoothness). This is the principled approach — every physical constraint is an explicit, tunable loss term.

### Architecture

```
Video
  ├─→ GVHMR ─→ SMPL poses + world trajectory + foot contacts
  ├─→ DA3-Metric-Large ─→ metric point cloud + camera poses
  │
  └─→ Physics Refinement (custom, inspired by LEMO/PROX)
        ├── Scene proxy: RANSAC ground plane + collision mesh (Open3D + trimesh)
        ├── Contact detection: foot velocity + proximity + GVHMR contact probs
        ├── Energy minimization (L-BFGS on PyTorch):
        │     E_contact:     pin feet to surface during contact
        │     E_penetration: SDF non-intersection with scene
        │     E_smooth:      temporal jerk penalty
        │     E_friction:    no horizontal sliding during contact
        │     E_stability:   CoM projection inside support polygon
        │     E_prior:       VPoser body prior (stay close to GVHMR init)
        ├── MuJoCo validation: forward-sim the corrected sequence, check stability
        │
        └─→ Corrected SMPL sequence + contact labels + metrics
```

### Why Each Component Is Feasible

1. **GVHMR**: Released, Colab available, 0.28s / 1.4K frames. Provides initialization + foot contacts.
2. **DA3-Metric-Large**: Released, Apache-2.0. Metric point clouds in meters. <12 GB VRAM.
3. **LEMO energy terms**: LEMO code released and runnable (Python 3.8/CUDA 10.0). We reimplement the loss functions in modern PyTorch — the math is documented in paper and code. Scene SDF collision, temporal smoothness prior, contact friction.
4. **PROX SDF penetration**: Released. We port the differentiable SDF penetration + contact losses. Old codebase (Python 3.6) is reference only.
5. **Ground plane**: `Open3D.segment_plane()` on DA3 point cloud. One function call.
6. **Collision mesh**: DA3 exports GLB directly. Or: Poisson reconstruction on PLY via Open3D. Then trimesh+FCL for queries.
7. **MuJoCo validation**: SMPLSim converts SMPL → MuJoCo XML. Forward sim only (verify, don't correct).
8. **VPoser prior**: Available from MPI (requires registration). Constrains poses to plausible manifold.

### Risk Assessment

| Step | Risk | Mitigation |
|------|------|-----------|
| GVHMR + DA3 inference | **Low** | Well-tested, demos available |
| Ground plane RANSAC | **Trivial** | Manual plane fallback |
| Scene SDF computation | **Medium** — voxelize mesh → SDF | `mesh_to_sdf` package or trimesh signed distance |
| Energy optimization convergence | **Medium** — tuning 6 loss weights | Start with LEMO's published weights, ablate on RICH |
| Coordinate alignment (GVHMR ↔ DA3) | **Medium** — different world frames | Align via gravity direction + ground plane normal |
| VPoser integration | **Low** — well-documented API | |

### Targets

| Metric | GVHMR Baseline | Our Target |
|--------|---------------|------------|
| Foot Sliding | 3.0 mm | **< 1 mm** |
| Ground Penetration | ~2-5 mm | **< 1 mm** |
| PA-MPJPE | 36.2 mm | **No degradation (< 38 mm)** |

### Implementation Plan (6 weeks)

#### Week 1: Environment + Baselines

| Day | Task | Deliverable |
|-----|------|------------|
| 1 | Set up conda env: GVHMR deps (PyTorch 2.3, CUDA 12.1) | Working env |
| 2 | Install DA3, download DA3-Metric-Large weights | DA3 inference working |
| 3 | Run GVHMR on 3 test videos (RICH, EMDB-2, custom) | SMPL .pkl outputs |
| 4 | Run DA3 on same videos, export PLY point clouds | Metric point clouds |
| 5 | Visualize GVHMR meshes + DA3 point clouds in same frame (Open3D) | Sanity check alignment |

**Gate:** Both produce outputs. Bodies roughly align with scene geometry.

#### Week 2: Scene Proxy + Contact Detection

| Day | Task | Deliverable |
|-----|------|------------|
| 1 | Ground plane RANSAC from DA3 point cloud | Plane coefficients (n, d) |
| 2 | Gravity alignment: rotate GVHMR world frame so GV Y-axis aligns with DA3 plane normal | Aligned coordinate system |
| 3 | Build collision mesh from DA3 output (GLB or Poisson reconstruction) | trimesh Trimesh object |
| 4 | Contact detection: foot vertex height < threshold AND velocity < threshold | Per-frame binary contact labels |
| 5 | Fuse with GVHMR's predicted contact probabilities (weighted average) | Robust contact labels |

**Gate:** Contact labels match visual ground truth. Ground plane correct.

#### Week 3: Energy Function + Optimization Loop

| Day | Task | Deliverable |
|-----|------|------------|
| 1 | `E_contact`: differentiable foot-to-surface distance, active only during contact | Loss function |
| 2 | `E_penetration`: scene SDF query for all body vertices, penalize negative values | Loss function |
| 3 | `E_friction`: horizontal velocity penalty during contact. `E_smooth`: jerk penalty | Loss functions |
| 4 | `E_stability`: project CoM onto support polygon, penalize distance to boundary | Loss function |
| 5 | Combine into total energy. Optimize with L-BFGS over per-frame Δθ (pose) + Δt (translation) corrections on top of GVHMR initialization. | Working optimizer |

**Gate:** Optimizer converges. Foot sliding and penetration improve on test clips.

#### Week 4: MuJoCo Validation + Tuning

| Day | Task | Deliverable |
|-----|------|------------|
| 1 | SMPLSim: convert SMPL → MuJoCo humanoid XML | Working MuJoCo model |
| 2 | Forward-simulate corrected motion, record contact forces + stability | Validation metrics |
| 3 | Compare MuJoCo contacts vs our contact labels — flag disagreements | Diagnostic report |
| 4 | Ablation: toggle each energy term, measure impact | Ablation table |
| 5 | Tune loss weights on RICH dataset (has vertex contact GT) | Final hyperparameters |

**Gate:** MuJoCo confirms plausibility. PA-MPJPE degradation < 2mm.

#### Week 5: Evaluation + Robustness

| Day | Task | Deliverable |
|-----|------|------------|
| 1-2 | RICH test set: foot sliding, penetration, PA-MPJPE, WA-MPJPE | Metrics table |
| 3 | EMDB-2: same metrics + trajectory drift | Metrics table |
| 4 | 3DPW: standard benchmark comparison | Metrics table |
| 5 | Temporal chunking for long videos (>500 frames): overlapping windows + stitching | Long video support |

**Gate:** Foot sliding < 1mm, penetration < 1mm, no PA-MPJPE degradation.

#### Week 6: Polish + Report

| Day | Task | Deliverable |
|-----|------|------------|
| 1-2 | Demo renders: before/after with ground contact heatmaps | Demo videos |
| 3 | Failure case analysis | Failure catalog |
| 4 | Technical report: architecture, ablations, comparisons | Report draft |
| 5 | Package: `pact3d optimize --video input.mp4 --output corrected/` | CLI tool |

---

## Option B: Feed-Forward Geometric Correction (No Optimization Loop)

**Approach:** Run GVHMR + DA3, then apply closed-form geometric corrections per frame: snap feet to ground, project penetrating vertices, freeze contact feet via IK, smooth temporally. No iterative solver — every operation is O(1) per frame.

### Architecture

```
Video
  ├─→ GVHMR ─→ SMPL poses + world trajectory + foot contacts
  ├─→ DA3-Metric-Large ─→ metric point cloud + ground plane
  │
  └─→ Deterministic Geometric Correction (no iterative optimization)
        ├── Ground plane from DA3 (RANSAC)
        ├── Contact labels from GVHMR (thresholded foot contact probabilities)
        ├── Corrections applied sequentially per frame:
        │     1. Ground snap: translate body so contact feet touch ground plane
        │     2. Penetration resolve: project penetrating vertices along surface normal
        │     3. Contact freeze: zero horizontal velocity of contact feet (IK adjustment)
        │     4. Temporal smooth: Savitzky-Golay filter on joint trajectories
        │
        └─→ Corrected SMPL sequence + contact labels
```

### Why Each Component Is Feasible

1. **GVHMR**: Same as Option A. Also provides foot contact probabilities — no separate contact model needed.
2. **DA3-Metric-Large**: Same as Option A. Ground plane via RANSAC.
3. **Ground snap**: During contact frames, translate root so foot vertices lie on ground plane. Closed-form: `Δt_y = plane_height - min(foot_vertex_heights)`. No solver.
4. **Penetration resolve**: For each vertex below ground, project to surface along normal. O(V) per frame, V=6890 for SMPL.
5. **Contact freeze (IK)**: When foot contacts ground, solve for ankle+knee angles that keep foot stationary while root moves. Analytical 2-joint IK on SMPL leg chain (pelvis→hip→knee→ankle→foot). Well-studied, closed-form.
6. **Temporal smoothing**: `scipy.signal.savgol_filter(joint_angles, window=11, order=3)`. One line.

### Why Feed-Forward?

No iterative solver at inference. Every correction is a closed-form geometric operation:
- **Deterministic**: Same input → same output, always
- **Fast**: O(N × V), no convergence waiting. ~1-2s / 1K frames.
- **Debuggable**: Each correction visualized and toggled independently
- **No hyperparameter tuning** (beyond contact threshold and smoothing window)
- **Baseline**: Establishes what geometric heuristics alone can achieve, quantifying the gap that justifies optimization (Option A)

### Limitations (Honest Assessment)

- **Ground plane only.** Won't handle chairs, walls, or objects. Only ground contact.
- **IK can introduce knee popping** if corrections are large. Mitigated by smoothing.
- **No energy-based trade-offs.** Can't balance "stay close to observation" vs "satisfy physics." Each correction applied greedily.
- **Likely won't hit <1mm foot sliding.** Realistic target: **<2mm** (improvement over GVHMR's 3.0mm but limited by greedy approach).
- **PhysHMR shows optimization beats two-stage.** This is fundamentally two-stage. But it's fast, simple, and the necessary baseline.

### Risk Assessment

| Step | Risk | Mitigation |
|------|------|-----------|
| GVHMR + DA3 inference | **Low** | Same as Option A |
| Ground plane RANSAC | **Trivial** | |
| Ground snap | **Low** — simple geometry | Multi-surface: local plane fitting for stairs/ramps |
| Penetration resolve | **Low** — vertex projection | May artifact at high-penetration frames |
| Contact IK | **Medium** — analytical IK for SMPL leg chain | Damped least-squares fallback |
| Temporal smoothing | **Trivial** | Window size: latency vs smoothness trade-off |
| Coordinate alignment | **Medium** — same as Option A | Shared solution with Option A |

### Targets

| Metric | GVHMR Baseline | Our Target |
|--------|---------------|------------|
| Foot Sliding | 3.0 mm | **< 2 mm** |
| Ground Penetration | ~2-5 mm | **< 1 mm** |
| PA-MPJPE | 36.2 mm | **No degradation (< 37 mm)** |

### Implementation Plan (4 weeks)

#### Week 1: Environment + Baselines

| Day | Task | Deliverable |
|-----|------|------------|
| 1 | Set up conda env (shared with Option A) | Working env |
| 2 | Install DA3, download weights | DA3 running |
| 3 | Run GVHMR on 3 test videos, inspect output format — verify foot contact probs | Confirmed outputs |
| 4 | Run DA3 on same videos, export PLY | Metric point clouds |
| 5 | Coordinate alignment: GVHMR gravity-view ↔ DA3 world. Match ground plane normals. | Aligned frames |

**Gate:** GVHMR bodies visible in DA3 point clouds. Contact labels look correct.

#### Week 2: Geometric Corrections

| Day | Task | Deliverable |
|-----|------|------------|
| 1 | Ground plane RANSAC (Open3D). Ground snap: during contact, shift root so min foot vertex height = 0 relative to plane. | `ground_snap()` |
| 2 | Penetration resolve: project vertices below plane to surface. | `resolve_penetration()` |
| 3 | Contact freeze via analytical IK: solve ankle + knee angles to keep foot stationary as root translates. SMPL kinematic chain: pelvis→hip→knee→ankle→foot. | `contact_ik()` |
| 4 | Temporal smoothing: Savitzky-Golay (window=11, order=3) on joint angles. Preserve contact constraints post-smoothing. | `temporal_smooth()` |
| 5 | Combine all corrections into pipeline. Run on test videos. Visualize before/after. | Working pipeline |

**Gate:** Visible improvement in foot contact. No gross artifacts.

#### Week 3: Evaluation

| Day | Task | Deliverable |
|-----|------|------------|
| 1-2 | RICH dataset: foot sliding, ground penetration, PA-MPJPE | Metrics |
| 3 | EMDB-2: WA-MPJPE, trajectory drift | Metrics |
| 4 | 3DPW: standard benchmark | Metrics |
| 5 | Comparison: GVHMR alone vs GVHMR + geometric corrections. Quantify the gap. | Baseline comparison |

**Gate:** Foot sliding improves over raw GVHMR. PA-MPJPE does not degrade.

#### Week 4: Polish

| Day | Task | Deliverable |
|-----|------|------------|
| 1-2 | Multi-surface: detect stairs/ramps via local plane fitting within foot neighborhood | Extended ground model |
| 3 | Edge cases: fast motion, occlusion, camera shake | Robustness |
| 4 | CLI: `pact3d correct --video input.mp4 --output corrected/` | CLI tool |
| 5 | Technical report + gap analysis (motivating Option A) | Report |

---

## Option C: Simulation-in-the-Loop (MultiPhys-Style MuJoCo Correction)

**Approach:** Run GVHMR + DA3, then use MuJoCo as a physics engine to forward-simulate a humanoid tracking the GVHMR reference. The physics engine enforces contacts, friction, and gravity natively — no custom loss functions needed. Based on released MultiPhys code.

### Architecture

```
Video
  ├─→ GVHMR ─→ SMPL poses + world trajectory (reference motion)
  ├─→ DA3-Metric-Large ─→ metric point cloud + ground plane
  │
  └─→ MuJoCo Simulation Loop (MultiPhys-style)
        ├── Scene setup:
        │     Ground plane → MuJoCo geom (box)
        │     Collision mesh → MuJoCo mesh geom (from DA3 GLB, V-HACD decomposed)
        │
        ├── Humanoid setup (via SMPLSim):
        │     SMPL params → MuJoCo XML (capsule-based humanoid)
        │     PD controllers on each joint
        │
        ├── Tracking loop (per-frame, forward in time):
        │     Target: GVHMR pose at frame t
        │     PD controller + learned residual drives joints toward target
        │     MuJoCo steps physics (contacts, friction, gravity)
        │     Record: actual pose, contact forces, penetration
        │
        ├── Post-processing:
        │     Map MuJoCo joint states back to SMPL params (via SMPLSim)
        │
        └─→ Physics-valid SMPL sequence + contact forces + stability metrics
```

### Why Each Component Is Feasible

1. **MultiPhys**: Released, runnable (`bash run_demo.sh`). Takes kinematic SMPL, runs MuJoCo with PD tracking, outputs physically-corrected motion. Demonstrated on CHI3D + Hi4D. Results: 7x less interpenetration, 5x less ground penetration.
2. **SMPLSim**: Released (Zhengyi Luo). Converts SMPL params → MuJoCo humanoid XML. Supports capsule-based (fast) and mesh-based (accurate) bodies. Handles SMPL/SMPL-H/SMPL-X.
3. **MuJoCo**: Apache-2.0, `pip install mujoco`. Full rigid-body dynamics. MuJoCo 3 adds SDF-based collisions for non-convex shapes. Contact forces, friction, gravity all handled natively.
4. **GVHMR**: Same as other options. Provides reference motion.
5. **DA3**: Same as other options. Scene geometry → MuJoCo collision bodies.

### Feed-Forward Nature

MuJoCo marches forward in time — no L-BFGS, no iterative optimization. The PD controller + physics engine jointly produce output in one pass through the sequence. This is "feed-forward" in the physics simulation sense.

The controller IS a learned network (trained on mocap data with MuJoCo). Options:
- **(a)** Use MultiPhys pretrained controller (works for walking/interaction they trained on)
- **(b)** Fine-tune on AMASS subsets matching target domain

### Why MultiPhys Over PHC+?

PhysHMR shows PHC+ makes foot sliding **worse** when used as post-processor (5.65mm → 12.71mm). MultiPhys is different:
- Designed for multi-person tracking with scene awareness (PHC+ is single-person)
- Uses MuJoCo (deterministic contacts) not Isaac Gym (GPU-parallel but less precise)
- Published results show clear penetration reduction (7x)
- Trained on close-interaction (CHI3D, Hi4D) where interpenetration is the main problem

### Risk Assessment

| Step | Risk | Mitigation |
|------|------|-----------|
| GVHMR + DA3 inference | **Low** | Same as other options |
| SMPLSim humanoid generation | **Low** — released, documented | Capsule approximation may miss some collisions |
| MultiPhys controller | **Medium** — pretrained on CHI3D/Hi4D only | Test on RICH/EMDB-2 first, fine-tune if needed |
| MuJoCo scene loading | **Medium** — DA3 mesh → convex decomposition (V-HACD) | Start with ground plane only, add mesh incrementally |
| **Controller domain gap** | **High** — may not generalize to arbitrary scenes/motions | Fine-tune on AMASS. Fallback: Option A. |
| MuJoCo → SMPL mapping | **Low** — SMPLSim handles both directions | Verify vertex accuracy |

### Targets

| Metric | GVHMR Baseline | Our Target |
|--------|---------------|------------|
| Foot Sliding | 3.0 mm | **< 2 mm** |
| Ground Penetration | ~2-5 mm | **< 0.5 mm** (MuJoCo enforces hard constraints) |
| Interpenetration (multi-person) | Uncontrolled | **7x reduction** (MultiPhys published) |
| PA-MPJPE | 36.2 mm | **< 41 mm** (some tracking error from PD control) |

### Implementation Plan (5 weeks)

#### Week 1: Environment + Component Setup

| Day | Task | Deliverable |
|-----|------|------------|
| 1 | Conda env: PyTorch 1.13, CUDA 11.7, MuJoCo 2.1.0 (MultiPhys requirement) | Working env |
| 2 | Clone + test MultiPhys on their demo data (`bash run_demo.sh`) | MultiPhys running |
| 3 | Install GVHMR + DA3 (may need separate conda env) | Both running |
| 4 | Install SMPLSim, generate MuJoCo humanoid from sample SMPL params | Working XML |
| 5 | Run GVHMR on test videos, verify output format compatibility with MultiPhys input | Format bridge working |

**Gate:** MultiPhys runs on demo data. GVHMR output feeds into MultiPhys.

#### Week 2: Scene Integration

| Day | Task | Deliverable |
|-----|------|------------|
| 1 | DA3 point cloud → RANSAC ground plane → MuJoCo ground geom (box) | Scene in MuJoCo |
| 2 | DA3 GLB mesh → convex decomposition (V-HACD via trimesh) → MuJoCo mesh geoms | Complex scene in MuJoCo |
| 3 | Run MultiPhys simulation with GVHMR reference + MuJoCo scene | First physics-corrected output |
| 4 | Visualize: overlay MuJoCo simulation on original video | Visual sanity check |
| 5 | Compare: foot sliding, penetration, PA-MPJPE vs raw GVHMR | Baseline metrics |

**Gate:** Simulation runs with scene geometry. Penetration visibly reduced.

#### Week 3: Controller Adaptation

| Day | Task | Deliverable |
|-----|------|------------|
| 1-2 | Evaluate pretrained controller on RICH and EMDB-2 sequences | Domain gap assessment |
| 3-4 | If controller fails: fine-tune on AMASS walking/running subsets with ground plane | Adapted controller |
| 5 | Ablation: ground-plane-only vs full-mesh collision | Scene complexity analysis |

**Gate:** Controller tracks GVHMR reference with < 5mm PA-MPJPE degradation.

#### Week 4: Evaluation

| Day | Task | Deliverable |
|-----|------|------------|
| 1-2 | Full evaluation on RICH, EMDB-2, 3DPW | Metrics tables |
| 3 | Multi-person evaluation on Hi4D (MultiPhys's strength) | Multi-person metrics |
| 4 | Contact force analysis: extract MuJoCo forces, compare with RICH GT | Contact quality |
| 5 | Cross-option comparison table: A vs B vs C | Comparison |

#### Week 5: Polish + Report

| Day | Task | Deliverable |
|-----|------|------------|
| 1-2 | Long video: sliding window with sim state handoff | Temporal scalability |
| 3 | Demo renders: MuJoCo visualization + contact force overlays | Demo videos |
| 4-5 | Technical report + CLI: `pact3d simulate --video input.mp4 --output corrected/` | Deliverables |

---

## Head-to-Head Comparison

| Dimension | Option A (Optimization) | Option B (Geometric) | Option C (Simulation) |
|-----------|:-:|:-:|:-:|
| **Correction method** | L-BFGS energy minimization | Closed-form geometric ops | MuJoCo forward physics sim |
| **Body tracker** | GVHMR | GVHMR | GVHMR |
| **Scene backbone** | DA3 | DA3 | DA3 |
| **Physics model** | Differentiable energy terms | None (geometric heuristics) | Full rigid-body dynamics |
| **Foot sliding target** | < 1 mm | < 2 mm | < 2 mm |
| **Penetration target** | < 1 mm (SDF) | < 1 mm (ground only) | < 0.5 mm (hard constraint) |
| **PA-MPJPE risk** | Low (< 2mm degradation) | Minimal | Medium (PD tracking error) |
| **Speed** | ~30-60s / 1K frames | **~1-2s / 1K frames** | ~10-30s / 1K frames |
| **Scene awareness** | Full (SDF collisions) | Ground plane only | Full (MuJoCo collisions) |
| **Multi-person** | Extend via SLAHMR | Single-person | **Native** (MultiPhys) |
| **Complexity** | High (6 loss terms + tuning) | **Low** (geometric ops) | Medium (MuJoCo setup + controller) |
| **Novel contribution** | PROX/LEMO losses + DA3 scene + GVHMR | Minimal (engineering baseline) | MultiPhys + DA3 (novel combination) |
| **Biggest risk** | Loss weight tuning | Limited correction capability | Controller domain gap |
| **Implementation** | 6 weeks | **4 weeks** | 5 weeks |

### Recommended Strategy

**Build in order: B → A → C.**

1. **Option B first** (weeks 1-4): Establishes shared infrastructure (GVHMR + DA3 + contact detection + evaluation + visualization). Produces first quantitative results in 2 weeks. The gap between geometric corrections and targets motivates Option A.

2. **Option A on top** (weeks 3-8, overlapping): Shares 80% of code with B (scene proxy, contact detection, evaluation). The only new code is the energy function + optimizer. B's results serve as the baseline to beat.

3. **Option C in parallel** (weeks 2-7): Independent MuJoCo track. Useful if multi-person support is needed or as a fundamentally different comparison point. Can share GVHMR + DA3 outputs from B.

---

## Shared Infrastructure (Build Once, Use in All Options)

```
pact3d/
├── scene/
│   ├── da3_inference.py       # DA3 point cloud + mesh extraction
│   ├── ground_plane.py        # RANSAC plane fitting (Open3D)
│   ├── collision_mesh.py      # GLB/PLY → trimesh, SDF computation
│   └── coordinate_align.py    # Align GVHMR gravity-view ↔ DA3 world frame
├── body/
│   ├── gvhmr_inference.py     # GVHMR wrapper
│   └── contact_detection.py   # Fused contact labels (GVHMR probs + geometric)
├── correct/
│   ├── geometric.py           # Option B: ground snap, penetration resolve, IK, smooth
│   ├── optimize.py            # Option A: energy minimization (LEMO-style)
│   └── simulate.py            # Option C: MuJoCo simulation loop
├── eval/
│   ├── metrics.py             # Foot sliding, penetration, PA-MPJPE, WA-MPJPE, drift
│   ├── datasets.py            # RICH, EMDB-2, 3DPW, Hi4D loaders
│   └── visualize.py           # Before/after rendering, contact heatmaps
└── cli.py                     # pact3d {correct,optimize,simulate} --video input.mp4
```

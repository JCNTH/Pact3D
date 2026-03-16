# Pact3D Implementation Plans

Three verified, end-to-end feasible pipeline options. Each component has been checked for actual code availability as of March 2026.

---

## Component Verification Summary

Before the plans: here's the ground truth on what's released.

### Body Trackers (all runnable today)

| Component | Repo | World Coords? | Contact? | License | VRAM |
|-----------|------|:---:|:---:|---------|------|
| **GVHMR** | [zju3dv/GVHMR](https://github.com/zju3dv/GVHMR) | Yes (gravity-view) | Yes (foot probs) | Non-commercial | ~4 GB |
| **WHAM** | [yohanshin/WHAM](https://github.com/yohanshin/WHAM) | Yes | Yes (foot contacts, 4-dim) | **MIT** | ~8 GB |
| **Human3R** | [fanegg/Human3R](https://github.com/fanegg/Human3R) | Yes (joint w/ scene) | No | Check repo | ~8 GB |
| **HMR2.0** | [shubham-goel/4D-Humans](https://github.com/shubham-goel/4D-Humans) | No (camera-relative) | No | **MIT** | ~8 GB |
| **SLAHMR** | [vye16/slahmr](https://github.com/vye16/slahmr) | Yes (multi-person) | No | **MIT** | ~16 GB |

### Scene Reconstruction (all runnable today)

| Component | Repo | Metric Scale? | Mesh Export? | License | VRAM |
|-----------|------|:---:|:---:|---------|------|
| **DA3-Metric-Large** | [ByteDance-Seed/Depth-Anything-3](https://github.com/ByteDance-Seed/Depth-Anything-3) | Yes (meters) | GLB, PLY | **Apache-2.0** (Large weights) | <12 GB |
| **DA3-Nested-Giant** | Same repo | Yes (meters) | GLB, PLY, 3DGS | CC BY-NC 4.0 (Giant weights) | <12 GB streaming |
| **VGGT** | [facebookresearch/vggt](https://github.com/facebookresearch/vggt) | Relative | COLMAP | CC BY-NC / Commercial ckpt | 8-40 GB |

### Physics / Optimization Tools (all runnable today)

| Component | Repo | What It Does | License | Key Deps |
|-----------|------|-------------|---------|----------|
| **LEMO** | [sanweiliti/LEMO](https://github.com/sanweiliti/LEMO) | Temporal optimization with scene collision + friction + smoothness prior | Research | SMPL-X, VPoser, AMASS |
| **PROX** | [mohamedhassanmus/prox](https://github.com/mohamedhassanmus/prox) | Per-frame SDF penetration + contact fitting | Research | Python 3.6 (old!), SMPL-X |
| **MultiPhys** | [nicolasugrinovic/multiphys](https://github.com/nicolasugrinovic/multiphys) | MuJoCo simulation loop for multi-person | Research | MuJoCo 2.1.0, PyTorch 1.13 |
| **PHC+** | [ZhengyiLuo/PHC](https://github.com/ZhengyiLuo/PHC) | RL humanoid controller | Research | Isaac Gym, MuJoCo |
| **MuJoCo** | `pip install mujoco` | Physics engine | **Apache-2.0** | None |
| **SMPLSim** | [ZhengyiLuo/SMPLSim](https://github.com/ZhengyiLuo/SMPLSim) | SMPL→MuJoCo XML | Research | MuJoCo |
| **Open3D** | `pip install open3d` | RANSAC plane fitting, point cloud ops | **MIT** | None |
| **trimesh** | `pip install trimesh python-fcl` | Mesh collision queries | **MIT** | python-fcl |

### NOT Released (do NOT depend on)

| Component | Status |
|-----------|--------|
| **PhysHMR** | Paper only. No code. Best approach but unusable. |
| **ZipMap** | Placeholder repo. "Code coming in weeks" since Jan 2026. |
| **SimPoE** | Never released. |
| **PACE** | No public repo. |

---

## Option A: Optimization-Based (LEMO-Style Energy Minimization)

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

### Why This Is Feasible

1. **GVHMR**: Released, runs on arbitrary video, outputs world-grounded SMPL + foot contacts. Demo: `python tools/demo/demo.py --video=input.mp4`. 0.28s for 1.4K frames.
2. **DA3-Metric-Large**: Released, Apache-2.0 (Large weights). Outputs metric point clouds in meters. `da3 predict --input video.mp4 --output out/ --export ply`. <12 GB VRAM.
3. **LEMO energy terms**: LEMO code is released and runnable. We extract the loss function design (scene SDF, friction, smoothness) but reimplement in modern PyTorch (LEMO uses Python 3.8 / CUDA 10.0). The math is well-documented in the paper and code.
4. **PROX fitting**: Released. We port the SDF penetration and contact loss terms. The old codebase (Python 3.6) is reference only — we reimplement the differentiable losses.
5. **Ground plane**: Open3D `segment_plane()` on DA3 point cloud. Trivial.
6. **Collision mesh**: DA3 exports GLB meshes directly. Or: Poisson reconstruction on PLY point cloud via Open3D. Then trimesh+FCL for collision queries.
7. **MuJoCo validation**: SMPLSim converts SMPL params → MuJoCo XML. `pip install mujoco`. Apache-2.0.
8. **VPoser prior**: Available from MPI (requires registration). Constrains body poses to plausible manifold.

### Feasibility Risk Assessment

| Step | Risk | Mitigation |
|------|------|-----------|
| GVHMR inference | **Low** — well-tested, Colab available | HuggingFace demo as fallback |
| DA3 point cloud | **Low** — straightforward CLI | DA3-Base (Apache-2.0) fallback |
| Ground plane RANSAC | **Trivial** — one function call | Manual plane if RANSAC fails |
| Scene SDF computation | **Medium** — need to voxelize mesh → SDF | Use `mesh_to_sdf` package or trimesh signed distance |
| Energy optimization | **Medium** — tuning loss weights | Start with LEMO's published weights, ablate |
| MuJoCo validation | **Low** — forward sim only, not control | SMPLSim handles SMPL→XML conversion |
| Coordinate alignment (GVHMR ↔ DA3) | **Medium** — different world frames | Align via gravity direction + ground plane normal |

### License Stack

| Component | License | Commercial? |
|-----------|---------|:-----------:|
| GVHMR | Non-commercial (ZJU) | No |
| DA3-Metric-Large | Apache-2.0 | **Yes** |
| MuJoCo | Apache-2.0 | **Yes** |
| Open3D | MIT | **Yes** |
| VPoser/SMPL-X | MPI research | No |
| Our optimization code | Ours | Yes |

**Overall: Non-commercial** due to GVHMR + VPoser. Swap GVHMR→WHAM (MIT) for commercial use (slight accuracy tradeoff).

### Implementation Plan (6 weeks)

#### Week 1: Environment + Baselines

| Day | Task | Deliverable |
|-----|------|------------|
| 1 | Set up conda env with GVHMR deps (PyTorch 2.3, CUDA 12.1) | Working env |
| 2 | Install DA3 (`pip install depth-anything-3`), download DA3-Metric-Large weights | DA3 inference working |
| 3 | Run GVHMR on 3 test videos (RICH, EMDB-2, custom) | SMPL .pkl outputs |
| 4 | Run DA3 on same videos, export PLY point clouds | Metric point clouds |
| 5 | Visualize GVHMR meshes + DA3 point clouds in same coordinate frame (Open3D) | Sanity check alignment |

**Gate:** GVHMR and DA3 both produce outputs. Bodies roughly align with scene geometry.

#### Week 2: Scene Proxy + Contact Detection

| Day | Task | Deliverable |
|-----|------|------------|
| 1 | Ground plane RANSAC from DA3 point cloud (Open3D `segment_plane`) | Plane coefficients (n, d) |
| 2 | Gravity alignment: rotate GVHMR world frame so gravity-view Y aligns with DA3 plane normal | Aligned coordinate system |
| 3 | Build collision mesh from DA3 output (GLB or Poisson reconstruction) | trimesh Trimesh object |
| 4 | Implement contact detection: foot vertex height < threshold AND velocity < threshold | Per-frame binary contact labels |
| 5 | Fuse with GVHMR's predicted contact probabilities (weighted average) | Robust contact labels |

**Gate:** Contact labels match visual ground truth on test videos. Ground plane is correct.

#### Week 3: Energy Function + Optimization Loop

| Day | Task | Deliverable |
|-----|------|------------|
| 1 | Implement `E_contact`: differentiable foot-to-surface distance, active only during contact frames | Loss function |
| 2 | Implement `E_penetration`: scene SDF query for all body vertices, penalize negative values | Loss function |
| 3 | Implement `E_friction`: horizontal velocity penalty during contact. `E_smooth`: jerk penalty | Loss functions |
| 4 | Implement `E_stability`: project CoM onto support polygon, penalize distance to boundary | Loss function |
| 5 | Combine into total energy, optimize with L-BFGS (PyTorch `torch.optim.LBFGS`). Optimize over SMPL pose + translation deltas (NOT shape). | Working optimizer |

**Optimization variables:** Per-frame additive corrections Δθ (pose) and Δt (translation) on top of GVHMR initialization.

**Gate:** Optimizer converges. Foot sliding and penetration metrics improve on test clips.

#### Week 4: MuJoCo Validation + Tuning

| Day | Task | Deliverable |
|-----|------|------------|
| 1 | SMPLSim: convert SMPL params → MuJoCo humanoid XML | Working MuJoCo model |
| 2 | Forward-simulate corrected motion in MuJoCo, record contact forces and stability | Validation metrics |
| 3 | Compare MuJoCo contacts vs our contact labels — flag disagreements | Diagnostic report |
| 4 | Ablation study: toggle each energy term, measure impact on foot sliding / penetration / PA-MPJPE | Ablation table |
| 5 | Tune loss weights on RICH dataset (has vertex contact GT) | Final hyperparameters |

**Gate:** MuJoCo forward sim confirms physical plausibility. No PA-MPJPE degradation > 2mm.

#### Week 5: Evaluation + Robustness

| Day | Task | Deliverable |
|-----|------|------------|
| 1-2 | Run on RICH test set — compute foot sliding, ground penetration, PA-MPJPE, WA-MPJPE | Metrics table |
| 3 | Run on EMDB-2 — same metrics + trajectory drift | Metrics table |
| 4 | Run on 3DPW — standard benchmark comparison | Metrics table |
| 5 | Temporal chunking for long videos (>500 frames): overlapping windows + stitching | Working on long videos |

**Gate:** Foot sliding < 1mm, penetration < 1mm, no PA-MPJPE degradation.

#### Week 6: Polish + Report

| Day | Task | Deliverable |
|-----|------|------------|
| 1-2 | Demo renders: before/after visualization with ground contact heatmaps | Demo videos |
| 3 | Failure case analysis: identify when optimization makes things worse | Failure catalog |
| 4 | Technical report with architecture, ablations, comparisons | Report draft |
| 5 | Package code: `pact3d optimize --video input.mp4 --output corrected/` | CLI tool |

---

## Option B: Feed-Forward Geometric Correction (No Optimization Loop)

### Architecture

```
Video
  ├─→ WHAM ─→ SMPL poses + world trajectory + foot contacts (4-dim)
  ├─→ DA3-Metric-Large ─→ metric point cloud + ground plane
  │
  └─→ Deterministic Geometric Correction (no iterative optimization)
        ├── Ground plane from DA3 (RANSAC)
        ├── Contact labels from WHAM (thresholded foot contact probabilities)
        ├── Corrections applied sequentially per frame:
        │     1. Ground snap: translate body so contact feet touch ground plane
        │     2. Penetration resolve: project penetrating vertices along surface normal
        │     3. Contact freeze: zero horizontal velocity of contact feet (IK adjustment)
        │     4. Temporal smooth: Savitzky-Golay or Gaussian filter on joint trajectories
        │
        └─→ Corrected SMPL sequence + contact labels
```

### Why This Is Feasible

1. **WHAM**: Released, **MIT licensed**, runnable today. `python demo.py --video input.mov --save_pkl`. Outputs SMPL params in world coordinates + 4-dim foot contact predictions (left/right heel/toe). This is the only body tracker that gives us contact for free.
2. **DA3-Metric-Large**: Same as Option A. Metric point cloud → ground plane via RANSAC.
3. **Ground snap**: Trivial geometry — during contact frames, translate root so foot vertices lie on ground plane. Closed-form solution (no optimization).
4. **Penetration resolve**: For each body vertex below ground plane, project to plane surface along normal. O(V) per frame, V=6890 for SMPL.
5. **Contact freeze (IK)**: When foot is in contact, adjust ankle/knee angles via analytical 2-joint IK to keep foot stationary while root moves. Well-studied, closed-form for leg chains.
6. **Temporal smoothing**: `scipy.signal.savgol_filter` on joint angle trajectories. One line of code.

### Why Feed-Forward?

No iterative solver. Every correction is a closed-form geometric operation applied once per frame (or once per sequence for smoothing). This means:
- **Deterministic**: Same input always produces same output
- **Fast**: O(N × V) where N = frames, V = vertices. No convergence waiting.
- **Debuggable**: Each correction can be visualized and toggled independently
- **No hyperparameters to tune** (beyond contact threshold and smoothing window)

### Feasibility Risk Assessment

| Step | Risk | Mitigation |
|------|------|-----------|
| WHAM inference | **Low** — Colab + Docker available | MIT license, well-maintained |
| DA3 point cloud | **Low** — same as Option A | |
| Ground plane | **Trivial** | |
| Ground snap | **Low** — simple geometry | Handle multi-surface (stairs) with local plane fitting |
| Penetration resolve | **Low** — vertex projection | May introduce artifacts at high-penetration frames |
| Contact IK | **Medium** — analytical IK for SMPL leg chain | Use damped least-squares if analytical fails |
| Temporal smoothing | **Trivial** — scipy | Window size affects latency vs smoothness |
| Coordinate alignment (WHAM ↔ DA3) | **Medium** — WHAM uses DPVO camera, DA3 has own poses | Align via ground plane normal matching |

### Limitations (Honest Assessment)

- **No scene-aware correction beyond ground plane.** Won't handle chairs, walls, or objects. Only ground contact.
- **IK can introduce knee popping** if corrections are large. Mitigated by smoothing.
- **No energy-based trade-offs.** Can't balance "stay close to observation" vs "satisfy physics." Each correction is applied greedily.
- **Likely won't hit <1mm foot sliding.** Realistic target: **<3mm** (matches WHAM's built-in contact trajectory).
- **PhysHMR shows optimization beats two-stage.** This approach is fundamentally two-stage. But it's fast, simple, and the baseline.

### License Stack

| Component | License | Commercial? |
|-----------|---------|:-----------:|
| WHAM | **MIT** | **Yes** |
| DA3-Metric-Large | **Apache-2.0** | **Yes** |
| Open3D | **MIT** | **Yes** |
| scipy | **BSD** | **Yes** |
| Our correction code | Ours | **Yes** |

**Overall: Fully commercial.** Every component is MIT/Apache-2.0/BSD.

### Implementation Plan (4 weeks)

#### Week 1: Environment + Baselines

| Day | Task | Deliverable |
|-----|------|------------|
| 1 | Set up conda env with WHAM deps (PyTorch 1.11, CUDA 11.3) | Working env |
| 2 | Install DA3, download weights | DA3 running |
| 3 | Run WHAM on 3 test videos, inspect `.pkl` outputs — verify `contact`, `pose_world`, `trans_world`, `feet` fields | Confirmed output format |
| 4 | Run DA3 on same videos, export PLY | Metric point clouds |
| 5 | Coordinate alignment: WHAM world ↔ DA3 world. Match ground plane normals. | Aligned frames |

**Gate:** WHAM bodies visible in DA3 point clouds. Contact labels look correct.

#### Week 2: Geometric Corrections

| Day | Task | Deliverable |
|-----|------|------------|
| 1 | Ground plane RANSAC (Open3D). Implement ground snap: during contact, shift root so min foot vertex height = 0 relative to plane. | `ground_snap()` function |
| 2 | Penetration resolve: for non-contact frames, project vertices below plane to plane surface. | `resolve_penetration()` function |
| 3 | Contact freeze via analytical IK: when foot contacts ground, solve for ankle + knee angles that keep foot stationary as root translates. Use SMPL kinematic chain (pelvis→hip→knee→ankle→foot). | `contact_ik()` function |
| 4 | Temporal smoothing: Savitzky-Golay filter (window=11, order=3) on joint angles. Preserve contact constraints post-smoothing. | `temporal_smooth()` function |
| 5 | Combine all corrections into pipeline. Run on test videos. Visualize before/after. | Working pipeline |

**Gate:** Visible improvement in foot contact quality. No gross artifacts.

#### Week 3: Evaluation

| Day | Task | Deliverable |
|-----|------|------------|
| 1-2 | RICH dataset: foot sliding, ground penetration, PA-MPJPE | Metrics |
| 3 | EMDB-2: WA-MPJPE, trajectory drift | Metrics |
| 4 | 3DPW: standard benchmark | Metrics |
| 5 | Comparison table: WHAM alone vs WHAM + our corrections vs Option A | Comparison |

**Gate:** Foot sliding improves over raw WHAM. PA-MPJPE does not degrade.

#### Week 4: Polish

| Day | Task | Deliverable |
|-----|------|------------|
| 1-2 | Multi-surface support: detect stairs/ramps via local plane fitting within foot neighborhood | Extended ground model |
| 3 | Edge cases: fast motion, occlusion, camera shake | Robustness |
| 4 | CLI: `pact3d correct --video input.mp4 --output corrected/` | CLI tool |
| 5 | Technical report | Report |

---

## Option C: Simulation-in-the-Loop (MultiPhys-Style MuJoCo Correction)

### Architecture

```
Video
  ├─→ GVHMR ─→ SMPL poses + world trajectory (reference motion)
  ├─→ DA3-Metric-Large ─→ metric point cloud + ground plane
  │
  └─→ MuJoCo Simulation Loop (MultiPhys-style)
        ├── Scene setup:
        │     Ground plane → MuJoCo geom (box)
        │     Collision mesh → MuJoCo mesh geom (from DA3 GLB)
        │
        ├── Humanoid setup (via SMPLSim):
        │     SMPL params → MuJoCo XML (capsule-based humanoid)
        │     PD controllers on each joint
        │
        ├── Tracking loop (per-frame):
        │     Target: GVHMR pose at frame t
        │     PD controller drives joints toward target
        │     MuJoCo steps physics (contacts, friction, gravity)
        │     Record: actual pose, contact forces, penetration
        │
        ├── Post-processing:
        │     Extract physically-valid trajectory from simulation
        │     Map MuJoCo joint states back to SMPL params
        │
        └─→ Physics-valid SMPL sequence + contact forces + stability metrics
```

### Why This Is Feasible

1. **MultiPhys is released and runnable.** `bash run_demo.sh` on demo data. It does exactly this: takes kinematic SMPL output, runs MuJoCo simulation with PD tracking, outputs physically-corrected motion. The code demonstrates the full pipeline on CHI3D and Hi4D datasets.
2. **SMPLSim**: Released by the same group (Zhengyi Luo). Converts SMPL parameters to MuJoCo humanoid XML automatically. This is the bridge between SMPL and MuJoCo.
3. **MuJoCo**: Apache-2.0, `pip install mujoco`. Handles all physics: rigid body dynamics, contact forces, friction, gravity. No custom physics code needed.
4. **GVHMR**: Same as Option A. Provides the reference motion to track.
5. **DA3**: Same as Options A/B. Provides scene geometry for MuJoCo collision bodies.

### How MultiPhys Actually Works (from their code)

1. **Input**: Kinematic SMPL sequences from any tracker (they use SLAHMR)
2. **Humanoid**: 24-joint capsule-based MuJoCo body generated from SMPL shape
3. **Controller**: Learned residual PD controller (neural network predicts torque residuals)
4. **Simulation**: MuJoCo steps forward, applying PD torques + gravity + contacts
5. **Output**: Physically-simulated trajectory that tracks the kinematic reference while respecting physics
6. **Key result**: 7x less interpenetration, 5x less ground penetration vs kinematic input

### Feed-Forward Nature

This IS feed-forward in the physics sense: MuJoCo runs a forward simulation. There's no iterative optimization like L-BFGS. The simulation marches forward in time, and the PD controller + physics engine jointly produce the output. One pass through the sequence.

However, MultiPhys's controller IS a learned network (trained on motion capture data with MuJoCo). You need either:
- (a) Use their pretrained controller (works for walking/interaction scenarios they trained on)
- (b) Retrain on your target domain (requires motion capture data + MuJoCo training loop)

### Feasibility Risk Assessment

| Step | Risk | Mitigation |
|------|------|-----------|
| GVHMR inference | **Low** | Same as Option A |
| DA3 scene geometry | **Low** | Same as Option A |
| SMPLSim humanoid generation | **Low** — released, documented | Capsule approximation may miss some collisions |
| MultiPhys controller | **Medium** — pretrained on CHI3D/Hi4D (close interaction). May not generalize to arbitrary scenes. | Test on RICH/EMDB-2 first. Retrain if needed. |
| MuJoCo scene loading | **Medium** — DA3 mesh → MuJoCo geom requires convex decomposition (V-HACD) | Use ground plane only initially, add mesh later |
| Controller domain gap | **High** — MultiPhys trained on specific datasets with specific motion types | May need fine-tuning. Fallback: Option A optimization. |
| MuJoCo → SMPL mapping | **Low** — SMPLSim handles both directions | Verify vertex-level accuracy |

### Why MultiPhys Over PHC+?

PhysHMR shows PHC+ **makes foot sliding worse** (5.65mm → 12.71mm) when used as post-processor. But MultiPhys is different:
- MultiPhys is designed specifically for multi-person tracking with scene awareness
- MultiPhys uses MuJoCo (deterministic contacts), PHC+ uses Isaac Gym (GPU-parallel but less precise)
- MultiPhys's evaluation shows clear improvement on penetration metrics (7x reduction)
- MultiPhys was trained on close-interaction scenarios (CHI3D, Hi4D) where interpenetration is the primary problem

The risk is that MultiPhys may not improve foot sliding as much as penetration (its primary focus). Option A's optimization approach explicitly targets foot sliding with contact+friction terms.

### License Stack

| Component | License | Commercial? |
|-----------|---------|:-----------:|
| GVHMR | Non-commercial | No |
| DA3-Metric-Large | Apache-2.0 | Yes |
| MultiPhys | Not specified (check repo) | Unclear |
| MuJoCo | Apache-2.0 | Yes |
| SMPLSim | Research | No |

**Overall: Non-commercial** due to GVHMR + SMPLSim.

### Implementation Plan (5 weeks)

#### Week 1: Environment + Component Setup

| Day | Task | Deliverable |
|-----|------|------------|
| 1 | Set up conda env: PyTorch 1.13, CUDA 11.7, MuJoCo 2.1.0 (MultiPhys requirement) | Working env |
| 2 | Clone + test MultiPhys on their demo data (`bash run_demo.sh`) | MultiPhys running |
| 3 | Install GVHMR + DA3 in same environment (may need separate envs) | Both running |
| 4 | Install SMPLSim, generate MuJoCo humanoid from sample SMPL params | Working XML |
| 5 | Run GVHMR on test videos, verify SMPL output format compatibility with MultiPhys input | Format bridge working |

**Gate:** MultiPhys runs on demo data. GVHMR output can feed into MultiPhys.

#### Week 2: Scene Integration

| Day | Task | Deliverable |
|-----|------|------------|
| 1 | DA3 point cloud → RANSAC ground plane → MuJoCo ground geom (box at plane height) | Scene in MuJoCo |
| 2 | DA3 GLB mesh → convex decomposition (V-HACD via trimesh) → MuJoCo mesh geoms | Complex scene in MuJoCo |
| 3 | Run MultiPhys simulation with GVHMR reference + MuJoCo scene | First physics-corrected output |
| 4 | Visualize: overlay MuJoCo simulation on original video | Visual sanity check |
| 5 | Compare MultiPhys output vs GVHMR input: foot sliding, penetration, PA-MPJPE | Baseline metrics |

**Gate:** MuJoCo simulation runs with scene geometry. Penetration visibly reduces.

#### Week 3: Controller Adaptation

| Day | Task | Deliverable |
|-----|------|------------|
| 1-2 | Evaluate pretrained MultiPhys controller on RICH and EMDB-2 sequences | Domain gap assessment |
| 3-4 | If controller fails: fine-tune on AMASS walking/running subsets with ground plane | Adapted controller |
| 5 | Ablation: ground-plane-only vs full-mesh collision | Scene complexity analysis |

**Gate:** Controller tracks GVHMR reference with <5mm PA-MPJPE degradation.

#### Week 4: Evaluation

| Day | Task | Deliverable |
|-----|------|------------|
| 1-2 | Full evaluation on RICH, EMDB-2, 3DPW | Metrics tables |
| 3 | Multi-person evaluation on Hi4D (MultiPhys's strength) | Multi-person metrics |
| 4 | Contact force analysis: extract MuJoCo contact forces, compare with RICH GT | Contact quality |
| 5 | Comparison table: Option A vs B vs C | Cross-option comparison |

#### Week 5: Polish + Report

| Day | Task | Deliverable |
|-----|------|------------|
| 1-2 | Long video support: sliding window with sim state handoff | Temporal scalability |
| 3 | Demo renders: MuJoCo visualization + contact force overlays | Demo videos |
| 4-5 | Technical report + CLI packaging | Deliverables |

---

## Head-to-Head Comparison

| Dimension | Option A (Optimization) | Option B (Feed-Forward Geometric) | Option C (MuJoCo Simulation) |
|-----------|:-:|:-:|:-:|
| **Approach** | Energy minimization (L-BFGS) | Closed-form geometric corrections | Forward physics simulation |
| **Physics model** | Differentiable energy terms | None (geometric heuristics) | Full rigid-body dynamics |
| **Foot sliding target** | <1mm | <3mm | <2mm (estimated) |
| **Penetration target** | <1mm | <1mm (ground only) | <1mm (full scene) |
| **Speed** | ~30-60s / 1K frames (optimization) | ~1-2s / 1K frames (no iteration) | ~10-30s / 1K frames (MuJoCo) |
| **Commercial license?** | No (GVHMR) | **Yes (all MIT/Apache)** | No (GVHMR) |
| **Scene awareness** | Full (SDF collisions) | Ground plane only | Full (MuJoCo collisions) |
| **Multi-person** | With SLAHMR extension | WHAM is single-person only | Yes (MultiPhys native) |
| **Complexity** | High (custom losses, tuning) | Low (geometric ops) | Medium (MuJoCo setup) |
| **Novel contribution** | PROX/LEMO + DA3 scene + modern tracker | Minimal (engineering) | MultiPhys + DA3 scene (novel combination) |
| **Implementation time** | 6 weeks | 4 weeks | 5 weeks |
| **Biggest risk** | Loss weight tuning, coordinate alignment | Limited correction capability | Controller domain gap |

### Recommended Strategy

**Start with Option B** (2 weeks to first results, establishes baselines and infrastructure).
**Then build Option A** on top (shared DA3 + contact detection code, adds optimization layer).
**Option C in parallel** if multi-person is required or as comparison.

Options A and B share 80% of their infrastructure (DA3 scene, contact detection, evaluation code, visualization). The key difference is the correction layer: Option B applies geometric fixes, Option A optimizes an energy function. Building B first de-risks A by validating the upstream components.

---

## Shared Infrastructure (Build Once, Use in All Options)

```
pact3d/
├── scene/
│   ├── da3_inference.py       # DA3 point cloud + mesh extraction
│   ├── ground_plane.py        # RANSAC plane fitting (Open3D)
│   ├── collision_mesh.py      # GLB/PLY → trimesh, SDF computation
│   └── coordinate_align.py    # Align tracker world frame ↔ DA3 world frame
├── body/
│   ├── gvhmr_inference.py     # GVHMR wrapper
│   ├── wham_inference.py      # WHAM wrapper
│   └── contact_detection.py   # Fused contact labels (tracker + geometric)
├── correct/
│   ├── geometric.py           # Option B: ground snap, penetration resolve, IK
│   ├── optimize.py            # Option A: energy minimization (LEMO-style)
│   └── simulate.py            # Option C: MuJoCo simulation loop
├── eval/
│   ├── metrics.py             # Foot sliding, penetration, PA-MPJPE, drift
│   ├── datasets.py            # RICH, EMDB-2, 3DPW loaders
│   └── visualize.py           # Before/after rendering
└── cli.py                     # pact3d {correct,optimize,simulate} --video input.mp4
```

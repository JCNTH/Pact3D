# Pact3D: Physics-Aware Contact Tracking in 3D
## Slide Deck for Shirley

---

## Slide 1: Title

# Pact3D
### Physics-Aware Contact Tracking in 3D

**Pitch:** Take a strong body tracker, add a lightweight physics layer, get simulation-ready human motion from monocular video.

- No training required
- Runs on a single consumer GPU
- 8-week project timeline

---

## Slide 2: The Problem

### Current Body Trackers Are Good — But Not Physical

| Issue | Example | Impact |
|-------|---------|--------|
| Foot skating | 3.0–4.4mm sliding | Motion looks "floaty" |
| Ground penetration | Bodies clip through floors | Can't use in simulation |
| Temporal jitter | 12.8–22.5 units | Unstable, twitchy output |
| No sim readiness | Raw SMPL params only | Can't load into physics engines |

**Even the best tracker (GVHMR) has these problems.**

The missing piece: **physics constraints** (gravity, contact, friction, collisions).

---

## Slide 3: Why Physics Constraints Work

### Evidence from 7+ Papers

| Study | What Was Added | Result |
|-------|---------------|--------|
| MultiPhys (CVPR'24) | MuJoCo simulation | **7x less penetration** |
| MultiPhys | Ground plane contact | **5x less ground pen.** |
| CRISP (arXiv'25) | Planar scene + RL | **8x lower failure rate** |
| PhysDiff (ICCV'23) | Physics in diffusion | **86% less physical error** |
| PROX (ICCV'19) | SDF + contact terms | **24% better V2V** |

**Key insight:** Physics doesn't just look better — it **improves accuracy too.**

MultiPhys: W-MPJPE 177.1 → 174.7mm (physics correction *helped* pose estimation)

---

## Slide 4: Critical Design Lesson

### PhysHMR (SIGGRAPH Asia'25) — Two-Stage Can Hurt

| Pipeline | Foot Sliding |
|----------|-------------|
| GVHMR alone | 5.65 mm |
| GVHMR + RL post-correction (PHC+) | **12.71 mm** (worse!) |
| PhysHMR (end-to-end) | **4.60 mm** (best) |

**Why?** RL balance-recovery creates new limb artifacts.

**Our approach:** Optimization-based energy minimization (PROX/LEMO style), not RL post-processing. Avoids this failure mode.

---

## Slide 5: Body Tracker — Which One?

### Camera-Space Accuracy (3DPW, mm, lower = better)

| Method | PA-MPJPE | MPJPE | World? | Multi? | License |
|--------|----------|-------|--------|--------|---------|
| GLAMR '22 | 51.1 | — | Yes | No | NVIDIA NC |
| HMR 2.0 '23 | 44.4 | 69.8 | No | No | MIT |
| WHAM '24 | 35.9 | 57.8 | Yes | No | Custom |
| **GVHMR '24** | **36.2** | **55.6** | **Yes** | No | Custom |
| **Human3R '25** | 44.1 | 71.2 | **Yes** | **Yes** | **MIT** |
| PromptHMR '25 | **35.5** | — | Yes | No | Available |

---

## Slide 6: Body Tracker — World-Grounded

### EMDB-2 (mm, lower = better)

| Method | WA-MPJPE | W-MPJPE | Jitter | Foot Slide | Speed |
|--------|---------|---------|--------|------------|-------|
| GLAMR | 280.8 | 726.6 | 46.3 | 20.7 | Slow |
| SLAHMR | 326.9 | 776.1 | 31.3 | 14.5 | ~4 hrs/1K fr |
| WHAM | 135.6 | 354.8 | 22.5 | 4.4 | ~5s/1K fr |
| **GVHMR** | **111.0** | **276.5** | **16.7** | **3.5** | **0.28s/1.4K fr** |
| **Human3R** | **112.2** | **267.9** | — | — | **15 FPS e2e** |

---

## Slide 7: Recommendation — Two-Track

### Primary: GVHMR
- Best accuracy + speed
- Lowest foot sliding (3.0mm) and jitter (12.8)
- Gravity-view coordinates are physics-friendly
- ~5000 FPS core network

### Alternative: Human3R
- Only method with multi-person + scene + camera in **one forward pass**
- MIT licensed (publication-safe)
- 15 FPS, 8 GB VRAM
- Its explicit weaknesses (penetration, no physics) = exactly what we fix

---

## Slide 8: Scene Geometry — Why Depth Anything 3

### Capabilities Matrix

| Feature | DA3 | Metric3D v2 | CUT3R | VGGT | ZipMap |
|---------|-----|------------|-------|------|--------|
| Metric depth | Yes | **Best** | Yes | Yes | No (relative) |
| Camera poses | **Yes** | No | Yes | Yes | Yes |
| Pointmaps | **Yes** | No | Yes | Yes | Yes |
| Streaming video | **Yes (<12GB)** | No | Yes | No | No (batch) |
| Code released | **Yes** | Yes | Yes | Yes | **No** |
| Consumer GPU | **Yes** | Yes | Yes | Tight | **No (H100)** |
| License | **Apache-2.0** | Apache-2.0 | CC BY-NC-SA | Custom | Unreleased |

### Why Not ZipMap?
- **No metric depth** — we need real-world scale (meters) for physics constraints (ground plane, SDF penetration). ZipMap gives relative reconstruction.
- **Code unreleased** — CVPR 2026 paper, not yet available. DA3 is shipped and tested.
- **Wrong primitive** — ZipMap reconstructs static scenes from unordered image collections. We need per-frame metric depth from streaming video.
- **Hardware** — ZipMap benchmarks on H100. DA3 runs at 78 FPS on RTX 3090/4090.
- **Overkill** — Full scene reconstruction when we only need a ground plane (RANSAC) + collision mesh.

**ZipMap is the right tool for building a full 3DGS environment. DA3 is the right tool for per-frame physics constraints on body motion.**

### Runtime

| Model | FPS | VRAM | Long video? |
|-------|-----|------|-------------|
| **DA3-Large** | **78** | **<12 GB** | **Any length** |
| DA3-Small | 161 | ~5 GB | Any length |
| VGGT | ~60 | 8-40+ GB | ~60 frames max |
| ZipMap | 75 | H100 required | Batch only |

---

## Slide 9: Proposed Architecture

```
Monocular RGB Video
       |
       +---> Body Tracker (GVHMR / Human3R)
       |       -> SMPL(-X) poses + world trajectory
       |
       +---> Scene Backbone (DA3-Metric-Large)
       |       -> Metric depth + pointmaps + camera poses
       |
       +---> Physics Refinement Layer (optimization-based)
               |
               +-- Ground Plane    (RANSAC on pointmap)
               +-- Collision Mesh  (pointmap -> mesh)
               +-- Contact Detection (foot velocity + proximity)
               |
               +-- Energy Minimization:
               |     E_contact      pin feet to surface        (PROX)
               |     E_penetration  SDF non-intersection       (PROX)
               |     E_friction     no sliding during contact  (LEMO)
               |     E_stability    CoM/CoP balance            (IPMAN)
               |     E_smooth       temporal jerk penalty      (LEMO)
               |
               +-- MuJoCo Validation (verify, don't correct)
               |
               -> Simulation-ready motion + contact labels
```

### Why This Physics Approach

**Optimization-based (PROX/LEMO style), NOT RL post-correction.**

PhysHMR (SigAsia'25) proved that RL post-correction **makes things worse**: GVHMR alone gets 5.65mm foot sliding, but adding PHC+ RL correction degrades it to 12.71mm. RL balance-recovery introduces new limb artifacts.

Instead, we use **differentiable energy minimization** — directly optimize SMPL parameters against physical loss terms. This is:
- **Proven:** PROX (24% V2V improvement), LEMO (eliminates skating), IPMAN (biomechanical stability)
- **Training-free:** No RL policy to train, no simulator-in-the-loop during correction
- **Composable:** Each energy term is independent, ablatable, and has a clear physical meaning
- **Safe:** Constrained optimization can't diverge the way RL rollouts can

**MuJoCo role:** Validation only (verify the output is physically simulable), not correction. This avoids the two-stage failure mode PhysHMR identified.

### Physics Energy Terms — Sources

| Term | What It Does | From | Evidence |
|------|-------------|------|----------|
| E_contact | Pin contact vertices to nearest surface | PROX (ICCV'19) | 24% V2V improvement |
| E_penetration | SDF-based body-scene non-intersection | PROX (ICCV'19) | Core of scene-aware HMR |
| E_friction | Zero velocity on contact vertices | LEMO (ICCV'21) | Eliminates skating without simulator |
| E_stability | Center of mass over support polygon | IPMAN (CVPR'23) | Biomechanically grounded balance |
| E_smooth | Minimize acceleration/jerk over time | LEMO (ICCV'21) | Temporal coherence, reduces jitter |

---

## Slide 10: What Makes This Different

### vs. MultiPhys (RL post-correction)
- We use **optimization**, not RL — avoids balance-recovery artifacts
- We add **scene geometry** (not just ground plane)

### vs. PROX/LEMO (optimization-based)
- We use **modern body trackers** (GVHMR/Human3R, not old SMPLify)
- We add **metric depth** for real-world scale
- We run on **video** (not just single frames)

### vs. PhysHMR (end-to-end)
- We're **training-free** — compose pretrained models
- We can swap components as better ones emerge

---

## Slide 11: Evaluation Plan

### Primary Dataset: RICH
- Scene scans + vertex contact GT + reliable global coords
- Enables evaluating contact, penetration, sliding, and trajectory simultaneously

### Targets

| Metric | Current SOTA | Our Target |
|--------|-------------|------------|
| Foot Sliding | 3.0 mm (GVHMR) | **< 1 mm** |
| Ground Penetration | ~2-5 mm (estimated) | **< 1 mm** |
| Inter-body Penetration | 18.7 mm (MultiPhys) | **< 20 mm** |
| PA-MPJPE | 36.2 mm (GVHMR) | **No degradation** |

### Supporting Datasets
- **EMDB-2** — World trajectory accuracy, drift
- **3DPW** — Standard benchmark comparability
- **Hi4D** — Multi-person close interaction

---

## Slide 12: Timeline (8 Weeks)

| Week | Focus | Risk |
|------|-------|------|
| **1** | Set up environment, run GVHMR + DA3 on test videos | Low |
| **2** | Ground plane RANSAC, gravity alignment, collision mesh | Low |
| **3** | Contact detection (foot velocity + proximity), loss terms | Low |
| **4** | MuJoCo integration, optimize root + feet | Medium |
| **5** | Hand/object non-penetration, primitive fitting | Medium |
| **6** | Full eval on RICH, EMDB-2, 3DPW + ablations | Low |
| **7** | Robustness: chunking, stitching, edge cases | Medium |
| **8** | Demo renders, metrics tables, technical report | Low |

**Weeks 1-4 = core value (ground contact)**
**Weeks 5+ = stretch goals (HOI, robustness)**

---

## Slide 13: Compute Requirements

| Component | VRAM | Time / 1K frames |
|-----------|------|-------------------|
| GVHMR (core) | ~4 GB | ~0.2 sec |
| Human3R | ~8 GB | ~67 sec |
| DA3-Metric-L | <12 GB | ~13 sec |
| MuJoCo optimization | CPU | ~10-30 sec |
| **Total pipeline** | **< 16 GB** | **< 2 min** |

**Runs on a single RTX 3090 / 4090.**

---

## Slide 14: License-Safe Stack

| Component | License | Role |
|-----------|---------|------|
| Human3R | **MIT** | Body + scene (preferred) |
| DA3 | **Apache-2.0** | Depth / pointmaps |
| MuJoCo | **Apache-2.0** | Physics engine |
| Open3D | **MIT** | Point cloud processing |
| PyTorch | **BSD** | Optimization backend |

Fully permissive for publication and commercial use (Human3R path).

---

## Slide 15: Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| DA3 depth too noisy | Plane-only proxy; physics corrects residual |
| MuJoCo integration complex | Start ground-only; MultiPhys as reference |
| GVHMR license issue | Fall back to Human3R (MIT) |
| Physics degrades accuracy | Evidence says it helps; ablate each term |
| Week 5 HOI too ambitious | HOI is stretch goal; core is weeks 1-4 |

---

## Slide 16: Summary

### Pact3D = Body Tracker + Scene Geometry + Physics Layer

1. **Feasible:** No training, pretrained models, 8 weeks, single GPU
2. **Impactful:** Targets the #1 gap in current trackers (physical plausibility)
3. **Evidence-backed:** 7+ papers show physics improves both plausibility AND accuracy
4. **Publication-ready:** MIT/Apache stack, clear benchmarks, novel integration
5. **Extensible:** Modular — swap any component as better ones emerge

### The Core Claim
> Physics constraints are the highest-impact, most feasible addition to existing body trackers. They are well-understood, training-free, and consistently improve both plausibility and accuracy.

---

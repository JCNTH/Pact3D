# Pact3D Research

## Table of Contents

- [Part 1: Physics-Aware Contact Tracking](#part-1-physics-aware-contact-tracking)
- [Part 2: NL Video Editor Subproject](#part-2-nl-video-editor-subproject)

---

# Part 1: Physics-Aware Contact Tracking

## Project Thesis

**Goal:** World-grounded, physics-aware human tracking from monocular video.

**Core insight:** The best "physics enablement" wins are not new networks, but constraints that remove degenerate solutions — floating feet, drift, scale ambiguity, interpenetration.

**Architecture:** Vision proposes, Physics refines.
- **Body backbone:** GVHMR / Human3R (per-frame SMPL meshes in world coords)
- **Scene backbone:** Depth Anything 3 (metric depth + pointmaps + camera poses)
- **Physics layer:** MuJoCo (contact + penetration + slip correction)
- **Output:** World-frame body trajectory + contact labels + penetration/slip metrics

---

## Body Tracker Selection

### Camera-Space Accuracy (3DPW, mm)

| Method | Year | PA-MPJPE | MPJPE | World? | Multi? | License |
|--------|------|----------|-------|--------|--------|---------|
| GLAMR | 2022 | 51.1 | — | Yes | No | NVIDIA NC |
| HMR 2.0 | 2023 | 44.4 | 69.8 | No | No | MIT |
| WHAM | 2024 | 35.9 | 57.8 | Yes | No | Custom |
| **GVHMR** | **2024** | **36.2** | **55.6** | **Yes** | No | Custom |
| **Human3R** | **2025** | 44.1 | 71.2 | **Yes** | **Yes** | **MIT** |
| PromptHMR | 2025 | **35.5** | — | Yes | No | Available |

### World-Grounded (EMDB-2, mm)

| Method | WA-MPJPE | W-MPJPE | Jitter | Foot Slide | Speed |
|--------|---------|---------|--------|------------|-------|
| GLAMR | 280.8 | 726.6 | 46.3 | 20.7 | Slow |
| SLAHMR | 326.9 | 776.1 | 31.3 | 14.5 | ~4 hrs/1K fr |
| WHAM | 135.6 | 354.8 | 22.5 | 4.4 | ~5s/1K fr |
| **GVHMR** | **111.0** | **276.5** | **16.7** | **3.5** | **0.28s/1.4K fr** |
| **Human3R** | **112.2** | **267.9** | — | — | **15 FPS e2e** |

### Recommendation

**Primary: GVHMR** — Best accuracy-speed tradeoff. Gravity-view coordinates give world frame directly. ~5000 FPS core network.

**Alternative: Human3R** — Multi-person + scene + camera in one forward pass. MIT licensed. Its explicit weaknesses (penetration, no physics) are exactly what we fix.

**Why not SAM-Body4D?** Camera-relative only, no world coordinates, uses MHR not SMPL. Would need separate world-grounding step.

---

## GVHMR Deep Dive

### How It Works
1. **Preprocessing (off-the-shelf):** YOLOv8 detection (4.9s) → ViTPose 2D keypoints (20.0s) → ViT features (10.1s) → DPVO camera motion (11.0s)
2. **Core Network:** Early fusion → Relative Transformer (12L, 8H, RoPE) → Multi-task MLP heads
3. **Post-processing:** Stationary labels → CCD-IK foot pinning

### Gravity-View Coordinate System
- Y = gravity direction (up), X = Y × camera_view, Z = right-hand rule
- Each frame independently gravity-anchored — frame 1000 is as accurate as frame 1
- Static camera: GV identical every frame. Moving camera: chain relative yaw rotations via DPVO

### Failure Modes

| Failure | Root Cause |
|---------|-----------|
| Foot sliding (3.0-3.5mm) | No physics constraints |
| Ground penetration | No scene awareness |
| Fast camera rotation | DPVO noisy estimates |
| Severe occlusion | ViTPose keypoints wrong |
| Multiple people | Single-person design |
| Gymnastics/swimming | GV assumes clear gravity |

---

## Scene Geometry: Depth Anything 3

### Why DA3 (scored 9.0/10)

| Feature | DA3 | Metric3D v2 | CUT3R | VGGT | ZipMap |
|---------|-----|------------|-------|------|--------|
| Metric depth | Yes | **Best** | Yes | Yes | No (relative) |
| Camera poses | **Yes** | No | Yes | Yes | Yes |
| Pointmaps | **Yes** | No | Yes | Yes | Yes |
| Streaming video | **Yes (<12GB)** | No | Yes | No | Yes* |
| License | **Apache-2.0** | Apache-2.0 | CC BY-NC-SA | Custom | Unknown |
| Released | **Yes** | Yes | Yes | Yes | **No** |

*ZipMap: code not yet released

### Runtime

| Model | FPS | VRAM | Long video? |
|-------|-----|------|-------------|
| **DA3-Large** | **78** | **<12 GB** | **Any length** |
| DA3-Small | 161 | ~5 GB | Any length |
| VGGT | ~60 | 8-40+ GB | ~60 frames max |
| ZipMap | 75 | H100 required | Batch only |

**Config:** DA3Metric-Large primary, DA3-Base fallback, MegaSaM complement, ZipMap future upgrade.

---

## Physics Evidence

### Why Physics Constraints Work

| Study | What Was Added | Key Improvement |
|-------|---------------|-----------------|
| MultiPhys (CVPR'24) | MuJoCo simulation loop | 7x less penetration, 5x less ground pen. |
| CRISP (arXiv'25) | Planar scene + RL tracking | 8x lower failure rate |
| PhysDiff (ICCV'23) | Physics in diffusion | 86% less physical error |
| PROX (ICCV'19) | SDF penetration + contact terms | 24% better V2V |
| LEMO (ICCV'21) | Friction + smoothness prior | Eliminates skating + jitter |
| **PhysHMR (SigAsia'25)** | **End-to-end visual→physics** | **Best on all metrics; two-stage hurts** |

### Critical Lesson: PhysHMR

| Pipeline | Foot Sliding |
|----------|-------------|
| GVHMR alone | 5.65 mm |
| GVHMR + RL post-correction (PHC+) | **12.71 mm (worse!)** |
| PhysHMR (end-to-end) | **4.60 mm (best)** |

**Implication:** Use optimization-based energy minimization (PROX/LEMO style), NOT RL post-processing.

---

## Proposed Architecture

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

### License-Safe Stack

| Component | License | Role |
|-----------|---------|------|
| Human3R | **MIT** | Body + scene |
| DA3 | **Apache-2.0** | Depth / pointmaps |
| MuJoCo | **Apache-2.0** | Physics engine |
| Open3D | **MIT** | Point cloud processing |
| PyTorch | **BSD** | Optimization backend |

---

## Joint Human-Scene Reconstruction Landscape

| Method | Year | Online? | Multi-Person? | Scene? | Key Benchmark |
|--------|------|---------|---------------|--------|---------------|
| HOSNeRF | 2023 | No | No | NeRF | ~5 days/video |
| Easi3R | 2025 | No | No | Dynamic | Training-free |
| JOSH | 2026 | No | Yes | Yes | WA-MPJPE **68.9** (best) |
| **Human3R** | **2025** | **Yes (15fps)** | **Yes** | **Dense** | WA-MPJPE 112.2 (best online) |
| SHARE | 2025 | No | No | Pointmap | RICH only |

---

## SAM-Body4D Deep Dive

### Three-Stage Pipeline (Training-Free)

1. **Masklet Generation:** SAM 3 → identity-consistent masks with memory mechanism
2. **Occlusion-Aware Refinement:** Diffusion-VAS detects occlusion (area increase + IoU drop < 0.7), inpaints missing body pixels
3. **Mask-Guided HMR:** Refined masks → SAM 3D Body → per-frame mesh params + Kalman filtering

### Foundation Models Used

| Model | Role |
|-------|------|
| SAM 3 | Video segmentation + identity tracking |
| Diffusion-VAS | Amodal segmentation / occlusion completion |
| SAM 3D Body | Per-frame mesh recovery |
| Depth-Anything V2 | Depth cues |
| MoGe-2 | Normal/geometry cues |

### Limitations for Pact3D
- Camera-relative only (no world coordinates)
- No physics awareness
- Uses MHR, not SMPL
- No quantitative evaluation
- Heavy: 5 foundation models, A100 GPU

### Setup (from [gaomingqi/sam-body4d](https://github.com/gaomingqi/sam-body4d))
```bash
conda create -n body4d python=3.12 -y && conda activate body4d
pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu118
pip install 'git+https://github.com/facebookresearch/detectron2.git@a1ce2f9' --no-build-isolation --no-deps
pip install -e models/sam3
pip install -e .
huggingface-cli login  # SAM 3 and SAM 3D Body require HF access approval
python scripts/setup.py --ckpt-root /path/to/checkpoints
python app.py  # Gradio demo
python scripts/offline_app.py --input_video <path>  # End-to-end
```

---

## ZipMap (CVPR'26)

Feed-forward 3D scene reconstruction with O(N) linear scaling via TTT layers. 1.40B params, 750+ frames in <10s on H100.

**Status:** Code/weights NOT released. Placeholder repo only. Future upgrade path for scene backbone.

**vs DA3:** DA3 has metric depth, Apache-2.0 license, consumer GPU support, and is released today. ZipMap is the right tool for full 3DGS environments; DA3 is right for per-frame physics constraints.

---

## Evaluation

### Datasets

| Dataset | Why | Ground Truth |
|---------|-----|-------------|
| **RICH** | Scene scans + vertex contact GT + global coords | SMPL-X, 3D scenes, vertex contacts |
| **EMDB-2** | Most accurate global GT (2.3cm pose, 5.1cm root) | SMPL, EM sensors |
| **3DPW** | Standard benchmark | SMPL, IMU-fused |
| **Hi4D** | Multi-person close interaction | 4D scans, vertex contacts |

### Targets

| Metric | Current SOTA | Our Target |
|--------|-------------|------------|
| Foot Sliding | 3.0 mm (GVHMR) | < 1 mm |
| Ground Penetration | ~2-5 mm | < 1 mm |
| PA-MPJPE | 36.2 mm (GVHMR) | No degradation |

### Metric Implementations

```python
def foot_sliding(joints_world, contact_mask, foot_idx, dt):
    foot = joints_world[:, foot_idx, :]
    v_xy = np.linalg.norm((foot[1:] - foot[:-1])[:, :2] / dt, axis=1)
    return float(np.mean(v_xy[contact_mask[1:]])) if np.any(contact_mask[1:]) else 0.0

def penetration_plane(vertices_world, plane_n, plane_d):
    signed = vertices_world @ plane_n + plane_d
    return float(np.mean(-np.minimum(signed, 0.0)))

def trajectory_drift(root_world, dt):
    vel = (root_world[1:] - root_world[:-1]) / dt
    acc = (vel[1:] - vel[:-1]) / dt
    return float(np.mean(np.linalg.norm(acc, axis=1)))
```

---

## 8-Week Plan

| Week | Focus | Risk |
|------|-------|------|
| 1 | Environment + baselines: DA3 + GVHMR/Human3R running | Low |
| 2 | Scene proxy: floor plane RANSAC, gravity alignment, collision mesh | Low |
| 3 | Contact inference: foot velocity + proximity, loss terms | Low |
| 4 | MuJoCo correction loop: body capsules + scene planes | Medium |
| 5 | Rigid object interaction: hand/object non-penetration | Medium |
| 6 | Evaluation on RICH, EMDB-2, 3DPW + ablations | Low |
| 7 | Robustness: chunking, stitching, edge cases | Medium |
| 8 | Demo renders, metrics tables, technical report | Low |

### Compute Requirements

| Component | VRAM | Time / 1K frames |
|-----------|------|-------------------|
| GVHMR | ~4 GB | ~0.2 sec |
| Human3R | ~8 GB | ~67 sec |
| DA3-Metric-L | <12 GB | ~13 sec |
| MuJoCo | CPU | ~10-30 sec |
| **Total** | **< 16 GB** | **< 2 min** |

---

## Physics & Simulation Stack

| Engine | License | Best For |
|--------|---------|----------|
| **MuJoCo** | **Apache-2.0** | Contact dynamics (primary choice) |
| PyBullet | zlib | Rapid prototyping |
| Brax | Apache-2.0 | JAX differentiable, massive parallelism |
| SAPIEN | Apache-2.0 | Articulated objects, PhysX 5 |
| Drake | BSD | Formal optimization-based control |

---

## Key References

### Body Tracking
- [GVHMR](https://github.com/zju3dv/GVHMR) — SigAsia 2024
- [Human3R](https://github.com/fanegg/Human3R) — ICLR 2026
- [WHAM](https://wham.is.tue.mpg.de/) — CVPR 2024
- [4D-Humans](https://github.com/shubham-goel/4D-Humans) — ICCV 2023
- [SAM-Body4D](https://github.com/gaomingqi/sam-body4d) — arXiv 2512.08406

### Scene Geometry
- [Depth Anything 3](https://github.com/ByteDance-Seed/Depth-Anything-3) — Apache-2.0
- [ZipMap](https://haian-jin.github.io/ZipMap/) — CVPR 2026 (unreleased)
- [CUT3R](https://github.com/CUT3R/CUT3R) — CVPR 2025

### Physics-Aware Methods
- [MultiPhys](https://github.com/nicolasugrinovic/multiphys) — CVPR 2024
- [PhysHMR](https://arxiv.org/abs/2510.02566) — SigAsia 2025
- [CRISP](https://github.com/Z1hanW/CRISP-Real2Sim) — arXiv 2025
- [PROX](https://prox.is.tue.mpg.de/) — ICCV 2019
- [LEMO](https://github.com/sanweiliti/LEMO) — ICCV 2021

---
---

# Part 2: NL Video Editor Subproject

## Vision

A natural language video editor built on SAM-Body4D that understands the **3D geometric structure** of video, not just pixels. Users issue commands like "highlight the striker in red" or "show a skeleton overlay on all players" and the system executes them with mesh-aware, physics-aware precision.

**The moat:** Every competitor (Runway, Descript, CapCut, Pika, Adobe, DaVinci) operates on 2D pixel grids or latent diffusion spaces. No one has mesh-aware + physics-aware editing.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│  ┌───────────────────────────────────────────┐   │
│  │  Command Bar (NL input)                   │   │
│  │  "Highlight the goalkeeper in yellow"     │   │
│  └───────────────────────────────────────────┘   │
│  ┌──────────┐  ┌─────────────────────────────┐   │
│  │ Chat     │  │  Video Preview + Timeline   │   │
│  │ History  │  │  ┌───────────────────────┐   │   │
│  │          │  │  │  ▶ video canvas       │   │   │
│  │          │  │  │    with overlays      │   │   │
│  │          │  │  └───────────────────────┘   │   │
│  │          │  │  ──●────────────────── 0:34  │   │
│  │          │  │  [masks] [meshes] [effects]  │   │
│  └──────────┘  └─────────────────────────────┘   │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│                   Backend                        │
│  NL Parser (Claude/Gemini API)                   │
│       ↓                                          │
│  Action Router                                   │
│       ↓                                          │
│  ┌─────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ SAM 2/3 │  │ SAM-Body │  │ Render Engine  │  │
│  │ segment │→ │ 4D mesh  │→ │ compose + fx   │  │
│  └─────────┘  └──────────┘  └────────────────┘  │
│  GPU Workers (A100)         FFmpeg output         │
└─────────────────────────────────────────────────┘
```

---

## Feature Tiers

### Tier 1: Core (SAM-Body4D as-is)
- "Highlight player #7 in blue"
- "Blur everyone except the goalkeeper"
- "Track the ball across the clip"
- "Isolate the dancer and remove the background"

### Tier 2: Mesh-Aware Edits
- "Freeze the frame when his arm is fully extended" — pose-based keyframe detection
- "Show a skeleton overlay on all players" — direct from mesh
- "Measure the angle of her knee at the jump" — biomechanics from mesh
- "Replace the person with a 3D avatar" — mesh retargeting

### Tier 3: Multi-Modal Intelligence (LLM + Vision + Mesh)
- "Cut to every time someone scores" — event detection via pose + context
- "Add slow-mo when the gymnast is inverted" — orientation from mesh
- "Generate a highlight reel of player #10" — temporal reasoning
- "Swap the jersey color to red" — segmentation mask + inpainting

### Tier 4: Physics-Aware (Pact3D stack)
- "Show ground contact forces as particles" — MuJoCo contact → VFX
- "Flag every frame where the foot slides" — physics validation
- "Simulate what would happen if he jumped 2x higher" — re-simulation

### Tier 5: World Model Integration
- "What if the ball bounced differently?" — counterfactual re-simulation
- "Extend this clip 3 seconds" — physics-plausible motion extrapolation
- "Place this person on a beach" — scene transfer with physics grounding

---

## World Models Research

### Open-Source Models (code + weights downloadable)

| Model | What It Does | License | Hardware | Integration Path |
|-------|-------------|---------|----------|-----------------|
| [NVIDIA Cosmos](https://github.com/nvidia-cosmos/cosmos-predict2.5) | Action-conditioned video prediction | Apache-2.0 (code) + NVIDIA Open Model (weights) | A100 80GB (2B); multi-GPU (14B) | **Best near-term.** Fine-tune on human data with SAM-Body4D action labels |
| [Aether](https://github.com/OpenRobotLab/Aether) | 4D reconstruction + action prediction + planning | MIT | A100 80GB | Unified 4D + planning. ICCV'25 Outstanding Paper |
| [DIAMOND](https://github.com/eloialonso/diamond) | RL agent in diffusion world model | MIT | Consumer GPU | Architectural reference for action-conditioned prediction |
| [Oasis 500M](https://github.com/etched-ai/open-oasis) | Real-time AI Minecraft | MIT | Consumer GPU (1-2 FPS) | Real-time generation reference |
| [SAM 2](https://github.com/facebookresearch/sam2) | Promptable video segmentation | Apache-2.0 | Consumer GPU | Core segmentation backbone |
| [Grounded SAM 2](https://github.com/IDEA-Research/Grounded-SAM-2) | Open-vocabulary video segmentation | Apache-2.0 | Standard GPU | NL-driven object selection |
| [AutoVFX](https://github.com/haoyuhsu/autovfx) | NL → physics VFX via Blender | No license file (caution) | Varies | **Closest to NL editor.** Extend with SAM-Body4D meshes |
| [PhysDreamer](https://github.com/a1600012888/PhysDreamer) | Physics interaction with 3D objects | Check repo | Not specified | Physics for non-human scene objects. Weights on HF |
| [PhysGen3D](https://github.com/by-luckk/PhysGen3D) | Single image → interactive 3D scene with physics | Check repo | Not specified | Freeze frame → modify → re-simulate |
| [MIMO](https://github.com/menyifang/MIMO) | Controllable character video synthesis | Check repo | 40GB+ VRAM | Identity swap + motion retarget |
| [LLaVA-Video](https://github.com/LLaVA-VL/LLaVA-NeXT) | Video understanding VLM | Llama 2 Community | 16GB+ VRAM | NL video Q&A, scene understanding |
| [VideoAgent](https://github.com/YueFan1014/VideoAgent) | Memory-augmented video agent | Check repo | RTX 4090 24GB | Agentic video understanding |
| [Cutie-Roto](https://github.com/Zarxrax/Cutie-Roto) | Video object segmentation / rotoscoping | MIT | Standard GPU | Free rotoscoping alternative |
| [4D Gaussian Splatting](https://github.com/hustvl/4DGaussians) | Dynamic scene reconstruction at 82fps | Non-commercial (Inria base) | RTX 3090 | Novel viewpoint rendering |

### API-Available Models

| Model | What It Does | Access | Integration Path |
|-------|-------------|--------|-----------------|
| Sora 2 (OpenAI) | Video generation, 25s, with audio | API ($0.15-0.40/s) | Scene extension, background replacement |
| Veo 3.1 (Google) | 60s video, 1080p, native audio, lip-sync | Gemini API | Reference-image conditioned generation |
| Gemini 3 Flash | Video understanding, 1hr+ | API | NL command parsing, temporal reasoning |
| ElevenLabs SFX V2 | Text-to-sound-effects, 48kHz | API | Physics-driven foley from contact events |
| WorldLabs | 3D scene generation from images | API | Scene creation, spatial understanding |

### Closed-Source (Not Available)
- GameNGen (Google) — no official weights, only unofficial repros
- Genie 2/3 (DeepMind) — not released, Project Genie limited to AI Ultra users
- UniSim (Berkeley/DeepMind) — no public weights
- CWMDT — paper only, no code released
- InterDyn — paper only, no code released
- Visual Particle Dynamics — no public repo

### Key Integration: CWMDT (Counterfactual World Models via Digital Twin)

[arXiv:2511.17481](https://arxiv.org/abs/2511.17481) — Most architecturally aligned with our "what if" editing paradigm:
1. SAM-2 segments + tracks objects → digital twin (structured text)
2. LLM reasons about counterfactual in text space
3. Video diffusion renders the result

Extend the digital twin to include SAM-Body4D body meshes as first-class entities.

---

## Frontier AI Capabilities

### Video Understanding

| Model | Params | Status | Key Capability |
|-------|--------|--------|----------------|
| Gemini 3 Flash | — | Product (API) | 1hr+ video, sub-second latency |
| [LLaVA-Video](https://llava-vl.github.io/blog/2024-09-30-llava-video/) | 7B/72B | Open-source | Strong video-MME benchmarks |
| [SlowFast-LLaVA-1.5](https://machinelearning.apple.com/research/slowfast-llava) (Apple) | 1B/3B/7B | Open-source | SOTA long-form at each scale |
| [LLaVA-Mini](https://arxiv.org/abs/2501.03895) | 7B | Open-source (ICLR'25) | 1 vision token, 77% FLOP reduction, 10K+ frames on 24GB |
| [VideoAgent](https://github.com/HKUDS/VideoAgent) | — | Open-source | Graph-structured agentic video understanding |

### 3D from Video

| Model | Status | Key Capability |
|-------|--------|----------------|
| [4D Gaussian Splatting](https://github.com/hustvl/4DGaussians) | Open-source (CVPR'24) | Dynamic scenes at 82fps |
| [MonoPartNeRF](https://arxiv.org/abs/2508.08798) | Research | Part-based NeRF for humans from monocular video |
| [Instant-NGP](https://nvlabs.github.io/instant-ngp/) | Open-source | 1000x faster NeRF, train in seconds |

### Agentic Video Editing

| System | Status | Key Capability |
|--------|--------|----------------|
| [VideoAgent](https://github.com/HKUDS/VideoAgent) (HKU) | Open-source | All-in-one agentic framework, best with Claude backbone |
| [LAVE](https://www.dgp.toronto.edu/~bryanw/lave/) (U Toronto) | Research (ACM'24) | Human-AI co-creation paradigm |
| Luma Agents | Product (March 2026) | Unified creative workflow orchestration |
| Poolday AI | Product | Autonomous editor chaining 50+ models |

### Audio-Visual AI

| Tool | Status | Integration |
|------|--------|-------------|
| Google V2A / Veo 3 | Product | Audio from video pixels, <120ms lip-sync |
| [ElevenLabs SFX V2](https://elevenlabs.io/sound-effects) | Product (API) | Text-to-SFX at 48kHz, 30s, looping |
| [Colourlab AI](https://colourlab.ai/) | Product | 22x faster color grading, DaVinci integration |

### Real-Time Processing

| System | Status | Speed |
|--------|--------|-------|
| [StreamMind](https://www.microsoft.com/en-us/research/articles/streammind-ai-system-that-responds-to-video-in-real-time/) (Microsoft) | Research | Real-time at 100fps |
| Google On-Device Effects | Product (YouTube) | ~6ms on Pixel 8 Pro |
| Decart Lucy 2 | Product | Near-zero latency video editing |

---

## Competitive Landscape

### Market: ~$3.67B in 2026, 18-22% CAGR

| Competitor | Category | Price | Key Gap vs. Pact3D |
|-----------|----------|-------|-------------------|
| Runway ML | Generation | $12-76/mo | 2D pixel inpainting, no mesh understanding |
| Descript | Transcript editing | $24-65/mo | NL is speech-grounded, not geometry-grounded |
| CapCut | Consumer social | Free-Pro | 2D filters only, 15 min limit |
| Pika Labs | Stylized generation | $8-76/mo | Pixel space swaps, no geometry |
| HeyGen | Avatar video | $24-149/mo | Talking heads only, no body articulation |
| Synthesia | Enterprise avatars | $18-67/mo+ | Preset animations, not physics-simulated |
| VEED.io | Browser editor | $12-55/mo | Format-level NL, not spatial |
| Adobe Premiere | Professional NLE | $22-70/mo | AI bolted onto 2D timeline |
| DaVinci Resolve | Professional NLE | Free/$295 | Closest (Depth Map v2) but still 2.5D |
| Topaz Video AI | Enhancement | $25/mo or $299+ | Pixel enhancement only |

### Capability Matrix

| Capability | All Competitors | Pact3D NL Editor |
|-----------|----------------|-----------------|
| 3D mesh understanding | No (DaVinci: 2.5D) | **Yes — SMPL meshes** |
| Physics-aware editing | No | **Yes — MuJoCo** |
| Body pose editing | No (Synthesia: presets) | **Yes — articulated** |
| Contact/penetration aware | No | **Yes** |
| NL spatial commands | No (Descript: transcript) | **Yes — geometry-grounded** |
| World-grounded coordinates | No | **Yes** |
| Simulation-ready output | No | **Yes** |

---

## UX Design Direction

### Design System: Untitled UI

**Reference:** [Untitled UI PRO v7.0](https://www.figma.com/design/YbdR1kLiOU262EEicORFYh/) — world's largest Figma UI kit (10,000+ components, 900+ variables, 420+ pages). Created by Jordan Hughes. Also ships as React + Tailwind CSS v4.1 + React Aria.

**Core principles:**
- **Light theme** with cool-tinted neutrals (grays lean blue, not warm)
- **Borderless components** — subtle layered shadows and background tints instead of borders
- **Inline styles** — controls appear contextually, not in fixed panels
- **Progressive disclosure** — simple by default, powerful on demand
- **Subtle skeuomorphism** — buttons have minimal depth (shadow + gradient), not flat
- **Tinted shadows** — `rgba(10, 13, 18, ...)` not pure black. Multiple layers per level

### Color Palette (Light Theme)

**Grays (foundation):**

| Token | Hex | Usage |
|-------|-----|-------|
| Gray 25 | `#FCFCFD` | Subtle backgrounds |
| Gray 50 | `#F9FAFB` | Page backgrounds, alternate rows |
| Gray 100 | `#F2F4F7` | Secondary backgrounds, hover |
| Gray 200 | `#E4E7EC` | Dividers (instead of borders) |
| Gray 300 | `#D0D5DD` | Input borders (when needed) |
| Gray 500 | `#667085` | Secondary text (AA) |
| Gray 600 | `#475467` | Default body text (AAA, 7.65 ratio) |
| Gray 700 | `#344054` | Strong body text |
| Gray 900 | `#101828` | Headings, highest contrast |
| White | `#FFFFFF` | Primary background |

**Brand (customizable, default purple):**

| Token | Hex | Usage |
|-------|-----|-------|
| brand-600 | `#7F56D9` | Primary button default |
| brand-700 | `#6941C6` | Hover state |

### Typography
- **Font:** Inter (variable, 100-900 weight + optical size axis)
- **Body:** Gray 600 (AAA accessible), not Gray 500
- **Scale:** 6 display sizes (2xl→xs) + 5 text sizes (xl→xs)
- **Features:** Tabular figures (`tnum`) for numeric data

### Shadow System (layered, not single box-shadow)

| Level | Characteristic |
|-------|---------------|
| shadow-md | `0px 4px 5px rgba(10,13,18,0.08)` + `0px 2px 2px rgba(10,13,18,0.04)` |
| shadow-lg | 3 layers, max opacity 0.08 |
| shadow-xl | 3 layers, soft diffused |
| shadow-2xl | `0px 24px 36px rgba(10,13,18,0.16)` + tight layer |

### Border Philosophy
- Cards use **shadow elevation** instead of borders
- Section separation via **background color** (White vs Gray 50) not lines
- Input borders only when necessary (Gray 300)
- Inline CTAs embedded in content flow, not boxed

### Tech Stack
```
React 19.1 + Tailwind CSS v4.1 + TypeScript 5.8 + React Aria
CSS layers: @layer reset, base, tokens, recipes, utilities
CSS variables: --color-brand-*, --color-gray-*
CLI: npx @untitleduico/cli tailwind
```

### Figma References

| Template | Link | Use For |
|----------|------|---------|
| Untitled UI PRO v7.0 | [Figma](https://www.figma.com/design/YbdR1kLiOU262EEicORFYh/) | **Primary design system** |
| AI Video Editing Software | [Figma](https://www.figma.com/community/file/1355500227637627705/ai-based-video-editing-software) | Editor layout reference |
| Video Editing Dashboard | [Figma](https://www.figma.com/community/file/1491449166618431732/video-editing-dashboard) | Timeline + media library patterns |
| AI SaaS Dark Theme Landing | [Figma](https://www.figma.com/community/file/1563044954628344634/ai-saas-landing-page-dark-theme) | Landing page structure (adapt to light) |
| 30+ SaaS Landing Pages | [Figma](https://www.figma.com/community/file/1227186272714321255/30-saas-landing-pages) | Hero section variations |

### Key UX Patterns (from Cursor/Claude)

**1. Ghost Previews (from Cursor Tab)**
When user types "add Ken Burns zoom," show ghost animation overlay *before* commit. Tab to accept, Esc to reject.

**2. Visual Diffs for Edits**
"Speed up this section" → timeline shows original duration ghosted out, new version highlighted. Accept/reject with keystroke.

**3. Inline Cmd+K Prompt**
Click any element → hotkey → small inline NL prompt → instant preview. No context switch.

**4. Semantic Timeline (multi-layer)**
- **Narrative layer** (top): Story beats, themes, emotional arc
- **Scene layer** (middle): Auto-detected scenes with thumbnails, speakers, topics
- **Frame layer** (bottom): Traditional precise timeline, visible on zoom

**5. Generative UI (from Vercel v0)**
Interface adapts to task. "Color grade this" → color wheels appear. "Write a script" → text editor appears. Controls are generated, not navigated to.

**6. AI as Team Member**
AI has its own cursor/presence on canvas. Shows activity status. Comments become prompts. Rejected suggestions train preferences.

### Interaction Paradigms

| Pattern | Who Does It Well | How It Maps to Video Editor |
|---------|-----------------|---------------------------|
| Document-native editing | Descript, Doki | Transcript IS the editing interface |
| Chat sidebar | Cursor | Conversational refinement of edits |
| Inline prompt bar | Pika, Runway | Quick single-action commands |
| Infinite canvas | tldraw | Storyboard planning, version branching |
| Voice control | Promwad | Hands-free review: "mark this," "cut here" |

---

## Priority Integration Roadmap

| Priority | Capability | Best Option | UX Win |
|----------|-----------|-------------|--------|
| 1 | NL video understanding | Gemini 3 Flash / LLaVA-Mini | Conversational editing commands |
| 2 | Object segmentation | SAM 2 + Grounded SAM 2 | NL-driven selection of anything |
| 3 | Body mesh tracking | SAM-Body4D | Identity-consistent 4D meshes |
| 4 | Agentic orchestration | VideoAgent / custom | Multi-step NL workflows |
| 5 | 3D scene from video | 4D Gaussian Splatting | Novel viewpoint rendering |
| 6 | Audio from physics | ElevenLabs SFX + V2A | Physics-driven foley |
| 7 | Video generation | Veo 3.1 / Sora 2 API | Scene extension, bg replacement |
| 8 | World model "what if" | NVIDIA Cosmos + CWMDT | Counterfactual re-simulation |
| 9 | Real-time preview | StreamMind / Decart | Live editing feedback |
| 10 | Style transfer | Mago Studio / DomoAI | Body-aware artistic stylization |

---

## What Makes This Unique

Every competitor is either:
- **Generation-first** (Runway, Pika) — creates video, doesn't understand its structure
- **Transcript-first** (Descript) — understands speech, not space
- **Timeline-first** (Premiere, DaVinci) — 2D pixel manipulation
- **Enhancement-first** (Topaz) — improves quality, no content awareness

We are **geometry-first**: understand the 3D structure of bodies and scenes, then let users edit that structure with natural language. The physics layer ensures edits are plausible. The world models enable counterfactual reasoning. No one else has this stack.

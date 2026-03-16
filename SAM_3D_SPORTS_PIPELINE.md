# SAM 3D Sports Pipeline — Comprehensive Research & Implementation Guide

## Table of Contents

- [1. Pipeline Overview](#1-pipeline-overview)
- [2. SAM 2 — Video Segmentation Foundation](#2-sam-2--video-segmentation-foundation)
- [3. SAM 3D Body & SAM-Body4D](#3-sam-3d-body--sam-body4d)
- [4. Multi-Person Tracking for Sports](#4-multi-person-tracking-for-sports)
- [5. World-Grounded Human Mesh Recovery](#5-world-grounded-human-mesh-recovery)
- [6. Physics-Based Refinement](#6-physics-based-refinement)
- [7. 3D Scene Reconstruction](#7-3d-scene-reconstruction)
- [8. 3D Mesh Visualization & UI](#8-3d-mesh-visualization--ui)
- [9. Person-to-Person Interaction](#9-person-to-person-interaction)
- [10. Kinematics & Dynamics Extraction](#10-kinematics--dynamics-extraction)
- [11. Sports Biomechanics from Video](#11-sports-biomechanics-from-video)
- [12. MuJoCo Integration](#12-mujoco-integration)
- [13. Full Dependency Stack](#13-full-dependency-stack)
- [14. Recommended Pipeline Configurations](#14-recommended-pipeline-configurations)
- [15. All References & GitHub Repos](#15-all-references--github-repos)

---

## 1. Pipeline Overview

### End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     SAM 3D SPORTS PIPELINE                              │
│                                                                         │
│  INPUT: Monocular sports video (broadcast, drone, sideline camera)      │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ STAGE 1: DETECTION + TRACKING                                   │    │
│  │                                                                 │    │
│  │  YOLO11/Grounding DINO → person detection                      │    │
│  │  BoT-SORT / SAM2MOT    → identity-consistent tracking          │    │
│  │  SAM 2 Video Predictor  → per-person masklets (spatio-temporal) │    │
│  └──────────────────────────────┬──────────────────────────────────┘    │
│                                 │                                       │
│  ┌──────────────────────────────▼──────────────────────────────────┐    │
│  │ STAGE 2: 3D HUMAN MESH RECOVERY                                │    │
│  │                                                                 │    │
│  │  Option A: SAM-Body4D pipeline (SAM3 → Diffusion-VAS →         │    │
│  │            SAM 3D Body → MHR meshes)                            │    │
│  │  Option B: GVHMR pipeline (ViTPose → DPVO → SMPL meshes        │    │
│  │            in world coordinates)                                │    │
│  │  Option C: Human3R (multi-person + scene in one forward pass)   │    │
│  └──────────────────────────────┬──────────────────────────────────┘    │
│                                 │                                       │
│  ┌──────────────────────────────▼──────────────────────────────────┐    │
│  │ STAGE 3: SCENE RECONSTRUCTION                                   │    │
│  │                                                                 │    │
│  │  Depth Anything 3 → metric depth + pointmaps + camera poses     │    │
│  │  DUSt3R/MASt3R    → dense 3D scene from arbitrary image pairs   │    │
│  │  RANSAC            → ground plane extraction                    │    │
│  │  Court/field model  → homography for bird's-eye view            │    │
│  └──────────────────────────────┬──────────────────────────────────┘    │
│                                 │                                       │
│  ┌──────────────────────────────▼──────────────────────────────────┐    │
│  │ STAGE 4: PHYSICS REFINEMENT                                     │    │
│  │                                                                 │    │
│  │  PhysPT / optimization → foot contact, ground penetration fix   │    │
│  │  MuJoCo validation     → physically plausible motion            │    │
│  │  MultiPhys             → multi-person contact constraints       │    │
│  └──────────────────────────────┬──────────────────────────────────┘    │
│                                 │                                       │
│  ┌──────────────────────────────▼──────────────────────────────────┐    │
│  │ STAGE 5: ANALYSIS + VISUALIZATION                               │    │
│  │                                                                 │    │
│  │  Kinematics → joint angles, velocities, CoM trajectory          │    │
│  │  Dynamics   → joint torques, GRFs (via OpenSim/MuJoCo)         │    │
│  │  Interaction → contact detection, momentum transfer             │    │
│  │  Rendering  → colored meshes, overlays, BEV, side-by-side      │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  OUTPUT: World-grounded 3D meshes + biomechanics + interactive viewer   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Pipeline Configuration Options

| Configuration | Best For | VRAM | Speed | World Coords | Physics |
|--------------|---------|------|-------|--------------|---------|
| **SAM-Body4D** (full) | Highest mesh quality, occlusion handling | ~32 GB peak | Slow (diffusion) | No (camera-relative) | No |
| **GVHMR** + SAM 2 | World-grounded single-person | ~16 GB | Fast (~5s/1K frames) | Yes | No |
| **Human3R** | Multi-person + scene, real-time | ~8 GB | 15 FPS | Yes | No |
| **GVHMR + PhysPT** | Physics-plausible world motion | ~20 GB | Medium | Yes | Yes |
| **GVHMR + MuJoCo** | Full dynamics analysis | ~16 GB + CPU | Medium | Yes | Yes |

---

## 2. SAM 2 — Video Segmentation Foundation

### Architecture

SAM 2 (Segment Anything Model 2) is Meta's foundation model for promptable visual segmentation in images and video. Key components:

- **Image Encoder**: Hiera backbone with FPN/skip-connections
- **Prompt Encoder**: Processes points, bounding boxes, or masks
- **Memory Module**: Memory encoder + memory bank + memory attention for temporal consistency
- **Occlusion Head**: Predicts per-frame object visibility
- **Streaming Processing**: One frame at a time; memory enables cross-frame coherence

**Masklets**: SAM 2's term for spatio-temporal masks — the segmentation of one object across all video frames. Given a prompt on any single frame, SAM 2 propagates forward and backward to produce the full masklet. The SA-V training dataset has 600K+ masklets across 51K videos.

**Occlusion handling**: Memory bank recalls object appearance through occlusions. SA-V has 42.5% disappearance rate to train robustness. For sports with long occlusions, use **SAM2Long** (ICCV 2025) — a training-free memory tree with uncertainty-aware path selection.

**Model sizes**: 4 variants — `sam2_hiera_tiny` (38.9M, ~47 FPS) to `sam2_hiera_large` (224.4M, ~30 FPS).

### Installation

```bash
# Requirements: Python >= 3.10, PyTorch >= 2.5.1, torchvision >= 0.20.1, CUDA 12.1

conda create -y -n sam2 python=3.10
conda activate sam2

pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

git clone https://github.com/facebookresearch/sam2.git && cd sam2
pip install -e .

# Optional: skip CUDA kernel compilation
# SAM2_BUILD_CUDA=0 pip install -e .

# Verify CUDA
python -c 'import torch; from torch.utils.cpp_extension import CUDA_HOME; print(torch.cuda.is_available(), CUDA_HOME)'
```

### Video Predictor API

```python
import torch
from sam2.sam2_video_predictor import SAM2VideoPredictor

predictor = SAM2VideoPredictor.from_pretrained("facebook/sam2-hiera-large")

with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
    state = predictor.init_state(<your_video>)

    # Add point/box prompts on a frame
    frame_idx, object_ids, masks = predictor.add_new_points_or_box(state, <prompts>)

    # Propagate to get masklets across all frames
    for frame_idx, object_ids, masks in predictor.propagate_in_video(state):
        # masks: per-object binary masks for each frame
        ...
```

Multiple objects tracked simultaneously with unique `obj_id` values. `vos_optimized=True` enables `torch.compile` for 2-3x speedup.

**GitHub**: https://github.com/facebookresearch/sam2

---

## 3. SAM 3D Body & SAM-Body4D

### SAM 3D Body

Meta's promptable model for single-image full-body 3D mesh recovery. Uses the **Momentum Human Rig (MHR)** — a parametric body model that decouples skeletal structure from surface shape (unlike SMPL). MHR provides 45 shape params, 204 pose params, 72 facial expression params, and 7 LOD levels.

```bash
# MHR Installation (via Pixi, recommended)
git clone git@github.com:facebookresearch/MHR.git && cd MHR
curl -OL https://github.com/facebookresearch/MHR/releases/download/v1.0.0/assets.zip
unzip assets.zip
pixi i

# Or via pip (experimental)
pip install pymomentum-cpu  # or pymomentum-gpu
pip install mhr
```

**Repos**:
- SAM 3D Body: https://github.com/facebookresearch/sam-3d-body
- MHR: https://github.com/facebookresearch/MHR
- Paper: arXiv:2602.15989

### SAM-Body4D (End-to-End 4D Mesh from Video)

Training-free framework for temporally consistent multi-person 4D mesh recovery. **The closest thing to an end-to-end SAM 3D sports pipeline.**

**Three-stage pipeline:**

```
Video
  │
  ▼
┌──────────────────────────────────────────────────┐
│ Stage 1: Identity-Consistent Masklet Generation  │
│                                                  │
│   SAM 3 (video segmentation model)               │
│   → per-person masklets with temporal continuity  │
│   → identity tracking via memory mechanism        │
└────────────────────┬─────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────┐
│ Stage 2: Occlusion-Aware Refinement              │
│                                                  │
│   Diffusion-VAS (amodal segmentation)            │
│   → detects occlusion (area increase + IoU drop) │
│   → inpaints missing body pixels                 │
└────────────────────┬─────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────┐
│ Stage 3: Mask-Guided HMR                         │
│                                                  │
│   SAM 3D Body per person per frame               │
│   → refined masklets serve as prompts            │
│   → padding-based parallel inference (1 GPU)     │
│   → Kalman filtering for temporal smoothness     │
│                                                  │
│   Output: Full-body MHR meshes per person/frame  │
└──────────────────────────────────────────────────┘
```

**Foundation models used:**

| Model | Role | VRAM |
|-------|------|------|
| SAM 3 | Video segmentation + identity tracking | ~3-4 GB |
| Diffusion-VAS | Amodal segmentation / occlusion completion | ~6-10 GB |
| SAM 3D Body | Per-frame mesh recovery | ~8-32 GB |
| Depth-Anything V2 | Depth cues | ~4 GB |
| MoGe-2 | Normal/geometry cues | ~4 GB |

**Setup:**

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

**Limitations for sports:**
- Camera-relative only (no world coordinates)
- No physics awareness
- Uses MHR, not SMPL (less compatible with biomechanics tools)
- Heavy: 5 foundation models, A100 GPU required
- No quantitative evaluation published

**Paper**: arXiv:2512.08406
**GitHub**: https://github.com/gaomingqi/sam-body4d

---

## 4. Multi-Person Tracking for Sports

### The Challenge

Sports scenes have: fast-moving athletes with similar appearances (uniforms), frequent occlusions (collisions, huddles), rapid camera motion. Standard SAM 2 can lose track.

### Tracking Approaches

| Method | Type | Strengths | GitHub |
|--------|------|-----------|--------|
| **SAM2MOT** (AAAI 2026) | Segmentation-driven MOT | +2.1 HOTA, +4.5 IDF1 vs ByteTrack on DanceTrack | [TripleJoy/SAM2MOT](https://github.com/TripleJoy/SAM2MOT) |
| **Grounded SAM 2** | Text-prompted detection + tracking | "Track all athletes", open-vocabulary | [IDEA-Research/Grounded-SAM-2](https://github.com/IDEA-Research/Grounded-SAM-2) |
| **BoT-SORT** | Detection-association | ReID features, camera motion compensation | [NirAharon/BoT-SORT](https://github.com/NirAharon/BoT-SORT) |
| **ByteTrack** | Detection-association | Very fast, no deep features | Integrated in Ultralytics |
| **SAM2Long** (ICCV 2025) | Memory-tree SAM 2 | Better occlusion handling | [Mark12Ding/SAM2Long](https://github.com/Mark12Ding/SAM2Long) |

### Recommended Sports Tracking Pipeline

```python
# Option 1: YOLO + BoT-SORT (fast, reliable)
from ultralytics import YOLO
model = YOLO("yolo11x.pt")
results = model.track(source="sports_video.mp4", tracker="botsort.yaml", persist=True)

# Option 2: Grounded SAM 2 (text-prompted, segmentation-native)
# "Track every person on the field"
```

**Best pipeline for sports:**
1. **Detection**: YOLO11 or Grounding DINO
2. **Tracking**: BoT-SORT (best for similar-looking athletes) or SAM2MOT
3. **Segmentation**: Feed tracked bboxes as prompts to SAM 2 Video Predictor
4. **HMR**: Crop each person via masklet → run through GVHMR / SAM 3D Body
5. **World-grounding**: GVHMR for global coordinate recovery

---

## 5. World-Grounded Human Mesh Recovery

### GVHMR (Primary Recommendation)

**Paper**: "World-Grounded Human Motion Recovery via Gravity-View Coordinates" (SIGGRAPH Asia 2024)

Predicts human pose in a **Gravity-View Coordinate** frame (Y = gravity, X = Y × camera_view, Z = right-hand rule). Each frame's pose is estimated independently — no autoregressive error accumulation. Per-frame GV estimates are transformed back to world coordinates using camera motion.

**Pipeline**: Video → bbox tracking → ViTPose 2D keypoints → ViT features → DPVO camera motion → Relative Transformer → SMPL params in GV → world transform

**Performance**: 1430-frame video in 280ms on RTX 4090 (excluding preprocessing). Core network: ~5000 FPS.

```bash
git clone https://github.com/zju3dv/GVHMR && cd GVHMR
conda create -y -n gvhmr python=3.10 && conda activate gvhmr
pip install -r requirements.txt && pip install -e .
# Also install DPVO (third-party/DPVO)
```

**Dependencies**: Python 3.10, PyTorch 2.3.0, CUDA 12.1, SMPL model files (register at smpl.is.tue.mpg.de). Optional: DPVO (Eigen 3.4.0, torch-scatter, numba, pypose).

**GitHub**: https://github.com/zju3dv/GVHMR

### Human3R (Multi-Person Alternative)

Multi-person + scene + camera in one forward pass. MIT licensed. 15 FPS end-to-end. Its explicit weaknesses (penetration, no physics) are what Pact3D's physics layer fixes.

**GitHub**: https://github.com/fanegg/Human3R

### Other World-Coordinate Methods

| Method | Year | Speed | Multi-Person | GitHub |
|--------|------|-------|-------------|--------|
| **GVHMR** | 2024 | ~5s/1K fr | No | [zju3dv/GVHMR](https://github.com/zju3dv/GVHMR) |
| **Human3R** | 2025 | 15 FPS | Yes | [fanegg/Human3R](https://github.com/fanegg/Human3R) |
| **WHAM** | 2024 | ~5s/1K fr | No | [yohanshin/WHAM](https://github.com/yohanshin/WHAM) |
| **TRAM** | 2024 | Medium | No | [yufu-wang/tram](https://github.com/yufu-wang/tram) |
| **SLAHMR** | 2023 | ~200 min/1K | Yes | [vye16/slahmr](https://github.com/vye16/slahmr) |
| **TRACE** | 2023 | Real-time | Yes | [Arthur151/ROMP](https://github.com/Arthur151/ROMP) |
| **PACE** (NVIDIA) | 2024 | — | Yes | [nvlabs.github.io/PACE](https://nvlabs.github.io/PACE/) |

### SMPL / SMPL-X Body Model

```bash
pip install smplx[all]
```

**Model files** (registration required):
- SMPL: https://smpl.is.tue.mpg.de → SMPL_{GENDER}.pkl
- SMPL-X: https://smpl-x.is.tue.mpg.de → SMPLX_{GENDER}.npz

```
models/
  smpl/
    SMPL_FEMALE.pkl
    SMPL_MALE.pkl
    SMPL_NEUTRAL.pkl
  smplx/
    SMPLX_FEMALE.npz
    SMPLX_MALE.npz
    SMPLX_NEUTRAL.npz
```

```python
import smplx
model = smplx.create(model_path='models/', model_type='smplx', gender='neutral')
output = model(betas=betas, body_pose=body_pose)
vertices = output.vertices  # (1, 10475, 3)
```

---

## 6. Physics-Based Refinement

### Why Physics Matters

| Study | What Was Added | Key Improvement |
|-------|---------------|-----------------|
| MultiPhys (CVPR 2024) | MuJoCo simulation loop | 7x less penetration |
| PhysHMR (SigAsia 2025) | End-to-end visual→physics | Best on all metrics |
| PhysPT (CVPR 2024) | Euler-Lagrange pretrained transformer | 83.8% less accel error, 68.7% less skating |
| CRISP (arXiv 2025) | Planar scene + RL tracking | 8x lower failure rate |
| PhysDiff (ICCV 2023) | Physics in diffusion | 86% less physical error |
| PROX (ICCV 2019) | SDF penetration + contact | 24% better V2V |
| LEMO (ICCV 2021) | Friction + smoothness prior | Eliminates skating + jitter |

### Critical Lesson: Post-Hoc RL Hurts

| Pipeline | Foot Sliding |
|----------|-------------|
| GVHMR alone | 5.65 mm |
| GVHMR + RL post-correction (PHC+) | **12.71 mm (worse!)** |
| PhysHMR (end-to-end) | **4.60 mm (best)** |

**Implication**: Use optimization-based energy minimization (PROX/LEMO style), NOT RL post-processing.

### PhysPT (CVPR 2024) — Recommended Post-Processing

Physics-aware Pretrained Transformer applied on top of any HMR output. Self-supervised, no physics engine at runtime. Estimates contact forces.

```bash
git clone https://github.com/zhangy76/PhysPT
```

- Uses spring-mass contact model (velocity + ground distance)
- Euler-Lagrange loss for physical plausibility
- Can be applied after GVHMR, HMR2, WHAM, etc.

### MultiPhys (CVPR 2024) — Multi-Person Physics

Handles multiple people with physical interactions. 7x less inter-body penetration vs SLAHMR.

```bash
git clone https://github.com/nicolasugrinovic/multiphys
```

### Pact3D Physics Layer Architecture

```
SMPL meshes (from GVHMR/Human3R)
    │
    ├── Ground Plane (RANSAC on DA3 pointmap)
    ├── Collision Mesh (pointmap → mesh)
    ├── Contact Detection (foot velocity + proximity)
    │
    └── Energy Minimization:
          E_contact      pin feet to surface        (PROX)
          E_penetration  SDF non-intersection       (PROX)
          E_friction     no sliding during contact  (LEMO)
          E_stability    CoM/CoP balance            (IPMAN)
          E_smooth       temporal jerk penalty      (LEMO)
          │
          └── MuJoCo Validation (verify, don't correct)
          │
          → Simulation-ready motion + contact labels
```

---

## 7. 3D Scene Reconstruction

### Depth Anything 3 (Primary — Released)

| Feature | DA3 | Metric3D v2 | CUT3R | ZipMap |
|---------|-----|------------|-------|--------|
| Metric depth | Yes | **Best** | Yes | No (relative) |
| Camera poses | **Yes** | No | Yes | Yes |
| Pointmaps | **Yes** | No | Yes | Yes |
| Streaming video | **Yes (<12GB)** | No | Yes | Yes* |
| License | **Apache-2.0** | Apache-2.0 | CC BY-NC-SA | Unknown |
| Released | **Yes** | Yes | Yes | **No** |

**Runtime**: DA3-Large: 78 FPS, <12 GB VRAM, any video length.

**GitHub**: https://github.com/ByteDance-Seed/Depth-Anything-3

### DUSt3R / MASt3R (Dense Scene Reconstruction)

```bash
# DUSt3R
git clone --recursive https://github.com/naver/dust3r && cd dust3r
conda create -n dust3r python=3.11 cmake=3.14.0
conda install pytorch torchvision pytorch-cuda=12.1 -c pytorch -c nvidia
pip install -r requirements.txt

# MASt3R (builds on DUSt3R, adds local features + metric pointmaps)
git clone --recursive https://github.com/naver/mast3r && cd mast3r
pip install -r requirements.txt && pip install -r dust3r/requirements.txt
```

```python
from mast3r.model import AsymmetricMASt3R
model = AsymmetricMASt3R.from_pretrained("naver/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric")
```

### Placing Humans into Reconstructed Scenes

1. Reconstruct 3D scene from video frames (DUSt3R/MASt3R/DA3) → metric 3D point cloud + camera poses
2. Recover human meshes in world coordinates (GVHMR/WHAM/TRAM)
3. Align coordinate systems via shared camera poses
4. Scene provides ground plane for grounding feet and preventing penetration

---

## 8. 3D Mesh Visualization & UI

### Rendering Libraries Comparison

| Library | Best For | Used By | Install |
|---------|---------|---------|---------|
| **Pyrender** | Paper figures (offline) | HMR, VIBE, SPIN, PyMAF, VirtualMarker | `pip install pyrender` |
| **PyTorch3D** | Differentiable rendering (training) | SHERT, BLADE, DensePose | `pip install pytorch3d` |
| **MMHuman3D** | All-in-one SMPL pipeline | OpenMMLab ecosystem | `pip install mmhuman3d` |
| **Trimesh** | Mesh data structure | Nearly universal | `pip install trimesh` |
| **Open3D** | Interactive desktop viz | SHERT | `pip install open3d` |

### Colored Meshes (Different Color per Person)

**Pyrender:**
```python
import pyrender, trimesh
colors = [(0.8,0.3,0.3,1.0), (0.3,0.3,0.8,1.0), (0.3,0.8,0.3,1.0), (0.8,0.8,0.3,1.0)]
for i, verts in enumerate(person_vertices):
    material = pyrender.MetallicRoughnessMaterial(
        metallicFactor=0.0, alphaMode='OPAQUE',
        baseColorFactor=colors[i % len(colors)]
    )
    tm = trimesh.Trimesh(vertices=verts, faces=smpl_faces)
    mesh = pyrender.Mesh.from_trimesh(tm, material=material)
    scene.add(mesh)
```

**PyTorch3D:**
```python
from pytorch3d.structures import Meshes, join_meshes_as_scene
from pytorch3d.renderer import TexturesVertex

meshes = []
for i, verts in enumerate(person_vertices):
    verts_rgb = torch.tensor(colors[i]).unsqueeze(0).expand(verts.shape[0], -1).unsqueeze(0)
    textures = TexturesVertex(verts_features=verts_rgb)
    meshes.append(Meshes(verts=[verts], faces=[faces], textures=textures))
scene = join_meshes_as_scene(meshes)
```

**MMHuman3D (easiest for multi-person):**
Pass verts with shape `(num_frame, num_person, 6890, 3)` → handles coloring automatically.

### Overlay Meshes on Video Frames

Standard approach across all libraries:
1. Render mesh to RGBA image + depth with `OffscreenRenderer`
2. Create validity mask: `valid_mask = (depth > 0)[:, :, None]`
3. Alpha-composite: `output = rendered[:,:,:3] * valid_mask + (1 - valid_mask) * original_frame`
4. Camera intrinsics must match video (`pyrender.IntrinsicsCamera(fx, fy, cx, cy)`)

### Side-by-Side Multi-Panel Views (Paper Style)

```python
import numpy as np

# Render same scene from multiple cameras
panel1 = original_frame                    # Original video
panel2 = render_with_overlay(front_cam)    # Mesh overlay (matching video camera)
panel3 = render_from_above(top_down_cam)   # Bird's-eye view
panel4 = render_from_side(side_cam)        # Side view (optional)

combined = np.concatenate([panel1, panel2, panel3], axis=1)
```

### Interactive 3D Visualization Tools

#### Rerun.io (Best for Development/Debugging)

```python
import rerun as rr
rr.init("human_mesh_demo", spawn=True)

# Log 3D mesh with per-vertex colors
rr.log("body", rr.Mesh3D(
    vertex_positions=vertices,
    vertex_colors=colors,
    triangle_indices=faces,
))
```

Features: time-synchronized 2D + 3D views, interactive navigation, streaming.
SAM 3D Body demo exists: `rerun-io/sam3d-body-rerun`.

- Install: `pip install rerun-sdk`
- GitHub: https://github.com/rerun-io/rerun

#### Viser (Web-Based Python Server)

```python
import viser
server = viser.ViserServer()
body_handle = server.scene.add_mesh_simple("/human", vertices, faces, color=(0.5, 0.5, 0.8))
```

SMPL visualizer example: https://viser.studio/main/examples/demos/smpl_visualizer/

- Install: `pip install viser`
- GitHub: https://github.com/nerfstudio-project/viser

#### React Three Fiber (Production Web Viewer)

```bash
npm install three @react-three/fiber @react-three/drei
```

Export meshes from Python as `.glb`/`.obj` → load in R3F with `useLoader(GLTFLoader, url)` → add `OrbitControls`.

#### Gradio (Quick Demos)

```python
import gradio as gr
demo = gr.Interface(fn=reconstruct_mesh, inputs=gr.Image(), outputs=gr.Model3D())
```

Supports `.obj`, `.glb`, `.gltf`, `.ply`, `.splat` with interactive 3D viewing. Dominant pattern for CVPR paper demos via Hugging Face Spaces.

### Sports-Specific Visualization

#### Bird's-Eye View (BEV)

**sportypy**: Python package for regulation playing surfaces (basketball, soccer, football, etc.)
```bash
pip install sportypy
```
- GitHub: https://github.com/sportsdataverse/sportypy

**Roboflow Supervision**: `ViewTransformer` for perspective → BEV transformation
```python
import supervision as sv
# Detect court keypoints → compute homography → transform player positions
```
- GitHub: https://github.com/roboflow/supervision + https://github.com/roboflow/sports

#### Summary: Tool by Use Case

| Use Case | Recommended Tool |
|----------|-----------------|
| Paper figures (offline render) | **Pyrender** |
| Differentiable rendering (training) | **PyTorch3D** |
| All-in-one SMPL pipeline | **MMHuman3D** |
| Interactive debugging | **Rerun.io** |
| Web-based interactive viewer | **Viser** |
| Production web viewer | **React Three Fiber** |
| Quick demo / HF Spaces | **Gradio** (`Model3D`) |
| Sports BEV tracking | **Supervision** + **sportypy** |
| Multi-person interaction | **BUDDI** / **HumanInteraction** |

---

## 9. Person-to-Person Interaction

### Contact Detection Between Meshes

1. **Proximity threshold**: Per-vertex minimum distances between meshes. Distance < 2-5 cm → contact. Use KD-trees or BVH for acceleration.
2. **Mesh intersection**: Signed distances or collision detection (`trimesh.collision`, `fcl`, MuJoCo). Negative distance = penetration = contact.
3. **Convex hull decomposition**: Per-body-part convex hulls from SMPL segments (used in combat sports paper, Feiz et al. CVPR 2025).

### Impact Force Estimation

- **Physics simulation**: Simulate both athletes in MuJoCo → contact forces from constraint solver
- **Impulse-momentum**: `F_avg * dt = m * delta_v` (velocity change at contact + anthropometric masses)
- **Conservation of momentum**: `m1*v1 + m2*v2 = m1*v1' + m2*v2'` with coefficient of restitution

### Key Interaction Papers

| Paper | Venue | Focus | GitHub |
|-------|-------|-------|--------|
| **BUDDI** | CVPR 2024 | Diffusion prior for 2-person interaction | [muelea/buddi](https://github.com/muelea/buddi) |
| **HumanInteraction** | CVPR 2024 | Interpenetration minimization + physics | [boycehbz/HumanInteraction](https://github.com/boycehbz/HumanInteraction) |
| **CloseApp** | CVPR 2025 | Appearance + proxemics reasoning | [boycehbz/CloseApp](https://github.com/boycehbz/CloseApp) |
| **InteractVLM** | CVPR 2025 | VLM-based contact point estimation | [saidwivedi/InteractVLM](https://github.com/saidwivedi/InteractVLM) |
| **Combat Sports Physics** | CVPR 2025 | Physics-based boxing pose with contacts | [hosseinfeiz.github.io/physpose](https://hosseinfeiz.github.io/physpose/) |
| **MultiPhys** | arXiv 2024 | Multi-person physics motion | [nicolasugrinovic/multiphys](https://github.com/nicolasugrinovic/multiphys) |
| **InterDyn** | CVPR 2025 | Collision dynamics via video diffusion | Paper only |

### Interaction Visualization

- Render both meshes in same scene with **different colors per person**
- Highlight **contact vertices** (red = contact, blue = non-contact)
- Show **interpenetration regions** where meshes overlap
- Use **transparency/alpha blending** for occluded body parts
- Overlay **force/momentum arrows** via matplotlib `quiver()` or 3D arrow primitives

---

## 10. Kinematics & Dynamics Extraction

### Extracting Kinematics from SMPL Meshes

#### Joint Angles

SMPL pose params: 24 joints × 3 = 72 values (axis-angle / Rodrigues representation). Joint mapping: 0=pelvis, 1=left_hip, 2=right_hip, 3=spine1, 4=left_knee, 5=right_knee, 6=spine2, 7=left_ankle, 8=right_ankle...

To get anatomical angles:
1. Extract axis-angle triplet for joint index
2. Convert to rotation matrix via Rodrigues
3. Decompose into Euler angles (ISB convention, typically ZXY)
4. Knee flexion = primary DOF in one Euler component

#### Joint Velocities & Accelerations (Finite Differences)

```python
import numpy as np

def compute_kinematics(joint_positions, dt):
    """joint_positions: (T, J, 3)"""
    # Central differences
    velocity = (joint_positions[2:] - joint_positions[:-2]) / (2 * dt)        # (T-2, J, 3)
    acceleration = (joint_positions[2:] - 2*joint_positions[1:-1] + joint_positions[:-2]) / dt**2
    return velocity, acceleration
```

Evaluation metrics: **MPJVE** (mean per-joint velocity error, cm/s), **Jitter** (jerk, 10² m/s³).

#### Center of Mass Trajectory

```python
# Weighted average using de Leva (1996) segment mass fractions
segment_masses = {'pelvis': 0.142, 'thigh': 0.100, 'shank': 0.061, ...}  # fraction of body mass
com = sum(mass * joint_pos for joint, (mass, joint_pos) in segment_data.items())
```

### Key Kinematics Libraries

| Library | Purpose | Link |
|---------|---------|------|
| `smplx` | Official SMPL/SMPL-X PyTorch | [vchoutas/smplx](https://github.com/vchoutas/smplx) |
| `SKEL` | Biomechanically accurate skeleton (46 DOF) | [MarilynKeller/SKEL](https://github.com/MarilynKeller/SKEL) |
| `SMPL2AddBiomechanics` | SMPL → OpenSim conversion | [MarilynKeller/SMPL2AddBiomechanics](https://github.com/MarilynKeller/SMPL2AddBiomechanics) |
| `scipy.spatial.transform` | Rotation conversions | Built into SciPy |

### Inverse Dynamics (Kinematics → Forces & Torques)

**Inverse dynamics** takes kinematics + external forces → solves Newton-Euler equations → net joint torques.

#### OpenSim Pipeline (Gold Standard)

```
SMPL motion (.npz/.pkl)
    │
    ▼ SMPL2AddBiomechanics
    │
OpenSim model (.osim) + joint angles (.mot)
    │
    ▼ AddBiomechanics (addbiomechanics.org)
    │
Joint angles + joint torques + GRFs
(residual forces < 2% of peak external force, ~3-5 min)
```

**Key bridge**: `SMPL2AddBiomechanics` converts SMPL sequences to scaled OpenSim skeleton models.
**SKEL model** (SigAsia 2023): Re-rigs SMPL with biomechanically accurate skeleton compatible with OpenSim.

#### OpenCap (Full Video-to-Dynamics)

Stanford's platform: smartphone videos → HRNet keypoints → OpenSim dynamics → joint angles, moments, muscle activations, contact forces. 25x faster and <1% cost of lab-based approaches.

- GitHub: https://github.com/stanfordnmbl/opencap-core
- Paper: PLOS Computational Biology 2023

#### MuJoCo Inverse Dynamics

```python
import mujoco
# mj_inverse() computes forces/torques from state (pos, vel, acc)
# Exact for the model's dynamics equations
```

#### Learning-Based (from Video)

| Paper | Venue | Key Result |
|-------|-------|-----------|
| **PhysPT** | CVPR 2024 | Estimates torques + contact forces from monocular video. -83.8% accel error, -68.7% skating |
| **FinePhys** | 2024-2025 | Explicit Euler-Lagrange parameter estimation from video |
| **Calibrationless Monocular Vision** | ScienceDirect 2024 | Single smartphone → OpenSim. GRF MAE 5.0% BW |

---

## 11. Sports Biomechanics from Video

### Sport-Specific Metrics

| Metric | Approach | Status |
|--------|----------|--------|
| **Sprint speed** | OpenPose + pixel-to-metric calibration, stride analysis | Working, validated |
| **Jump height** | CoM tracking + flight time measurement | Good accuracy vs force plates |
| **Throwing velocity** | Wrist/hand keypoint tracking + calibration | Emerging |
| **Barbell velocity** | VBT apps with computer vision | Commercially deployed |

### Key Datasets & Benchmarks

| Dataset | Focus | What It Provides |
|---------|-------|-----------------|
| **AthleticsPose** (2025) | Athletics movements | 8 synced cameras, 23 athletes |
| **AthletePose3D** (CVPR 2025) | Athletic 3D HPE | Kinematic validation |
| **FineSports** (CVPR 2024) | Multi-person hierarchical sports | Fine-grained action assessment |
| **RICH** | Scene scans + vertex contact GT | SMPL-X, 3D scenes, vertex contacts |
| **Hi4D** | Multi-person close interaction | 4D scans, vertex contacts |

### Injury Risk Prediction

- **BINN** (2025): Fuses kinematic + physiological + performance data with attention mechanisms
- **IPE-DL** (2025): Permutation entropy + deep learning for injury prediction
- **CNNs/RNNs** (ScienceDirect 2025): LSTM achieved 91.5% accuracy on biometric/motion data

---

## 12. MuJoCo Integration

### SMPL → MuJoCo Conversion

**SMPLSim** by Zhengyi Luo — the primary tool:

```bash
pip install smpl_sim
```

```python
from smpl_sim.smpl_robot import SMPL_Robot

# Generate MuJoCo XML for SMPL humanoid matching subject's body shape
robot = SMPL_Robot(
    model_path='models/smpl/',
    gender='neutral',
    mesh=True  # mesh-based collision (vs capsule-based)
)
robot.write_xml("humanoid.xml")
```

- Supports MuJoCo >= 3 and Isaac Gym
- Capsule-based (faster) or mesh-based (more accurate) collision
- Any gender and body shape via beta parameters

**GitHub**: https://github.com/ZhengyiLuo/SMPLSim

### Full Pipeline: Video → MuJoCo Simulation

```
1. Video → SMPL (via GVHMR/WHAM/HMR2)
   └── Per-frame SMPL parameters (pose, shape, translation)

2. SMPL → MuJoCo XML (via SMPLSim)
   └── Articulated rigid-body model matching subject's body

3. Motion retargeting
   └── SMPL axis-angle → MuJoCo joint quaternions
   └── Joint limit clamping

4. Physics simulation
   └── Option A: UHC/PHC RL controller for physical replay
   └── Option B: mj_inverse() for inverse dynamics

5. Contact simulation
   └── Enable mesh/capsule collisions
   └── MuJoCo computes contact forces automatically
```

### Related Simulation Tools

| Tool | Purpose | GitHub |
|------|---------|--------|
| **SMPLSim** | SMPL → MuJoCo XML | [ZhengyiLuo/SMPLSim](https://github.com/ZhengyiLuo/SMPLSim) |
| **UHC** | Universal Humanoid Controller | [ZhengyiLuo/UHC](https://github.com/ZhengyiLuo/UHC) |
| **PHC** | Perpetual Humanoid Control | [ZhengyiLuo/PHC](https://github.com/ZhengyiLuo/PHC) |
| **HumEnv** | SMPL humanoid RL environment | [facebookresearch/humenv](https://github.com/facebookresearch/humenv) |
| **GMR** | Motion retargeting to robots | [YanjieZe/GMR](https://github.com/YanjieZe/GMR) |
| **O2MConverter** | OpenSim → MuJoCo converter | [aikkala/O2MConverter](https://github.com/aikkala/O2MConverter) |
| **Combat Sports** (CVPR 2025) | Multi-person physics with SMPL | [hosseinfeiz.github.io/physpose](https://hosseinfeiz.github.io/physpose/) |

---

## 13. Full Dependency Stack

### Core Python Environment

```bash
conda create -n pact3d python=3.10 -y
conda activate pact3d

# PyTorch (CUDA 12.1)
pip install torch==2.3.0 torchvision==0.18.0 --index-url https://download.pytorch.org/whl/cu121
```

### Segmentation & Tracking

```bash
# SAM 2
git clone https://github.com/facebookresearch/sam2.git
cd sam2 && pip install -e . && cd ..

# Grounded SAM 2
git clone https://github.com/IDEA-Research/Grounded-SAM-2.git

# YOLO + BoT-SORT
pip install ultralytics
```

### Human Mesh Recovery

```bash
# GVHMR
git clone https://github.com/zju3dv/GVHMR
cd GVHMR && pip install -r requirements.txt && pip install -e . && cd ..

# SMPL body model
pip install smplx[all]
# Download SMPL files from smpl.is.tue.mpg.de (registration required)

# SAM-Body4D (if using MHR pipeline)
git clone https://github.com/gaomingqi/sam-body4d
```

### Scene Reconstruction

```bash
# Depth Anything 3
git clone https://github.com/ByteDance-Seed/Depth-Anything-3

# DUSt3R
git clone --recursive https://github.com/naver/dust3r

# MASt3R
git clone --recursive https://github.com/naver/mast3r
```

### Physics

```bash
pip install mujoco
pip install smpl_sim  # SMPLSim for SMPL→MuJoCo

# PhysPT
git clone https://github.com/zhangy76/PhysPT

# MultiPhys
git clone https://github.com/nicolasugrinovic/multiphys
```

### Biomechanics

```bash
# SKEL (biomechanical skeleton)
git clone https://github.com/MarilynKeller/SKEL

# SMPL → OpenSim
git clone https://github.com/MarilynKeller/SMPL2AddBiomechanics

# OpenSim → MuJoCo
git clone https://github.com/aikkala/O2MConverter
```

### Visualization

```bash
pip install pyrender trimesh open3d
pip install rerun-sdk
pip install viser
pip install mmhuman3d
pip install sportypy supervision
pip install gradio

# For headless servers
pip install PyOpenGL PyOpenGL_accelerate
# Set: os.environ["PYOPENGL_PLATFORM"] = "osmesa"
```

### Frontend (if building web UI)

```bash
npm install three @react-three/fiber @react-three/drei
npm install react react-dom typescript tailwindcss
```

---

## 14. Recommended Pipeline Configurations

### Config A: Research Demo (Fastest to Results)

**Goal**: Get colored 3D meshes overlaid on sports video ASAP.

```
Video → YOLO11 detect → BoT-SORT track → SAM 2 masklets
     → Crop per person → GVHMR (world-grounded SMPL)
     → Pyrender overlay (different color per person)
     → Side-by-side: original | mesh overlay | top-down view
```

**VRAM**: ~16 GB | **Time**: ~2 min / 1K frames | **Complexity**: Medium

### Config B: Full SAM-Body4D Pipeline

**Goal**: Highest quality 4D meshes with occlusion handling.

```
Video → SAM 3 masklets → Diffusion-VAS refinement
     → SAM 3D Body (MHR meshes) → Kalman smoothing
     → DA3 scene geometry → Mesh overlay
```

**VRAM**: ~32 GB (A100) | **Time**: ~15-30 min / 30s video | **Complexity**: High

### Config C: Full Pact3D Stack (Physics + Biomechanics)

**Goal**: World-grounded, physically plausible motion with biomechanics.

```
Video → YOLO11 + BoT-SORT → SAM 2 → per-person crops
     → GVHMR (world SMPL) → DA3 (scene + ground plane)
     → PhysPT (physics refinement) → MuJoCo (validation)
     → SMPL2AddBiomechanics → OpenSim (joint torques, GRFs)
     → Rerun.io / Viser (interactive 3D viewer)
     → sportypy (BEV court overlay)
```

**VRAM**: ~20 GB | **Time**: ~5-10 min / 1K frames | **Complexity**: High

### Config D: Multi-Person Interaction Analysis

**Goal**: Detect and quantify player-to-player contacts in sports.

```
Video → YOLO11 + BoT-SORT → SAM 2 → per-person crops
     → GVHMR per person → MultiPhys (multi-person physics)
     → Mesh proximity → contact detection (< 5cm threshold)
     → Impulse-momentum analysis → force estimation
     → Colored meshes + contact highlights + force arrows
```

---

## 15. All References & GitHub Repos

### Segmentation & Tracking

| Component | GitHub | Paper |
|-----------|--------|-------|
| SAM 2 | [facebookresearch/sam2](https://github.com/facebookresearch/sam2) | arXiv:2408.00714 |
| SAM 3D Body | [facebookresearch/sam-3d-body](https://github.com/facebookresearch/sam-3d-body) | arXiv:2602.15989 |
| SAM-Body4D | [gaomingqi/sam-body4d](https://github.com/gaomingqi/sam-body4d) | arXiv:2512.08406 |
| MHR | [facebookresearch/MHR](https://github.com/facebookresearch/MHR) | — |
| SAM2MOT | [TripleJoy/SAM2MOT](https://github.com/TripleJoy/SAM2MOT) | AAAI 2026 |
| SAM2Long | [Mark12Ding/SAM2Long](https://github.com/Mark12Ding/SAM2Long) | ICCV 2025 |
| Grounded SAM 2 | [IDEA-Research/Grounded-SAM-2](https://github.com/IDEA-Research/Grounded-SAM-2) | — |
| BoT-SORT | [NirAharon/BoT-SORT](https://github.com/NirAharon/BoT-SORT) | — |

### Human Mesh Recovery

| Component | GitHub | Paper |
|-----------|--------|-------|
| GVHMR | [zju3dv/GVHMR](https://github.com/zju3dv/GVHMR) | SigAsia 2024 |
| Human3R | [fanegg/Human3R](https://github.com/fanegg/Human3R) | ICLR 2026 |
| WHAM | [yohanshin/WHAM](https://github.com/yohanshin/WHAM) | CVPR 2024 |
| TRAM | [yufu-wang/tram](https://github.com/yufu-wang/tram) | ECCV 2024 |
| SLAHMR | [vye16/slahmr](https://github.com/vye16/slahmr) | CVPR 2023 |
| TRACE | [Arthur151/ROMP](https://github.com/Arthur151/ROMP) | CVPR 2023 |
| TokenHMR | [saidwivedi/TokenHMR](https://github.com/saidwivedi/TokenHMR) | CVPR 2024 |
| SAT-HMR | [ChiSu001/SAT-HMR](https://github.com/ChiSu001/SAT-HMR) | CVPR 2025 |
| smplx | [vchoutas/smplx](https://github.com/vchoutas/smplx) | — |

### Scene Reconstruction

| Component | GitHub | Paper |
|-----------|--------|-------|
| Depth Anything 3 | [ByteDance-Seed/Depth-Anything-3](https://github.com/ByteDance-Seed/Depth-Anything-3) | Apache-2.0 |
| DUSt3R | [naver/dust3r](https://github.com/naver/dust3r) | CVPR 2024 |
| MASt3R | [naver/mast3r](https://github.com/naver/mast3r) | ECCV 2024 |
| ZipMap | [Haian-Jin/ZipMap](https://github.com/Haian-Jin/ZipMap) | CVPR 2026 (unreleased) |

### Physics & Simulation

| Component | GitHub | Paper |
|-----------|--------|-------|
| PhysPT | [zhangy76/PhysPT](https://github.com/zhangy76/PhysPT) | CVPR 2024 |
| MultiPhys | [nicolasugrinovic/multiphys](https://github.com/nicolasugrinovic/multiphys) | CVPR 2024 |
| PhysHMR | — (no code) | SigAsia 2025 |
| PHC | [ZhengyiLuo/PHC](https://github.com/ZhengyiLuo/PHC) | ICCV 2023 |
| SMPLSim | [ZhengyiLuo/SMPLSim](https://github.com/ZhengyiLuo/SMPLSim) | — |
| UHC | [ZhengyiLuo/UHC](https://github.com/ZhengyiLuo/UHC) | — |
| HumEnv | [facebookresearch/humenv](https://github.com/facebookresearch/humenv) | — |
| MuJoCo | [google-deepmind/mujoco](https://github.com/google-deepmind/mujoco) | Apache-2.0 |

### Biomechanics

| Component | GitHub | Paper |
|-----------|--------|-------|
| SKEL | [MarilynKeller/SKEL](https://github.com/MarilynKeller/SKEL) | SigAsia 2023 |
| SMPL2AddBiomechanics | [MarilynKeller/SMPL2AddBiomechanics](https://github.com/MarilynKeller/SMPL2AddBiomechanics) | — |
| OpenCap | [stanfordnmbl/opencap-core](https://github.com/stanfordnmbl/opencap-core) | PLOS Comp Bio 2023 |
| O2MConverter | [aikkala/O2MConverter](https://github.com/aikkala/O2MConverter) | — |
| GMR | [YanjieZe/GMR](https://github.com/YanjieZe/GMR) | ICRA 2026 |

### Interaction

| Component | GitHub | Paper |
|-----------|--------|-------|
| BUDDI | [muelea/buddi](https://github.com/muelea/buddi) | CVPR 2024 |
| HumanInteraction | [boycehbz/HumanInteraction](https://github.com/boycehbz/HumanInteraction) | CVPR 2024 |
| CloseApp | [boycehbz/CloseApp](https://github.com/boycehbz/CloseApp) | CVPR 2025 |
| InteractVLM | [saidwivedi/InteractVLM](https://github.com/saidwivedi/InteractVLM) | CVPR 2025 |
| Combat Sports Physics | [hosseinfeiz.github.io/physpose](https://hosseinfeiz.github.io/physpose/) | CVPR 2025 |

### Visualization

| Component | GitHub | Install |
|-----------|--------|---------|
| Pyrender | [mmatl/pyrender](https://github.com/mmatl/pyrender) | `pip install pyrender` |
| PyTorch3D | [facebookresearch/pytorch3d](https://github.com/facebookresearch/pytorch3d) | `pip install pytorch3d` |
| MMHuman3D | [open-mmlab/mmhuman3d](https://github.com/open-mmlab/mmhuman3d) | `pip install mmhuman3d` |
| Rerun.io | [rerun-io/rerun](https://github.com/rerun-io/rerun) | `pip install rerun-sdk` |
| Viser | [nerfstudio-project/viser](https://github.com/nerfstudio-project/viser) | `pip install viser` |
| sportypy | [sportsdataverse/sportypy](https://github.com/sportsdataverse/sportypy) | `pip install sportypy` |
| Supervision | [roboflow/supervision](https://github.com/roboflow/supervision) | `pip install supervision` |

---

*Compiled from deep research across 5 parallel agents covering SAM 3D/Body4D, GVHMR/PhysHMR/ZipMap, 3D mesh visualization, kinematics/dynamics, and codebase analysis. March 2026.*

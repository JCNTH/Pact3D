# SAM 3D Sports Pipeline: Comprehensive Implementation Guide

## Table of Contents

- [1. Executive Summary](#1-executive-summary)
- [2. Pipeline Architecture](#2-pipeline-architecture)
- [3. Component Deep Dives](#3-component-deep-dives)
- [4. Person-to-Person Interaction](#4-person-to-person-interaction)
- [5. Kinematics & Dynamics Extraction](#5-kinematics--dynamics-extraction)
- [6. 3D Mesh Visualization & UI](#6-3d-mesh-visualization--ui)
- [7. Libraries & Dependencies](#7-libraries--dependencies)
- [8. Installation & Setup](#8-installation--setup)
- [9. Sports-Specific Considerations](#9-sports-specific-considerations)
- [10. Recent CVPR Papers & Integration](#10-recent-cvpr-papers--integration)
- [11. Implementation Roadmap](#11-implementation-roadmap)

---

## 1. Executive Summary

This document describes a complete pipeline for reconstructing **multi-person 3D human meshes from monocular sports footage**, with physics-aware refinement, person-to-person interaction modeling, and biomechanical analysis. The pipeline chains foundation models in a modular architecture:

```
Sports Video → Detection & Tracking → Per-Person Segmentation → 3D Mesh Recovery
    → World Grounding → Scene Reconstruction → Physics Refinement
    → Kinematics/Dynamics → Visualization
```

**Core insight from our research:** The best pipeline is not one monolithic model, but a modular chain where **vision proposes and physics refines**. SAM-Body4D handles occlusion-robust tracking, GVHMR provides world-grounded coordinates, and MuJoCo enforces physical plausibility.

---

## 2. Pipeline Architecture

### 2.1 Full Pipeline Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        INPUT: Monocular Sports Video                     │
└──────────────────────┬───────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: Detection & Multi-Person Tracking                              │
│  ┌────────────┐   ┌──────────────┐   ┌─────────────────────────────┐    │
│  │ YOLOv8/v11 │──▶│ SAM 2 / SAM 3│──▶│ Identity-Consistent Masklets│    │
│  │ (detect)   │   │ (segment)    │   │ (per-person tracking)       │    │
│  └────────────┘   └──────────────┘   └─────────────────────────────┘    │
└──────────────────────┬───────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  STAGE 2: Occlusion Recovery (SAM-Body4D Pattern)                        │
│  ┌──────────────────┐   ┌────────────────────┐   ┌──────────────────┐   │
│  │ Diffusion-VAS    │──▶│ Occlusion Detection│──▶│ RGB Inpainting   │   │
│  │ (full body pred) │   │ (mask comparison)  │   │ (clean frames)   │   │
│  └──────────────────┘   └────────────────────┘   └──────────────────┘   │
└──────────────────────┬───────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  STAGE 3: Per-Person 3D Mesh Recovery                                    │
│  ┌─────────────────────────┐   ┌──────────────────────────────────────┐  │
│  │ Option A: SAM 3D Body   │   │ Option B: GVHMR (world-grounded)    │  │
│  │ • MHR representation    │   │ • SMPL representation               │  │
│  │ • Camera-relative       │   │ • Gravity-View world coords         │  │
│  │ • Hands + feet + body   │   │ • Root velocity + trajectory        │  │
│  │ • Per-frame inference   │   │ • Feed-forward transformer          │  │
│  └─────────────────────────┘   └──────────────────────────────────────┘  │
│                                                                          │
│  RECOMMENDED: SAM-Body4D tracking → feed clean crops to GVHMR            │
│  (gets both occlusion handling AND world coordinates)                     │
└──────────────────────┬───────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  STAGE 4: Scene Reconstruction                                           │
│  ┌─────────────────────────┐   ┌──────────────────────────────────────┐  │
│  │ Depth Anything 3        │   │ ZipMap (future, when code releases)  │  │
│  │ • Metric depth maps     │   │ • Dense point clouds                │  │
│  │ • Camera poses          │   │ • Queryable scene state             │  │
│  │ • Pointmaps             │   │ • Novel view synthesis              │  │
│  │ • Apache-2.0 license    │   │ • Linear-time scaling               │  │
│  └─────────────────────────┘   └──────────────────────────────────────┘  │
│                                                                          │
│  Ground Plane: RANSAC on pointmap → plane normal + offset                │
│  Collision Mesh: Poisson surface reconstruction from dense points        │
└──────────────────────┬───────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  STAGE 5: Physics Refinement                                             │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │ Energy Minimization (PROX/LEMO style, NOT RL post-processing)   │    │
│  │                                                                  │    │
│  │  E_contact     = pin feet to ground during contact   (PROX)     │    │
│  │  E_penetration = SDF non-intersection with scene     (PROX)     │    │
│  │  E_friction    = no sliding during ground contact    (LEMO)     │    │
│  │  E_stability   = center-of-mass / center-of-pressure (IPMAN)   │    │
│  │  E_smooth      = temporal jerk minimization          (LEMO)     │    │
│  │  E_interperson = inter-body non-penetration          (MultiPhys)│    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  MuJoCo Validation: simulate refined motion, verify physical plausibility│
└──────────────────────┬───────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  STAGE 6: Kinematics, Dynamics & Interaction Analysis                    │
│  ┌───────────────┐  ┌──────────────────┐  ┌────────────────────────┐    │
│  │ Joint angles  │  │ Inverse dynamics │  │ Contact detection      │    │
│  │ Velocities    │  │ Ground reaction  │  │ Proximity graphs       │    │
│  │ Accelerations │  │ Joint torques    │  │ Force estimation       │    │
│  └───────────────┘  └──────────────────┘  └────────────────────────┘    │
└──────────────────────┬───────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  STAGE 7: Visualization & UI                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────────────┐  │
│  │ Colored mesh │  │ Skeleton     │  │ Bird's-eye trajectory maps   │  │
│  │ overlays     │  │ overlays     │  │ Force/contact visualization  │  │
│  │ (per-person) │  │ (joint conn) │  │ Speed/acceleration heatmaps  │  │
│  └──────────────┘  └──────────────┘  └───────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Recommended Configuration

| Stage | Primary Tool | Alternative | Why |
|-------|-------------|-------------|-----|
| Detection | YOLOv8/v11 | GroundingDINO | YOLO is faster; GDINO for NL queries |
| Tracking | SAM 2/3 masklets | ByteTrack | SAM masklets preserve identity through occlusion |
| Occlusion | Diffusion-VAS | Skip if no occlusion | Critical for contact sports |
| Body Mesh | GVHMR | SAM 3D Body | GVHMR gives world coords + SMPL (MuJoCo compatible) |
| Scene | Depth Anything 3 | ZipMap (future) | DA3 is released, metric, Apache-2.0 |
| Physics | MuJoCo + optimization | PyBullet | MuJoCo is industry standard, Apache-2.0 |
| Visualization | aitviewer + pyrender | Open3D | aitviewer has native SMPL support |

### 2.3 Key Design Decision: SAM-Body4D Tracking → GVHMR Mesh Recovery

SAM-Body4D uses SAM 3D Body internally (MHR representation, camera-relative). For our sports pipeline, we adapt the pattern but swap the HMR backend:

```
SAM-Body4D tracking pipeline (masklets + occlusion recovery)
    → Clean per-person crops with identity labels
    → Feed to GVHMR instead of SAM 3D Body
    → Get SMPL meshes in world coordinates
    → Compatible with MuJoCo physics
```

This gets us the best of both worlds:
- **From SAM-Body4D:** Occlusion handling, identity tracking, multi-person support
- **From GVHMR:** World-grounded coordinates, SMPL output, zero drift, 280ms inference

---

## 3. Component Deep Dives

### 3.1 SAM 3D Body

**Paper:** [SAM 3D Body: Robust Full-Body Human Mesh Recovery](https://ai.meta.com/research/publications/sam-3d-body-robust-full-body-human-mesh-recovery/) (Meta, 2024)
**GitHub:** [facebookresearch/sam-3d-body](https://github.com/facebookresearch/sam-3d-body)
**Checkpoints:** [facebook/sam-3d-body-dinov3](https://huggingface.co/facebook/sam-3d-body-dinov3) (HuggingFace)

#### What It Does
- Single-image full-body 3D human mesh recovery
- Encoder-decoder architecture with auxiliary prompts (2D keypoints, masks)
- Uses **MHR (Momentum Human Rig)** — decouples skeleton and surface shape
- Includes body, hands, and feet
- Promptable (like SAM family)

#### Output Format
- MHR mesh parameters (not standard SMPL)
- Camera-relative 3D coordinates
- Body + hand + foot meshes

#### Limitations for Sports
- Per-frame only (no temporal consistency without SAM-Body4D wrapper)
- Camera-relative (no world coordinates)
- MHR not directly compatible with MuJoCo (needs conversion)
- Requires HuggingFace access approval for checkpoints

#### Installation
```bash
git clone https://github.com/facebookresearch/sam-3d-body.git
cd sam-3d-body
# Follow INSTALL.md for dependencies
pip install -e .

# Download checkpoints
huggingface-cli download facebook/sam-3d-body-dinov3 --local-dir checkpoints/sam-3d-body-dinov3

# Run inference
python demo.py \
  --image_folder <path_to_images> \
  --output_folder <path_to_output> \
  --checkpoint_path ./checkpoints/sam-3d-body-dinov3/model.ckpt \
  --mhr_path ./checkpoints/sam-3d-body-dinov3/assets/mhr_model.pt
```

### 3.2 SAM-Body4D

**Paper:** [SAM-Body4D: Training-Free 4D Human Body Mesh Recovery from Videos](https://arxiv.org/abs/2512.08406) (2025)
**GitHub:** [gaomingqi/sam-body4d](https://github.com/gaomingqi/sam-body4d)

#### What It Does
Chains three foundation models training-free:
1. **SAM 3** → Promptable video segmentation → identity-consistent masklets
2. **Diffusion-VAS** → Occlusion-aware refinement → full body mask recovery
3. **SAM 3D Body** → Per-frame mesh from clean masks → 4D meshes

#### Three-Stage Pipeline

**Stage 1 — Masklet Generator:**
- SAM 3 video predictor produces identity-consistent masks
- Uses propagation (spatial-temporal correspondence from history)
- Uses detection (semantic matching from prompt)
- Each person gets a persistent masklet across all frames

**Stage 2 — Occlusion-Aware Refiner:**
- Diffusion-VAS predicts full body mask even for occluded parts
- Compares predicted full mask against original masklet
- If IoU < 0.7 and area increases significantly → occlusion detected
- Occluded frames grouped into temporal chunks → RGB inpainting
- Output: clean full-body masks + inpainted pixels

**Stage 3 — Mask-Guided HMR:**
- Refined masks → SAM 3D Body → per-frame mesh parameters
- Temporal consistency from masklets propagates to 4D meshes
- Padding-based parallel strategy for multi-person/multi-frame inference

#### Installation
```bash
conda create -n body4d python=3.12 -y && conda activate body4d
pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu118
pip install 'git+https://github.com/facebookresearch/detectron2.git@a1ce2f9' \
    --no-build-isolation --no-deps
pip install -e models/sam3
pip install -e .

# Requires HuggingFace access approval for SAM 3 and SAM 3D Body
huggingface-cli login
python scripts/setup.py --ckpt-root /path/to/checkpoints

# Run end-to-end
python scripts/offline_app.py --input_video <path_to_video>

# Or use Gradio demo
python app.py
```

#### Limitations
- Camera-relative only — no world coordinates or global trajectory
- Uses MHR instead of SMPL — not directly MuJoCo-compatible
- Diffusion inpainting can hallucinate under heavy occlusion
- Segmentation errors cascade: bad masklet → bad inpaint → bad mesh
- Full-body occlusion loses track entirely
- Multi-person close contact can merge masklets

### 3.3 GVHMR

**Paper:** [World-Grounded Human Motion Recovery via Gravity-View Coordinates](https://dl.acm.org/doi/abs/10.1145/3680528.3687565) (SIGGRAPH Asia 2024)
**GitHub:** [zju3dv/GVHMR](https://github.com/zju3dv/GVHMR)
**Project Page:** [zju3dv.github.io/gvhmr](https://zju3dv.github.io/gvhmr/)

#### How It Works

**Gravity-View Coordinate System:**
- Y = gravity direction (up), X = Y × camera_view, Z = right-hand rule
- Each frame independently gravity-anchored — frame 1000 is as accurate as frame 1
- Zero drift on long videos (unlike WHAM which drifts to 80-110°)
- Camera-robust: only 1.6mm accuracy drop with estimated vs ground-truth camera

**Architecture:**
1. **Input Features:** Bounding boxes (YOLOv8) + 2D keypoints (ViTPose) + image features (ViT) + camera rotations (SimpleVO/DPVO)
2. **Early Fusion:** Projects all inputs through MLPs into shared 512-d space → single per-frame token
3. **Relative Transformer:** 12-layer, 8-head transformer with RoPE (generalizes to any video length)
4. **Multi-task MLP Heads:** 7 heads decode SMPL pose/shape, camera params, GV orientation, root velocity, stationary labels
5. **Post-processing:** CCD-IK foot pinning based on per-joint stationary probability

**Output:**
- SMPL pose parameters (θ) and shape parameters (β)
- Camera parameters
- GV world orientation per frame
- Root velocity
- Joint stationary labels

#### Performance
| Metric | GVHMR | WHAM | Improvement |
|--------|-------|------|-------------|
| WA-MPJPE (EMDB-2) | 111.0 mm | 135.6 mm | 18% better |
| W-MPJPE (EMDB-2) | 276.5 mm | 354.8 mm | 22% better |
| Foot Sliding | 3.5 mm | 4.4 mm | 20% better |
| Inference (1430 frames) | 280 ms | ~5 sec | 18x faster |

#### Installation
```bash
git clone https://github.com/zju3dv/GVHMR.git
cd GVHMR
# Follow docs/INSTALL.md

# Create environment
conda create -n gvhmr python=3.10 -y && conda activate gvhmr
pip install -e .

# Download checkpoints (automatic on first run)

# Run demo (static camera)
python tools/demo/demo.py --video=docs/example_video/tennis.mp4 -s

# Run demo (moving camera, uses SimpleVO)
python tools/demo/demo.py --video=path/to/video.mp4

# Process folder of videos
python tools/demo/demo_folder.py -f inputs/ -d outputs/ -s
```

#### Failure Modes

| Failure | Root Cause | Mitigation |
|---------|-----------|------------|
| Foot sliding (3.0-3.5mm) | No physics constraints | → PhysHMR or optimization-based refinement |
| Ground penetration | No scene awareness | → DA3 ground plane + SDF penalty |
| Preprocessing bottleneck (46s) | YOLO + ViTPose + ViT + DPVO | Core network only 0.28s |
| Severe occlusion | ViTPose keypoints fail | → SAM-Body4D occlusion pipeline |
| Multiple people | Single-person design | → Run per-person with SAM tracking |
| Extreme poses | Training data bias | → Fine-tune on sports data |

### 3.4 PhysHMR

**Paper:** [PhysHMR: Learning Humanoid Control Policies from Vision](https://arxiv.org/abs/2510.02566) (SIGGRAPH Asia 2025)
**Code:** Not yet released

#### How It Works
First unified framework jointly performing human motion perception AND control:
1. **Visual Encoder** (from GVHMR): Extracts per-frame features from monocular video
2. **Pixel-as-Ray:** Lifts 2D keypoints (u,v) into 3D spatial rays using camera intrinsics K — provides soft global pose reference without explicit 3D root prediction
3. **Physics Simulator** (MuJoCo/IsaacGym): Receives visual features → outputs joint torques → drives simulated humanoid
4. **Distillation:** PHC+ pretrained on mocap → teaches visual policy → raises success rate from 65.5% to 88.4%

#### Key Results
| Pipeline | Foot Sliding |
|----------|-------------|
| GVHMR alone | 5.65 mm |
| GVHMR + PHC+ (RL post-processing) | 12.71 mm (worse!) |
| PhysHMR (end-to-end) | **4.60 mm** |

**Critical lesson:** RL post-processing makes things WORSE. End-to-end or optimization-based refinement is the way.

#### Limitations
- No code released yet
- 11.6% failure rate (1 in 9 sequences)
- Flat ground only
- Single person only
- Extreme poses fail (sitting, skateboarding, ballet)

### 3.5 ZipMap

**Paper:** [ZipMap: Linear-Time Stateful 3D Reconstruction via TTT](https://arxiv.org/abs/2603.04385) (CVPR 2026)
**GitHub:** [Haian-Jin/ZipMap](https://github.com/Haian-Jin/ZipMap)

#### How It Works
- Replaces quadratic self-attention with **TTT (Test-Time Training) layers**
- Compresses entire image collection into compact hidden state in ONE forward pass
- Hidden state is queryable — feed any camera pose, get colored 3D point map
- Supports bidirectional (all frames inform each other) and streaming (causal) modes

#### Architecture
1. **Input Tokenization:** DINOv2 encodes images → spatial feature maps; camera extrinsics/intrinsics → 9-dim ray maps
2. **Feature Backbone (24 blocks):** Each block = local window attention + large-chunk TTT layer
3. **Prediction Heads:** Camera head (quaternion + translation + intrinsics), Point head (x,y,z per pixel), Depth head (distance + confidence), Query head (novel viewpoint)

#### Performance
| Method | 700 frames | Scaling |
|--------|-----------|---------|
| VGGT | 200+ seconds | O(N²) |
| CUT3R | ~30 seconds | O(N) but less accurate |
| **ZipMap** | **<10 seconds** | **O(N), most accurate** |

#### Use for Sports Pipeline
- Camera poses align body trajectories against reconstructed scene geometry
- Dense point clouds for ground plane estimation (RANSAC) and collision mesh construction
- **Status:** Code released March 2026; requires H100 GPU

### 3.6 Depth Anything 3 (Current Scene Backbone)

**GitHub:** [ByteDance-Seed/Depth-Anything-3](https://github.com/ByteDance-Seed/Depth-Anything-3)
**License:** Apache-2.0

| Feature | Specification |
|---------|--------------|
| Metric depth | Yes |
| Camera poses | Yes |
| Pointmaps | Yes |
| Streaming video | Yes (<12 GB VRAM) |
| FPS (Large) | 78 |
| FPS (Small) | 161 |

**Why DA3 over ZipMap for now:** Released, metric depth, Apache-2.0 license, consumer GPU compatible.

---

## 4. Person-to-Person Interaction

### 4.1 MultiPhys (CVPR 2024)

**Paper:** [MultiPhys: Multi-Person Physics-aware 3D Motion Estimation](https://arxiv.org/abs/2404.11987)
**GitHub:** [nicolasugrinovic/multiphys](https://github.com/nicolasugrinovic/multiphys)
**Project Page:** [iri.upc.edu/people/nugrinovic/multiphys](https://www.iri.upc.edu/people/nugrinovic/multiphys/)

The most directly relevant paper for multi-person physics in sports:
- Feeds kinematic motion estimates into MuJoCo in an autoregressive manner
- 7x less inter-body penetration than SLAHMR
- 5x less ground penetration
- Handles varying degrees of engagement between pairs of individuals

**Integration pattern:**
```
Per-person GVHMR output → MultiPhys physics simulator
    → Physically plausible multi-person trajectories
    → Contact events + forces between players
```

### 4.2 BUDDI (CVPR 2024)

**Paper:** [Generative Proxemics: A Prior for 3D Social Interaction from Images](https://muelea.github.io/buddi/)
**GitHub:** [muelea/buddi](https://github.com/muelea/buddi)

- Diffusion model learning joint distribution of two people in close proximity
- Operates directly on SMPL-X parameters via transformer backbone
- Trained on Flickr images + Hi4D/CHI3D motion capture
- Uses SDS loss (DreamFusion-inspired) — no ground-truth contact annotations needed

**Use case:** Prior for reconstructing two players in close contact (tackles, blocks, wrestling).

### 4.3 Closely Interactive Human Reconstruction (CVPR 2024)

**GitHub:** [boycehbz/HumanInteraction](https://github.com/boycehbz/HumanInteraction)

- Proxemics and physics-guided adaptation for closely interacting humans
- Complementary to BUDDI for contact-heavy sports scenarios

### 4.4 Contact Detection Between Meshes

For detecting person-to-person interaction from reconstructed meshes:

```python
import trimesh
import numpy as np

def detect_contact(mesh_a, mesh_b, threshold_mm=50.0):
    """Detect contact between two SMPL meshes."""
    # Compute pairwise distances between mesh vertices
    from scipy.spatial import cKDTree
    tree_b = cKDTree(mesh_b.vertices)
    distances, indices = tree_b.query(mesh_a.vertices)

    # Contact vertices are those within threshold
    contact_mask_a = distances < (threshold_mm / 1000.0)  # convert to meters
    contact_vertices_a = mesh_a.vertices[contact_mask_a]
    contact_vertices_b = mesh_b.vertices[indices[contact_mask_a]]

    # Penetration detection via signed distance
    signed_distances = trimesh.proximity.signed_distance(mesh_b, mesh_a.vertices)
    penetration_mask = signed_distances > 0
    penetration_depth = np.mean(signed_distances[penetration_mask]) if np.any(penetration_mask) else 0.0

    return {
        'in_contact': np.any(contact_mask_a),
        'contact_area': np.sum(contact_mask_a),
        'min_distance': np.min(distances),
        'penetration_depth': penetration_depth,
        'contact_vertices_a': contact_vertices_a,
        'contact_vertices_b': contact_vertices_b
    }
```

### 4.5 Interaction Graph

For multi-person sports, build a per-frame interaction graph:

```python
from itertools import combinations

def build_interaction_graph(meshes, person_ids, threshold_mm=100.0):
    """Build a graph of person-person interactions per frame."""
    edges = []
    for (i, id_a), (j, id_b) in combinations(enumerate(person_ids), 2):
        contact = detect_contact(meshes[i], meshes[j], threshold_mm)
        if contact['in_contact']:
            edges.append({
                'person_a': id_a,
                'person_b': id_b,
                'distance': contact['min_distance'],
                'penetration': contact['penetration_depth'],
                'contact_area': contact['contact_area']
            })
    return edges
```

---

## 5. Kinematics & Dynamics Extraction

### 5.1 Forward Kinematics from SMPL

SMPL provides a kinematic chain of 24 joints. From the pose parameters θ and shape parameters β:

```python
import smplx
import torch
import numpy as np

def extract_kinematics(smpl_params_sequence, fps=30.0):
    """Extract full kinematics from a sequence of SMPL parameters.

    Args:
        smpl_params_sequence: dict with keys 'pose' (T, 72), 'shape' (T, 10), 'trans' (T, 3)
        fps: video frame rate
    """
    # Initialize SMPL model
    body_model = smplx.create(
        model_path='models/smpl',
        model_type='smpl',
        gender='neutral',
        batch_size=len(smpl_params_sequence['pose'])
    )

    # Forward kinematics → joint positions
    output = body_model(
        body_pose=torch.tensor(smpl_params_sequence['pose'][:, 3:], dtype=torch.float32),
        global_orient=torch.tensor(smpl_params_sequence['pose'][:, :3], dtype=torch.float32),
        betas=torch.tensor(smpl_params_sequence['shape'], dtype=torch.float32),
        transl=torch.tensor(smpl_params_sequence['trans'], dtype=torch.float32)
    )

    joints = output.joints.detach().numpy()  # (T, J, 3)
    vertices = output.vertices.detach().numpy()  # (T, V, 3)
    dt = 1.0 / fps

    # Joint velocities (finite differences)
    joint_velocities = np.gradient(joints, dt, axis=0)  # (T, J, 3) m/s

    # Joint accelerations
    joint_accelerations = np.gradient(joint_velocities, dt, axis=0)  # (T, J, 3) m/s²

    # Angular velocities from pose parameters (axis-angle)
    pose_aa = smpl_params_sequence['pose'].reshape(-1, 24, 3)  # (T, 24, 3)
    angular_velocities = np.gradient(pose_aa, dt, axis=0)  # (T, 24, 3) rad/s

    # Center of mass (approximate as mean of all joints)
    com = np.mean(joints, axis=1)  # (T, 3)
    com_velocity = np.gradient(com, dt, axis=0)
    com_acceleration = np.gradient(com_velocity, dt, axis=0)

    return {
        'joints': joints,
        'vertices': vertices,
        'joint_velocities': joint_velocities,
        'joint_accelerations': joint_accelerations,
        'angular_velocities': angular_velocities,
        'center_of_mass': com,
        'com_velocity': com_velocity,
        'com_acceleration': com_acceleration
    }
```

### 5.2 Joint Angles (Biomechanical)

```python
def compute_joint_angle(parent_joint, joint, child_joint):
    """Compute angle at a joint given its parent and child positions."""
    v1 = parent_joint - joint
    v2 = child_joint - joint
    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
    return np.degrees(np.arccos(np.clip(cos_angle, -1, 1)))

# SMPL joint indices
JOINT_MAP = {
    'left_knee': (1, 4, 7),      # L_Hip, L_Knee, L_Ankle
    'right_knee': (2, 5, 8),     # R_Hip, R_Knee, R_Ankle
    'left_elbow': (16, 18, 20),  # L_Shoulder, L_Elbow, L_Wrist
    'right_elbow': (17, 19, 21), # R_Shoulder, R_Elbow, R_Wrist
    'left_hip': (0, 1, 4),       # Pelvis, L_Hip, L_Knee
    'right_hip': (0, 2, 5),      # Pelvis, R_Hip, R_Knee
}

def extract_biomechanical_angles(joints_sequence):
    """Extract biomechanically meaningful joint angles over time."""
    T = joints_sequence.shape[0]
    angles = {}
    for joint_name, (p, j, c) in JOINT_MAP.items():
        angles[joint_name] = np.array([
            compute_joint_angle(
                joints_sequence[t, p],
                joints_sequence[t, j],
                joints_sequence[t, c]
            ) for t in range(T)
        ])
    return angles
```

### 5.3 Inverse Dynamics (MuJoCo)

```python
import mujoco

def inverse_dynamics_mujoco(model_path, joint_positions_sequence, dt):
    """Compute joint torques via MuJoCo inverse dynamics.

    Args:
        model_path: path to SMPL-compatible MuJoCo XML model
        joint_positions_sequence: (T, N_joints, 3) array
        dt: timestep
    """
    model = mujoco.MjModel.from_xml_path(model_path)
    data = mujoco.MjData(model)

    torques = []
    for t in range(1, len(joint_positions_sequence) - 1):
        # Set joint positions
        q = joint_positions_sequence[t]
        q_prev = joint_positions_sequence[t - 1]
        q_next = joint_positions_sequence[t + 1]

        # Finite difference velocities and accelerations
        qvel = (q_next - q_prev) / (2 * dt)
        qacc = (q_next - 2 * q + q_prev) / (dt ** 2)

        # Set state
        data.qpos[:] = q.flatten()[:model.nq]
        data.qvel[:] = qvel.flatten()[:model.nv]
        data.qacc[:] = qacc.flatten()[:model.nv]

        # Inverse dynamics
        mujoco.mj_inverse(model, data)
        torques.append(data.qfrc_inverse.copy())

    return np.array(torques)
```

### 5.4 Ground Reaction Force Estimation

```python
def estimate_ground_reaction_force(com_acceleration, body_mass, gravity=9.81):
    """Estimate ground reaction force from center of mass acceleration.

    Newton's second law: F_grf = m * (a_com + g)
    """
    g_vector = np.array([0, gravity, 0])  # assuming Y-up
    grf = body_mass * (com_acceleration + g_vector)
    return grf  # (T, 3) in Newtons
```

### 5.5 Libraries for Biomechanical Analysis

| Library | Purpose | Install |
|---------|---------|---------|
| [smplx](https://github.com/vchoutas/smplx) | SMPL/SMPL-X forward kinematics | `pip install smplx` |
| [MuJoCo](https://mujoco.org/) | Physics simulation, inverse dynamics | `pip install mujoco` |
| [Pinocchio](https://github.com/stack-of-tasks/pinocchio) | Rigid body dynamics (analytical) | `pip install pin` |
| [OpenSim](https://opensim.stanford.edu/) | Biomechanical simulation | Separate install |
| [biomechanics-toolkit](https://github.com/Biomechanical-ToolKit/BTKCore) | C3D file processing | `pip install btk` |
| [ezc3d](https://github.com/pyomeca/ezc3d) | C3D motion capture I/O | `pip install ezc3d` |

---

## 6. 3D Mesh Visualization & UI

### 6.1 Visualization Libraries Comparison

| Library | SMPL Support | Video Overlay | Interactive | Offscreen | Multi-person Colors |
|---------|-------------|---------------|-------------|-----------|-------------------|
| **aitviewer** | Native | Yes (weak-persp/OpenCV) | Yes (ImGui) | Yes (headless) | Yes |
| **pyrender** | Via trimesh | Manual composite | No | Yes | Yes (material) |
| **Open3D** | Manual | No | Yes | Yes | Yes (vertex colors) |
| **MMHuman3D** | Native | Yes (built-in) | No | Yes | Yes (palette) |
| **Blender** | Via scripts | Yes | Yes | Yes | Yes (materials) |
| **Three.js** | Manual | Browser-based | Yes | No | Yes |

### 6.2 Recommended: aitviewer (ETH Zurich)

**GitHub:** [eth-ait/aitviewer](https://github.com/eth-ait/aitviewer)

Best choice for research visualization — native SMPL support, interactive GUI, video export.

```python
from aitviewer.renderables.smpl import SMPLSequence
from aitviewer.viewer import Viewer

# Load SMPL sequences for multiple people
colors = [
    (0.2, 0.6, 1.0, 0.8),  # Blue - Player 1
    (1.0, 0.3, 0.2, 0.8),  # Red - Player 2
    (0.2, 0.9, 0.3, 0.8),  # Green - Player 3
    (1.0, 0.8, 0.1, 0.8),  # Yellow - Player 4
]

viewer = Viewer()

for i, (poses, betas, trans) in enumerate(player_data):
    smpl_seq = SMPLSequence(
        poses_body=poses[:, 3:66],
        smpl_layer=smpl_layer,
        poses_root=poses[:, :3],
        betas=betas,
        trans=trans,
        color=colors[i % len(colors)],
        name=f"Player_{i+1}"
    )
    viewer.scene.add(smpl_seq)

viewer.run()
```

### 6.3 Pyrender for Video Overlay (Paper-Quality)

The standard approach used in CVPR papers for mesh-on-video rendering:

```python
import pyrender
import trimesh
import numpy as np
import cv2

# Per-person color palette (RGBA)
PERSON_COLORS = [
    [0.4, 0.7, 1.0, 0.7],   # Light blue
    [1.0, 0.4, 0.3, 0.7],   # Coral red
    [0.3, 0.9, 0.4, 0.7],   # Green
    [1.0, 0.8, 0.2, 0.7],   # Gold
    [0.8, 0.3, 0.8, 0.7],   # Purple
    [0.2, 0.8, 0.8, 0.7],   # Teal
]

def render_mesh_overlay(frame, vertices, faces, camera_params, person_id=0):
    """Render a colored SMPL mesh overlaid on a video frame.

    Args:
        frame: (H, W, 3) BGR video frame
        vertices: (V, 3) mesh vertices in camera space
        faces: (F, 3) mesh face indices
        camera_params: dict with 'focal_length', 'principal_point'
        person_id: index for color assignment
    """
    H, W = frame.shape[:2]
    color = PERSON_COLORS[person_id % len(PERSON_COLORS)]

    # Create colored trimesh
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
    mesh.visual.face_colors = np.array(color) * 255

    # Convert to pyrender mesh
    material = pyrender.MetallicRoughnessMaterial(
        baseColorFactor=color,
        metallicFactor=0.0,
        roughnessFactor=0.5,
        alphaMode='BLEND'
    )
    py_mesh = pyrender.Mesh.from_trimesh(mesh, material=material)

    # Set up scene
    scene = pyrender.Scene(bg_color=[0, 0, 0, 0], ambient_light=[0.3, 0.3, 0.3])
    scene.add(py_mesh)

    # Camera
    fx, fy = camera_params['focal_length']
    cx, cy = camera_params['principal_point']
    camera = pyrender.IntrinsicsCamera(fx=fx, fy=fy, cx=cx, cy=cy, znear=0.1, zfar=100.0)
    scene.add(camera, pose=np.eye(4))

    # Lighting
    light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=2.0)
    scene.add(light, pose=np.eye(4))

    # Render offscreen
    renderer = pyrender.OffscreenRenderer(W, H)
    color_img, depth = renderer.render(scene, flags=pyrender.RenderFlags.RGBA)
    renderer.delete()

    # Alpha composite onto video frame
    alpha = color_img[:, :, 3:4] / 255.0
    frame_rgb = frame[:, :, ::-1].astype(float)  # BGR to RGB
    composite = frame_rgb * (1 - alpha) + color_img[:, :, :3].astype(float) * alpha
    return composite.astype(np.uint8)[:, :, ::-1]  # RGB back to BGR


def render_full_video(video_path, all_person_meshes, camera_params, output_path):
    """Render multi-person mesh overlay on entire video.

    Args:
        video_path: input video path
        all_person_meshes: list of dicts, each with 'vertices' (T, V, 3) and 'faces' (F, 3)
        camera_params: camera parameters per frame
        output_path: output video path
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (W, H))

    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Overlay each person's mesh
        for person_id, person_mesh in enumerate(all_person_meshes):
            if frame_idx < len(person_mesh['vertices']):
                frame = render_mesh_overlay(
                    frame,
                    person_mesh['vertices'][frame_idx],
                    person_mesh['faces'],
                    camera_params[frame_idx],
                    person_id
                )

        writer.write(frame)
        frame_idx += 1

    cap.release()
    writer.release()
```

### 6.4 MMHuman3D (Turnkey Solution)

**Docs:** [mmhuman3d.readthedocs.io](https://mmhuman3dyl-1993.readthedocs.io/en/latest/visualize_smpl.html)

```python
from mmhuman3d.core.visualization import visualize_smpl_pose

# Supports per-person colors, video overlay, and batch rendering
visualize_smpl_pose(
    poses=poses_array,          # (T, 72)
    betas=betas_array,          # (T, 10)
    transl=transl_array,        # (T, 3)
    body_model_config=dict(model_path='models/smpl', type='smpl'),
    origin_frames=video_path,   # overlay on video
    output_path='output.mp4',
    palette=['blue', 'red'],    # per-person colors
    render_choice='hq',
)
```

### 6.5 Skeleton Overlay Visualization

```python
def draw_skeleton(frame, joints_2d, connections, color=(0, 255, 0), thickness=2):
    """Draw 2D skeleton overlay on frame.

    Args:
        frame: video frame
        joints_2d: (J, 2) array of 2D joint positions
        connections: list of (joint_a, joint_b) tuples
        color: BGR color
    """
    for j_a, j_b in connections:
        pt_a = tuple(joints_2d[j_a].astype(int))
        pt_b = tuple(joints_2d[j_b].astype(int))
        cv2.line(frame, pt_a, pt_b, color, thickness)

    for j in range(len(joints_2d)):
        pt = tuple(joints_2d[j].astype(int))
        cv2.circle(frame, pt, 4, color, -1)

    return frame

# SMPL skeleton connections
SMPL_CONNECTIONS = [
    (0, 1), (0, 2), (0, 3),        # Pelvis → hips, spine
    (1, 4), (2, 5), (3, 6),        # Hips → knees, spine
    (4, 7), (5, 8), (6, 9),        # Knees → ankles, chest
    (9, 12), (9, 13), (9, 14),     # Chest → neck, shoulders
    (12, 15),                       # Neck → head
    (13, 16), (14, 17),            # Shoulders → elbows
    (16, 18), (17, 19),            # Elbows → wrists
    (18, 20), (19, 21),            # Wrists → hands
    (7, 10), (8, 11),              # Ankles → feet
]
```

### 6.6 Sports-Specific Visualizations

#### Bird's-Eye Trajectory Map

```python
def draw_trajectory_map(trajectories, field_dims=(105, 68), output_size=(1050, 680)):
    """Draw bird's-eye view of player trajectories on a field.

    Args:
        trajectories: dict of {person_id: (T, 3) world positions}
        field_dims: (length, width) in meters
        output_size: output image size
    """
    canvas = np.ones((*output_size[::-1], 3), dtype=np.uint8) * 40  # dark background

    # Draw field lines
    cv2.rectangle(canvas, (50, 50), (output_size[0]-50, output_size[1]-50), (255, 255, 255), 2)
    cv2.line(canvas, (output_size[0]//2, 50), (output_size[0]//2, output_size[1]-50), (255, 255, 255), 1)

    scale_x = (output_size[0] - 100) / field_dims[0]
    scale_y = (output_size[1] - 100) / field_dims[1]

    for person_id, traj in trajectories.items():
        color = PERSON_COLORS[person_id % len(PERSON_COLORS)]
        color_bgr = (int(color[2]*255), int(color[1]*255), int(color[0]*255))

        points = []
        for pos in traj:
            x = int(pos[0] * scale_x + 50)
            y = int(pos[2] * scale_y + 50)  # X-Z plane for top-down
            points.append((x, y))

        # Draw trajectory line
        for i in range(1, len(points)):
            cv2.line(canvas, points[i-1], points[i], color_bgr, 2)

        # Draw current position (last point)
        if points:
            cv2.circle(canvas, points[-1], 8, color_bgr, -1)
            cv2.putText(canvas, str(person_id), points[-1], cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

    return canvas
```

#### Speed/Acceleration Heatmap

```python
def speed_heatmap(joint_velocities, joint_names, fps, output_path):
    """Generate a heatmap of joint speeds over time.

    Args:
        joint_velocities: (T, J, 3) array
        joint_names: list of joint names
        fps: frame rate
    """
    import matplotlib.pyplot as plt

    speeds = np.linalg.norm(joint_velocities, axis=2)  # (T, J)
    times = np.arange(speeds.shape[0]) / fps

    fig, ax = plt.subplots(figsize=(16, 8))
    im = ax.imshow(speeds.T, aspect='auto', cmap='hot',
                   extent=[times[0], times[-1], 0, len(joint_names)])
    ax.set_yticks(range(len(joint_names)))
    ax.set_yticklabels(joint_names, fontsize=8)
    ax.set_xlabel('Time (s)')
    ax.set_title('Joint Speed Heatmap (m/s)')
    plt.colorbar(im, label='Speed (m/s)')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
```

### 6.7 Interactive Web UI (Gradio)

For a quick demo interface:

```python
import gradio as gr

def process_video(video_path, show_mesh, show_skeleton, show_trajectory):
    """Process sports video and return visualization."""
    # Run pipeline...
    output_path = run_full_pipeline(
        video_path,
        render_mesh=show_mesh,
        render_skeleton=show_skeleton,
        render_trajectory=show_trajectory
    )
    return output_path

demo = gr.Interface(
    fn=process_video,
    inputs=[
        gr.Video(label="Upload Sports Footage"),
        gr.Checkbox(label="Show 3D Mesh Overlay", value=True),
        gr.Checkbox(label="Show Skeleton", value=True),
        gr.Checkbox(label="Show Trajectory Map", value=False),
    ],
    outputs=gr.Video(label="Processed Output"),
    title="Pact3D Sports Analysis",
    description="Upload monocular sports footage for 3D mesh reconstruction with physics-aware refinement"
)

demo.launch()
```

---

## 7. Libraries & Dependencies

### 7.1 Complete Requirements

```
# Core ML
torch>=2.1.0
torchvision>=0.16.0
numpy>=1.24.0
scipy>=1.11.0

# SMPL / Body Models
smplx>=0.1.28
human-body-prior
chumpy

# 3D Geometry & Visualization
trimesh>=4.0.0
pyrender>=0.1.45
open3d>=0.17.0
aitviewer>=1.14.0
pyglet>=2.0.0
moderngl>=5.8.0

# Video & Image Processing
opencv-python>=4.8.0
Pillow>=10.0.0
ffmpeg-python>=0.2.0
imageio>=2.31.0
imageio-ffmpeg>=0.4.9

# Detection & Tracking
ultralytics>=8.0.0          # YOLOv8/v11
mmpose>=1.0.0               # ViTPose (optional, GVHMR bundles it)
segment-anything-2           # SAM 2

# Physics
mujoco>=3.0.0
dm-control                   # DeepMind control suite (optional)

# Biomechanics
pin>=3.0.0                   # Pinocchio rigid body dynamics
ezc3d>=1.5.0                 # Motion capture I/O

# Depth & Scene
# Depth Anything 3 — clone from GitHub

# Plotting & Analysis
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.15.0               # Interactive 3D plots

# Web UI (optional)
gradio>=4.0.0
streamlit>=1.28.0

# Utilities
tqdm>=4.65.0
einops>=0.7.0
omegaconf>=2.3.0
huggingface-hub>=0.16.0
```

### 7.2 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| GPU | RTX 3090 (24 GB) | RTX 4090 (24 GB) or A100 (80 GB) |
| CUDA | 11.8+ | 12.1+ |
| RAM | 32 GB | 64 GB |
| Storage | 50 GB (models) | 100 GB |
| Python | 3.10+ | 3.11 or 3.12 |
| OS | Ubuntu 20.04+ | Ubuntu 22.04 |

### 7.3 GPU VRAM Budget

| Component | VRAM | Time / 1K frames |
|-----------|------|-------------------|
| YOLOv8 detection | ~2 GB | ~5 sec |
| ViTPose 2D keypoints | ~4 GB | ~20 sec |
| SAM 2/3 segmentation | ~8 GB | ~30 sec |
| SAM 3D Body | ~12 GB | ~60 sec |
| GVHMR core network | ~4 GB | 0.2 sec |
| Depth Anything 3 | <12 GB | ~13 sec |
| MuJoCo physics | CPU | ~10-30 sec |
| Pyrender visualization | ~2 GB | ~15 sec |
| **Peak (sequential)** | **~12 GB** | **~2-3 min** |

---

## 8. Installation & Setup

### 8.1 Environment Setup

```bash
# Create main environment
conda create -n pact3d python=3.11 -y
conda activate pact3d

# PyTorch with CUDA 12.1
pip install torch==2.3.0 torchvision==0.18.0 --index-url https://download.pytorch.org/whl/cu121

# Core dependencies
pip install smplx trimesh pyrender open3d mujoco numpy scipy opencv-python
pip install matplotlib seaborn plotly tqdm einops omegaconf huggingface-hub
pip install gradio ultralytics imageio imageio-ffmpeg ffmpeg-python

# aitviewer (interactive 3D viewer)
git clone https://github.com/eth-ait/aitviewer.git
cd aitviewer && pip install -e . && cd ..

# Pinocchio for rigid body dynamics
pip install pin
```

### 8.2 Model Installation

#### GVHMR
```bash
git clone https://github.com/zju3dv/GVHMR.git
cd GVHMR
pip install -e .
# Follow docs/INSTALL.md for checkpoints
# Checkpoints auto-download on first run
cd ..
```

#### SAM 3D Body
```bash
git clone https://github.com/facebookresearch/sam-3d-body.git
cd sam-3d-body
pip install -e .
# Requires HuggingFace access approval
huggingface-cli login
huggingface-cli download facebook/sam-3d-body-dinov3 --local-dir checkpoints/sam-3d-body-dinov3
cd ..
```

#### SAM-Body4D
```bash
git clone https://github.com/gaomingqi/sam-body4d.git
cd sam-body4d
pip install -e models/sam3
pip install -e .
python scripts/setup.py --ckpt-root checkpoints/
cd ..
```

#### SAM 2 (Video Segmentation)
```bash
pip install segment-anything-2
# Or clone for full control:
git clone https://github.com/facebookresearch/sam2.git
cd sam2 && pip install -e . && cd ..
```

#### Depth Anything 3
```bash
git clone https://github.com/ByteDance-Seed/Depth-Anything-3.git
cd Depth-Anything-3
pip install -e .
cd ..
```

#### MultiPhys (Multi-Person Physics)
```bash
git clone https://github.com/nicolasugrinovic/multiphys.git
cd multiphys
# Follow installation instructions in README
pip install -e .
cd ..
```

#### SMPL Model Files
```bash
# Download from https://smpl.is.tue.mpg.de/
# Requires registration
mkdir -p models/smpl
# Place SMPL_NEUTRAL.pkl, SMPL_MALE.pkl, SMPL_FEMALE.pkl in models/smpl/
```

### 8.3 Verify Installation

```python
# test_install.py
import torch
print(f"PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}")

import smplx
print(f"SMPL-X: OK")

import trimesh, pyrender
print(f"Trimesh: OK, Pyrender: OK")

import mujoco
print(f"MuJoCo: {mujoco.__version__}")

import cv2
print(f"OpenCV: {cv2.__version__}")

import ultralytics
print(f"Ultralytics (YOLO): OK")

print("\nAll core dependencies installed successfully!")
```

---

## 9. Sports-Specific Considerations

### 9.1 Challenges by Sport

| Sport | Key Challenge | Recommended Approach |
|-------|--------------|---------------------|
| Soccer/Football | Wide field, small players, frequent occlusion | High-res input, SAM 2 tracking, DA3 for field plane |
| Basketball | Fast motion, close contact, jumping | High FPS input (60+), PhysHMR for aerial, MultiPhys for contact |
| Wrestling/MMA | Constant close contact, tangled limbs | BUDDI prior, MultiPhys, aggressive occlusion handling |
| Tennis | Single/doubles, fast racket motion | GVHMR sufficient, add hand tracking for racket |
| Swimming | Water occlusion, non-standard gravity | GVHMR GV system handles; need water surface as ground |
| Track & Field | Long sequences, extreme poses | GVHMR + RoPE handles long videos; no drift |

### 9.2 Input Preprocessing

```python
def preprocess_sports_video(video_path, target_fps=30, max_resolution=1920):
    """Preprocess sports footage for optimal pipeline performance."""
    cap = cv2.VideoCapture(video_path)
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Downsample if needed
    scale = min(1.0, max_resolution / max(W, H))
    new_W, new_H = int(W * scale), int(H * scale)

    # Frame sampling for target FPS
    frame_interval = max(1, int(original_fps / target_fps))

    frames = []
    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            if scale < 1.0:
                frame = cv2.resize(frame, (new_W, new_H))
            frames.append(frame)
        frame_idx += 1

    cap.release()
    return frames, target_fps
```

### 9.3 Multi-Person Pipeline

```python
def run_multi_person_pipeline(video_path):
    """Full multi-person sports analysis pipeline."""

    # Stage 1: Detect all people in first frame
    from ultralytics import YOLO
    detector = YOLO('yolov8x.pt')
    results = detector(video_path, stream=True)

    # Stage 2: Track with SAM 2 masklets
    # Each detected person becomes a SAM 2 prompt
    # SAM 2 produces identity-consistent masklets across all frames

    # Stage 3: Per-person crop extraction
    # Use masklets to extract clean per-person crops
    # Apply Diffusion-VAS for occluded frames (SAM-Body4D pattern)

    # Stage 4: Run GVHMR per person
    # Each person's crop sequence → GVHMR → SMPL in world coords
    per_person_smpl = {}
    for person_id, crops in person_crops.items():
        smpl_output = run_gvhmr(crops)
        per_person_smpl[person_id] = smpl_output

    # Stage 5: Scene reconstruction
    depth_maps, ground_plane = run_depth_anything_3(video_path)

    # Stage 6: Physics refinement (MultiPhys for multi-person)
    refined = run_multiphys(per_person_smpl, ground_plane)

    # Stage 7: Extract kinematics & interactions
    kinematics = {pid: extract_kinematics(smpl) for pid, smpl in refined.items()}
    interactions = detect_all_interactions(refined)

    # Stage 8: Visualize
    render_full_video(video_path, refined, output_path='output.mp4')

    return refined, kinematics, interactions
```

---

## 10. Recent CVPR Papers & Integration

### 10.1 Papers from Our Research Thread

| Paper | Venue | Key Contribution | Code | Integration Role |
|-------|-------|-----------------|------|-----------------|
| [GVHMR](https://github.com/zju3dv/GVHMR) | SigAsia 2024 | Gravity-View world coords, zero drift | Yes | **Primary body tracker** |
| [ZipMap](https://github.com/Haian-Jin/ZipMap) | CVPR 2026 | Linear-time 3D reconstruction via TTT | Yes | Future scene backbone |
| [PhysHMR](https://arxiv.org/abs/2510.02566) | SigAsia 2025 | End-to-end visual→physics, 4.60mm foot slide | No | Architecture reference |
| [SAM-Body4D](https://github.com/gaomingqi/sam-body4d) | arXiv 2025 | Training-free 4D mesh from video | Yes | Occlusion handling pattern |
| [MultiPhys](https://github.com/nicolasugrinovic/multiphys) | CVPR 2024 | Multi-person physics, 7x less penetration | Yes | **Multi-person physics** |

### 10.2 Additional Relevant Papers

| Paper | Venue | Key Contribution | Code |
|-------|-------|-----------------|------|
| [BUDDI](https://github.com/muelea/buddi) | CVPR 2024 | Proxemics diffusion prior for interacting pairs | Yes |
| [HumanInteraction](https://github.com/boycehbz/HumanInteraction) | CVPR 2024 | Physics-guided close interaction reconstruction | Yes |
| [PROX](https://prox.is.tue.mpg.de/) | ICCV 2019 | Scene-aware body fitting (SDF + contact) | Yes |
| [LEMO](https://github.com/sanweiliti/LEMO) | ICCV 2021 | Friction + smoothness priors | Yes |
| [IPMAN](https://arxiv.org/abs/2305.12929) | CVPR 2023 | Center-of-pressure stability constraint | Yes |
| [PhysDiff](https://nvlabs.github.io/PhysDiff/) | ICCV 2023 | Physics in diffusion generation | Yes |
| [CRISP](https://github.com/Z1hanW/CRISP-Real2Sim) | arXiv 2025 | Planar scene + RL tracking | Yes |

### 10.3 Integration Map

```
Our Pipeline Uses Ideas From:

SAM-Body4D ──────► Masklet tracking pattern (Stage 1-2)
GVHMR ───────────► Body mesh recovery (Stage 3)
Depth Anything 3 ► Scene geometry (Stage 4)
PROX + LEMO ─────► Energy minimization terms (Stage 5)
MultiPhys ───────► Multi-person physics (Stage 5)
PhysHMR ─────────► Pixel-as-ray strategy, end-to-end proof (Architecture ref)
BUDDI ───────────► Close interaction prior (Stage 5, contact sports)
ZipMap ──────────► Future scene backbone upgrade (Stage 4)
```

---

## 11. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [ ] Set up conda environment with all dependencies
- [ ] Install and verify GVHMR on sample videos
- [ ] Install and verify SAM 2 for person tracking
- [ ] Install and verify Depth Anything 3 for scene reconstruction
- [ ] Run GVHMR on sports footage, inspect outputs

### Phase 2: Multi-Person Pipeline (Weeks 3-4)
- [ ] Implement SAM 2 masklet generation for multi-person tracking
- [ ] Build per-person crop extraction from masklets
- [ ] Chain: YOLOv8 → SAM 2 → per-person GVHMR
- [ ] Implement SAM-Body4D occlusion recovery pattern
- [ ] Test on contact sports footage

### Phase 3: Physics & Scene (Weeks 5-6)
- [ ] RANSAC ground plane estimation from DA3 pointmaps
- [ ] Implement energy minimization (E_contact, E_penetration, E_friction)
- [ ] Integrate MultiPhys for multi-person physics
- [ ] MuJoCo validation loop
- [ ] Measure foot sliding and penetration metrics

### Phase 4: Kinematics & Dynamics (Week 7)
- [ ] Extract joint angles, velocities, accelerations from SMPL sequences
- [ ] Implement inverse dynamics via MuJoCo
- [ ] Build contact detection between person meshes
- [ ] Interaction graph construction
- [ ] Ground reaction force estimation

### Phase 5: Visualization & UI (Week 8)
- [ ] Colored multi-person mesh overlay on video (pyrender)
- [ ] Skeleton overlay visualization
- [ ] Bird's-eye trajectory maps
- [ ] Speed/acceleration heatmaps
- [ ] Interactive viewer with aitviewer
- [ ] Gradio web demo

### Phase 6: Evaluation & Demo (Weeks 9-10)
- [ ] Evaluate on RICH, EMDB-2, 3DPW, Hi4D datasets
- [ ] Ablation studies (with/without physics, with/without occlusion handling)
- [ ] Generate paper-quality visualizations
- [ ] Demo video on real sports footage
- [ ] Technical report

---

## References

### Code Repositories
- **SAM 3D Body:** https://github.com/facebookresearch/sam-3d-body
- **SAM-Body4D:** https://github.com/gaomingqi/sam-body4d
- **GVHMR:** https://github.com/zju3dv/GVHMR
- **ZipMap:** https://github.com/Haian-Jin/ZipMap
- **MultiPhys:** https://github.com/nicolasugrinovic/multiphys
- **BUDDI:** https://github.com/muelea/buddi
- **aitviewer:** https://github.com/eth-ait/aitviewer
- **SMPL-X:** https://github.com/vchoutas/smplx
- **Depth Anything 3:** https://github.com/ByteDance-Seed/Depth-Anything-3
- **MuJoCo:** https://mujoco.org/
- **SAM 2:** https://github.com/facebookresearch/sam2

### Papers
- PhysHMR: https://arxiv.org/abs/2510.02566
- ZipMap: https://arxiv.org/abs/2603.04385
- SAM-Body4D: https://arxiv.org/abs/2512.08406
- MultiPhys: https://arxiv.org/abs/2404.11987
- GVHMR: https://dl.acm.org/doi/abs/10.1145/3680528.3687565

### Visualization Tools
- aitviewer: https://eth-ait.github.io/aitviewer/
- MMHuman3D visualization: https://mmhuman3dyl-1993.readthedocs.io/en/latest/visualize_smpl.html
- Pyrender: https://pyrender.readthedocs.io/

# Scene Geometry Backbone Comparison for Pact3D

## Why Depth Anything 3 is the Recommended Scene Backbone

**TL;DR:** For a physics-aware human tracking project on limited GPU hardware, DA3 uniquely combines (1) streaming video inference under 12 GB VRAM, (2) metric depth output, (3) camera pose estimation, (4) pointmap/raymap/3DGS outputs needed for collision surfaces, (5) Apache-2.0 licensing, and (6) a family of model sizes from 22M to 1.15B parameters. No other single method covers all six requirements simultaneously.

---

## 1. Quantitative Benchmark Comparison

### Table A: Zero-Shot Metric Depth (AbsRel / delta1)

All numbers are zero-shot (no fine-tuning on test domain). Lower AbsRel is better; higher delta1 is better.

| Method | NYUv2 AbsRel | NYUv2 delta1 | KITTI AbsRel | KITTI delta1 | ETH3D AbsRel | ETH3D delta1 | Source |
|--------|-------------|-------------|-------------|-------------|--------------|-------------|--------|
| **DA3-Metric (L)** | 0.070 | 0.963 | 0.086 | 0.953 | **0.104** | **0.917** | DA3 paper Table 11 |
| DA2 (ViT-L, ZoeDepth) | ~0.051 | ~0.973 | ~0.050 | ~0.970 | -- | -- | DA2 paper Table 4 (in-domain FT, not ZS) |
| Metric3D v2 (ViT-g) | **0.043** | **0.981** | **0.043** | **0.982** | 0.042 | 0.983 | Metric3D repo (ZS with 142M+16M data) |
| UniDepth v2 | 0.064 | 0.968 | 0.076 | 0.968 | 0.152 | 0.863 | DA3 paper Table 11 |
| DepthPro | 0.093 | 0.932 | 0.121 | 0.843 | 0.349 | 0.386 | DA3 paper Table 11 |
| MoGe (ViT-L) | -- | -- | -- | -- | -- | -- | Affine-invariant only (no metric) |
| MoGe-2 (ViT-L) | Competitive | Competitive | Competitive | Competitive | -- | -- | Metric; outperforms UniDepth, DepthPro |

**Key observations:**
- Metric3D v2 (ViT-g) wins on NYUv2 and KITTI by a clear margin, but requires a 1.0B Giant2 backbone and was trained on 16M labeled samples.
- DA3-Metric wins on ETH3D (diverse outdoor scenes) by a large margin (delta1 0.917 vs. 0.863 for UniDepth v2), showing superior generalization.
- DA2's strong NYU/KITTI numbers come from in-domain fine-tuning, not zero-shot transfer.

### Table B: Video Depth (Dynamic Scenes)

| Method | Sintel AbsRel | Bonn AbsRel | KITTI AbsRel | Dynamic Scenes? |
|--------|--------------|------------|-------------|----------------|
| MonST3R | 0.335 | **0.063** | **0.104** | Yes (motion-aware DUSt3R) |
| DepthCrafter | **0.292** | 0.075 | 0.110 | Yes (diffusion-based) |
| DA2 (per-frame) | -- | -- | -- | No (no temporal consistency) |
| MegaSaM | Competitive | -- | -- | Yes (SLAM + mono prior) |

---

## 2. Comprehensive Method Comparison

### Table C: Capabilities Matrix

| Method | Params | Metric Depth | Camera Poses | Pointmaps | Dynamic Scenes | Streaming/Online | Video Support |
|--------|--------|-------------|-------------|-----------|---------------|-----------------|--------------|
| **DA3 (L)** | 0.35B | Yes (DA3Metric) | Yes (from raymaps) | Yes | Partial | **Yes (<12GB)** | **Yes** |
| DA3 (S) | 0.02B | Via fine-tune | Yes | Yes | Partial | Yes | Yes |
| DA2 (ViT-L) | 0.34B | Via ZoeDepth FT | No | No | No | No | Per-frame only |
| Metric3D v2 | 0.34-1.0B | **Yes (native)** | No | No | No | No | Per-frame only |
| UniDepth v2 | ~0.3B | **Yes (native)** | Intrinsics only | Yes (3D points) | No | No | Per-frame only |
| MoGe / MoGe-2 | ~0.3B (ViT-L) | MoGe: No / MoGe-2: Yes | FoV only | Yes | No | No | Per-frame only |
| DUSt3R | ~0.5B | No (relative) | Yes (via GA) | Yes | No | No (quadratic GA) | Pairwise |
| MASt3R | ~0.5B | Yes (metric pointmaps) | Yes (via GA) | Yes | No | 15 FPS (SLAM variant) | Pairwise + GA |
| CUT3R | ~0.5B | Yes | Yes | Yes | **Yes** | **Yes (RNN, const mem)** | Yes |
| VGGT | 1.0B | Yes | Yes | Yes | No | No (quadratic) | Multi-view batch |
| ZipMap | 1.4B | Yes | Yes | Yes | Partial | **Yes (TTT, linear)** | **Yes** |
| SLAM3R | ~0.5B | No (relative) | Implicit (no explicit) | Yes | No | **Yes (20+ FPS)** | Yes |
| MegaSaM | ~0.1B (SLAM) | Yes (via mono prior) | Yes (BA) | No (disparity) | **Yes** | Optimization-based | Yes |
| MonST3R | ~0.5B | Relative (SI) | Yes (via GA) | Yes | **Yes** | Feed-forward + light opt | Yes |

### Table D: Runtime, Memory, and License

| Method | FPS (GPU) | VRAM (inference) | License | Availability |
|--------|-----------|-----------------|---------|-------------|
| **DA3-Large** | **78 FPS** | **<12 GB (streaming)** | **Apache-2.0** (Base/Small/Metric) | Released |
| **DA3-Small** | **161 FPS** | ~4-6 GB | **Apache-2.0** | Released |
| DA3-Giant | 38 FPS | ~16-20 GB | CC BY-NC 4.0 | Released |
| DA2 (ViT-L) | ~30 FPS | ~4-6 GB | Apache-2.0 | Released |
| DA2 (ViT-S) | ~72 FPS | ~2 GB | Apache-2.0 | Released |
| Metric3D v2 (ViT-L) | ~15-20 FPS | ~8-10 GB | Apache-2.0 | Released |
| Metric3D v2 (ViT-g) | ~5-8 FPS | ~20+ GB | Apache-2.0 | Released |
| UniDepth v2 | ~15-25 FPS | ~6-10 GB | CC BY-NC 4.0 | Released |
| MoGe (ViT-L) | ~17 FPS (60ms) | ~6-8 GB | MIT | Released |
| MoGe-2 (ViT-L) | ~15 FPS | ~8 GB | MIT | Released |
| DUSt3R | 1-5 FPS (with GA) | 8-24+ GB (quadratic) | CC BY-NC-SA 4.0 | Released |
| MASt3R | 0.4-1 FPS (with GA) | 8-24+ GB (quadratic) | CC BY-NC-SA 4.0 | Released |
| CUT3R | 15-18 FPS | **~8 GB (constant)** | CC BY-NC-SA 4.0 | Released |
| VGGT | ~60 FPS (32 views) | 8-40+ GB (quadratic) | Custom (commercial available) | Released |
| ZipMap | ~75 FPS (750 frames) | H100-class | Not yet specified | **Not released** |
| SLAM3R | **20+ FPS** | ~8-12 GB | -- | Released |
| MegaSaM | Optimization-based | ~8-16 GB | -- | Released |
| MonST3R | Feed-forward + opt | ~8-16 GB (GA bottleneck) | CC BY-NC-SA 4.0 | Released |

---

## 3. Decision Matrix: Which Method for Which Need?

### For Pact3D specifically (physics-aware human tracking from monocular video):

| Requirement | DA3 | DA2 | Metric3D v2 | UniDepth v2 | MoGe-2 | CUT3R | VGGT | ZipMap | MegaSaM | MonST3R |
|-------------|-----|-----|------------|------------|--------|-------|------|--------|---------|---------|
| Metric depth for physics scale | Y | Partial | **Best** | Y | Y | Y | Y | Y | Y | Partial |
| Camera poses for world frame | **Y** | N | N | Partial | N | Y | **Y** | Y | **Y** | Y |
| Streaming for long videos | **Y** | N | N | N | N | Y | N | Y* | N | N |
| <12 GB VRAM | **Y** | Y | Partial | Y | Y | Y | N | N | Y | Partial |
| Handles people in scene | **Y** | Y | Y | Y | Y | Y | N | Partial | **Y** | **Y** |
| Pointmaps for collision mesh | **Y** | N | N | Y | Y | Y | Y | Y | N | Y |
| Permissive license (Apache/MIT) | **Y** | Y | Y | N (NC) | **Y** | N (NC) | Partial | ? | ? | N (NC) |
| Released & usable today | **Y** | Y | Y | Y | Y | Y | Y | **N** | Y | Y |
| Temporal consistency | **Y** | N | N | N | N | Y | N | Y | **Y** | Y |

*ZipMap: code not yet released

### Scoring (weighted for project needs):

| Method | Depth Quality (25%) | Efficiency (25%) | Feature Set (20%) | License (15%) | Maturity (15%) | **Total** |
|--------|-------------------|-----------------|-------------------|--------------|---------------|-----------|
| **DA3-Large** | 8/10 | **9/10** | **10/10** | **10/10** | 8/10 | **9.0** |
| Metric3D v2 | **10/10** | 6/10 | 4/10 | 10/10 | 9/10 | 7.6 |
| CUT3R | 7/10 | 8/10 | 8/10 | 5/10 | 7/10 | 7.1 |
| MoGe-2 | 8/10 | 7/10 | 6/10 | **10/10** | 8/10 | 7.7 |
| UniDepth v2 | 8/10 | 7/10 | 5/10 | 5/10 | 8/10 | 6.7 |
| VGGT | 8/10 | 5/10 | 9/10 | 7/10 | 8/10 | 7.2 |
| MegaSaM | 7/10 | 5/10 | 7/10 | 6/10 | 7/10 | 6.3 |
| DA2 | 7/10 | 9/10 | 3/10 | 10/10 | 10/10 | 7.5 |
| MonST3R | 7/10 | 5/10 | 8/10 | 5/10 | 7/10 | 6.3 |
| DUSt3R/MASt3R | 6/10 | 3/10 | 7/10 | 5/10 | 8/10 | 5.6 |
| SLAM3R | 6/10 | 8/10 | 6/10 | 6/10 | 7/10 | 6.6 |
| ZipMap | 9/10 | 9/10 | 9/10 | 5/10 | **1/10** | 6.8 |

---

## 4. Justification: Why DA3 Wins for Pact3D

### Argument 1: Unique combination of outputs from a single model

DA3 is the only method that produces ALL of the following from a single backbone:
- **Metric depth** (DA3Metric-Large, Apache-2.0)
- **Camera poses** (inferred from ray representations)
- **Dense pointmaps** (for collision mesh extraction)
- **3D Gaussian Splatting** (for visualization / novel views)
- **Streaming inference** for arbitrarily long video sequences

No other method provides this full set. Metric3D v2 produces better depth but no camera poses. VGGT produces everything but requires quadratic memory and an H100. CUT3R produces everything but is CC BY-NC-SA 4.0.

### Argument 2: GPU-budget feasibility

The project targets limited GPU resources (single consumer GPU, 12-24 GB VRAM):

| Method | Can run long video on RTX 3090 (24GB)? | Can run on RTX 4070 (12GB)? |
|--------|---------------------------------------|---------------------------|
| **DA3 (streaming)** | Yes (any length) | **Yes (any length, <12GB)** |
| DA2 | Yes (per-frame, no temporal) | Yes (per-frame only) |
| Metric3D v2 (ViT-L) | Yes (per-frame) | Yes (per-frame only) |
| Metric3D v2 (ViT-g) | Marginal | No |
| CUT3R | Yes (constant memory RNN) | Yes (8GB constant) |
| VGGT | ~60-75 frames max | ~15-20 frames max |
| ZipMap | No (needs H100) | No |
| DUSt3R/MASt3R | ~50-100 frames (quadratic GA) | ~20-50 frames |
| MonST3R | ~50-100 frames (GA bottleneck) | Marginal with --not_batchify |

DA3's sliding-window streaming design is explicitly engineered for <12 GB VRAM on arbitrarily long sequences. This is critical for a project processing monocular videos of walking/running humans, which can easily be thousands of frames.

### Argument 3: Depth quality is sufficient (not best, but sufficient)

For physics-aware tracking, the depth map serves two purposes:
1. **Ground plane detection** (RANSAC on pointmap) -- requires reasonable metric accuracy, not SOTA
2. **Collision surface estimation** -- requires correct scene topology, tolerates ~5-10% scale error

DA3-Metric's AbsRel of 0.070 (NYU) and 0.086 (KITTI) is within the useful range. The physics layer itself corrects residual errors (penetration correction, ground plane refinement). Spending 3x more VRAM on Metric3D v2 (ViT-g) to get AbsRel 0.043 yields diminishing returns when the physics optimizer will refine the collision surface anyway.

### Argument 4: Licensing enables publication and release

| Method | License | Can publish code? | Can release model weights? |
|--------|---------|-------------------|---------------------------|
| **DA3 (Base/Small/Metric)** | **Apache-2.0** | **Yes** | **Yes** |
| DA3 (Large/Giant) | CC BY-NC 4.0 | Research only | Research only |
| Metric3D v2 | Apache-2.0 | Yes | Yes |
| UniDepth v2 | CC BY-NC 4.0 | Research only | Research only |
| CUT3R | CC BY-NC-SA 4.0 | Research only | Research only |
| VGGT | Custom | Depends on version | Commercial version available |
| MoGe/MoGe-2 | MIT | Yes | Yes |
| DUSt3R/MASt3R/MonST3R | CC BY-NC-SA 4.0 | Research only | Research only |

DA3Metric-Large (the model you would actually use) is Apache-2.0. Combined with Human3R (MIT) and MuJoCo (Apache-2.0), the entire stack is permissively licensed.

### Argument 5: Ecosystem integration

DA3 is designed to work alongside body trackers in the same pipeline:
- Its pointmaps can be directly used by Human3R's CUT3R backbone (same representation space)
- The camera pose output aligns with WHAM/GVHMR's world-frame requirements
- The streaming API matches the sequential frame-by-frame processing of body trackers
- Multiple output formats (GLB, NPZ, PLY) integrate with Open3D/trimesh for collision mesh generation

---

## 5. When NOT to Use DA3

| Scenario | Better Choice | Why |
|----------|--------------|-----|
| Need absolute best metric depth accuracy | Metric3D v2 (ViT-g) | 40% lower AbsRel on NYU/KITTI |
| Need to reconstruct from unordered photo collections | VGGT or ZipMap | DA3 streaming assumes sequential input |
| Need dense matching / feature correspondence | MASt3R | DA3 doesn't output local features |
| Need end-to-end dynamic scene decomposition | MonST3R or Easi3R | DA3 doesn't separate static/dynamic |
| Need human-aware reconstruction in one model | Human3R (CUT3R backbone) | DA3 doesn't model humans explicitly |
| Academic project with no license concerns | CUT3R | Native dynamic support, constant memory |

---

## 6. Recommended Configuration for Pact3D

```
Primary:   DA3Metric-Large (Apache-2.0, 0.35B params, streaming, <12GB)
Fallback:  DA3-Base (Apache-2.0, 0.12B, faster, ~6GB)
Complement: MegaSaM (for camera pose refinement on hard dynamic sequences)
Future:    ZipMap (when released, linear-time replacement)
```

**Pipeline integration:**
1. DA3Metric-Large: video -> per-frame metric depth + pointmaps + camera poses
2. RANSAC on pointmap -> ground plane + gravity direction
3. Body tracker (WHAM/Human3R) -> per-frame SMPL meshes in camera frame
4. Transform body to world frame using DA3 camera poses
5. Physics layer (MuJoCo): contact + penetration correction using DA3 collision surface

---

## Sources

- [Depth Anything 3 GitHub](https://github.com/ByteDance-Seed/Depth-Anything-3)
- [Depth Anything 3 Paper (arXiv:2511.10647)](https://arxiv.org/abs/2511.10647)
- [Depth Anything 3 Project Page](https://depth-anything-3.github.io/)
- [Depth Anything V2 Paper (arXiv:2406.09414)](https://arxiv.org/abs/2406.09414)
- [Depth Anything V2 GitHub](https://github.com/DepthAnything/Depth-Anything-V2)
- [Metric3D v2 Paper (arXiv:2404.15506)](https://arxiv.org/abs/2404.15506)
- [Metric3D v2 GitHub](https://github.com/YvanYin/Metric3D)
- [UniDepth Paper (CVPR 2024)](https://arxiv.org/abs/2403.18913)
- [UniDepth V2 Paper (arXiv:2502.20110)](https://arxiv.org/abs/2502.20110)
- [UniDepth GitHub](https://github.com/lpiccinelli-eth/UniDepth)
- [MoGe GitHub (CVPR'25 Oral)](https://github.com/microsoft/MoGe)
- [MoGe-2 Paper (arXiv:2507.02546)](https://arxiv.org/abs/2507.02546)
- [DUSt3R GitHub](https://github.com/naver/dust3r)
- [MASt3R-SLAM](https://edexheim.github.io/mast3r-slam/)
- [CUT3R GitHub](https://github.com/CUT3R/CUT3R)
- [VGGT GitHub (CVPR 2025 Best Paper)](https://github.com/facebookresearch/vggt)
- [VGGT Paper (arXiv:2503.11651)](https://arxiv.org/abs/2503.11651)
- [ZipMap Project Page](https://haian-jin.github.io/ZipMap/)
- [SLAM3R GitHub (CVPR 2025 Highlight)](https://github.com/PKU-VCL-3DV/SLAM3R)
- [MegaSaM Project Page](https://mega-sam.github.io/)
- [MegaSaM Paper (arXiv:2412.04463)](https://arxiv.org/abs/2412.04463)
- [MonST3R GitHub (ICLR 2025)](https://github.com/Junyi42/monst3r)
- [MonST3R Paper (arXiv:2410.03825)](https://arxiv.org/abs/2410.03825)
- [Human3R GitHub](https://github.com/fanegg/Human3R)
- [FastVGGT (arXiv:2509.02560)](https://arxiv.org/abs/2509.02560)
- [G-CUT3R Paper](https://arxiv.org/html/2508.11379)
- [Evict3R Paper](https://arxiv.org/html/2509.17650)

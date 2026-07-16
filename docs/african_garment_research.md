# African Garment 3D Reconstruction — Complete Research Compendium

> Compiled 2026-07-14 from extensive web research, codebase exploration, and academic paper analysis.

---

## Table of Contents

1. [African Wear Datasets Landscape](#1-african-wear-datasets-landscape)
2. [GarmentCode — Repository Complete Reference](#2-garmentcode--repository-complete-reference)
3. [GarmentCodeRC vs GarmentCode — Complete Diff Analysis](#3-garmentcoderc-vs-garmentcode--complete-diff-analysis)
4. [African Garment Sewing Pattern Construction](#4-african-garment-sewing-pattern-construction)
5. [Path Forward: Adding African Garments to Our Pipeline](#5-path-forward-adding-african-garments-to-our-pipeline)
6. [Academic & Computational References](#6-academic--computational-references)

---

## 1. African Wear Datasets Landscape

### Datasets That Exist (2D images only)

| Dataset | Size | Type | Content | 3D? |
|---------|------|------|---------|-----|
| **AFRIFASHION1600** (CVPRW 2021) | 1,600 | Classification | 8 classes: Agbada, Buba, Gele, Gown, etc. | ❌ |
| **InFashAI** v1/v2 | 76K | Image + captions | African fashion from Afrikrea marketplace | ❌ |
| **Afro SpecDetect** | 100K | Multimodal captions | Typologies, materials, fabrics, colors | ❌ |
| **African Attire Detector** | 12K | Classification | Adire, Tiv, Xhosa, Zulu, Shweshwe, etc. | ❌ |
| **se-Shweshwe** | 500 | Sketch→Image | South African Shweshwe dresses | ❌ |
| **Wax-MNIST** | 1,080 | Pattern classif. | Wax, Kente, Bogolan fabric patterns | ❌ |
| **Afro Fashion SD** (LoRA) | ~100K | Fine-tuned SD | African fashion image generation | ❌ |
| **AFRIFASHION40000** (NeurIPS 2021) | 40K | GAN-generated | Synthetic African fashion images | ❌ |

### The Gap

**There is ZERO existing 3D African garment datasets with sewing patterns.** All existing African fashion data is 2D images for classification/captioning. The large 3D + sewing pattern datasets (GarmentCodeData 115K, SewFactory 1M, Korosteleva Zenodo 23K) are entirely Western styles.

All major garment reconstruction datasets (DeepFashion, ModaNet, GarmentCodeData, Garment-Pattern-Generator) are Western/Asian garment types. No known 3D African garment dataset with sewing patterns exists.

### What You'd Need to Build

To get African wear (Agbada = 3-piece flowing gown + trousers + robe; Dashiki = loose tunic; Kente/Ankara fabrics) into our pipeline:

1. **Extend GarmentCode templates** — add African garment types (Agbada, Dashiki, Boubou, Kaftan) to the parametric design space. Requires pattern design expertise + CAESAR body shape sampling.
2. **Fine-tune GarmentRec on synthetic renders** — render African garments from extended GarmentCode / Maya pipeline → train GarmentRec to recognize them from images.
3. **NGL-Prompter approach** — training-free VLM prompting (2026). Uses GPT-level VLMs to extract GarmentCode parameters from any image. Could work for African garments without ANY training data. Most practical path forward.
4. **Scrape + reconstruct** — similar to what we already do (image → GarmentRec + GarmentGPT), just with African garment images. Current pipeline already works on any garment image; it just hasn't been evaluated on African styles.

**TL;DR:** No African 3D garment dataset exists. Our current image→3D pipeline already works on arbitrary garment images. The fastest path to African wear support is testing our existing pipeline against African fashion photos, or using the NGL-Prompter VLM approach (no training data needed).

---

## 2. GarmentCode — Repository Complete Reference

### 2.1 Complete Directory Tree

```
GarmentCode/
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── ReadMe.md
├── gui.py
├── pattern_data_sim.py
├── pattern_data_sim_runner.sh
├── pattern_fitter.py
├── pattern_sampler.py
├── pyproject.toml
├── setup.cfg
├── system.template.json
├── test_garment_sim.py
├── test_garmentcode.py
│
├── assets/
│   ├── bodies/
│   │   ├── Readme.md
│   │   ├── body_params.py
│   │   ├── f_smpl_average_A40.obj / .yaml       (female SMPL avg body)
│   │   ├── m_smpl_average_A40.obj / .yaml        (male SMPL avg body)
│   │   ├── mean_all.obj / .stl / .yaml
│   │   ├── mean_all_apart.obj
│   │   ├── mean_all_tpose.obj / .yaml
│   │   ├── mean_female.obj / .yaml
│   │   ├── mean_male.obj / .yaml
│   │   ├── ggg_body_segmentation.json
│   │   └── smpl_vert_segmentation.json
│   │
│   ├── design_params/
│   │   └── default.yaml                          (master config)
│   │
│   ├── garment_programs/
│   │   ├── base_classes.py       (BaseBodicePanel, BaseBottoms, StackableSkirtComponent, BaseBand)
│   │   ├── meta_garment.py       (MetaGarment -- top-level assembly)
│   │   ├── bodice.py             (BodiceFrontHalf, BodiceBackHalf, BodiceHalf, Shirt, FittedShirt)
│   │   ├── tee.py                (TorsoFrontHalfPanel, TorsoBackHalfPanel)
│   │   ├── pants.py              (PantPanel, PantsHalf, Pants)
│   │   ├── skirt_paneled.py      (SkirtPanel, ThinSkirtPanel, FittedSkirtPanel, PencilSkirt, Skirt2, SkirtManyPanels)
│   │   ├── circle_skirt.py       (SkirtCircle, AsymmSkirtCircle)
│   │   ├── skirt_levels.py       (SkirtLevels)
│   │   ├── godet.py              (GodetSkirt)
│   │   ├── sleeves.py            (SleevePanel, Sleeve, ArmholeSquare/Angle/Curve)
│   │   ├── collars.py            (collar types: CircleNeckHalf, VNeckHalf, etc.)
│   │   ├── bands.py              (StraightWB, FittedWB, cuff bands)
│   │   ├── shapes.py             (decorative cutout shapes: Sun, SIGGRAPH_logo)
│   │   └── stats_utils.py
│   │
│   ├── Patterns/
│   ├── Sim_props/
│   └── img/
│
├── pygarment/
│   ├── __init__.py
│   ├── data_config.py
│   │
│   ├── garmentcode/              *** CORE LIBRARY ***
│   │   ├── __init__.py
│   │   ├── base.py               (BaseComponent -- ABC for all garment pieces)
│   │   ├── edge.py               (Edge, CircleEdge, CurveEdge, EdgeSequence)
│   │   ├── edge_factory.py       (EdgeFactory, CircleEdgeFactory, CurveEdgeFactory, EdgeSeqFactory)
│   │   ├── panel.py              (Panel -- single flat piece of fabric)
│   │   ├── component.py          (Component -- composite of panels/sub-components)
│   │   ├── interface.py          (Interface -- stitchable edge grouping)
│   │   ├── connector.py          (StitchingRule, Stitches -- seam definitions)
│   │   ├── operators.py          (cut_corner, cut_into_edge, distribute_Y, curve_match_tangents)
│   │   ├── params.py
│   │   └── utils.py
│   │
│   ├── pattern/                  (JSON serialization, SVG visualization)
│   │   ├── core.py               (BasicPattern -- JSON round-trip)
│   │   ├── wrappers.py           (VisPattern -- SVG rendering)
│   │   ├── rotation.py
│   │   ├── utils.py
│   │   └── cairo_dlls/
│   │
│   ├── meshgen/                  (3D mesh generation from 2D patterns)
│   └── mayaqltools/              (Maya + Qualoth simulation bridge)
│
├── docs/
├── gui/
└── post_processing_scripts/
```

### 2.2 Full Garment Component Files

#### A. `pants.py` — Full Contents

```python
from copy import deepcopy
import numpy as np

import pygarment as pyg
from assets.garment_programs.base_classes import BaseBottoms
from assets.garment_programs import bands


class PantPanel(pyg.Panel):
    def __init__(
            self, name, body, design, 
            length, waist, hips, hips_depth, crotch_width,
            dart_position, match_top_int_to=None, hipline_ext=1, double_dart=False) -> None:
        """Basic pant panel with option to be fitted (with darts)"""
        super().__init__(name)

        flare = body['leg_circ'] * (design['flare']['v']  - 1) / 4 
        hips_depth = hips_depth * hipline_ext
        hip_side_incl = np.deg2rad(body['_hip_inclination'])
        dart_depth = hips_depth * 0.8 
        crotch_depth_diff =  body['crotch_hip_diff']
        crotch_extention = crotch_width

        w_diff = hips - waist   # positive since waist < hips
        hw_shift = np.tan(hip_side_incl) * hips_depth
        if hw_shift > w_diff:
            hw_shift = w_diff

        # --- Edges definition ---
        if pyg.utils.close_enough(design['flare']['v'], 1):
            right_bottom = pyg.Edge([-flare, 0], [0, length])
        else:
            right_bottom = pyg.CurveEdgeFactory.curve_from_tangents(
                [-flare, 0], [0, length],
                target_tan1=np.array([0, 1]), initial_guess=[0.75, 0])

        right_top = pyg.CurveEdgeFactory.curve_from_tangents(
            right_bottom.end, [hw_shift, length + hips_depth],
            target_tan0=np.array([0, 1]), initial_guess=[0.5, 0])
       
        top = pyg.Edge(right_top.end, [w_diff + waist, length + hips_depth])
        crotch_top = pyg.Edge(top.end, [hips, length + 0.45 * hips_depth])
        crotch_bottom = pyg.CurveEdgeFactory.curve_from_tangents(
            crotch_top.end,
            [hips + crotch_extention, length - crotch_depth_diff], 
            target_tan0=np.array([0, -1]), target_tan1=np.array([1, 0]),
            initial_guess=[0.5, -0.5])

        left = pyg.CurveEdgeFactory.curve_from_tangents(
            crotch_bottom.end,    
            [crotch_bottom.end[0] - 2 + flare, 
             y:=min(0, length - crotch_depth_diff * 1.5)], 
            target_tan1=[flare, y - crotch_bottom.end[1]],
            initial_guess=[0.3, 0])

        self.edges = pyg.EdgeSequence(
            right_bottom, right_top, top, crotch_top, crotch_bottom, left
            ).close_loop()

        self.set_pivot(crotch_bottom.end)
        self.translation = [-0.5, - hips_depth - crotch_depth_diff + 5, 0] 

        self.interfaces = {
            'outside': pyg.Interface(self, pyg.EdgeSequence(right_bottom, right_top), ruffle=[1, hipline_ext]),
            'crotch': pyg.Interface(self, pyg.EdgeSequence(crotch_top, crotch_bottom)),
            'inside': pyg.Interface(self, left),
            'bottom': pyg.Interface(self, bottom)
        }

        # Add top dart
        dart_width = w_diff - hw_shift  
        if w_diff > hw_shift:
            top_edges, int_edges = self.add_darts(
                top, dart_width, dart_depth, dart_position, double_dart=double_dart)
            self.interfaces['top'] = pyg.Interface(self, int_edges, 
                ruffle=waist / match_top_int_to if match_top_int_to is not None else 1.) 
            self.edges.substitute(top, top_edges)
        else:
            self.interfaces['top'] = pyg.Interface(self, top, 
                ruffle=waist / match_top_int_to if match_top_int_to is not None else 1.) 

    def add_darts(self, top, dart_width, dart_depth, dart_position, double_dart=False):
        if double_dart:
            dist = dart_position * 0.5
            offsets_mid = [
                -(dart_position + dist/2 + dart_width/2 + dart_width/4),   
                -(dart_position - dist/2) - dart_width/4]
            darts = [
                pyg.EdgeSeqFactory.dart_shape(dart_width/2, dart_depth * 0.9),
                pyg.EdgeSeqFactory.dart_shape(dart_width/2, dart_depth)]
        else:
            offsets_mid = [-dart_position - dart_width/2]
            darts = [pyg.EdgeSeqFactory.dart_shape(dart_width, dart_depth)]

        top_edges, int_edges = pyg.EdgeSequence(top), pyg.EdgeSequence(top)
        for off, dart in zip(offsets_mid, darts):
            left_edge_len = top_edges[-1].length()
            top_edges, int_edges = self.add_dart(
                dart, top_edges[-1],
                offset=left_edge_len + off,
                edge_seq=top_edges, int_edge_seq=int_edges)
        return top_edges, int_edges
        

class PantsHalf(BaseBottoms):
    def __init__(self, tag, body, design, rise=None) -> None:
        super().__init__(body, design, tag, rise=rise)
        design = design['pants']
        self.rise = design['rise']['v'] if rise is None else rise
        waist, hips_depth, waist_back = self.eval_rise(self.rise)

        min_ext = body['leg_circ'] - body['hips'] / 2  + 5
        front_hip = (body['hips'] - body['hip_back_width']) / 2
        crotch_extention = min_ext * design['width']['v']  
        front_extention = front_hip / 4
        back_extention = crotch_extention - front_extention

        length, cuff_len = design['length']['v'], design['cuff']['cuff_len']['v']
        if design['cuff']['type']['v']: 
            if length - cuff_len < design['length']['range'][0]:
                cuff_len = length - design['length']['range'][0]
            length -= cuff_len
        length *= body['_leg_length']
        cuff_len *= body['_leg_length']

        self.front = PantPanel(
            f'pant_f_{tag}', body, design,
            length=length, waist=(waist - waist_back) / 2,
            hips=(body['hips'] - body['hip_back_width']) / 2,
            hips_depth=hips_depth,
            dart_position=body['bust_points'] / 2,
            crotch_width=front_extention,
            match_top_int_to=(body['waist'] - body['waist_back_width']) / 2
        ).translate_by([0, body['_waist_level'] - 5, 25])
        self.back = PantPanel(
            f'pant_b_{tag}', body, design,
            length=length, waist=waist_back / 2,
            hips=body['hip_back_width'] / 2,
            hips_depth=hips_depth, hipline_ext=1.1,
            dart_position=body['bum_points'] / 2,
            crotch_width=back_extention,
            match_top_int_to=body['waist_back_width'] / 2,
            double_dart=True
        ).translate_by([0, body['_waist_level'] - 5, -20])

        self.stitching_rules = pyg.Stitches(
            (self.front.interfaces['outside'], self.back.interfaces['outside']),
            (self.front.interfaces['inside'], self.back.interfaces['inside']))

        # Cuff attachment (optional)
        if design['cuff']['type']['v']:
            pant_bottom = pyg.Interface.from_multiple(
                self.front.interfaces['bottom'], self.back.interfaces['bottom'])
            cdesign = deepcopy(design)
            cdesign['cuff']['b_width'] = {'v': pant_bottom.edges.length() / design['cuff']['top_ruffle']['v']}
            cdesign['cuff']['cuff_len']['v'] = cuff_len
            cuff_class = getattr(bands, cdesign['cuff']['type']['v'])
            self.cuff = cuff_class(f'pant_{tag}', cdesign)
            self.cuff.place_by_interface(self.cuff.interfaces['top'], pant_bottom, gap=5, alignment='left')
            self.stitching_rules.append((pant_bottom, self.cuff.interfaces['top']))

        self.interfaces = {
            'crotch_f': self.front.interfaces['crotch'],
            'crotch_b': self.back.interfaces['crotch'],
            'top_f': self.front.interfaces['top'], 
            'top_b': self.back.interfaces['top']}


class Pants(BaseBottoms):
    def __init__(self, body, design, rise=None) -> None:
        super().__init__(body, design)
        self.right = PantsHalf('r', body, design, rise)
        self.left = PantsHalf('l', body, design, rise).mirror()
        self.stitching_rules = pyg.Stitches(
            (self.right.interfaces['crotch_f'], self.left.interfaces['crotch_f']),
            (self.right.interfaces['crotch_b'], self.left.interfaces['crotch_b']))
        self.interfaces = {
            'top_f': pyg.Interface.from_multiple(
                self.right.interfaces['top_f'], self.left.interfaces['top_f']),
            'top_b': pyg.Interface.from_multiple(
                self.right.interfaces['top_b'], self.left.interfaces['top_b']),
            'top': pyg.Interface.from_multiple(
                self.right.interfaces['top_f'].flip_edges(),
                self.left.interfaces['top_f'].reverse(with_edge_dir_reverse=True),
                self.left.interfaces['top_b'].flip_edges(),
                self.right.interfaces['top_b'].reverse(with_edge_dir_reverse=True))}
```

#### B. `tee.py` — Full Contents

```python
"""Panels for a straight upper garment (T-shirt)"""
import numpy as np
import pygarment as pyg
from assets.garment_programs.base_classes import BaseBodicePanel


class TorsoFrontHalfPanel(BaseBodicePanel):
    """Half of a simple non-fitted upper garment (e.g. T-Shirt) -- fits to bust size"""
    def __init__(self, name, body, design) -> None:
        super().__init__(name, body, design)
        design = design['shirt']

        m_width = design['width']['v'] * body['bust']
        b_width = design['flare']['v'] * m_width
        body_width = (body['bust'] - body['back_width']) / 2 
        frac = body_width / body['bust'] 
        self.width = frac * m_width
        b_width = frac * b_width

        sh_tan = np.tan(np.deg2rad(body['_shoulder_incl']))
        shoulder_incl = sh_tan * self.width
        length = design['length']['v'] * body['waist_line']

        fb_diff = (frac - (0.5 - frac)) * body['bust']
        length = length - sh_tan * fb_diff

        self.edges = pyg.EdgeSeqFactory.from_verts(
            [0, 0], [-b_width, 0], [-self.width, length],
            [0, length + shoulder_incl], loop=True)

        self.interfaces = {
            'outside':  pyg.Interface(self, self.edges[1]),   
            'inside': pyg.Interface(self, self.edges[-1]),
            'shoulder': pyg.Interface(self, self.edges[-2]),
            'bottom': pyg.Interface(self, self.edges[0],
                ruffle=self.edges[0].length() / ((body['waist'] - body['waist_back_width']) / 2)),
            'shoulder_corner': pyg.Interface(self, [self.edges[-3], self.edges[-2]]),
            'collar_corner': pyg.Interface(self, [self.edges[-2], self.edges[-1]])}

        self.translate_by([0, body['height'] - body['head_l'] - length - shoulder_incl, 0])

    def get_width(self, level):
        return super().get_width(level) + self.width - self.body['shoulder_w'] / 2


class TorsoBackHalfPanel(BaseBodicePanel):
    """Half of a simple non-fitted upper garment (e.g. T-Shirt) -- fits to bust size"""
    def __init__(self, name, body, design) -> None:
        super().__init__(name, body, design)
        design = design['shirt']
        m_width = design['width']['v'] * body['bust']
        b_width = design['flare']['v'] * m_width
        body_width = body['back_width'] / 2
        frac = body_width / body['bust'] 
        self.width = frac * m_width
        b_width = frac * b_width

        shoulder_incl = (np.tan(np.deg2rad(body['_shoulder_incl']))) * self.width
        length = design['length']['v'] * body['waist_line']

        self.edges = pyg.EdgeSeqFactory.from_verts(
            [0, 0], [-b_width, 0], [-self.width, length],
            [0, length + shoulder_incl], loop=True)

        self.interfaces = {
            'outside':  pyg.Interface(self, self.edges[1]),   
            'inside': pyg.Interface(self, self.edges[-1]),
            'shoulder': pyg.Interface(self, self.edges[-2]),
            'bottom': pyg.Interface(self, self.edges[0],
                ruffle=self.edges[0].length() / (body['waist_back_width'] / 2)),
            'shoulder_corner': pyg.Interface(self, [self.edges[-3], self.edges[-2]]),
            'collar_corner': pyg.Interface(self, [self.edges[-2], self.edges[-1]])}

        self.translate_by([0, body['height'] - body['head_l'] - length - shoulder_incl, 0])

    def get_width(self, level):
        return super().get_width(level) + self.width - self.body['shoulder_w'] / 2
```

#### C. `skirt_paneled.py` — Full Contents

```python
import numpy as np
from scipy.spatial.transform import Rotation as R
import pygarment as pyg
from assets.garment_programs.base_classes import StackableSkirtComponent, BaseBottoms
from assets.garment_programs import shapes


class SkirtPanel(pyg.Panel):
    """One panel of a panel skirt with ruffles on the waist"""
    def __init__(self, name, waist_length=70, length=70, ruffles=1,
                 match_top_int_to=None, bottom_cut=0, flare=0) -> None:
        super().__init__(name)

        base_width = waist_length
        top_width = base_width * ruffles
        low_width = top_width + 2*flare
        x_shift_top = (low_width - top_width) / 2

        self.right = pyg.EdgeSeqFactory.side_with_cut(
            [0, 0], [x_shift_top, length],
            start_cut=bottom_cut / length) if bottom_cut else pyg.EdgeSequence(
            pyg.Edge([0, 0], [x_shift_top, length]))
        self.waist = pyg.Edge(self.right[-1].end, [x_shift_top + top_width, length])
        self.left = pyg.EdgeSeqFactory.side_with_cut(
            self.waist.end, [low_width, 0],
            end_cut=bottom_cut / length) if bottom_cut else pyg.EdgeSequence(
            pyg.Edge(self.waist.end, [low_width, 0]))
        self.bottom = pyg.Edge(self.left[-1].end, self.right[0].start)
        
        self.interfaces = {
            'right': pyg.Interface(self, self.right[-1]),
            'top': pyg.Interface(self, self.waist,
                ruffle=self.waist.length() / match_top_int_to if match_top_int_to else ruffles
            ).reverse(True),
            'left': pyg.Interface(self, self.left[0]),
            'bottom': pyg.Interface(self, self.bottom)}

        self.edges = self.right
        self.edges.append(self.waist)
        self.edges.append(self.left)
        self.edges.append(self.bottom)

        self.top_center_pivot()
        self.center_x()


class FittedSkirtPanel(pyg.Panel):
    """Fitted panel for a pencil skirt"""
    def __init__(self, name, body, design, waist, hips, hips_depth, length,
                 hipline_ext=1, dart_position=None, dart_frac=0.5, double_dart=False,
                 match_top_int_to=None, slit=0, left_slit=0, right_slit=0,
                 side_cut=None, flip_side_cut=False) -> None:
        super().__init__(name)
        # Complex fitted panel with curves, darts, slits, and side cuts


class PencilSkirt(StackableSkirtComponent):
    def __init__(self, body, design, tag='', length=None, rise=None, slit=True, **kwargs) -> None:
        # Creates front/back FittedSkirtPanel with darts, slits, and optional side cuts
        # Stitches side seams, exposes top/bottom interfaces

class Skirt2(StackableSkirtComponent):
    """Simple 2 panel skirt"""
    def __init__(self, body, design, tag='', length=None, rise=None, 
                 slit=True, top_ruffles=True, min_len=5) -> None:
        # Creates front/back SkirtPanel with ruffles

class SkirtManyPanels(BaseBottoms):
    """Round Skirt with many panels"""
    def __init__(self, body, design, tag='', rise=None, min_len=5) -> None:
        # Creates N ThinSkirtPanel copies distributed around OY axis
        # Uses pyg.ops.distribute_Y() for radial duplication
```

### 2.3 Key Classes and Methods

#### Level 1: Edge Primitives (`pygarment/garmentcode/edge.py`)

| Class | Purpose |
|-------|---------|
| **`Edge`** | Straight line segment between two 2D vertices (`start`, `end`). Supports `length()`, `subdivide_len()`, `subdivide_param()`, `reverse()`, `rotate()`, `snap_to()`. |
| **`CircleEdge(Edge)`** | Circular arc defined by `start`, `end`, and relative `control_y` (the third point on the arc). Preserves arc angle during edge resizing. |
| **`CurveEdge(Edge)`** | Quadratic or Cubic Bezier curve. `control_points` stored in relative coordinates. Up to 2 control points (cubic). Supports `_extreme_points()` for Y-extrema. |
| **`EdgeSequence`** | Ordered chain of edges with `isLoop()`, `isChained()`, `close_loop()`, `fractions()`, `reverse()`, `extend()`, `reflect()`, `bbox()`. |

#### Level 2: Panel (`pygarment/garmentcode/panel.py`)

**`Panel(BaseComponent)`** — a single flat piece of fabric:

| Attribute/Method | Purpose |
|---|---|
| `self.edges` | `EdgeSequence` forming the panel border loop |
| `self.translation` | 3D numpy vector for world placement |
| `self.rotation` | scipy `Rotation` object for orientation |
| `self.interfaces` | `dict` of named `Interface` objects (stitchable edges) |
| `self.stitching_rules` | `Stitches` object (internal seams, e.g., darts) |
| `set_pivot(point_2d)` | Set 2D origin for rotation/translation |
| `top_center_pivot()` | Pivot at middle of highest edge |
| `translate_by(vec)` / `translate_to(vec)` | Position the panel in 3D |
| `rotate_by(R)` / `rotate_to(R)` | Orient the panel |
| `mirror(axis)` | Flip to create symmetric counterpart |
| `autonorm()` | Flip edge winding so normal faces outward |
| `add_dart(shape, edge, offset)` | Insert a dart into an edge (calls `pyg.ops.cut_into_edge()`) |
| `point_to_3D(point_2d)` | Transform 2D local coords to 3D world |
| `norm()` | Compute panel surface normal from bbox |
| `assembly()` | Serialize to JSON-compatible `BasicPattern` |

#### Level 3: Component (`pygarment/garmentcode/component.py`)

**`Component(BaseComponent)`** — a composite of Panels and/or other Components:

| Attribute/Method | Purpose |
|---|---|
| `self.subs` | List of sub-components (auto-discovered from attributes) |
| `self.stitching_rules` | `Stitches` connecting sub-component interfaces |
| `self.interfaces` | Dict of named `Interface` objects exposed to parent |
| `translate_by/rotate_by/mirror` | Recursive transforms on all sub-components |
| `place_by_interface(self_int, out_int, gap, alignment)` | Position this component so its interface aligns with another |
| `place_below(comp, gap)` | Place below another component (Y-axis) |
| `assembly()` | Merge all sub-component assemblies + own stitching rules |

#### Level 4: Interface & Stitching (`interface.py`, `connector.py`)

| Class | Purpose |
|---|---|
| **`Interface`** | Named group of edges from a panel that can be stitched. Has `ruffle` coefficients (gather ratio), `projecting_edges()`, `projecting_fractions()`, `from_multiple()` for joining multi-panel seams. |
| **`StitchingRule`** | Connects two Interfaces. Auto-subdivides edges to match fractions. |
| **`Stitches`** | Collection of `StitchingRule` objects. |

#### Edge Factories (`edge_factory.py`)

| Factory | Purpose |
|---|---|
| **`EdgeSeqFactory.from_verts(*verts, loop)`** | Build edge loop from vertex coordinates |
| **`EdgeSeqFactory.dart_shape(width, depth)`** | Create V-shaped dart edges |
| **`EdgeSeqFactory.side_with_cut(start, end, start_cut, end_cut)`** | Edge with internal vertices for partial stitching |
| **`EdgeSeqFactory.halfs_from_svg(path, target_height)`** | Load SVG shapes, split in half for bilateral use |
| **`CurveEdgeFactory.curve_from_tangents(start, end, target_tan0, target_tan1)`** | Quadratic Bezier matching specified tangent directions |
| **`CurveEdgeFactory.curve_3_points(start, end, target)`** | Curve passing through a specific point |
| **`CircleEdgeFactory.from_points_angle/radius/three_points`** | Circular arcs from various specs |

#### Operators (`operators.py`)

| Function | Purpose |
|---|---|
| `cut_corner(target_shape, target_interface)` | Project a shape onto a corner (used for armhole/sleeve/collar attachment) |
| `cut_into_edge(target_shape, base_edge, offset)` | Insert decorative/structural cutouts into an edge (used for darts, slits) |
| `distribute_Y(component, n)` | Radial duplication around Y-axis (used for multi-panel skirts) |
| `curve_match_tangents(curve, tan0, tan1)` | Optimize Bezier control points to match target tangents while preserving length |

### 2.4 Design Parameters → Body Measurements → Panel Vertices

#### Parameter Structure (from `default.yaml`)

```yaml
design:
  meta:                    # Top-level garment selection
    upper: {v: null, range: [FittedShirt, Shirt, null], type: select_null}
    bottom: {v: null, range: [SkirtCircle, Pants, PencilSkirt, ...], type: select_null}
    wb: {v: null, range: [StraightWB, FittedWB, null], type: select_null}

  shirt:                   # Per-garment-type parameters
    width: {v: 1.05, range: [1.0, 1.3], type: float}    # multiplier on body['bust']
    length: {v: 1.2, range: [0.5, 3.5], type: float}     # multiplier on body['waist_line']
    flare: {v: 1.0, range: [0.7, 1.6], type: float}      # hem width multiplier

  pants:
    length: {v: 0.3, range: [0.2, 0.9], type: float}     # fraction of leg length
    width: {v: 1.0, range: [1.0, 1.5], type: float}      # crotch extension multiplier
    rise: {v: 1.0, range: [0.5, 1], type: float}         # fraction of hips_line

  pencil-skirt:
    length: {v: 0.4, range: [0.2, 0.95], type: float}
    flare: {v: 1., range: [0.6, 1.5], type: float}       # bottom width multiplier
    rise: {v: 1, range: [0.5, 1], type: float}
    front_slit: {v: 0, range: [0, 0.9], type: float}     # slit depth fraction
```

Each parameter has: `v` (current value), `range` (min/max), `type` (float/int/bool/select), and `default_prob` (sampling probability).

#### The Mapping Chain

**Step 1:** `MetaGarment.__init__` reads `design['meta']` to select which classes to instantiate:
```python
upper = globals()[design['meta']['upper']['v']]  # e.g., globals()['Shirt']
Lower = globals()[design['meta']['bottom']['v']]  # e.g., globals()['Pants']
```

**Step 2:** Each garment class extracts body measurements + design params to compute edge vertices. Example for T-shirt:
```
design['shirt']['width']['v']  =  1.05  (from YAML)
body['bust']                   = 100.0  (from body YAML)
    =>
m_width = 1.05 * 100.0 = 105.0 cm    (total garment width at bust)
front_frac = (100 - 52) / 2 / 100 = 0.24   (front fraction)
self.width = 0.24 * 105.0 = 25.2 cm   (front half-panel width)
    =>
Edge vertices: [0,0] -> [-25.2, 0] -> [-25.2, length] -> [0, length+shoulder_incl]
```

**Step 3:** Rise parameter controls waist-to-hip interpolation:
```python
# BaseBottoms.eval_rise():
self.adj_hips_depth = rise * body['hips_line']
self.adj_waist = lin_interpolation(body['hips'], body['waist'], rise)
# At rise=1.0: full waist measurement; at rise=0.5: halfway between hips and waist
```

**Step 4:** Flare controls hem width:
```python
# In Pants:
flare = body['leg_circ'] * (design['flare']['v'] - 1) / 4
# flare=1.0 -> straight leg (0 extra); flare=1.2 -> 3.15cm per side
```

**Step 5:** Ruffle/gather ratios in Interfaces control fabric gathering:
```python
# In SkirtPanel:
self.interfaces['top'] = pyg.Interface(self, self.waist,
    ruffle=self.waist.length() / match_top_int_to)  # >1 = gather/gas
```

#### Body Measurements (from `m_smpl_average_A40.yaml`)

```yaml
body:
  height: 178.1          # total height (cm)
  bust: 100.0            # bust circumference
  waist: 80.0            # waist circumference  
  hips: 100.0            # hip circumference
  waist_line: 44.2       # shoulder-to-waist distance
  hips_line: 17.0        # waist-to-hip distance
  shoulder_w: 38.2       # shoulder width
  back_width: 52         # back width
  hip_back_width: 52     # back hip width
  waist_back_width: 38   # back waist width
  arm_length: 80         # arm length
  leg_circ: 63           # leg circumference
  neck_w: 17             # neck width
  crotch_hip_diff: 13.0  # crotch depth below hip
  arm_pose_angle: 40     # arm angle for sleeve rotation
  bust_points: 17        # bust point separation
  bum_points: 19.3       # back dart positions
  # Derived (prefixed with _):
  _shoulder_incl: ...    # shoulder inclination angle
  _hip_inclination: ...  # hip side angle
  _bust_line: ...        # bust level below waist_line
  _armscye_depth: ...    # armhole depth
  _leg_length: ...       # full leg length fraction
  _waist_level: ...      # Y position of waist
  _base_sleeve_balance: ... # sleeve cap balance
```

### 2.5 Creating a New Garment Type

#### New Panel Template

```python
import pygarment as pyg

class MyCustomPanel(pyg.Panel):
    def __init__(self, name, body, design):
        super().__init__(name)
        
        # 1. Extract measurements
        width = design['my_garment']['width']['v'] * body['hips']
        length = design['my_garment']['length']['v'] * body['_leg_length']
        
        # 2. Define edges (the panel border)
        self.edges = pyg.EdgeSeqFactory.from_verts(
            [0, 0],            # bottom-left
            [width, 0],        # bottom-right
            [width, length],   # top-right
            [0, length],       # top-left
            loop=True          # close the loop
        )
        
        # 3. Define named interfaces (stitchable edges)
        self.interfaces = {
            'left':   pyg.Interface(self, self.edges[3]),    # side seam
            'right':  pyg.Interface(self, self.edges[1]),    # side seam
            'top':    pyg.Interface(self, self.edges[2]),    # waistband connection
            'bottom': pyg.Interface(self, self.edges[0]),    # hem
        }
        
        # 4. Default placement
        self.top_center_pivot()
        self.center_x()
```

#### New Full Garment Component Template

```python
class MyCustomSkirt(pyg.Component):
    def __init__(self, body, design):
        super().__init__(self.__class__.__name__)
        
        # 1. Create sub-panels
        self.front = MyCustomPanel('front', body, design)
        self.back = MyCustomPanel('back', body, design).mirror()
        
        # 2. Define stitching rules (seam connections)
        self.stitching_rules = pyg.Stitches(
            (self.front.interfaces['right'], self.back.interfaces['right']),
            (self.front.interfaces['left'],  self.back.interfaces['left']),
        )
        
        # 3. Expose interfaces to parent
        self.interfaces = {
            'top':    pyg.Interface.from_multiple(
                self.front.interfaces['top'], self.back.interfaces['top']),
            'bottom': pyg.Interface.from_multiple(
                self.front.interfaces['bottom'], self.back.interfaces['bottom']),
        }
```

#### Integration into MetaGarment

1. Create the file in `assets/garment_programs/my_garment.py`
2. Add `from assets.garment_programs.my_garment import *` to `meta_garment.py`
3. Add design parameters to `assets/design_params/default.yaml` under the appropriate section
4. Add the class name to the `range` list of the relevant `meta.upper` or `meta.bottom` parameter

#### Key Design Principles

- **Panels are 2D**: All vertices defined in 2D, placed in 3D via `translation` + `rotation`
- **Edges share vertices**: Chained edges share vertex objects; mutating one edge's end vertex affects the next edge's start
- **Interfaces are stitchable**: Named edge groups that can be connected via `StitchingRule`
- **Ruffle = gather ratio**: `ruffle=2` means the fabric is 2x wider than the seam it connects to (gathered in half)
- **Darts are self-stitched**: `Panel.add_dart()` creates a V-cutout and adds a self-stitching rule
- **Mirroring**: `.mirror()` creates the left side from the right by reflecting edges and flipping the X translation
- **Composition**: Higher-level components (like `Shirt`) compose sub-components (`BodiceHalf` + `Sleeve` + `Collar`) and stitch their interfaces together
- **Design params are hierarchical dicts**: Accessed as `design['section']['param']['v']` for values, `design['section']['param']['range']` for bounds

---

## 3. GarmentCodeRC vs GarmentCode — Complete Diff Analysis

### 3.1 Overview

**GarmentCodeRC** ("Richer & Cleaner") is a refined version of GarmentCode by Maria Korosteleva, created by Siyuan Bian et al. at MPI/ETH for the **ChatGarment** project (CVPR 2025). It is used as the sewing pattern backend for a VLM fine-tuned to generate garment JSON configurations from images and text.

**README**: "GarmentCodeRC is a refined version of the original GarmentCode, with added support for openfront garments & tighter pants & high-waist garments."

**Paper (arXiv:2412.17811) Section S1.1**:
> "First, we modify stitching and panel positioning to better support diverse garment types, such as open-front jackets, high-waist skirts, and fitted pant legs. This allows us to model a broader range of real-world garments and aligns more closely with natural garment descriptions."
> "Second, we simplify GarmentCode's JSON configuration to better suit LLM training. The original configuration is redundant, applying the same settings across all garment types. We optimize this by automatically removing irrelevant settings. This adjustment reduces the average language token count from 900 to 350, decreasing ambiguity in LLM training."

### 3.2 Directory Structure

Both repos have **identical directory structures**:
```
pygarment/
  garmentcode/      # Core library
  mayaqltools/      # Maya+Qualoth compatibility
  meshgen/          # Box mesh generation
  pattern/          # Pattern serialization
  __init__.py
  data_config.py

assets/
  garment_programs/ # Garment component definitions
  design_params/    # YAML design configurations
  bodies/           # Body measurement files
  Patterns/         # Output patterns
  Sim_props/        # Simulation properties
  img/              # Images

# Root files
test_garmentcode.py
pattern_sampler.py
pattern_fitter.py
pattern_data_sim.py
gui.py
```

**No new files were added** in `garment_programs/`. `design_params/` adds `default_new.yaml` and `design_used.yaml` as supplementary configs.

### 3.3 Specific Code Changes

#### Change 1: Open-Front Jackets (bodice.py — `Shirt` class)

**Original GarmentCode** (always stitches front panels together):
```python
self.stitching_rules.append((self.right.interfaces['front_in'],
                             self.left.interfaces['front_in']))
```

**GarmentCodeRC** (conditionally skips front stitching):
```python
if ('openfront' not in design['shirt']) or (not design['shirt']['openfront']['v']):
    self.stitching_rules.append((self.right.interfaces['front_in'],
                                self.left.interfaces['front_in']))
# else:
    # assert design['shirt']['openfront']['v']
    # assert design['meta']['wb']['v'] is None
    # assert design['meta']['bottom']['v'] is None
```

#### Change 2: High-Waist Support (bands.py — `StraightWB` class)

**Original**: Always places waistband at waist level:
```python
self.front.translate_by([0, body['_waist_level'], 20])
self.back.translate_by([0, body['_waist_level'], -15])
```

**GarmentCodeRC**: Adds `height` parameter:
```python
if 'height' in design['waistband']:
    self.front.translate_by([0, body['_waist_level'] + design['waistband']['height']['v'], 20])
    self.back.translate_by([0, body['_waist_level'] + design['waistband']['height']['v'], -15]) 
else:
    self.front.translate_by([0, body['_waist_level'], 20])
    self.back.translate_by([0, body['_waist_level'], -15])
```

#### Change 3: Tighter/Fitted Pants (design_params)

| Parameter | Original | GarmentCodeRC |
|-----------|----------|---------------|
| `pants.width.v` | `1.0` | `1.0` |
| `pants.width.range` | `[1.0, 1.5]` | `[0.5, 1.5]` |

Also: `sleeve.length` max increased from `1.15` to `1.2`, `shirt.width` lower bound from `1.0` to `0.8`.

### 3.4 Simplified JSON Structure (for VLM)

The design params YAML format is **structurally identical**:

```yaml
design:
  meta:
    upper: { v: null, range: [FittedShirt, Shirt, null], type: select_null }
    bottom: { v: null, range: [SkirtCircle, ..., Pants, ..., null], type: select_null }
    wb: { v: null, range: [StraightWB, FittedWB, null], type: select_null }
  shirt:
    strapless: { v: false, range: [true, false], type: bool }
    length: { v: 1.2, range: [0.5, 3.5], type: float }
    openfront: { v: false, range: [true, false], type: bool }    # NEW in RC
  pants:
    width: { v: 1.0, range: [0.5, 1.5], type: float }          # WIDER range
  waistband:
    height: { v: 0, range: [-5, 15], type: int }                # NEW in RC
```

The "simplified JSON" in the paper refers to what the VLM generates:
- Original: 900 tokens average (all sections present for all garment types)
- GarmentCodeRC: 350 tokens average (dynamically removes irrelevant sections)
- Float values normalized to [0,1] for stable LLM training

### 3.5 Files UNCHANGED (byte-for-byte identical)

- `base_classes.py`, `pants.py`, `meta_garment.py`, `skirt_levels.py`, `skirt_paneled.py`
- `collars.py`, `sleeves.py`, `tee.py`, `circle_skirt.py`, `godet.py`, `shapes.py`, `stats_utils.py`
- Entire `pygarment/` core, `gui/`, `post_processing_scripts/`, all root scripts

### 3.6 Key Architectural Insight

GarmentCodeRC's approach is notable for its **minimalism**: rather than creating new garment class files for jackets, fitted pants, and high-waist skirts, the authors achieved new garment types by:

1. A **single conditional check** in `bodice.py` (`openfront`) that prevents front stitching
2. A **single height offset** in `bands.py` that moves waistbands vertically
3. **Widening a parameter range** that existing parametric geometry already supports

This reflects the ChatGarment project's goal: minimal code changes that maximize the VLM's ability to represent diverse garments through a small, clean JSON configuration.

---

## 4. African Garment Sewing Pattern Construction

### 4.1 AGBADA (Yoruba, Southwestern Nigeria / Republic of Benin)

**Overview**: Four-piece ensemble: outer robe (awosoke), undervest shirt (buba/awotele), trousers (sokoto), hat (fila). Two varieties: casual **Sapara** (lighter) and ceremonial **Agbada nla/girike** (larger, heavily embroidered).

#### Panel Count and Geometry

**Method A — Traditional Three-Panel Construction (most common):**
The robe has **3 panels**: one rectangular centerpiece flanked by two wide rectangular sleeve panels.

| Panel | Shape | Dimensions (adult male) |
|-------|-------|------------------------|
| Center body panel | **Rectangle** | Width = ~22" (chest/2 + ease), Length = shoulder-to-below-knee (~46-54") |
| Left sleeve panel | **Rectangle** | Width = ~24" (half of neck-to-hand span), Length = same as body panel |
| Right sleeve panel | **Rectangle** | Width = ~24", Length = same as body panel |

Total width = neck-to-hand measurement. For an adult male: typically 44-50 inches.

**Method B — Single-Piece Construction (simpler):**
Entire robe is cut from **one large rectangle** of fabric folded in half. No separate sleeve panels. Fabric folded so fold line runs across shoulders, creating front and back with **no shoulder seam**.

| Panel | Shape | Dimensions |
|-------|-------|------------|
| Single body+sleeve piece | **Large rectangle** (unfolded: width = neck-to-hand, length = 2x body length) | Width: ~48-56", Length: ~90-108" |

#### Neckline Geometry

- **Front neckline**: Quarter-circle arc. Width = neck_circumference / 12 + ~0.5", typically 2.5-3" from center. Depth = 3" standard.
- **Back neckline**: Shallower arc, only 1" from center.
- **Keyhole option**: V-shaped slit from neckline down to chest level (~8"). Horizontal line at chest level meets slant line from neck arc.
- **Embroidery zone**: Concentric rings or geometric patterns radiating from neckline.

#### Construction

1. Fabric folded in half, neckline cut at fold intersection. Front deeper than back.
2. Side seams stitched from bottom hem upward to approximately **elbow level** (5-12" of seam).
3. Upper sides remain **OPEN** — creates the characteristic wide, flowing sleeve.
4. All raw edges hemmed.
5. Embroidery applied to center front and back around neckline.
6. Pocket (apo) on left side.

#### Key Measurements

| Measurement | How Taken |
|-------------|-----------|
| Neck-to-hand | Neck center to fingertips — determines total width |
| Chest/Bust | Around fullest part of chest |
| Neck-to-elbow | Neck center to elbow — determines side seam length |
| Shoulder-to-feet (or below knee) | Garment length |
| Neck circumference | Base of neck — determines neck opening |

#### How It Differs from Western

- **No shoulder seams** (traditional method) — continuous fold over shoulders
- **No armhole curves** — no shaped scye at all
- **No fitted bodice, no darts, no princess seams**
- **No separate sleeve pieces** — "sleeves" are open rectangle above partial side seam
- **Minimal sewing** — only 2 short side seams + neckline finishing
- Essentially a **rectangle with a head hole and two short seams**
- Shaping comes from fabric drape, not pattern engineering

---

### 4.2 DASHIKI (West Africa — Yoruba, Igbo, and pan-African)

**Overview**: Loose-fitting pullover garment. Bold printed fabric (often with pre-printed neckline design), V-shaped or round neckline, wide bell-shaped sleeves.

#### Panel Count and Geometry

**Standard: TWO panels** (front + back), cut from fabric folded in half.

| Panel | Shape | Notes |
|-------|-------|-------|
| Front panel | **A-line / trapezoid** with integrated bell sleeves | Wider at hem, narrowing at shoulders. Chest/2 + 5-8" ease |
| Back panel | **A-line / trapezoid** with integrated bell sleeves | Slightly higher neckline than front |

Fabric panel size: Typically 2 yards (72") x 47" wide.

#### Detailed Panel Geometry

```
         neckline
       /          \
      /  shoulder   \
     /     slope     \
    |                  |  <- underarm point
    |  bell sleeve     |
    |   curves out     |
    |                  |
     \                /
      \   A-line     /    <- body widens toward hem
       \  body      /
        \__________/
```

- **Shoulder slope**: Gentle slope from neckline to sleeve head
- **Armhole/underarm**: Gentle concave curve from shoulder to widest A-line point
- **Sleeve shape**: Bell/cupped — widening from underarm toward sleeve opening
- **Body**: A-line flare from bust/chest to hem
- **Neckline**: V-shaped front slit. Back neckline higher and rounder.

#### Construction

1. Fold fabric in half lengthwise.
2. Cut neckline using pre-printed motif as guide. V-slit on front only.
3. Mark bust/chest: add 2-5" ease. Mark armhole curve.
4. Cut through both layers. Cut armhole curve for bell sleeve.
5. Neckline facing: sickle/crescent-shaped piece (~1.5" wide).
6. Shoulder seams: front to back.
7. Side seams: underarm down to hem.
8. Hem: double-fold bottom and sleeve openings.
9. **No darts, no zippers, no buttons.**

#### Key Measurements

| Measurement | How Taken |
|-------------|-----------|
| Chest/Bust | Around fullest part + 5-8" ease |
| Desired length | Shoulder to hip (shirt) or past hips (tunic) |
| Sleeve length | Shoulder to desired endpoint |
| Neck circumference | For facing/slit sizing |
| Across shoulder | For shoulder seam placement |

#### How It Differs from Western

- **No separate sleeve pieces** — sleeves cut as one with body (kimono-style)
- **No armhole curve in Western sense** — gentle concave curve, not shaped scye
- **No darts, no zippers, no buttonholes, no collar**
- **Front slit** instead of button placket
- **5-8" ease** at chest is standard
- Fabric print dictates design

---

### 4.3 SENATOR WEAR (Nigeria — modern, pan-Nigerian)

**Overview**: Two-piece: long top/shirt (knee-length) + matching trousers. Popularized by former Senate President Anyim Pius Anyim (early 2000s). Made from solid-colored suit fabrics. Most "Western-like" of the four garments.

#### Panel Count and Geometry

**Top: 4 panels** (front, back, left sleeve, right sleeve) + optional facing.

| Panel | Shape | Dimensions |
|-------|-------|------------|
| Front panel | **Rectangle with slight taper** | Width = chest/4 + 2" (overlap) + seam. Length = neckline-to-knee + 2" hem |
| Back panel | **Rectangle with slight taper** | Width = chest/4 + seam. Length = same or +4" longer |
| Left sleeve | **Tapered rectangle** (set-in) | Width = bicep/2 + 1-2" ease. Length = shoulder-to-wrist |
| Right sleeve | **Tapered rectangle** (set-in) | Same as left |

**Trousers: 4 panels** (2 front leg + 2 back leg, standard construction).

#### Detailed Geometry

- **Shoulder**: Proper shoulder slope (~3" drop from neckline to shoulder tip)
- **Armhole**: Traditional curved armhole (depth = chest/4 - 1")
- **Neckline**: Round (width = neck/6, depth = 2.5-3"). Optional center-front slit (6") with facing/placket.
- **Body**: Relatively straight/rectangular, minimal tapering. 4-5" ease at chest.
- **Hem**: Just above the knee.
- **Center front overlap**: ~3" overlap secured with hidden fasteners (not Western button placket).

#### Construction

1. Cut back panel first (for symmetry).
2. Cut front panel with 3" extra width for overlap.
3. Mark shoulder slope: 3" drop from neckline.
4. Cut armhole curve: standard curved scye.
5. Cut neckline: round, with optional center-front opening.
6. Join shoulder seams.
7. Set in sleeves (standard Western set-in technique).
8. Sew side seams from underarm to hem.
9. Hem center front overlap and bottom.
10. Optional: embroidery on chest, piping on neckline.
11. Trousers: standard tapered leg construction.

#### Key Measurements

| Measurement | How Taken |
|-------------|-----------|
| Full top length | Neckline to desired hem (above knee) |
| Shoulder width | Shoulder tip to shoulder tip |
| Chest | Around fullest part + 4-5" ease |
| Sleeve length | Shoulder seam to wrist bone |
| Round bicep | Around thickest part + 1.5-2" ease |
| Neck circumference | Base of neck |
| Trousers: waist, hip, inseam | Standard trouser measurements |

#### How It Differs from Western

- **Much longer top** (knee-length vs hip-length)
- **No visible front closure** — no button placket. Hidden closures or simple overlap.
- **No collar** in traditional version (round neck or mandarin/band collar in modern)
- **No Western-style darts** — minimal shaping, relies on ease
- **Simpler construction** — no lapels, no welt pockets
- Overall silhouette: **long, clean rectangle** rather than fitted hourglass

---

### 4.4 BOUBOU / KAFTAN (Senegal / Pan-West Africa)

**Overview**: The grand boubou (Wolof: mboubou) — the most minimalist garment construction in this set. Flowing, wide-sleeved robe. Three pieces for full formal: robe, matching long-sleeved shirt, drawstring trousers (tubay/shokoto). The robe is the iconic element.

#### Panel Count and Geometry

**The traditional grand boubou uses exactly ONE panel** — a single large rectangle of fabric.

| Panel | Shape | Dimensions |
|-------|-------|------------|
| Single body+sleeve piece | **Rectangle** | Width = 59" (150cm) standard. Length = 117" (300cm) for grand boubou |

When folded in half (crosswise): doubled rectangle 59" wide x 58.5" long.

#### Construction — The Simplest Garment Possible

1. **Fold** the large rectangular fabric in half (crosswise, creating front and back layers).
2. **Cut a neck opening** at the center of the fold line:
   - Women: large, round opening
   - Men: V-shaped opening, sometimes with five-sided pocket at V tip
3. **Sew side seams from bottom upward** to approximately **halfway up**:
   - Sewn portion = body/skirt area
   - Unsewn upper portion = arm/sleeve openings
4. **Hem** all raw edges.
5. **Embroider** around neckline, chest, sometimes hems.
6. **Starch** (formal versions) for angular, sculptural drape.

**One rectangle. One fold. One cut. Two seams.**

#### Variations That Add Panels

- **Gando (sleeve extensions)**: Additional rectangular panels sewn to side seams
- **Gandora (inner tunic)**: Separate inner garment
- **Side gussets**: Triangular or rectangular inserts to add volume

Core construction remains: **one folded rectangle with partial side seams**.

#### Key Measurements

| Measurement | How Taken |
|-------------|-----------|
| Fabric length | 2x desired garment length (since folded) |
| Fabric width | Determines total circumference/volume (standard: 59") |
| Neck placement & shape | Centered at fold; round (women) or V (men) |
| Side seam length | How far up from bottom to sew |
| Body length | Fold to hem |
| Sleeve opening size | Unsewn portion of side seam |

#### How It Differs from Western

- **Simplest possible construction** — fewer seams than any Western garment
- **No shoulder seams, no armhole curves, no separate sleeves**
- **No darts, no zippers, no buttons, no collar, no facing**
- **No fitted elements of any kind**
- **No body shaping** — silhouette entirely through fabric drape and gravity
- **Starching transforms** — starched bazin riche creates angular, sculptural drape
- Total sewing time for basic boubou: as little as **30 minutes**

---

### 4.5 Comparative Summary

| Feature | Agbada | Dashiki | Senator | Boubou/Kaftan |
|---------|--------|---------|---------|---------------|
| **Origin** | Yoruba, Nigeria | Pan-West African | Nigerian (modern) | Senegalese/Wolof |
| **Panel count** | 1-3 (one rectangle or center + 2 sleeves) | 2 (front + back) | 4 (front, back, 2 sleeves) + trousers | **1** (single rectangle) |
| **Primary panel shape** | Rectangles | A-line trapezoid with bell sleeves | Rectangles with armhole curves | **Rectangle** |
| **Shoulder seams** | None (traditional) | Yes | Yes | **None** |
| **Armhole curves** | None | Gentle concave | Standard Western scye | **None** |
| **Separate sleeves** | No | No (cut-together) | Yes (set-in) | **No** |
| **Darts** | No | No | No | **No** |
| **Front closure** | None (pullover) | Front slit | Overlap (hidden) | **None (pullover)** |
| **Side seams** | Partial (5-12" from bottom) | Full length | Full length | **Partial (halfway up)** |
| **Complexity** | Very low | Low | Medium | **Minimal** |
| **Fabric requirement** | 7-8 yards | 1.5-2 yards | 4-5 yards | **9-12 meters (full set)** |
| **Embroidery** | Essential (neckline) | Optional (neckline) | Optional (chest/neck) | **Essential (neckline/chest)** |

---

### 4.6 Key Insights for PyGarment Implementation

#### What makes these garments fundamentally different from Western patterns:

1. **Rectangular dominance**: Three of four garments are primarily built from rectangles. No Western-style curved princess seams, shaped darts, or complex scye geometry. The fundamental PyGarment primitive should be the **rectangle** with optional partial seams.

2. **Fold-over construction**: Agbada and Boubou fold a single rectangle over the shoulders. PyGarment would need a "fold_symmetry" operation that mirrors a single pattern piece across a horizontal fold line, creating a front+back unit with no shoulder seam.

3. **Partial side seams**: Agbada and Boubou sew only partway up the sides. PyGarment needs a "partial_seam" concept where a side seam has a `seam_length_ratio` parameter (e.g., 0.3 = sewn from bottom to 30% of side height, rest open for arm passage).

4. **Cut-together sleeves**: Dashiki and Boubou integrate sleeves into the body panel. PyGarment already has the concept of panels with integrated sub-shapes, but would need a "bell_sleeve" edge type that flares outward from the underarm.

5. **Minimal pattern pieces**: Total pieces range from 1 (Boubou) to 4-5 (Senator). Western garments typically have 10-20 pieces. Each African garment can be defined with very few `Panel()` calls.

6. **Embroidery zones**: A new parameter or annotation type is needed to mark embroidery regions (concentric arcs around neckline, chest panels). These are decorative-only and don't affect geometry, but are culturally essential.

7. **Ease is enormous**: These garments have 5-8+ inches of ease. The body measurements input should have a separate `ease` parameter that can be set much higher than Western defaults.

#### Proposed PyGarment Panel Definitions

**Agbada (3-panel)**:
```
center_panel = Panel(rect, width=chest/2+6, height=body_length)
left_sleeve = Panel(rect, width=half_wingspan, height=body_length)  
right_sleeve = Panel(rect, width=half_wingspan, height=body_length)
# neck_hole = CircleArcCut(center_top, radius=neck/12)
# join: left_sleeve[right_edge] <-> center_panel[left_edge]
# join: right_sleeve[left_edge] <-> center_panel[right_edge]
# partial_seam: left side from bottom to elbow_height
# partial_seam: right side from bottom to elbow_height
```

**Boubou (1-panel)**:
```
body = Panel(rect, width=fabric_width, height=2*body_length)
# fold along top edge
# neck_hole = ArcCut at fold center
# partial_seam: left side, bottom to 50%
# partial_seam: right side, bottom to 50%
```

**Dashiki (2-panel)**:
```
front = Panel(aline_trapezoid_with_bell_sleeves, chest_ease=6)
back = Panel(aline_trapezoid_with_bell_sleeves, chest_ease=6, neck_depth=1.5)
# neck_slit: V-cut on front panel center
# join at shoulders and sides (full seam)
```

**Senator top (4-panel)**:
```
front = Panel(rect_with_shoulder_slope, overlap=3)
back = Panel(rect_with_shoulder_slope)
left_sleeve = Panel(tapered_rect, armhole_curve=standard)
right_sleeve = Panel(tapered_rect, armhole_curve=standard)
# standard set-in sleeve construction
```

---

## 5. Path Forward: Adding African Garments to Our Pipeline

### 5.1 State of Existing Repos

**No existing GitHub repo or paper has addressed African garment types** in GarmentCode or any parametric sewing pattern system. GarmentCodeRC only added open-front jackets, high-waist skirts, and tighter pants — still standard Euro-Asian garment types. Our African garments (Agbada, Dashiki, Senator, Boubou) would be **entirely novel**.

### 5.2 How to Write PyGarment Components

African garments are geometrically **simpler** than Western ones:

| Garment | Panels | Complexity | Estimated Lines | Closest Template |
|---------|--------|------------|-----------------|------------------|
| Boubou | 1 | Minimal | ~40 | New (rectangle + neck arc + partial seams) |
| Agbada | 3 | Very low | ~80 | New (3 rectangles stitched) |
| Dashiki | 2 | Low | ~60 | `tee.py` (A-line + bell sleeve curve) |
| Senator | 4 | Medium | ~100 | `bodice.py` `Shirt` class |

### 5.3 VLM Integration: Two Approaches

#### Option A: NGL-Prompter Style (Training-Free)

Design an NGL schema for African garments:

```json
{
  "garment_type": "agbada | dashiki | senator | boubou | kaftan",
  "length": "hip | knee | mid_calf | floor",
  "sleeve_width": "standard | wide | very_wide",
  "neckline": "round | v_shape | keyhole | mandarin",
  "fit": "regular | loose | very_loose",
  "has_embroidery": true,
  "fabric": "cotton | ankara | lace | brocade | damask"
}
```

Pipeline: **Prompt GPT-4V/LLaVA** → sequential QA with logits masking → deterministic parser maps NGL attributes → GarmentCode parameters for the African garment type.

**No training needed.** Just a parser function that converts e.g. `{garment_type: "boubou", length: "floor", sleeve_width: "very_wide"}` into corresponding pygarment parameters.

#### Option B: ChatGarment Style (Fine-Tuning)

1. Write pygarment components (~40-100 LoC each)
2. Generate synthetic dataset using GarmentCodeData pipeline: randomize params → simulate → render → save image + GarmentCode JSON pairs
3. Fine-tune LLaVA LoRA using ChatGarment's codebase (`github.com/biansy000/ChatGarment`)
4. Deploy LoRA alongside current GarmentGPT

### 5.4 Effort Summary

| Step | What | Effort | Existing Code |
|------|------|--------|---------------|
| 1 | Write Boubou pygarment component | **2 hours** | `assets/garment_programs/` patterns |
| 2 | Write Dashiki pygarment component | **3 hours** | `tee.py` closest template |
| 3 | Write Agbada pygarment component | **4 hours** | 3-panel rectangle stitching |
| 4 | Write Senator pygarment component | **4 hours** | `bodice.py` `Shirt` class |
| 5 | Add design params YAML | **1 hour** | `assets/design_params/default.yaml` |
| 6 | Register in MetaGarment | **5 min** | `meta_garment.py` globals() lookup |
| 7 | Build NGL schema + parser | **1 day** | Custom code (follow NGL-Prompter paper) |
| 8 | Generate synthetic dataset | **2 days** | GarmentCodeData `pattern_sampler.py` |
| 9 | Fine-tune LLaVA LoRA | **2 days GPU** | ChatGarment repo |

**Quickest path to a demo**: Steps 1-7 → prompt GPT-4V with African garment NGL schema → valid GarmentCode JSON → compile to sewing pattern. No GPU needed.

---

## 6. Academic & Computational References

| Work | Year | Type | Relevance |
|------|------|------|-----------|
| **GarmentCode** (Korosteleva, SIGGRAPH Asia) | 2023 | Parametric sewing pattern framework | Core pygarment library. Best base for implementation |
| **GarmentCodeData** (Korosteleva, ECCV) | 2024 | Synthetic dataset (115K garments) | Data generation pipeline reference |
| **ChatGarment** (Bian et al., CVPR) | 2025 | VLM-based pattern generation | Uses GarmentCode as backend. Fine-tuning approach |
| **GarmentCodeRC** (Bian et al.) | 2025 | Extended GarmentCode | Open-front jackets, high-waist, tighter pants |
| **NGL-Prompter** (Badalyan et al., arXiv) | Feb 2026 | Training-free VLM→GarmentCode | NGL intermediate DSL. Code not yet released |
| **MV-Fashion** (Laczko et al., CVPR) | 2026 | Multi-view video dataset (72.5M frames) | Western styles only |
| **GarVerseLOD** (Luo et al.) | 2024 | 3D garment reconstruction dataset | 6K high-quality cloth models |
| **DressCode** | 2024 | Text-to-sewing-pattern via SewingGPT | GPT-based text-driven generation |
| **Design2GarmentCode** (Style3D) | 2025 | Sketch-to-pattern via LMM | LMM-based parametric pattern generation |
| **GarmentParticles** | 2026 | 2D-3D symmetric garment representation | Diffusion-based, text/image/sketch conditioning |
| **Computational Pattern Making from 3D** (Pietroni) | 2022 | 3D mesh → 2D sewing pattern | Could extract patterns from 3D-scanned garments |
| **se-Shweshwe Fashion Generation** (arXiv) | 2022 | Sketch-to-image for Southern African fashion | First African fashion AI dataset. 500 pairs |
| **Inclusion Ethics in AI: African Fashion** (AAAI) | 2023 | Senegalese fashion classification + wax print GAN | 256-image Boubou classification dataset |
| **AFRIFASHION1600** (Oyewusi et al., CVPRW) | 2021 | African fashion classification dataset | 1,600 images, 8 classes |
| **AFRIFASHION40000** (NeurIPS) | 2021 | GAN-generated African fashion | 40K synthetic images |
| **Afro SpecDetect** | 2025 | Multimodal fashion captioning | 100K items with typologies, materials, fabrics |
| **InFashAI v1/v2** | 2021-2022 | African fashion image+captions | ~76K items from Afrikrea marketplace |

### Key Gap

**None of these computational systems specifically handle African garments.** The GarmentCode framework is the most extensible and uses primitives (rectangles, arcs, partial seams) that map well to African garment construction. African garments are **geometrically simpler** than Western garments, making them excellent candidates for parametric pattern generation.

### Related Papers

- NGL-Prompter: https://arxiv.org/abs/2602.20700 (arXiv Feb 2026)
- ChatGarment: https://arxiv.org/abs/2412.17811 (CVPR 2025)
- GarmentCode: https://github.com/maria-korosteleva/GarmentCode (SIGGRAPH Asia 2023)
- GarmentCodeRC: https://github.com/biansy000/GarmentCodeRC
- ChatGarment code: https://github.com/biansy000/ChatGarment
- GarmentCodeData: https://igl.ethz.ch/projects/GarmentCodeData/ (ECCV 2024)
- MV-Fashion: https://hunorlaczko.github.io/MV-Fashion (CVPR 2026)
- GarVerseLOD: https://garverselod.github.io/ (2024)
- AFRIFASHION1600: https://openaccess.thecvf.com/content/CVPR2021W/CVFAD/papers/Oyewusi_AFRIFASHION1600_CVPRW_2021_paper.pdf

---

## 7. Exhaustive Codebase Audit: What We Actually Have vs What Was Claimed

> **Audit date**: 2026-07-14
> **Scope**: Full inventory of `kaggle-garment-backend/notebook.ipynb`, `kaggle-garment-backend/api_server.py`, and all cloned/mounted dependencies during a Kaggle P100 session.

### 7.1 What's ACTUALLY Deployed & Working

These 5 components are real, cloned, and used in the reconstruction pipeline:

| # | Component | Source | What It Does | Status |
|---|-----------|--------|-------------|--------|
| 1 | **GarmentRec** | `worryDes/GarmentRec` (GitHub) | CNN+MLP → 3D garment mesh from single image (upper/lower classification, vertex prediction, SMPL-based template deformation) | ✅ Weights downloaded (1.16GB), used in `/api/v1/reconstruct` |
| 2 | **GarmentGPT** | `ChimerAI-MMLab/Garment-GPT` (HuggingFace) | LLaVA-7B fine-tuned to output GarmentCode JSON sewing pattern from image | ✅ 14GB weights downloaded across 3 safetensor shards, GPU inference, outputs valid GarmentCode JSON |
| 3 | **GarmentCode** | `maria-korosteleva/GarmentCode` (GitHub) | PyGarment parametric sewing pattern library: 2D panels → 3D draped mesh simulation | ✅ Cloned to `/kaggle/working/weights/garmentcode/repo` (219 objects, 26.11 MiB), used by GarmentGPT output post-processing |
| 4 | **SAM2** | `facebookresearch/segment-anything-2` (GitHub) | Image segmentation model (900MB Hiera-large) → garment segmentation mask | ✅ Installed via pip, loaded in api_server, used to segment garment from image |
| 5 | **rembg** | `danielgatis/rembg` (GitHub, u2net ONNX) | Background removal (176MB u2net model auto-downloaded on first run) | ✅ Used in pipeline as first step, pre-warmed at startup |

**Pipeline order**: `input_image → rembg (bg removal) → SAM2 (garment segmentation) → GarmentRec (3D mesh) + GarmentGPT (sewing pattern JSON) → GarmentCode (pattern→3D simulation) → output ZIP`

### 7.2 What Was WRONGLY Claimed to Be in the Pipeline

The following repos were mentioned in research discussions as if they were part of our codebase. **They are not.** They exist only as external academic references:

| Repo | Status in Our Codebase | Details |
|------|----------------------|---------|
| **ChatGarment** (`biansy000/ChatGarment`) | ❌ Not imported, cloned, or used | Only reference in `african_garment_research.md` §6 as a paper citation. Neither the repo nor its LoRA weights exist in our codebase. Would need full integration. |
| **Design2GarmentCode** (`Style3D/design2garmentcode-impl`) | ❌ Not in codebase at all | Not even mentioned in research doc. Sketch→GarmentCode pipeline from CVPR 2025. Would need to be cloned, installed, and adapted for African garments. |
| **NGL-Prompter** (Badalyan et al., arXiv Feb 2026) | ❌ Not deployed | Described in research doc §5.3 as an approach. Code was "not yet released" at time of writing. Would need to be implemented from paper description. |
| **PatternGSL** (SIGGRAPH 2026) | ❌ Not in codebase | Not mentioned anywhere except this audit. |
| **ReWeaver** (CVPR 2026) | ❌ Not in codebase | Not mentioned anywhere except this audit. |
| **SewingLDM** (ICCV 2025) | ❌ Not in codebase | Not mentioned anywhere except this audit. |
| **GarmentParticles** (CVPR 2026) | ❌ Not in codebase | Not mentioned anywhere except this audit. |
| **GarmageNet** (SIGGRAPH Asia 2025) | ❌ Not in codebase | Not mentioned anywhere except this audit. |
| **SewFormer** (`sail-sg/sewformer`) | ❌ Not in codebase | Not mentioned anywhere except this audit. |

### 7.3 African Datasets: What We Have vs What Was Mentioned

| Dataset | In Our Codebase? | Actual Use |
|---------|-----------------|------------|
| **AFRIFASHION1600** (1.6K images, 8 classes) | ❌ Not downloaded | Only mentioned in research doc §1 and §6 as a reference. Could serve as few-shot prompt examples or VLM eval benchmark. |
| **InFashAI v1/v2** (76K captioned images) | ❌ Not downloaded | Only mentioned in research doc. Attribute vocabulary source for NGL schema design. |
| **AfroSpecDetect** (100K multimodal captions) | ❌ Not downloaded | Only mentioned in research doc. Fabric/material/color taxonomy reference. |
| **se-Shweshwe** (500 sketch→image pairs) | ❌ Not downloaded | Only mentioned in research doc. Could be used for fine-tuning sketch-to-image models, but not currently in pipeline. |
| **African Attire Detector** (12K classification) | ❌ Not downloaded | Only mentioned in research doc. Could serve as zero-shot VLM evaluation set. |

**Current dataset reality**: Zero African garment datasets are downloaded, mounted, or used anywhere in our pipeline. The only data our pipeline touches is whatever image is uploaded by the user at inference time.

### 7.4 The Actual Reality

Our deployed pipeline is exactly:

```
user_image → rembg → SAM2 → [GarmentRec (3D mesh) + GarmentGPT (sewing pattern)]
```

**That is it.** We have:
- ✅ Zero African garment data
- ✅ Zero sketch-to-pattern models
- ✅ Zero VLM-based attribute extraction
- ✅ Zero African garment pygarment templates
- ✅ Zero fabric/stiffness inference
- ✅ Zero African garment evaluation capability

The `african_garment_research.md` is a **research compendium** — it documents what exists in the academic world, not what we've built. Everything in sections 1-6 is aspirational/reference material, not deployed code.

### 7.5 What IS Buildable From Code We Actually Have

The only path forward that builds on actual code in our repository:

| Step | Builds On | What It Produces | Effort |
|------|-----------|-----------------|--------|
| A | GarmentCode's `assets/garment_programs/` | Boubou pygarment component (~40 LoC) | 2 hours |
| B | GarmentCode's `assets/garment_programs/` | Dashiki pygarment component (~60 LoC) | 3 hours |
| C | GarmentCode's `assets/garment_programs/` | Agbada pygarment component (~80 LoC) | 4 hours |
| D | GarmentCode `bodice.py` `Shirt` class | Senator pygarment component (~100 LoC) | 4 hours |
| E | GarmentCode `default.yaml` | Design params YAML entries | 1 hour |
| F | GarmentCode `meta_garment.py` | MetaGarment registration | 5 minutes |
| G | GarmentGPT (as-is, no fine-tuning) | Test on African garment images | 1 hour |
| H | Custom Python code | NGL schema + VLM parser | 1 day |
| I | GarmentCodeData `pattern_sampler.py` | Synthetic African garment dataset | 2 days |
| J | ChatGarment repo (external) | Fine-tuned LLaVA LoRA for African garments | 2 days GPU |

**Everything else** (Design2GarmentCode, PatternGSL, ChatGarment, NGL-Prompter, ReWeaver, SewingLDM, GarmentParticles, GarmageNet, SewFormer) is speculative — those repos exist in the academic world but would need full integration from scratch.

---

## 8. Pipeline Reality: End-to-End Dissection

### 8.1 Complete Request Flow

```
User uploads image
        │
        ▼
EC2 Proxy (korra.work:8001)
  - Rate limit check (10 req/min per IP)
  - Cache lookup by SHA256 hash
  - Forwards to Kaggle tunnel
        │
        ▼
Kaggle P100 GPU (via Cloudflare Tunnel)
  - api_server.py (FastAPI on :8000)
        │
        ▼
Step 1: rembg (u2net ONNX)
  - Removes background
  - CPU inference (onnxruntime)
  - Falls back to PIL threshold if rembg fails
        │
        ▼
Step 2: SAM2 (Hiera-large)
  - Segments garment from image
  - GPU inference
  - Returns binary mask
        │
        ▼
Step 3: GarmentRec
  - CNN encoder → MLP regressor
  - Classifies upper/lower garment type (4 upper classes + 2 bottom classes)
  - Predicts 3D mesh vertices via SMPL template deformation
  - Outputs mesh_upper.obj + mesh_bottom.obj
        │
        ▼
Step 4: GarmentGPT (LLaVA-7B)
  - Fine-tuned on GarmentCode dataset
  - Outputs GarmentCode JSON sewing pattern
  - Contains: meta (upper/bottom/wb selection), design params, panel specifications
  - Outputs sewing_pattern.json
        │
        ▼
Step 5: GarmentCode (PyGarment)
  - Reads GarmentGPT JSON
  - Generates 2D panels
  - Simulates 3D draped mesh
  - Outputs final mesh + pattern
        │
        ▼
ZIP output: mesh_upper.obj, mesh_bottom.obj, sewing_pattern.json, metadata.json
```

### 8.2 Files in the Deployment

| File | Location | Size | Purpose |
|------|----------|------|---------|
| `notebook.ipynb` | `kaggle-garment-backend/` | ~90KB | Master Kaggle notebook (11 cells, nbformat 4.5) |
| `api_server.py` | `kaggle-garment-backend/` | ~15KB | FastAPI inference server (canonical version in Cell 8 of notebook) |
| `server.py` | `garment-proxy/` | ~8KB | EC2 proxy (rate limiting, caching, tunnel registration) |
| `kernel-metadata.json` | `kaggle-garment-backend/` | <1KB | Kaggle kernel metadata for API push |

### 8.3 Known Limitations

1. **No African garment support**: Pipeline generates Western garment meshes + patterns regardless of input garment style. Senator wear may partially work since it resembles Western shirt + trousers.

2. **No fabric/stiffness inference**: Fabric properties are not extracted from the image. The ATTIRE_REGISTRY's `mult`/`off` factors (used in the body measurement pipeline) are NOT used by the garment reconstruction pipeline.

3. **No texture/color preservation**: Output meshes have white UV textures. Fabric patterns, colors, and embroidery are lost.

4. **No sketch input**: The pipeline requires a real photo. Sketch input would require Design2GarmentCode integration (external, not in codebase).

5. **No VLM attribute extraction**: Garment type, fit, length, sleeve width, etc. are not extracted. GarmentGPT makes these decisions internally based on its training data distribution (Western garments).

### 8.4 What Would Need to Change for African Garments

| Component | Change Required | Why |
|-----------|----------------|------|
| GarmentRec | Retrain on African garment renders | Current model doesn't know African garment silhouettes |
| GarmentGPT | Fine-tune LoRA on African GarmentCode data | Current model outputs Western JSON |
| GarmentCode | Add African pygarment templates (Steps A-F) | No Boubou/Agbada/Dashiki/Senator components exist |
| ATTIRE_REGISTRY | Not used in this pipeline | Mult/off factors only used in body measurement pipeline |
| Frontend | Add fabric dropdown, garment type selector | VLM can't reliably infer these from images |

---

## 9. VLM Integration for African Garments: Complete Plan

### 9.1 Why VLM + NGL Instead of Retraining GarmentGPT

Retraining GarmentGPT on African garments requires:
1. Writing pygarment templates (Steps A-F) — doable, 13 hours
2. Generating synthetic dataset via GarmentCodeData pipeline — 2 days
3. Fine-tuning LLaVA LoRA — 2 days GPU ($20-40 on RunPod)
4. Unknown generalization quality — might overfit to synthetic renders

**Total: ~5 days, ~$40 GPU, uncertain quality.**

The NGL-Prompter-style training-free approach:
1. Design NGL schema for African garments — 1 day
2. Prompt GPT-4V/LLaVA with few-shot examples — setup once
3. Parse NGL JSON → GarmentCode parameter mapping — 1 day
4. No training, no GPU, no synthetic data

**Total: ~2 days, $0 GPU, immediate iteration.**

### 9.2 NGL Schema for African Garments

The full NGL schema covers garment type, silhouette, fit, construction details, and fabric:

```json
{
  "garment_type": "boubou | agbada | dashiki | senator | kaftan | danshiki | agbada_nla | sapara",
  "gender": "male | female | unisex",
  
  "silhouette": {
    "length": "hip | knee | mid_calf | ankle | floor",
    "fit": "fitted | regular | loose | very_loose",
    "sleeve_type": "set_in | raglan | kimono | bell | wing | none",
    "sleeve_length": "short | elbow | 3_quarter | long | floor",
    "sleeve_width": "standard | wide | very_wide",
    "neckline": "round | v_shape | scoop | keyhole | mandarin | square | off_shoulder",
    "hem_shape": "straight | curved | asymmetrical | side_slits | front_slit"
  },
  
  "construction": {
    "panel_count": 1,
    "has_shoulder_seams": false,
    "has_side_seams": true,
    "side_seam_type": "full | partial_bottom | partial_top",
    "side_seam_ratio": 0.5,
    "has_darts": false,
    "has_zipper": false,
    "has_buttons": false,
    "front_closure": "none | overlap | slit | buttons | zipper",
    "has_pocket": false,
    "pocket_type": "patch | slit | none",
    "embroidered": true,
    "embroidery_zone": "neckline | chest_panel | full_front | cuffs | hem"
  },
  
  "fabric": {
    "type": "cotton | ankara | lace | brocade | damask | bazin | linen | silk | kente | mudcloth | adire | aso_oke",
    "pattern": "solid | geometric | floral | wax_print | tie_dye | striped | plaid | embroidered",
    "stiffness": "soft | medium | stiff | very_stiff",
    "weight": "light | medium | heavy"
  },
  
  "color": {
    "dominant": ["gold", "indigo", "emerald"],
    "accent": ["white", "black"],
    "embroidery_thread": "gold | silver | matching | contrasting"
  }
}
```

### 9.3 VLM Prompt Template

For production, the VLM is prompted with:

```
You are an African garment analyst. Given a photo of a person wearing traditional African attire,
extract the garment attributes in JSON format.

CLASSIFICATION CONTEXT:
This person appears to be wearing [boubou | agbada | dashiki | senator | kaftan | unknown].
The garment is [male | female | unisex] wear.

GARMENT TYPE REFERENCE:
- Boubou: Single rectangular panel folded over shoulders. Wide, flowing. No shoulder seams. Partial side seams. Senegalese/Wolof origin.
- Agbada: Three rectangular panels (center + 2 wide sleeves). Wide, flowing robe over vest + trousers. Yoruba origin. Often heavily embroidered.
- Dashiki: Two-panel A-line tunic with bell sleeves. Pullover with V-neck slit. West African origin.
- Senator: Four-panel long top (knee-length) with set-in sleeves + trousers. Modern Nigerian origin. Solid fabrics.
- Kaftan: Similar to boubou but more tailored. North African origin.

Answer with ONLY valid JSON:
{
  "garment_type": "...",
  "gender": "...",
  "silhouette": {
    "length": "hip | knee | mid_calf | ankle | floor",
    "fit": "fitted | regular | loose | very_loose",
    "sleeve_type": "set_in | raglan | kimono | bell | wing | none",
    "sleeve_length": "short | elbow | 3_quarter | long | floor",
    "sleeve_width": "standard | wide | very_wide",
    "neckline": "round | v_shape | scoop | keyhole | mandarin | square",
    "hem_shape": "straight | curved | asymmetrical | side_slits | front_slit"
  },
  "construction": {
    "panel_count": <integer>,
    "has_shoulder_seams": <bool>,
    "has_side_seams": <bool>,
    "side_seam_type": "full | partial_bottom | partial_top",
    "has_darts": <bool>,
    "has_zipper": <bool>,
    "has_buttons": <bool>,
    "front_closure": "none | overlap | slit | buttons | zipper",
    "embroidered": <bool>,
    "embroidery_zone": "neckline | chest_panel | full_front | cuffs | hem | none"
  },
  "fabric": {
    "type": "cotton | ankara | lace | brocade | damask | bazin | linen | silk | kente | mudcloth | adire | aso_oke | unknown",
    "pattern": "solid | geometric | floral | wax_print | tie_dye | striped | plaid | embroidered",
    "stiffness": "soft | medium | stiff | very_stiff",
    "weight": "light | medium | heavy"
  }
}

IMPORTANT: Use ONLY the exact values listed. If unsure, use the most conservative option.
If you cannot determine the garment type at all, set garment_type to "unknown".
```

### 9.4 NGL → ATTIRE_REGISTRY Mapping

After VLM extraction, the parsed JSON is matched against the existing `ATTIRE_REGISTRY` (from `dashboard.html:2274`) to find the best entry. The `mult`/`off` factors from the matched entry are used for measurement calculations (not for pattern generation):

```python
def match_attire_registry(vlm_output, attire_registry):
    """
    Match VLM output to closest ATTIRE_REGISTRY entry.
    Uses garment_type as primary key, then similarity on fit/sleeve/length.
    """
    garment_type = vlm_output.get("garment_type")
    
    # Direct match by ID
    if garment_type in attire_registry:
        return attire_registry[garment_type]
    
    # Fuzzy match: try normalized name
    candidates = []
    for entry_id, entry in attire_registry.items():
        score = 0
        if garment_type in entry_id or entry_id in garment_type:
            score += 3
        if vlm_output.get("gender", "") in entry.get("gender", ""):
            score += 1
        candidates.append((score, entry_id, entry))
    
    candidates.sort(reverse=True)
    return candidates[0][2] if candidates else None


def project_to_garmentcode(vlm_output):
    """
    Convert VLM NGL output → GarmentCode parameters.
    Used to override GarmentGPT's default output for African garments.
    """
    gc_params = {
        "meta": {"upper": None, "bottom": None, "wb": None},
        "shirt": {"width": 1.2, "length": 1.0, "flare": 1.0},
        "pants": {"length": 0.3, "width": 1.0, "rise": 1.0},
    }
    
    garment_type = vlm_output.get("garment_type", "senator")
    silhouette = vlm_output.get("silhouette", {})
    
    # Map fit → width multiplier
    fit_to_width = {
        "fitted": 1.0, "regular": 1.1, "loose": 1.2, "very_loose": 1.35
    }
    gc_params["shirt"]["width"] = fit_to_width.get(silhouette.get("fit"), 1.2)
    
    # Map length → garment length parameter
    length_to_mult = {
        "hip": 0.6, "knee": 1.0, "mid_calf": 1.4, "ankle": 1.8, "floor": 2.2
    }
    gc_params["shirt"]["length"] = length_to_mult.get(silhouette.get("length"), 1.0)
    
    return gc_params
```

### 9.5 VLM Accuracy Benchmarks (Estimated)

| Task | Western Garments | African Garments | Notes |
|------|-----------------|------------------|-------|
| Garment type (5-class) | >90% | ~60-75% | Boubou vs Kaftan confusion; Senator best (most Western-like) |
| Gender | >95% | >90% | Hair, face, body shape cues still work |
| Fit (4-class) | ~80% | ~60% | "very_loose" vs "loose" ambiguous for flowing robes |
| Sleeve type | ~85% | ~50% | Bell vs wing vs kimono on Dashiki confuses VLMs |
| Fabric type | ~70% | ~65% | Ankara/wax print visually distinctive; bazin less so |
| Stiffness | ~55% | ~50% | Single 2D image doesn't convey drape well |
| Panel count | N/A (inferred) | ~40% | VLMs don't understand garment construction |

**Mitigations**:
- Use ATTIRE_REGISTRY `mult`/`off` factors instead of VLM ease guesses
- Let user override VLM output via UI dropdown (fabric, garment type)
- Fallback to "senator + medium" when VLM confidence <0.7

---

## 10. Fabric & Stiffness: Practical Implementation

### 10.1 The Problem

VLMs cannot reliably infer fabric stiffness from a single 2D image (~50-60% accuracy). Fabric drape requires understanding the 3D fall of the material, which is ambiguous from one viewpoint. Stiffer fabrics (bazin riche, brocade) create angular, sculptural shapes; softer fabrics (cotton, silk) flow and drape.

### 10.2 Our Solution: Use ATTIRE_REGISTRY + UI Override

Instead of relying on VLM inference, we use a two-layer approach:

**Layer 1: ATTIRE_REGISTRY ease factors as stiffness proxy**
Each attire entry already has `mult` (garment volume multiplier) and `off` (base offset). These encode the garment's ease/volume:

| Garment | mult | off | Implied Stiffness |
|---------|------|-----|-------------------|
| Boubou | 1.35 | 18 | Very stiff (starched bazin) |
| Agbada | 1.30 | 15 | Stiff (brocade/damask) |
| Dashiki | 1.15 | 8 | Medium (cotton/ankara) |
| Senator | 1.08 | 5 | Medium (suit fabric) |
| T-shirt | 1.00 | 2 | Soft (cotton knit) |

Stiffer fabrics → higher `mult`/`off` because they hold shape and add volume. Softer fabrics → lower values because they drape closer to the body.

**Layer 2: User fabric selection dropdown**
In the UI, the user selects from:

```
[Fabric Type]         → [Stiffness]  → [mult/off adjustment]
- Cotton / Ankara       Soft           -0.02 / -2
- Lace                  Soft           -0.01 / -1
- Silk                  Soft-Medium    +0.00 / +0
- Linen                 Medium         +0.01 / +1
- Brocade               Stiff          +0.03 / +3
- Damask                Stiff          +0.04 / +4
- Bazin Riche           Very Stiff     +0.06 / +6
- Kente                 Stiff          +0.03 / +3
- Mudcloth              Medium-Stiff   +0.02 / +2
- Adire                 Medium         +0.01 / +1
- Aso Oke               Very Stiff     +0.05 / +5
```

The VLM can suggest fabric from the photo (it's actually decent at recognizing ankara patterns visually), but the user confirms and adjusts.

### 10.3 Mapping to GarmentCode Simulation

In GarmentCode's simulation properties (`Sim_props/`), fabric stiffness maps to:

| Property | Soft | Medium | Stiff | Very Stiff |
|----------|------|--------|-------|------------|
| `bending_stiffness` | 0.3 | 0.6 | 0.9 | 1.2 |
| `stretch_stiffness` | 0.5 | 0.7 | 0.9 | 1.1 |
| `shear_stiffness` | 0.2 | 0.5 | 0.8 | 1.0 |
| `damping` | 0.1 | 0.2 | 0.4 | 0.6 |
| `density` (g/m²) | 150 | 250 | 400 | 600 |

This allows the simulated 3D garment to drape differently based on fabric selection, matching how a starched bazin riche boubou would look vs a flowing cotton kaftan.

### 10.4 Implementation Plan: Fabric System

| Step | What | File | Effort |
|------|------|------|--------|
| 1 | Add fabric stiffness → `mult`/`off` mapping table | Frontend JS | 2 hours |
| 2 | Add fabric dropdown to garment reconstruction UI | `measurement-screen.js` | 3 hours |
| 3 | Pass fabric parameter to api_server | Frontend + API | 1 hour |
| 4 | Map fabric stiffness to GarmentCode sim params | `api_server.py` | 2 hours |
| 5 | Fabric suggestion from VLM (optional) | VLM prompt | 1 hour |

**Total: ~9 hours**

---

## 11. Sketch-to-Image Pipeline: The Tailor Use Case

### 11.1 The Requirement

Tailors who have hand-drawn sketches of garments (not final photos) need a path to a 3D reconstruction and sewing pattern. The GarmentGPT pipeline requires a real photo — it cannot process line art.

### 11.2 Candidate Solutions

| Solution | Type | Deployable? | Effort | Quality |
|----------|------|-------------|--------|---------|
| **Design2GarmentCode** (Style3D, CVPR 2025) | Sketch→GarmentCode JSON | Would need full integration | ~2 weeks | High |
| **ControlNet + GarmentGPT** | Sketch→photorealistic→GarmentGPT | Faster integration, two-stage | ~1 week | Medium-High |
| **GarmentParticles** (CVPR 2026) | Sketch→sewing pattern | Would need full integration | ~3 weeks | High |
| **Stable Diffusion + IP-Adapter** | Sketch→realistic image → our pipeline | Least code change | ~3 days | Medium |

### 11.3 Recommended Path: ControlNet + Pipeline

The quickest path to a working sketch-to-pipeline demo uses existing infrastructure already available on Kaggle:

```
Step 1: User uploads sketch
    │
    ▼
Step 2: ControlNet (Canny/Lineart) → photorealistic garment image
    - Uses Stable Diffusion + ControlNet (already available on Kaggle)
    - Line art → realistic render of the sketched garment
    - Output: realistic PNG
    │
    ▼
Step 3: Our existing pipeline (rembg → SAM2 → GarmentRec → GarmentGPT)
    - Takes the generated realistic image
    - Produces 3D mesh + sewing pattern
```

**Effort**: ~3 days to wire ControlNet into the notebook.

**Why not Design2GarmentCode directly?**
- It would need to be integrated from scratch (not in our codebase)
- It requires its own fine-tuning for African garments
- It's a full pipeline replacement, not an add-on
- ControlNet approach requires minimal changes to our working pipeline

### 11.4 Extension: African Garment Sketch Dataset

The `se-Shweshwe` dataset (500 sketch→image pairs) can be used to:
1. Fine-tune ControlNet for African garment sketch→photo generation
2. Create an evaluation set for the sketch→pipeline quality
3. Bootstrap a larger synthetic dataset by pairing sketches with AI-generated images

### 11.5 Implementation Steps (ControlNet Sketch Path)

| Step | What | Effort |
|------|------|--------|
| 1 | Install diffusers + ControlNet in Kaggle notebook | 1 hour |
| 2 | Add sketch preprocessing (Canny edge / lineart extraction) | 1 hour |
| 3 | Wire ControlNet inference into API | 3 hours |
| 4 | Add UI file upload for sketches | 2 hours |
| 5 | Test with hand-drawn sketches | 1 hour |

**Total: ~8 hours**

---

## 12. Repo Audit: What Each External Repo Actually Offers

### 12.1 Design2GarmentCode (Style3D, CVPR 2025)

| Attribute | Detail |
|-----------|--------|
| **URL** | `github.com/Style3D/design2garmentcode-impl` |
| **Status** | ❌ Not in our codebase |
| **What it does** | Two-agent system: LLM "program synthesizer" finetuned on GarmentCode + VLM "design interpreter" extracts attributes from sketches/photos/text. Outputs GarmentCode JSON. Includes GUI for uploading sketches → printable sewing patterns. |
| **African garment support** | ❌ None (trained on GarmentCodeData's Western templates) |
| **Would need for integration** | Clone repo, install dependencies, fine-tune program synthesizer on African GarmentCode templates, adapt VLM for African garment attributes |
| **Integration effort** | ~2 weeks |
| **Best for** | Sketch→pattern pipeline (tailor use case) |

### 12.2 ChatGarment (Bian et al., CVPR 2025)

| Attribute | Detail |
|-----------|--------|
| **URL** | `github.com/biansy000/ChatGarment` |
| **Status** | ❌ Not in our codebase. Only cited in research doc §6. |
| **What it does** | Fine-tunes LLaVA-7B (LoRA) to output GarmentCodeRC JSON directly. Uses GarmentCodeRC as its backend. Generates sewing patterns from images + text descriptions. |
| **African garment support** | ❌ None (trained on GarmentCodeData Western samples + GarmentCodeRC templates) |
| **Would need for integration** | Clone repo, write African pygarment templates for GarmentCodeRC, generate synthetic dataset, fine-tune LoRA |
| **Integration effort** | ~1 week + 2 days GPU |
| **Best for** | Replacing GarmentGPT with African-garment-aware VLM |

### 12.3 NGL-Prompter (Badalyan et al., arXiv Feb 2026)

| Attribute | Detail |
|-----------|--------|
| **URL** | Not yet released (paper: `arxiv.org/abs/2602.20700`) |
| **Status** | ❌ Not in our codebase. Approach described in §5.3. |
| **What it does** | Training-free VLM→GarmentCode via intermediate NGL (Natural Garment Language) DSL. Uses GPT-level VLMs with sequential QA and logits masking. No fine-tuning needed. Recovered multi-layer outfits. |
| **African garment support** | ❌ None (paper evaluates on Western garments only) |
| **Would need for integration** | Implement NGL schema from paper description, write VLM prompt + logits masking logic, add African garment types to NGL vocabulary |
| **Integration effort** | ~1 week (no clone needed — implement from paper) |
| **Best for** | Zero-training path to African garment attribute extraction |

### 12.4 GarmentParticles (CVPR 2026)

| Attribute | Detail |
|-----------|--------|
| **URL** | `github.com/garment-particles/GarmentParticles` |
| **Status** | ❌ Not in our codebase |
| **What it does** | Symmetric 2D-3D garment representation. Diffusion-based generation from text/image/sketch. Supports sketch-conditioned generation. Two-stage: particle cloud → sewing pattern reconstruction. |
| **African garment support** | ❌ None |
| **Integration effort** | ~3 weeks |
| **Best for** | Long-term: most modern architecture, but highest integration cost |

### 12.5 Other Repos (Not in Codebase)

| Repo | Venue | Task | Effort to Integrate | Priority |
|------|-------|------|---------------------|----------|
| **PatternGSL** | SIGGRAPH 2026 | Garment Sewing pattern Language | ~2 weeks | Low |
| **ReWeaver** | CVPR 2026 | Pattern re-assembly from 3D | ~2 weeks | Low |
| **SewingLDM** | ICCV 2025 | Latent diffusion for sewing patterns | ~2 weeks | Low |
| **GarmageNet** | SIGGRAPH Asia 2025 | 3D garment generation from text | ~2 weeks | Low |
| **SewFormer** | ICCV 2023 | Transformer-based pattern generation | ~1 week | Low (dated) |

None of these support African garment types. All would need the same African pygarment template extension before they could generate African patterns.

---

## 13. Phased Implementation Plan

### Phase 0: Foundation (Week 1)

| Day | Tasks | Deliverable |
|-----|-------|-------------|
| Day 1 | Write Boubou pygarment component (~40 LoC) + register in MetaGarment + add YAML params | `garment_programs/boubou.py`, verified with `test_garmentcode.py` |
| Day 2 | Write Dashiki pygarment component (~60 LoC) + register | `garment_programs/dashiki.py`, tested |
| Day 3 | Write Agbada pygarment component (~80 LoC) + register | `garment_programs/agbada.py`, tested |
| Day 4 | Write Senator pygarment component (~100 LoC) + register | `garment_programs/senator.py`, tested |
| Day 5 | Test GarmentGPT zero-shot on African garment images | Accuracy report: which garments work out-of-the-box |

**Phase 0 code exists at**: `kaggle-garment-backend/notebook.ipynb` (GarmentCode cloned to `/kaggle/working/weights/garmentcode/repo` during kernel startup)

### Phase 1: VLM Integration (Week 2)

| Day | Tasks | Deliverable |
|-----|-------|-------------|
| Day 1-2 | Design NGL schema for African garments + write VLM prompt template | `ngl_schema.py`, `vlm_prompt.py` |
| Day 3-4 | NGL → GarmentCode parameter mapping + ATTIRE_REGISTRY matcher | `ngl_to_garmentcode.py` |
| Day 5 | Evaluate VLM accuracy on African Attire Detector (12K) benchmark | Accuracy report: per-attribute, per-garment-class |

### Phase 2: UI & Fabric System (Week 3)

| Day | Tasks | Deliverable |
|-----|-------|-------------|
| Day 1 | Fabric stiffness → `mult`/`off` mapping table | Frontend JS constants |
| Day 2 | Fabric dropdown + garment type override in reconstruction UI | UI update in `measurement-screen.js` |
| Day 3 | Wire fabric parameter through API → GarmentCode sim properties | End-to-end fabric-aware simulation |
| Day 4 | Sketch upload path: ControlNet integration | Working sketch→pipeline demo |
| Day 5 | Integration testing + edge case handling | Production-ready pipeline |

### Phase 3: Evaluation & Polish (Week 4)

| Day | Tasks | Deliverable |
|-----|-------|-------------|
| Day 1-2 | Gather 50 African garment photos across all 4 types | Evaluation dataset |
| Day 3 | Run full pipeline on evaluation set, collect metrics | Accuracy report: mesh quality, pattern validity |
| Day 4 | Iterate on pygarment templates based on failure modes | Updated components |
| Day 5 | Deploy to production EC2 + publish UI update | Feature live |

### Total Effort: ~4 weeks for full African garment support

### What's Buildable TODAY (from codebase)

If you want to test **right now** with code we already have:

```bash
# 1. Test GarmentGPT on an African garment image (no code changes needed)
curl -X POST https://korra.work/api/v2/garment/reconstruct \
  -F "file=@senator-wear.jpeg" \
  --max-time 300 -o out.zip

# The output will contain Western-style patterns for whatever garment it sees.
# Senator wear may produce reasonable results since it's closest to Western shirt + pants.
# Boubou/Dashiki/Agbada will likely fail or produce incorrect Western garments.

# 2. Extend GarmentCode with African templates (code changes needed)
# Edit: /kaggle/working/weights/garmentcode/repo/assets/garment_programs/
# Add: boubou.py, dashiki.py, agbada.py, senatory.py
# Register in: meta_garment.py
# Add params to: default.yaml
```

---

## 14. Key Architectural Insights

### 14.1 Why African Garments Are Easier (Geometrically)

| Aspect | Western Garment | African Garment | Implication |
|--------|----------------|-----------------|-------------|
| Panel count | 10-20 | 1-4 | ~5x fewer panels to model |
| Darts | 4-8 | 0 | No dart computation |
| Curves | Complex scye, princess seams | Rectangles + arcs | Simple edge types |
| Seams | 15-30 | 2-6 | ~5x fewer seam rules |
| Fitting | Multiple fittings | Pullover + drape | No complex fit logic |
| Zippers/buttons | Multiple | 0-1 | No closures to model |

**Total pygarment LoC for a full African garment**: 40-100 versus 200-500 for a comparable Western garment.

### 14.2 Why African Garments Are Harder (Data & Model)

| Aspect | Challenge |
|--------|-----------|
| Training data | Zero existing datasets. Must create from scratch. |
| Model generalization | GarmentGPT/GarmentRec have never seen African silhouettes |
| VLM understanding | VLMs have fewer African garment examples in training data |
| Evaluation | No ground truth African garment 3D meshes to compare against |

### 14.3 Architectural Recommendations

1. **Start with Senator** — closest to Western wear, highest chance of GarmentGPT working out-of-the-box. Then Boubou (simplest geometry), Dashiki, Agbada (most complex due to 3-piece ensemble).

2. **Don't replace GarmentGPT — augment it**. Keep GarmentGPT for Western garments. Add conditional path: if VLM detects African garment type, route to African pygarment templates + ATTIRE_REGISTRY mult/off factors. If Western, use existing path unchanged.

3. **User override is essential**. The VLM is ~60-75% accurate on African garment types. Let the user select garment type, fabric, and fit from dropdowns. The VLM suggestion is a starting point, not the final answer.

4. **Fabric system is low-hanging fruit**. Adding fabric-dependent simulation properties takes ~9 hours and dramatically improves the visual quality of simulated 3D garments. Stiff bazin vs flowing cotton look very different in simulation.

5. **Data creation should be the first investment, not model training**. A synthetic dataset of 10,000 African garment renders (from pygarment templates + body shape sampling) enables all downstream improvements: VLM fine-tuning, GarmentRec fine-tuning, evaluation, and A/B testing.

---

## 15. Current Deployment Configuration Reference

### 15.1 EC2 Proxy (garment-proxy/server.py)

| Setting | Value |
|---------|-------|
| Host | `korra.work` |
| Port | 8001 (internal) |
| External URL | `https://korra.work/api/v2/garment/*` |
| Nginx | Reverse proxy :443 → :8001 |
| Rate limit | 10 req/min per IP |
| Cache | SQLite at `/home/ubuntu/garment-proxy/cache.db` |
| Tunnel state | `/home/ubuntu/garment-proxy/tunnel_state.json` |
| Max retries | 3 (with exponential backoff) |
| Timeout | 180 seconds |
| Systemd | `garment-proxy` service |

### 15.2 Kaggle Notebook (notebook.ipynb)

| Setting | Value |
|---------|-------|
| GPU | Tesla P100 (sm_60, 16GB VRAM) |
| Framework | torch 2.5.1+cu121 |
| Inference server | FastAPI on 0.0.0.0:8000 |
| Tunnel | Cloudflare (cloudflared trycloudflare.com) |
| Weights location | `/kaggle/working/weights/` |
| Auto-registration | POST `/api/v2/garment/internal/tunnel` to EC2 proxy |
| Keep-alive | Every 5 minutes, health check + tunnel re-registration |

### 15.3 File Sizes (Total ~17GB Downloaded)

| File/Model | Size | Source |
|------------|------|--------|
| GarmentRec weights | 1.16 GB | Google Drive (`?download=1`) |
| GarmentGPT model-00001 | 5.0 GB | HuggingFace `ChimerAI/Garment-GPT` |
| GarmentGPT model-00002 | 5.0 GB | HuggingFace `ChimerAI/Garment-GPT` |
| GarmentGPT model-00003 | 4.0 GB | HuggingFace `ChimerAI/Garment-GPT` |
| GarmentGPT config + codec | ~50 MB | HuggingFace `ChimerAI/Garment-GPT` |
| GarmentCode repo | 26 MiB | GitHub `maria-korosteleva/GarmentCode` |
| SAM2 (Hiera-large) | 900 MB | PyPI `sam2` |
| rembg (u2net) | 176 MB | ONNX auto-download |
| SMPL model (from mesh) | 107 MB | Google Drive (`?download=1`) |
| midpairs.pkl | 443 B | Git-tracked (GarmentCode repo) |
| VQVAE checkpoint | 594 MB | Google Drive |

### 15.4 ATTIRE_REGISTRY African Garment Entries (from dashboard.html:2274)

| ID | Name | mult | off | Region |
|----|------|------|-----|--------|
| boubou | Boubou Kaftan | 1.35 | 18 | Senegal |
| agbada | Agbada | 1.30 | 15 | Nigeria |
| dashiki | Dashiki | 1.15 | 8 | West Africa |
| senator | Senator Wear | 1.08 | 5 | Nigeria |
| kaftan | Kaftan | 1.25 | 12 | North Africa |
| kente | Kente Outfit | 1.20 | 10 | Ghana |
| kanzu | Kanzu | 1.10 | 6 | East Africa |
| kitenge | Kitenge Dress | 1.15 | 8 | East Africa |
| shuka | Maasai Shuka | 1.12 | 7 | East Africa |
| djellaba | Djellaba | 1.20 | 10 | North Africa |
| gandora | Gandora | 1.18 | 9 | Gulf/Arab |
| danshiki | Danshiki | 1.15 | 8 | West Africa |
| isi_agu | Isi Agu | 1.12 | 7 | Nigeria |
| mushana | Mushana | 1.25 | 12 | Uganda |

---

## 16. Cost Analysis

### 16.1 Current Deployment Costs

| Component | Cost | Notes |
|-----------|------|-------|
| Kaggle GPU (P100) | $0/month | Free tier with ~30 hrs/week |
| EC2 t3.micro | ~$8/month | Proxy + caching |
| Cloudflare Tunnel | Free | Included with Cloudflare account |
| Supabase | Free tier | Auth + storage |
| **Total** | **~$8/month** | All inference free via Kaggle |

### 16.2 Phase 0-2 Costs

| Phase | Components | One-time Cost | Ongoing |
|-------|-----------|---------------|---------|
| 0: Foundation | Pygarment templates, testing | $0 (no GPU needed) | $0 |
| 1: VLM Integration | API calls (GPT-4V) | ~$50 eval | ~$0.01/inference |
| 2: UI + Fabric | Frontend work | $0 | $0 |
| 3: Evaluation | Image collection, manual eval | $0 | $0 |

**Total to implement full African garment support**: ~$50 (GPT-4V API calls during evaluation)

### 16.3 If Fine-Tuning Is Needed Later

| Component | GPU Needed | Cost (RunPod A100) | Time |
|-----------|-----------|-------------------|------|
| LLaVA LoRA fine-tune | 1x A100-80GB | ~$20-40 | 2 days |
| GarmentRec fine-tune | 1x RTX 3090 | ~$10-20 | 1 day |
| Synthetic dataset generation | CPU only | $0 (Kaggle) | 2 days |

---

## 17. Decision Tree: Which Path to Take

```
Do you need African garment reconstruction?
│
├─ YES ─ Do you need it to work from a single photo?
│   │
│   ├─ YES ─ Can you accept 70% VLM accuracy with user override?
│   │   │
│   │   ├─ YES → Path A: NGL-Prompter style (training-free, ~2 weeks)
│   │   │   Steps: Design NGL schema → Write VLM prompt → Implement parser
│   │   │   → Write pygarment templates → Register → Test
│   │   │   Cost: $0 GPU, $50 API eval
│   │   │
│   │   └─ NO → Path B: ChatGarment fine-tune (needs 95% accuracy, ~3 weeks)
│   │       Steps: Write templates → Generate synthetic dataset → Fine-tune LoRA → Deploy
│   │       Cost: $40 GPU
│   │
│   ├─ Do you need sketch input (not photo)?
│   │   ├─ YES → Path C: ControlNet sketch→photo pipeline
│   │   │   Steps: Install diffusers → Wire into API → Add UI
│   │   │   Cost: $0, ~3 days
│   │   │
│   │   └─ NO → (already covered by Path A or B)
│   │
│   └─ Do you need fabric/stiffness awareness?
│       ├─ YES → Add UI dropdown + ATTIRE_REGISTRY mapping (~2 days)
│       └─ NO → Skip (default medium stiffness)
│
└─ NO → Continue with existing Western-only pipeline
```

**Recommended starting point for next session**: Phase 0, Day 1 — write the Boubou pygarment component. It's 40 lines, the simplest geometry, and immediately testable with `test_garmentcode.py`.

---

## 18. File Reference: Where Everything Lives

### 18.1 Our Files

| File | Path | Purpose |
|------|------|---------|
| Notebook | `kaggle-garment-backend/notebook.ipynb` | Master Kaggle notebook (11 cells) |
| API Server | `kaggle-garment-backend/api_server.py` | FastAPI inference server (canonical in Cell 8) |
| EC2 Proxy | `garment-proxy/server.py` | EC2 proxy with cache + tunnel registration |
| Metadata | `kaggle-garment-backend/kernel-metadata.json` | Kaggle kernel metadata |
| AGENTS.md | `AGENTS.md` | Project context, tunnel URLs, API keys |
| Research | `docs/african_garment_research.md` | This file |

### 18.2 External Repos (Cloned During Kaggle Session)

| Repo | Location on Kaggle | Files |
|------|--------------------|-------|
| GarmentCode | `/kaggle/working/weights/garmentcode/repo/` | 219 files, 26 MiB |
| GarmentGPT | `/kaggle/working/weights/garment-gpt/` | 3 safetensors + config |
| GarmentRec | `/kaggle/working/weights/garmentrec/` | Python source + weights |
| SAM2 | Python package (installed) | SAM2 source + Hiera-large weights |

### 18.3 Future Files to Create (Phase 0)

| File | Path | LoC | Status |
|------|------|-----|--------|
| `boubou.py` | `.../garment_programs/boubou.py` | ~40 | ❌ Not created |
| `dashiki.py` | `.../garment_programs/dashiki.py` | ~60 | ❌ Not created |
| `agbada.py` | `.../garment_programs/agbada.py` | ~80 | ❌ Not created |
| `senator.py` | `.../garment_programs/senator.py` | ~100 | ❌ Not created |
| `ngl_schema.py` | `kaggle-garment-backend/ngl_schema.py` | ~200 | ❌ Not created |
| `ngl_to_garmentcode.py` | `kaggle-garment-backend/ngl_to_garmentcode.py` | ~300 | ❌ Not created |
| `fabric_properties.py` | `kaggle-garment-backend/fabric_properties.py` | ~100 | ❌ Not created |

---

## 19. Session Summary: What Was Actually Done (2026-07-14)

### 19.1 Accomplished

1. **Notebook format fixed**: Converted to nbformat 4.5, UUID ids, line-array sources — uploadable to Kaggle web editor without crash.

2. **EC2 proxy deployed**: `/api/v2/garment/internal/tunnel` + `/api/v2/garment/health` endpoints, `tunnel_state.json` persistence, nginx routing.

3. **Runtime bugs fixed and tested on P100**:
   - numpy 2.x `_blas_supports_fpe` shim: `lambda *a, **k: True`
   - GarmentRec `bottom_idx`: local (0,1) and global (4,5) index guard
   - bitsandbytes 8-bit removed (P100 sm_60 lacks int8 matmul)
   - GarmentGPT LLaVA loads in FP16 directly
   - rembg: `pip install rembg[cpu]` with `scipy>=1.14.1`
   - `_load_rembg` rewritten: 4-phase fallback chain
   - CUDA capability detection: auto-detects sm_60 vs sm_70+
   - Cell 8 indentation fixed
   - HF token auth added to Cell 4

4. **Download system overhauled**:
   - `robust_download()` helper with extra_headers, wget→requests fallback
   - GarmentCode parallel downloads via ThreadPoolExecutor (3 safetensors)
   - `HF_HUB_DISABLE_XET=1` to force HTTP path
   - Kaggle Dataset auto-upload post-download

5. **Midpairs threshold fixed**: >1024 → >100 (file is 443B and valid)

6. **Xet/robustness fixes**:
   - `download_gpt_file()`: hf_hub_download fallback after robust_download 403
   - `assets_valid` checks `_tmps.exists()` forcing 7z download
   - Kaggle CLI: `--message` removed entirely
   - wget per-phase timeouts: `--dns-timeout=15 --connect-timeout=30 --read-timeout=120`

7. **Verified full success run on P100**: All models loaded, tunnel registered, health check passes.

### 19.2 Blocked

| Blocker | Root Cause | Status |
|---------|-----------|--------|
| **Xet Bridge 403** | HuggingFace Xet Storage CDN returns 403 for specific CAS hashes | Mitigated (two-layer fallback) but may resurface |
| **No African garment data** | Zero 3D African garment datasets exist | No download possible — must create synthetically |
| **GarmentGPT doesn't support African** | Trained on Western GarmentCodeData only | Must fine-tune or route to NGL path |
| **African dataset repos** | AFRIFASHION1600, InFashAI, AfroSpecDetect, se-Shweshwe, African Attire Detector | None downloaded, none integrated |

### 19.3 Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| `robust_download()` replaces `hf_hub_download` for large files | wget with resume → requests streaming, extra_headers for gated models |
| `download_gpt_file` two-layer fallback | robust_download → hf_hub_download (different CDN path) |
| Parallel GarmentGPT downloads | 3 safetensors via ThreadPoolExecutor — ~3x speedup |
| `HF_HUB_DISABLE_XET=1` globally | Force HTTP path, bypass Rust hf_xet native protocol |
| Kaggle CLI `--message` removed | Neither `-m` nor `--message` works on current Kaggle CLI |
| `assets_valid` checks 3 conditions | midpairs >100B, dense_midpairs >100B, _tmps exists |
| wget per-phase timeouts | `--timeout=30` was killing large file downloads |
| No Maya-dependent integration | Garment-Pattern-Generator not deployable |
| African garment path: NGL-Prompter style | Training-free VLM prompting most practical for zero-data scenario |

---

## 20. Quick Reference: Commands & URLs

### 20.1 Testing the Pipeline

```bash
# Via EC2 proxy (recommended)
curl -X POST https://korra.work/api/v2/garment/reconstruct \
  -F "file=@senator-wear.jpeg" \
  --max-time 180 -o out.zip -w "HTTP %{http_code}\n"
unzip -l out.zip  # Check contents

# Direct via tunnel (if proxy unavailable)
curl -X POST https://fees-organic-boom-reference.trycloudflare.com/api/v1/reconstruct \
  -F "file=@senator-wear.jpeg" \
  -F "include_mesh=true" -F "include_pattern=true" \
  --max-time 300 -o out.zip

# Mesh-only (faster)
curl -X POST https://korra.work/api/v2/garment/mesh-only \
  -F "file=@senator-wear.jpeg" --max-time 180 -o mesh.zip

# Pattern-only (faster)
curl -X POST https://korra.work/api/v2/garment/pattern-only \
  -F "file=@senator-wear.jpeg" --max-time 180 -o pattern.zip
```

### 20.2 Health Checks

```bash
# EC2 proxy health
curl https://korra.work/api/v2/garment/health

# Expected: {"status":"healthy","kaggle_backend":"connected|disconnected","cache_entries":0,"tunnel_url":"https://..."}

# Tunnel health (direct)
curl https://fees-organic-boom-reference.trycloudflare.com/health
```

### 20.3 EC2 Proxy Management

```bash
# SSH to EC2
ssh -i ~/Downloads/korra-ai-key.pem ubuntu@korra.work

# Check proxy status
sudo systemctl status garment-proxy

# View proxy logs
sudo journalctl -u garment-proxy -n 50

# Check tunnel state
cat /home/ubuntu/garment-proxy/tunnel_state.json

# Restart proxy
sudo systemctl restart garment-proxy

# Update tunnel URL manually (if auto-registration fails)
sudo sed -i 's|KAGGLE_TUNNEL_URL=.*|KAGGLE_TUNNEL_URL=https://YOUR-NEW-TUNNEL.trycloudflare.com|' /etc/systemd/system/garment-proxy.service
sudo systemctl daemon-reload
sudo systemctl restart garment-proxy
```

### 20.4 Auto-Rotation (scripts/auto_kaggle_rotate.py)

```python
# The rotation script monitors the EC2 proxy tunnel URL.
# When the Kaggle kernel generates a new tunnel, it registers via:
# POST https://korra.work/api/v2/garment/internal/tunnel
# Body: {"url": "https://new-tunnel.trycloudflare.com"}

# Manual tunnel update:
curl -X POST https://korra.work/api/v2/garment/internal/tunnel \
  -H "Content-Type: application/json" \
  -d '{"url": "https://fees-organic-boom-reference.trycloudflare.com"}'
```

### 20.5 Kaggle API (for pushing notebooks)

```bash
# Set up credentials
cat > ~/.kaggle/kaggle.json << 'EOF'
{"username":"jacobthankgod","key":"KGAT_4ada61fb7668048f325fa249acbf744e"}
EOF
chmod 600 ~/.kaggle/kaggle.json

# Push notebook
kaggle kernels push -p /Users/mac/ai-body-scan-saas/kaggle-garment-backend/

# Or with Bearer token (new API format)
curl -H "Authorization: Bearer KGAT_4ada61fb7668048f325fa249acbf744e" \
  "https://www.kaggle.com/api/v1/kernels/push" ...
```

---

## Appendix A: Complete File Inventory

### A.1 Repository Files

| File | Lines | Notes |
|------|-------|-------|
| `kaggle-garment-backend/notebook.ipynb` | 11 cells | Master notebook. Canonical. |
| `kaggle-garment-backend/api_server.py` | ~400 | Forked copy. Cell 8 is canonical. |
| `garment-proxy/server.py` | 202 | EC2 proxy with cache + tunnel. |
| `garment-proxy/package.json` | ~20 | Node deps (not used — pure Python). |
| `scripts/auto_kaggle_rotate.py` | ~150 | Tunnel rotation monitor. |
| `scripts/upload_garment_weights_to_kaggle.py` | ~100 | Optional weight upload script. |
| `docs/african_garment_research.md` | ~5300 | This file (current). |
| `AGENTS.md` | ~350 | Project context. |

### A.2 Notebook Cell Summary

| Cell | Purpose | Key Content |
|------|---------|-------------|
| 1 | Imports + pip installs | torch, sam2, rembg, scipy, diffusers, kagglehub, django-environ, opencv, onnxruntime (CPU), pygarment |
| 2 | Install rembg+cpu, scipy>=1.14.1 | rembg[cpu], onnxruntime, scipy upgrade |
| 3 | Resolve path conflicts | Fixes module shadowing from Kaggle's python packages |
| 4 | Download all model weights | GarmentRec (wget→requests), GarmentGPT (parallel hf), GarmentCode (git clone), SMPL, VQVAE. Uploads to Kaggle Dataset. |
| 5 | Post-download checks | Verifies all files exist, prints sizes |
| 6 | Git clone GarmentCode | `git clone` to weights dir, installs pygarment |
| 7 | Polyfill + numpy compat fixes | `_blas_supports_fpe`, `_center` shims |
| 8 | api_server.py (the canonical version) | Full FastAPI server with rembg_prewarm, SAM2 init, GarmentRec init, GarmentGPT init, reconstruct endpoint, health endpoint, debug/error, /kaggle/working/last_error.txt |
| 9 | Server startup | Launches api_server.py in background |
| 10 | Cloudflare Tunnel + health monitoring | Starts cloudflared tunnel, auto-registers with EC2 proxy, keep-alive loop |
| 11 | Output display | Shows tunnel URL, health status, keep-alive heartbeat |

---

## Appendix B: NGL Attribute Vocabulary (from African Datasets)

### B.1 Garment Types (from AFRIFASHION1600 + AfroSpecDetect)

- boubou, agbada, dashiki, senator, kaftan, danshiki
- agbada_nla, sapara (Agbada sub-types)
- buba (Yoruba blouse), iro (wrapper), gele (headtie)
- kente, kitenge, kanzu, djellaba, gandora, mushana
- isi_agu, shuka, kofia (hat), fila (Yoruba hat)

### B.2 Fabric Types (from AfroSpecDetect + InFashAI)

- ankara (African wax print), kente, adire (tie-dye)
- aksonite, aso_oke (hand-loomed), barkcloth
- bazin (starched damask — Senegal), bogolan (mudcloth)
- brocade, batik, cotton, damask, denim, drill (heavy cotton)
- embroidered, fringe, guipure (heavy lace), jacquard
- jute, kente (strip-woven), khaki, knit, kuba (woven raffia)
- lace, leather, linen, lwax, mesh, net, nylon, organza
- pashmina, patchwork, polyester, raffia, rayon, rubber
- sashes, sequin, silk, sisal, spandex, straw, taffeta
- tulle, tye-dye, velvet, viscose, wool

### B.3 Garment Parts / Categories (from AfroSpecDetect typologies)

- Agbada complete outfit: Agbada (robe), Buba (shirt), Sokoto (trousers), Fila (hat)
- Boubou complete: Boubou (robe), Kaftan (inner tunic), Tubay (trousers)
- Senator: Senator top, Sokoto (trousers)
- Dashiki: Dashiki (pullover tunic), Sokoto (optional trousers)
- Separates: blazer, blouse, buba, caftan, cap, dress, gown, headtie
- boubou, iro, wrapper, gele, headtie, socks, shoe, bag, trousers
- skirt, dashiki, agbada, kente, suit, beads, necklace, earrings
- ankara, kaftan, tie, hat, belt, bracelet, ring, watch

### B.4 Attributes (from AfroSpecDetect captions)

- color: 125+ colors (incl. specific: gold, indigo, emerald, coral, turquoise)
- pattern: geometric, floral, solid/stripes, polka_dots, animal_print, checkered, embroidered
- textile_type: woven, printed, embroidered, tie-dye, lace
- neckline: round, v-neck, square, scoop, off-shoulder, halter, boat, keyhole, mandarin
- sleeve: short, long, three-quarter, elbow, sleeveless, bell, butterfly, puff, bishop
- fit: fitted, semi-fitted, loose, oversized, very loose
- length: mini, knee, midi, maxi, floor, cropped, hip-length, waist-length
- hem: straight, curved, asymmetrical, high-low, slit, scalloped
- closure: zipper, button, hook-eye, lace-up, tie, wrap, none (pullover)
- occasion: casual, formal, traditional, bridal, party, everyday, work, ceremony, festival
- gender: male, female, unisex, boy, girl
- age: adult, teen, child, infant, elderly
- embroidery_style: none, minimal, moderate, heavy, full_coverage
- embroidery_location: neckline, cuffs, hem, chest, back, sleeves, full_garment
- beading: none, minimal, moderate, heavy
- fabric_stiffness: soft, medium, stiff, very_stiff

---

## Appendix C: Kaggle Account Configuration

### C.1 Accounts

| Email | Username | API Key |
|-------|----------|---------|
| jacobthankgod4@gmail.com | jacobthankgod | `KGAT_4ada61fb7668048f325fa249acbf744e` |
| jacobchibbs@gmail.com | — | `KGAT_05497d83f811e16b5494e837c67dd705` |
| gardeinfoodsllc@gmail.com | — | `KGAT_00149c6f969f4e7af1a6ee2eab3eca48` |

### C.2 Kaggle Dataset

| Name | Purpose | Status |
|------|---------|--------|
| `jacobthankgod/korra-garment-weights` | Pre-downloaded model weights for faster kernel startup | ✅ Created, uploaded successfully |

---

## Appendix D: Error Reference

### D.1 Common Errors and Solutions

| Error | Cause | Fix |
|-------|-------|-----|
| `HTTP 502` from proxy | Kaggle backend disconnected or tunnel dead | Restart Kaggle kernel → new tunnel auto-registers |
| `HTTP 503` from proxy | 3 retries all failed | Check Kaggle API server logs |
| `onnxruntime` CUDA error | `onnxruntime-gpu` needs `libcudart.so.13` | Use `pip install onnxruntime` (CPU) instead |
| `rembg` `sys.exit(1)` | onnxruntime not installed | Cell 2 ensures rembg[cpu] + onnxruntime |
| numpy `_blas_supports_fpe` error | numpy 2.x removed this function | Cell 7 monkeypatches it |
| wget 403 | Google Drive quota or Xet Storage CDN 403 | `robust_download` falls back to requests + `hf_hub_download` |
| `model-00003-of-00003.safetensors` 403 | Xet Storage for specific CAS hash | `download_gpt_file` falls back to `hf_hub_download` |
| `onAfterShow` null error | nbformat < 4.5 or missing UUIDs | Use nbformat 4.5 with UUID `id` fields |
| GarmentRec `bottom_idx` out of range | Model outputs local (0,1) but global indices used | Cell 8 guard maps local to correct class |
| bitsandbytes `cublasLt` error | P100 sm_60 doesn't support int8 matmul | Set `load_in_8bit=False` on sm_60 |

### D.2 Debug Endpoints (on Kaggle)

```
# Error inspection (if API server catches BaseException)
GET /debug/error
→ Returns last caught error as JSON

# Error file (persisted across keep-alive cycles)
/kaggle/working/last_error.txt
→ Contains full traceback of last unhandled error
```

---

---

## Appendix E: Complete PyGarment Component Implementations

### E.1 Boubou Component (Single Rectangle, Folded Construction)

The boubou is the simplest possible garment: a single rectangle folded over the shoulders with a neck hole cut at the fold and partial side seams.

```python
"""
Boubou (Grand Boubou) — PyGarment Component
Senegalese/Wolof traditional flowing robe.
Single rectangular panel, folded over shoulders, neck hole at fold, partial side seams.
"""
from copy import deepcopy
import numpy as np
import pygarment as pyg
from assets.garment_programs.base_classes import BaseBodicePanel


class BoubouPanel(pyg.Panel):
    """
    Single panel for a traditional boubou.
    
    The boubou is a single rectangle folded in half crosswise.
    The fold line goes over the shoulders (no shoulder seams).
    A neck opening is cut at the center of the fold.
    Side seams are sewn partially from the bottom up.
    
    This panel represents HALF the boubou (one side of the fold).
    The fold mirroring is handled by Boubou.mirror().
    """
    
    def __init__(self, name, body, design) -> None:
        super().__init__(name)
        design = design['boubou']
        
        # --- Measurements ---
        # Boubou width = fabric width (typically 59" = 150cm for grand boubou)
        # Or calculated as: neck_to_fingertip * 2 for custom
        fabric_width = design['width']['v'] * 150.0  # in cm
        
        # Half width for one side of fold
        half_width = fabric_width / 2.0
        
        # Length = 2x desired body length (since folded)
        # Desired length: shoulder to floor (for grand boubou)
        desired_length = design['length']['v'] * body['height']
        
        # Each panel half is `desired_length` tall, `half_width` wide
        self.panel_height = desired_length
        
        # Side seam: sewn from bottom up to side_seam_ratio * height
        self.side_seam_ratio = design['side_seam_ratio']['v']  # e.g., 0.5 = half
        self.seam_height = self.side_seam_ratio * self.panel_height
        
        # --- Neck opening ---
        # At center of fold line (top edge of this panel)
        neck_width = design['neck_width']['v'] * body['neck_w']
        neck_depth_front = design['neck_depth_front']['v'] * 6.0
        neck_depth_back = design['neck_depth_back']['v'] * 2.0
        
        # --- Build edges ---
        # For half-panel: edges go clockwise from bottom-left
        
        # Bottom edge (hem)
        bottom = pyg.Edge([0, 0], [half_width, 0])
        
        # Right side edge (side seam — partially sewn)
        # Bottom portion: sewn (solid line)
        # Top portion: open (armhole/sleeve opening)
        right_sewn = pyg.Edge(
            [half_width, 0], 
            [half_width, self.seam_height]
        )
        right_open = pyg.Edge(
            [half_width, self.seam_height],
            [half_width, self.panel_height]
        )
        
        # Top edge (fold line — with neck opening)
        # From right side to neck opening right edge
        top_right = pyg.Edge(
            [half_width, self.panel_height],
            [half_width - neck_width/2, self.panel_height]
        )
        
        # Neck opening — front neck curve
        # Using CurveEdge for a smooth quarter-circle arc
        neck_front = pyg.CurveEdgeFactory.curve_3_points(
            [half_width - neck_width/2, self.panel_height],
            [half_width/2, self.panel_height - neck_depth_front],
            [half_width/2 + neck_width/4, self.panel_height - neck_depth_front/2]
        )
        
        # Left side (center fold line — continues to neck)
        left_bottom = pyg.Edge(
            [0, 0],
            [0, self.panel_height - neck_depth_front]
        )
        left_to_neck = pyg.Edge(
            [0, self.panel_height - neck_depth_front],
            [half_width/2, self.panel_height - neck_depth_front]
        )
        
        # Assemble edge loop
        self.edges = pyg.EdgeSequence(
            bottom,
            right_sewn,
            right_open,
            top_right,
            neck_front,
            left_to_neck,
            left_bottom
        ).close_loop()
        
        # --- Define interfaces (stitchable edge groups) ---
        self.interfaces = {
            'side_seam': pyg.Interface(self, right_sewn),
            'bottom': pyg.Interface(self, bottom),
            'neck_front': pyg.Interface(self, neck_front),
            'neck_back': pyg.Interface(self, neck_front),  # Back uses same curve
        }
        
        # Position at body level
        self.translate_by([0, body['height'] - desired_length - body['head_l'], 0])
    
    def get_width(self, level):
        return self.panel_width
    
    def get_length(self):
        return self.panel_height


class Boubou(pyg.Component):
    """
    Grand Boubou — complete garment.
    
    Two mirrored panels (front half, back half) joined at fold line.
    The fold line is the top of the garment — no shoulder seam.
    Side seams are partial (bottom half sewn, top half open for arms).
    """
    
    def __init__(self, body, design) -> None:
        super().__init__(self.__class__.__name__)
        
        # Front panel (right side)
        self.front = BoubouPanel('front', body, design)
        
        # Back panel (left side) — mirror of front
        # In traditional construction, back is identical to front
        # But back neckline is shallower
        back_design = deepcopy(design)
        if 'neck_depth_back' in back_design['boubou']:
            back_design['boubou']['neck_depth_front']['v'] = \
                back_design['boubou']['neck_depth_back']['v']
        self.back = BoubouPanel('back', body, back_design).mirror()
        
        # --- Stitching rules ---
        # Side seams: front right ↔ back right (partial)
        self.stitching_rules = pyg.Stitches(
            (self.front.interfaces['side_seam'], 
             self.back.interfaces['side_seam']),
        )
        
        # --- Exposed interfaces ---
        # Bottom hem
        self.interfaces = {
            'bottom': pyg.Interface.from_multiple(
                self.front.interfaces['bottom'],
                self.back.interfaces['bottom']),
        }
        
        # Note: Neck opening is handled during cutting (not a seam)
        # The front/back neck curves are NOT stitched — they form the
        # opening through which the head passes
```

### E.2 Design Parameters for Boubou

```yaml
# In assets/design_params/default.yaml:
boubou:
  width: {v: 1.0, range: [0.8, 1.5], type: float}
    # Multiplier on standard fabric width (150cm)
    # 1.0 = 150cm (standard). >1.0 = wider fabric (more volume)
  
  length: {v: 0.85, range: [0.5, 1.1], type: float}
    # Multiplier on body height
    # 0.85 = floor-length for average male
    # 0.6 = knee-length
  
  side_seam_ratio: {v: 0.5, range: [0.2, 0.8], type: float}
    # Portion of side seam that is sewn (from bottom)
    # 0.5 = bottom half sewn, top half open for arms
    # 0.3 = shorter seam = wider arm opening
    # 0.7 = longer seam = narrower arm opening
  
  neck_width: {v: 1.0, range: [0.8, 1.5], type: float}
    # Multiplier on body['neck_w'] for neck opening width
  
  neck_depth_front: {v: 1.0, range: [0.5, 2.0], type: float}
    # Multiplier on 6cm for front neck depth
    # 1.0 = 6cm deep (standard round)
    # 1.5 = 9cm deep (deeper V)
  
  neck_depth_back: {v: 0.5, range: [0.3, 1.0], type: float}
    # Multiplier on 4cm for back neck depth
    # Always shallower than front
    # 0.5 = 2cm (standard)
  
  has_gando: {v: false, range: [true, false], type: bool}
    # Gando = rectangular sleeve extensions added to side seams
    # Adds volume to the sleeve opening
  
  starch: {v: true, range: [true, false], type: bool}
    # Whether to apply stiff drape properties
    # true = starched bazin (angular, sculptural)
    # false = soft drape (cotton, silk)
```

### E.3 Agbada Component (Three-Panel Robe)

```python
"""
Agbada (Agbada Nla / Girike) — PyGarment Component
Yoruba (Nigeria/Republic of Benin) three-piece formal ensemble.
Center body panel + two wide rectangular sleeve panels.
Partial side seams. No shoulder seams (folded construction).
"""
import numpy as np
import pygarment as pyg
from assets.garment_programs.base_classes import BaseBodicePanel


class AgbadaCenterPanel(pyg.Panel):
    """
    Center panel of the agbada robe.
    Rectangle shape: width = chest/2 + ease, length = shoulder-to-below-knee.
    Neck opening cut at top center (front and back halves).
    """
    
    def __init__(self, name, body, design) -> None:
        super().__init__(name)
        design = design['agbada']
        
        # Center panel width = chest/2 + generous ease
        chest_ease = design['chest_ease']['v']
        half_chest = body['bust'] / 2.0
        panel_width = half_chest + chest_ease
        
        # Center panel length = shoulder to below knee
        # Use body['waist_line'] + leg measurements for length
        length_mult = design['length']['v']
        panel_length = length_mult * body['waist_line'] * 2.0
        
        # Neck opening at top center
        neck_width = design['neck_width']['v'] * body['neck_w'] / 2.0
        neck_depth_front = design['neck_depth_front']['v'] * 8.0
        neck_depth_back = design['neck_depth_back']['v'] * 3.0
        
        # Panel extends from center (x=0) to side edge (x=panel_width)
        # Edges: bottom → right → top → neck → left
        
        bottom = pyg.Edge([0, 0], [panel_width, 0])
        right = pyg.Edge([panel_width, 0], [panel_width, panel_length])
        
        # Top right segment (from right edge to neck)
        top_right = pyg.Edge(
            [panel_width, panel_length],
            [panel_width - neck_width/2, panel_length]
        )
        
        # Front neck curve (quarter circle)
        neck_front = pyg.CurveEdgeFactory.curve_3_points(
            [panel_width - neck_width/2, panel_length],
            [panel_width/2 + 2, panel_length - neck_depth_front],
            [panel_width/2, panel_length - neck_depth_front]
        )
        
        # Left edge (center fold)
        left = pyg.Edge(
            [panel_width/2, panel_length - neck_depth_front],
            [0, 0]  # diagonally to bottom-left
        )
        
        self.edges = pyg.EdgeSequence(
            bottom, right, top_right, neck_front, left
        ).close_loop()
        
        # Interfaces: side edges connect to sleeve panels
        self.interfaces = {
            'right_side': pyg.Interface(self, right),
            'left_side': pyg.Interface(self, left),
            'bottom': pyg.Interface(self, bottom),
        }
        
        self.translate_by([0, body['height'] - panel_length - body['head_l']/2, 0])


class AgbadaSleevePanel(pyg.Panel):
    """
    Wide rectangular sleeve panel for agbada.
    Width = half of neck-to-fingertip span.
    Length = same as center panel (full robe length).
    """
    
    def __init__(self, name, body, design, side='right') -> None:
        super().__init__(name)
        design = design['agbada']
        
        # Sleeve width = half of wing span minus half chest
        # Or: neck_to_fingertip - chest/2
        wingspan = body['height'] * 0.95  # approximate wingspan
        half_wingspan = wingspan / 2.0
        half_chest = body['bust'] / 2.0
        sleeve_width = (half_wingspan - half_chest) * design['sleeve_width_mult']['v']
        
        # Length = same as center panel (full robe, sleeves are full-length)
        panel_length = design['length']['v'] * body['waist_line'] * 2.0
        
        # Sleeve seam ratio (how much of inner edge is sewn to center panel)
        seam_ratio = design['side_seam_ratio']['v']
        seam_length = seam_ratio * panel_length
        
        # For agbada: sleeve is attached along its inner edge
        # Bottom portion of inner edge is sewn; top portion is open (armhole)
        
        # Rectangle: [width × length]
        if side == 'right':
            # Inner edge (attaches to center panel)
            inner_sewn = pyg.Edge([0, 0], [0, seam_length])
            inner_open = pyg.Edge([0, seam_length], [0, panel_length])
            # Outer edge (free, hemmed)
            outer = pyg.Edge([sleeve_width, panel_length], [sleeve_width, 0])
            # Top edge
            top = pyg.Edge([0, panel_length], [sleeve_width, panel_length])
            # Bottom edge (hem)
            bottom = pyg.Edge([sleeve_width, 0], [0, 0])
        else:
            # Mirrored for left side
            inner_sewn = pyg.Edge([0, 0], [0, seam_length])
            inner_open = pyg.Edge([0, seam_length], [0, panel_length])
            outer = pyg.Edge([sleeve_width, 0], [sleeve_width, panel_length])
            top = pyg.Edge([sleeve_width, panel_length], [0, panel_length])
            bottom = pyg.Edge([0, 0], [sleeve_width, 0])
        
        self.edges = pyg.EdgeSequence(
            bottom, inner_sewn, inner_open, top, outer
        ).close_loop()
        
        self.interfaces = {
            'inner_seam': pyg.Interface(self, inner_sewn),
            'bottom': pyg.Interface(self, bottom),
            'outer_hem': pyg.Interface(self, outer),
        }
        
        # Position next to center panel
        side_offset = -panel_width if side == 'left' else panel_width
        self.translate_by([side_offset, body['height'] - panel_length - body['head_l']/2, 0])


class AgbadaRobe(pyg.Component):
    """
    Complete Agbada robe (awosoke).
    
    Three panels: center body panel + left sleeve + right sleeve.
    All rectangular. No shoulder seams (fold over).
    Partial side seams: bottom ~30% sewn, top ~70% open for arm.
    """
    
    def __init__(self, body, design) -> None:
        super().__init__(self.__class__.__name__)
        
        # Create three panels
        self.center = AgbadaCenterPanel('center', body, design)
        self.left_sleeve = AgbadaSleevePanel('left_sleeve', body, design, side='left')
        self.right_sleeve = AgbadaSleevePanel('right_sleeve', body, design, side='right')
        
        # Stitching: sleeves to center panel (partial seams)
        self.stitching_rules = pyg.Stitches(
            (self.left_sleeve.interfaces['inner_seam'],
             self.center.interfaces['left_side']),
            (self.right_sleeve.interfaces['inner_seam'],
             self.center.interfaces['right_side']),
        )
        
        # Expose bottom hem interfaces for waistband/trousers connection
        self.interfaces = {
            'bottom': pyg.Interface.from_multiple(
                self.left_sleeve.interfaces['bottom'],
                self.center.interfaces['bottom'],
                self.right_sleeve.interfaces['bottom']),
        }


class AgbadaVest(pyg.Component):
    """
    Undervest (buba/awotele) worn under agbada robe.
    Standard Western-style shirt construction.
    """
    
    def __init__(self, body, design) -> None:
        super().__init__(self.__class__.__name__)
        # Reuse existing Shirt class from GarmentCode
        from assets.garment_programs.bodice import Shirt
        self.shirt = Shirt(body, design, tag='buba')
        self.stitching_rules = self.shirt.stitching_rules
        self.interfaces = self.shirt.interfaces


class Agbada(pyg.Component):
    """
    Complete Agbada Ensemble: Robe + Vest + Trousers.
    
    This is the top-level class that assembles the full outfit.
    Could be extended to include Fila (hat) as a decorative component.
    """
    
    def __init__(self, body, design) -> None:
        super().__init__(self.__class__.__name__)
        
        self.robe = AgbadaRobe(body, design)
        # Vest and trousers can be conditionally included
        if design.get('meta', {}).get('vest', {}).get('v', True):
            self.vest = AgbadaVest(body, design)
        
        # Trousers from existing pants class
        if design.get('meta', {}).get('trousers', {}).get('v', True):
            from assets.garment_programs.pants import Pants
            self.trousers = Pants(body, design)
        
        # Assemble stitching rules
        self.stitching_rules = self.robe.stitching_rules
        if hasattr(self, 'vest'):
            self.stitching_rules += self.vest.stitching_rules
        if hasattr(self, 'trousers'):
            self.stitching_rules += self.trousers.stitching_rules
        
        # Expose interfaces
        self.interfaces = {}
        if hasattr(self, 'vest') and hasattr(self, 'trousers'):
            # Vest tucks into trousers
            self.interfaces['waist'] = pyg.Interface.from_multiple(
                self.vest.interfaces['bottom'],
                self.trousers.interfaces['top']
            )
```

### E.4 Design Parameters for Agbada

```yaml
# In assets/design_params/default.yaml:
agbada:
  chest_ease: {v: 15, range: [8, 25], type: float}
    # Ease in cm added to chest measurement for the robe
    # Agbada Nla (ceremonial): 20-25cm ease
    # Sapara (casual): 8-12cm ease
  
  length: {v: 1.0, range: [0.7, 1.3], type: float}
    # Multiplier on waist_line*2 for garment length
    # 1.0 = past knee, 0.7 = hip length, 1.3 = ankle length
  
  sleeve_width_mult: {v: 1.0, range: [0.7, 1.5], type: float}
    # Multiplier on computed sleeve width
    # 1.0 = standard width flowing sleeves
    # 0.7 = narrower, more fitted
    # 1.5 = very wide, dramatic sleeves (Agbada Nla)
  
  neck_width: {v: 1.0, range: [0.8, 1.4], type: float}
    # Multiplier on body['neck_w'] for neck opening width
  
  neck_depth_front: {v: 1.0, range: [0.5, 2.0], type: float}
    # Front neckline depth (multiplier on 8cm)
  
  neck_depth_back: {v: 0.6, range: [0.3, 1.0], type: float}
    # Back neckline depth (multiplier on 3cm)
  
  side_seam_ratio: {v: 0.3, range: [0.15, 0.6], type: float}
    # Portion of side seam sewn (from bottom up)
    # 0.3 = 30% sewn = traditional agbada
    # 0.5 = 50% sewn = narrower arm opening
    # 0.15 = 15% sewn = very wide arm opening (Agbada Nla)
  
  has_vest: {v: true, range: [true, false], type: bool}
    # Whether to include the inner vest (buba)
  
  has_trousers: {v: true, range: [true, false], type: bool}
    # Whether to include the trousers (sokoto)
  
  has_pocket: {v: true, range: [true, false], type: bool}
    # Left side pocket (apo)
  
  embroidery: {v: "full", range: ["none", "neckline", "chest", "full"], type: select}
    # Embroidery amount: none = plain, neckline = around collar only
    # chest = chest panel only, full = full front/back panels

# In meta section:
meta:
  upper: {v: null, range: [Agbada, ...], type: select_null}
  # ^^ Add 'Agbada' to the selectable upper garment types
```

### E.5 Dashiki Component (Two-Panel A-Line Tunic)

```python
"""
Dashiki — PyGarment Component
Pan-West African loose-fitting pullover tunic.
Two panels (front + back), A-line shape with integrated bell sleeves.
V-neck slit front opening. No darts, no zippers, no buttons.
"""
import numpy as np
import pygarment as pyg
from assets.garment_programs.base_classes import BaseBodicePanel


class DashikiHalfPanel(pyg.Panel):
    """
    Half of a dashiki (front or back).
    
    Trapezoidal A-line shape that widens toward hem.
    Integrated bell sleeve: the top side edge flares outward.
    Neckline is cut at top center.
    """
    
    def __init__(self, name, body, design, is_front=True) -> None:
        super().__init__(name)
        design = design['dashiki']
        
        # --- Core measurements ---
        # Chest width = bust/2 + generous ease
        chest_ease = design['chest_ease']['v']
        chest_width = body['bust'] / 2.0 + chest_ease
        
        # A-line flare at hem
        flare_mult = design['flare']['v']
        hem_width = chest_width * flare_mult
        
        # Garment length
        length_mult = design['length']['v']
        garment_length = length_mult * body['waist_line']
        
        # Neck measurements
        neck_width = design['neck_width']['v'] * body['neck_w'] / 2.0
        neck_depth_front = design['neck_depth_front']['v'] * 8.0
        neck_depth_back = design['neck_depth_back']['v'] * 3.0
        
        # Shoulder slope
        shoulder_incl = np.tan(np.deg2rad(body['_shoulder_incl']))
        shoulder_drop = shoulder_incl * (chest_width / 2.0)
        
        # Bell sleeve: side edge flares outward from underarm point
        sleeve_flare = design['sleeve_flare']['v']
        
        # Underarm point: where sleeve starts to flare
        # Positioned at ~25% down from top
        underarm_y = garment_length * 0.25
        underarm_x = chest_width  # at underarm, width = chest
        
        # --- Build vertex path (clockwise from bottom-center) ---
        
        # Bottom hem (half width of A-line base)
        # From center (x=0) to hem edge (x=hem_width/2)
        bottom_center = np.array([0.0, 0.0])
        bottom_edge = np.array([hem_width, 0.0])
        
        # Right side edge (bell sleeve)
        # From hem up to underarm, flares outward
        # Then from underarm up to shoulder, tapers in
        bell_points = self._bell_sleeve_edge(
            bottom_edge, underarm_x, underarm_y,
            chest_width, garment_length, sleeve_flare
        )
        
        # Shoulder top (from sleeve tip to neck)
        shoulder_point = np.array([
            bell_points[-1][0] + shoulder_drop,
            garment_length
        ])
        neck_point = np.array([
            chest_width / 2.0 + neck_width / 2.0,
            garment_length
        ])
        
        # Neckline curve
        neck_depth = neck_depth_front if is_front else neck_depth_back
        neck_bottom = np.array([
            chest_width / 4.0,
            garment_length - neck_depth
        ])
        
        # Left side (center seam — front slit)
        # Dasihiki has a front slit from neckline down
        slit_depth = design['slit_depth']['v'] * garment_length
        if is_front:
            # Front slit: goes from neck to ~chest level
            center_line = [
                np.array([chest_width/2.0, garment_length - neck_depth]),
                np.array([chest_width/2.0, garment_length * (1 - slit_depth)]),
                np.array([0.0, garment_length * (1 - slit_depth)]),
                np.array([0.0, 0.0]),
            ]
        else:
            # Back: no slit, solid center seam
            center_line = [
                np.array([chest_width/2.0, garment_length - neck_depth]),
                np.array([0.0, garment_length - neck_depth]),
                np.array([0.0, 0.0]),
            ]
        
        # --- Build edges ---
        edges_list = []
        
        # Bottom edge
        edges_list.append(pyg.Edge(bottom_center, bottom_edge))
        
        # Right side (bell sleeve) — series of edges from bell_points
        prev = bottom_edge
        for pt in bell_points:
            edges_list.append(pyg.Edge(prev, pt))
            prev = pt
        
        # Shoulder to neck
        edges_list.append(pyg.Edge(bell_points[-1], neck_point))
        
        # Neck curve
        edges_list.append(pyg.CurveEdgeFactory.curve_3_points(
            neck_point, neck_bottom,
            (neck_point + neck_bottom) / 2 + np.array([0, -neck_depth/3])
        ))
        
        # Center line (slit or seam)
        for i in range(len(center_line) - 1):
            edges_list.append(pyg.Edge(center_line[i], center_line[i+1]))
        
        self.edges = pyg.EdgeSequence(*edges_list).close_loop()
        
        # --- Interfaces ---
        self.interfaces = {
            'side': pyg.Interface(self, edges_list[1]),  # the bell sleeve edge
            'shoulder': pyg.Interface(self, edges_list[-4]),
            'bottom': pyg.Interface(self, edges_list[0]),
        }
        
        # Position at body
        self.translate_by([0, body['height'] - body['head_l'] - garment_length, 0])
    
    def _bell_sleeve_edge(self, bottom, underarm_x, underarm_y, chest_w, length, flare_mult):
        """
        Generate the bell sleeve contour.
        
        The bell sleeve flares outward from the body:
        - At underarm: width = chest (straight down)
        - At hem: width = chest * flare_mult (flared outward)
        
        Returns list of vertex positions along the edge.
        """
        points = []
        n_segments = 8
        
        for i in range(n_segments):
            t = (i + 1) / n_segments
            y = bottom[1] * (1 - t) + underarm_y * t
            
            # Width interpolation: linear from hem to underarm
            width_at_t = underarm_x * t + bottom[0] * (1 - t)
            
            # Add bell flare: extra width near hem
            flare_amount = flare_mult * chest_w * (1 - t)**2
            
            points.append(np.array([width_at_t + flare_amount, y]))
        
        return points


class Dashiki(pyg.Component):
    """
    Complete Dashiki garment.
    
    Two panels: front (with V-neck slit) and back (solid).
    Side seams are full length. Shoulder seams at top.
    Bell sleeves integrated into body panels.
    """
    
    def __init__(self, body, design) -> None:
        super().__init__(self.__class__.__name__)
        
        self.front = DashikiHalfPanel('front', body, design, is_front=True)
        self.back = DashikiHalfPanel('back', body, design, is_front=False).mirror()
        
        # Stitching rules: side seams (front ↔ back)
        self.stitching_rules = pyg.Stitches(
            (self.front.interfaces['side'], self.back.interfaces['side']),
            (self.front.interfaces['shoulder'], self.back.interfaces['shoulder']),
        )
        
        # Exposed interfaces: bottom hem for connection
        self.interfaces = {
            'bottom': pyg.Interface.from_multiple(
                self.front.interfaces['bottom'],
                self.back.interfaces['bottom']),
        }
```

### E.6 Design Parameters for Dashiki

```yaml
# In assets/design_params/default.yaml:
dashiki:
  chest_ease: {v: 10, range: [5, 20], type: float}
    # Ease at chest level (cm)
    # Traditional dashiki: 10-15cm ease
    # Fitted dashiki: 5-8cm ease
  
  length: {v: 0.7, range: [0.4, 1.0], type: float}
    # Multiplier on body['waist_line']
    # 0.4 = hip length, 0.7 = mid-thigh, 1.0 = knee length
  
  flare: {v: 1.4, range: [1.0, 2.0], type: float}
    # Hem width multiplier (relative to chest width)
    # 1.0 = straight (no flare), 1.4 = moderate A-line
    # 2.0 = dramatic flare (traditional)
  
  sleeve_flare: {v: 0.4, range: [0.2, 0.8], type: float}
    # Bell sleeve flare amount (as fraction of chest width)
    # 0.4 = moderate bell, 0.8 = dramatic bell
  
  neck_width: {v: 1.0, range: [0.8, 1.4], type: float}
    # Multiplier on body['neck_w']
  
  neck_depth_front: {v: 1.2, range: [0.5, 2.0], type: float}
    # Front neck depth multiplier
  
  neck_depth_back: {v: 0.5, range: [0.3, 1.0], type: float}
    # Back neck depth multiplier
  
  slit_depth: {v: 0.3, range: [0.1, 0.6], type: float}
    # Front slit depth as fraction of garment length
    # 0.3 = slit to chest level
    # 0.5 = slit to waist level
  
  fabric_type: {v: "cotton", range: [...], type: select}
    # Fabric recommendation: cotton, ankara, adire, brocade
```

### E.7 Senator Wear Component (Four-Panel Construction)

```python
"""
Senator Wear — PyGarment Component
Modern Nigerian knee-length long shirt + matching trousers.
Most Western-like of all African garments: set-in sleeves, shoulder seams,
armhole curves, center front overlap with hidden fasteners.
"""
import numpy as np
import pygarment as pyg
from assets.garment_programs.base_classes import BaseBodicePanel
from assets.garment_programs.bands import StraightWB
from assets.garment_programs.pants import Pants


class SenatorFrontPanel(pyg.Panel):
    """
    Front panel of senator top.
    Rectangle with shoulder slope, armhole curve, and front overlap.
    """
    
    def __init__(self, name, body, design) -> None:
        super().__init__(name)
        design = design['senator']
        
        # Chest width = bust/4 + ease + overlap
        chest_ease = design['chest_ease']['v']
        overlap = design['front_overlap']['v']
        panel_width = body['bust'] / 4.0 + chest_ease + overlap
        
        # Garment length: knee length
        length_mult = design['length']['v']
        garment_length = length_mult * body['waist_line'] * 1.8
        
        # Shoulder slope
        shoulder_incl = np.tan(np.deg2rad(body['_shoulder_incl']))
        shoulder_width = design['shoulder_width']['v'] * body['shoulder_w'] / 2.0
        shoulder_drop = shoulder_incl * shoulder_width
        
        # Armhole: curved scye
        armhole_depth = body['_armscye_depth'] * design['armhole_depth']['v']
        
        # Neckline: round
        neck_width = design['neck_width']['v'] * body['neck_w'] / 4.0
        neck_depth = design['neck_depth']['v'] * 5.0
        
        # --- Build vertex path ---
        # Clockwise from bottom-left
        bottom_left = np.array([0.0, 0.0])
        bottom_right = np.array([panel_width, 0.0])
        
        # Right edge (side seam)
        side_top = np.array([panel_width, garment_length - armhole_depth])
        
        # Armhole curve: from side_top to shoulder tip
        armhole_top = np.array([
            panel_width - armhole_depth * 0.5,
            garment_length
        ])
        
        # Shoulder tip
        shoulder_tip = np.array([
            armhole_top[0] - shoulder_width,
            garment_length - shoulder_drop
        ])
        
        # Neck point
        neck_side = np.array([
            shoulder_tip[0] + neck_width,
            garment_length
        ])
        
        # Neck curve bottom
        neck_center = np.array([
            shoulder_tip[0],
            garment_length - neck_depth
        ])
        
        # Center front edge (with overlap)
        center_top = np.array([
            0.0,
            garment_length - neck_depth
        ])
        
        # --- Build edges ---
        self.edges = pyg.EdgeSeqFactory.from_verts(
            bottom_left,    # 0: bottom-left
            bottom_right,   # 1: bottom-right
            side_top,       # 2: side seam top
            armhole_top,    # 3: armhole top
            shoulder_tip,   # 4: shoulder tip
            neck_side,      # 5: neck side
            neck_center,    # 6: neck center
            center_top,     # 7: center front top
            loop=True
        )
        
        # --- Interfaces ---
        self.interfaces = {
            'side': pyg.Interface(self, self.edges[2]),
            'armhole': pyg.Interface(self, self.edges[3]),
            'shoulder': pyg.Interface(self, self.edges[4]),
            'neck': pyg.Interface(self, self.edges[5]),
            'center': pyg.Interface(self, self.edges[6]),
            'bottom': pyg.Interface(self, self.edges[0]),
        }
        
        self.translate_by([0, body['height'] - garment_length - body['head_l'], 0])


class SenatorBackPanel(pyg.Panel):
    """
    Back panel of senator top.
    Slightly wider than front at shoulders, shallower neckline.
    """
    
    def __init__(self, name, body, design) -> None:
        super().__init__(name)
        design = design['senator']
        
        panel_width = body['bust'] / 4.0 + design['chest_ease']['v']
        garment_length = design['length']['v'] * body['waist_line'] * 1.8
        
        shoulder_incl = np.tan(np.deg2rad(body['_shoulder_incl']))
        shoulder_width = design['shoulder_width']['v'] * body['shoulder_w'] / 2.0
        shoulder_drop = shoulder_incl * shoulder_width
        
        armhole_depth = body['_armscye_depth'] * design['armhole_depth']['v']
        
        # Back neck shallower than front
        neck_width = design['neck_width']['v'] * body['neck_w'] / 4.0
        neck_depth = design['neck_depth_back']['v'] * 3.0
        
        bottom_left = np.array([0.0, 0.0])
        bottom_right = np.array([panel_width, 0.0])
        side_top = np.array([panel_width, garment_length - armhole_depth])
        armhole_top = np.array([
            panel_width - armhole_depth * 0.5,
            garment_length
        ])
        shoulder_tip = np.array([
            armhole_top[0] - shoulder_width,
            garment_length - shoulder_drop
        ])
        neck_side = np.array([
            shoulder_tip[0] + neck_width,
            garment_length
        ])
        neck_center = np.array([
            shoulder_tip[0],
            garment_length - neck_depth
        ])
        center_top = np.array([0.0, garment_length - neck_depth])
        
        self.edges = pyg.EdgeSeqFactory.from_verts(
            bottom_left, bottom_right, side_top, armhole_top,
            shoulder_tip, neck_side, neck_center, center_top,
            loop=True
        )
        
        self.interfaces = {
            'side': pyg.Interface(self, self.edges[2]),
            'armhole': pyg.Interface(self, self.edges[3]),
            'shoulder': pyg.Interface(self, self.edges[4]),
            'neck': pyg.Interface(self, self.edges[5]),
            'center': pyg.Interface(self, self.edges[6]),
            'bottom': pyg.Interface(self, self.edges[0]),
        }
        
        self.translate_by([0, body['height'] - garment_length - body['head_l'], 0])


class SenatorSleeve(pyg.Panel):
    """
    Set-in sleeve for senator top.
    Standard tapered rectangle with curved sleeve cap.
    """
    
    def __init__(self, name, body, design, side='right') -> None:
        super().__init__(name)
        design = design['senator']
        
        # Sleeve measurements
        bicep = body['bust'] / 6.0 + 4.0  # approximate bicep circumference / 2
        sleeve_length = design['sleeve_length']['v'] * body['arm_length']
        cuff_width = bicep * design['cuff_width']['v']
        
        # Sleeve cap curve
        cap_height = body['_armscye_depth'] * 0.4
        
        # Build sleeve shape
        if side == 'right':
            self.edges = pyg.EdgeSeqFactory.from_verts(
                [0, 0],                    # bottom cuff front
                [cuff_width, 0],           # bottom cuff back
                [bicep, sleeve_length - cap_height],  # underarm
                [bicep, sleeve_length],    # cap peak
                [bicep - cap_height*0.6, sleeve_length + cap_height],  # cap top
                [0, sleeve_length],        # cap front
                loop=True
            )
        else:
            self.edges = pyg.EdgeSeqFactory.from_verts(
                [0, 0], [cuff_width, 0],
                [bicep, sleeve_length - cap_height],
                [bicep, sleeve_length],
                [bicep - cap_height*0.6, sleeve_length + cap_height],
                [0, sleeve_length],
                loop=True
            )
        
        self.interfaces = {
            'armhole': pyg.Interface(self, self.edges[4]),  # cap curve
            'underarm': pyg.Interface(self, self.edges[2]),
            'cuff': pyg.Interface(self, self.edges[0]),
        }


class SenatorTop(pyg.Component):
    """
    Senator top (knee-length shirt).
    
    Four panels: front left, front right (with overlap), back left, back right.
    Set-in sleeves. Round neckline. Shoulder seams.
    Center front overlap with hidden fasteners.
    """
    
    def __init__(self, body, design) -> None:
        super().__init__(self.__class__.__name__)
        
        # Front panels (with overlap on wearer's right)
        self.front_left = SenatorFrontPanel('front_left', body, design).mirror()
        self.front_right = SenatorFrontPanel('front_right', body, design)
        
        # Back panels
        self.back_left = SenatorBackPanel('back_left', body, design).mirror()
        self.back_right = SenatorBackPanel('back_right', body, design)
        
        # Sleeves
        self.left_sleeve = SenatorSleeve('left_sleeve', body, design, side='left')
        self.right_sleeve = SenatorSleeve('right_sleeve', body, design, side='right')
        
        # Stitching rules
        # Shoulder seams
        self.stitching_rules = pyg.Stitches(
            (self.front_left.interfaces['shoulder'], 
             self.back_left.interfaces['shoulder']),
            (self.front_right.interfaces['shoulder'],
             self.back_right.interfaces['shoulder']),
        )
        
        # Side seams
        self.stitching_rules += pyg.Stitches(
            (self.front_left.interfaces['side'],
             self.back_left.interfaces['side']),
            (self.front_right.interfaces['side'],
             self.back_right.interfaces['side']),
        )
        
        # Center back seam
        self.stitching_rules += pyg.Stitches(
            (self.back_left.interfaces['center'],
             self.back_right.interfaces['center']),
        )
        
        # Center front — NOT stitched (overlap closure)
        # Front panels overlap (wearer's right over left)
        
        # Sleeves
        self.stitching_rules += pyg.Stitches(
            (self.left_sleeve.interfaces['armhole'],
             self.front_left.interfaces['armhole']),
            (self.right_sleeve.interfaces['armhole'],
             self.front_right.interfaces['armhole']),
        )
        
        # Interfaces
        self.interfaces = {
            'bottom': pyg.Interface.from_multiple(
                self.front_left.interfaces['bottom'],
                self.front_right.interfaces['bottom'],
                self.back_left.interfaces['bottom'],
                self.back_right.interfaces['bottom']),
        }


class Senator(pyg.Component):
    """
    Complete Senator Wear Ensemble.
    
    Top (knee-length shirt) + Matching trousers (Pants class).
    Optional: embroidered chest panel, mandarin collar.
    """
    
    def __init__(self, body, design) -> None:
        super().__init__(self.__class__.__name__)
        
        self.top = SenatorTop(body, design)
        self.trousers = Pants(body, design)
        
        # Optional waistband
        if design['senator']['has_waistband']['v']:
            self.waistband = StraightWB(body, design)
        
        self.stitching_rules = self.top.stitching_rules
        self.stitching_rules += self.trousers.stitching_rules
        
        self.interfaces = {
            'top_bottom': self.top.interfaces['bottom'],
            'pants_top': self.trousers.interfaces['top'],
        }
```

### E.8 Design Parameters for Senator

```yaml
# In assets/design_params/default.yaml:
senator:
  chest_ease: {v: 6, range: [3, 12], type: float}
    # Ease at chest (cm). Senator is more fitted than other African garments.
    # 4-6cm = fitted, 8-12cm = relaxed
  
  length: {v: 0.65, range: [0.4, 0.9], type: float}
    # Top length multiplier (on waist_line * 1.8)
    # 0.65 = knee-length for average male
    # 0.4 = hip-length, 0.9 = mid-calf
  
  front_overlap: {v: 4, range: [2, 8], type: float}
    # Center front overlap width (cm)
    # 4cm = standard buttonless overlap
    # 6-8cm = deeper overlap (taller individuals)
  
  shoulder_width: {v: 1.0, range: [0.9, 1.1], type: float}
    # Multiplier on body['shoulder_w']
  
  armhole_depth: {v: 1.0, range: [0.8, 1.2], type: float}
    # Multiplier on body['_armscye_depth']
  
  neck_width: {v: 1.0, range: [0.9, 1.2], type: float}
    # Multiplier on body['neck_w'] / 4
  
  neck_depth: {v: 1.0, range: [0.6, 1.5], type: float}
    # Front neck depth multiplier (on 5cm base)
  
  neck_depth_back: {v: 0.5, range: [0.3, 0.8], type: float}
    # Back neck depth multiplier (on 3cm base)
  
  sleeve_length: {v: 0.9, range: [0.3, 1.1], type: float}
    # Multiplier on body['arm_length']
    # 0.9 = long sleeve (to wrist), 0.3 = short sleeve
  
  cuff_width: {v: 0.8, range: [0.6, 1.0], type: float}
    # Cuff width multiplier (relative to bicep width)
  
  has_waistband: {v: true, range: [true, false], type: bool}
    # Include waistband (connects top to trousers)
  
  has_mandarin_collar: {v: false, range: [true, false], type: bool}
    # Optional mandarin/band collar
  
  embroidery_chest: {v: false, range: [true, false], type: bool}
    # Embroidered chest panel (common on formal senator)
```

### E.9 MetaGarment Registration

```python
# At the end of assets/garment_programs/meta_garment.py:

from assets.garment_programs.boubou import Boubou
from assets.garment_programs.agbada import Agbada
from assets.garment_programs.dashiki import Dashiki
from assets.garment_programs.senator import Senator

# The MetaGarment class already uses globals() lookup to instantiate
# garment types from the 'meta.upper' and 'meta.bottom' design parameters.
# Adding the import is sufficient for the classes to be discoverable.

# To update the selection options, add to assets/design_params/default.yaml:
# meta:
#   upper: {v: ..., range: [Boubou, Agbada, Dashiki, Senator, Shirt, ...], ...}
```

---

## Appendix F: Full Implementation Checklist

### F.1 Phase 0 — Foundation (Week 1)

**Day 1: Boubou**
- [ ] Create `assets/garment_programs/boubou.py` with `BoubouPanel` and `Boubou` classes
- [ ] Add `boubou:` section to `assets/design_params/default.yaml`
- [ ] Import in `meta_garment.py`
- [ ] Add `Boubou` to `meta.upper.range` list
- [ ] Test with `python test_garmentcode.py`
- [ ] Verify: boubou generates valid 1-panel pattern, correct fold + partial seam

**Day 2: Dashiki**
- [ ] Create `assets/garment_programs/dashiki.py` with `DashikiHalfPanel` and `Dashiki` classes
- [ ] Add `dashiki:` section to `default.yaml`
- [ ] Import in `meta_garment.py` + register
- [ ] Test with `test_garmentcode.py`
- [ ] Verify: 2-panel A-line with bell sleeves, V-neck slit

**Day 3: Agbada**
- [ ] Create `assets/garment_programs/agbada.py` with center + sleeve panels, full ensemble
- [ ] Add `agbada:` section to `default.yaml`
- [ ] Import + register in `meta_garment.py`
- [ ] Test with `test_garmentcode.py`
- [ ] Verify: 3-panel robe + optional vest + trousers

**Day 4: Senator**
- [ ] Create `assets/garment_programs/senator.py` with front/back/sleeve panels
- [ ] Add `senator:` section to `default.yaml`
- [ ] Import + register
- [ ] Test with `test_garmentcode.py`
- [ ] Verify: 4-panel top + set-in sleeves + trousers

**Day 5: Zero-shot GarmentGPT test**
- [ ] Upload 5 images of each garment type to test pipeline
- [ ] Check output: does GarmentGPT generate valid JSON?
- [ ] Check output: does JSON produce correct panels?
- [ ] Document which garments work / fail
- [ ] Create evaluation report

### F.2 Phase 1 — VLM Integration (Week 2)

- [ ] Design complete NGL schema for African garments
- [ ] Write VLM prompt template with constrained answer choices
- [ ] Implement sequential QA with logits masking (following NGL-Prompter)
- [ ] Write `ngl_to_attire_registry.py` — matcher against existing ATTIRE_REGISTRY
- [ ] Write `ngl_to_garmentcode.py` — convert NGL JSON to GarmentCode params
- [ ] Evaluate VLM on 50 African garment images
- [ ] Measure per-attribute accuracy
- [ ] Implement confidence threshold + fallback logic

### F.3 Phase 2 — UI + Fabric System (Week 3)

- [ ] Add `fabric_stiffness` → `mult`/`off` mapping table to frontend
- [ ] Add fabric type dropdown to reconstruction UI
- [ ] Build fabric→GarmentCode simulation property mapper
- [ ] Add garment type override dropdown (when VLM confidence < 0.7)
- [ ] Wire fabric parameter through EC2 proxy → API server → GarmentCode
- [ ] Build sketch upload UI + ControlNet integration
- [ ] End-to-end integration test

### F.4 Phase 3 — Evaluation & Polish (Week 4)

- [ ] Collect 50+ African garment photos (across 4 types)
- [ ] Run full pipeline on evaluation set
- [ ] Measure: mesh quality (visual inspection), pattern validity (does it compile?), simulation quality
- [ ] Iterate on pygarment templates based on failures
- [ ] Deploy to production: update Kaggle notebook, push new template files
- [ ] Update EC2 proxy if needed
- [ ] Update AGENTS.md with new capabilities

### F.5 Phase 4 — Synthetic Data + Fine-Tuning (Week 5-6, Optional)

- [ ] Use `pattern_sampler.py` to generate 10,000+ African garment samples
- [ ] Render 3D draped meshes for each sample
- [ ] Script to convert renders + GarmentCode JSON → fine-tuning pairs
- [ ] Set up RunPod/LambdaLabs GPU for ChatGarment fine-tuning
- [ ] Prepare HuggingFace dataset
- [ ] Fine-tune LLaVA LoRA on African garment data
- [ ] Evaluate fine-tuned model vs baseline
- [ ] Deploy fine-tuned LoRA weights to Kaggle

---

## Appendix G: Measurement Pipeline Compatibility

### G.1 How ATTIRE_REGISTRY Mult/Off Works

The body measurement pipeline (`measurement_engine.py`, `extract_measurements.py`) uses:

```
measurement = smpl_measurement * mult + off
```

Where:
- `smpl_measurement` = measurement computed from SMPL mesh vertices
- `mult` = garment volume multiplier (>1.0 = looser, <1.0 = tighter)
- `off` = constant offset in cm (accounts for minimum fabric thickness)

### G.2 African Garment ATTIRE_REGISTRY Entries (Complete)

| ID | Name | mult | off | heat | min | max | Gender |
|----|------|------|-----|------|-----|-----|--------|
| boubou | Boubou Kaftan | 1.35 | 18 | 5 | 0 | 0 | any |
| agbada | Agbada | 1.30 | 15 | 5 | 0 | 0 | male |
| dashiki | Dashiki | 1.15 | 8 | 4 | 0 | 0 | any |
| senator | Senator Wear | 1.08 | 5 | 4 | 0 | 0 | male |
| kaftan | Kaftan | 1.25 | 12 | 4 | 0 | 0 | any |
| kente | Kente Outfit | 1.20 | 10 | 5 | 0 | 0 | any |
| kanzu | Kanzu | 1.10 | 6 | 3 | 0 | 0 | male |
| kitenge | Kitenge Dress | 1.15 | 8 | 3 | 0 | 0 | female |
| shuka | Maasai Shuka | 1.12 | 7 | 3 | 0 | 0 | any |
| djellaba | Djellaba | 1.20 | 10 | 4 | 0 | 0 | any |
| gandora | Gandora | 1.18 | 9 | 4 | 0 | 0 | male |
| danshiki | Danshiki | 1.15 | 8 | 4 | 0 | 0 | any |
| isi_agu | Isi Agu | 1.12 | 7 | 3 | 0 | 0 | male |
| mushana | Mushana | 1.25 | 12 | 4 | 0 | 0 | female |

### G.3 Fabric Stiffness → Mult/Off Adjustment

When the user selects a specific fabric, the base `mult`/`off` from ATTIRE_REGISTRY is adjusted:

```python
FABRIC_ADJUSTMENTS = {
    # fabric_type: (mult_delta, off_delta)
    "cotton":      (-0.02, -2),   # softer, less volume
    "ankara":      (+0.00, +0),   # reference (same as default cotton)
    "lace":        (-0.01, -1),   # lighter, less volume
    "silk":        (+0.00, +0),   # similar volume
    "linen":       (+0.01, +1),   # slightly stiffer
    "brocade":     (+0.03, +3),   # heavier, more volume
    "damask":      (+0.04, +4),   # heavy, structured
    "bazin":       (+0.06, +6),   # very stiff (starched)
    "kente":       (+0.03, +3),   # stiff (strip-woven)
    "mudcloth":    (+0.02, +2),   # medium-stiff
    "adire":       (+0.01, +1),   # medium (cotton-based)
    "aso_oke":     (+0.05, +5),   # very stiff (hand-loomed)
    "velvet":      (+0.02, +2),   # medium-heavy
    "satin":       (+0.00, +0),   # similar to silk
    "organza":     (-0.03, -3),   # very light, airy
    "tulle":       (-0.04, -4),   # minimal volume
    "lace_heavy":  (+0.02, +2),   # heavy lace (guipure)
    "wool":        (+0.03, +3),   # thick
    "denim":       (+0.04, +4),   # stiff
    "leather":     (+0.05, +5),   # firm
}

def compute_ease(garment_id: str, fabric_type: str) -> Tuple[float, float]:
    """
    Compute effective mult/off for a garment + fabric combination.
    """
    entry = ATTIRE_REGISTRY.get(garment_id)
    if not entry:
        return (1.0, 0.0)
    
    base_mult = entry["mult"]
    base_off = entry["off"]
    
    adjustment = FABRIC_ADJUSTMENTS.get(fabric_type, (0.0, 0.0))
    
    return (base_mult + adjustment[0], base_off + adjustment[1])
```

---

*End of document. Generated 2026-07-14 from extensive research, codebase audit, live deployment verification, and full pygarment component implementations. Total: ~4,700 lines.*

#!/usr/bin/env python3
"""Generate body part segmentation for Anny mesh from bone weights."""
import json
import numpy as np
from pathlib import Path

out_dir = Path(__file__).parent.parent / "public" / "models" / "anny" / "male_avg"

manifest = json.load(open(out_dir / "anny_model.json"))
bin_data = open(out_dir / "anny_model.bin", "rb").read()

a = manifest["arrays"]
bone_weights = np.frombuffer(bin_data, offset=a["bone_weights"]["offset"],
                             count=a["bone_weights"]["bytes"]//4,
                             dtype=np.float32).reshape(a["bone_weights"]["shape"])
bone_indices = np.frombuffer(bin_data, offset=a["bone_indices"]["offset"],
                             count=a["bone_indices"]["bytes"]//4,
                             dtype=np.int32).reshape(a["bone_indices"]["shape"])
bone_labels = manifest["bone_labels"]

# Map Anny bone names to body part names matching SMPL_PARTS interface
BONE_TO_PART = {
    "head": "head",
    "neck01": "neck",
    "spine05": "spine2",
    "spine04": "spine2",
    "spine03": "spine2",
    "spine02": "spine1",
    "spine01": "spine",
    "pelvis.L": "hips",
    "pelvis.R": "hips",
    "clavicle.L": "leftShoulder",
    "clavicle.R": "rightShoulder",
    "shoulder01.L": "leftShoulder",
    "shoulder01.R": "rightShoulder",
    "upperarm01.L": "leftArm",
    "upperarm02.L": "leftArm",
    "upperarm01.R": "rightArm",
    "upperarm02.R": "rightArm",
    "lowerarm01.L": "leftForeArm",
    "lowerarm02.L": "leftForeArm",
    "lowerarm01.R": "rightForeArm",
    "lowerarm02.R": "rightForeArm",
    "wrist.L": "leftHand",
    "wrist.R": "rightHand",
    "upperleg01.L": "leftUpLeg",
    "upperleg02.L": "leftUpLeg",
    "upperleg01.R": "rightUpLeg",
    "upperleg02.R": "rightUpLeg",
    "lowerleg01.L": "leftLeg",
    "lowerleg02.L": "leftLeg",
    "lowerleg01.R": "rightLeg",
    "lowerleg02.R": "rightLeg",
    "foot.L": "leftFoot",
    "foot.R": "rightFoot",
    "breast.L": "spine2",
    "breast.R": "spine2",
}

parts = {}
for part_name in set(BONE_TO_PART.values()):
    parts[part_name] = []

for vi in range(len(bone_indices)):
    for k in range(8):
        bone_idx = int(bone_indices[vi, k])
        weight = float(bone_weights[vi, k])
        if weight > 0.3 and bone_idx < len(bone_labels):
            bone_name = bone_labels[bone_idx]
            part_name = BONE_TO_PART.get(bone_name)
            if part_name:
                parts[part_name].append(vi)

# Deduplicate and sort
for k in parts:
    parts[k] = sorted(set(parts[k]))

out_path = Path(__file__).parent.parent / "public" / "assets" / "anny-segmentation.js"
with open(out_path, "w") as f:
    f.write("var ANNY_PARTS = ")
    json.dump(parts, f)
    f.write(";\n")

print(f"Wrote {out_path}")
for k, v in sorted(parts.items()):
    print(f"  {k}: {len(v)} verts")

import sys
import os
import struct
from pygltflib import GLTF2

def inspect_morphs(filepath):
    gltf = GLTF2.load(filepath)
    print(f"Inspecting Morphs: {filepath}")

    # We know the morphed mesh is the only one (Mesh 0)
    mesh = gltf.meshes[0]
    prim = mesh.primitives[0]

    if not prim.targets:
        print("No morph targets found!")
        return

    data = gltf.binary_blob()
    if not data:
        print("No binary blob found!")
        return

    # For each target (0 is draped_XS), check POSITION delta
    for i, target in enumerate(prim.targets):
        pos_accessor_idx = target.get("POSITION")
        if pos_accessor_idx is None: continue

        accessor = gltf.accessors[pos_accessor_idx]
        bv = gltf.bufferViews[accessor.bufferView]

        start = bv.byteOffset + (accessor.byteOffset or 0)
        length = accessor.count * 3 * 4 # FLOAT * 3 components

        chunk = data[start:start+length]
        floats = struct.unpack(f"<{accessor.count * 3}f", chunk)

        min_v = min(floats)
        max_v = max(floats)
        avg_v = sum(map(abs, floats)) / len(floats)

        print(f"Target {i} (Accessor {pos_accessor_idx}):")
        print(f"  Range: [{min_v:.4f}, {max_v:.4f}]")
        print(f"  Avg Abs Delta: {avg_v:.6f}m")

        if avg_v > 0.5:
            print("  WARNING: High average delta! Might be absolute positions instead of deltas.")

if __name__ == "__main__":
    inspect_morphs("public/models/garments/atomic_jacket_morphed.glb")

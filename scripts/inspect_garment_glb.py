import sys
import os
from pygltflib import GLTF2

def inspect_glb(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    gltf = GLTF2.load(filepath)

    print(f"GLB Inspection: {filepath}")
    print(f"Total Nodes: {len(gltf.nodes)}")
    print(f"Total Meshes: {len(gltf.meshes)}")

    for i, node in enumerate(gltf.nodes):
        print(f"Node {i}: {node.name}")
        if node.scale: print(f"  Scale: {node.scale}")
        if node.rotation: print(f"  Rotation: {node.rotation}")
        if node.translation: print(f"  Translation: {node.translation}")
        if node.mesh is not None:
            print(f"  Links to Mesh: {node.mesh}")

    for i, mesh in enumerate(gltf.meshes):
        print(f"Mesh {i}: {mesh.name}")
        if mesh.weights:
            print(f"  Weights: {mesh.weights}")
        for j, prim in enumerate(mesh.primitives):
            if prim.targets:
                print(f"  Primitive {j} has {len(prim.targets)} morph targets")

if __name__ == "__main__":
    path = "public/models/garments/atomic_jacket_morphed.glb"
    inspect_glb(path)

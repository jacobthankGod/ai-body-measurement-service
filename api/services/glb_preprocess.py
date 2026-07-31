"""
Backend: Pre-process GLB into a lightweight JSON for instant frontend loading.
Extracts geometry + compressed textures, serves as compact JSON.
"""
import json
import struct
import io
import os
import logging
from pathlib import Path
from PIL import Image

import pygltflib
import numpy as np

logger = logging.getLogger("KORRA_GLB_PREPROCESS")

GLB_PATH = Path(__file__).resolve().parent.parent.parent / "public" / "assets" / "agbada_cloth_model.glb"
CACHE_PATH = Path(__file__).resolve().parent.parent.parent / "public" / "assets" / "agbada_lightweight.json"
MAX_TEX = 512
JPEG_QUALITY = 70


def build_lightweight():
    """Read the 46MB GLB and export a lightweight JSON (~1-2MB) for instant loading."""
    if CACHE_PATH.exists() and CACHE_PATH.stat().st_mtime > GLB_PATH.stat().st_mtime:
        logger.info("Lightweight cache is fresh, skipping rebuild")
        return str(CACHE_PATH)

    logger.info(f"Building lightweight from {GLB_PATH}")
    gltf = pygltflib.GLTF2().load(str(GLB_PATH))
    blob = gltf.binary_blob()
    if blob is None:
        # External buffers
        blob = b""

    # Extract buffer view data
    bv_data = {}
    for i, bv in enumerate(gltf.bufferViews):
        offset = bv.byteOffset or 0
        end = offset + bv.byteLength
        bv_data[i] = blob[offset:end]

    # Process each mesh primitive
    meshes_out = []
    accessors = gltf.accessors
    buffer_views = gltf.bufferViews

    for mesh_idx, mesh in enumerate(gltf.meshes):
        for prim_idx, prim in enumerate(mesh.primitives):
            attrib = prim.attributes
            indices_acc = accessors[prim.indices] if prim.indices is not None else None
            pos_acc = accessors[attrib.POSITION] if hasattr(attrib, 'POSITION') and attrib.POSITION is not None else None
            normal_acc = accessors[attrib.NORMAL] if hasattr(attrib, 'NORMAL') and attrib.NORMAL is not None else None
            texcoord_acc = accessors[attrib.TEXCOORD_0] if hasattr(attrib, 'TEXCOORD_0') and attrib.TEXCOORD_0 is not None else None

            out = {}
            if indices_acc:
                bv = buffer_views[indices_acc.bufferView]
                raw = bv_data[indices_acc.bufferView]
                count = indices_acc.count
                if indices_acc.componentType == 5123:  # UNSIGNED_SHORT
                    arr = np.frombuffer(raw, dtype=np.uint16, count=count, offset=indices_acc.byteOffset or 0)
                elif indices_acc.componentType == 5125:  # UNSIGNED_INT
                    arr = np.frombuffer(raw, dtype=np.uint32, count=count, offset=indices_acc.byteOffset or 0)
                else:
                    arr = np.frombuffer(raw, dtype=np.uint16, count=count, offset=indices_acc.byteOffset or 0)
                out['indices'] = arr.tolist()

            if pos_acc:
                bv = buffer_views[pos_acc.bufferView]
                raw = bv_data[pos_acc.bufferView]
                count = pos_acc.count * 3
                arr = np.frombuffer(raw, dtype=np.float32, count=count, offset=pos_acc.byteOffset or 0)
                out['positions'] = arr.tolist()

            if normal_acc:
                bv = buffer_views[normal_acc.bufferView]
                raw = bv_data[normal_acc.bufferView]
                count = normal_acc.count * 3
                arr = np.frombuffer(raw, dtype=np.float32, count=count, offset=normal_acc.byteOffset or 0)
                out['normals'] = arr.tolist()

            if texcoord_acc:
                bv = buffer_views[texcoord_acc.bufferView]
                raw = bv_data[texcoord_acc.bufferView]
                count = texcoord_acc.count * 2
                arr = np.frombuffer(raw, dtype=np.float32, count=count, offset=texcoord_acc.byteOffset or 0)
                out['uvs'] = arr.tolist()

            # Material info
            if hasattr(prim, 'material') and prim.material is not None:
                out['material'] = prim.material
            else:
                out['material'] = None

            meshes_out.append(out)

    # Extract and compress textures
    textures_out = {}
    for img_idx, img in enumerate(gltf.images):
        if img.bufferView is None:
            continue
        raw = bv_data[img.bufferView]
        try:
            pil_img = Image.open(io.BytesIO(raw))
            w, h = pil_img.size

            # Resize
            if max(w, h) > MAX_TEX:
                ratio = MAX_TEX / max(w, h)
                pil_img = pil_img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

            # Convert to JPEG base64
            buf = io.BytesIO()
            if pil_img.mode in ('RGBA', 'PA', 'P'):
                # Check alpha
                if pil_img.mode == 'RGBA':
                    alpha = pil_img.getchannel('A')
                    if alpha.getextrema() == (255, 255):
                        pil_img = pil_img.convert('RGB')
                    else:
                        # Keep as PNG for transparency
                        pil_img.save(buf, format='PNG', optimize=True)
                        textures_out[img_idx] = 'data:image/png;base64,' + base64_encode(buf.getvalue())
                        continue
                else:
                    pil_img = pil_img.convert('RGB')

            pil_img.save(buf, format='JPEG', quality=JPEG_QUALITY, optimize=True)
            textures_out[img_idx] = 'data:image/jpeg;base64,' + base64_encode(buf.getvalue())
            logger.info(f"  Texture {img_idx}: {w}x{h} -> {pil_img.size[0]}x{pil_img.size[1]}, compressed")
        except Exception as e:
            logger.warning(f"  Texture {img_idx} failed: {e}")
            textures_out[img_idx] = None

    # Material -> texture mapping
    materials_out = {}
    for mat_idx, mat in enumerate(gltf.materials):
        mat_info = {}
        if hasattr(mat, 'pbrMetallicRoughness') and mat.pbrMetallicRoughness:
            pbr = mat.pbrMetallicRoughness
            if hasattr(pbr, 'baseColorTexture') and pbr.baseColorTexture is not None:
                tex = gltf.textures[pbr.baseColorTexture.index]
                mat_info['map'] = tex.source
            if hasattr(pbr, 'metallicRoughnessTexture') and pbr.metallicRoughnessTexture is not None:
                tex = gltf.textures[pbr.metallicRoughnessTexture.index]
                mat_info['metallicRoughnessMap'] = tex.source
        if hasattr(mat, 'normalTexture') and mat.normalTexture is not None:
            tex = gltf.textures[mat.normalTexture.index]
            mat_info['normalMap'] = tex.source
        if hasattr(mat, 'emissiveTexture') and mat.emissiveTexture is not None:
            tex = gltf.textures[mat.emissiveTexture.index]
            mat_info['emissiveMap'] = tex.source
        if hasattr(mat, 'occlusionTexture') and mat.occlusionTexture is not None:
            tex = gltf.textures[mat.occlusionTexture.index]
            mat_info['aoMap'] = tex.source

        # PBR values
        if hasattr(mat, 'pbrMetallicRoughness') and mat.pbrMetallicRoughness:
            pbr = mat.pbrMetallicRoughness
            if hasattr(pbr, 'baseColorFactor') and pbr.baseColorFactor is not None:
                mat_info['baseColorFactor'] = list(pbr.baseColorFactor)
            if hasattr(pbr, 'metallicFactor') and pbr.metallicFactor is not None:
                mat_info['metallicFactor'] = pbr.metallicFactor
            if hasattr(pbr, 'roughnessFactor') and pbr.roughnessFactor is not None:
                mat_info['roughnessFactor'] = pbr.roughnessFactor

        materials_out[mat_idx] = mat_info

    # Build output
    output = {
        'meshes': meshes_out,
        'textures': textures_out,
        'materials': materials_out,
    }

    with open(CACHE_PATH, 'w') as f:
        json.dump(output, f, separators=(',', ':'))

    file_size = os.path.getsize(CACHE_PATH)
    logger.info(f"Lightweight JSON written: {file_size / 1024:.1f} KB")
    return str(CACHE_PATH)


def base64_encode(data):
    import base64
    return base64.b64encode(data).decode('ascii')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    build_lightweight()

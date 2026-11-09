#!/usr/bin/env python3
"""Derive full shader-map manifests for HU 006.027.001 from the X20511I 007.030.001 maps.

The 17 mapped native shaders that differ between the two builds keep the same length and an
identical USSE program (inspect-sgx-shader.py prints the same decode); only the container
checksum and a compiler/version header field changed. So each entry keeps its reconstructed
GLSL and only its pinned native hash is updated to the 006 file.

usage: make-car006-shader-maps.py REPO_ROOT ROOTFS_006
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

repo, rootfs = Path(sys.argv[1]), Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("essl", repo / "tools/prepare-hmi-native-essl-map.py")
essl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(essl)
ro = rootfs / "opt/hmi/ID5/data/ro"
maps = repo / "tools/shaders/native-reconstructions"
for source_name, target_name in (("hmi-vertex-map-v67.json", "hmi-vertex-map-car006.json"),
                                 ("hmi-fragment-map-v112.json", "hmi-fragment-map-car006.json")):
    data = json.loads((maps / source_name).read_text())
    if data.get("schema") in essl.DELTA_BASE_SCHEMAS:
        data = essl.apply_map_delta(data, repo)
    changed = 0
    for entry in data["mappings"]:
        actual = hashlib.sha256((ro / entry["asset_path"]).read_bytes()).hexdigest()
        if entry.get("shader_sha256") and entry["shader_sha256"] != actual:
            entry["x20511i_shader_sha256"] = entry["shader_sha256"]
            entry["shader_sha256"] = actual
            changed += 1
    data["derived_from"] = source_name
    data["purpose"] = ("HU 006.027.001 (ID5_1811) copy of " + source_name +
                       "; same GLSL, native hashes re-pinned to the 006 shader files")
    (maps / target_name).write_text(json.dumps(data, indent=2) + "\n")
    print(f"{target_name}: {len(data['mappings'])} mappings, {changed} re-pinned")

#!/usr/bin/env python3
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

for name in ["iloveyou.usdz", "heart.usdz", "ufo.usdz"]:
    path = ROOT / "assets" / "models" / name
    print(f"=== Checking {name} ({path.stat().st_size} bytes) ===")
    assert path.exists(), f"Missing {name}"
    with zipfile.ZipFile(path, "r") as zf:
        names = zf.namelist()
        print(f"  Archive entries: {names}")
        assert "model.usda" in names, "model.usda missing in USDZ"
        data = zf.read("model.usda").decode("utf-8")
        assert data.startswith("#usda 1.0"), "Missing #usda 1.0 header"
        assert 'metersPerUnit = 1.0' in data
        assert 'upAxis = "Y"' in data
        mesh_count = data.count("def Mesh")
        mat_count = data.count("def Material")
        print(f"  Meshes: {mesh_count}")
        print(f"  Materials: {mat_count}")
        assert mesh_count > 0, "No meshes found"
        assert mat_count > 0, "No materials found"
    print(f"  PASS: {name} is structurally sound.")

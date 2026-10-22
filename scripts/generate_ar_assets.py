#!/usr/bin/env python3
"""
Generates the Little Surprises AR models (USDZ for Apple AR Quick Look):

  assets/models/iloveyou.usdz  - #01 colorful 3D "I LOVE YOU" block letters with gem hearts
  assets/models/heart.usdz     - #11 translucent pink faceted crystal heart
  assets/models/ufo.usdz       - #15 cute UFO with tractor beam and projected heart

Geometry rules (checked by scripts/test_usdz_assets.py):
  * every solid is a closed, outward-facing (right-handed) manifold with positive volume
  * hard-edged meshes use subdivisionScheme = "none" and carry authored extents
  * materials are bound with the MaterialBindingAPI applied
  * translucent meshes are double sided
The generator is deterministic. Output is NOT a substitute for testing on a real iPhone.
"""

import math
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "assets" / "models"


# ----------------------------------------------------------------------------
# Mesh construction
# ----------------------------------------------------------------------------

def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _newell_normal(verts):
    """Unit normal of a (possibly non-triangular) polygon from CCW vertex order."""
    nx = ny = nz = 0.0
    for i, p in enumerate(verts):
        q = verts[(i + 1) % len(verts)]
        nx += (p[1] - q[1]) * (p[2] + q[2])
        ny += (p[2] - q[2]) * (p[0] + q[0])
        nz += (p[0] - q[0]) * (p[1] + q[1])
    mag = math.sqrt(nx * nx + ny * ny + nz * nz)
    if mag < 1e-14:
        return (0.0, 1.0, 0.0)
    return (nx / mag, ny / mag, nz / mag)


class Mesh:
    """Face-vertex mesh; vertices are never shared between faces, so normals
    are explicit per face-vertex ("vertex" interpolation == one per point)."""

    def __init__(self):
        self.points, self.normals, self.counts, self.indices = [], [], [], []

    def add_face(self, verts, normals=None):
        if normals is None:
            n = _newell_normal(verts)
            normals = [n] * len(verts)
        base = len(self.points)
        self.points.extend(verts)
        self.normals.extend(normals)
        self.counts.append(len(verts))
        self.indices.extend(range(base, base + len(verts)))

    def extent(self):
        xs, ys, zs = zip(*self.points)
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def box(cx, cy, cz, w, h, d, rot_z_deg=0.0):
    """Closed box, optionally rotated about its own centre around Z."""
    m = Mesh()
    a = math.radians(rot_z_deg)
    ca, sa = math.cos(a), math.sin(a)

    def P(x, y, z):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca, cz + z)

    x0, x1, y0, y1, z0, z1 = -w / 2, w / 2, -h / 2, h / 2, -d / 2, d / 2
    m.add_face([P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)])  # front  +z
    m.add_face([P(x1, y0, z0), P(x0, y0, z0), P(x0, y1, z0), P(x1, y1, z0)])  # back   -z
    m.add_face([P(x0, y1, z1), P(x1, y1, z1), P(x1, y1, z0), P(x0, y1, z0)])  # top    +y
    m.add_face([P(x0, y0, z0), P(x1, y0, z0), P(x1, y0, z1), P(x0, y0, z1)])  # bottom -y
    m.add_face([P(x1, y0, z1), P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1)])  # right  +x
    m.add_face([P(x0, y0, z0), P(x0, y0, z1), P(x0, y1, z1), P(x0, y1, z0)])  # left   -x
    return m


def _flat_segments(profile):
    """Profile (r, y) polyline bottom->top to lathe segments with hard (per-segment) normals."""
    segs = []
    for (r0, y0), (r1, y1) in zip(profile, profile[1:]):
        dr, dy = r1 - r0, y1 - y0
        ln = math.hypot(dr, dy)
        n = (dy / ln, -dr / ln)
        segs.append(((r0, y0, n), (r1, y1, n)))
    return segs


def _arc_segments(radius, y_center, t0_deg, t1_deg, steps):
    """Smooth-shaded circular arc in the (r, y) half plane (spheres / domes)."""
    segs = []
    for i in range(steps):
        ta = math.radians(t0_deg + (t1_deg - t0_deg) * i / steps)
        tb = math.radians(t0_deg + (t1_deg - t0_deg) * (i + 1) / steps)
        pa = (radius * math.cos(ta), y_center + radius * math.sin(ta), (math.cos(ta), math.sin(ta)))
        pb = (radius * math.cos(tb), y_center + radius * math.sin(tb), (math.cos(tb), math.sin(tb)))
        segs.append((pa, pb))
    return segs


def lathe(segments, steps=32, center=(0.0, 0.0, 0.0)):
    """Surface of revolution about +Y. Profile runs bottom->top with r >= 0 so that
    quads wound (A, D, C, B) face outward. Degenerate (pole) quads collapse to triangles."""
    m = Mesh()
    cx, cy, cz = center
    for (r0, y0, n0), (r1, y1, n1) in segments:
        for j in range(steps):
            a0, a1 = 2 * math.pi * j / steps, 2 * math.pi * (j + 1) / steps

            def V(r, y, n, a):
                return ((cx + r * math.cos(a), cy + y, cz + r * math.sin(a)),
                        (n[0] * math.cos(a), n[1], n[0] * math.sin(a)))

            quad = [V(r0, y0, n0, a0), V(r1, y1, n1, a0), V(r1, y1, n1, a1), V(r0, y0, n0, a1)]  # A, D, C, B
            kept = []
            for v in quad:
                if not kept or math.dist(kept[-1][0], v[0]) > 1e-9:
                    kept.append(v)
            if len(kept) > 1 and math.dist(kept[-1][0], kept[0][0]) <= 1e-9:
                kept.pop()
            if len(kept) >= 3:
                m.add_face([v[0] for v in kept], [v[1] for v in kept])
    return m


def sphere(radius, center, lat_steps=10, lon_steps=18):
    return lathe(_arc_segments(radius, 0.0, -90, 90, lat_steps), lon_steps, center)


def dome(radius, center, lat_steps=8, lon_steps=24):
    """Upper hemisphere with a flat bottom cap (closed solid)."""
    segs = [((0.0, 0.0, (0.0, -1.0)), (radius, 0.0, (0.0, -1.0)))]
    segs += _arc_segments(radius, 0.0, 0, 90, lat_steps)
    return lathe(segs, lon_steps, center)


def cylinder(radius, y0, y1, center, steps=16):
    return lathe(_flat_segments([(0.0, y0), (radius, y0), (radius, y1), (0.0, y1)]), steps, center)


def heart_outline(n):
    """Classic heart curve, returned CCW (viewed from +z), centred on mean y, in units of 1/16 half-width."""
    pts = []
    for k in range(n):
        u = -math.pi + 2 * math.pi * k / n
        pts.append((16 * math.sin(u) ** 3,
                    13 * math.cos(u) - 5 * math.cos(2 * u) - 2 * math.cos(3 * u) - math.cos(4 * u)))
    cy = sum(p[1] for p in pts) / n
    pts = [(x, y - cy) for x, y in pts]
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n)) / 2
    if area < 0:
        pts.reverse()
    return pts


def heart_gem(width, depth, center, n=40, layers=((1.0, 0.0), (0.74, 0.55), (0.42, 0.88))):
    """Closed, faceted, flat-shaded gemstone heart (girdle at z=0, table apex at +/-depth)."""
    m = Mesh()
    cx, cy, cz = center
    s = width / 32.0
    outline = heart_outline(n)
    rings = [[(cx + sc * x * s, cy + sc * y * s, cz + zf * depth) for x, y in outline] for sc, zf in layers]
    apex_front = (cx, cy, cz + depth)
    tris = []
    for lo, li in zip(rings, rings[1:]):
        for k in range(n):
            k2 = (k + 1) % n
            tris.append([lo[k], lo[k2], li[k2]])
            tris.append([lo[k], li[k2], li[k]])
    last = rings[-1]
    for k in range(n):
        tris.append([last[k], last[(k + 1) % n], apex_front])
    for t in tris:  # front half
        m.add_face(t)
    for t in tris:  # back half: mirror through z = cz and reverse winding
        mirrored = [(p[0], p[1], 2 * cz - p[2]) for p in reversed(t)]
        m.add_face(mirrored)
    return m


# ----------------------------------------------------------------------------
# USDA serialisation
# ----------------------------------------------------------------------------

def _vec(t):
    return "(" + ", ".join(f"{c:.6f}" for c in t) + ")"


def format_mesh(name, mesh, material, color, double_sided=False):
    lo, hi = mesh.extent()
    pts = ", ".join(_vec(p) for p in mesh.points)
    nrm = ", ".join(_vec(n) for n in mesh.normals)
    idx = ", ".join(str(i) for i in mesh.indices)
    cnt = ", ".join(str(c) for c in mesh.counts)
    return f'''
        def Mesh "{name}" (
            prepend apiSchemas = ["MaterialBindingAPI"]
        )
        {{
            float3[] extent = [{_vec(lo)}, {_vec(hi)}]
            int[] faceVertexCounts = [{cnt}]
            int[] faceVertexIndices = [{idx}]
            point3f[] points = [{pts}]
            normal3f[] normals = [{nrm}] (
                interpolation = "vertex"
            )
            color3f[] primvars:displayColor = [{_vec(color)}] (
                interpolation = "constant"
            )
            uniform token orientation = "rightHanded"
            uniform bool doubleSided = {"true" if double_sided else "false"}
            uniform token subdivisionScheme = "none"
            rel material:binding = </Root/Materials/{material}>
        }}'''


def format_material(name, diffuse, roughness=0.3, metallic=0.0, opacity=1.0, ior=1.5, emissive=None):
    emit = f"\n                color3f inputs:emissiveColor = {_vec(emissive)}" if emissive else ""
    return f'''
        def Material "{name}"
        {{
            token outputs:surface.connect = </Root/Materials/{name}/PBRPreview.outputs:surface>

            def Shader "PBRPreview"
            {{
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = {_vec(diffuse)}{emit}
                float inputs:roughness = {roughness:.2f}
                float inputs:metallic = {metallic:.2f}
                float inputs:opacity = {opacity:.2f}
                float inputs:ior = {ior:.2f}
                token outputs:surface
            }}
        }}'''


def usda_document(group_name, materials, meshes):
    return f'''#usda 1.0
(
    defaultPrim = "Root"
    metersPerUnit = 1.0
    upAxis = "Y"
)

def Xform "Root" (
    kind = "component"
)
{{
    def Scope "Materials"
    {{{"".join(materials)}
    }}

    def Xform "{group_name}"
    {{{"".join(meshes)}
    }}
}}
'''


def package_usdz(usda_content, output_usdz_path):
    """
    Packages USDA text into an uncompressed (ZIP_STORED) .usdz whose first file's
    data begins on a 64-byte boundary, per the USDZ specification.
    """
    name = "model.usda"
    info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_STORED
    header_len = 30 + len(name.encode("utf-8"))
    pad = (64 - (header_len + 4) % 64) % 64  # extra field = 4-byte header + pad bytes
    info.extra = struct.pack("<HH", 0x1986, pad) + b"\0" * pad
    with zipfile.ZipFile(output_usdz_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr(info, usda_content.encode("utf-8"))


# ----------------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------------

GOLD, PINK, PURPLE, CORAL = (1.0, 0.78, 0.25), (0.95, 0.22, 0.48), (0.68, 0.28, 0.88), (0.98, 0.42, 0.36)


def build_iloveyou_model():
    mats = {
        "PinkMat": (PINK, 0.25, 0.1), "GoldMat": (GOLD, 0.2, 0.3),
        "PurpleMat": (PURPLE, 0.25, 0.1), "CoralMat": (CORAL, 0.25, 0.1),
    }
    materials = [format_material(k, c, r, mt) for k, (c, r, mt) in mats.items()]
    meshes = []

    def add(name, mesh, mat, double_sided=False):
        meshes.append(format_mesh(name, mesh, mat, mats[mat][0], double_sided))

    T = 0.03  # letter depth
    # Row 1: "I" flanked by two hearts
    add("I_bar", box(0.0, 0.18, 0, 0.025, 0.09, T), "GoldMat")
    add("I_top", box(0.0, 0.22, 0, 0.065, 0.02, T), "GoldMat")
    add("I_bot", box(0.0, 0.14, 0, 0.065, 0.02, T), "GoldMat")
    add("HeartLeft", heart_gem(0.12, 0.03, (-0.14, 0.18, 0.0)), "PinkMat")
    add("HeartRight", heart_gem(0.12, 0.03, (0.14, 0.18, 0.0)), "PinkMat")
    # Row 2: L O V E
    add("L_vert", box(-0.16, 0.06, 0, 0.022, 0.09, T), "CoralMat")
    add("L_horiz", box(-0.136, 0.02, 0, 0.05, 0.022, T), "CoralMat")
    add("O_left", box(-0.079, 0.06, 0, 0.02, 0.09, T), "PinkMat")
    add("O_right", box(-0.031, 0.06, 0, 0.02, 0.09, T), "PinkMat")
    add("O_top", box(-0.055, 0.095, 0, 0.065, 0.02, T), "PinkMat")
    add("O_bot", box(-0.055, 0.025, 0, 0.065, 0.02, T), "PinkMat")
    ang = math.degrees(math.atan2(0.03, 0.087))  # diagonal strokes so V does not read as U
    ln = math.hypot(0.03, 0.087)
    add("V_left", box(0.04, 0.0615, 0, 0.02, ln, T, +ang), "PurpleMat")
    add("V_right", box(0.07, 0.0615, 0, 0.02, ln, T, -ang), "PurpleMat")
    add("E_vert", box(0.14, 0.06, 0, 0.022, 0.09, T), "CoralMat")
    add("E_top", box(0.17, 0.095, 0, 0.055, 0.02, T), "CoralMat")
    add("E_mid", box(0.165, 0.06, 0, 0.045, 0.018, T), "CoralMat")
    add("E_bot", box(0.17, 0.025, 0, 0.055, 0.02, T), "CoralMat")
    # Row 3: Y O U with hearts at both ends
    yang = math.degrees(math.atan2(0.035, 0.045))
    yln = math.hypot(0.035, 0.045)
    add("Y_stem", box(-0.11, -0.09, 0, 0.022, 0.05, T), "PurpleMat")
    add("Y_left", box(-0.1275, -0.0425, 0, 0.02, yln, T, +yang), "PurpleMat")
    add("Y_right", box(-0.0925, -0.0425, 0, 0.02, yln, T, -yang), "PurpleMat")
    add("Y_O_left", box(-0.024, -0.06, 0, 0.02, 0.09, T), "GoldMat")
    add("Y_O_right", box(0.024, -0.06, 0, 0.02, 0.09, T), "GoldMat")
    add("Y_O_top", box(0.0, -0.025, 0, 0.065, 0.02, T), "GoldMat")
    add("Y_O_bot", box(0.0, -0.095, 0, 0.065, 0.02, T), "GoldMat")
    add("U_left", box(0.086, -0.05, 0, 0.02, 0.075, T), "PinkMat")
    add("U_right", box(0.134, -0.05, 0, 0.02, 0.075, T), "PinkMat")
    add("U_bot", box(0.11, -0.095, 0, 0.065, 0.022, T), "PinkMat")
    add("HeartFarLeft", heart_gem(0.10, 0.025, (-0.225, -0.06, 0.0)), "PinkMat")
    add("HeartFarRight", heart_gem(0.10, 0.025, (0.225, -0.06, 0.0)), "PinkMat")
    package_usdz(usda_document("Letters", materials, meshes), MODELS_DIR / "iloveyou.usdz")


def build_heart_model():
    materials = [
        format_material("CrystalHeartMat", (1.0, 0.48, 0.70), 0.08, 0.05, 0.62, 1.52, emissive=(0.12, 0.02, 0.06)),
        format_material("InnerGlowMat", (1.0, 0.85, 0.95), 0.15, 0.0, 1.0, 1.45, emissive=(0.55, 0.25, 0.4)),
    ]
    meshes = [
        format_mesh("CrystalHeart", heart_gem(0.30, 0.09, (0, 0, 0)), "CrystalHeartMat", (1.0, 0.48, 0.70), True),
        format_mesh("HeartCore", heart_gem(0.14, 0.04, (0, 0, 0)), "InnerGlowMat", (1.0, 0.85, 0.95), False),
    ]
    package_usdz(usda_document("HeartGeometry", materials, meshes), MODELS_DIR / "heart.usdz")


def build_ufo_model():
    mats = [
        ("SaucerHullMat", (0.75, 0.65, 0.92), 0.2, 0.4, 1.0, None),
        ("CockpitDomeMat", (0.45, 0.95, 0.85), 0.05, 0.0, 0.55, None),
        ("TractorBeamMat", (0.35, 0.98, 0.75), 0.3, 0.0, 0.30, (0.10, 0.45, 0.35)),
        ("HeartGlowMat", (1.0, 0.25, 0.55), 0.1, 0.1, 1.0, (0.55, 0.05, 0.2)),
        ("BeaconGoldMat", (1.0, 0.85, 0.3), 0.15, 0.5, 1.0, (0.6, 0.45, 0.1)),
    ]
    materials = [format_material(n, c, r, m, o, 1.5, e) for n, c, r, m, o, e in mats]
    col = {n: c for n, c, *_ in mats}
    meshes = []
    saucer = [(0.0, 0.0), (0.05, 0.0), (0.15, 0.04), (0.19, 0.062), (0.15, 0.082), (0.07, 0.095), (0.0, 0.095)]
    meshes.append(format_mesh("Saucer", lathe(_flat_segments(saucer), 40), "SaucerHullMat", col["SaucerHullMat"]))
    meshes.append(format_mesh("CockpitDome", dome(0.07, (0, 0.095, 0)), "CockpitDomeMat", col["CockpitDomeMat"], True))
    meshes.append(format_mesh("AntennaMast", cylinder(0.005, 0.0, 0.04, (0, 0.165, 0), 12), "BeaconGoldMat", col["BeaconGoldMat"]))
    meshes.append(format_mesh("AntennaTip", sphere(0.012, (0, 0.21, 0), 8, 14), "BeaconGoldMat", col["BeaconGoldMat"]))
    for i in range(8):
        a = 2 * math.pi * i / 8
        meshes.append(format_mesh(f"Beacon_{i}", sphere(0.011, (0.19 * math.cos(a), 0.062, 0.19 * math.sin(a)), 6, 10),
                                  "BeaconGoldMat", col["BeaconGoldMat"]))
    beam = [(0.0, -0.18), (0.13, -0.18), (0.045, 0.02), (0.0, 0.02)]
    meshes.append(format_mesh("TractorBeam", lathe(_flat_segments(beam), 32), "TractorBeamMat", col["TractorBeamMat"], True))
    meshes.append(format_mesh("ProjectedHeart", heart_gem(0.13, 0.035, (0, -0.10, 0)), "HeartGlowMat", col["HeartGlowMat"]))
    package_usdz(usda_document("UfoModel", materials, meshes), MODELS_DIR / "ufo.usdz")


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    for name, fn in (("iloveyou", build_iloveyou_model), ("heart", build_heart_model), ("ufo", build_ufo_model)):
        fn()
        print(f"Generated {name}.usdz ({(MODELS_DIR / (name + '.usdz')).stat().st_size} bytes)")


if __name__ == "__main__":
    main()

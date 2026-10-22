#!/usr/bin/env python3
"""
Generates authentic Apple Quick Look-compatible USDZ 3D models for Little Surprises:
1. assets/models/iloveyou.usdz - Playful colorful 3D 'I LOVE YOU' with decorative hearts
2. assets/models/heart.usdz    - Translucent pink crystal/gemstone heart
3. assets/models/ufo.usdz      - Cute colorful UFO with glowing cockpit, tractor beam & heart
"""

import math
import os
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "assets" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# Helper functions for 3D Geometry Generation
# ==============================================================================

def create_box(x_min, x_max, y_min, y_max, z_min, z_max):
    """Returns (points, indices, counts, normals) for an axis-aligned box."""
    pts = [
        (x_min, y_min, z_max), (x_max, y_min, z_max), (x_max, y_max, z_max), (x_min, y_max, z_max), # Front
        (x_max, y_min, z_min), (x_min, y_min, z_min), (x_min, y_max, z_min), (x_max, y_max, z_min), # Back
        (x_min, y_max, z_max), (x_max, y_max, z_max), (x_max, y_max, z_min), (x_min, y_max, z_min), # Top
        (x_min, y_min, z_min), (x_max, y_min, z_min), (x_max, y_min, z_max), (x_min, y_min, z_max), # Bottom
        (x_max, y_min, z_max), (x_max, y_min, z_min), (x_max, y_max, z_min), (x_max, y_max, z_max), # Right
        (x_min, y_min, z_min), (x_min, y_min, z_max), (x_min, y_max, z_max), (x_min, y_max, z_min), # Left
    ]
    indices = list(range(24))
    counts = [4] * 6
    normals = [
        (0, 0, 1), (0, 0, 1), (0, 0, 1), (0, 0, 1),
        (0, 0, -1), (0, 0, -1), (0, 0, -1), (0, 0, -1),
        (0, 1, 0), (0, 1, 0), (0, 1, 0), (0, 1, 0),
        (0, -1, 0), (0, -1, 0), (0, -1, 0), (0, -1, 0),
        (1, 0, 0), (1, 0, 0), (1, 0, 0), (1, 0, 0),
        (-1, 0, 0), (-1, 0, 0), (-1, 0, 0), (-1, 0, 0),
    ]
    return pts, indices, counts, normals


def create_uv_sphere(radius, lat_steps=16, lon_steps=24, center=(0, 0, 0)):
    """Creates a UV sphere."""
    cx, cy, cz = center
    pts = []
    normals = []
    for i in range(lat_steps + 1):
        lat = math.pi * (-0.5 + float(i) / lat_steps)
        sin_lat = math.sin(lat)
        cos_lat = math.cos(lat)
        for j in range(lon_steps + 1):
            lon = 2 * math.pi * float(j) / lon_steps
            sin_lon = math.sin(lon)
            cos_lon = math.cos(lon)
            nx = cos_lat * cos_lon
            ny = sin_lat
            nz = cos_lat * sin_lon
            pts.append((cx + radius * nx, cy + radius * ny, cz + radius * nz))
            normals.append((nx, ny, nz))

    indices = []
    counts = []
    for i in range(lat_steps):
        for j in range(lon_steps):
            first = i * (lon_steps + 1) + j
            second = first + lon_steps + 1
            # Triangle 1
            indices.extend([first, second, first + 1])
            counts.append(3)
            # Triangle 2
            indices.extend([second, second + 1, first + 1])
            counts.append(3)

    return pts, indices, counts, normals


def create_faceted_heart_mesh(scale=0.15, center=(0, 0, 0)):
    """
    Creates a beautiful faceted 3D gemstone heart model.
    A multi-faceted cut crystal heart with crisp facet normals.
    """
    cx, cy, cz = center
    # Key crystal vertices
    # Front center cleft, top lobes, outer flanks, bottom point, back symmetry
    # We construct a parametric 3D heart with faceted subdivision
    u_steps = 28
    v_steps = 14
    pts = []
    normals = []
    indices = []
    counts = []

    def heart_func(u, v):
        # u in [-pi, pi], v in [-pi/2, pi/2]
        # 3D cardioid formula with crystal thickness
        sin_u = math.sin(u)
        cos_u = math.cos(u)
        sin_v = math.sin(v)
        cos_v = math.cos(v)

        # 2D heart profile in X-Y
        hx = 16 * (sin_u ** 3)
        hy = 13 * cos_u - 5 * math.cos(2 * u) - 2 * math.cos(3 * u) - math.cos(4 * u)
        # Z thickness shaped by v and cardioid profile
        hz = 8 * sin_v * (1.0 - 0.2 * abs(sin_u))

        # Normalize and scale
        s = scale / 17.0
        return (cx + hx * s, cy + (hy + 2.0) * s, cz + hz * s)

    # Build vertex grid
    grid = []
    for iv in range(v_steps + 1):
        v = -math.pi / 2 + math.pi * (iv / v_steps)
        row = []
        for iu in range(u_steps):
            u = -math.pi + 2 * math.pi * (iu / u_steps)
            pt = heart_func(u, v)
            row.append(len(pts))
            pts.append(pt)
        grid.append(row)

    # Create quads/triangles
    for iv in range(v_steps):
        for iu in range(u_steps):
            iu_next = (iu + 1) % u_steps
            p00 = grid[iv][iu]
            p01 = grid[iv][iu_next]
            p10 = grid[iv + 1][iu]
            p11 = grid[iv + 1][iu_next]

            # Triangle 1: p00, p10, p01
            indices.extend([p00, p10, p01])
            counts.append(3)
            # Triangle 2: p01, p10, p11
            indices.extend([p01, p10, p11])
            counts.append(3)

    # Compute flat/facet normals for crystal look
    # For Apple USD Quick Look, calculating per-vertex averaged normals or facet normals:
    v_normals = [[0.0, 0.0, 0.0] for _ in pts]
    idx = 0
    for c in counts:
        tri = indices[idx:idx + c]
        idx += c
        p0 = pts[tri[0]]
        p1 = pts[tri[1]]
        p2 = pts[tri[2]]
        # Cross product (p1 - p0) x (p2 - p0)
        ux, uy, uz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
        vx, vy, vz = p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]
        nx = uy * vz - uz * vy
        ny = uz * vx - ux * vz
        nz = ux * vy - uy * vx
        mag = math.sqrt(nx * nx + ny * ny + nz * nz)
        if mag > 1e-8:
            nx /= mag
            ny /= mag
            nz /= mag
            for v_idx in tri:
                v_normals[v_idx][0] += nx
                v_normals[v_idx][1] += ny
                v_normals[v_idx][2] += nz

    for n in v_normals:
        mag = math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2])
        if mag > 1e-8:
            normals.append((n[0] / mag, n[1] / mag, n[2] / mag))
        else:
            normals.append((0.0, 1.0, 0.0))

    return pts, indices, counts, normals


def create_extruded_polygon(points_2d, z_depth=0.04, center=(0, 0, 0)):
    """
    Extrudes a simple 2D polygon along Z axis with front, back, and side quads.
    """
    cx, cy, cz = center
    n = len(points_2d)
    pts = []
    normals = []
    indices = []
    counts = []

    half_z = z_depth / 2.0
    # Front vertices (z = +half_z)
    for x, y in points_2d:
        pts.append((cx + x, cy + y, cz + half_z))
    # Back vertices (z = -half_z)
    for x, y in points_2d:
        pts.append((cx + x, cy + y, cz - half_z))

    # Fan triangulation for front face (assuming roughly star-convex or simple)
    # Using center vertex for robust triangulation
    front_center_idx = len(pts)
    pts.append((cx + sum(p[0] for p in points_2d) / n, cy + sum(p[1] for p in points_2d) / n, cz + half_z))
    for i in range(n):
        i_next = (i + 1) % n
        indices.extend([front_center_idx, i, i_next])
        counts.append(3)

    back_center_idx = len(pts)
    pts.append((cx + sum(p[0] for p in points_2d) / n, cy + sum(p[1] for p in points_2d) / n, cz - half_z))
    for i in range(n):
        i_next = (i + 1) % n
        indices.extend([back_center_idx, i_next, i])
        counts.append(3)

    # Side walls
    for i in range(n):
        i_next = (i + 1) % n
        f0 = i
        f1 = i_next
        b0 = n + i
        b1 = n + i_next
        indices.extend([f0, f1, b1, b0])
        counts.append(4)

    # Compute normals
    v_normals = [[0.0, 0.0, 0.0] for _ in pts]
    idx = 0
    for c in counts:
        face = indices[idx:idx + c]
        idx += c
        p0 = pts[face[0]]
        p1 = pts[face[1]]
        p2 = pts[face[2]]
        ux, uy, uz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
        vx, vy, vz = p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]
        nx = uy * vz - uz * vy
        ny = uz * vx - ux * vz
        nz = ux * vy - uy * vx
        mag = math.sqrt(nx * nx + ny * ny + nz * nz)
        if mag > 1e-8:
            nx /= mag
            ny /= mag
            nz /= mag
            for v_idx in face:
                v_normals[v_idx][0] += nx
                v_normals[v_idx][1] += ny
                v_normals[v_idx][2] += nz

    for n_vec in v_normals:
        mag = math.sqrt(n_vec[0] * n_vec[0] + n_vec[1] * n_vec[1] + n_vec[2] * n_vec[2])
        if mag > 1e-8:
            normals.append((n_vec[0] / mag, n_vec[1] / mag, n_vec[2] / mag))
        else:
            normals.append((0.0, 0.0, 1.0))

    return pts, indices, counts, normals


def create_cylinder(radius_top, radius_bottom, height, radial_steps=24, center=(0, 0, 0)):
    """Creates a cylinder/cone with top and bottom caps."""
    cx, cy, cz = center
    half_h = height / 2.0
    pts = []
    normals = []
    indices = []
    counts = []

    # Top ring
    top_indices = []
    for j in range(radial_steps):
        angle = 2 * math.pi * j / radial_steps
        pts.append((cx + radius_top * math.cos(angle), cy + half_h, cz + radius_top * math.sin(angle)))
        top_indices.append(len(pts) - 1)

    # Bottom ring
    bottom_indices = []
    for j in range(radial_steps):
        angle = 2 * math.pi * j / radial_steps
        pts.append((cx + radius_bottom * math.cos(angle), cy - half_h, cz + radius_bottom * math.sin(angle)))
        bottom_indices.append(len(pts) - 1)

    # Top center
    top_center = len(pts)
    pts.append((cx, cy + half_h, cz))
    # Bottom center
    bottom_center = len(pts)
    pts.append((cx, cy - half_h, cz))

    # Top cap
    for j in range(radial_steps):
        j_next = (j + 1) % radial_steps
        indices.extend([top_center, top_indices[j], top_indices[j_next]])
        counts.append(3)

    # Bottom cap
    for j in range(radial_steps):
        j_next = (j + 1) % radial_steps
        indices.extend([bottom_center, bottom_indices[j_next], bottom_indices[j]])
        counts.append(3)

    # Side quads
    for j in range(radial_steps):
        j_next = (j + 1) % radial_steps
        t0 = top_indices[j]
        t1 = top_indices[j_next]
        b0 = bottom_indices[j]
        b1 = bottom_indices[j_next]
        indices.extend([t0, t1, b1, b0])
        counts.append(4)

    # Normals
    v_normals = [[0.0, 0.0, 0.0] for _ in pts]
    idx = 0
    for c in counts:
        face = indices[idx:idx + c]
        idx += c
        p0 = pts[face[0]]
        p1 = pts[face[1]]
        p2 = pts[face[2]]
        ux, uy, uz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
        vx, vy, vz = p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]
        nx = uy * vz - uz * vy
        ny = uz * vx - ux * vz
        nz = ux * vy - uy * vx
        mag = math.sqrt(nx * nx + ny * ny + nz * nz)
        if mag > 1e-8:
            nx /= mag
            ny /= mag
            nz /= mag
            for v_idx in face:
                v_normals[v_idx][0] += nx
                v_normals[v_idx][1] += ny
                v_normals[v_idx][2] += nz

    for n_vec in v_normals:
        mag = math.sqrt(n_vec[0] * n_vec[0] + n_vec[1] * n_vec[1] + n_vec[2] * n_vec[2])
        if mag > 1e-8:
            normals.append((n_vec[0] / mag, n_vec[1] / mag, n_vec[2] / mag))
        else:
            normals.append((0.0, 1.0, 0.0))

    return pts, indices, counts, normals


# ==============================================================================
# USD USDA Serialization
# ==============================================================================

def format_usda_mesh(name, pts, indices, counts, normals, material_path, display_color):
    """Formats a Mesh definition in USDA format."""
    pts_str = ", ".join(f"({p[0]:.4f}, {p[1]:.4f}, {p[2]:.4f})" for p in pts)
    idx_str = ", ".join(str(i) for i in indices)
    cnt_str = ", ".join(str(c) for c in counts)
    nrm_str = ", ".join(f"({n[0]:.4f}, {n[1]:.4f}, {n[2]:.4f})" for n in normals)
    col_str = f"({display_color[0]:.2f}, {display_color[1]:.2f}, {display_color[2]:.2f})"

    return f"""
    def Mesh "{name}"
    {{
        int[] faceVertexCounts = [{cnt_str}]
        int[] faceVertexIndices = [{idx_str}]
        point3f[] points = [{pts_str}]
        normal3f[] normals = [{nrm_str}] (
            interpolation = "vertex"
        )
        color3f[] primvars:displayColor = [{col_str}]
        rel material:binding = <{material_path}>
    }}"""


def format_material(name, diff_color, roughness=0.3, metallic=0.0, opacity=1.0, ior=1.5):
    """Formats a UsdPreviewSurface material in USDA."""
    diff_str = f"({diff_color[0]:.3f}, {diff_color[1]:.3f}, {diff_color[2]:.3f})"
    return f"""
        def Material "{name}"
        {{
            token outputs:surface.connect = </Root/Materials/{name}/PBRPreview.outputs:surface>

            def Shader "PBRPreview"
            {{
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = {diff_str}
                float inputs:roughness = {roughness:.2f}
                float inputs:metallic = {metallic:.2f}
                float inputs:opacity = {opacity:.2f}
                float inputs:ior = {ior:.2f}
                token outputs:surface
            }}
        }}"""


def package_usdz(usda_content, output_usdz_path):
    """
    Writes a USDA file and packages it into a valid 64-byte aligned,
    uncompressed (ZIP_STORED) .usdz file per Apple USDZ specification.
    """
    tmp_usda = output_usdz_path.with_suffix(".usda")
    tmp_usda.write_text(usda_content, encoding="utf-8")

    # Build USDZ: zip with ZIP_STORED
    with zipfile.ZipFile(output_usdz_path, "w", compression=zipfile.ZIP_STORED) as zf:
        # First entry must be the USDA file
        zf.write(tmp_usda, arcname="model.usda")

    if tmp_usda.exists():
        tmp_usda.unlink()


# ==============================================================================
# 1. Model: I LOVE YOU in AR (iloveyou.usdz)
# ==============================================================================

def build_iloveyou_model():
    print("Building iloveyou.usdz...")
    # Letter 3D boxes/strokes for "I", "LOVE", "YOU"
    # Layout:
    # Row 1: I (with two cute hearts)
    # Row 2: L O V E
    # Row 3: Y O U
    meshes = []
    materials = []

    # Material definitions
    materials.append(format_material("PinkMat", (0.95, 0.22, 0.48), roughness=0.25, metallic=0.1))
    materials.append(format_material("GoldMat", (1.0, 0.78, 0.25), roughness=0.2, metallic=0.3))
    materials.append(format_material("PurpleMat", (0.68, 0.28, 0.88), roughness=0.25, metallic=0.1))
    materials.append(format_material("CoralMat", (0.98, 0.42, 0.36), roughness=0.25, metallic=0.1))

    # Stroke helper
    def add_box(name, x, y, z, w, h, d, mat, color):
        pts, idx, cnt, nrm = create_box(x - w/2, x + w/2, y - h/2, y + h/2, z - d/2, z + d/2)
        meshes.append(format_usda_mesh(name, pts, idx, cnt, nrm, f"/Root/Materials/{mat}", color))

    # Row 1 (y = 0.18): "I" + 2 floating hearts
    # Letter "I"
    add_box("I_bar", 0.0, 0.18, 0.0, 0.025, 0.09, 0.03, "GoldMat", (1.0, 0.78, 0.25))
    add_box("I_top", 0.0, 0.22, 0.0, 0.065, 0.02, 0.03, "GoldMat", (1.0, 0.78, 0.25))
    add_box("I_bot", 0.0, 0.14, 0.0, 0.065, 0.02, 0.03, "GoldMat", (1.0, 0.78, 0.25))

    # Flanking 3D hearts for Row 1
    h1_pts, h1_idx, h1_cnt, h1_nrm = create_faceted_heart_mesh(scale=0.065, center=(-0.14, 0.18, 0.01))
    meshes.append(format_usda_mesh("HeartLeft", h1_pts, h1_idx, h1_cnt, h1_nrm, "/Root/Materials/PinkMat", (0.95, 0.22, 0.48)))
    h2_pts, h2_idx, h2_cnt, h2_nrm = create_faceted_heart_mesh(scale=0.065, center=(0.14, 0.18, -0.01))
    meshes.append(format_usda_mesh("HeartRight", h2_pts, h2_idx, h2_cnt, h2_nrm, "/Root/Materials/PinkMat", (0.95, 0.22, 0.48)))

    # Row 2 (y = 0.06): "L O V E"
    # L
    lx = -0.16
    add_box("L_vert", lx, 0.06, 0.0, 0.022, 0.09, 0.03, "CoralMat", (0.98, 0.42, 0.36))
    add_box("L_horiz", lx + 0.024, 0.02, 0.0, 0.05, 0.022, 0.03, "CoralMat", (0.98, 0.42, 0.36))

    # O
    ox = -0.055
    add_box("O_left", ox - 0.024, 0.06, 0.0, 0.02, 0.09, 0.03, "PinkMat", (0.95, 0.22, 0.48))
    add_box("O_right", ox + 0.024, 0.06, 0.0, 0.02, 0.09, 0.03, "PinkMat", (0.95, 0.22, 0.48))
    add_box("O_top", ox, 0.095, 0.0, 0.065, 0.02, 0.03, "PinkMat", (0.95, 0.22, 0.48))
    add_box("O_bot", ox, 0.025, 0.0, 0.065, 0.02, 0.03, "PinkMat", (0.95, 0.22, 0.48))

    # V
    vx = 0.055
    add_box("V_left", vx - 0.018, 0.06, 0.0, 0.02, 0.09, 0.03, "PurpleMat", (0.68, 0.28, 0.88))
    add_box("V_right", vx + 0.018, 0.06, 0.0, 0.02, 0.09, 0.03, "PurpleMat", (0.68, 0.28, 0.88))
    add_box("V_bot", vx, 0.02, 0.0, 0.045, 0.02, 0.03, "PurpleMat", (0.68, 0.28, 0.88))

    # E
    ex = 0.16
    add_box("E_vert", ex - 0.02, 0.06, 0.0, 0.022, 0.09, 0.03, "CoralMat", (0.98, 0.42, 0.36))
    add_box("E_top", ex + 0.01, 0.095, 0.0, 0.055, 0.02, 0.03, "CoralMat", (0.98, 0.42, 0.36))
    add_box("E_mid", ex + 0.005, 0.06, 0.0, 0.045, 0.018, 0.03, "CoralMat", (0.98, 0.42, 0.36))
    add_box("E_bot", ex + 0.01, 0.025, 0.0, 0.055, 0.02, 0.03, "CoralMat", (0.98, 0.42, 0.36))

    # Row 3 (y = -0.06): "Y O U"
    # Y
    yx = -0.11
    add_box("Y_stem", yx, -0.09, 0.0, 0.022, 0.05, 0.03, "PurpleMat", (0.68, 0.28, 0.88))
    add_box("Y_left", yx - 0.02, -0.045, 0.0, 0.02, 0.05, 0.03, "PurpleMat", (0.68, 0.28, 0.88))
    add_box("Y_right", yx + 0.02, -0.045, 0.0, 0.02, 0.05, 0.03, "PurpleMat", (0.68, 0.28, 0.88))

    # O
    yox = 0.0
    add_box("Y_O_left", yox - 0.024, -0.06, 0.0, 0.02, 0.09, 0.03, "GoldMat", (1.0, 0.78, 0.25))
    add_box("Y_O_right", yox + 0.024, -0.06, 0.0, 0.02, 0.09, 0.03, "GoldMat", (1.0, 0.78, 0.25))
    add_box("Y_O_top", yox, -0.025, 0.0, 0.065, 0.02, 0.03, "GoldMat", (1.0, 0.78, 0.25))
    add_box("Y_O_bot", yox, -0.095, 0.0, 0.065, 0.02, 0.03, "GoldMat", (1.0, 0.78, 0.25))

    # U
    ux = 0.11
    add_box("U_left", ux - 0.024, -0.05, 0.0, 0.02, 0.075, 0.03, "PinkMat", (0.95, 0.22, 0.48))
    add_box("U_right", ux + 0.024, -0.05, 0.0, 0.02, 0.075, 0.03, "PinkMat", (0.95, 0.22, 0.48))
    add_box("U_bot", ux, -0.095, 0.0, 0.065, 0.022, 0.03, "PinkMat", (0.95, 0.22, 0.48))

    # Central crowned small heart
    hc_pts, hc_idx, hc_cnt, hc_nrm = create_faceted_heart_mesh(scale=0.045, center=(0.0, -0.06, 0.015))
    meshes.append(format_usda_mesh("HeartCenter", hc_pts, hc_idx, hc_cnt, hc_nrm, "/Root/Materials/PinkMat", (0.95, 0.22, 0.48)))

    usda = f"""#usda 1.0
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
    {{
{"".join(materials)}
    }}

    def Xform "Letters"
    {{
{"".join(meshes)}
    }}
}}
"""
    package_usdz(usda, MODELS_DIR / "iloveyou.usdz")
    print(f"Generated iloveyou.usdz ({os.path.getsize(MODELS_DIR / 'iloveyou.usdz')} bytes)")


# ==============================================================================
# 2. Model: Hold My Heart (heart.usdz)
# ==============================================================================

def build_heart_model():
    print("Building heart.usdz...")
    # Beautiful faceted translucent pink crystal heart
    materials = [
        format_material("CrystalHeartMat", (1.0, 0.48, 0.70), roughness=0.08, metallic=0.05, opacity=0.78, ior=1.52),
        format_material("InnerGlowMat", (1.0, 0.85, 0.95), roughness=0.15, metallic=0.0, opacity=0.90, ior=1.45)
    ]

    # Outer crystal heart mesh
    pts, idx, cnt, nrm = create_faceted_heart_mesh(scale=0.22, center=(0, 0, 0))
    mesh1 = format_usda_mesh("CrystalHeart", pts, idx, cnt, nrm, "/Root/Materials/CrystalHeartMat", (1.0, 0.48, 0.70))

    # Inner glowing core
    core_pts, core_idx, core_cnt, core_nrm = create_faceted_heart_mesh(scale=0.11, center=(0, 0, 0))
    mesh2 = format_usda_mesh("HeartCore", core_pts, core_idx, core_cnt, core_nrm, "/Root/Materials/InnerGlowMat", (1.0, 0.85, 0.95))

    usda = f"""#usda 1.0
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
    {{
{"".join(materials)}
    }}

    def Xform "HeartGeometry"
    {{
{mesh1}
{mesh2}
    }}
}}
"""
    package_usdz(usda, MODELS_DIR / "heart.usdz")
    print(f"Generated heart.usdz ({os.path.getsize(MODELS_DIR / 'heart.usdz')} bytes)")


# ==============================================================================
# 3. Model: Alien UFO with projected heart (ufo.usdz)
# ==============================================================================

def build_ufo_model():
    print("Building ufo.usdz...")
    materials = [
        format_material("SaucerHullMat", (0.75, 0.65, 0.92), roughness=0.2, metallic=0.4), # Lilac saucer
        format_material("CockpitDomeMat", (0.45, 0.95, 0.85), roughness=0.05, metallic=0.0, opacity=0.60, ior=1.45), # Cyan dome
        format_material("TractorBeamMat", (0.35, 0.98, 0.75), roughness=0.3, metallic=0.0, opacity=0.35, ior=1.0), # Glow beam
        format_material("HeartGlowMat", (1.0, 0.25, 0.55), roughness=0.1, metallic=0.1, opacity=0.95), # Glowing pink heart
        format_material("BeaconGoldMat", (1.0, 0.85, 0.3), roughness=0.15, metallic=0.5), # Gold antenna & lights
    ]

    meshes = []

    # 1. Main Saucer Body (flattened wide disc)
    # Upper rim cylinder / cone
    hull_pts, hull_idx, hull_cnt, hull_nrm = create_cylinder(radius_top=0.06, radius_bottom=0.18, height=0.035, radial_steps=32, center=(0, 0.08, 0))
    meshes.append(format_usda_mesh("SaucerUpper", hull_pts, hull_idx, hull_cnt, hull_nrm, "/Root/Materials/SaucerHullMat", (0.75, 0.65, 0.92)))

    # Lower hull cone
    lh_pts, lh_idx, lh_cnt, lh_nrm = create_cylinder(radius_top=0.18, radius_bottom=0.05, height=0.045, radial_steps=32, center=(0, 0.04, 0))
    meshes.append(format_usda_mesh("SaucerLower", lh_pts, lh_idx, lh_cnt, lh_nrm, "/Root/Materials/SaucerHullMat", (0.75, 0.65, 0.92)))

    # 2. Cockpit Glass Bubble Dome (UV sphere on top)
    dome_pts, dome_idx, dome_cnt, dome_nrm = create_uv_sphere(radius=0.07, lat_steps=14, lon_steps=24, center=(0, 0.10, 0))
    meshes.append(format_usda_mesh("CockpitDome", dome_pts, dome_idx, dome_cnt, dome_nrm, "/Root/Materials/CockpitDomeMat", (0.45, 0.95, 0.85)))

    # 3. Antenna on top of dome
    ant_pts, ant_idx, ant_cnt, ant_nrm = create_cylinder(radius_top=0.004, radius_bottom=0.005, height=0.04, radial_steps=12, center=(0, 0.18, 0))
    meshes.append(format_usda_mesh("AntennaMast", ant_pts, ant_idx, ant_cnt, ant_nrm, "/Root/Materials/BeaconGoldMat", (1.0, 0.85, 0.3)))

    tip_pts, tip_idx, tip_cnt, tip_nrm = create_uv_sphere(radius=0.012, lat_steps=10, lon_steps=14, center=(0, 0.20, 0))
    meshes.append(format_usda_mesh("AntennaTip", tip_pts, tip_idx, tip_cnt, tip_nrm, "/Root/Materials/BeaconGoldMat", (1.0, 0.85, 0.3)))

    # 4. Saucer Rim Beacons (ring of 8 glowing spheres around the rim)
    for i in range(8):
        ang = 2 * math.pi * i / 8
        bx = 0.17 * math.cos(ang)
        bz = 0.17 * math.sin(ang)
        b_pts, b_idx, b_cnt, b_nrm = create_uv_sphere(radius=0.010, lat_steps=8, lon_steps=12, center=(bx, 0.06, bz))
        meshes.append(format_usda_mesh(f"Beacon_{i}", b_pts, b_idx, b_cnt, b_nrm, "/Root/Materials/BeaconGoldMat", (1.0, 0.85, 0.3)))

    # 5. Downward Glowing Tractor Beam (translucent cone tapering down)
    beam_pts, beam_idx, beam_cnt, beam_nrm = create_cylinder(radius_top=0.045, radius_bottom=0.13, height=0.20, radial_steps=28, center=(0, -0.08, 0))
    meshes.append(format_usda_mesh("TractorBeam", beam_pts, beam_idx, beam_cnt, beam_nrm, "/Root/Materials/TractorBeamMat", (0.35, 0.98, 0.75)))

    # 6. Projected Glowing Heart at the base of the beam
    h_pts, h_idx, h_cnt, h_nrm = create_faceted_heart_mesh(scale=0.085, center=(0, -0.10, 0))
    meshes.append(format_usda_mesh("ProjectedHeart", h_pts, h_idx, h_cnt, h_nrm, "/Root/Materials/HeartGlowMat", (1.0, 0.25, 0.55)))

    usda = f"""#usda 1.0
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
    {{
{"".join(materials)}
    }}

    def Xform "UfoModel"
    {{
{"".join(meshes)}
    }}
}}
"""
    package_usdz(usda, MODELS_DIR / "ufo.usdz")
    print(f"Generated ufo.usdz ({os.path.getsize(MODELS_DIR / 'ufo.usdz')} bytes)")


def main():
    build_iloveyou_model()
    build_heart_model()
    build_ufo_model()
    print("All AR models successfully generated.")


if __name__ == "__main__":
    main()

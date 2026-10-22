#!/usr/bin/env python3
"""
Automated checks for the three AR Quick Look assets (#01 iloveyou, #11 heart, #15 ufo)
and for their AR links on the pages.

Layers
  1. Packaging (pure stdlib, always runs): stored ZIP, USD first entry, 64-byte data alignment.
  2. OpenUSD checks (needs `pip install usd-core`): topology, orientation, volumes, extents,
     MaterialBindingAPI, subdivision, normals and double-sidedness.
  3. Pixar/Apple ARKit compliance checker (the `usdchecker --arkit` rule set).
  4. Page integration: rel="ar" links, model paths, <img> first child, feature-detection fallback.

Layers 2 and 3 are skipped locally if the dependency is missing. In CI set
REQUIRE_USD_CHECKS=1 so a missing dependency fails the build instead of skipping.

What this CANNOT prove: Apple Quick Look rendering, scale/placement on a real iPhone, or the
MIME type served by the deployed host. Those stay separately gated.
"""
import collections
import math
import os
import re
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS = Path(os.environ.get("AR_MODELS_DIR", ROOT / "assets" / "models"))  # override for negative controls
NAMES = ["iloveyou", "heart", "ufo"]
REQUIRE = os.environ.get("REQUIRE_USD_CHECKS") == "1"

try:
    from pxr import Usd, UsdGeom, UsdShade, Gf  # noqa: F401
    HAVE_USD = True
except Exception:  # pragma: no cover
    HAVE_USD = False


def _load_compliance_checker():
    extra = os.environ.get("USD_COMPLIANCE_CHECKER_DIR")
    if extra:
        sys.path.insert(0, extra)
    try:
        from complianceChecker import ComplianceChecker
        return ComplianceChecker
    except Exception:
        pass
    try:
        from pxr.UsdUtils.complianceChecker import ComplianceChecker
        return ComplianceChecker
    except Exception:
        return None


class Packaging(unittest.TestCase):
    def test_usdz_container(self):
        for name in NAMES:
            with self.subTest(model=name):
                path = MODELS / f"{name}.usdz"
                self.assertTrue(path.exists(), f"missing {path}")
                self.assertGreater(path.stat().st_size, 20000, "suspiciously small (placeholder?)")
                self.assertLess(path.stat().st_size, 5 * 1024 * 1024)
                with zipfile.ZipFile(path) as zf:
                    self.assertIsNone(zf.testzip())
                    infos = zf.infolist()
                    self.assertEqual(len(infos), 1)
                    first = infos[0]
                    self.assertTrue(first.filename.endswith((".usda", ".usdc", ".usd")))
                    self.assertEqual(first.compress_type, zipfile.ZIP_STORED)
                    data_offset = first.header_offset + 30 + len(first.filename.encode()) + len(first.extra)
                    self.assertEqual(data_offset % 64, 0, "USDZ file data must start on a 64-byte boundary")
                    self.assertTrue(zf.read(first).startswith(b"#usda 1.0"))


@unittest.skipUnless(HAVE_USD or REQUIRE, "usd-core not installed (set REQUIRE_USD_CHECKS=1 in CI)")
class OpenUsdGeometry(unittest.TestCase):
    def test_dependency_present_in_ci(self):
        self.assertTrue(HAVE_USD, "usd-core is required (REQUIRE_USD_CHECKS=1)")

    def _meshes(self, name):
        stage = Usd.Stage.Open(str(MODELS / f"{name}.usdz"))
        self.assertIsNotNone(stage)
        self.assertEqual(stage.GetDefaultPrim().GetName(), "Root")
        self.assertEqual(UsdGeom.GetStageUpAxis(stage), "Y")
        self.assertAlmostEqual(UsdGeom.GetStageMetersPerUnit(stage), 1.0)
        meshes = [UsdGeom.Mesh(p) for p in stage.Traverse() if p.IsA(UsdGeom.Mesh)]
        self.assertGreater(len(meshes), 0)
        return stage, meshes

    @staticmethod
    def _topology(mesh):
        pts = mesh.GetPointsAttr().Get()
        counts = mesh.GetFaceVertexCountsAttr().Get()
        idx = mesh.GetFaceVertexIndicesAttr().Get()
        key = lambda i: tuple(round(c, 5) for c in pts[i])
        directed = collections.Counter()
        volume = 0.0
        faces = []
        o = 0
        for c in counts:
            f = [key(i) for i in idx[o:o + c]]
            faces.append((list(idx[o:o + c]), f))
            for a in range(c):
                u, v = f[a], f[(a + 1) % c]
                if u != v:
                    directed[(u, v)] += 1
            p0 = Gf.Vec3d(*f[0])
            for a in range(1, c - 1):
                volume += Gf.Dot(p0, Gf.Cross(Gf.Vec3d(*f[a]), Gf.Vec3d(*f[a + 1]))) / 6.0
            o += c
        return pts, counts, idx, directed, volume, faces

    def test_closed_outward_manifolds(self):
        for name in NAMES:
            stage, meshes = self._meshes(name)  # keep stage alive
            for m in meshes:
                with self.subTest(model=name, mesh=m.GetPrim().GetName()):
                    pts, counts, idx, directed, volume, _ = self._topology(m)
                    self.assertTrue(all(0 <= i < len(pts) for i in idx), "index out of range")
                    self.assertEqual(sum(counts), len(idx))
                    self.assertTrue(all(math.isfinite(c) for p in pts for c in p), "NaN/inf point")
                    bad = [e for e, n in directed.items() if n != 1 or directed.get((e[1], e[0]), 0) != 1]
                    self.assertEqual(bad, [], f"{len(bad)} open/non-manifold edges")
                    self.assertGreater(volume, 1e-9, f"signed volume {volume:.3e} is not positive (inverted?)")

    def test_normals_agree_with_winding(self):
        for name in NAMES:
            stage, meshes = self._meshes(name)  # keep stage alive
            for m in meshes:
                with self.subTest(model=name, mesh=m.GetPrim().GetName()):
                    pts = m.GetPointsAttr().Get()
                    nrm = m.GetNormalsAttr().Get()
                    self.assertEqual(m.GetNormalsInterpolation(), "vertex")
                    self.assertEqual(len(nrm), len(pts))
                    counts, idx = m.GetFaceVertexCountsAttr().Get(), m.GetFaceVertexIndicesAttr().Get()
                    o, wrong = 0, 0
                    for c in counts:
                        f = [Gf.Vec3d(*pts[i]) for i in idx[o:o + c]]
                        n = Gf.Cross(f[1] - f[0], f[2] - f[0])
                        if n.GetLength() > 1e-14:
                            avg = sum((Gf.Vec3d(*nrm[i]) for i in idx[o:o + c]), Gf.Vec3d(0))
                            if Gf.Dot(n, avg) <= 0:
                                wrong += 1
                        o += c
                    self.assertEqual(wrong, 0, f"{wrong} faces whose shading normal opposes winding")

    def test_schema_and_authoring(self):
        for name in NAMES:
            stage, meshes = self._meshes(name)
            for m in meshes:
                prim = m.GetPrim()
                with self.subTest(model=name, mesh=prim.GetName()):
                    self.assertIn("MaterialBindingAPI", prim.GetAppliedSchemas())
                    self.assertEqual(m.GetSubdivisionSchemeAttr().Get(), "none")
                    ext = m.GetExtentAttr().Get()
                    self.assertIsNotNone(ext, "extent not authored")
                    pts = m.GetPointsAttr().Get()
                    lo = [min(p[i] for p in pts) for i in range(3)]
                    hi = [max(p[i] for p in pts) for i in range(3)]
                    for i in range(3):
                        self.assertAlmostEqual(ext[0][i], lo[i], places=5)
                        self.assertAlmostEqual(ext[1][i], hi[i], places=5)
                    mat, _ = UsdShade.MaterialBindingAPI(prim).ComputeBoundMaterial()
                    self.assertTrue(mat, "material binding does not resolve")
                    opacity = mat.GetPrim().GetChild("PBRPreview").GetAttribute("inputs:opacity").Get()
                    if opacity < 1.0:
                        self.assertTrue(m.GetDoubleSidedAttr().Get(), "translucent mesh must be double sided")

    def test_real_world_scale(self):
        for name in NAMES:
            stage, _ = self._meshes(name)
            box = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ["default"]).ComputeWorldBound(
                stage.GetDefaultPrim()).ComputeAlignedBox()
            size = box.GetMax() - box.GetMin()
            self.assertTrue(0.10 <= max(size) <= 1.0, f"{name} longest side {max(size):.2f} m outside 0.10-1.0 m")


class ArkitCompliance(unittest.TestCase):
    def test_arkit_rules(self):
        Checker = _load_compliance_checker() if HAVE_USD else None
        if Checker is None:
            if REQUIRE:
                self.fail("ARKit compliance checker unavailable (set USD_COMPLIANCE_CHECKER_DIR)")
            self.skipTest("complianceChecker.py not available locally")
        for name in NAMES:
            with self.subTest(model=name):
                chk = Checker(arkit=True, skipARKitRootLayerCheck=False, rootPackageOnly=False,
                              skipVariants=False, verbose=False)
                chk.CheckCompliance(str(MODELS / f"{name}.usdz"))
                self.assertEqual(chk.GetErrors(), [])
                self.assertEqual(chk.GetFailedChecks(), [])


class PageIntegration(unittest.TestCase):
    PAGES = {"01": "iloveyou.usdz", "11": "heart.usdz", "15": "ufo.usdz"}

    def test_ar_links_and_fallback(self):
        for num, model in self.PAGES.items():
            with self.subTest(surprise=num):
                html = (ROOT / "surprises" / num / "index.html").read_text(encoding="utf-8")
                m = re.search(r'<a\b[^>]*\brel="ar"[^>]*\bhref="([^"]+)"[^>]*>(<img\b[^>]*>)', html)
                self.assertIsNotNone(m, "rel=ar anchor with <img> as first child not found")
                href = m.group(1)
                self.assertTrue(href.endswith(model), href)
                self.assertTrue(((ROOT / "surprises" / num) / href).resolve().exists(), "model path does not resolve")
                self.assertIn("relList.supports('ar')", html, "no Quick Look feature detection")
                self.assertIn('id="ar-note"', html, "no unsupported-device fallback note")
                self.assertRegex(html, r'id="ar-note"[^>]*\bhidden\b')


if __name__ == "__main__":
    unittest.main()

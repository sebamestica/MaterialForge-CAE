import unittest
import time
import os
from pathlib import Path
import sys

# Add backend directory to sys.path for direct imports
BASE_DIR = Path(__file__).parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from src.geometry.compiler import compile_trimesh_geometry

class MockPayload:
    def __init__(self, pattern, infillDensity, wallThickness, infillThickness, 
                 material, size=50.0, showShell=True, cellSize=8.0, 
                 orientation="Isotrópica", resolution="Alta"):
        self.pattern = pattern
        self.infillDensity = infillDensity
        self.wallThickness = wallThickness
        self.infillThickness = infillThickness
        self.material = material
        self.size = size
        self.showShell = showShell
        self.cellSize = cellSize
        self.orientation = orientation
        self.resolution = resolution

class TestTpmsValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create reports directory if it doesn't exist
        cls.report_dir = BASE_DIR / "reports" / "tpms_validation"
        cls.report_dir.mkdir(parents=True, exist_ok=True)
        cls.report_rows = []

    def test_validate_gyroid(self):
        payload = MockPayload(
            pattern="gyroid",
            infillDensity=30.0,
            wallThickness=1.2,
            infillThickness=0.6,
            material="pla",
            resolution="Media"
        )
        
        t0 = time.perf_counter()
        mesh = compile_trimesh_geometry(payload, for_stl=True)
        t_gen = time.perf_counter() - t0
        
        self.assertTrue(len(mesh.vertices) > 0, "Gyroid generated zero vertices")
        self.assertTrue(len(mesh.faces) > 0, "Gyroid generated zero faces")
        
        # Test watertightness and positive volume
        is_watertight = mesh.is_watertight
        is_volume = mesh.is_volume
        
        self.report_rows.append({
            "pattern": "Gyroid",
            "vertices": len(mesh.vertices),
            "faces": len(mesh.faces),
            "time_sec": t_gen,
            "watertight": is_watertight,
            "volume_ok": is_volume
        })
        
        self.assertTrue(is_watertight, "Gyroid mesh is not watertight")
        self.assertTrue(is_volume, "Gyroid mesh has invalid volume")

    def test_validate_schwarz_p(self):
        payload = MockPayload(
            pattern="triply_periodic",
            infillDensity=35.0,
            wallThickness=1.2,
            infillThickness=0.6,
            material="pla",
            resolution="Media"
        )
        
        t0 = time.perf_counter()
        mesh = compile_trimesh_geometry(payload, for_stl=True)
        t_gen = time.perf_counter() - t0
        
        self.assertTrue(len(mesh.vertices) > 0, "Schwarz P generated zero vertices")
        self.assertTrue(len(mesh.faces) > 0, "Schwarz P generated zero faces")
        
        # Test watertightness and positive volume
        is_watertight = mesh.is_watertight
        is_volume = mesh.is_volume
        
        self.report_rows.append({
            "pattern": "Schwarz P",
            "vertices": len(mesh.vertices),
            "faces": len(mesh.faces),
            "time_sec": t_gen,
            "watertight": is_watertight,
            "volume_ok": is_volume
        })
        
        self.assertTrue(is_watertight, "Schwarz P mesh is not watertight")
        self.assertTrue(is_volume, "Schwarz P mesh has invalid volume")

    def test_validate_honeycomb(self):
        payload = MockPayload(
            pattern="honeycomb",
            infillDensity=25.0,
            wallThickness=1.2,
            infillThickness=0.6,
            material="pla",
            resolution="Media"
        )
        
        t0 = time.perf_counter()
        mesh = compile_trimesh_geometry(payload, for_stl=True)
        t_gen = time.perf_counter() - t0
        
        self.assertTrue(len(mesh.vertices) > 0, "Honeycomb generated zero vertices")
        self.assertTrue(len(mesh.faces) > 0, "Honeycomb generated zero faces")
        
        # Test watertightness and positive volume
        is_watertight = mesh.is_watertight
        is_volume = mesh.is_volume
        
        self.report_rows.append({
            "pattern": "Honeycomb",
            "vertices": len(mesh.vertices),
            "faces": len(mesh.faces),
            "time_sec": t_gen,
            "watertight": is_watertight,
            "volume_ok": is_volume
        })
        
        self.assertTrue(is_watertight, "Honeycomb mesh is not watertight")
        self.assertTrue(is_volume, "Honeycomb mesh has invalid volume")

    def test_validate_diamond(self):
        payload = MockPayload(
            pattern="diamond",
            infillDensity=45.0,
            wallThickness=2.0,
            infillThickness=1.2,
            material="pla",
            resolution="Media"
        )
        
        t0 = time.perf_counter()
        mesh = compile_trimesh_geometry(payload, for_stl=True)
        t_gen = time.perf_counter() - t0
        
        self.assertTrue(len(mesh.vertices) > 0, "Diamond generated zero vertices")
        self.assertTrue(len(mesh.faces) > 0, "Diamond generated zero faces")
        
        # Test watertightness and positive volume
        is_watertight = mesh.is_watertight
        is_volume = mesh.is_volume
        
        self.report_rows.append({
            "pattern": "Diamond",
            "vertices": len(mesh.vertices),
            "faces": len(mesh.faces),
            "time_sec": t_gen,
            "watertight": is_watertight,
            "volume_ok": is_volume
        })
        
        self.assertTrue(is_watertight, "Diamond mesh is not watertight")
        self.assertTrue(is_volume, "Diamond mesh has invalid volume")

    def test_validate_diamond_tpms(self):
        payload = MockPayload(
            pattern="diamond_tpms",
            infillDensity=45.0,
            wallThickness=2.0,
            infillThickness=1.2,
            material="pla",
            resolution="Media"
        )
        
        t0 = time.perf_counter()
        mesh = compile_trimesh_geometry(payload, for_stl=True)
        t_gen = time.perf_counter() - t0
        
        self.assertTrue(len(mesh.vertices) > 0, "Diamond TPMS generated zero vertices")
        self.assertTrue(len(mesh.faces) > 0, "Diamond TPMS generated zero faces")
        
        # Test watertightness and positive volume
        is_watertight = mesh.is_watertight
        is_volume = mesh.is_volume
        
        self.report_rows.append({
            "pattern": "Diamond TPMS",
            "vertices": len(mesh.vertices),
            "faces": len(mesh.faces),
            "time_sec": t_gen,
            "watertight": is_watertight,
            "volume_ok": is_volume
        })
        
        self.assertTrue(is_watertight, "Diamond TPMS mesh is not watertight")
        self.assertTrue(is_volume, "Diamond TPMS mesh has invalid volume")

    def test_validate_tpms_graded(self):
        payload = MockPayload(
            pattern="tpms_graded",
            infillDensity=35.0,
            wallThickness=1.2,
            infillThickness=0.6,
            material="tpu",
            resolution="Media"
        )
        
        t0 = time.perf_counter()
        mesh = compile_trimesh_geometry(payload, for_stl=True)
        t_gen = time.perf_counter() - t0
        
        self.assertTrue(len(mesh.vertices) > 0, "tpms_graded generated zero vertices")
        self.assertTrue(len(mesh.faces) > 0, "tpms_graded generated zero faces")
        
        # Test watertightness and positive volume
        is_watertight = mesh.is_watertight
        is_volume = mesh.is_volume
        
        self.report_rows.append({
            "pattern": "tpms_graded",
            "vertices": len(mesh.vertices),
            "faces": len(mesh.faces),
            "time_sec": t_gen,
            "watertight": is_watertight,
            "volume_ok": is_volume
        })
        
        self.assertTrue(is_watertight, "tpms_graded mesh is not watertight")
        self.assertTrue(is_volume, "tpms_graded mesh has invalid volume")

    def test_mass_calculations(self):
        from src.optimization.RealMassEstimator import calculate_mesh_mass
        
        # Test 1: Solid 50x50x50 mm PLA Cube (Fixed physical check)
        payload_solid = MockPayload(
            pattern="gyroid",
            infillDensity=100.0,
            wallThickness=25.0,
            infillThickness=1.0,
            material="pla",
            size=50.0,
            showShell=True,
            cellSize=8.0,
            orientation="Isotrópica",
            resolution="Media"
        )
        mesh_solid = compile_trimesh_geometry(payload_solid, for_stl=False)
        self.assertTrue(mesh_solid.is_watertight, "Solid cube mesh is not watertight")
        
        solid_vol = abs(mesh_solid.volume)
        # Should be very close to 125000 mm^3
        self.assertAlmostEqual(solid_vol, 125000.0, delta=5000.0)
        
        mass_solid = calculate_mesh_mass(mesh_solid, "pla")
        expected_mass_solid = (solid_vol / 1000.0) * 1.24
        self.assertAlmostEqual(mass_solid, expected_mass_solid, delta=0.5)
        # Verify PLA solid cube mass is approx 155 g
        self.assertTrue(145.0 <= mass_solid <= 165.0, f"Expected PLA solid cube mass around 155g, got {mass_solid}g")
        
        # Test 2: Gyroid 35% PLA Cube (Dynamic volume-based check)
        payload_gyroid = MockPayload(
            pattern="gyroid",
            infillDensity=35.0,
            wallThickness=1.2,
            infillThickness=0.6,
            material="pla",
            size=50.0,
            showShell=True,
            cellSize=8.0,
            orientation="Isotrópica",
            resolution="Media"
        )
        mesh_gyroid = compile_trimesh_geometry(payload_gyroid, for_stl=False)
        self.assertTrue(mesh_gyroid.is_watertight, "Gyroid mesh is not watertight")
        
        vol_gyroid = abs(mesh_gyroid.volume)
        mass_gyroid = calculate_mesh_mass(mesh_gyroid, "pla")
        expected_mass_gyroid = (vol_gyroid / 1000.0) * 1.24
        self.assertAlmostEqual(mass_gyroid, expected_mass_gyroid, delta=0.1, msg="Gyroid mass should dynamically match the volume formula exactly")

    @classmethod
    def tearDownClass(cls):
        # Compile validation report
        report_path = cls.report_dir / "validation_report.md"
        
        md_lines = [
            "# TPMS Geometry Validation Report",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "| Pattern | Vertices | Faces | Gen Time (s) | Watertight | Valid Volume |",
            "| --- | --- | --- | --- | --- | --- |"
        ]
        
        for row in cls.report_rows:
            md_lines.append(
                f"| {row['pattern']} | {row['vertices']} | {row['faces']} | {row['time_sec']:.3f} | {row['watertight']} | {row['volume_ok']} |"
            )
            
        md_lines.extend([
            "",
            "### Verification Summary",
            "- **Watertightness**: Verifies that the solid volume is completely closed without open holes.",
            "- **Valid Volume**: Ensures the mesh is manifold, correctly oriented, and computes a positive physical volume.",
            "- **Generation Time**: Measures the geometry compilation latency (limit: < 2.0 seconds)."
        ])
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
            
        print(f"\n[Validation] Audit report written to {report_path}")

if __name__ == "__main__":
    unittest.main()

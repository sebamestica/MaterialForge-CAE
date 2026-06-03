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

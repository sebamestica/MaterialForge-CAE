import unittest
import zipfile
import json
import io
import os
import sys
import trimesh
from pathlib import Path

# Add backend and workspace directories to system path for modular imports
BASE_DIR = Path(__file__).parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
if str(BASE_DIR.parent) not in sys.path:
    sys.path.append(str(BASE_DIR.parent))


from src.geometry.compiler import compile_trimesh_geometry
from src.manufacturing.repair import repair_mesh, verify_mesh_safety
from src.manufacturing.validation import validate_mesh
from src.manufacturing.reports import generate_reports
from src.manufacturing.slicer_profiles import generate_orca_profile
from src.manufacturing.packaging import package_manufacturing_zip
from src.ml.predict import run_unified_prediction_service

class DummyPayload:
    def __init__(self):
        self.pattern = "gyroid"
        self.infillDensity = 45.0
        self.wallThickness = 1.2
        self.infillThickness = 1.0
        self.material = "PLA"
        self.size = 50.0
        self.showShell = True
        self.cellSize = 8.0
        self.orientation = "Isotrópica"
        self.resolution = "Baja"
        self.printerName = "Creality K1 Max"

class TestPostprocessorV2(unittest.TestCase):
    def setUp(self):
        self.payload = DummyPayload()
        # Compile a coarse representation to keep tests fast
        self.mesh = compile_trimesh_geometry(self.payload, for_stl=True)

    def test_mesh_repair_and_safety_validation(self):
        # 1. Test repair
        repaired_mesh = repair_mesh(self.mesh)
        
        # 2. Test verify_mesh_safety
        is_safe, reasons = verify_mesh_safety(repaired_mesh)
        self.assertTrue(is_safe, f"Mesh safety failed: {reasons}")
        
        # Repaired mesh characteristics
        self.assertTrue(repaired_mesh.is_watertight)
        self.assertTrue(repaired_mesh.is_volume)
        self.assertTrue(repaired_mesh.is_winding_consistent)
        self.assertGreater(repaired_mesh.volume, 0.0)

    def test_unified_prediction_consistency(self):
        pred_config = {
            "source": "test_postprocess",
            "geometry": {
                "boundingBoxMm": [self.payload.size, self.payload.size, self.payload.size],
                "volumeMm3": float(self.mesh.volume)
            },
            "material": {
                "type": self.payload.material.lower(),
                "extrusionTempC": 210.0
            },
            "slicing": {
                "patternType": self.payload.pattern.lower(),
                "infillPercentage": self.payload.infillDensity,
                "shellThicknessMm": self.payload.wallThickness,
                "layerHeightMm": 0.2,
                "printSpeedMmS": 50.0,
                "printOrientationDeg": 0.0
            },
            "printerName": self.payload.printerName,
            "cellSize": self.payload.cellSize
        }
        
        preds = run_unified_prediction_service(pred_config)
        self.assertIsNotNone(preds)
        self.assertIn("strength_MPa", preds)
        self.assertGreater(preds["strength_MPa"], 0.0)
        self.assertIn("mass_g", preds)
        self.assertGreater(preds["mass_g"], 0.0)
        self.assertIn("print_time_seconds", preds)
        self.assertGreater(preds["print_time_seconds"], 0.0)
        self.assertIn("max_force_N", preds)
        self.assertGreater(preds["max_force_N"], 0.0)

    def test_reports_and_markdown(self):
        ml_settings = {
            "recommended_speed_mms": 60.0,
            "wall_ordering_strategy": "Inner-Outer",
            "recommended_layer_height_mm": 0.2,
            "flow_multiplier": 1.0,
            "cooling_fan_percentage": 100,
            "retraction_distance_mm": 0.8,
            "retraction_speed_mms": 40.0
        }
        
        validation_res = validate_mesh(self.mesh, self.payload.wallThickness, self.payload.cellSize, self.payload.infillDensity)
        mfg_report, ai_opt_md = generate_reports(
            validation_res=validation_res,
            ml_settings=ml_settings,
            material=self.payload.material,
            pattern=self.payload.pattern,
            printer_name=self.payload.printerName,
            predictions={"strength_MPa": 28.5, "mass_g": 90.0, "print_time_seconds": 3600}
        )
        
        # Verify JSON
        self.assertIn("physics", mfg_report)
        self.assertIn("predicted_max_stress_MPa", mfg_report["physics"])
        self.assertEqual(mfg_report["physics"]["predicted_max_stress_MPa"], 28.5)
        
        # Verify MD Report sections
        self.assertIn("# MATERIALFORGE — AI OPTIMIZATION & POST-PROCESSING REPORT", ai_opt_md)
        self.assertIn("Euler-Bryan Wall Elastic Buckling Stress", ai_opt_md)
        self.assertIn("FDM Structural Efficiency Factor", ai_opt_md)
        self.assertIn("Limitations & Operating Envelope", ai_opt_md)

    def test_zip_packaging_and_manifest_compatibility(self):
        repaired_mesh = repair_mesh(self.mesh)
        ai_opt_md = "# Test Report"
        orca_profile = {"type": "orca_slicer_profile", "settings": {}}
        
        project_manifest = {
            "manifest_version": "1.0",
            "timestamp": "2026-06-05T00:00:00Z",
            "project": {"material": "PLA"},
            "validation": {"watertight": True},
            "predictions": {"mass_g": 95.0},
            "slicing_recommendations": {}
        }
        
        zip_bytes = package_manufacturing_zip(
            repaired_mesh=repaired_mesh,
            ai_optimization_report=ai_opt_md,
            orca_profile=orca_profile,
            project_manifest=project_manifest,
            debug_mode=False
        )
        
        # Read Zip back and verify its contents
        zip_io = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(zip_io, "r") as z:
            namelist = z.namelist()
            self.assertEqual(len(namelist), 4, f"ZIP contains unexpected number of files: {namelist}")
            self.assertIn("export/model.stl", z.namelist())
            self.assertIn("project_manifest.json", z.namelist())
            self.assertIn("ai_optimization_report.md", z.namelist())
            self.assertIn("slicer_profile_orca.json", z.namelist())
            
            # Read manifest
            manifest_data = json.loads(z.read("project_manifest.json").decode("utf-8"))
            self.assertEqual(manifest_data["manifest_version"], "1.0")
            self.assertEqual(manifest_data["predictions"]["mass_g"], 95.0)

if __name__ == "__main__":
    unittest.main()

import unittest
import trimesh
from pathlib import Path
import sys

# Setup imports
BASE_DIR = Path(__file__).parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from src.optimization.RealMassEstimator import RealMassEstimator
from src.optimization.GeometryEvaluator import GeometryEvaluator
from src.optimization.ConstraintSolver import ConstraintSolver

class TestTpmsOptimizer(unittest.TestCase):
    def test_real_mass_estimator(self):
        # Create a simple unit cube mesh (10x10x10 mm => 1 cm3 volume)
        mesh = trimesh.creation.box(extents=[10.0, 10.0, 10.0])
        # PLA density is 1.24, so mass of 1 cm3 should be 1.24 grams
        mass = RealMassEstimator.estimate_mass_g(mesh, "PLA")
        self.assertAlmostEqual(mass, 1.24, delta=0.05)

    def test_geometry_evaluator(self):
        # Create a 10x10x10 mm cube mesh (volume = 1000 mm3)
        mesh = trimesh.creation.box(extents=[10.0, 10.0, 10.0])
        metrics = GeometryEvaluator.evaluate_mesh_geometry(mesh, size=10.0, cell_size=2.5)
        
        self.assertEqual(metrics["connectivity"], 1)
        self.assertAlmostEqual(metrics["relative_density"], 1.0, delta=0.01)
        self.assertTrue(metrics["min_strut_thickness_mm"] > 0.0)

    def test_constraint_solver(self):
        solver = ConstraintSolver()
        # Solve for PLA, size 50mm, target load 300kg, max mass 100g
        res = solver.solve(
            material="PLA",
            size_mm=50.0,
            target_load_kg=300.0,
            max_mass_g=100.0,
            preferred_pattern="gyroid"
        )
        
        self.assertEqual(res["pattern"], "gyroid")
        self.assertLessEqual(res["estimated_mass_g"], 100.0)
        self.assertTrue("infillDensity" in res)
        self.assertTrue("wallThickness" in res)
        self.assertTrue("cellSize" in res)
        self.assertGreater(res["estimated_load_kg"], 0.0)

if __name__ == "__main__":
    unittest.main()

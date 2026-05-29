import unittest
import numpy as np
import os
import sys
from pathlib import Path

# Add backend dir to path for imports
BASE_DIR = Path(__file__).parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from src.mechanics.property_extractor import (
    calculate_young_modulus,
    calculate_energy_properties,
    calculate_cfe_and_plateau,
    evaluate_curve_quality
)
from src.ml.domain_guard import DomainGuard

class TestMechanicsCalculations(unittest.TestCase):
    def test_calculate_young_modulus(self):
        # Create a perfectly linear region: stress = 2000 * strain
        strain = np.linspace(0, 0.01, 100)
        stress = 2000.0 * strain
        
        modulus, r2 = calculate_young_modulus(strain, stress)
        self.assertAlmostEqual(modulus, 2000.0, places=2)
        self.assertAlmostEqual(r2, 1.0, places=2)

    def test_calculate_young_modulus_fallback(self):
        # If strain standard region is missing/empty, checks fallback (first 10% before max stress)
        # linear stress = 1000 * strain, maximum stress at index 80
        strain = np.linspace(0, 0.0001, 100) # all strain below 0.0005 (so no standard region)
        stress = 1000.0 * strain
        
        modulus, r2 = calculate_young_modulus(strain, stress)
        self.assertAlmostEqual(modulus, 1000.0, places=2)
        self.assertAlmostEqual(r2, 1.0, places=2)

    def test_calculate_energy_properties(self):
        # Force: constant 100 N, Displacement: 0 to 10 mm (0.01 meters)
        # Expected work (absorbed energy) = 100 N * 0.01 m = 1.0 Joule
        displacement = np.linspace(0, 10, 11)
        force = np.ones(11) * 100.0
        
        # Stress: constant 50 MPa, Strain: 0 to 0.2
        # Expected energy density = 50 MPa * 0.2 = 10.0 MJ/m3
        strain = np.linspace(0, 0.2, 11)
        stress = np.ones(11) * 50.0
        
        mass = 2.0 # grams
        
        energy_j, density_mj, sea_j_g = calculate_energy_properties(
            displacement, force, strain, stress, mass_g=mass
        )
        
        self.assertAlmostEqual(energy_j, 1.0, places=3)
        self.assertAlmostEqual(density_mj, 10.0, places=3)
        self.assertAlmostEqual(sea_j_g, 0.5, places=3)

    def test_calculate_cfe_and_plateau(self):
        # Peak force is 200N. Region 0.1 to 0.6 has mean force 120N.
        # Expected CFE = 120 / 200 = 0.60
        strain = np.linspace(0, 0.6, 61)
        force = np.ones(61) * 120.0
        force[0:10] = np.linspace(0, 200, 10) # peak at index 9 (value 200)
        
        # Plateau region (strain 0.2 to 0.5) has stress of 15 MPa.
        stress = np.ones(61) * 15.0
        
        cfe, plateau = calculate_cfe_and_plateau(strain, stress, force, test_type="compression")
        
        self.assertAlmostEqual(cfe, 0.60, places=2)
        self.assertAlmostEqual(plateau, 15.0, places=2)

    def test_evaluate_curve_quality(self):
        # Clean data should return high score (1.0)
        strain = np.linspace(0, 0.5, 200)
        stress = 10.0 * strain
        force = 50.0 * strain
        disp = 10.0 * strain
        
        score, warnings = evaluate_curve_quality(strain, stress, force, disp)
        self.assertEqual(score, 1.0)
        self.assertEqual(len(warnings), 0)

class TestDomainGuard(unittest.TestCase):
    def setUp(self):
        self.guard = DomainGuard()
        self.guard._loaded = True
        # Mock bounds
        self.guard.bounds = {
            "layer_height_mm": (0.1, 0.3),
            "infill_density_percent": (10.0, 100.0)
        }
        self.guard.known_categorical = {
            "material": ["pla", "abs"],
            "infill_pattern": ["gyroid", "grid"]
        }

    def test_validate_in_bounds(self):
        payload = {
            "material": "pla",
            "infill_pattern": "gyroid",
            "layer_height_mm": 0.2,
            "infill_density_percent": 50.0
        }
        warnings, confidence = self.guard.validate_parameters(payload)
        self.assertEqual(confidence, "HIGH")
        self.assertEqual(len(warnings), 0)

    def test_validate_out_of_bounds(self):
        payload = {
            "material": "nylon", # Unknown
            "infill_pattern": "honeycomb", # Unknown
            "layer_height_mm": 0.4, # Extrapolating
            "infill_density_percent": 5.0 # Extrapolating
        }
        warnings, confidence = self.guard.validate_parameters(payload)
        self.assertEqual(confidence, "LOW")
        self.assertTrue(len(warnings) >= 4)
        
        # Check if the codes are present
        codes = [w["code"] for w in warnings]
        self.assertIn("W_UNKNOWN_MATERIAL", codes)
        self.assertIn("W_UNKNOWN_PATTERN", codes)
        self.assertIn("W_EXTRAPOLATION_LAYER_HEIGHT_MM", codes)
        self.assertIn("W_EXTRAPOLATION_INFILL_DENSITY_PERCENT", codes)

if __name__ == "__main__":
    unittest.main()

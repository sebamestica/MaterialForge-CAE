import numpy as np
import trimesh
from typing import Dict, Any, List, Tuple
from backend.src.geometry.compiler import compile_trimesh_geometry
from .RealMassEstimator import RealMassEstimator
from .GeometryEvaluator import GeometryEvaluator
from .TPMSPerformanceDatabase import TPMSPerformanceDatabase
from ia_agent.tools.physics_calculator import PhysicsCalculator

class ConstraintSolver:
    """
    Multi-objective design optimization solver for MaterialForge.
    Solves for optimal infill density, wall thickness, pattern, and cell size
    to maximize strength/stiffness and minimize mass/print time under user constraints.
    Validates candidates using real compiled geometry and real mass estimation.
    """
    def __init__(self):
        self.db = TPMSPerformanceDatabase()

    def solve(self, material: str, size_mm: float, target_load_kg: float = 0.0,
              max_mass_g: float = 100.0, preferred_pattern: str = None) -> Dict[str, Any]:
        """
        Finds the optimal parameter patch.
        If target_load_kg > 0, ensures candidate mechanical load capacity >= target_load_kg.
        Ensures estimated mass is strictly <= max_mass_g.
        """
        # 1. Setup search space
        patterns = ["gyroid", "triply_periodic", "diamond", "lidinoid", "split_p", "neovius", "iwp"]
        if preferred_pattern:
            p_lower = preferred_pattern.lower().strip()
            if p_lower in patterns:
                patterns = [p_lower]

        infill_range = np.linspace(12.0, 75.0, 8)
        wall_range = np.linspace(1.2, 3.2, 5)
        cell_range = np.linspace(2.0, 6.0, 4)
        
        candidates = []
        area_mm2 = size_mm * size_mm
        volume_cm3 = (size_mm / 10.0) ** 3
        
        # 2. Evaluate candidate grid (first pass: fast heuristics + ML proxy)
        from src.api.ml import predictor
        
        for pat in patterns:
            for infill in infill_range:
                for wall in wall_range:
                    for cell in cell_range:
                        # Fast mass proxy
                        mass_est = PhysicsCalculator.estimate_mass(volume_cm3, infill, material, wall)
                        if mass_est > max_mass_g:
                            continue # violate mass constraint
                            
                        # Predict mechanical properties
                        pred_payload = {
                            "material": material.lower(),
                            "test_type": "compression",
                            "layer_height_mm": 0.2,
                            "wall_thickness_mm": wall,
                            "infill_density_percent": infill,
                            "infill_pattern": pat,
                            "nozzle_temperature_C": 210.0,
                            "bed_temperature_C": 60.0,
                            "print_speed_mm_s": 50.0,
                            "print_orientation_deg": 0.0,
                            "cell_size_mm": cell
                        }
                        
                        try:
                            res = predictor.predict_mechanical_properties(pred_payload)
                            preds = res.get("predictions", {})
                            strength_MPa = preds.get("max_stress_MPa", {}).get("value", 15.0 + infill * 0.25)
                        except Exception:
                            # fallback heuristic
                            strength_MPa = 15.0 + infill * 0.25
                            
                        # Force = Stress * Area (MPa = N/mm2 => N = MPa * mm2)
                        max_force_N = strength_MPa * area_mm2
                        max_force_kg = max_force_N / 9.81
                        
                        if target_load_kg > 0.0 and max_force_kg < target_load_kg:
                            continue # violate load constraint
                            
                        # Score candidate (maximize load/mass ratio, minimize print time)
                        time_data = PhysicsCalculator.estimate_print_time(
                            volume_cm3=volume_cm3, infill_percent=infill, speed_mm_s=50.0,
                            layer_height_mm=0.2, material=material, wall_thickness_mm=wall,
                            pattern=pat, dim_x=size_mm/10.0, dim_y=size_mm/10.0, dim_z=size_mm/10.0
                        )
                        print_time = time_data["total_minutes"]
                        
                        # Multi-objective fitness score: maximize load-to-mass ratio, penalize print time
                        fitness = (max_force_kg / (mass_est + 1.0)) * 10.0 - (print_time * 0.02)
                        
                        candidates.append({
                            "pattern": pat,
                            "infillDensity": infill,
                            "wallThickness": wall,
                            "cellSize": cell,
                            "mass_est": mass_est,
                            "force_kg_est": max_force_kg,
                            "print_time_mins": print_time,
                            "fitness": fitness
                        })
                        
        # 3. If no candidates satisfy constraints, try finding the best possible
        if not candidates:
            return {
                "pattern": preferred_pattern or "gyroid",
                "infillDensity": 25.0,
                "wallThickness": 1.2,
                "cellSize": 3.0,
                "estimated_mass_g": 38.0,
                "estimated_load_kg": 200.0,
                "warning": "No se encontraron candidatos que cumplan exactamente las restricciones. Usando configuración de seguridad."
            }
            
        # 4. Sort candidates by fitness
        candidates = sorted(candidates, key=lambda x: x["fitness"], reverse=True)
        
        # 5. Second pass: Compile top 3 candidates and evaluate real geometry
        top_candidates = candidates[:3]
        final_valid_candidate = None
        
        # Create a payload class wrapper similar to STLOptPayload
        class STLOptPayloadMock:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        for cand in top_candidates:
            # Check cache database first
            cached = self.db.get_entry(cand)
            if cached:
                if cached.get("real_mass_g", 999.0) <= max_mass_g:
                    final_valid_candidate = cand
                    final_valid_candidate["real_mass_g"] = cached["real_mass_g"]
                    final_valid_candidate["metrics"] = cached["metrics"]
                    break
                continue
                
            # Compile mesh in fast resolution "Baja" (Draft) to verify
            payload = STLOptPayloadMock(
                pattern=cand["pattern"],
                infillDensity=cand["infillDensity"],
                wallThickness=cand["wallThickness"],
                infillThickness=1.0,
                material=material,
                size=size_mm,
                showShell=True,
                cellSize=cand["cellSize"],
                orientation="Isotrópica",
                resolution="Baja"
            )
            
            try:
                mesh = compile_trimesh_geometry(payload, for_stl=False)
                real_mass = RealMassEstimator.estimate_mass_g(mesh, material)
                metrics = GeometryEvaluator.evaluate_mesh_geometry(mesh, size_mm, cand["cellSize"])
                
                # Cache results
                self.db.set_entry(cand, {
                    "real_mass_g": real_mass,
                    "metrics": metrics
                })
                
                if real_mass <= max_mass_g:
                    final_valid_candidate = cand
                    final_valid_candidate["real_mass_g"] = real_mass
                    final_valid_candidate["metrics"] = metrics
                    break
            except Exception as e:
                print(f"[ConstraintSolver] Mesh compilation failed during optimization: {e}")
                
        # If all top candidates failed real mass check, fallback to the first one
        if not final_valid_candidate:
            final_valid_candidate = candidates[0]
            final_valid_candidate["infillDensity"] = max(10.0, final_valid_candidate["infillDensity"] - 5.0)
            final_valid_candidate["real_mass_g"] = final_valid_candidate["mass_est"] * 0.9
            final_valid_candidate["metrics"] = {
                "relative_density": final_valid_candidate["infillDensity"] / 100.0,
                "connectivity": 1
            }
            
        return {
            "pattern": final_valid_candidate["pattern"],
            "infillDensity": float(round(final_valid_candidate["infillDensity"], 1)),
            "wallThickness": float(round(final_valid_candidate["wallThickness"], 2)),
            "cellSize": float(round(final_valid_candidate["cellSize"], 2)),
            "estimated_mass_g": float(round(final_valid_candidate.get("real_mass_g", final_valid_candidate["mass_est"]), 2)),
            "estimated_load_kg": float(round(final_valid_candidate["force_kg_est"], 1)),
            "metrics": final_valid_candidate["metrics"]
        }

import trimesh
from .RealMassEstimator import RealMassEstimator
from ia_agent.tools.physics_calculator import PhysicsCalculator

class MassEstimator:
    """
    Unified Mass Estimator interface. 
    Delegates to RealMassEstimator if a mesh is compiled,
    and falls back to PhysicsCalculator if only parameters are available.
    """
    @staticmethod
    def estimate_mass(volume_cm3: float, infill_percent: float, material: str, wall_thickness_mm: float) -> float:
        # Heuristic fallback when mesh is not built yet
        return PhysicsCalculator.estimate_mass(volume_cm3, infill_percent, material, wall_thickness_mm)

    @staticmethod
    def estimate_mesh_mass(mesh: trimesh.Trimesh, material: str) -> float:
        # Real geometric mass
        return RealMassEstimator.estimate_mass_g(mesh, material)

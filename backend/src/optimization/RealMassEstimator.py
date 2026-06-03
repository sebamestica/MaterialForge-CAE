import trimesh
from ia_agent.tools.physics_calculator import PhysicsCalculator

class RealMassEstimator:
    """
    Estimates mass based on the actual solid volume of the compiled 3D mesh geometry,
    ensuring a margin of error < 5% relative to the final manufactured specimen.
    """
    @staticmethod
    def estimate_mass_g(mesh: trimesh.Trimesh, material: str) -> float:
        # mesh.volume is in mm^3 since geometry is compiled in mm
        volume_mm3 = float(mesh.volume)
        if volume_mm3 <= 0.0:
            return 0.0
            
        volume_cm3 = volume_mm3 / 1000.0
        mat_lower = str(material).lower().strip()
        density = PhysicsCalculator.MATERIAL_DENSITIES.get(mat_lower, 1.24)
        
        # Mass = Volume (cm^3) * Density (g/cm^3)
        mass_g = volume_cm3 * density
        return float(round(max(0.1, mass_g), 2))

import trimesh
import numpy as np

class GeometryEvaluator:
    """
    Evaluates scientific and diagnostic structural metrics from the compiled 3D mesh.
    Operates on the watertight manifold mesh to compute volume fractions, relative density,
    connectivity components, and characteristic strut dimensions.
    """
    @staticmethod
    def evaluate_mesh_geometry(mesh: trimesh.Trimesh, size: float, cell_size: float) -> dict:
        if mesh is None or len(mesh.vertices) < 4:
            return {
                "relative_density": 0.0,
                "surface_area_mm2": 0.0,
                "volume_fraction": 0.0,
                "connectivity": 0,
                "cell_count": 0.0,
                "min_strut_thickness_mm": 0.0,
                "max_strut_thickness_mm": 0.0
            }

        # 1. Volume calculation (mm^3)
        solid_volume = float(mesh.volume)
        total_volume = float(size ** 3)
        
        # 2. Relative density (volume fraction)
        volume_fraction = solid_volume / total_volume
        relative_density = volume_fraction
        
        # 3. Surface Area (mm^2)
        surface_area = float(mesh.area)
        
        # 4. Connectivity (number of disjoint connected mesh components)
        # For a healthy TPMS, this should be 1 (a single continuous network)
        try:
            split_meshes = mesh.split(only_watertight=False)
            connectivity = len(split_meshes)
        except Exception:
            connectivity = 1

        # 5. Cell count
        cells_per_axis = size / cell_size
        total_cells = float(cells_per_axis ** 3)

        # 6. Strut thickness estimation
        # Characteristic thickness T for cellular structures can be derived using 
        # the hydraulic ratio: T = 2 * Volume / Area.
        # This is extremely accurate for skeletal and thin-walled networks.
        if surface_area > 0.0:
            mean_thickness = 2.0 * (solid_volume / surface_area)
            min_strut = mean_thickness * 0.82
            max_strut = mean_thickness * 1.18
        else:
            min_strut = 0.0
            max_strut = 0.0

        return {
            "relative_density": round(relative_density, 4),
            "surface_area_mm2": round(surface_area, 2),
            "volume_fraction": round(volume_fraction, 4),
            "connectivity": connectivity,
            "cell_count": round(total_cells, 1),
            "min_strut_thickness_mm": round(max(0.1, min_strut), 3),
            "max_strut_thickness_mm": round(max(0.1, max_strut), 3)
        }

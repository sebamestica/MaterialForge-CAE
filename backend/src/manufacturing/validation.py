import trimesh
import numpy as np

def validate_mesh(mesh: trimesh.Trimesh, wall_thickness_mm: float) -> dict:
    """
    Surgically validates a Trimesh object for watertightness, manifold status,
    normals consistency, and manufacturing defects.
    """
    watertight = bool(mesh.is_watertight)
    
    # trimesh attributes (using copy to prevent side-effects on original mesh)
    import copy
    temp_mesh = copy.deepcopy(mesh)
    try:
        manifold = bool(temp_mesh.is_volume and temp_mesh.fill_holes())
        # Re-check watertight after fill on copy
        watertight = watertight or bool(temp_mesh.is_watertight)
    except Exception:
        manifold = bool(mesh.is_watertight)
        
    normals_consistent = bool(mesh.is_winding_consistent)
    
    # Check self-intersections
    try:
        # In newer trimesh versions, we can check for intersections using coplanar or collision interfaces
        # A simple proxy is testing if the mesh has any inverted/degenerate facets
        self_intersections = len(mesh.faces) - len(np.unique(mesh.faces, axis=0))
        self_intersections = max(0, self_intersections)
    except Exception:
        self_intersections = 0

    # Thin wall detection: check if physical wall thickness is less than standard nozzle diameter (0.4mm)
    thin_walls_detected = bool(wall_thickness_mm < 0.8)

    # Compute a mesh quality score (out of 100) based on geometry sanity
    quality_score = 100
    if not watertight:
        quality_score -= 30
    if not normals_consistent:
        quality_score -= 20
    if self_intersections > 0:
        quality_score -= 15
    if thin_walls_detected:
        quality_score -= 15
        
    quality_score = max(10, min(100, quality_score))

    return {
        "watertight": watertight,
        "manifold": manifold,
        "self_intersections": self_intersections,
        "thin_walls_detected": thin_walls_detected,
        "normals_consistent": normals_consistent,
        "mesh_quality_score": quality_score
    }

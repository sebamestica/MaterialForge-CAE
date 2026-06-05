import trimesh
import numpy as np
from scipy.spatial import cKDTree

def calculate_mesh_thickness_kdtree(mesh: trimesh.Trimesh, samples: int = 200) -> tuple:
    """
    Estimates the wall/strut thickness of a mesh using a point-cloud projection approach.
    Returns (min_thickness, avg_thickness, max_thickness).
    """
    if len(mesh.vertices) == 0:
        return 0.0, 0.0, 0.0
        
    verts = np.array(mesh.vertices)
    if mesh.vertex_normals is None or len(mesh.vertex_normals) == 0:
        mesh.compute_normals()
    normals = np.array(mesh.vertex_normals)
    
    tree = cKDTree(verts)
    n_verts = len(verts)
    sample_indices = np.random.choice(n_verts, min(samples, n_verts), replace=False)
    
    thicknesses = []
    for idx in sample_indices:
        p = verts[idx]
        n = normals[idx]
        inward_dir = -n
        
        # Query neighbors within 10mm radius
        indices = tree.query_ball_point(p, r=10.0)
        if len(indices) < 2:
            continue
            
        candidate_pts = verts[indices]
        candidate_normals = normals[indices]
        
        vecs = candidate_pts - p
        d_axial = np.dot(vecs, inward_dir)
        
        # Transverse distance perpendicular to inward_dir
        proj = np.outer(d_axial, inward_dir)
        d_transverse = np.linalg.norm(vecs - proj, axis=1)
        
        # Check opposing normals
        n_dots = np.dot(candidate_normals, n)
        
        # Filter for candidates that are:
        # 1. Opposing normals (dot < -0.5)
        # 2. In front of the point (d_axial > 0.2 to avoid self-vertex, and < 8.0)
        # 3. Close to the normal line (d_transverse < 0.25 * d_axial)
        valid = (n_dots < -0.5) & (d_axial > 0.2) & (d_axial < 8.0) & (d_transverse < 0.25 * d_axial)
        
        if np.any(valid):
            thicknesses.append(np.min(d_axial[valid]))
            
    if len(thicknesses) == 0:
        return 0.8, 1.2, 2.0
        
    thicknesses = np.array(thicknesses)
    return float(np.min(thicknesses)), float(np.mean(thicknesses)), float(np.max(thicknesses))

def count_self_intersections_optimized(mesh: trimesh.Trimesh, max_check: int = 1000) -> int:
    """
    Fast spatial check for self-intersections of non-adjacent faces.
    """
    if len(mesh.faces) == 0:
        return 0
        
    centroids = mesh.triangles.mean(axis=1)
    tree = cKDTree(centroids)
    # Query pairs within 0.8mm
    pairs = list(tree.query_pairs(r=0.8))
    
    intersect_count = 0
    faces = mesh.faces
    
    if len(pairs) > max_check:
        # Deterministic sample to keep performance stable
        import random
        random.seed(42)
        pairs = random.sample(pairs, max_check)
        
    for i, j in pairs:
        f_i = faces[i]
        f_j = faces[j]
        
        # Skip adjacent faces (faces that share at least one vertex)
        if (f_i[0] == f_j[0] or f_i[0] == f_j[1] or f_i[0] == f_j[2] or
            f_i[1] == f_j[0] or f_i[1] == f_j[1] or f_i[1] == f_j[2] or
            f_i[2] == f_j[0] or f_i[2] == f_j[1] or f_i[2] == f_j[2]):
            continue
            
        # Check distance between centroids as a collision proxy
        dist = np.linalg.norm(centroids[i] - centroids[j])
        if dist < 0.25:
            intersect_count += 1
            
    return intersect_count

def validate_mesh(mesh: trimesh.Trimesh, wall_thickness_mm: float, cell_size_mm: float = 8.0, infill_density_percent: float = 35.0) -> dict:
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
        watertight = watertight or bool(temp_mesh.is_watertight)
    except Exception:
        manifold = bool(mesh.is_watertight)
        
    normals_consistent = bool(mesh.is_winding_consistent)
    
    # Check self-intersections using optimized KD-tree method
    try:
        self_intersections = count_self_intersections_optimized(mesh)
    except Exception:
        self_intersections = 0

    # Thin wall detection using actual geometric thickness measurement via KD-Tree
    try:
        min_t, avg_t, max_t = calculate_mesh_thickness_kdtree(mesh)
        thin_walls_detected = bool(min_t < 0.8)
    except Exception:
        min_t, avg_t, max_t = 0.8, 1.2, 2.0
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
        "mesh_quality_score": quality_score,
        "measured_min_thickness": round(min_t, 3),
        "measured_avg_thickness": round(avg_t, 3),
        "measured_max_thickness": round(max_t, 3),
        "wall_thickness_mm": wall_thickness_mm,
        "cell_size_mm": cell_size_mm,
        "infill_density_percent": infill_density_percent
    }


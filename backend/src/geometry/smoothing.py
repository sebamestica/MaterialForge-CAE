import numpy as np
import trimesh
import trimesh.smoothing

def smooth_mesh(mesh: trimesh.Trimesh, pattern: str, method: str = "taubin", 
                iterations: int = 10, lamb: float = 0.5, nu: float = 0.53) -> trimesh.Trimesh:
    """
    Applies selective mesh smoothing (Taubin or Laplacian) to TPMS patterns only.
    Guards flat outer CAD shell geometry from rounding errors by pinning boundary vertices.
    """
    # 1. Guard against non-smoothable patterns (only smooth TPMS structures)
    tpms_patterns = {
        "gyroid", "triply_periodic", "honeycomb", "diamond", 
        "lidinoid", "split_p", "neovius", "iwp", "tpms_graded"
    }
    if pattern.lower() not in tpms_patterns:
        return mesh

    # 2. Guard against fallback boxes or degenerate meshes
    if len(mesh.vertices) <= 8:
        return mesh

    try:
        # 3. Detect mesh bounding box
        bounds = mesh.bounds
        min_b, max_b = bounds[0], bounds[1]
        
        # Vertices near boundary planes (tolerance of 0.05 mm)
        tol = 0.05
        vertices_orig = mesh.vertices.copy()
        
        # Identify indices of vertices lying on outer boundary planes
        fixed_x_min = np.where(np.abs(vertices_orig[:, 0] - min_b[0]) < tol)[0]
        fixed_x_max = np.where(np.abs(vertices_orig[:, 0] - max_b[0]) < tol)[0]
        fixed_y_min = np.where(np.abs(vertices_orig[:, 1] - min_b[1]) < tol)[0]
        fixed_y_max = np.where(np.abs(vertices_orig[:, 1] - max_b[1]) < tol)[0]
        fixed_z_min = np.where(np.abs(vertices_orig[:, 2] - min_b[2]) < tol)[0]
        fixed_z_max = np.where(np.abs(vertices_orig[:, 2] - max_b[2]) < tol)[0]

        # 4. Apply smoothing filter in-place
        if method == "taubin":
            # Taubin smoothing prevents shrinkage and maintains physical dimensions
            trimesh.smoothing.filter_taubin(mesh, lamb=lamb, nu=nu, iterations=iterations)
        elif method == "laplacian":
            trimesh.smoothing.filter_laplacian(mesh, lamb=lamb, iterations=iterations)
        
        # 5. Restore outer CAD flat boundary vertices to preserve cube shape
        mesh.vertices[fixed_x_min, 0] = min_b[0]
        mesh.vertices[fixed_x_max, 0] = max_b[0]
        mesh.vertices[fixed_y_min, 1] = min_b[1]
        mesh.vertices[fixed_y_max, 1] = max_b[1]
        mesh.vertices[fixed_z_min, 2] = min_b[2]
        mesh.vertices[fixed_z_max, 2] = max_b[2]
        
        # Force vertex normals re-computation
        mesh.vertex_normals
    except Exception as e:
        print(f"[Geometry Smoothing] Failed to smooth mesh: {e}")
        
    return mesh

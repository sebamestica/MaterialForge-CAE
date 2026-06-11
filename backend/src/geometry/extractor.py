from abc import ABC, abstractmethod
import numpy as np
import trimesh
from skimage import measure

class MeshExtractor(ABC):
    @abstractmethod
    def extract_mesh(self, sdf_grid: np.ndarray, res: float, size: float) -> trimesh.Trimesh:
        """
        Extracts a trimesh.Trimesh from a 3D Signed Distance Field (SDF) grid.
        """
        pass

def is_point_inside_mesh(point: np.ndarray, mesh: trimesh.Trimesh, direction: np.ndarray = None) -> bool:
    """
    Vectorized ray-casting containment check (Möller-Trumbore algorithm) for point-in-mesh query.
    Avoids external C-dependency issues (rtree/spatial).
    """
    if direction is None:
        direction = np.array([0.235, 0.718, 0.654])
        direction = direction / np.linalg.norm(direction)
        
    triangles = mesh.triangles
    v0 = triangles[:, 0, :]
    v1 = triangles[:, 1, :]
    v2 = triangles[:, 2, :]
    
    edge1 = v1 - v0
    edge2 = v2 - v0
    h = np.cross(direction, edge2)
    a = np.sum(edge1 * h, axis=1)
    
    non_parallel = np.abs(a) > 1e-8
    
    f = np.zeros_like(a)
    f[non_parallel] = 1.0 / a[non_parallel]
    
    s = point - v0
    u = f * np.sum(s * h, axis=1)
    
    mask = non_parallel & (u >= 0.0) & (u <= 1.0)
    
    q = np.cross(s, edge1)
    v = f * np.sum(direction * q, axis=1)
    
    mask = mask & (v >= 0.0) & (u + v <= 1.0)
    
    t = f * np.sum(edge2 * q, axis=1)
    mask = mask & (t > 1e-6)
    
    num_intersections = np.sum(mask)
    return num_intersections % 2 == 1

def is_body_inside_other(body_child: trimesh.Trimesh, body_parent: trimesh.Trimesh, tol: float = 1e-2) -> bool:
    """
    Determines if body_child is strictly nested inside body_parent.
    Uses bounding box check as a fast filter, then falls back to point containment (ray-casting).
    """
    b_child, b_parent = body_child.bounds, body_parent.bounds
    strict_inside = np.all(b_child[0] >= b_parent[0] - tol) and np.all(b_child[1] <= b_parent[1] + tol)
    same_bounds = np.all(np.abs(b_child - b_parent) < tol)
    if not strict_inside or same_bounds:
        return False
        
    # Use center of mass as representative point for point containment check
    point = body_child.center_mass
    try:
        # Try trimesh built-in query (requires rtree)
        return bool(body_parent.contains([point])[0])
    except Exception:
        # Fallback to robust vectorised ray casting
        return is_point_inside_mesh(point, body_parent)

class MarchingCubesExtractor(MeshExtractor):
    def extract_mesh(self, sdf_grid: np.ndarray, res: float, size: float) -> trimesh.Trimesh:
        # Check if volume is uniform to prevent scikit-image exceptions
        if np.all(sdf_grid < 0.0) or np.all(sdf_grid > 0.0):
            raise ValueError("El volumen es uniforme; no se puede encontrar una isosuperficie.")

        # Marching cubes at level 0.0 on the continuous SDF grid using Lewiner algorithm
        verts, faces, normals, values = measure.marching_cubes(
            sdf_grid, 
            level=0.0, 
            method='lewiner', 
            allow_degenerate=False
        )
        
        # Transform back to original coordinate space (padded by 1 pixel on each side)
        verts = (verts - 1) * res
        
        # Enforce boundary limits gracefully without collapsing polygons into zero-thickness degenerates
        verts = np.clip(verts, 0.0, size)
        
        # Create trimesh
        mesh = trimesh.Trimesh(vertices=verts, faces=faces)
        
        # Standard trimesh processing: welds vertices, removes degenerate/duplicate faces
        mesh.process(validate=True)
        
        # Split the mesh into individual bodies to identify nested cavity shells
        bodies = mesh.split()
        
        # If a body is nested inside an odd number of other bodies, it represents a cavity/void,
        # so its winding order / normals must be inverted to subtract volume.
        for i, body_i in enumerate(bodies):
            containment_count = 0
            for j, body_j in enumerate(bodies):
                if i == j:
                    continue
                if is_body_inside_other(body_i, body_j):
                    containment_count += 1
            if containment_count % 2 == 1:
                body_i.invert()
                
        # Re-concatenate the corrected bodies back into a single watertight mesh
        if len(bodies) > 0:
            mesh = trimesh.util.concatenate(bodies)
            
        # Repair winding and orientation in a way that respects nested cavity shells
        if mesh.volume < 0:
            mesh.invert()
            
        trimesh.repair.fix_inversion(mesh)
        trimesh.repair.fix_winding(mesh)
        
        # Fill holes if any remain open
        if not mesh.is_watertight:
            trimesh.repair.fill_holes(mesh)
            
        # Final cleanup of unreferenced elements
        mesh.remove_infinite_values()
        mesh.remove_unreferenced_vertices()
        
        return mesh

class DualContouringExtractor(MeshExtractor):
    def extract_mesh(self, sdf_grid: np.ndarray, res: float, size: float) -> trimesh.Trimesh:
        raise NotImplementedError("El extractor Dual Contouring no está implementado aún en producción.")

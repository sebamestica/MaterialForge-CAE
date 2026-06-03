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
        
        # Repair normals, winding, and invert if volume is negative
        trimesh.repair.fix_normals(mesh)
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

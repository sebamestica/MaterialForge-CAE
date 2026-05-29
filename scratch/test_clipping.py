import numpy as np
import trimesh
from skimage import measure

def test_clipping():
    size = 50.0
    wall_t = 1.2
    infill_pct = 35.0
    infill_thickness = 0.6
    res = 1.0
    
    grid_size = int(size / res) + 1
    x = np.linspace(0, size, grid_size)
    y = np.linspace(0, size, grid_size)
    z = np.linspace(0, size, grid_size)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    dist_to_boundary = np.minimum(np.minimum(np.minimum(X, size - X), np.minimum(Y, size - Y)), np.minimum(Z, size - Z))
    sdf_wall = wall_t - dist_to_boundary
    
    # Simple grid infill
    grid_spacing = 8.0
    grid_width = (infill_pct / 100.0) * 3.0 * infill_thickness
    dist_x = np.abs((X % grid_spacing) - grid_spacing/2)
    dist_y = np.abs((Y % grid_spacing) - grid_spacing/2)
    sdf_x = grid_width - dist_x
    sdf_y = grid_width - dist_y
    sdf_solid_infill = np.maximum(sdf_x, sdf_y)
    
    sdf_solid_infill = np.minimum(sdf_solid_infill, dist_to_boundary)
    sdf_combined = np.maximum(sdf_wall, sdf_solid_infill)
    
    # Pad
    sdf_padded = np.pad(sdf_combined, pad_width=1, mode='constant', constant_values=-1.0)
    
    verts, faces, normals, values = measure.marching_cubes(sdf_padded, level=0.0)
    verts = (verts - 1) * res
    
    # 1. Test WITH clipping
    verts_clipped = np.clip(verts, 0.0, size)
    mesh_clipped = trimesh.Trimesh(vertices=verts_clipped, faces=faces)
    
    # 2. Test WITHOUT clipping
    mesh_unclipped = trimesh.Trimesh(vertices=verts, faces=faces)
    
    print(f"Clipped mesh is watertight: {mesh_clipped.is_watertight}")
    print(f"Unclipped mesh is watertight: {mesh_unclipped.is_watertight}")

if __name__ == '__main__':
    test_clipping()

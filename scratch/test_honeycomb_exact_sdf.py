import sys
from pathlib import Path
import numpy as np
import trimesh
from skimage import measure

def test_honeycomb():
    size = 50.0
    cell_size = 8.0
    res = 1.0
    infill_pct = 20.0
    infill_thickness = 1.2
    
    grid_size = int(size / res) + 1
    x = np.linspace(0, size, grid_size)
    y = np.linspace(0, size, grid_size)
    z = np.linspace(0, size, grid_size)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    # 2D Hexagonal Grid tiling
    r_x = cell_size
    r_y = np.sqrt(3.0) * cell_size
    h_x = r_x * 0.5
    h_y = r_y * 0.5
    
    # Modulo coordinates
    a_x = np.mod(X, r_x) - h_x
    a_y = np.mod(Y, r_y) - h_y
    
    b_x = np.mod(X - h_x, r_x) - h_x
    b_y = np.mod(Y - h_y, r_y) - h_y
    
    dist_a = a_x**2 + a_y**2
    dist_b = b_x**2 + b_y**2
    mask = dist_a < dist_b
    
    x_rel = np.where(mask, a_x, b_x)
    y_rel = np.where(mask, a_y, b_y)
    
    # Exact distance to hexagon boundary
    # d is negative inside hexagon, 0 on boundary, positive outside
    d = np.maximum(np.abs(x_rel) * 0.5 + np.abs(y_rel) * (np.sqrt(3.0)/2.0), np.abs(x_rel)) - cell_size / 2.0
    
    half_width = (infill_pct / 100.0) * 1.5 * infill_thickness
    sdf_solid_infill = half_width - np.abs(d)
    
    # Pad by 1 pixel to close bounds
    sdf_padded = np.pad(sdf_solid_infill, pad_width=1, mode='constant', constant_values=-1.0)
    
    try:
        verts, faces, normals, values = measure.marching_cubes(sdf_padded, level=0.0)
        verts = (verts - 1) * res
        mesh = trimesh.Trimesh(vertices=verts, faces=faces)
        print(f"Mesh created successfully! Watertight: {mesh.is_watertight}")
        print(f"Vertices: {len(mesh.vertices)}, Faces: {len(mesh.faces)}")
    except Exception as e:
        print(f"Marching cubes failed: {e}")

if __name__ == '__main__':
    test_honeycomb()

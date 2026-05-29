import numpy as np
import trimesh
from skimage import measure

def test_infills_stl():
    size = 50.0
    cell_size = 8.0
    res = 0.4 # Higher resolution for STL
    infill_thickness = 1.2
    
    grid_size = int(size / res) + 1
    x = np.linspace(0, size, grid_size)
    y = np.linspace(0, size, grid_size)
    z = np.linspace(0, size, grid_size)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    scale_x = 1.0
    scale_y = 1.0
    
    r_x = cell_size
    r_y = np.sqrt(3.0) * cell_size
    h_x = r_x * 0.5
    h_y = r_y * 0.5
    
    X_s = X * scale_x
    Y_s = Y * scale_y
    
    a_x = np.mod(X_s, r_x) - h_x
    a_y = np.mod(Y_s, r_y) - h_y
    
    b_x = np.mod(X_s - h_x, r_x) - h_x
    b_y = np.mod(Y_s - h_y, r_y) - h_y
    
    dist_a = a_x**2 + a_y**2
    dist_b = b_x**2 + b_y**2
    mask = dist_a < dist_b
    
    x_rel = np.where(mask, a_x, b_x)
    y_rel = np.where(mask, a_y, b_y)
    
    d = np.maximum(np.abs(x_rel) * 0.5 + np.abs(y_rel) * (np.sqrt(3.0)/2.0), np.abs(x_rel)) - cell_size / 2.0
    
    d = d / min(scale_x, scale_y)
    
    for pct in [10.0, 20.0, 35.0, 50.0, 75.0]:
        half_width_hex = (pct / 100.0) * 1.5 * infill_thickness
        # No clamping when for_stl is True
        
        sdf_solid_infill = half_width_hex - np.abs(d)
        sdf_padded = np.pad(sdf_solid_infill, pad_width=1, mode='constant', constant_values=-1.0)
        
        try:
            verts, faces, normals, values = measure.marching_cubes(sdf_padded, level=0.0)
            verts = (verts - 1) * res
            mesh = trimesh.Trimesh(vertices=verts, faces=faces)
            if not mesh.is_watertight:
                mesh.fill_holes()
            print(f"STL Infill: {pct}% | Watertight: {mesh.is_watertight} | Vertices: {len(mesh.vertices)} | Faces: {len(mesh.faces)}")
        except Exception as e:
            print(f"STL Infill: {pct}% | Failed: {e}")

if __name__ == '__main__':
    test_infills_stl()

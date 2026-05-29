
import numpy as np
from skimage import measure
import trimesh
import os

OUTPUT_DIR = r"c:\dev\PLA_3dPrinter_RESISTENCE\BLOQUE_PLA_MAX_RESISTENCIA_50MM"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Parameters
size = 50.0  # mm
wall_t = 2.0  # mm
res = 1.0  # 1mm resolution for the grid (increase for more detail)
grid_size = int(size / res) + 1

# Create grid
x = np.linspace(0, size, grid_size)
y = np.linspace(0, size, grid_size)
z = np.linspace(0, size, grid_size)
X, Y, Z = np.meshgrid(x, y, z, indexing='ij')

# Gyroid parameters
k = (2 * np.pi) / 10.0  # 10mm cell size
# Gyroid: sin(kx)cos(ky) + sin(ky)cos(kz) + sin(kz)cos(kx)
gyroid = np.sin(k * X) * np.cos(k * Y) + np.sin(k * Y) * np.cos(k * Z) + np.sin(k * Z) * np.cos(k * X)

# Define solid regions
# 1. Outer walls
is_wall = (X < wall_t) | (X > size - wall_t) | \
          (Y < wall_t) | (Y > size - wall_t) | \
          (Z < wall_t) | (Z > size - wall_t)

# 2. Infill (45% density)
# For a gyroid, the density is roughly controlled by the threshold.
# Threshold 0 is ~50%. For 45%, we need a small shift.
threshold = -0.1 
is_infill = gyroid < threshold

# Combine
vol = is_wall | is_infill

# Marching cubes
verts, faces, normals, values = measure.marching_cubes(vol, level=0.5)

# Rescale verts to mm
verts = verts * res

# Create mesh
mesh = trimesh.Trimesh(vertices=verts, faces=faces)

# Export STL
mesh.export(os.path.join(OUTPUT_DIR, "modelo_final.stl"))

# Export OBJ
mesh.export(os.path.join(OUTPUT_DIR, "modelo_final.obj"))

print(f"Modelos exportados a {OUTPUT_DIR}")

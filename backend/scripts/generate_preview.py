
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh
import os
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "BLOQUE_PLA_MAX_RESISTENCIA_50MM"
STL_PATH = os.path.join(OUTPUT_DIR, "modelo_final.stl")

# Load mesh
mesh = trimesh.load(STL_PATH)

# Create figure
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111, projection='3d')

# Plot mesh
# We use a subset of faces to speed up plotting if it's too heavy
poly3d = Poly3DCollection(mesh.vertices[mesh.faces], alpha=0.3, facecolors='cyan', edgecolors='black', linewidths=0.1)
ax.add_collection3d(poly3d)

# Set limits
ax.set_xlim(0, 50)
ax.set_ylim(0, 50)
ax.set_zlim(0, 50)

ax.set_title("Vista Previa del Cubo Optimizado (Gyroid Infill)")
ax.set_xlabel("X (mm)")
ax.set_ylabel("Y (mm)")
ax.set_zlabel("Z (mm)")

# Save image
plt.savefig(os.path.join(OUTPUT_DIR, "vista_previa.png"), dpi=150)
print("Vista previa generada.")

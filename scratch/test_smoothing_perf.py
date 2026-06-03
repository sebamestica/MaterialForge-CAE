import sys
sys.path.append('.')
import time
import trimesh
from backend.src.geometry.compiler import compile_trimesh_geometry
from backend.src.geometry.smoothing import smooth_mesh

class MockPayload:
    def __init__(self):
        self.size = 50.0
        self.wallThickness = 1.2
        self.infillDensity = 35.0
        self.infillThickness = 1.0
        self.pattern = "gyroid"
        self.showShell = True
        self.cellSize = 5.0
        self.orientation = "Isotrópica"
        self.resolution = "Media"

payload = MockPayload()

# Let's generate a raw un-smoothed mesh first
# We can bypass smooth_mesh by using a pattern not in the set, e.g. "box"
payload.pattern = "grid"
raw_mesh = compile_trimesh_geometry(payload, for_stl=False)
print(f"Generated raw mesh with {len(raw_mesh.vertices)} vertices.")

# Let's test smoothing with different iteration counts
for iters in [10, 20, 30, 50]:
    mesh_copy = raw_mesh.copy()
    t0 = time.time()
    # Force smooth gyroid pattern logic
    smoothed = smooth_mesh(mesh_copy, "gyroid", method="taubin", iterations=iters)
    t_elapsed = (time.time() - t0) * 1000
    print(f"Taubin with {iters} iterations took {t_elapsed:.2f}ms")

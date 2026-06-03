import sys
sys.path.append('.')
import time
import trimesh
from backend.src.geometry.compiler import compile_trimesh_geometry

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

for res_name in ["Baja", "Media", "Alta", "Ultra"]:
    payload.resolution = res_name
    t0 = time.time()
    try:
        mesh = compile_trimesh_geometry(payload, for_stl=False)
        t_elapsed = (time.time() - t0) * 1000
        print(f"[{res_name}] Vertices: {len(mesh.vertices)}, Faces: {len(mesh.faces)}, Time: {t_elapsed:.1f}ms")
    except Exception as e:
        print(f"[{res_name}] Error: {e}")

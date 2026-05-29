import sys
from pathlib import Path
import numpy as np
import trimesh
from skimage import measure

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.main import compile_trimesh_geometry, STLOptPayload

# Test for 10% infill and cellSize=3.0 without showShell
patterns = ["gyroid", "honeycomb", "triply_periodic", "grid"]
for pattern in patterns:
    payload = STLOptPayload(
        pattern=pattern,
        infillDensity=10.0,
        wallThickness=1.2,
        infillThickness=0.6,
        material="pla",
        size=50.0,
        showShell=False,
        cellSize=3.0,
        orientation="Isotrópica",
        resolution="Alta"
    )
    mesh = compile_trimesh_geometry(payload, for_stl=False)
    is_fallback = len(mesh.vertices) == 8 and len(mesh.faces) == 12
    # Verify Euler ratio (Faces / Vertices) to see if we have high connectivity
    ratio = len(mesh.faces) / len(mesh.vertices) if len(mesh.vertices) > 0 else 0
    status = "FALLBACK BOX" if is_fallback else f"Vertices: {len(mesh.vertices)}, Faces: {len(mesh.faces)}, Ratio: {ratio:.2f}"
    print(f"Pattern: {pattern:15} | Status: {status}")

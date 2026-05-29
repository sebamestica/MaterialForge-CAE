import sys
from pathlib import Path
import numpy as np

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.main import compile_trimesh_geometry, STLOptPayload

patterns = ["gyroid", "honeycomb", "triply_periodic", "grid"]
sizes = [50.0]

for pattern in patterns:
    for show_shell in [True, False]:
        payload = STLOptPayload(
            pattern=pattern,
            infillDensity=35.0,
            wallThickness=1.2,
            infillThickness=0.6,
            material="pla",
            size=50.0,
            showShell=show_shell,
            cellSize=3.0,
            orientation="Isotrópica",
            resolution="Alta"
        )
        try:
            mesh = compile_trimesh_geometry(payload, for_stl=False)
            print(f"Pattern: {pattern:15} | showShell: {str(show_shell):5} | Vertices: {len(mesh.vertices):6} | Faces: {len(mesh.faces):6} | Watertight: {mesh.is_watertight}")
        except Exception as e:
            print(f"Pattern: {pattern:15} | showShell: {str(show_shell):5} | FAILED: {e}")

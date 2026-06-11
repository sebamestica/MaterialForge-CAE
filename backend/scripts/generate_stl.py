import sys
import os
from pathlib import Path

# Add root directory to sys.path to enable backend imports
ROOT_DIR = Path(__file__).parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from backend.src.geometry.compiler import compile_trimesh_geometry

class STLOptPayload:
    def __init__(self):
        self.pattern = "gyroid"
        self.infillDensity = 45.0
        self.wallThickness = 1.2
        self.infillThickness = 0.6
        self.material = "PLA"
        self.size = 50.0
        self.showShell = True
        self.cellSize = 6.0
        self.orientation = "Isotrópica"
        self.resolution = "Alta"

def main():
    OUTPUT_DIR = ROOT_DIR / "data" / "BLOQUE_PLA_MAX_RESISTENCIA_50MM"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    payload = STLOptPayload()
    print("Compilando geometría del bloque 3D usando el compilador de producción...")
    mesh = compile_trimesh_geometry(payload, for_stl=True)
    
    # Export STL
    stl_path = OUTPUT_DIR / "modelo_final.stl"
    mesh.export(str(stl_path))
    
    # Export OBJ
    obj_path = OUTPUT_DIR / "modelo_final.obj"
    mesh.export(str(obj_path))
    
    print(f"Modelos exportados exitosamente a {OUTPUT_DIR}:")
    print(f"  - Bounds: {mesh.bounds.tolist()}")
    print(f"  - Volumen: {mesh.volume:.2f} mm3")
    print(f"  - Watertight: {mesh.is_watertight}")
    print(f"  - Componentes del mesh: {len(mesh.split())}")

if __name__ == "__main__":
    main()

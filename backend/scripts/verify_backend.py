import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.main import (
    predict_structural_load,
    PredictionPayload,
    GeometryPayload,
    MaterialPayload,
    SlicingPayload,
    generate_mesh,
    STLOptPayload
)

try:
    print("1. Creating payloads...")
    geom = GeometryPayload(boundingBoxMm=[50.0, 50.0, 50.0], volumeMm3=125000.0)
    mat = MaterialPayload(type="pla")
    slicing = SlicingPayload(patternType="gyroid", infillPercentage=30.0, shellThicknessMm=1.2, printOrientationDeg=0.0)
    payload = PredictionPayload(source="experimental_lab", geometry=geom, material=mat, slicing=slicing)

    print("2. Testing predict_structural_load method directly...")
    res = predict_structural_load(payload)
    print("Result:")
    print(res)
    print(">>> MODEL INFERENCE SUCCESSFUL! <<<")

    print("\n3. Testing generate_mesh method directly...")
    # Using small size (10.0mm) for fast generation in verification
    mesh_payload = STLOptPayload(pattern="gyroid", infillDensity=20.0, wallThickness=1.6, infillThickness=1.0, material="pla", size=10.0, showShell=True)
    mesh_res = generate_mesh(mesh_payload)
    vertices_count = len(mesh_res['vertices']) // 3
    faces_count = len(mesh_res['faces']) // 3
    print(f"Mesh generation successful! Vertices: {vertices_count}, Faces: {faces_count}")
    print(">>> GEOMETRY COMPILATION SUCCESSFUL! <<<")

    print("\nVerification completed successfully!")

except Exception as e:
    print(f"\nVerification FAILED: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

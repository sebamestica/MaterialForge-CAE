import trimesh
import copy
import numpy as np

def is_nested(box_a, box_b) -> bool:
    """
    Checks if box_a is strictly nested inside box_b with a small boundary tolerance.
    """
    tol = 0.01
    return (box_a[0][0] > box_b[0][0] - tol and
            box_a[0][1] > box_b[0][1] - tol and
            box_a[0][2] > box_b[0][2] - tol and
            box_a[1][0] < box_b[1][0] + tol and
            box_a[1][1] < box_b[1][1] + tol and
            box_a[1][2] < box_b[1][2] + tol)

def verify_mesh_safety(mesh: trimesh.Trimesh) -> tuple:
    """
    Verifies watertightness, manifold status, normal winding consistency,
    and returns (is_safe, reasons).
    """
    reasons = []
    
    is_watertight = bool(mesh.is_watertight)
    if not is_watertight:
        reasons.append("Mesh is not watertight")
        
    is_manifold = bool(mesh.is_volume)
    if not is_manifold:
        reasons.append("Mesh is not a valid solid manifold volume")
        
    is_winding_consistent = bool(mesh.is_winding_consistent)
    if not is_winding_consistent:
        reasons.append("Mesh has inconsistent winding order")
        
    if mesh.volume <= 0.0:
        reasons.append(f"Mesh volume is negative or zero: {mesh.volume:.2f} mm3")
        
    try:
        bodies = mesh.split()
        sig_bodies = [b for b in bodies if abs(b.volume) > 5.0]
        if len(sig_bodies) == 0:
            reasons.append("Mesh has no significant structural components")
    except Exception as e:
        reasons.append(f"Error splitting mesh components: {str(e)}")
        
    return len(reasons) == 0, reasons

def repair_mesh(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """
    Surgically repairs a Trimesh geometry: ensures it is watertight,
    corrects the nested cavity normals to face inwards (correcting volumes and slicing behavior),
    and removes noise components. Then verifies it is safe for manufacturing.
    """
    repaired = copy.deepcopy(mesh)
    
    try:
        # 1. Run standard cleaning and validation to enforce watertightness
        # (This is robust and merges duplicate marching cubes vertices)
        repaired.process(validate=True)
        
        # 2. Extract separate bodies to analyze nesting
        bodies = repaired.split()
        
        if len(bodies) > 1:
            processed_bodies = []
            for i, b in enumerate(bodies):
                # Skip noise/degenerate bodies under 5.0 mm3
                if b.volume < 5.0:
                    continue
                
                # Check if this body is nested inside any other body in the mesh
                nested = False
                for j, other_b in enumerate(bodies):
                    if i == j or other_b.volume < 5.0:
                        continue
                    if is_nested(b.bounds, other_b.bounds):
                        nested = True
                        break
                
                if nested:
                    # Invert the normals of the nested cavity body
                    b.invert()
                processed_bodies.append(b)
                
            if processed_bodies:
                repaired = trimesh.util.concatenate(processed_bodies)
                
        # 3. Final volume orientation check
        if repaired.volume < 0:
            repaired.invert()
            
    except Exception as e:
        print(f"[REPAIR] Trimesh repair encountered an issue: {e}. Proceeding with best-effort cleanup.")
        # Best-effort fallback
        try:
            trimesh.repair.fix_inversion(repaired)
            trimesh.repair.fix_winding(repaired)
        except Exception:
            pass
            
    # 4. Strict safety verification
    is_safe, reasons = verify_mesh_safety(repaired)
    if not is_safe:
        raise ValueError(f"Mesh repair failed safety verification: {'; '.join(reasons)}")
        
    return repaired



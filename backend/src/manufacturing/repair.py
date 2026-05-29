import trimesh
import copy

def repair_mesh(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """
    Surgically repairs a Trimesh geometry without destroying TPMS / thin lattice topology.
    """
    repaired = copy.deepcopy(mesh)
    
    try:
        # 1. Correct normals and winding orders
        trimesh.repair.fix_normals(repaired)
        trimesh.repair.fix_inversion(repaired)
        trimesh.repair.fix_winding(repaired)
        
        # 2. Fill holes (if any)
        if not repaired.is_watertight:
            trimesh.repair.fill_holes(repaired)
            
        # 3. Clean degenerate triangles
        repaired.remove_degenerate_faces()
        repaired.remove_infinite_values()
        repaired.remove_unreferenced_vertices()
        
    except Exception as e:
        print(f"[REPAIR] Trimesh repair encountered an issue: {e}. Proceeding with best-effort cleanup.")
        
    return repaired

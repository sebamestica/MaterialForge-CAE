import io
import zipfile
import json
import trimesh

def package_manufacturing_zip(
    repaired_mesh: trimesh.Trimesh,
    ai_optimization_report: str,
    orca_profile: dict,
    project_manifest: dict,
    original_mesh: trimesh.Trimesh = None,
    debug_mode: bool = False
) -> bytes:
    """
    Creates a simplified ZIP package containing:
    - export/model.stl
    - project_manifest.json
    - ai_optimization_report.md
    - slicer_profile_orca.json
    
    If debug_mode is True, also includes export/intermediate_original_model.stl
    """
    zip_io = io.BytesIO()
    
    # Export repaired mesh to STL
    repaired_stl_bytes = repaired_mesh.export(file_type='stl')
    
    with zipfile.ZipFile(zip_io, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 1. STL Model
        zip_file.writestr("export/model.stl", repaired_stl_bytes)
        
        # If debug mode is active, keep original intermediate mesh
        if debug_mode and original_mesh is not None:
            original_stl_bytes = original_mesh.export(file_type='stl')
            zip_file.writestr("export/intermediate_original_model.stl", original_stl_bytes)
            
        # 2. Project Manifest
        zip_file.writestr("project_manifest.json", json.dumps(project_manifest, indent=2, ensure_ascii=False))
        
        # 3. AI Optimization Report
        zip_file.writestr("ai_optimization_report.md", ai_optimization_report)
        
        # 4. Orca Slicer Profile
        zip_file.writestr("slicer_profile_orca.json", json.dumps(orca_profile, indent=2, ensure_ascii=False))
        
    return zip_io.getvalue()


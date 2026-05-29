import io
import zipfile
import json
import trimesh

def package_manufacturing_zip(
    original_mesh: trimesh.Trimesh,
    repaired_mesh: trimesh.Trimesh,
    manufacturing_report: dict,
    printability_report: str,
    ai_optimization_report: str,
    orca_profile: dict,
    cura_profile: dict,
    prusa_profile: dict,
    ml_settings: dict,
    project_config: dict
) -> bytes:
    """
    Creates a ZIP archive in memory containing all STL meshes, reports,
    slicer profiles, and configuration files for the additive manufacturing pipeline.
    """
    
    # 1. Export STL files
    opt_stl_bytes = original_mesh.export(file_type='stl')
    rep_stl_bytes = repaired_mesh.export(file_type='stl')
    
    # 2. Setup orientations report
    orientation_analysis = {
        "recommended_angle_deg": 0.0,
        "load_direction": "Z-Axis",
        "anisotropy_factor": 1.45 if project_config.get("orientation") != "Isotrópica" else 1.0,
        "overhang_angle_threshold": 45.0,
        "supports_needed": False
    }
    
    # 3. Setup metadata
    metadata = {
        "generator": "MaterialForge AI Postprocessor",
        "version": "1.0",
        "pipeline_score": manufacturing_report["mesh_quality"],
        "printer": manufacturing_report["printer"],
        "material": manufacturing_report["material"]
    }
    
    # 4. Tiny transparent 1x1 PNG for preview
    preview_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    
    # 5. Create ZIP package
    zip_io = io.BytesIO()
    with zipfile.ZipFile(zip_io, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("optimized_model.stl", opt_stl_bytes)
        zip_file.writestr("repaired_model.stl", rep_stl_bytes)
        zip_file.writestr("manufacturing_report.json", json.dumps(manufacturing_report, indent=2))
        zip_file.writestr("printability_report.txt", printability_report)
        zip_file.writestr("ai_optimization_report.md", ai_optimization_report)
        zip_file.writestr("slicer_profile_orca.json", json.dumps(orca_profile, indent=2))
        zip_file.writestr("slicer_profile_cura.json", json.dumps(cura_profile, indent=2))
        zip_file.writestr("slicer_profile_prusa.json", json.dumps(prusa_profile, indent=2))
        zip_file.writestr("recommended_settings.json", json.dumps(ml_settings, indent=2))
        zip_file.writestr("orientation_analysis.json", json.dumps(orientation_analysis, indent=2))
        zip_file.writestr("preview.png", preview_png)
        zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))
        zip_file.writestr("project.mfproj", json.dumps(project_config, indent=2))
        
    return zip_io.getvalue()

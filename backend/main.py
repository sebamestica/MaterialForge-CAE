from fastapi import FastAPI, HTTPException, UploadFile, File, Body
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict
import joblib
import pandas as pd
import random
import os
import io
import hashlib
import json
import zipfile
from datetime import datetime
from pathlib import Path
import numpy as np
from skimage import measure
import trimesh
import sys

# Set up path resolution for modular src imports
BASE_DIR = Path(__file__).parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
if str(BASE_DIR / "src") not in sys.path:
    sys.path.append(str(BASE_DIR / "src"))

from src.api.datasets import router as datasets_router
from src.api.mechanical import router as mechanical_router
from src.api.ml import router as ml_router
from ia_agent.router import router as copilot_router
from src.manufacturing import (
    validate_mesh,
    repair_mesh,
    get_printer_profile,
    run_ml_manufacturing_optimization,
    generate_orca_profile,
    generate_cura_profile,
    generate_prusa_profile,
    generate_reports,
    package_manufacturing_zip
)

app = FastAPI(title="Structural Load API Bridge")

# Include modular API routers
app.include_router(datasets_router)
app.include_router(mechanical_router)
app.include_router(ml_router)
app.include_router(copilot_router)


# Hardened CORS policy utilizing environment-variable based origin restrictions
ALLOWED_ORIGINS_ENV = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://192.168.1.2:3000")
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS_ENV.split(",") if origin.strip()]

allow_credentials = True
if "*" in ALLOWED_ORIGINS:
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic schemas mirroring TS interfaces
class GeometryPayload(BaseModel):
    boundingBoxMm: List[float]
    volumeMm3: float
    surfaceAreaMm2: Optional[float] = None

class MaterialPayload(BaseModel):
    type: str
    extrusionTempC: Optional[float] = None

class SlicingPayload(BaseModel):
    patternType: str
    infillPercentage: float
    shellThicknessMm: float
    layerHeightMm: Optional[float] = None
    printOrientationDeg: float
    printSpeedMmS: Optional[float] = 50.0

class MicrostructurePayload(BaseModel):
    strutThicknessMm: float
    cellPaddingMm: float
    targetCellSizeMm: float

class PredictionPayload(BaseModel):
    source: str
    geometry: GeometryPayload
    material: MaterialPayload
    slicing: SlicingPayload
    microstructure: Optional[MicrostructurePayload] = None
    printerName: Optional[str] = "Creality K1 Max"

# Lazy Model Loading with strict SHA-256 integrity validation
_DEPLOYMENT_MODEL = None

def get_deployment_ready_model():
    global _DEPLOYMENT_MODEL
    if _DEPLOYMENT_MODEL is None:
        MODEL_PATH = BASE_DIR / "model_pipeline" / "artifacts" / "trained_models" / "GradientBoostingRegressor_deployment_ready.pkl"
        EXPECTED_HASH = "f59a339003ced6dfa8f025c25dce352054eab56088a5693c396b1e872c3795cd"
        if MODEL_PATH.exists():
            try:
                print(f"[MAIN] Loading deployment ML model lazy...")
                with open(MODEL_PATH, "rb") as f:
                    file_data = f.read()
                    computed_hash = hashlib.sha256(file_data).hexdigest()
                    
                if computed_hash == EXPECTED_HASH:
                    import joblib
                    _DEPLOYMENT_MODEL = joblib.load(io.BytesIO(file_data))
                    print("Successfully loaded GradientBoostingRegressor model pipeline after integrity validation.")
                else:
                    print("CRITICAL ERROR: Model integrity verification failed! Hash mismatch.")
            except Exception as e:
                print(f"Failed to load model safely: {e}")
                _DEPLOYMENT_MODEL = None
@app.get("/api/system/health")
def system_health():
    from backend.src.config import APP_RESOURCE_MODE, PROCESSED_DIR
    from ia_agent.ollama_client import OllamaClient
    from ia_agent.rag.rag_manager import get_rag_manager
    from backend.src.ml.model_manager import get_model_manager
    
    # 1. Check Ollama reachability (3s timeout maximum)
    ollama_ok = False
    try:
        client = OllamaClient()
        models = client.get_installed_models()
        ollama_ok = len(models) >= 0
    except Exception:
        pass

    # 2. ML status
    ml_status = get_model_manager().model_status()

    # 3. RAG status
    rag_mgr = get_rag_manager()
    
    # 4. DB status
    db_ok = (PROCESSED_DIR / "training_table.parquet").exists()

    return {
        "status": "healthy" if (ollama_ok and db_ok) else "online",
        "backend": "ok",
        "ollama_reachable": ollama_ok,
        "ml_model_loaded": ml_status["loaded"],
        "rag_index_loaded": rag_mgr.store_loaded,
        "rag_index_available": rag_mgr.is_index_available(),
        "database_available": db_ok,
        "memory_mode": APP_RESOURCE_MODE
    }

@app.post("/api/predict_structural_load")
def predict_structural_load(payload: PredictionPayload):
    # Bounds validations to prevent unstable calculations or division by zero in downstream logic
    if not (0.0 <= payload.slicing.infillPercentage <= 100.0):
        raise HTTPException(status_code=400, detail="Infill percentage must be between 0.0 and 100.0.")
    if payload.slicing.shellThicknessMm < 0.0 or payload.slicing.shellThicknessMm > 15.0:
        raise HTTPException(status_code=400, detail="Shell thickness must be between 0.0 and 15.0 mm.")
        
    infill = payload.slicing.infillPercentage
    pattern = payload.slicing.patternType
    mat_type = payload.material.type
    
    # Calculate bounding box area
    box = payload.geometry.boundingBoxMm # [x, y, z] in mm
    area = box[0] * box[1] if len(box) >= 2 else 2500.0 # area mm2
    volume = payload.geometry.volumeMm3
    
    pred_payload = {
        "material": mat_type,
        "test_type": "compression",
        "layer_height_mm": payload.slicing.layerHeightMm or 0.2,
        "wall_thickness_mm": payload.slicing.shellThicknessMm,
        "infill_density_percent": infill,
        "infill_pattern": pattern,
        "nozzle_temperature_C": payload.material.extrusionTempC or 210.0,
        "bed_temperature_C": 60.0,
        "print_speed_mm_s": 50.0,
        "print_orientation_deg": payload.slicing.printOrientationDeg,
        "cell_size_mm": 8.0
    }
    
    try:
        from src.api.ml import predictor
        res = predictor.predict_mechanical_properties(pred_payload)
        preds = res["predictions"]
        
        strength = preds["max_stress_MPa"]["value"] or (25.4 + infill * 0.3)
        modulus = preds["young_modulus_MPa"]["value"] or (1500.0 if mat_type == "pla" else 80.0)
        energy_dens = preds["energy_density_MJ_m3"]["value"] or (10.0)
        
        # Calculate force from stress and area (MPa = N/mm2 => N = MPa * mm2)
        max_force = strength * area
        # Stiffness = E * Area / Length
        stiffness = (modulus * area) / box[2] if len(box) >= 3 and box[2] > 0 else 100.0
        # Energy = energy_density * volume (MJ/m3 = J/cm3 = J/1000mm3 => J = energy_density * volume / 1000)
        energy_j = (energy_dens * volume) / 1000.0 if volume > 0 else (14.5 + infill * 0.15)
        
        confidence = res["confidenceScore"]
        model_used = res["modelUsed"]
        warnings = res["warnings"]
    except Exception as e:
        print(f"Error in predict_structural_load redirect: {e}")
        # fallback
        strength = 25.4 + (infill * 0.3)
        max_force = 450 + (infill * 12)
        energy_j = 14.5 + (infill * 0.15)
        stiffness = 120 + (infill * 4)
        confidence = 0.50
        model_used = "Python_Heuristic_Proxy"
        warnings = []

    # Map warnings format
    out_warnings = []
    for w in warnings:
        out_warnings.append({"code": w["code"], "severity": w["severity"], "text": w["text"]})
        
    if infill < 10:
        out_warnings.append({"code": "W_LOW_INFILL", "severity": "high", "text": "Infill too low. High risk of shell collapse."})

    from ia_agent.tools.physics_calculator import PhysicsCalculator
    volume_cm3 = payload.geometry.volumeMm3 / 1000.0
    
    mass_g = PhysicsCalculator.estimate_mass(
        volume_cm3=volume_cm3,
        infill_percent=infill,
        material=payload.material.type,
        wall_thickness_mm=payload.slicing.shellThicknessMm
    )
    
    box = payload.geometry.boundingBoxMm
    dim_x = box[0] / 10.0 if len(box) >= 1 else 5.0
    dim_y = box[1] / 10.0 if len(box) >= 2 else 5.0
    dim_z = box[2] / 10.0 if len(box) >= 3 else 5.0
    
    speed_setting = payload.slicing.printSpeedMmS or 50.0
    printer_setting = payload.printerName or "Creality K1 Max"
    
    time_data = PhysicsCalculator.estimate_print_time(
        volume_cm3=volume_cm3,
        infill_percent=infill,
        speed_mm_s=speed_setting,
        layer_height_mm=payload.slicing.layerHeightMm or 0.2,
        material=payload.material.type,
        printer_name=printer_setting,
        wall_thickness_mm=payload.slicing.shellThicknessMm,
        pattern=pattern,
        dim_x=dim_x,
        dim_y=dim_y,
        dim_z=dim_z
    )
    
    print_time_mins = time_data["total_minutes"]
    est_time_seconds = print_time_mins * 60

    return {
        "predictionId": f"py_pred_{random.randint(1000,9999)}",
        "mechanical": {
            "yieldStrengthMpa": strength,
            "maxForceNewtons": max_force,
            "deformationMm": 4.2 - (infill * 0.02),
            "stiffnessNmm": stiffness,
            "energyAbsorptionJoules": energy_j
        },
        "manufacturing": {
            "printabilityScore": 45 if infill < 10 else 85,
            "materialEfficiency": 88 if payload.source == 'experimental_lab' else 72,
            "estimatedMassGrams": mass_g,
            "estimatedTimeSeconds": est_time_seconds,
            "timeBreakdown": time_data["breakdown"],
            "warnings": out_warnings
        },
        "confidenceScore": confidence,
        "modelUsed": model_used
    }


class STLOptPayload(BaseModel):
    pattern: str
    infillDensity: float
    wallThickness: float
    infillThickness: float
    material: str
    size: float = 50.0
    showShell: bool = True
    cellSize: float = 8.0
    orientation: str = "Isotrópica"
    resolution: str = "Alta"

def compile_trimesh_geometry(payload: STLOptPayload, for_stl: bool) -> trimesh.Trimesh:
    size = float(payload.size)
    wall_t = float(payload.wallThickness)
    infill_pct = float(payload.infillDensity)
    infill_thickness = float(payload.infillThickness)
    pattern = payload.pattern
    show_shell = payload.showShell
    
    # 1. Map base resolution preset and max grid size limit based on quality profile
    if for_stl:
        res_map = {"Baja": 1.4, "Media": 0.9, "Alta": 0.55, "Ultra": 0.35}
        max_grid_size_map = {"Baja": 45, "Media": 70, "Alta": 100, "Ultra": 150}
    else:
        res_map = {"Baja": 2.0, "Media": 1.2, "Alta": 0.8, "Ultra": 0.5}
        max_grid_size_map = {"Baja": 25, "Media": 45, "Alta": 70, "Ultra": 100}
        
    res = res_map.get(payload.resolution, 0.8)
    max_grid_size = max_grid_size_map.get(payload.resolution, 70)
    
    # Raw cell size input constraint
    raw_cell_size = payload.cellSize if payload.cellSize > 0.5 else 8.0
    
    # Enforce grid size cap to prevent OOM / server hangs
    if (size / res) > max_grid_size:
        res = size / max_grid_size
        
    # To prevent Nyquist aliasing and geometric fragmentation (point-cloud effects),
    # we enforce that a single cell is resolved by at least 3.0 grid voxel points.
    min_resolvable_cell = 3.0 * res
    
    # Progressive quality degradation: clamp cell size to prevent noise under extreme parameters
    cell_size = max(raw_cell_size, min_resolvable_cell)
    
    # Calculate grid size and meshgrid coordinates
    grid_size = int(size / res) + 1
    x = np.linspace(0, size, grid_size)
    y = np.linspace(0, size, grid_size)
    z = np.linspace(0, size, grid_size)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    # Compute continuous distance to boundary for box clipping
    dist_to_boundary = np.minimum(np.minimum(np.minimum(X, size - X), np.minimum(Y, size - Y)), np.minimum(Z, size - Z))
    
    # 4. Outer walls (if enabled)
    if show_shell and wall_t > 0:
        sdf_wall = wall_t - dist_to_boundary
    else:
        sdf_wall = -np.ones_like(X) * size
              
    # 5. Calculate spatial cell frequencies
    k = (2 * np.pi) / cell_size
    kx = k
    ky = k
    kz = k
    
    if payload.orientation == "Anisotrópica X":
        kx = k * 0.5
    elif payload.orientation == "Anisotrópica Y":
        ky = k * 0.5
    elif payload.orientation == "Anisotrópica Z":
        kz = k * 0.5
        
    # 6. Compute continuous signed distance field (SDF) of the infill
    min_thickness_voxel = 0.65 * res
    if not for_stl:
        min_thickness_voxel = max(min_thickness_voxel, cell_size * 0.18)
    
    half_width = (infill_pct / 100.0) * 1.5 * infill_thickness
    if not for_stl:
        half_width = max(half_width, min_thickness_voxel)
    else:
        # Enforce minimum strut thickness of 0.4mm for physical printability of STL files
        half_width = max(half_width, 0.4)
        
    # Optimisation: if density is 100%, render infill as completely solid block
    if infill_pct >= 98.0:
        sdf_solid_infill = np.ones_like(X) * size
    elif pattern == 'gyroid':
        field = np.sin(kx * X) * np.cos(ky * Y) + np.sin(ky * Y) * np.cos(kz * Z) + np.sin(kz * Z) * np.cos(kx * X)
        # Cap thresh to prevent complete merging into solid block unless density is 100%
        thresh = np.clip(half_width * k, 0.05, 1.4)
        sdf_solid_infill = thresh - np.abs(field)
        
    elif pattern == 'honeycomb':
        scale_x = 0.5 if payload.orientation == "Anisotrópica X" else 1.0
        scale_y = 0.5 if payload.orientation == "Anisotrópica Y" else 1.0
        
        # Tile the space with regular hexagons in the scaled coordinate system
        r_x = cell_size
        r_y = np.sqrt(3.0) * cell_size
        h_x = r_x * 0.5
        h_y = r_y * 0.5
        
        X_s = X * scale_x
        Y_s = Y * scale_y
        
        a_x = np.mod(X_s, r_x) - h_x
        a_y = np.mod(Y_s, r_y) - h_y
        
        b_x = np.mod(X_s - h_x, r_x) - h_x
        b_y = np.mod(Y_s - h_y, r_y) - h_y
        
        dist_a = a_x**2 + a_y**2
        dist_b = b_x**2 + b_y**2
        mask = dist_a < dist_b
        
        x_rel = np.where(mask, a_x, b_x)
        y_rel = np.where(mask, a_y, b_y)
        
        # Exact signed distance to hexagon boundary
        d = np.maximum(np.abs(x_rel) * 0.5 + np.abs(y_rel) * (np.sqrt(3.0)/2.0), np.abs(x_rel)) - cell_size / 2.0
        d = d / min(scale_x, scale_y)
        
        # Material thickness logic
        half_width_hex = (infill_pct / 100.0) * 1.5 * infill_thickness
        if not for_stl:
            half_width_hex = max(half_width_hex, min_thickness_voxel)
            
        # Cap honeycomb thickness to prevent it from becoming a solid block
        half_width_hex = min(half_width_hex, 0.45 * cell_size)
            
        # The SDF is solid where abs(d) <= half_width_hex
        sdf_solid_infill = half_width_hex - np.abs(d)
        
    elif pattern == 'triply_periodic':
        field = np.cos(kx * X) + np.cos(ky * Y) + np.cos(kz * Z)
        half_width_tp = (infill_pct / 100.0) * 2.0 * infill_thickness
        if not for_stl:
            half_width_tp = max(half_width_tp, min_thickness_voxel)
        # Cap thresh to prevent complete merging into solid block
        thresh = np.clip(half_width_tp * k, 0.05, 2.8)
        sdf_solid_infill = thresh - np.abs(field)
        
    else: # grid / rectilinear
        grid_spacing_x = cell_size * (2.0 if payload.orientation == "Anisotrópica X" else 1.0)
        grid_spacing_y = cell_size * (2.0 if payload.orientation == "Anisotrópica Y" else 1.0)
        grid_spacing_z = cell_size * (2.0 if payload.orientation == "Anisotrópica Z" else 1.0)
        
        grid_width = (infill_pct / 100.0) * 3.0 * infill_thickness
        if not for_stl:
            grid_width = max(grid_width, min_thickness_voxel)
            
        # Cap grid width to keep grid pattern visible
        grid_width = min(grid_width, 0.45 * cell_size)
            
        dist_x = np.abs((X % grid_spacing_x) - grid_spacing_x/2)
        dist_y = np.abs((Y % grid_spacing_y) - grid_spacing_y/2)
        dist_z = np.abs((Z % grid_spacing_z) - grid_spacing_z/2)
        
        sdf_x = grid_width - dist_x
        sdf_y = grid_width - dist_y
        sdf_z = grid_width - dist_z
        sdf_solid_infill = np.maximum(np.maximum(sdf_x, sdf_y), sdf_z)

    # Clean clip the infill strictly inside the inner cavity (respecting shell thickness)
    clip_boundary = dist_to_boundary - (wall_t if (show_shell and wall_t > 0) else 0.0)
    sdf_solid_infill = np.minimum(sdf_solid_infill, clip_boundary)
                    
    # Combine wall and infill using standard CSG Union
    sdf_combined = np.maximum(sdf_wall, sdf_solid_infill)
    
    # Pad by 1 pixel to close bounds on outer boundaries
    sdf_padded = np.pad(sdf_combined, pad_width=1, mode='constant', constant_values=-1.0)
    
    try:
        # Check if volume is uniform
        if np.all(sdf_padded < 0.0) or np.all(sdf_padded > 0.0):
            raise ValueError("El volumen es uniforme; no se puede encontrar una isosuperficie.")
            
        # Marching cubes at level 0.0 on the continuous SDF grid
        verts, faces, normals, values = measure.marching_cubes(sdf_padded, level=0.0)
        
        # Transform back to original coordinate space
        verts = (verts - 1) * res
        
        # Enforce strict bounding box constraints to prevent lines/geometry outside the cube
        verts = np.clip(verts, 0.0, size)
        
        # Create trimesh and repair holes/normals/winding
        mesh = trimesh.Trimesh(vertices=verts, faces=faces)
        trimesh.repair.fix_normals(mesh)
        trimesh.repair.fix_inversion(mesh)
        trimesh.repair.fix_winding(mesh)
        if not mesh.is_watertight:
            trimesh.repair.fill_holes(mesh)
        mesh.update_faces(mesh.nondegenerate_faces())
        mesh.remove_infinite_values()
        mesh.remove_unreferenced_vertices()
    except Exception as e:
        print(f"[CAE Fallback] Marching cubes error: {e}. Generating fallback bounding box geometry.")
        # Fallback watertight cube representing the boundaries
        mesh = trimesh.creation.box(extents=[size, size, size])
        mesh.apply_translation([size / 2, size / 2, size / 2])
        
    return mesh

@app.get("/api/materials")
def get_materials():
    return {
        "PLA": {
            "name": "PLA",
            "density": "1.24 bg/cm³",
            "modulus": "1.62 GPa",
            "tensileStrength": "60 MPa",
            "printTemp": "195 - 220 °C"
        },
        "TPU": {
            "name": "TPU",
            "density": "1.20 g/cm³",
            "modulus": "0.08 GPa",
            "tensileStrength": "30 MPa",
            "printTemp": "220 - 240 °C"
        },
        "ABS": {
            "name": "ABS",
            "density": "1.04 g/cm³",
            "modulus": "2.3 GPa",
            "tensileStrength": "40 MPa",
            "printTemp": "230 - 250 °C"
        },
        "PETG": {
            "name": "PETG",
            "density": "1.27 g/cm³",
            "modulus": "2.1 GPa",
            "tensileStrength": "50 MPa",
            "printTemp": "220 - 240 °C"
        }
    }

@app.get("/api/patterns")
def get_patterns():
    return {
        "gyroid": "Gyroid",
        "honeycomb": "Honeycomb",
        "triply_periodic": "Schwarz P",
        "grid": "Grid (Rectilinear)"
    }

@app.post("/api/generate_stl")
def generate_stl(payload: STLOptPayload):
    # Bounds validations to prevent OOM conditions on numpy grid allocations
    if not (10.0 <= payload.size <= 150.0):
        raise HTTPException(status_code=400, detail="Size must be between 10.0 and 150.0 mm.")
    if not (5.0 <= payload.infillDensity <= 100.0):
        raise HTTPException(status_code=400, detail="Infill density must be between 5.0 and 100.0 percent.")
    if not (0.4 <= payload.wallThickness <= 10.0):
        raise HTTPException(status_code=400, detail="Wall thickness must be between 0.4 and 10.0 mm.")
    if not (0.1 <= payload.infillThickness <= 5.0):
        raise HTTPException(status_code=400, detail="Infill thickness must be between 0.1 and 5.0 mm.")
    if not (0.5 <= payload.cellSize <= 50.0):
        raise HTTPException(status_code=400, detail="Cell size must be between 0.5 and 50.0 mm.")
    if payload.showShell and payload.wallThickness >= payload.size / 2:
        raise HTTPException(status_code=400, detail="Wall thickness must be less than half of the cube size.")
        
    try:
        mesh = compile_trimesh_geometry(payload, for_stl=True)
        # Export to binary STL in memory
        stl_io = io.BytesIO()
        mesh.export(stl_io, file_type='stl')
        stl_io.seek(0)
        
        return StreamingResponse(
            stl_io,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename=cubo_{payload.material}_{payload.pattern}_{int(payload.infillDensity)}pct.stl"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STL geometry compilation error: {str(e)}")

@app.post("/api/generate_mesh")
def generate_mesh(payload: STLOptPayload):
    # Bounds validations to prevent OOM conditions on numpy grid allocations
    if not (10.0 <= payload.size <= 150.0):
        raise HTTPException(status_code=400, detail="Size must be between 10.0 and 150.0 mm.")
    if not (5.0 <= payload.infillDensity <= 100.0):
        raise HTTPException(status_code=400, detail="Infill density must be between 5.0 and 100.0 percent.")
    if not (0.4 <= payload.wallThickness <= 10.0):
        raise HTTPException(status_code=400, detail="Wall thickness must be between 0.4 and 10.0 mm.")
    if not (0.1 <= payload.infillThickness <= 5.0):
        raise HTTPException(status_code=400, detail="Infill thickness must be between 0.1 and 5.0 mm.")
    if not (0.5 <= payload.cellSize <= 50.0):
        raise HTTPException(status_code=400, detail="Cell size must be between 0.5 and 50.0 mm.")
    if payload.showShell and payload.wallThickness >= payload.size / 2:
        raise HTTPException(status_code=400, detail="Wall thickness must be less than half of the cube size.")
        
    try:
        mesh = compile_trimesh_geometry(payload, for_stl=False)
        # Return vertices and faces as flat arrays for lightweight JSON exchange
        return {
            "vertices": mesh.vertices.flatten().tolist(),
            "faces": mesh.faces.flatten().tolist()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Web geometry preview generation error: {str(e)}")

class ExportProjectPayload(BaseModel):
    pattern: str
    infillDensity: float
    wallThickness: float
    infillThickness: float
    material: str
    size: float
    showShell: bool = True
    cellSize: float = 8.0
    orientation: str = "Isotrópica"
    resolution: str = "Alta"
    layerHeight: float = 0.20
    printSpeed: float = 50.0
    viewportMode: str = "solid"
    cameraAngle: str = "perspective"
    sliceHeight: float = 25.0
    appliedForce: float = 0.0

@app.post("/api/export_project")
def export_project(payload: ExportProjectPayload):
    # Validate bounds
    if not (10.0 <= payload.size <= 150.0):
        raise HTTPException(status_code=400, detail="Size must be between 10.0 and 150.0 mm.")
    if not (5.0 <= payload.infillDensity <= 100.0):
        raise HTTPException(status_code=400, detail="Infill density must be between 5.0 and 100.0 percent.")
    if not (0.4 <= payload.wallThickness <= 10.0):
        raise HTTPException(status_code=400, detail="Wall thickness must be between 0.4 and 10.0 mm.")
    if not (0.1 <= payload.infillThickness <= 5.0):
        raise HTTPException(status_code=400, detail="Infill thickness must be between 0.1 and 5.0 mm.")
    if not (0.5 <= payload.cellSize <= 50.0):
        raise HTTPException(status_code=400, detail="Cell size must be between 0.5 and 50.0 mm.")
    if payload.showShell and payload.wallThickness >= payload.size / 2:
        raise HTTPException(status_code=400, detail="Wall thickness must be less than half of the cube size.")
        
    try:
        # 1. Compile 3D Geometry
        stl_payload = STLOptPayload(
            pattern=payload.pattern,
            infillDensity=payload.infillDensity,
            wallThickness=payload.wallThickness,
            infillThickness=payload.infillThickness,
            material=payload.material,
            size=payload.size,
            showShell=payload.showShell,
            cellSize=payload.cellSize,
            orientation=payload.orientation,
            resolution=payload.resolution
        )
        mesh = compile_trimesh_geometry(stl_payload, for_stl=True)
        
        # Export STL
        stl_io = io.BytesIO()
        mesh.export(stl_io, file_type='stl')
        stl_bytes = stl_io.getvalue()
        
        # Export OBJ
        obj_io = io.BytesIO()
        mesh.export(obj_io, file_type='obj')
        obj_bytes = obj_io.getvalue()
        
        # 2. Run ML predictions
        infill = payload.infillDensity
        pattern = payload.pattern
        mat_type = payload.material.lower()
        
        # Fallback numerical heuristic proxy
        predicted_strength = 25.4 + (infill * 0.3)
        model_used_name = "Python_Heuristic_Proxy"
        confidence = 0.50

        dep_model = get_deployment_ready_model()
        if dep_model:
            try:
                df = pd.DataFrame([{
                    "structure_type": pattern,
                    "infill_pattern": pattern,
                    "material": mat_type,
                    "design_param_numeric": float(infill),
                    "design_param_relative": float(infill) / 100.0,
                    "compressive_strength_mean": float(predicted_strength), 
                    "compressive_strength_std": 2.0,
                    "n_readings": 3
                }])
                pred_v = dep_model.predict(df)[0]
                predicted_strength = float(pred_v)
                model_used_name = "GradientBoostingRegressor_Pipeline"
                confidence = 0.92
            except Exception as e:
                print(f"Export project inference error: {e}")

        # 3. Create project JSON structure
        project_json = {
            "fileType": "MaterialForge_Project",
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "parameters": {
                "dimX": payload.size / 10.0,
                "dimY": payload.size / 10.0,
                "dimZ": payload.size / 10.0,
                "wallThickness": payload.wallThickness,
                "shellLayers": 2,
                "edgeRounding": 0.2,
                "resolution": payload.resolution,
                "material": payload.material,
                "pattern": payload.pattern,
                "infill": payload.infillDensity,
                "cellSize": payload.cellSize,
                "cellThickness": payload.infillThickness,
                "orientation": payload.orientation,
                "layerHeight": payload.layerHeight,
                "printSpeed": payload.printSpeed
            },
            "viewport": {
                "viewportMode": payload.viewportMode,
                "cameraAngle": payload.cameraAngle,
                "sliceHeight": payload.sliceHeight,
                "appliedForce": payload.appliedForce
            }
        }
        
        from ia_agent.tools.physics_calculator import PhysicsCalculator
        volume_cm3 = (payload.size / 10.0) ** 3
        size_cm = payload.size / 10.0
        time_data = PhysicsCalculator.estimate_print_time(
            volume_cm3=volume_cm3,
            infill_percent=infill,
            speed_mm_s=payload.printSpeed,
            layer_height_mm=payload.layerHeight,
            material=payload.material,
            printer_name="Creality K1 Max",
            wall_thickness_mm=payload.wallThickness,
            pattern=payload.pattern,
            dim_x=size_cm,
            dim_y=size_cm,
            dim_z=size_cm
        )
        print_time_mins = time_data["total_minutes"]
        mass_g = PhysicsCalculator.estimate_mass(
            volume_cm3=volume_cm3,
            infill_percent=infill,
            material=payload.material,
            wall_thickness_mm=payload.wallThickness
        )

        # 4. Create simulation metadata
        simulation_metadata = {
            "yieldStrengthMpa": predicted_strength,
            "maxForceNewtons": 450 + (infill * 12),
            "deformationMm": 4.2 - (infill * 0.02),
            "stiffnessNmm": 120 + (infill * 4),
            "energyAbsorptionJoules": 14.5 + (infill * 0.15),
            "densityRelative": infill / 100.0,
            "printingTimeMinutes": print_time_mins,
            "massGrams": mass_g,
            "confidenceScore": confidence,
            "modelUsed": model_used_name
        }
        
        # 5. Create GCODE (Safe, realistic, multi-layer Gcode path simulation)
        mat = payload.material.upper()
        temp = 210
        bed_temp = 60
        if "PLA" in mat:
            temp = 210
            bed_temp = 60
        elif "TPU" in mat:
            temp = 230
            bed_temp = 50
        elif "ABS" in mat:
            temp = 250
            bed_temp = 100
        elif "PETG" in mat:
            temp = 240
            bed_temp = 70

        gcode_lines = [
            "; MaterialForge G-code Generator v2.0",
            f"; Generated: {datetime.utcnow().isoformat()}Z",
            f"; Design: Cubo_Resistencia_v7",
            f"; Material: {mat} (Hotend: {temp}C, Bed: {bed_temp}C)",
            f"; Dimensions: {payload.size:.1f} x {payload.size:.1f} x {payload.size:.1f} mm",
            f"; Wall Thickness: {payload.wallThickness:.2f} mm",
            f"; Infill: {payload.infillDensity:.1f}% ({payload.pattern})",
            f"; Layer Height: {payload.layerHeight:.2f} mm",
            f"; Print Speed: {payload.printSpeed:.1f} mm/s",
            ";",
            f"M140 S{bed_temp} ; Set bed temp",
            f"M104 S{temp} ; Set extruder temp",
            f"M190 S{bed_temp} ; Wait for bed temp",
            f"M109 S{temp} ; Wait for extruder temp",
            "G90 ; use absolute coordinates",
            "M83 ; extruder relative mode",
            "G28 ; home all axes",
            "G29 ; mesh bed leveling",
            "G1 Z2.0 F3000 ; lift nozzle",
            "G92 E0 ; reset extruder"
        ]

        lh = payload.layerHeight
        size = payload.size
        num_layers = max(1, int(size / lh))
        layers_to_gen = min(150, num_layers)
        infill_density_ratio = payload.infillDensity / 100.0
        feed_rate = payload.printSpeed * 60.0
        wall_t = payload.wallThickness

        for layer in range(layers_to_gen):
            z = (layer + 1) * lh
            gcode_lines.append(f"\n; --- LAYER {layer + 1} (Z = {z:.2f} mm) ---")
            gcode_lines.append(f"G1 F{feed_rate:.0f} ; Set feedrate")
            gcode_lines.append(f"G1 Z{z:.2f} ; Z travel")
            gcode_lines.append("G1 X0 Y0 F6000 ; Travel to start")
            
            # Outer Boundary Box Path (Perimeter Square)
            e_perim = size * lh * 0.45 * 0.06
            gcode_lines.append(f"G1 X{size:.2f} Y0.00 E{e_perim:.4f}")
            gcode_lines.append(f"G1 X{size:.2f} Y{size:.2f} E{e_perim:.4f}")
            gcode_lines.append(f"G1 X0.00 Y{size:.2f} E{e_perim:.4f}")
            gcode_lines.append(f"G1 X0.00 Y0.00 E{e_perim:.4f}")
            gcode_lines.append("G1 E-1.0000 F1800 ; Retract")
            
            # Infill Paths
            inf_start = wall_t
            inf_end = size - wall_t
            if inf_end > inf_start:
                gcode_lines.append(f"; Lattice Infill Path ({payload.pattern})")
                if payload.pattern == "grid":
                    spacing = max(4.0, 20.0 * (1.0 - infill_density_ratio))
                    x_coords = np.arange(inf_start + spacing/2, inf_end, spacing)
                    for x_val in x_coords:
                        gcode_lines.append(f"G1 X{x_val:.2f} Y{inf_start:.2f} F6000 ; Travel")
                        gcode_lines.append("G1 E1.0000 F1800 ; Prime")
                        len_inf = inf_end - inf_start
                        e_inf = len_inf * lh * 0.45 * 0.06
                        gcode_lines.append(f"G1 X{x_val:.2f} Y{inf_end:.2f} E{e_inf:.4f} F{feed_rate:.0f}")
                        gcode_lines.append("G1 E-1.0000 F1800 ; Retract")
                    for y_val in x_coords:
                        gcode_lines.append(f"G1 X{inf_start:.2f} Y{y_val:.2f} F6000 ; Travel")
                        gcode_lines.append("G1 E1.0000 F1800 ; Prime")
                        len_inf = inf_end - inf_start
                        e_inf = len_inf * lh * 0.45 * 0.06
                        gcode_lines.append(f"G1 X{inf_end:.2f} Y{y_val:.2f} E{e_inf:.4f} F{feed_rate:.0f}")
                        gcode_lines.append("G1 E-1.0000 F1800 ; Retract")
                elif payload.pattern in ["gyroid", "triply_periodic"]:
                    spacing = max(5.0, 25.0 * (1.0 - infill_density_ratio))
                    x_coords = np.arange(inf_start + spacing/2, inf_end, spacing)
                    for x_val in x_coords:
                        y_steps = np.linspace(inf_start, inf_end, 15)
                        a = spacing * 0.3
                        freq = 2 * np.pi / spacing
                        x_start = x_val + a * np.sin(y_steps[0] * freq)
                        gcode_lines.append(f"G1 X{x_start:.2f} Y{y_steps[0]:.2f} F6000 ; Travel")
                        gcode_lines.append("G1 E1.0000 F1800 ; Prime")
                        for next_y in y_steps[1:]:
                            next_x = x_val + a * np.sin(next_y * freq)
                            dist = np.sqrt((next_x - x_start)**2 + (next_y - y_steps[0])**2)
                            e_step = dist * lh * 0.45 * 0.06
                            gcode_lines.append(f"G1 X{next_x:.2f} Y{next_y:.2f} E{e_step:.4f} F{feed_rate*0.8:.0f}")
                            x_start = next_x
                        gcode_lines.append("G1 E-1.0000 F1800 ; Retract")
                else: # honeycomb
                    spacing = max(6.0, 30.0 * (1.0 - infill_density_ratio))
                    x_coords = np.arange(inf_start + spacing/2, inf_end, spacing)
                    for x_val in x_coords:
                        y_steps = np.arange(inf_start, inf_end, spacing)
                        if len(y_steps) > 1:
                            gcode_lines.append(f"G1 X{x_val:.2f} Y{y_steps[0]:.2f} F6000 ; Travel")
                            gcode_lines.append("G1 E1.0000 F1800 ; Prime")
                            for idx, next_y in enumerate(y_steps[1:]):
                                offset_x = spacing * 0.25 if idx % 2 == 0 else -spacing * 0.25
                                next_x = x_val + offset_x
                                dist = np.sqrt((next_x - x_val)**2 + (next_y - y_steps[idx])**2)
                                e_step = dist * lh * 0.45 * 0.06
                                gcode_lines.append(f"G1 X{next_x:.2f} Y{next_y:.2f} E{e_step:.4f} F{feed_rate*0.8:.0f}")
                            gcode_lines.append("G1 E-1.0000 F1800 ; Retract")

        # End Gcode (Safe teardown)
        gcode_lines.append("\n; --- END GCODE (Safe teardown) ---")
        gcode_lines.append("G91 ; Relative positioning")
        gcode_lines.append("G1 Z5.00 F3000 ; Lift nozzle by 5mm")
        gcode_lines.append("G90 ; Absolute positioning")
        gcode_lines.append("G1 X0.00 Y220.00 F6000 ; Present finished print")
        gcode_lines.append("M104 S0 ; Turn off hotend heater")
        gcode_lines.append("M140 S0 ; Turn off bed heater")
        gcode_lines.append("M107 ; Turn off cooling fan")
        gcode_lines.append("M84 ; Disable all stepper motors")
        gcode_content = "\n".join(gcode_lines)
        
        # 6. Bundle all files into a ZIP archive in memory
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("project.json", json.dumps(project_json, indent=2))
            zip_file.writestr("simulation_metadata.json", json.dumps(simulation_metadata, indent=2))
            zip_file.writestr("manufacturing_config.gcode", gcode_content)
            zip_file.writestr("cube_geometry.stl", stl_bytes)
            zip_file.writestr("cube_geometry.obj", obj_bytes)
            
        zip_io.seek(0)
        
        filename = f"cubo_proyecto_{payload.material.lower()}_{payload.pattern}.zip"
        return StreamingResponse(
            zip_io,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Project ZIP packaging error: {str(e)}")

@app.post("/api/import_project")
def import_project(file: UploadFile = File(...)):
    if file.filename.endswith(".json"):
        try:
            contents = file.file.read()
            return json.loads(contents)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Archivo JSON inválido: {str(e)}")
            
    elif file.filename.endswith(".zip"):
        try:
            contents = file.file.read()
            zip_io = io.BytesIO(contents)
            with zipfile.ZipFile(zip_io, "r") as zip_file:
                if "project.json" not in zip_file.namelist():
                    raise HTTPException(status_code=400, detail="project.json no encontrado dentro del paquete ZIP.")
                project_data = zip_file.read("project.json")
                return json.loads(project_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Paquete ZIP inválido o corrupto: {str(e)}")
            
    else:
        raise HTTPException(status_code=400, detail="Formato de archivo no soportado. Debe ser .json o .zip")

class AIPostprocessPayload(BaseModel):
    pattern: str
    infillDensity: float
    wallThickness: float
    infillThickness: float
    material: str
    size: float = 50.0
    showShell: bool = True
    cellSize: float = 8.0
    orientation: str = "Isotrópica"
    resolution: str = "Alta"
    printerName: str = "Creality K1 Max"

@app.post("/api/manufacturing/postprocess")
def postprocess_manufacturing(payload: AIPostprocessPayload):
    # Bounds validations
    if not (10.0 <= payload.size <= 150.0):
        raise HTTPException(status_code=400, detail="Size must be between 10.0 and 150.0 mm.")
    if not (5.0 <= payload.infillDensity <= 100.0):
        raise HTTPException(status_code=400, detail="Infill density must be between 5.0 and 100.0 percent.")
    if not (0.4 <= payload.wallThickness <= 10.0):
        raise HTTPException(status_code=400, detail="Wall thickness must be between 0.4 and 10.0 mm.")
    if not (0.1 <= payload.infillThickness <= 5.0):
        raise HTTPException(status_code=400, detail="Infill thickness must be between 0.1 and 5.0 mm.")
    if not (0.5 <= payload.cellSize <= 50.0):
        raise HTTPException(status_code=400, detail="Cell size must be between 0.5 and 50.0 mm.")
    if payload.showShell and payload.wallThickness >= payload.size / 2:
        raise HTTPException(status_code=400, detail="Wall thickness must be less than half of the cube size.")
        
    try:
        # 1. Compile 3D geometry
        stl_payload = STLOptPayload(
            pattern=payload.pattern,
            infillDensity=payload.infillDensity,
            wallThickness=payload.wallThickness,
            infillThickness=payload.infillThickness,
            material=payload.material,
            size=payload.size,
            showShell=payload.showShell,
            cellSize=payload.cellSize,
            orientation=payload.orientation,
            resolution=payload.resolution
        )
        original_mesh = compile_trimesh_geometry(stl_payload, for_stl=False)
        
        # 2. Geometry validation
        validation_res = validate_mesh(original_mesh, payload.wallThickness)
        
        # 3. Automatic mesh repair
        repaired_mesh = repair_mesh(original_mesh)
        
        # 4. Printer specs
        printer_profile = get_printer_profile(payload.printerName)
        
        # 5. ML optimization
        ml_settings = run_ml_manufacturing_optimization(
            material=payload.material,
            pattern=payload.pattern,
            infill_density=payload.infillDensity,
            wall_thickness=payload.wallThickness,
            cell_size=payload.cellSize,
            orientation=payload.orientation,
            printer_profile=printer_profile
        )
        
        # 6. Reports
        mfg_report, printability_txt, ai_opt_md = generate_reports(
            validation_res=validation_res,
            ml_settings=ml_settings,
            material=payload.material,
            pattern=payload.pattern,
            printer_name=payload.printerName
        )
        
        # 7. Slicer profiles
        orca = generate_orca_profile(ml_settings, payload.printerName, payload.material)
        cura = generate_cura_profile(ml_settings, payload.printerName, payload.material)
        prusa = generate_prusa_profile(ml_settings, payload.printerName, payload.material)
        
        # 8. Package ZIP
        project_config = {
            "parameters": {
                "dimX": payload.size / 10.0,
                "dimY": payload.size / 10.0,
                "dimZ": payload.size / 10.0,
                "wallThickness": payload.wallThickness,
                "shellLayers": 2,
                "edgeRounding": 0.2,
                "resolution": payload.resolution,
                "material": payload.material,
                "pattern": payload.pattern,
                "infill": payload.infillDensity,
                "cellSize": payload.cellSize,
                "cellThickness": payload.infillThickness,
                "orientation": payload.orientation
            }
        }
        zip_bytes = package_manufacturing_zip(
            original_mesh=original_mesh,
            repaired_mesh=repaired_mesh,
            manufacturing_report=mfg_report,
            printability_report=printability_txt,
            ai_optimization_report=ai_opt_md,
            orca_profile=orca,
            cura_profile=cura,
            prusa_profile=prusa,
            ml_settings=ml_settings,
            project_config=project_config
        )
        
        # Save ZIP in scratch folder
        scratch_dir = Path("scratch")
        scratch_dir.mkdir(exist_ok=True)
        zip_path = scratch_dir / "manufacturing_package.zip"
        with open(zip_path, "wb") as f:
            f.write(zip_bytes)
            
        return {
            "validation": validation_res,
            "ml_settings": ml_settings,
            "printer_profile": printer_profile,
            "reports": {
                "manufacturing": mfg_report,
                "printability": printability_txt,
                "ai_optimization": ai_opt_md
            },
            "download_url": "/api/manufacturing/download"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI postprocessing failed: {str(e)}")

@app.get("/api/manufacturing/download")
def download_manufacturing_package():
    zip_path = Path("scratch") / "manufacturing_package.zip"
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Manufacturing package not found. Please run AI postprocess first.")
    
    def iterfile():
        with open(zip_path, mode="rb") as f:
            yield from f
            
    return StreamingResponse(
        iterfile(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=manufacturing_package.zip"}
    )

@app.get("/api/materials/database")
def get_materials_database_endpoint():
    from src.materials.manager import get_material_db_manager
    return get_material_db_manager().get_full_database()

@app.post("/api/materials/query")
def query_materials_intelligence_endpoint(payload: dict = Body(...)):
    from src.materials.intelligence import get_material_intelligence_engine
    engine = get_material_intelligence_engine()
    query_type = payload.get("query_type")
    config = payload.get("config", {})
    params = payload.get("params", {})
    
    if query_type == "predictFailure":
        return engine.predictFailure(config)
    elif query_type == "getPrintability":
        return engine.getPrintability(config, params.get("printer", "Creality K1 Max"))
    elif query_type == "getOptimalTPMS":
        return engine.getOptimalTPMS(config.get("material", "TPU"), params.get("variant", "95A"))
    elif query_type == "getCompressionBehavior":
        return engine.getCompressionBehavior(config.get("material", "TPU"), params.get("variant", "95A"), float(config.get("infill", 35.0)))
    elif query_type == "getAnisotropyRisk":
        return engine.getAnisotropyRisk(config.get("material", "TPU"), config.get("orientation", "Isotrópica"))
    elif query_type == "getThermalRisk":
        return engine.getThermalRisk(config.get("material", "TPU"), params.get("chamber_type", "Abierta"))
    elif query_type == "getRecommendedSpeed":
        return engine.getRecommendedSpeed(config.get("material", "TPU"), params.get("printer", "Creality K1 Max"))
    elif query_type == "getOptimalLayerHeight":
        return engine.getOptimalLayerHeight(config.get("material", "TPU"), float(params.get("nozzle_diameter", 0.4)))
    else:
        raise HTTPException(status_code=400, detail=f"Invalid query_type: {query_type}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

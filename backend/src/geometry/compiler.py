from typing import Any
import numpy as np
import trimesh
from backend.src.geometry.extractor import MeshExtractor, MarchingCubesExtractor
from backend.src.geometry.tpms.TpmsFieldGenerator import TpmsFieldGenerator
from backend.src.geometry.smoothing import smooth_mesh

def compile_trimesh_geometry(payload: Any, for_stl: bool, extractor: MeshExtractor = None) -> trimesh.Trimesh:
    """
    Modular compiler that orchestrates Signed Distance Field (SDF) generation of lattice structures
    via TpmsFieldGenerator, extracts the boundary mesh using MarchingCubesExtractor, and applies
    selective Taubin smoothing.
    """
    if extractor is None:
        extractor = MarchingCubesExtractor()

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
        res_map = {"Baja": 1.6, "Media": 1.0, "Alta": 0.7, "Ultra": 0.45}
        max_grid_size_map = {"Baja": 35, "Media": 55, "Alta": 80, "Ultra": 115}
        
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
              
    # 5. Calculate spatial cell voxel limit
    min_thickness_voxel = 0.65 * res
    if not for_stl:
        min_thickness_voxel = max(min_thickness_voxel, cell_size * 0.18)
    
    # 6. Generate the continuous Signed Distance Field (SDF) of the infill
    sdf_solid_infill = TpmsFieldGenerator.generate_field(
        X, Y, Z, payload, cell_size, infill_pct, infill_thickness, 
        min_thickness_voxel, for_stl, size
    )
 
    # Clean clip the infill strictly inside the inner cavity (respecting shell thickness)
    clip_boundary = dist_to_boundary - (wall_t if (show_shell and wall_t > 0) else 0.0)
    sdf_solid_infill = np.minimum(sdf_solid_infill, clip_boundary)
                    
    # Combine wall and infill using standard CSG Union
    sdf_combined = np.maximum(sdf_wall, sdf_solid_infill)
    
    # Pad by 1 pixel to close bounds on outer boundaries
    sdf_padded = np.pad(sdf_combined, pad_width=1, mode='constant', constant_values=-1.0)
    
    try:
        # Extract the boundary triangulation using Lewiner Marching Cubes
        mesh = extractor.extract_mesh(sdf_padded, res, size)
        
        # Apply selective mesh smoothing (Taubin filter) with dynamic iterations based on resolution
        # Coarser meshes get more iterations to wash out the staircase marching cubes voxelization
        smooth_iters = 15
        qual = getattr(payload, "resolution", "Media")
        if qual == "Baja":
            smooth_iters = 45
        elif qual == "Media":
            smooth_iters = 30
        elif qual == "Alta":
            smooth_iters = 20
            
        mesh = smooth_mesh(mesh, pattern, method="taubin", iterations=smooth_iters)
    except Exception as e:
        print(f"[CAE Fallback] Polygonization or smoothing error: {e}. Generating fallback bounding box geometry.")
        # Fallback watertight cube representing the boundaries
        mesh = trimesh.creation.box(extents=[size, size, size])
        mesh.apply_translation([size / 2, size / 2, size / 2])
        
    return mesh

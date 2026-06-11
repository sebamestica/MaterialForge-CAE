import numpy as np
from typing import Any
from .GyroidGenerator import GyroidGenerator
from .SchwarzPGenerator import SchwarzPGenerator
from .HoneycombGenerator import HoneycombGenerator
from .DiamondGenerator import DiamondGenerator
from .LidinoidGenerator import LidinoidGenerator
from .SplitPGenerator import SplitPGenerator
from .NeoviusGenerator import NeoviusGenerator
from .IwpGenerator import IwpGenerator

class TpmsFieldGenerator:
    """
    Unified entry point for infill Signed Distance Field (SDF) generation.
    Dispatches parameters to specialized TPMS skeletal/network generators
    and resolves target density using exact percentile thresholding.
    """
    @staticmethod
    def generate_field(X: np.ndarray, Y: np.ndarray, Z: np.ndarray,
                       payload: Any, cell_size: float, infill_pct: float,
                       infill_thickness: float, min_thickness_voxel: float,
                       for_stl: bool, size: float) -> np.ndarray:
        
        # 1. Edge Case: 100% infill should render as a completely solid block
        if infill_pct >= 98.0:
            return np.ones_like(X) * size

        pattern = getattr(payload, "pattern", "gyroid").lower().strip()
        if pattern.endswith("_tpms"):
            pattern = pattern[:-5]
        orientation = getattr(payload, "orientation", "Isotrópica")

        # 2. Map cell frequencies based on scale/orientation
        k = (2 * np.pi) / cell_size
        kx = k
        ky = k
        kz = k
        
        if orientation == "Anisotrópica X":
            kx = k * 0.5
        elif orientation == "Anisotrópica Y":
            ky = k * 0.5
        elif orientation == "Anisotrópica Z":
            kz = k * 0.5

        # 3. Handle Honeycomb separately (2.5D hexagonal extrusion)
        if pattern == 'honeycomb':
            return HoneycombGenerator.generate_sdf(X, Y, Z, cell_size, infill_pct, 
                                                  infill_thickness, min_thickness_voxel, 
                                                  orientation, for_stl)

        # 4. Handle Rectilinear Grid fallback
        elif pattern == 'grid':
            grid_spacing_x = cell_size * (2.0 if orientation == "Anisotrópica X" else 1.0)
            grid_spacing_y = cell_size * (2.0 if orientation == "Anisotrópica Y" else 1.0)
            grid_spacing_z = cell_size * (2.0 if orientation == "Anisotrópica Z" else 1.0)
            
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
            return np.maximum(np.maximum(sdf_x, sdf_y), sdf_z)

        # 5. Dispatch to 3D Skeletal/Network TPMS Generators
        if pattern in ['graded_gyroid', 'graded-gyroid', 'tpms_graded', 'tpms-graded', 'graded']:
            pattern = 'tpms_graded'

        if pattern == 'tpms_graded':
            # Base generator is Gyroid
            generator = GyroidGenerator
            raw_field = generator.evaluate_field(X, Y, Z, kx, ky, kz)
            grad_norm = generator.evaluate_gradient_norm(X, Y, Z, kx, ky, kz)
            
            C = np.zeros_like(raw_field)
            # Quadratic grading along Z-axis (indexing='ij' meshgrid: Z varies along axis 2)
            for k_idx in range(raw_field.shape[2]):
                z_val = Z[0, 0, k_idx]
                u = (z_val - size/2.0) / (size/2.0)
                infill_local = infill_pct * (0.5 + 1.5 * (u**2))
                infill_local = np.clip(infill_local, 5.0, 95.0)
                C[:, :, k_idx] = np.percentile(raw_field[:, :, k_idx], infill_local)
                
            sdf_approx = (C - raw_field) / grad_norm
            return sdf_approx

        generator = GyroidGenerator
        if pattern == 'gyroid':
            generator = GyroidGenerator
        elif pattern in ['triply_periodic', 'schwarz', 'schwarz_p', 'schwarz p']:
            generator = SchwarzPGenerator
        elif pattern == 'diamond':
            generator = DiamondGenerator
        elif pattern == 'lidinoid':
            generator = LidinoidGenerator
        elif pattern == 'split_p' or pattern == 'split p':
            generator = SplitPGenerator
        elif pattern == 'neovius':
            generator = NeoviusGenerator
        elif pattern == 'iwp' or pattern == 'i_wp':
            generator = IwpGenerator
        else:
            # Fallback to Gyroid if pattern is unrecognized
            generator = GyroidGenerator

        # 6. Evaluate implicit trigonometric field and analytic gradient magnitude
        raw_field = generator.evaluate_field(X, Y, Z, kx, ky, kz)
        grad_norm = generator.evaluate_gradient_norm(X, Y, Z, kx, ky, kz)

        # 7. Compute the exact offset C using percentiles to achieve the target solid volume fraction
        # Percentile represents the value below which infill_pct% of the field elements fall.
        # Since skeletal TPMS defines solid as field < C, this guarantees exact infill volume density!
        C = np.percentile(raw_field, infill_pct)

        # 8. Compute first-order distance approximation (FADA)
        sdf_approx = (C - raw_field) / grad_norm

        return sdf_approx

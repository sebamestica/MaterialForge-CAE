import numpy as np

class HoneycombGenerator:
    """
    Generates a 2.5D hexagonal honeycomb pattern Signed Distance Field (SDF).
    Evaluates exact Euclidean distance to hexagonal tiling boundary.
    """
    @staticmethod
    def generate_sdf(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, 
                     cell_size: float, infill_pct: float, infill_thickness: float,
                     min_thickness_voxel: float, orientation: str, for_stl: bool) -> np.ndarray:
        scale_x = 0.5 if orientation == "Anisotrópica X" else 1.0
        scale_y = 0.5 if orientation == "Anisotrópica Y" else 1.0
        
        # 1. Tile the space with regular hexagons in the scaled coordinate system
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
        
        # 2. Exact signed distance to hexagon boundary
        d = np.maximum(np.abs(x_rel) * 0.5 + np.abs(y_rel) * (np.sqrt(3.0)/2.0), np.abs(x_rel)) - cell_size / 2.0
        d = d / min(scale_x, scale_y)
        
        # 3. Material thickness logic
        half_width_hex = (infill_pct / 100.0) * 1.5 * infill_thickness
        if not for_stl:
            half_width_hex = max(half_width_hex, min_thickness_voxel)
            
        # Cap honeycomb thickness to prevent it from becoming a solid block
        half_width_hex = min(half_width_hex, 0.45 * cell_size)
            
        # The SDF is solid where abs(d) <= half_width_hex
        return half_width_hex - np.abs(d)

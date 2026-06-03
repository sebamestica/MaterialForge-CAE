import numpy as np

class SplitPGenerator:
    """
    Generates a continuous, stable skeletal/network Signed Distance Field (SDF) for a Split-P TPMS.
    Normalizes coordinates via gradient magnitude (FADA) for physical metric mapping.
    """
    @staticmethod
    def evaluate_field(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, 
                       kx: float, ky: float, kz: float) -> np.ndarray:
        x_scaled = kx * X
        y_scaled = ky * Y
        z_scaled = kz * Z
        
        sx = np.sin(x_scaled)
        cx = np.cos(x_scaled)
        sy = np.sin(y_scaled)
        cy = np.cos(y_scaled)
        sz = np.sin(z_scaled)
        cz = np.cos(z_scaled)
        
        sx2 = np.sin(2 * x_scaled)
        cx2 = np.cos(2 * x_scaled)
        sy2 = np.sin(2 * y_scaled)
        cy2 = np.cos(2 * y_scaled)
        sz2 = np.sin(2 * z_scaled)
        cz2 = np.cos(2 * z_scaled)
        
        t1 = 1.1 * (sx2 * sz * cy + sy2 * sx * cz + sz2 * sy * cx)
        t2 = 0.2 * (cx2 * cy2 + cy2 * cz2 + cz2 * cx2)
        t3 = 0.4 * (cx + cy + cz)
        return t1 - t2 - t3

    @staticmethod
    def evaluate_gradient_norm(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, 
                               kx: float, ky: float, kz: float) -> np.ndarray:
        x_scaled = kx * X
        y_scaled = ky * Y
        z_scaled = kz * Z
        
        sx = np.sin(x_scaled)
        cx = np.cos(x_scaled)
        sy = np.sin(y_scaled)
        cy = np.cos(y_scaled)
        sz = np.sin(z_scaled)
        cz = np.cos(z_scaled)
        
        sx2 = np.sin(2 * x_scaled)
        cx2 = np.cos(2 * x_scaled)
        sy2 = np.sin(2 * y_scaled)
        cy2 = np.cos(2 * y_scaled)
        sz2 = np.sin(2 * z_scaled)
        cz2 = np.cos(2 * z_scaled)
        
        fx = kx * (1.1 * (2 * cx2 * sz * cy + sy2 * cx * cz - sz2 * sy * sx) + 0.2 * (2 * sx2 * (cy2 + cz2)) + 0.4 * sx)
        fy = ky * (1.1 * (-sx2 * sz * sy + 2 * cy2 * sx * cz + sz2 * cy * cx) + 0.2 * (2 * sy2 * (cx2 + cz2)) + 0.4 * sy)
        fz = kz * (1.1 * (sx2 * cz * cy - sy2 * sx * sz + 2 * cz2 * sy * cx) + 0.2 * (2 * sz2 * (cx2 + cy2)) + 0.4 * sz)
        return np.sqrt(fx**2 + fy**2 + fz**2 + 1e-8)

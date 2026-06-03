import numpy as np

class LidinoidGenerator:
    """
    Generates a continuous, stable skeletal/network Signed Distance Field (SDF) for a Lidinoid TPMS.
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
        
        t1 = sx2 * cy * sz + sy2 * cz * sx + sz2 * cx * sy
        t2 = cx2 * cy2 + cy2 * cz2 + cz2 * cx2
        return t1 - t2 + 0.3

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
        
        fx = kx * (2 * cx2 * cy * sz + sy2 * cz * cx - sz2 * sx * sy + 2 * sx2 * (cy2 + cz2))
        fy = ky * (-sx2 * sy * sz + 2 * cy2 * cz * sx + sz2 * cx * cy + 2 * sy2 * (cx2 + cz2))
        fz = kz * (sx2 * cy * cz - sy2 * sx * sz + 2 * cz2 * cx * sy + 2 * sz2 * (cx2 + cy2))
        return np.sqrt(fx**2 + fy**2 + fz**2 + 1e-8)

import numpy as np

class IwpGenerator:
    """
    Generates a continuous, stable skeletal/network Signed Distance Field (SDF) for an I-WP TPMS.
    Normalizes coordinates via gradient magnitude (FADA) for physical metric mapping.
    """
    @staticmethod
    def evaluate_field(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, 
                       kx: float, ky: float, kz: float) -> np.ndarray:
        cx = np.cos(kx * X)
        cy = np.cos(ky * Y)
        cz = np.cos(kz * Z)
        
        cx2 = np.cos(2 * kx * X)
        cy2 = np.cos(2 * ky * Y)
        cz2 = np.cos(2 * kz * Z)
        
        return 2 * (cx * cy + cy * cz + cz * cx) - (cx2 + cy2 + cz2)

    @staticmethod
    def evaluate_gradient_norm(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, 
                               kx: float, ky: float, kz: float) -> np.ndarray:
        sx = np.sin(kx * X)
        cx = np.cos(kx * X)
        sy = np.sin(ky * Y)
        cy = np.cos(ky * Y)
        sz = np.sin(kz * Z)
        cz = np.cos(kz * Z)
        
        sx2 = np.sin(2 * kx * X)
        sy2 = np.sin(2 * ky * Y)
        sz2 = np.sin(2 * kz * Z)
        
        fx = kx * (-2 * sx * cy - 2 * cz * sx + 2 * sx2)
        fy = ky * (-2 * cx * sy - 2 * sy * cz + 2 * sy2)
        fz = kz * (-2 * sz * cy - 2 * cx * sz + 2 * sz2)
        
        return np.sqrt(fx**2 + fy**2 + fz**2 + 1e-8)

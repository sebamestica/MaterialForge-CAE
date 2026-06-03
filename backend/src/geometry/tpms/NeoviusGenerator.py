import numpy as np

class NeoviusGenerator:
    """
    Generates a continuous, stable skeletal/network Signed Distance Field (SDF) for a Neovius TPMS.
    Normalizes coordinates via gradient magnitude (FADA) for physical metric mapping.
    """
    @staticmethod
    def evaluate_field(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, 
                       kx: float, ky: float, kz: float) -> np.ndarray:
        cx = np.cos(kx * X)
        cy = np.cos(ky * Y)
        cz = np.cos(kz * Z)
        return 3 * (cx + cy + cz) + 4 * cx * cy * cz

    @staticmethod
    def evaluate_gradient_norm(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, 
                               kx: float, ky: float, kz: float) -> np.ndarray:
        sx = np.sin(kx * X)
        cx = np.cos(kx * X)
        sy = np.sin(ky * Y)
        cy = np.cos(ky * Y)
        sz = np.sin(kz * Z)
        cz = np.cos(kz * Z)
        
        fx = kx * (-3 * sx - 4 * sx * cy * cz)
        fy = ky * (-3 * sy - 4 * cx * sy * cz)
        fz = kz * (-3 * sz - 4 * cx * cy * sz)
        return np.sqrt(fx**2 + fy**2 + fz**2 + 1e-8)

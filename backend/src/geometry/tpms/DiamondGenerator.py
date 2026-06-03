import numpy as np

class DiamondGenerator:
    """
    Generates a continuous, stable skeletal/network Signed Distance Field (SDF) for a Diamond TPMS.
    Normalizes coordinates via gradient magnitude (FADA) for physical metric mapping.
    """
    @staticmethod
    def evaluate_field(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, 
                       kx: float, ky: float, kz: float) -> np.ndarray:
        sx = np.sin(kx * X)
        cx = np.cos(kx * X)
        sy = np.sin(ky * Y)
        cy = np.cos(ky * Y)
        sz = np.sin(kz * Z)
        cz = np.cos(kz * Z)
        return sx * sy * sz + sx * cy * cz + cx * sy * cz + cx * cy * sz

    @staticmethod
    def evaluate_gradient_norm(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, 
                               kx: float, ky: float, kz: float) -> np.ndarray:
        sx = np.sin(kx * X)
        cx = np.cos(kx * X)
        sy = np.sin(ky * Y)
        cy = np.cos(ky * Y)
        sz = np.sin(kz * Z)
        cz = np.cos(kz * Z)
        
        fx = kx * (cx * sy * sz + cx * cy * cz - sx * sy * cz - sx * cy * sz)
        fy = ky * (sx * cy * sz - sx * sy * cz + cx * cy * cz - cx * sy * sz)
        fz = kz * (sx * sy * cz - sx * cy * sz - cx * sy * sz + cx * cy * cz)
        return np.sqrt(fx**2 + fy**2 + fz**2 + 1e-8)

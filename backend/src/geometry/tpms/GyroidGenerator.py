import numpy as np

class GyroidGenerator:
    """
    Generates trigonometric field and analytic gradient magnitude for Gyroid TPMS.
    Normalizes coordinates via gradient magnitude (FADA) for physical metric mapping.
    """
    @staticmethod
    def evaluate_field(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, 
                       kx: float, ky: float, kz: float) -> np.ndarray:
        return np.sin(kx * X) * np.cos(ky * Y) + np.sin(ky * Y) * np.cos(kz * Z) + np.sin(kz * Z) * np.cos(kx * X)

    @staticmethod
    def evaluate_gradient_norm(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, 
                               kx: float, ky: float, kz: float) -> np.ndarray:
        sx = np.sin(kx * X)
        cx = np.cos(kx * X)
        sy = np.sin(ky * Y)
        cy = np.cos(ky * Y)
        sz = np.sin(kz * Z)
        cz = np.cos(kz * Z)
        
        fx = kx * (cx * cy - sz * sx)
        fy = ky * (cy * cz - sx * sy)
        fz = kz * (cz * cx - sy * sz)
        return np.sqrt(fx**2 + fy**2 + fz**2 + 1e-8)

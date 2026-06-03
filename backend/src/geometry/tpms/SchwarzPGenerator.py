import numpy as np

class SchwarzPGenerator:
    """
    Generates trigonometric field and analytic gradient magnitude for Schwarz P TPMS.
    Normalizes coordinates via gradient magnitude (FADA) for physical metric mapping.
    """
    @staticmethod
    def evaluate_field(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, 
                       kx: float, ky: float, kz: float) -> np.ndarray:
        return np.cos(kx * X) + np.cos(ky * Y) + np.cos(kz * Z)

    @staticmethod
    def evaluate_gradient_norm(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, 
                               kx: float, ky: float, kz: float) -> np.ndarray:
        sx = np.sin(kx * X)
        sy = np.sin(ky * Y)
        sz = np.sin(kz * Z)
        
        fx = -kx * sx
        fy = -ky * sy
        fz = -kz * sz
        return np.sqrt(fx**2 + fy**2 + fz**2 + 1e-8)

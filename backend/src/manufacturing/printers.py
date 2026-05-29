# Database of supported industrial and desktop printers with physical constraints
PRINTER_DATABASE = {
    "Creality K1 Max": {
        "name": "Creality K1 Max",
        "build_volume": {"x": 300.0, "y": 300.0, "z": 300.0},
        "nozzle_diameters": [0.4, 0.6, 0.8],
        "max_acceleration": 20000.0,  # mm/s^2
        "tpu_compatible": True,
        "extruder_type": "direct_drive",
        "max_volumetric_flow": 32.0,  # mm^3/s
        "bed_temp_limit": 120.0,
        "hotend_temp_limit": 300.0
    },
    "Ender 3 V3 KE": {
        "name": "Ender 3 V3 KE",
        "build_volume": {"x": 220.0, "y": 220.0, "z": 240.0},
        "nozzle_diameters": [0.4, 0.6],
        "max_acceleration": 8000.0,
        "tpu_compatible": True,
        "extruder_type": "direct_drive",
        "max_volumetric_flow": 24.0,
        "bed_temp_limit": 100.0,
        "hotend_temp_limit": 300.0
    },
    "Creality K1C": {
        "name": "Creality K1C",
        "build_volume": {"x": 220.0, "y": 220.0, "z": 250.0},
        "nozzle_diameters": [0.4, 0.6],
        "max_acceleration": 20000.0,
        "tpu_compatible": True,
        "extruder_type": "direct_drive",
        "max_volumetric_flow": 32.0,
        "bed_temp_limit": 100.0,
        "hotend_temp_limit": 300.0
    },
    "Creality CR Series": {
        "name": "Creality CR Series",
        "build_volume": {"x": 300.0, "y": 300.0, "z": 400.0},
        "nozzle_diameters": [0.4, 0.6, 0.8],
        "max_acceleration": 2500.0,
        "tpu_compatible": False,  # Bowden tubes have issues with soft TPU
        "extruder_type": "bowden",
        "max_volumetric_flow": 15.0,
        "bed_temp_limit": 100.0,
        "hotend_temp_limit": 260.0
    }
}

def get_printer_profile(printer_name: str) -> dict:
    """
    Retrieves the hardware constraint profile for the selected printer.
    """
    return PRINTER_DATABASE.get(printer_name, PRINTER_DATABASE["Creality K1 Max"])

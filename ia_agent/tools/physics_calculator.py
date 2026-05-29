import math
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

class PhysicsCalculator:
    # Baseline hardcoded fallback densities
    MATERIAL_DENSITIES = {
        "pla": 1.24,
        "tpu": 1.20,
        "abs": 1.04,
        "petg": 1.27,
        "carbon-pla": 1.20,
        "nylon": 1.15
    }

    # Load custom densities from material_profiles.json to keep them synchronized
    _profiles_path = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/data/material_profiles.json")
    if _profiles_path.exists():
        try:
            with open(_profiles_path, "r", encoding="utf-8") as _f:
                _profiles = json.load(_f)
                for _mat, _data in _profiles.items():
                    if "density_g_cm3" in _data:
                        MATERIAL_DENSITIES[_mat.lower()] = float(_data["density_g_cm3"])
        except Exception as _e:
            print(f"[PhysicsCalculator] Error dynamically loading material densities from JSON: {_e}")

    @staticmethod
    def calculate_volume(shape_type: str, dim_x: float, dim_y: float, dim_z: float) -> float:
        """
        Calculates volume in cm^3 of the selected geometry shape.
        Dimensions dim_x, dim_y, dim_z are in cm.
        """
        shape = str(shape_type).lower().strip()
        
        # Cube
        if "cubo" in shape or "cube" in shape:
            return float(dim_x * dim_y * dim_z)
            
        # Sphere
        elif "esfera" in shape or "sphere" in shape:
            radius = dim_x / 2.0
            return float((4.0 / 3.0) * math.pi * (radius ** 3))
            
        # Cylinder
        elif "cilindro" in shape or "cylinder" in shape:
            radius = dim_x / 2.0
            return float(math.pi * (radius ** 2) * dim_z)
            
        # Cone
        elif "cono" in shape or "cone" in shape:
            radius = dim_x / 2.0
            return float((1.0 / 3.0) * math.pi * (radius ** 2) * dim_z)
            
        # Torus
        elif "toro" in shape or "torus" in shape:
            # Major radius R, minor radius r
            R = dim_x / 2.0
            r = dim_z / 4.0 # approximate minor radius
            return float(2.0 * (math.pi ** 2) * R * (r ** 2))
            
        # Pyramid
        elif "piramide" in shape or "pyramid" in shape:
            base_area = dim_x * dim_y
            return float((1.0 / 3.0) * base_area * dim_z)
            
        # Hexagonal Prism
        elif "prisma" in shape or "prism" in shape:
            # Hexagonal base area = 3*sqrt(3)/2 * side^2
            side = dim_x / 2.0
            base_area = (3.0 * math.sqrt(3) / 2.0) * (side ** 2)
            return float(base_area * dim_z)

        # Default Cube fallback
        return float(dim_x * dim_y * dim_z)

    @classmethod
    def estimate_mass(cls, volume_cm3: float, infill_percent: float, material: str, wall_thickness_mm: float) -> float:
        """Estimates total specimen mass in grams considering infill density and shell thickness."""
        mat = str(material).lower().strip()
        density = cls.MATERIAL_DENSITIES.get(mat, 1.24)
        
        # Basic heuristic model:
        # Infill volume fraction
        infill_fraction = infill_percent / 100.0
        
        # Wall/Shell volume fraction heuristic:
        # wall_fraction grows with wall thickness relative to object radius
        wall_fraction = min(0.6, wall_thickness_mm * 0.1)
        
        effective_infill_fraction = infill_fraction * (1.0 - wall_fraction)
        total_fraction = wall_fraction + effective_infill_fraction
        
        # Mass = volume * total_fraction * material_density
        mass = volume_cm3 * total_fraction * density
        
        # Adhesion/raft compensation
        return float(max(1.0, round(mass, 1)))

    @classmethod
    def estimate_print_time(
        cls,
        volume_cm3: float,
        infill_percent: float,
        speed_mm_s: float,
        layer_height_mm: float,
        material: str = "PLA",
        printer_name: str = "Creality K1 Max",
        wall_thickness_mm: float = 1.2,
        pattern: str = "gyroid",
        dim_x: float = None,
        dim_y: float = None,
        dim_z: float = None
    ) -> Dict[str, Any]:
        """
        Calculates print time in minutes using real slicer-like layer-by-layer kinematic simulation.
        Considers perimeters, infill continuous paths, top/bottom layers, speeds by feature,
        Klipper constant acceleration kinematics, travel segments, retractions, and TPU material slowing rules.
        """
        # Resolve dimensions if not provided (assume a cube)
        if dim_x is None or dim_y is None or dim_z is None:
            side_cm = max(1.0, volume_cm3 ** (1.0 / 3.0))
            dim_x = side_cm
            dim_y = side_cm
            dim_z = side_cm

        dim_x_mm = dim_x * 10.0
        dim_y_mm = dim_y * 10.0
        dim_z_mm = dim_z * 10.0

        # Define Printer Profiles
        PRINTER_PROFILES = {
            "Creality K1 Max": {
                "max_speed_mm_s": 600.0,
                "recommended_tpu_speed": 35.0,
                "travel_speed_mm_s": 500.0,
                "acceleration_mm_s2": 20000.0,
                "firmware": "Klipper"
            },
            "Creality Ender 3 V3 KE": {
                "max_speed_mm_s": 500.0,
                "recommended_tpu_speed": 30.0,
                "travel_speed_mm_s": 350.0,
                "acceleration_mm_s2": 8000.0,
                "firmware": "Klipper"
            },
            "Creality K1C": {
                "max_speed_mm_s": 600.0,
                "recommended_tpu_speed": 40.0,
                "travel_speed_mm_s": 500.0,
                "acceleration_mm_s2": 20000.0,
                "firmware": "Klipper"
            }
        }

        # Resolve selected printer profile
        p_profile = PRINTER_PROFILES.get("Creality K1 Max")
        resolved_name = "Creality K1 Max"
        for key in PRINTER_PROFILES:
            if key.lower() in printer_name.lower() or printer_name.lower() in key.lower():
                p_profile = PRINTER_PROFILES[key]
                resolved_name = key
                break

        max_speed = p_profile["max_speed_mm_s"]
        travel_speed = p_profile["travel_speed_mm_s"]
        acceleration = p_profile["acceleration_mm_s2"]
        
        # Pattern complexity factor
        pattern_complexity = {
            "grid": 1.0,
            "lines": 0.92,
            "gyroid": 1.18,
            "triply_periodic": 1.25,
            "schwarz": 1.25,
            "honeycomb": 1.32
        }
        
        pat_key = pattern.lower().strip()
        comp_factor = 1.0
        for pk, val in pattern_complexity.items():
            if pk in pat_key:
                comp_factor = val
                break

        # Dynamic Speeds by Feature (relative to base speed_mm_s)
        base_speed = min(max_speed, max(10.0, float(speed_mm_s)))
        lh = max(0.04, float(layer_height_mm))
        mat = str(material).lower().strip()
        is_tpu = "tpu" in mat

        if is_tpu:
            # TPU 95A strict slicing speed bounds
            outer_wall_speed = max(15.0, min(base_speed * 0.5, 30.0))
            inner_wall_speed = max(20.0, min(base_speed * 0.75, 45.0))
            infill_speed = max(25.0, min(base_speed, 50.0))
            top_surface_speed = max(15.0, min(base_speed * 0.45, 25.0))
            travel_speed_actual = min(travel_speed, 350.0)
            # Reduce effective acceleration due to elastomer flexing
            acceleration_actual = acceleration * 0.4
        else:
            outer_wall_speed = base_speed * 0.6
            inner_wall_speed = base_speed * 0.8
            infill_speed = base_speed
            top_surface_speed = base_speed * 0.5
            travel_speed_actual = travel_speed
            acceleration_actual = acceleration

        # Layers calculation
        total_height_mm = dim_z_mm
        total_layers = max(1, int(total_height_mm / lh))
        
        # 1.0 mm of solid shell at top and bottom
        top_bottom_layers = max(2, int(1.0 / lh) * 2) 
        if top_bottom_layers >= total_layers:
            top_bottom_layers = max(1, total_layers // 2)
        infill_layers = max(0, total_layers - top_bottom_layers)

        # Feature Length calculations (per layer)
        perimeter_mm = 2.0 * (dim_x_mm + dim_y_mm)
        wall_count = max(1, int(wall_thickness_mm / 0.4))
        
        outer_wall_len = perimeter_mm
        inner_wall_len = perimeter_mm * (wall_count - 1)

        # Infill area inside shell walls
        infill_width_mm = max(1.0, dim_x_mm - 2.0 * wall_thickness_mm)
        infill_height_mm = max(1.0, dim_y_mm - 2.0 * wall_thickness_mm)
        infill_area_mm2 = infill_width_mm * infill_height_mm
        
        infill_fraction = max(0.01, min(1.0, infill_percent / 100.0))
        # Solid infill path length (for top/bottom layers)
        solid_infill_len = infill_area_mm2 / 0.45 
        # Sparse infill path length (for infill layers) - calibrated to 1.6 to represent wave spacing
        sparse_infill_len = (infill_area_mm2 * infill_fraction / 1.6) * comp_factor

        # Travel distance estimate per layer
        travel_dist = 4.0 * max(dim_x_mm, dim_y_mm) if infill_percent < 50 else 6.0 * max(dim_x_mm, dim_y_mm)
        
        # Retractions per layer
        retracts_per_layer = 3.0
        if "honeycomb" in pat_key:
            retracts_per_layer = 6.0
        elif "gyroid" in pat_key or "tpms" in pat_key:
            retracts_per_layer = 2.0  # continuous TPMS path reduces retractions

        retraction_time_cost = 0.4 if is_tpu else 0.15

        # Slicers kinematic simulation helper (trapezoidal / triangular profiles)
        def estimate_segment_time(length: float, target_speed: float, accel: float) -> float:
            if length <= 0:
                return 0.0
            v_junction = 8.0 
            if target_speed <= v_junction:
                return length / target_speed
                
            d_accel = (target_speed**2 - v_junction**2) / (2.0 * accel)
            if length >= 2.0 * d_accel:
                t_accel_decel = 2.0 * (target_speed - v_junction) / accel
                t_cruise = (length - 2.0 * d_accel) / target_speed
                return t_accel_decel + t_cruise
            else:
                v_peak = math.sqrt(v_junction**2 + accel * length)
                return 2.0 * (v_peak - v_junction) / accel

        outer_wall_time = 0.0
        inner_wall_time = 0.0
        infill_time = 0.0
        top_bottom_time = 0.0
        travel_time = 0.0
        retraction_time = 0.0

        # Layer-by-layer simulation loop
        for layer in range(total_layers):
            is_first = (layer == 0)
            
            # Outer walls
            speed_ow = 15.0 if is_first else outer_wall_speed
            outer_wall_time += estimate_segment_time(outer_wall_len, speed_ow, acceleration_actual)
            
            # Inner walls
            speed_iw = 20.0 if is_first else inner_wall_speed
            inner_wall_time += estimate_segment_time(inner_wall_len, speed_iw, acceleration_actual)
            
            # Infill vs Solid
            is_solid = (layer < (top_bottom_layers // 2)) or (layer >= (total_layers - top_bottom_layers // 2))
            if is_solid:
                speed_solid = 15.0 if is_first else top_surface_speed
                top_bottom_time += estimate_segment_time(solid_infill_len, speed_solid, acceleration_actual)
            else:
                speed_inf = 20.0 if is_first else infill_speed
                infill_time += estimate_segment_time(sparse_infill_len, speed_inf, acceleration_actual)
                
            # Travel
            speed_tr = min(travel_speed_actual, 100.0) if is_first else travel_speed_actual
            travel_time += estimate_segment_time(travel_dist, speed_tr, acceleration_actual)
            
            # Retractions
            retraction_time += retracts_per_layer * retraction_time_cost

        # Warmup and calibration overhead (minutes)
        firmware_overhead = 300.0
        if "k1 max" in resolved_name.lower():
            firmware_overhead = 480.0
        elif "k1c" in resolved_name.lower():
            firmware_overhead = 420.0
            
        tpu_slowdown = 0.0
        if is_tpu:
            # Cooling time allocation per layer
            cooling_overhead = total_layers * 1.2
            tpu_slowdown = cooling_overhead + (outer_wall_time + inner_wall_time) * 0.15
            
        total_seconds = (
            outer_wall_time + 
            inner_wall_time + 
            infill_time + 
            top_bottom_time + 
            travel_time + 
            retraction_time + 
            tpu_slowdown + 
            firmware_overhead
        )
        
        total_minutes = int(math.ceil(total_seconds / 60.0))
        
        # Proportional Breakdown calculations to match total_minutes exactly
        total_seconds_calculated = (
            outer_wall_time + 
            inner_wall_time + 
            infill_time + 
            top_bottom_time + 
            travel_time + 
            retraction_time + 
            tpu_slowdown + 
            firmware_overhead
        )
        
        if total_seconds_calculated > 0:
            walls_min = int(round(total_minutes * (outer_wall_time + inner_wall_time) / total_seconds_calculated))
            infill_min = int(round(total_minutes * infill_time / total_seconds_calculated))
            travel_min = int(round(total_minutes * travel_time / total_seconds_calculated))
            top_bottom_min = int(round(total_minutes * top_bottom_time / total_seconds_calculated))
            # Put remainder in firmware overhead
            firmware_overhead_min = total_minutes - (walls_min + infill_min + travel_min + top_bottom_min)
        else:
            walls_min = infill_min = travel_min = top_bottom_min = 0
            firmware_overhead_min = total_minutes

        confidence = 0.95 if not is_tpu else 0.88
            
        return {
            "total_minutes": total_minutes,
            "confidence": confidence,
            "breakdown": {
                "walls_min": walls_min,
                "infill_min": infill_min,
                "travel_min": travel_min,
                "top_bottom_min": top_bottom_min,
                "firmware_overhead_min": firmware_overhead_min
            }
        }

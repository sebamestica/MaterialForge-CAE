from typing import Dict, Any

class DesignStateTool:
    @staticmethod
    def format_design_summary(config: Dict[str, Any]) -> str:
        """Formats the active parametric editor design state into a readable summary for the prompt."""
        shape = config.get("shapeType", "Cubo")
        mat = str(config.get("material", "PLA")).upper()
        infill = config.get("infill", 35.0)
        pattern = config.get("pattern", "gyroid")
        
        dim_x = config.get("dimX", 5.0)
        dim_y = config.get("dimY", 5.0)
        dim_z = config.get("dimZ", 5.0)
        
        wall_t = config.get("wallThickness", 1.2)
        cell_size = config.get("cellSize", 3.0)
        cell_t = config.get("cellThickness", 0.6)
        
        layer_h = config.get("layerHeight", 0.20)
        speed = config.get("printSpeed", 50)
        
        applied_force = config.get("appliedForce", 0.0)
        
        summary = (
            f"- Forma geométrica: {shape}\n"
            f"- Dimensiones: {dim_x} x {dim_y} x {dim_z} cm\n"
            f"- Material: {mat}\n"
            f"- Densidad Infill: {infill}%\n"
            f"- Patrón Celular: {pattern}\n"
            f"- Grosor Pared (Shell): {wall_t} mm\n"
            f"- Tamaño Celda: {cell_size} mm\n"
            f"- Grosor Celda: {cell_t} mm\n"
            f"- Altura Capa (Slicer): {layer_h} mm\n"
            f"- Velocidad Impresión: {speed} mm/s\n"
            f"- Fuerza Compresiva Aplicada: {applied_force} N\n"
        )
        return summary

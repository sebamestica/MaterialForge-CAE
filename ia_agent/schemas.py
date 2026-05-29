from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

class ChatMessage(BaseModel):
    role: str
    content: str

class CopilotConfig(BaseModel):
    material: str
    infill: float
    pattern: str
    cellSize: float
    cellThickness: float
    wallThickness: float
    dimX: float
    dimY: float
    dimZ: float
    resolution: str
    layerHeight: float
    printSpeed: float
    viewportMode: str
    
    # Extended fields matching the 3D editor state
    shapeType: Optional[str] = "Cubo"
    geometryId: Optional[str] = "cube-default"
    importedFilename: Optional[str] = None
    scaleX: Optional[float] = 1.0
    scaleY: Optional[float] = 1.0
    scaleZ: Optional[float] = 1.0
    offsetX: Optional[float] = 0.0
    offsetY: Optional[float] = 0.0
    offsetZ: Optional[float] = 0.0
    rotX: Optional[float] = 0.0
    rotY: Optional[float] = 0.0
    rotZ: Optional[float] = 0.0
    
    # Physics load cases
    appliedForce: Optional[float] = 0.0
    forceDirX: Optional[float] = 0.0
    forceDirY: Optional[float] = 0.0
    forceDirZ: Optional[float] = -1.0
    
    # Target objectives & user intent constraints
    targetObjective: Optional[str] = "balance" # strength, energy, lightweight, balance
    testType: Optional[str] = "compression" # compression, tensile
    loadCase: Optional[str] = "static"
    maxMassG: Optional[float] = 100.0
    maxDimCm: Optional[float] = 5.0

class ConfigPatch(BaseModel):
    material: Optional[str] = None
    infill: Optional[float] = None
    pattern: Optional[str] = None
    cellSize: Optional[float] = None
    cellThickness: Optional[float] = None
    wallThickness: Optional[float] = None
    dimX: Optional[float] = None
    dimY: Optional[float] = None
    dimZ: Optional[float] = None
    resolution: Optional[str] = None
    layerHeight: Optional[float] = None
    printSpeed: Optional[float] = None
    viewportMode: Optional[str] = None
    shapeType: Optional[str] = None
    scaleX: Optional[float] = None
    scaleY: Optional[float] = None
    scaleZ: Optional[float] = None
    rotX: Optional[float] = None
    rotY: Optional[float] = None
    rotZ: Optional[float] = None
    forceDirX: Optional[float] = None
    forceDirY: Optional[float] = None
    forceDirZ: Optional[float] = None

class ValidationReport(BaseModel):
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    estimated_volume_cm3: float
    estimated_mass_g: float
    limit_report: Dict[str, Any]

class PredictionReport(BaseModel):
    predicted_max_stress_MPa: Optional[float] = None
    predicted_young_modulus_MPa: Optional[float] = None
    predicted_energy_density_MJ_m3: Optional[float] = None
    predicted_specific_energy_absorption_kJ_kg: Optional[float] = None
    predicted_mass_g: Optional[float] = None
    confidence: float
    confidence_level: str # HIGH, LOW
    warnings: List[str]
    model_used: str

class RetrievedSource(BaseModel):
    source: str
    record_id: Optional[str] = None
    text: str
    confidence: float

class AIAnalysis(BaseModel):
    text: str
    objective_detected: str
    key_findings: str
    mechanical_justification: str

class VariantData(BaseModel):
    id: str
    name: str
    description: str
    score: float
    compression_score: float
    energy_absorption_score: float
    stability_score: float
    printability_score: float
    risk_level: str  # LOW, MEDIUM, HIGH
    estimated_print_time: str
    estimated_mass: str
    pros: List[str] = []
    cons: List[str] = []
    warnings: List[str] = []
    config_patch: ConfigPatch

class CopilotStructuredResponse(BaseModel):
    analysis: AIAnalysis
    variants: List[VariantData]
    recommended_variant: str
    ui_actions: List[str] = ["apply", "compare", "simulate"]

class CopilotChatPayload(BaseModel):
    messages: List[ChatMessage]
    config: CopilotConfig

# --- MANUFACTURING LAYER SCHEMAS ---
class PrinterVolume(BaseModel):
    x: float
    y: float
    z: float

class PrinterHardware(BaseModel):
    nozzle_diameter: float
    max_nozzle_temp: float
    max_bed_temp: float

class PrinterMotionLimits(BaseModel):
    max_speed: float
    recommended_tpu_speed: List[float]
    max_acceleration: float

class PrinterSlicerInfo(BaseModel):
    preferred: str

class PrinterProfile(BaseModel):
    name: str
    manufacturer: str
    firmware: str
    motion_system: str
    build_volume: PrinterVolume
    origin: str
    hardware: PrinterHardware
    motion_limits: PrinterMotionLimits
    materials: List[str]
    slicer: PrinterSlicerInfo
    manufacturing_constraints: List[str]
    tpu_rules: List[str]
    supported_exports: List[str]

class ManufacturingValidationRequest(BaseModel):
    printer_name: str
    config: CopilotConfig

class ManufacturingValidationReport(BaseModel):
    is_manufacturable: bool
    errors: List[str]
    warnings: List[str]
    tpu_safety_score: float  # 0 to 100
    recommendations: List[str]


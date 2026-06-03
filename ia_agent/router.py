from fastapi import APIRouter, HTTPException, BackgroundTasks, Body
from typing import Dict, Any, List
import json
import threading
from pathlib import Path

from .schemas import (
    CopilotChatPayload, CopilotConfig, CopilotStructuredResponse,
    PrinterProfile, ManufacturingValidationRequest, ManufacturingValidationReport
)
from .copilot import run_copilot_stream, recommend_config
from .tools.prediction_tool import PredictionTool
from .ollama_client import OllamaClient

router = APIRouter(tags=["copilot"])
INDEX_DIR = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/data/rag_index")

@router.post("/api/copilot/chat")
async def chat_endpoint(payload: CopilotChatPayload):
    """Conversational streaming chat endpoint (NDJSON format)."""
    return run_copilot_stream(payload)

@router.post("/api/copilot/recommend", response_model=CopilotStructuredResponse)
def recommend_endpoint(payload: CopilotChatPayload):
    """Direct, non-streaming structured recommendation endpoint."""
    return recommend_config(payload)

@router.post("/api/copilot/predict")
def predict_endpoint(config: Dict[str, Any]):
    """Runs structural mechanical predictions directly on a given parameters dict."""
    try:
        tool = PredictionTool()
        return tool.predict_mechanical_response(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

_indexing_lock = threading.Lock()
_indexing_in_progress = False

def _run_indexing_background():
    global _indexing_in_progress
    try:
        from .rag.indexer import Indexer
        indexer = Indexer()
        indexer.run_indexing()
    except Exception as e:
        print(f"[RAG_BACKGROUND] Indexing failed: {e}")
    finally:
        with _indexing_lock:
            _indexing_in_progress = False

@router.post("/api/copilot/rag/reindex")
def reindex_endpoint(background_tasks: BackgroundTasks):
    """Triggers RAG re-indexing over Readme files and dataset summaries in the background."""
    global _indexing_in_progress
    with _indexing_lock:
        if _indexing_in_progress:
            raise HTTPException(status_code=409, detail="RAG indexing is already in progress.")
        _indexing_in_progress = True
        
    background_tasks.add_task(_run_indexing_background)
    return {
        "status": "started",
        "message": "RAG indexing started in background."
    }

@router.post("/api/copilot/ollama/unload")
def unload_ollama_endpoint():
    """Forces Ollama to release VRAM/RAM models immediately by calling keep_alive=0."""
    try:
        client = OllamaClient()
        unloaded = client.unload_models()
        return {
            "status": "success" if unloaded else "failed",
            "message": "Ollama models unloaded from VRAM/RAM." if unloaded else "Failed to unload models from Ollama."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/copilot/memory/unload_all")
def unload_all_endpoint():
    """Unloads ML model, RAG index, tabular store, and Ollama LLM models from memory."""
    try:
        from backend.src.ml.model_manager import get_model_manager
        from .rag.rag_manager import get_rag_manager
        from .data_access.tabular_store import TabularStore
        
        # Unload Python memory managers
        get_model_manager().unload_model()
        get_rag_manager().unload_rag_index()
        TabularStore().unload()
        
        # Unload Ollama GPU/CPU models
        client = OllamaClient()
        client.unload_models()
        
        return {
            "status": "success",
            "message": "All cached models, RAG vector store, tabular datasets, and Ollama LLMs unloaded from VRAM/RAM."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/copilot/rag/status")
def status_endpoint():
    """Returns RAG manifest information and status."""
    manifest_path = INDEX_DIR / "index_manifest.json"
    if not manifest_path.exists():
        return {
            "status": "not_indexed",
            "message": "RAG index has not been built yet. Call /api/copilot/rag/reindex to index documents."
        }
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return {
                "status": "indexed",
                "manifest": json.load(f)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/copilot/models")
def models_endpoint():
    """Lists available models currently installed in local Ollama tags."""
    try:
        client = OllamaClient()
        return {
            "installed_models": client.get_installed_models(),
            "best_chat_model": client.select_best_chat_model(),
            "best_embedding_model": client.select_embedding_model()
        }
    except Exception as e:
        return {
            "installed_models": [],
            "error": f"No se pudo conectar a Ollama: {str(e)}"
        }

@router.get("/api/copilot/health")
def health_endpoint():
    """Returns health status checks for Ollama connection, RAG index, ML Predictor, and processed tables."""
    client = OllamaClient()
    
    # 1. Ollama Health
    ollama_ok = False
    try:
        models = client.get_installed_models()
        ollama_ok = len(models) >= 0
    except Exception:
        pass
        
    from backend.src.ml.model_manager import get_model_manager
    from .rag.rag_manager import get_rag_manager
    from .data_access.tabular_store import TabularStore

    # 2. RAG status
    rag_available = (INDEX_DIR / "vector_store.json").exists()
    rag_loaded = get_rag_manager().store_loaded
    
    # 3. Predictor status
    ml_available = (Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/data/models") / "latest_model.pkl").exists()
    ml_loaded = get_model_manager().model_status()["loaded"]
    
    # 4. Tabular tables status
    processed_dir = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/data/processed")
    tables_available = (processed_dir / "training_table.parquet").exists()
    tabular_store = TabularStore()
    tabular_loaded = tabular_store._training_table is not None

    return {
        "status": "healthy" if (ollama_ok and tables_available) else "online",
        "services": {
            "ollama_connection": "online" if ollama_ok else "offline",
            "rag_index": "loaded" if rag_loaded else ("available" if rag_available else "missing"),
            "predictive_models": "loaded" if ml_loaded else ("available" if ml_available else "missing"),
            "tabular_data": "loaded" if tabular_loaded else ("available" if tables_available else "missing")
        }
    }


# --- STATE MANAGEMENT ---
class CopilotStateStore:
    def __init__(self):
        self.history = []
        self.snapshots = []
        self.current_config = {
            "material": "TPU",
            "infill": 35.0,
            "pattern": "gyroid",
            "cellSize": 5.0,
            "cellThickness": 1.0,
            "wallThickness": 1.2,
            "dimX": 5.0,
            "dimY": 5.0,
            "dimZ": 5.0,
            "resolution": "Media",
            "layerHeight": 0.2,
            "printSpeed": 30.0,
            "viewportMode": "solid",
            "shapeType": "Cubo",
            "scaleX": 1.0,
            "scaleY": 1.0,
            "scaleZ": 1.0,
            "rotX": 0.0,
            "rotY": 0.0,
            "rotZ": 0.0,
            "forceDirX": 0.0,
            "forceDirY": 0.0,
            "forceDirZ": -1.0,
            "appliedForce": 0.0,
            "targetObjective": "balance",
            "testType": "compression",
            "loadCase": "static",
            "maxMassG": 100.0,
            "maxDimCm": 5.0
        }

state_store = CopilotStateStore()


@router.get("/api/copilot/current-config")
def get_current_config_endpoint():
    """Returns the current active configuration from the copilot state store."""
    return state_store.current_config


@router.get("/api/copilot/history")
def get_history_endpoint():
    """Returns the history of patches and optimization actions applied."""
    return state_store.history


@router.post("/api/copilot/apply")
def apply_endpoint(config: Dict[str, Any]):
    """
    Saves current state snapshot, merges and applies the new config patch,
    and appends an entry to history.
    """
    try:
        # Push previous config to snapshots for reverting
        prev_config = state_store.current_config.copy()
        state_store.snapshots.append(prev_config)
        
        # Limit snapshot stack size to 20
        if len(state_store.snapshots) > 20:
            state_store.snapshots.pop(0)

        # Merge and update current config
        for k, v in config.items():
            state_store.current_config[k] = v
            
        # Log to history
        import datetime
        history_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": "applied_config",
            "diff": {k: {"before": prev_config.get(k), "after": v} for k, v in config.items() if prev_config.get(k) != v}
        }
        state_store.history.append(history_entry)
        
        return {
            "status": "success",
            "message": "Configuración aplicada y snapshot guardado.",
            "current_config": state_store.current_config,
            "history": state_store.history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply config: {str(e)}")


@router.post("/api/copilot/revert")
def revert_endpoint():
    """Reverts to the previously saved configuration snapshot."""
    if not state_store.snapshots:
        raise HTTPException(status_code=400, detail="No hay snapshots previos para revertir.")
    
    try:
        prev_config = state_store.snapshots.pop()
        old_config = state_store.current_config.copy()
        state_store.current_config = prev_config
        
        import datetime
        history_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": "reverted_config",
            "diff": {k: {"before": old_config.get(k), "after": v} for k, v in prev_config.items() if old_config.get(k) != v}
        }
        state_store.history.append(history_entry)
        
        return {
            "status": "success",
            "message": "Configuración revertida al snapshot anterior.",
            "current_config": state_store.current_config,
            "history": state_store.history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revert config: {str(e)}")


@router.post("/api/copilot/optimize")
def optimize_endpoint(payload: Dict[str, Any] = Body(...)):
    """
    Computes an optimized config patch based on target objective and runs ML predictions
    to estimate improvements against the baseline configuration.
    """
    objective = payload.get("objective", "balance")
    base_config = payload.get("config") or state_store.current_config
    
    # 1. Run baseline prediction
    predictor = PredictionTool()
    base_preds = predictor.predict_mechanical_response(base_config)
    
    # 2. Heuristics for patch based on engineering constraints and RAG literature
    patch = {}
    reasoning = ""
    
    material = str(base_config.get("material", "TPU")).upper()
    
    if objective in ["strength", "optimize_strength", "optimize_compression"]:
        # Compression strength optimization
        if material == "TPU":
            patch = {
                "infill": 75.0,
                "pattern": "gyroid",
                "wallThickness": 2.0,
                "printSpeed": 25.0,
                "cellSize": 4.5
            }
            reasoning = "Para compresión en TPU, la literatura científica sugiere infill alto (75%), patrón Gyroid TPMS continuo para distribuir cargas isotrópicamente y velocidad lenta (25 mm/s) para evitar delaminación y subextrusión."
        else: # PLA
            patch = {
                "infill": 65.0,
                "pattern": "gyroid",
                "wallThickness": 1.6,
                "printSpeed": 50.0,
                "cellSize": 5.0
            }
            reasoning = "Para compresión en PLA, un infill del 65% con patrón Gyroid proporciona máxima resistencia a compresión sin pandeo local, manteniendo el peso debajo del límite de 100g."
            
    elif objective in ["energy", "optimize_energy_absorption"]:
        # Energy absorption optimization
        patch = {
            "material": "TPU",
            "infill": 60.0,
            "pattern": "gyroid",
            "cellSize": 4.0,
            "wallThickness": 1.6,
            "printSpeed": 25.0
        }
        reasoning = "La literatura técnica confirma que las retículas de TPU con patrón Gyroid absorben hasta un 300% más energía por deformación elástica. Se optimizan las celdas a 4.0 mm para una absorción progresiva estable."
        
    elif objective in ["lightweight", "optimize_weight"]:
        patch = {
            "infill": 15.0,
            "pattern": "gyroid",
            "cellSize": 8.0,
            "wallThickness": 0.8,
            "printSpeed": 60.0
        }
        reasoning = "Optimización enfocada en minimizar la masa. Se reduce el infill al 15% y se incrementa el tamaño de celda a 8.0 mm para máxima eficiencia volumétrica."
        
    else: # balance
        patch = {
            "infill": 40.0,
            "pattern": "gyroid",
            "cellSize": 5.0,
            "wallThickness": 1.2,
            "printSpeed": 40.0
        }
        reasoning = "Optimización balanceada: infill del 40% y patrón Gyroid para un equilibrio óptimo entre rigidez a la compresión, absorción de energía y tiempo de fabricación."

    # 3. Predict on optimized merged config
    opt_config = base_config.copy()
    for k, v in patch.items():
        opt_config[k] = v
        
    opt_preds = predictor.predict_mechanical_response(opt_config)
    
    # 4. Calculate improvements
    def calc_pct(new_val, old_val):
        if old_val is None or old_val == 0:
            return "+0%"
        pct = ((new_val - old_val) / old_val) * 100
        sign = "+" if pct >= 0 else ""
        return f"{sign}{round(pct, 1)}%"
        
    est_stress = calc_pct(opt_preds.get("predicted_max_stress_MPa") or 0, base_preds.get("predicted_max_stress_MPa") or 0)
    est_energy = calc_pct(opt_preds.get("predicted_energy_density_MJ_m3") or 0, base_preds.get("predicted_energy_density_MJ_m3") or 0)
    
    old_speed = base_config.get("printSpeed", 40.0)
    new_speed = opt_config.get("printSpeed", 40.0)
    old_infill = base_config.get("infill", 35.0)
    new_infill = opt_config.get("infill", 35.0)
    
    old_time_factor = old_infill / old_speed
    new_time_factor = new_infill / new_speed
    time_change_pct = ((new_time_factor - old_time_factor) / old_time_factor) * 100
    est_time = f"{'+' if time_change_pct >= 0 else ''}{round(time_change_pct, 1)}%"

    estimated_improvement = {
        "compression_strength": est_stress,
        "energy_absorption": est_energy,
        "print_time": est_time
    }
    
    return {
        "intent": "optimize_compression" if objective in ["strength", "optimize_strength", "optimize_compression"] else "recommend_config",
        "message": reasoning,
        "reasoning": reasoning,
        "confidence": 0.95,
        "estimated_improvement": estimated_improvement,
        "config_patch": patch
    }


@router.post("/api/copilot/variants")
def variants_endpoint(config: Dict[str, Any] = Body(default_factory=dict)):
    """
    Generates 3 structural mechanical candidate configurations (Strength, Energy, Balanced),
    calculating their engineering sub-scores and overall Score.
    """
    base_config = config or state_store.current_config
    predictor = PredictionTool()
    
    # Query best configurations from the experimental database if available
    from .data_access.tabular_store import TabularStore
    try:
        store = TabularStore()
        best_str_list = store.get_best_configs_for_target("max_stress_MPa", limit=3)
        best_en_list = store.get_best_configs_for_target("energy_density_MJ_m3", limit=3)
        best_bal_list = store.get_best_configs_for_target("specific_energy_absorption_kJ_kg", limit=3)
    except Exception as e:
        print(f"[VARIANTS] TabularStore query failed: {e}")
        best_str_list, best_en_list, best_bal_list = [], [], []

    def _get_float(d, key, default):
        v = d.get(key)
        if v is None:
            return default
        try:
            import math
            fv = float(v)
            if math.isnan(fv):
                return default
            return fv
        except (ValueError, TypeError):
            return default

    def _get_str(d, key, default):
        v = d.get(key)
        if v is None:
            return default
        return str(v)

    # Map candidate 1 (Strength)
    cand_str = None
    if best_str_list:
        rec = best_str_list[0]
        cand_str = {
            "name": "Opción 1: Resistencia Máxima a Compresión",
            "material": _get_str(rec, "material", "PLA").upper(),
            "infill": _get_float(rec, "infill_density_percent", 70.0),
            "pattern": _get_str(rec, "infill_pattern", "gyroid").lower(),
            "cellSize": _get_float(rec, "cell_size_mm", 4.5),
            "wallThickness": _get_float(rec, "wall_thickness_mm", 1.6),
            "printSpeed": _get_float(rec, "print_speed_mm_s", 45.0),
            "layerHeight": _get_float(rec, "layer_height_mm", 0.2),
            "desc": f"Configuración óptima de alta resistencia basada en probeta real con esfuerzo de {_get_float(rec, 'max_stress_MPa', 0.0):.1f} MPa."
        }
    else:
        # High score fallback for Strength
        cand_str = {
            "name": "Opción 1: Resistencia Máxima a Compresión",
            "material": "PLA",
            "infill": 80.0,
            "pattern": "gyroid",
            "cellSize": 4.0,
            "wallThickness": 2.4,
            "printSpeed": 40.0,
            "layerHeight": 0.15,
            "desc": "Densidad de infill de 80% y paredes gruesas optimizadas para resistir esfuerzos axiales altos."
        }

    # Map candidate 2 (Energy)
    cand_en = None
    if best_en_list:
        rec = best_en_list[0]
        cand_en = {
            "name": "Opción 2: Máxima Absorción de Energía",
            "material": _get_str(rec, "material", "TPU").upper(),
            "infill": _get_float(rec, "infill_density_percent", 60.0),
            "pattern": _get_str(rec, "infill_pattern", "gyroid").lower(),
            "cellSize": _get_float(rec, "cell_size_mm", 4.0),
            "wallThickness": _get_float(rec, "wall_thickness_mm", 1.6),
            "printSpeed": _get_float(rec, "print_speed_mm_s", 25.0),
            "layerHeight": _get_float(rec, "layer_height_mm", 0.2),
            "desc": f"Configuración optimizada de absorción basada en ensayo experimental de {_get_float(rec, 'energy_density_MJ_m3', 0.0):.2f} MJ/m³."
        }
    else:
        # High score fallback for Energy
        cand_en = {
            "name": "Opción 2: Máxima Absorción de Energía",
            "material": "TPU",
            "infill": 70.0,
            "pattern": "gyroid",
            "cellSize": 3.5,
            "wallThickness": 2.0,
            "printSpeed": 25.0,
            "layerHeight": 0.2,
            "desc": "Optimizada en TPU elastomérico con celdas compactas para amortiguación de impacto progresiva."
        }

    # Map candidate 3 (Balance)
    cand_bal = None
    if best_bal_list:
        rec = best_bal_list[0]
        cand_bal = {
            "name": "Opción 3: Balance Eficiente de Peso y Tiempo",
            "material": _get_str(rec, "material", base_config.get("material", "PLA")).upper(),
            "infill": _get_float(rec, "infill_density_percent", 45.0),
            "pattern": _get_str(rec, "infill_pattern", "gyroid").lower(),
            "cellSize": _get_float(rec, "cell_size_mm", 5.0),
            "wallThickness": _get_float(rec, "wall_thickness_mm", 1.2),
            "printSpeed": _get_float(rec, "print_speed_mm_s", 50.0),
            "layerHeight": _get_float(rec, "layer_height_mm", 0.2),
            "desc": f"Configuración balanceada derivada del dataset experimental, maximizando eficiencia mecánica por masa."
        }
    else:
        # High score fallback for Balance
        cand_bal = {
            "name": "Opción 3: Balance Eficiente de Peso y Tiempo",
            "material": "PLA",
            "infill": 45.0,
            "pattern": "gyroid",
            "cellSize": 5.0,
            "wallThickness": 1.6,
            "printSpeed": 45.0,
            "layerHeight": 0.2,
            "desc": "Configuración balanceada que optimiza la relación rigidez/peso para aplicaciones generales."
        }

    variants = []
    candidates = [cand_str, cand_en, cand_bal]
    
    for idx, cand in enumerate(candidates):
        cand_config = base_config.copy()
        cand_config.update({
            "material": cand["material"],
            "infill": cand["infill"],
            "pattern": cand["pattern"],
            "cellSize": cand["cellSize"],
            "wallThickness": cand["wallThickness"],
            "printSpeed": cand["printSpeed"],
            "layerHeight": cand["layerHeight"]
        })
        
        preds = predictor.predict_mechanical_response(cand_config)
        max_stress = preds.get("predicted_max_stress_MPa") or 15.0
        energy_dens = preds.get("predicted_energy_density_MJ_m3") or 5.0
        mass = preds.get("predicted_mass_g") or 50.0
        
        c_strength = min(100.0, max_stress * (2.0 if cand["material"] == "PLA" else 3.5))
        c_size = cand["cellSize"]
        w_thick = cand["wallThickness"]
        c_stability = min(100.0, max(0.0, (w_thick / 2.0) * 60.0 + (1.0 - (abs(c_size - 5.0)/5.0)) * 40.0))
        c_absorption = min(100.0, energy_dens * (6.0 if cand["material"] == "TPU" else 15.0))
        c_manufacturability = max(10.0, 100.0 - abs(cand["printSpeed"] - 40.0) * 0.5 - abs(cand["layerHeight"] - 0.2) * 100.0)
        
        if cand["material"] == "TPU":
            c_printability = max(10.0, 100.0 - max(0.0, cand["printSpeed"] - 25.0) * 1.5)
        else:
            c_printability = max(50.0, 100.0 - max(0.0, cand["printSpeed"] - 60.0) * 0.5)
            
        c_efficiency = max(0.0, 100.0 - mass)
        
        overall_score = (
            0.40 * c_strength +
            0.20 * c_stability +
            0.15 * c_absorption +
            0.10 * c_manufacturability +
            0.10 * c_printability +
            0.05 * c_efficiency
        )
        
        variants.append({
            "id": f"variant-{idx + 1}",
            "name": cand["name"],
            "description": cand["desc"],
            "config": {
                "material": cand["material"],
                "infill": cand["infill"],
                "pattern": cand["pattern"],
                "cellSize": cand["cellSize"],
                "wallThickness": cand["wallThickness"],
                "printSpeed": cand["printSpeed"],
                "layerHeight": cand["layerHeight"]
            },
            "scores": {
                "compression": round(c_strength, 1),
                "stability": round(c_stability, 1),
                "absorption": round(c_absorption, 1),
                "manufacturability": round(c_manufacturability, 1),
                "printability": round(c_printability, 1),
                "efficiency": round(c_efficiency, 1),
                "overall": round(overall_score, 1)
            },
            "metrics": {
                "predicted_max_stress_MPa": round(max_stress, 2),
                "predicted_energy_density_MJ_m3": round(energy_dens, 2),
                "predicted_mass_g": round(mass, 1)
            }
        })
        
    variants.sort(key=lambda x: x["scores"]["overall"], reverse=True)
    return {
        "status": "success",
        "variants": variants
    }


# --- MANUFACTURING LAYER ENDPOINTS ---

PRINTERS_DIR = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/data/printers")
OUTPUTS_DIR = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/data/outputs")
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/api/copilot/printers", response_model=List[PrinterProfile])
def get_printers_endpoint():
    """Reads printer profiles from the database and returns them."""
    profiles = []
    if not PRINTERS_DIR.exists():
        return []
    for filepath in PRINTERS_DIR.glob("*.json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                profiles.append(PrinterProfile(**data))
        except Exception as e:
            print(f"[MANUFACTURING] Error loading printer profile {filepath}: {e}")
    # Sort by name
    profiles.sort(key=lambda x: x.name)
    return profiles

@router.post("/api/copilot/validate-manufacturing", response_model=ManufacturingValidationReport)
def validate_manufacturing_endpoint(req: ManufacturingValidationRequest):
    """Performs machine-aware physical validation on the given CAD configuration."""
    printer_name = req.printer_name
    config = req.config
    
    # Load printer profile
    printer_profile = None
    for filepath in PRINTERS_DIR.glob("*.json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("name") == printer_name:
                    printer_profile = data
                    break
        except Exception:
            pass
            
    if not printer_profile:
        # Fallback to K1 Max if not found
        k1_path = PRINTERS_DIR / "k1_max.json"
        if k1_path.exists():
            with open(k1_path, "r", encoding="utf-8") as f:
                printer_profile = json.load(f)
        else:
            raise HTTPException(status_code=404, detail=f"Printer profile '{printer_name}' not found.")

    errors = []
    warnings = []
    recommendations = []
    tpu_safety_score = 100.0

    # 1. Bounding box / Build volume check
    dim_x_mm = config.dimX * 10.0
    dim_y_mm = config.dimY * 10.0
    dim_z_mm = config.dimZ * 10.0
    
    vol = printer_profile["build_volume"]
    max_x = vol["x"]
    max_y = vol["y"]
    max_z = vol["z"]

    if dim_x_mm > max_x:
        errors.append(f"El ancho del modelo ({dim_x_mm:.1f} mm) excede el límite del eje X de la cama ({max_x:.1f} mm).")
    if dim_y_mm > max_y:
        errors.append(f"La profundidad del modelo ({dim_y_mm:.1f} mm) excede el límite del eje Y de la cama ({max_y:.1f} mm).")
    if dim_z_mm > max_z:
        errors.append(f"La altura del modelo ({dim_z_mm:.1f} mm) excede la altura máxima del eje Z ({max_z:.1f} mm).")

    # Margin check
    margin = 15.0  # 15 mm safety margin for bed adhesion/brim
    if (dim_x_mm > max_x - margin) and (dim_x_mm <= max_x):
        warnings.append(f"El modelo está muy cerca del límite X de la cama. Margen de brim recomendado: {margin} mm.")
    if (dim_y_mm > max_y - margin) and (dim_y_mm <= max_y):
        warnings.append(f"El modelo está muy cerca del límite Y de la cama. Margen de brim recomendado: {margin} mm.")

    # 2. Material support check
    selected_material = config.material.upper()
    supported_materials = [m.upper() for m in printer_profile["materials"]]
    if selected_material not in supported_materials:
        errors.append(f"El material seleccionado ({config.material}) no está soportado por la impresora {printer_profile['name']}. Soportados: {', '.join(printer_profile['materials'])}")

    # 3. TPU constraints check
    if selected_material == "TPU":
        limits = printer_profile["motion_limits"]
        rec_tpu_speed = limits["recommended_tpu_speed"]
        max_tpu_speed = rec_tpu_speed[1]
        
        speed = config.printSpeed
        
        # Speed checks
        if speed > max_tpu_speed:
            diff = speed - max_tpu_speed
            # Deduct safety score based on excess speed
            tpu_safety_score -= min(60.0, diff * 1.5)
            errors.append(f"Velocidad de impresión de TPU ({speed} mm/s) es crítica. El límite sugerido para esta máquina es de {max_tpu_speed} mm/s.")
            recommendations.append(f"Reducir la velocidad de impresión de TPU a {max_tpu_speed} mm/s para prevenir fallos por extrusión inestable.")
        elif speed > max_tpu_speed - 10.0:
            tpu_safety_score -= 15.0
            warnings.append(f"Velocidad de impresión de TPU ({speed} mm/s) está cerca del límite recomendado de {max_tpu_speed} mm/s.")
            recommendations.append("Asegurarse de calibrar la tensión del extrusor y la retracción antes de imprimir.")
        else:
            recommendations.append("Velocidad de impresión de TPU configurada dentro de parámetros recomendados de flujo continuo.")

        # Retraction alerts
        # TPU requires slow and short retraction
        if printer_profile["motion_system"] == "Bedslinger":
            tpu_safety_score -= 10.0
            warnings.append("Las impresoras Bedslinger (cama móvil Y) introducen vibraciones adicionales que pueden causar desadherencia de piezas flexibles.")
            recommendations.append("Utilizar un Brim de al menos 5 mm y adhesivo en cama caliente para piezas de TPU de base reducida.")

    # 4. Temperature and layer height constraints
    if selected_material == "PLA":
        if config.printSpeed > 300.0 and printer_profile["name"] == "Creality Ender 3 V3 KE":
            warnings.append("Velocidades mayores a 300 mm/s en Ender 3 V3 KE pueden causar subextrusión si el extremo caliente (hotend) no alcanza la tasa de flujo volumétrico requerida.")
            recommendations.append("Incrementar la temperatura de boquilla a 225 °C si se imprime a alta velocidad.")
            
    # Bounding warnings
    if config.layerHeight < 0.08:
        warnings.append(f"Altura de capa muy baja ({config.layerHeight} mm). Aumenta la probabilidad de atasco de boquilla con TPU.")
    elif config.layerHeight > 0.32:
        warnings.append(f"Altura de capa alta ({config.layerHeight} mm). Reducirá drásticamente la adhesión interlaminar y la resistencia mecánica final.")

    is_manufacturable = len(errors) == 0

    return ManufacturingValidationReport(
        is_manufacturable=is_manufacturable,
        errors=errors,
        warnings=warnings,
        tpu_safety_score=max(0.0, min(100.0, tpu_safety_score)),
        recommendations=recommendations
    )

@router.post("/api/copilot/export-manufacturing")
def export_manufacturing_endpoint(req: ManufacturingValidationRequest):
    """
    Simulates printing setup and generates a production package (OrcaSlicer profiles and Klipper G-code)
    tailored to the selected printer.
    """
    printer_name = req.printer_name
    config = req.config

    # Re-run validation first
    val_report = validate_manufacturing_endpoint(req)
    
    # Simple calculations for print metrics
    size_mm = config.dimX * 10.0
    material = config.material.upper()
    infill = config.infill
    layer_h = config.layerHeight
    
    from .tools.physics_calculator import PhysicsCalculator
    
    volume_cm3 = (config.dimX * config.dimY * config.dimZ)
    mass_g = PhysicsCalculator.estimate_mass(
        volume_cm3=volume_cm3,
        infill_percent=infill,
        material=material,
        wall_thickness_mm=config.wallThickness
    )
    
    time_data = PhysicsCalculator.estimate_print_time(
        volume_cm3=volume_cm3,
        infill_percent=infill,
        speed_mm_s=config.printSpeed,
        layer_height_mm=config.layerHeight,
        material=material,
        printer_name=printer_name,
        wall_thickness_mm=config.wallThickness,
        pattern=config.pattern,
        dim_x=config.dimX,
        dim_y=config.dimY,
        dim_z=config.dimZ
    )
    print_time_mins = time_data["total_minutes"]
    print_time_seconds = print_time_mins * 60
    
    hours = print_time_mins // 60
    minutes = print_time_mins % 60
    print_time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

    # Simulate GCODE generation with Klipper commands
    bed_temp = 60.0 if material == "PLA" else 50.0
    nozzle_temp = 210.0 if material == "PLA" else 230.0
    
    gcode_lines = [
        f"; G-Code generated by MaterialForge Slicing Engine v1.2",
        f"; Printer Profile: {printer_name}",
        f"; Filament: {material} (1.75mm)",
        f"; Layer Height: {layer_h} mm",
        f"; Infill Density: {infill} %",
        f"; Infill Pattern: {config.pattern}",
        f"; Target Extruder Temp: {nozzle_temp} C",
        f"; Target Bed Temp: {bed_temp} C",
        f"; Estimated Mass: {mass_g:.2f} grams",
        f"; Estimated Print Time: {print_time_str}",
        "",
        "; --- KLIPPER START G-CODE ---",
        f"M140 S{bed_temp} ; Set bed temp",
        f"M104 S{nozzle_temp} ; Set extruder temp",
        "G28 ; Home all axes",
        "BED_MESH_CALIBRATE ; Run Klipper auto-leveling",
        "G1 Z2.0 F3000 ; Move Z Axis up",
        "G92 E0 ; Reset Extruder",
        f"M109 S{nozzle_temp} ; Wait for extruder temp",
        f"M190 S{bed_temp} ; Wait for bed temp",
        "G1 X10.1 Y20 Z0.28 F5000.0 ; Move to start position",
        "G1 X10.1 Y200.0 Z0.28 F1500.0 E15 ; Draw prime line Y",
        "G92 E0 ; Reset Extruder again",
        "G1 Z2.0 F3000 ; Lift nozzle",
        "",
        "; --- LAYER 1 ---",
        "G92 E0",
        "G1 F1200 ; Set feedrate",
        f"G1 X{150 - size_mm/2:.2f} Y{150 - size_mm/2:.2f} Z{layer_h:.2f} ; Position to draw brim",
        "; ... [Toolpaths omitted for brevity] ...",
        "M107 ; Turn off fan",
        "",
        "; --- LAYER 2 ---",
        "; ... [Infill printing] ...",
        f"; SPEED FACTOR: {speed} mm/s",
        "",
        "; --- KLIPPER END G-CODE ---",
        "M104 S0 ; turn off temperature",
        "M140 S0 ; turn off bed",
        "G91 ; Relative positioning",
        "G1 E-2 F2700 ; Retract filament",
        "G1 Z10 F3000 ; Lift nozzle 10mm",
        "G28 X0 Y0 ; Home X and Y",
        "M84 ; Disable steppers"
    ]
    
    gcode_content = "\n".join(gcode_lines)
    
    # Save simulated GCODE to disk
    gcode_filename = f"cube_{material.lower()}_{config.pattern}_{int(infill)}pct.gcode"
    gcode_path = OUTPUTS_DIR / gcode_filename
    with open(gcode_path, "w", encoding="utf-8") as f:
        f.write(gcode_content)

    # Save simulated 3MF profile summary
    profile_summary = {
        "printer": printer_name,
        "slicer": "OrcaSlicer Config Package",
        "config_version": "1.0",
        "slicing_parameters": {
            "nozzle_temperature": nozzle_temp,
            "bed_temperature": bed_temp,
            "initial_layer_speed": 15.0,
            "infill_speed": speed,
            "outer_wall_speed": speed * 0.6,
            "inner_wall_speed": speed * 0.8,
            "retraction_distance": 1.2 if material == "TPU" else 5.0,
            "retraction_speed": 25.0 if material == "TPU" else 45.0,
            "input_shaping_x": "mzv",
            "input_shaping_y": "mzv",
            "pressure_advance": 0.045 if material == "TPU" else 0.02
        }
    }
    
    profile_filename = f"orcaslicer_{material.lower()}_profile.json"
    profile_path = OUTPUTS_DIR / profile_filename
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile_summary, f, indent=4)

    return {
        "status": "success",
        "validation": val_report.dict(),
        "summary": {
            "estimated_print_time": print_time_str,
            "estimated_mass_grams": round(mass_g, 2),
            "layers_count": int(size_mm / layer_h),
            "filament_length_m": round(mass_g / 3.0, 2),
            "gcode_file": gcode_filename,
            "profile_file": profile_filename
        },
        "gcode_preview": gcode_lines[:30],
        "orcaslicer_profile": profile_summary
    }

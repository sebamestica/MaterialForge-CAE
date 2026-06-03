from typing import Dict, Any, List, Optional
from pathlib import Path

from .context_broker import ContextBroker
from .data_access.tabular_store import TabularStore
from .tools.prediction_tool import PredictionTool
from .tools.domain_guard import DomainGuardTool

class ContextBuilder:
    def __init__(self):
        self.context_broker = ContextBroker()
        self.tabular = TabularStore()
        self.predictor = PredictionTool()
        self.guard = DomainGuardTool()

    def build_context(self, query: str, config: Dict[str, Any], intent: str) -> Dict[str, Any]:
        """
        Retrieves database and literature summaries from ContextBroker, runs predictions,
        validates ranges, runs the multiobjective ConstraintSolver if a load target is detected,
        and compiles the design context.
        """
        # 1. Light Context Broker instead of heavy RAG
        rag_sources = self.context_broker.retrieve_context(query, config, intent, k=5)

        # 2. Tabular similar experiments
        similar_experiments = self.tabular.get_similar_experiments(config, limit=5)

        # 3. Material Summary
        material = config.get("material", "PLA")
        material_summary = self.tabular.get_material_summary(material)

        # 4. Predict mechanical properties using backend model
        pred_report = self.predictor.predict_mechanical_response(config)

        # 5. Check training domain extrapolation using Domain Guard
        guard_warnings, confidence = self.guard.validate_config(config)

        # 6. Run physical ConstraintSolver for structural loads or target mass constraints
        import re
        q = query.lower()
        target_load_kg = 0.0
        max_mass_g = 100.0
        
        # Regex to capture load requirements (e.g., "soportar 500 kg")
        kg_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg|kilo|kilogramo)", q)
        if kg_match:
            target_load_kg = float(kg_match.group(1))
            
        # Regex to capture custom target mass constraints (e.g., "menos de 80g")
        g_match = re.search(r"(?:peso|pesar|menos\s+de|máximo|límite)\s*(\d+(?:\.\d+)?)\s*(?:g|gramo)", q)
        if g_match:
            max_mass_g = float(g_match.group(1))

        optimized_solver_result = None
        if target_load_kg > 0.0 or max_mass_g < 100.0:
            try:
                from backend.src.optimization.ConstraintSolver import ConstraintSolver
                solver = ConstraintSolver()
                size_mm = float(config.get("dimX", 5.0)) * 10.0
                optimized_solver_result = solver.solve(
                    material=material,
                    size_mm=size_mm,
                    target_load_kg=target_load_kg,
                    max_mass_g=max_mass_g,
                    preferred_pattern=config.get("pattern", "gyroid")
                )
            except Exception as e:
                print(f"[ContextBuilder] Error running ConstraintSolver: {e}")

        return {
            "rag_sources": rag_sources,
            "similar_experiments": similar_experiments,
            "material_summary": material_summary,
            "prediction": pred_report,
            "domain_warnings": guard_warnings,
            "domain_confidence": confidence,
            "optimized_solver_result": optimized_solver_result
        }

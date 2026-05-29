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
        validates ranges, and compiles the design context.
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

        return {
            "rag_sources": rag_sources,
            "similar_experiments": similar_experiments,
            "material_summary": material_summary,
            "prediction": pred_report,
            "domain_warnings": guard_warnings,
            "domain_confidence": confidence
        }

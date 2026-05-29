import re
from typing import Dict, Any, List

class IntentRouter:
    @staticmethod
    def classify_intent(query: str) -> Dict[str, Any]:
        """
        Runs a rule-based classification on the user query to detect the objective.
        Returns:
        {
          "intent": str,
          "confidence": float,
          "required_tools": List[str]
        }
        """
        q = query.lower().strip()

        # Optimize for strength
        if any(w in q for w in ["resistencia", "fuerza", "soportar", "cargar", "stress", "tensión", "stiffness", "rigidez"]):
            return {
                "intent": "optimize_strength",
                "confidence": 0.90,
                "required_tools": ["prediction_tool", "config_recommender"]
            }

        # Optimize for energy absorption
        if any(w in q for w in ["absorb", "impacto", "energía", "amortigua", "sea", "choque"]):
            return {
                "intent": "optimize_energy_absorption",
                "confidence": 0.90,
                "required_tools": ["prediction_tool", "config_recommender"]
            }

        # Predict mechanical behavior
        if any(w in q for w in ["predecir", "predic", "simula", "calcula", "estimar"]):
            return {
                "intent": "run_prediction",
                "confidence": 0.85,
                "required_tools": ["prediction_tool", "domain_guard"]
            }

        # Diagnose design failure
        if any(w in q for w in ["falló", "fallo", "colapso", "rompió", "rompe", "rotura", "fractura", "debil"]):
            return {
                "intent": "diagnose_failure",
                "confidence": 0.85,
                "required_tools": ["prediction_tool", "domain_guard"]
            }

        # Compare materials
        if any(w in q for w in ["comparar", "diferencia", "vs", "tpu vs", "pla vs"]):
            return {
                "intent": "compare_materials",
                "confidence": 0.80,
                "required_tools": ["material_lookup"]
            }

        # Recommend configuration
        if any(w in q for w in ["recomendar", "recomienda", "configuracion", "configuración", "sugerir", "sugiere", "cambiar", "ajustar"]):
            return {
                "intent": "recommend_config",
                "confidence": 0.85,
                "required_tools": ["config_recommender"]
            }

        # Explain/General inquiry
        if any(w in q for w in ["explicar", "explica", "qué es", "cómo funciona", "ayuda", "hola", "buenos días"]):
            return {
                "intent": "explain",
                "confidence": 0.80,
                "required_tools": []
            }

        return {
            "intent": "unknown",
            "confidence": 0.50,
            "required_tools": []
        }

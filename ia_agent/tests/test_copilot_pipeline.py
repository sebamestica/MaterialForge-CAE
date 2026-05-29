import unittest
from unittest.mock import MagicMock, patch
import json
from pathlib import Path
from pydantic import ValidationError

from ..schemas import CopilotConfig, ConfigPatch, CopilotStructuredResponse, CopilotChatPayload
from ..validators import validate_config_patch
from ..ollama_client import OllamaClient
from ..prompt_builder import PromptBuilder
from ..response_parser import ResponseParser
from ..tools.prediction_tool import PredictionTool
from ..tools.physics_calculator import PhysicsCalculator
from ..rag.retriever import Retriever
from ..rag.vector_store import SimpleVectorStore

class TestCopilotPipeline(unittest.TestCase):
    def setUp(self):
        # Sample baseline config representing active editor state
        self.current_config = {
            "material": "PLA",
            "infill": 35.0,
            "pattern": "gyroid",
            "cellSize": 3.0,
            "cellThickness": 0.6,
            "wallThickness": 1.2,
            "dimX": 4.0,
            "dimY": 4.0,
            "dimZ": 4.0,
            "resolution": "Alta",
            "layerHeight": 0.20,
            "printSpeed": 50.0,
            "viewportMode": "solid",
            "shapeType": "Cubo"
        }

    # 1. test_no_dimension_above_5cm()
    def test_no_dimension_above_5cm(self):
        patch_data = {"dimX": 8.0} # invalid (> 5.0)
        report = validate_config_patch(self.current_config, patch_data)
        
        # Check dimX is corrected to 5.0
        self.assertEqual(report["corrected_patch"]["dimX"], 5.0)
        self.assertTrue(any("dimX" in w for w in report["warnings"]))

    # 2. test_mass_limit_100g()
    def test_mass_limit_100g(self):
        # Extreme massive cube config: 5x5x5 cm and 100% infill density
        large_patch = {
            "dimX": 5.0,
            "dimY": 5.0,
            "dimZ": 5.0,
            "infill": 100.0,
            "material": "PETG"
        }
        report = validate_config_patch(self.current_config, large_patch)
        
        # Estimated mass = 125 cm3 * 1.0 * 1.27 ~ 158g (> 100g limit)
        self.assertFalse(report["is_valid"])
        self.assertTrue(any("peso" in e or "g" in e for e in report["errors"]))

    # 3. test_invalid_json_is_repaired_or_rejected()
    def test_invalid_json_is_repaired_or_rejected(self):
        # Mock OllamaClient to raise exception on first call (mismatched JSON structure),
        # but return valid payload on repair call.
        client = OllamaClient()
        client.chat_json = MagicMock()
        client.chat_json.side_effect = [
            ValueError("Mismatched JSON format"), # 1st call fails
            {
                "analysis": {
                    "text": "Configuración reparada",
                    "objective_detected": "compression",
                    "key_findings": "reparación",
                    "mechanical_justification": "justificación"
                },
                "variants": [
                    {
                        "id": "variant_A",
                        "name": "Propuesta A",
                        "description": "desc",
                        "score": 92.0,
                        "compression_score": 90.0,
                        "energy_absorption_score": 80.0,
                        "stability_score": 90.0,
                        "printability_score": 80.0,
                        "risk_level": "LOW",
                        "estimated_print_time": "1h",
                        "estimated_mass": "40.0g",
                        "pros": [],
                        "cons": [],
                        "warnings": [],
                        "config_patch": {"material": "TPU", "infill": 40.0}
                    }
                ],
                "recommended_variant": "variant_A",
                "ui_actions": ["apply", "compare"]
            } # 2nd call succeeds
        ]

        parser = ResponseParser(client)
        resp = parser.extract_structured_response(
            conversation_history=[],
            assistant_response="Sugiero usar TPU e infill de 40.",
            current_config=self.current_config,
            context_data={}
        )
        
        self.assertEqual(resp.recommended_variant, "variant_A")
        self.assertEqual(resp.variants[0].config_patch.material, "TPU")
        self.assertEqual(resp.variants[0].config_patch.infill, 40.0)

    # 4. test_rag_returns_limited_context()
    @patch('ia_agent.rag.retriever.SimpleVectorStore')
    @patch('ia_agent.rag.retriever.OllamaEmbeddings')
    def test_rag_returns_limited_context(self, mock_emb, mock_store):
        # Mock retriever similarity search to return many results
        mock_store_inst = mock_store.return_value
        mock_store_inst.load.return_value = True
        mock_store_inst.similarity_search.return_value = [
            ({"chunk_id": f"C-{i}", "text": f"Chunk text {i}", "metadata": {"source_path": "doc.md"}}, 0.90)
            for i in range(20)
        ]
        
        mock_emb_inst = mock_emb.return_value
        mock_emb_inst.embed_query.return_value = [0.1] * 768

        retriever = Retriever()
        results = retriever.retrieve_context("consulta de prueba", self.current_config, "explain", k=5)
        
        # Verify k is respected
        self.assertEqual(len(results), 5)

    # 5. test_csv_full_text_not_in_prompt()
    def test_csv_full_text_not_in_prompt(self):
        context = {
            "similar_experiments": [
                {"specimen_id": "EXP-01", "material": "PLA", "infill_density_percent": 30.0}
            ],
            "rag_sources": []
        }
        
        config_summary = "Forma: Cubo"
        prompt = PromptBuilder.build_system_prompt(config_summary, context)
        
        # Verify prompt is short and doesn't contain full CSV string structures
        self.assertNotIn("unified_materials_database.csv", prompt)
        self.assertTrue(len(prompt) < 4000)

    # 6. test_prediction_tool_handles_missing_model(self):
    def test_prediction_tool_handles_missing_model(self):
        with patch('ia_agent.tools.prediction_tool.PREDICTOR_AVAILABLE', False):
            tool = PredictionTool()
            res = tool.predict_mechanical_response(self.current_config)
            
            # Should fallback to rules, mark confidence as LOW
            self.assertEqual(res["confidence_level"], "LOW")
            self.assertIn("Heuristic", res["model_used"])

    # 7. test_config_patch_schema()
    def test_config_patch_schema(self):
        # Verify all parameters can be validated by ConfigPatch
        patch = ConfigPatch(
            material="PLA",
            infill=40.0,
            pattern="gyroid",
            cellSize=4.0,
            cellThickness=0.8,
            wallThickness=1.6,
            dimX=3.5,
            dimY=3.5,
            dimZ=3.5,
            resolution="Alta",
            layerHeight=0.15,
            printSpeed=60.0
        )
        self.assertEqual(patch.material, "PLA")
        self.assertEqual(patch.infill, 40.0)

    # 8. test_current_config_extended_fields()
    def test_current_config_extended_fields(self):
        # Verify CopilotConfig handles editor state parameters
        config = CopilotConfig(
            material="PLA",
            infill=35.0,
            pattern="gyroid",
            cellSize=3.0,
            cellThickness=0.6,
            wallThickness=1.2,
            dimX=4.0,
            dimY=4.0,
            dimZ=4.0,
            resolution="Alta",
            layerHeight=0.2,
            printSpeed=50.0,
            viewportMode="wireframe",
            shapeType="Esfera",
            scaleX=1.5,
            appliedForce=250.0,
            forceDirZ=-1.0
        )
        self.assertEqual(config.shapeType, "Esfera")
        self.assertEqual(config.scaleX, 1.5)
        self.assertEqual(config.appliedForce, 250.0)

    # 9. test_model_selection_prefers_7b_over_3b()
    def test_model_selection_prefers_7b_over_3b(self):
        client = OllamaClient()
        client.chat_model_override = None
        # Mock tags endpoint returning both 7b and 3b models
        client.get_installed_models = MagicMock(return_value=["qwen2.5-coder:3b", "qwen2.5-coder:7b"])
        
        best = client.select_best_chat_model()
        self.assertEqual(best, "qwen2.5-coder:7b")

    # 10. test_ollama_unavailable_returns_503_clear_error()
    def test_ollama_unavailable_returns_503_clear_error(self):
        client = OllamaClient(base_url="http://invalid-ollama-url:11434")
        
        # Querying models should fail cleanly returning empty tags
        models = client.get_installed_models()
        self.assertEqual(len(models), 0)

        # Triggering inference stream should raise 503 HTTPException
        from fastapi import HTTPException
        payload = CopilotChatPayload(
            messages=[],
            config=CopilotConfig(
                material="PLA", infill=35.0, pattern="gyroid", cellSize=3.0,
                cellThickness=0.6, wallThickness=1.2, dimX=4.0, dimY=4.0, dimZ=4.0,
                resolution="Alta", layerHeight=0.2, printSpeed=50.0, viewportMode="solid"
            )
        )
        
        with patch('ia_agent.copilot.OllamaClient.get_installed_models', return_value=[]):
            with self.assertRaises(HTTPException) as ctx:
                from ..copilot import run_copilot_stream
                run_copilot_stream(payload)
            self.assertEqual(ctx.exception.status_code, 503)

    # 11. test_material_profiles_loading_and_consistency()
    def test_material_profiles_loading_and_consistency(self):
        from ..context_broker import ContextBroker
        broker = ContextBroker()
        
        # Verify material_profiles was loaded successfully
        self.assertIsNotNone(broker.material_profiles)
        self.assertIn("PLA", broker.material_profiles)
        self.assertIn("TPU", broker.material_profiles)
        
        # Verify specific details of TPU profile
        tpu_prof = broker.material_profiles["TPU"]
        self.assertEqual(tpu_prof["full_name"], "Poliuretano Termoplástico (Thermoplastic Polyurethane)")
        self.assertEqual(tpu_prof["density_g_cm3"], 1.20)
        self.assertEqual(tpu_prof["young_modulus_mpa"], 80.0)
        
        # Verify PhysicsCalculator.MATERIAL_DENSITIES loaded dynamically
        self.assertEqual(PhysicsCalculator.MATERIAL_DENSITIES["tpu"], 1.20)
        self.assertEqual(PhysicsCalculator.MATERIAL_DENSITIES["pla"], 1.24)
        
        # Verify context broker formats TPU profile text correctly
        profile_text = broker._get_material_profile_text("TPU")
        self.assertIn("Poliuretano Termoplástico", profile_text)
        self.assertIn("1.2 g/cm³", profile_text)
        self.assertIn("80.0 MPa", profile_text)

if __name__ == "__main__":
    unittest.main()

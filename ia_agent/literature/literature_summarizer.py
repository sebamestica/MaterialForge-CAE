import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# Setup path resolution for ia_agent
BASE_DIR = Path(__file__).parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from ia_agent.ollama_client import OllamaClient

class LiteratureSummarizer:
    def __init__(self):
        self.client = OllamaClient()

    def summarize_literature(self, parsed_data: Dict[str, List[str]]) -> Dict[str, Any]:
        """Summarizes parsed passages using local Ollama model in JSON format."""
        
        # Build prompt for Ollama
        system_instruction = (
            "Eres un asistente científico de MaterialForge. Tu tarea es compilar y sintetizar los fragmentos "
            "de texto de literatura científica provistos para extraer directrices de diseño mecánico, "
            "parámetros de impresión recomendados y heurísticas de optimización para impresión 3D en FDM "
            "(especialmente TPU y estructuras Gyroid/TPMS).\n\n"
            "Debes devolver un objeto JSON con el siguiente esquema exacto (debes respetar los nombres de campos):\n"
            "{\n"
            "  \"materials\": {\n"
            "    \"TPU\": {\n"
            "      \"recommended_nozzle_temp\": [temperatura_min, temperatura_max],\n"
            "      \"recommended_speed\": [velocidad_min, velocidad_max],\n"
            "      \"compression_behavior\": \"resumen de comportamiento bajo compresión\",\n"
            "      \"anisotropy_notes\": \"notas de anisotropía y cómo afecta la orientación\",\n"
            "      \"layer_adhesion_notes\": \"notas sobre la adherencia entre capas y unión\",\n"
            "      \"common_failure_modes\": [\"modo1\", \"modo2\"]\n"
            "    },\n"
            "    \"PLA\": {\n"
            "      \"recommended_nozzle_temp\": [temperatura_min, temperatura_max],\n"
            "      \"recommended_speed\": [velocidad_min, velocidad_max],\n"
            "      \"compression_behavior\": \"resumen de compresión\",\n"
            "      \"anisotropy_notes\": \"notas de anisotropía\",\n"
            "      \"layer_adhesion_notes\": \"notas de adhesión\",\n"
            "      \"common_failure_modes\": [\"modo1\", \"modo2\"]\n"
            "    }\n"
            "  },\n"
            "  \"patterns\": {\n"
            "    \"gyroid\": {\n"
            "      \"advantages\": [\"ventaja1\", \"ventaja2\"],\n"
            "      \"disadvantages\": [\"desventaja1\"],\n"
            "      \"compression_behavior\": [\"nota_compresion1\", \"nota_compresion2\"],\n"
            "      \"energy_absorption\": [\"nota1\", \"nota2\"],\n"
            "      \"recommended_density_range\": [densidad_min_pct, densidad_max_pct]\n"
            "    },\n"
            "    \"honeycomb\": {\n"
            "      \"advantages\": [],\n"
            "      \"disadvantages\": [],\n"
            "      \"compression_behavior\": [],\n"
            "      \"energy_absorption\": [],\n"
            "      \"recommended_density_range\": []\n"
            "    }\n"
            "  },\n"
            "  \"printing_rules\": [\"regla de impresión 1\", \"regla 2\"],\n"
            "  \"simulation_notes\": [\"nota simulación 1\"],\n"
            "  \"optimization_rules\": [\"regla optimización 1\"],\n"
            "  \"manufacturing_constraints\": [\"restricción 1\"]\n"
            "}\n\n"
            "Sintetiza la información de forma precisa. Si no hay suficiente información en los fragmentos "
            "para algún campo, complétalo con tus conocimientos sobre ingeniería de materiales FDM de manera coherente."
        )

        # Collect text fragments
        fragments = []
        for key, paras in parsed_data.items():
            if paras:
                fragments.append(f"=== FRAGMENTOS ASOCIADOS A {key.upper()} ===")
                fragments.extend([f"- {p}" for p in paras[:8]]) # limit to first 8 to avoid context overflow

        text_content = "\n".join(fragments)
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Aquí están los fragmentos de literatura científica para procesar:\n\n{text_content}"}
        ]

        try:
            print("[LiteratureSummarizer] Requesting structured summary from local Ollama...")
            # Query Ollama for structured json
            result = self.client.chat_json(messages, options={"temperature": 0.1})
            if result and ("materials" in result or "printing_rules" in result):
                print("[LiteratureSummarizer] Successfully compiled literature summary via LLM.")
                return result
        except Exception as e:
            print(f"[LiteratureSummarizer] Local LLM chat failed: {e}. Generating rule-based fallback summary.")
        
        return self.generate_fallback_summary(parsed_data)

    def generate_fallback_summary(self, parsed_data: Dict[str, List[str]]) -> Dict[str, Any]:
        """Generates a high-quality scientific summary as a fallback if LLM is unavailable."""
        return {
          "materials": {
            "TPU": {
              "recommended_nozzle_temp": [220, 235],
              "recommended_speed": [20, 35],
              "compression_behavior": "Comportamiento elástico y altamente no lineal. Absorbe energía mediante deformación por flexión/pandeo de las paredes de celda sin fracturarse, mostrando una meseta (plateau) larga y constante antes de la densificación.",
              "anisotropy_notes": "Sufre de anisotropía moderada a alta; las uniones entre capas son el punto débil. Soportará mayor compresión si la carga es perpendicular al esfuerzo y las capas mantienen continuidad vertical.",
              "layer_adhesion_notes": "Mejora significativamente a bajas velocidades (20-35 mm/s) y temperaturas más altas (220-235 °C). Requiere poco o nulo flujo de refrigeración de capa para promover la fusión molecular.",
              "common_failure_modes": [
                "Despegue interlaminar bajo cizallamiento",
                "Pandeo lateral localizado de las paredes delgadas del contorno",
                "Subextrusión y huecos internos debido a velocidad excesiva"
              ]
            },
            "PLA": {
              "recommended_nozzle_temp": [195, 220],
              "recommended_speed": [40, 60],
              "compression_behavior": "Fallo frágil catastrófico tras alcanzar el punto de fluencia máxima. Alta resistencia inicial pero nula disipación viscoplástica bajo cargas de impacto.",
              "anisotropy_notes": "Alta anisotropía. Las capas impresas en dirección del esfuerzo vertical tienden a deslizarse e iniciar la delaminación en ángulos de 45 grados.",
              "layer_adhesion_notes": "Adhesión moderada, facilitada por temperatura y velocidades normales del slicer. Requiere enfriamiento completo de capa.",
              "common_failure_modes": [
                "Fractura frágil por cizallamiento a 45 grados",
                "Delaminación en capas bajo esfuerzo cortante",
                "Pandeo elástico repentino"
              ]
            }
          },
          "patterns": {
            "gyroid": {
              "advantages": [
                "Comportamiento mecánico casi isotrópico",
                "Continuidad tridimensional sin puntos de acumulación de tensiones",
                "Excelente disipación de energía multidireccional"
              ],
              "disadvantages": [
                "Complejidad en el corte y mayor tamaño de archivo GCODE",
                "Mayor susceptibilidad a hilos (stringing) en velocidades altas"
              ],
              "compression_behavior": [
                "Se deforma de manera estable y progresiva sin fallos localizados",
                "Las paredes de la celda experimentan flexión en lugar de estiramiento"
              ],
              "energy_absorption": [
                "Mayor disipación de energía por volumen específico",
                "Curva de deformación suave que mitiga picos de fuerza durante el impacto"
              ],
              "recommended_density_range": [55, 80]
            },
            "honeycomb": {
              "advantages": [
                "Altísima resistencia a compresión pura en el eje vertical (eje Z)",
                "Rigidez específica sobresaliente"
              ],
              "disadvantages": [
                "Gran anisotropía, muy débil frente a esfuerzos en los ejes X/Y",
                "Fallo por pandeo repentino y colapso de las celdas hexagonales"
              ],
              "compression_behavior": [
                "Alta rigidez elástica inicial, seguida de pandeo catastrófico",
                "Las paredes experimentan colapso localizado simultáneo"
              ],
              "energy_absorption": [
                "Eficiencia de absorción de impacto pobre tras el colapso elástico",
                "Baja resiliencia bajo cargas repetidas"
              ],
              "recommended_density_range": [30, 60]
            }
          },
          "printing_rules": [
            "Para filamentos elásticos (TPU), limitar la velocidad a un rango de 20-35 mm/s.",
            "Utilizar temperaturas elevadas de extrusión en TPU (220-235°C) para optimizar la fusión de capas.",
            "Desactivar el ventilador de enfriamiento o mantenerlo a menos de 20% para TPU.",
            "PLA requiere enfriamiento al 100% y velocidades más altas (40-60 mm/s) para estabilidad dimensional."
          ],
          "simulation_notes": [
            "La rigidez del cubo de TPU es altamente no lineal y requiere análisis elástico a grandes deformaciones.",
            "Las interfaces y carcasas (shells) dominan la resistencia al pandeo lateral en geometrías delgadas."
          ],
          "optimization_rules": [
            "Para maximizar la compresión en TPU, favorecer el patrón TPMS Gyroid con infills de 55-80%.",
            "Aumentar el número de perímetros (wall thickness a 1.6-2.4mm) para evitar el pandeo periférico de las caras del cubo.",
            "Usar densidad graduada ( graded density) si es posible para suavizar el impacto en la zona central."
          ],
          "manufacturing_constraints": [
            "Extrusor Direct Drive recomendado para TPU; sistemas Bowden sufren atoramientos.",
            "Grosor mínimo de pared de 0.8 mm (2 pasadas de boquilla) para mantener consistencia física."
          ]
        }

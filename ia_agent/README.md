# MaterialForge AI Copilot Agent (`ia_agent`)

Este directorio contiene la lógica del **Copiloto Científico de IA** para MaterialForge, encapsulado e independiente para su fácil exportación y uso en otros entornos.

El agente está diseñado para interactuar con modelos de lenguaje locales a través de **Ollama**, sirviendo como asistente técnico experto en ingeniería de materiales, diseño en impresión 3D FDM y optimización estructural.

## Características Clave
1. **Detección Automática de Modelos Locales:** Interroga la API de Ollama para seleccionar el mejor modelo de codificación/razonamiento disponible (ej. `qwen2.5-coder:3b`, `llama3.2:3b`, `gemma3`, etc.).
2. **Contexto Experimental Real:** Lee y formatea el archivo `unified_materials_database.csv` del directorio `data/` del proyecto para basar sus sugerencias en ensayos mecánicos reales (fuerza máxima, deformación, módulo de Young, etc.).
3. **Validación de Restricciones Físicas Obligatorias:** El prompt del sistema fuerza al agente a validar y recordar los límites del proyecto:
   - **Dimensiones:** Máximo 5.0 x 5.0 x 5.0 cm (125 cm³).
   - **Masa total:** Máximo 100 gramos.
   - **Libertad de formas:** Cubo, Esfera, Cilindro, Cono, Toro, Pirámide y Prisma Hexagonal.
4. **Respuestas con Recomendación Estructurada (JSON):** Al sugerir mejoras paramétricas, el agente anexa al final de su respuesta un bloque JSON estándar. Este bloque es interpretado automáticamente por el cliente frontend de MaterialForge para aplicar los parámetros al editor interactivo con un solo clic.

---

## Requisitos de Sistema
- **Python 3.10+**
- **Ollama** ejecutándose localmente (`http://localhost:11434`) con algún modelo instalado, por ejemplo:
  ```bash
  ollama run qwen2.5-coder:3b
  # o bien:
  ollama run llama3.2
  ```

### Dependencias Python
El módulo depende de:
```text
fastapi
pydantic
pandas
```

---

## Estructura del Módulo

- `copilot.py`: Implementación del payload de Pydantic, cargador de datos experimentales, prompt del sistema con directrices físicas e invocación streaming a Ollama.
- `__init__.py`: Inicializador del paquete de Python.

---

## Ejemplo de Integración en FastAPI

Puedes importar y usar la lógica del agente directamente en tus rutas HTTP de la siguiente manera:

```python
from fastapi import FastAPI
from ia_agent.copilot import CopilotChatPayload, run_copilot_stream

app = FastAPI()

@app.post("/api/copilot/chat")
async def chat_endpoint(payload: CopilotChatPayload):
    # Retorna un StreamingResponse con formato ndjson
    return run_copilot_stream(payload)
```

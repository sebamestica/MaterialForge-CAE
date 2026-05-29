# Sistema de Análisis y Simulación de Impresión 3D - Backend & Data Science Lab

Este repositorio contiene el núcleo de simulación, modelado mecánico y procesamiento de datos para el estudio de resistencia estructural en probetas impresas en 3D (PLA y TPU).

El sistema utiliza modelos de Machine Learning (como `GradientBoostingRegressor`) entrenados con datos reales de ensayos de compresión para predecir la resistencia de distintas configuraciones de infill y geometrías.

---

## 📁 Estructura General del Proyecto

El proyecto está estructurado como una plataforma CAD/CAE de nivel industrial modular, dividida en un Backend de simulación/ML y un Frontend web en Next.js (React Three Fiber):

```text
├── backend/                             # Servidor FastAPI de Inferencia y Geometría
│   ├── main.py                          # Servidor FastAPI y endpoints de la API Bridge
│   ├── requirements.txt                 # Dependencias unificadas de Python
│   ├── model_pipeline/                  # Pipeline de entrenamiento y validación de modelos ML
│   ├── normalization/                   # Pipeline de limpieza y normalización de datasets
│   ├── specimen_linkage/                # Vinculación y trazabilidad de probetas
│   ├── decision_ready/                  # Reportes analíticos de madurez de modelos
│   ├── compression_graphics/            # Generación de gráficos y reportes visuales
│   └── scripts/                         # Utilidades locales de optimización geométrica
│
├── frontend/                            # Cliente Web Interactivo en Next.js
│   ├── src/
│   │    ├── config/                     # Configuraciones Centrales de Parámetros
│   │    ├── stores/                     # Control de Estado Global (Zustand)
│   │    │
│   │    ├── cad/                        # Núcleo de Geometría CAD e Infill
│   │    │    ├── geometry/              # Tamaño y dimensiones de los objetos
│   │    │    ├── tpms/                  # Definición matemática de celdas
│   │    │    ├── exporters/             # Exportadores STL, G-Code y PDF
│   │    │    └── validators/            # Validadores geométricos de malla
│   │    │
│   │    ├── rendering/                  # Canvas de Visualización 3D (R3F)
│   │    │    ├── viewport/              # Visor 3D principal (BaseViewport.tsx)
│   │    │    └── diagnostics/           # Diagnósticos y estadísticas de FPS (PerformanceHUD)
│   │    │
│   │    ├── slicing/                    # Cinemática e Impresoras 3D
│   │    │    ├── manufacturing/         # Panel de Fabricación y validaciones
│   │    │    ├── printerProfiles/       # Especificaciones de hardware (Creality, Ender)
│   │    │    └── gcode/                 # Generación y simulación de trayectorias
│   │    │
│   │    ├── ml/                         # Capa de Inteligencia Artificial
│   │    │    ├── adapters/              # Adaptadores desacoplados (Ollama, OpenAI, LM Studio)
│   │    │    └── rag/                   # Sistema de Ingesta Vectorial y RAG
│   │    │
│   │    └── app/                        # Next.js Pages Router
│
├── data/                                # Base de datos y datasets en formato CSV
└── .venv/                               # Entorno virtual de Python
```

---

## 🛠️ Requisitos e Instalación

Para ejecutar el backend de forma local, activa el entorno virtual de Python e instala las dependencias necesarias:

1. **Activar el entorno virtual**:
   - En Windows (PowerShell):
     ```powershell
     & .venv\Scripts\activate
     ```
   - En Linux/macOS:
     ```bash
     source .venv/bin/activate
     ```

2. **Instalar dependencias**:
   ```bash
   pip install -r backend/requirements.txt
   ```

---

## 🚀 Ejecución del Servidor API

El backend expone una API REST construida con FastAPI que realiza inferencias estructurales y genera geometrías 3D de forma volumétrica:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Una vez levantado el servidor, puedes explorar la documentación interactiva en:
👉 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Endpoints Disponibles:

1. **Inferencia de Carga Estructural (`POST /api/predict_structural_load`)**:
   - Recibe parámetros de diseño (geometría, material y tipo/densidad de infill).
   - Utiliza el modelo `GradientBoostingRegressor_deployment_ready.pkl` para predecir la resistencia de fluencia (`yieldStrengthMpa`), carga máxima, rigidez y deformación aproximada con un alto nivel de confianza.

2. **Generación de Mallas STL Manifold (`POST /api/generate_stl`)**:
   - Genera campos de distancia volumétrica (SDF) para patrones celulares complejos (Gyroid, Honeycomb, Triply Periodic Schwarz P).
   - Ejecuta un extractor *Marching Cubes* para devolver un archivo binario `.stl` watertight e imprimible en 3D.

3. **Previsualización de Malla Liviana (`POST /api/generate_mesh`)**:
   - Similar a `/api/generate_stl` pero devuelve vértices y caras listos para visualizadores web ligeros en formato JSON.

---

## 🔬 Scripts de Optimización e Inferencia Local

En `backend/scripts/` hay utilidades que consumen el modelo entrenado y los datos para diseñar geometrías optimizadas:

- **Optimización PLA (`optimize_cube.py`)**:
  Diseña un bloque de PLA de 50mm para maximizar la resistencia a la compresión por debajo de un límite de peso de 100g.
  ```powershell
  python backend/scripts/optimize_cube.py
  ```

- **Optimización TPU (`execute_project_tpu.py`)**:
  Diseña y genera una malla 3D optimizada para maximizar la absorción de energía en impactos utilizando estructuras elásticas de TPU.
  ```powershell
  python backend/scripts/execute_project_tpu.py
  ```

---

## 📊 Ejecución de Pipelines de Datos

Puedes ejecutar cualquiera de las fases del pipeline de ciencia de datos independientemente:

- **Limpieza de Datos**:
  ```powershell
  python backend/normalization/run_pipeline.py
  ```
- **Trazabilidad de Probetas**:
  ```powershell
  python backend/specimen_linkage/run_specimen_linkage.py
  ```
- **Entrenamiento de Modelos**:
  ```powershell
  python backend/model_pipeline/run_model_pipeline.py
  ```
- **Consolidación e Informe de Estabilidad**:
  ```powershell
  python backend/decision_ready/run_decision_ready.py
  ```
- **Gráficos Estadísticos**:
  ```powershell
  python backend/compression_graphics/run_compression_graphics.py
  ```

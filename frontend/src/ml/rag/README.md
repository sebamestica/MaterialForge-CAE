# Sistema RAG (Retrieval-Augmented Generation)

Este directorio contiene las utilidades y la lógica para el sistema RAG que asiste al copiloto científico de MaterialForge en el análisis de materiales y optimización física.

---

## Componentes Principales

```text
frontend/src/ml/rag/
 ├── retrieval.ts      # Motor de consulta semántica RAG
 └── vectorStore.ts    # Base de datos vectorial ligera en memoria/cliente
```

---

## Configuración del RAG

El comportamiento del RAG se ajusta en el archivo de configuración central:
👉 [rag.config.ts](file:///c:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/frontend/src/config/rag.config.ts)

Aquí puede configurar:
- **`chunkSize`**: Tamaño máximo de los bloques de texto.
- **`overlap`**: Solapamiento de caracteres para mantener coherencia conceptual.
- **`topK`**: Cantidad de documentos de contexto inyectados en la consulta LLM.
- **`similarityThreshold`**: Puntaje de confianza mínimo para recuperar fragmentos de datos.

---

## Flujo de Ingestión de Documentos

Para indexar nueva documentación científica (por ejemplo, papers sobre TPU/ABS, hojas de especificaciones de filamentos):

1. **Ubicación de Documentos**: Guarde los archivos PDF o ficheros estructurados en el directorio de datos del servidor:
   👉 [backend/data/](file:///c:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/backend/data/)

2. **Generación de Embeddings**: Al cargar documentos, el sistema calcula los vectores usando el modelo configurado en el adaptador activo de `AiAdapter`.

3. **Búsqueda Vectorial**: Las preguntas del usuario en el widget del Copiloto se transforman en vectores de consulta, se realiza una multiplicación de similitud de coseno contra el vector store, y los fragmentos más relevantes se inyectan en el prompt del LLM.

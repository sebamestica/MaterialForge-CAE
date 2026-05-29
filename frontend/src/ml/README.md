# Capa de Modelos de Inteligencia Artificial (AI/ML)

Este directorio contiene la arquitectura de desacoplamiento para los proveedores de modelos de lenguaje (LLM). Utiliza el **Patrón de Diseño Adapter** para aislar los detalles del proveedor del cliente web, garantizando que puedas cambiar el proveedor de IA sin modificar el resto de la aplicación.

---

## Estructura de Directorios

```text
frontend/src/ml/
 ├── adapters/               # Adaptadores de proveedores de LLM
 │    ├── index.ts           # Interfaz común y fábrica del adaptador activo
 │    ├── ollama.adapter.ts  # Conexión local a Ollama daemon (puerto 11434)
 │    ├── openai.adapter.ts  # Integración oficial con OpenAI API
 │    ├── lmstudio.adapter.ts# Conexión local a LM Studio (puerto 1234)
 │    └── local.adapter.ts   # Adaptador de respaldo para endpoints personalizados
 └── rag/                    # Sistema RAG (Retrieval-Augmented Generation)
```

---

## Configuración Centralizada

Para cambiar el modelo activo o ajustar los parámetros de inferencia, modifique el archivo de configuración central:
👉 [model.config.ts](file:///c:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/frontend/src/config/model.config.ts)

```typescript
export const modelConfig = {
  activeProvider: "ollama", // Opciones: "ollama" | "openai" | "lmstudio" | "local"
  providers: {
    ollama: {
      endpoint: "http://127.0.0.1:11434",
      modelName: "llama3",
    },
    openai: {
      apiKey: process.env.NEXT_PUBLIC_OPENAI_API_KEY || "",
      modelName: "gpt-4-turbo",
    },
    // ...
  }
};
```

---

## La Interfaz `AiAdapter`

Cualquier adaptador de IA debe implementar la siguiente interfaz definida en [adapters/index.ts](file:///c:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/frontend/src/ml/adapters/index.ts):

```typescript
export interface AiAdapter {
  generate(prompt: string, context?: any): Promise<string>;
  stream(prompt: string, context: any, onToken: (token: string) => void): Promise<string>;
  healthCheck(): Promise<boolean>;
  embed(text: string): Promise<number[]>;
}
```

### Cómo agregar un nuevo proveedor de IA:
1. Cree un nuevo archivo en `adapters/my-provider.adapter.ts`.
2. Implemente la clase implementando `AiAdapter`.
3. Registre su adaptador en el factory selector `getActiveAdapter` dentro de `adapters/index.ts`.
4. Añada sus llaves de configuración a `config/model.config.ts`.

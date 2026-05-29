# Motor de Renderizado 3D (Three.js & React Three Fiber)

Este módulo controla la visualización 3D interactiva en tiempo real del cubo y sus retículas internas (Gyroid, Honeycomb, Schwarz P, Grid).

---

## Estructura de Carpetas

```text
frontend/src/rendering/
 ├── viewport/          # Componentes de Canvas 3D (BaseViewport.tsx)
 └── diagnostics/       # HUD de Diagnósticos y Calidad
```

---

## Modos de Visualización (Shading Modes)

El viewport soporta seis modos avanzados:
1. **Sólido (`solid`)**: Representa la geometría del cubo/infill con iluminación difusa tradicional.
2. **Carcasa (`shell`)**: Muestra la estructura exterior del cubo en modo alámbrico brillante.
3. **Alámbrico (`wireframe`)**: Visualiza la triangulación pura de la malla procesada.
4. **Transparente (`transparent`)**: Renderiza con opacidad parcial para inspeccionar la retícula sin ocultar el volumen externo.
5. **Estrés (`heatmap`)**: Modifica dinámicamente los colores en VRAM mediante un gradiente térmico de deformación (fuerza aplicada en Newton).
6. **Sección (`slicer`)**: Utiliza clipping planes locales para rebanar el modelo en cualquier altura Z.

---

## Directrices de Optimización de Memoria (VRAM)

Para garantizar un rendimiento estable de **45-60 FPS** sin congelar el navegador:

- **Eliminación Manual de Búferes**: Al actualizar los parámetros (infill, tamaño), la geometría antigua se desecha explícitamente llamando a `geometry.dispose()` y `material.dispose()`, evitando fugas de memoria en la GPU.
- **In-place updates**: En el modo de estrés (heatmap), modificamos directamente el atributo de colores del búfer (`colorAttr.needsUpdate = true`) en lugar de reconstruir toda la malla, logrando actualizaciones fluidas a más de 60 FPS.
- **Cierre del viewport**: Al desmontar el Canvas, se eliminan todos los escuchadores de eventos y animaciones en ejecución.

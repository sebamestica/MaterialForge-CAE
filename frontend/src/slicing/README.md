# Módulo de Slicing y Estimación de Manufactura

Este módulo agrupa la lógica relacionada con el laminado (slicing), perfiles de hardware 3D y estimaciones de tiempo, masa y flujo del material.

---

## Estructura de Directorios

```text
frontend/src/slicing/
 ├── manufacturing/          # Panel de configuración y control (ManufacturingPanel.tsx)
 ├── estimators/             # Algoritmos cinemáticos de estimación temporal (por crear/desacoplar)
 └── printerProfiles/        # Base de datos de perfiles de hardware (Creality K1 Max, Ender 3 V3, etc.)
```

---

## Perfiles de Impresora Soportados

La plataforma preconfigura cuatro impresoras de referencia industrial:
- **Creality K1 Max**: Direct Drive, compatible con TPU, volumen de 300x300x300mm.
- **Ender 3 V3 KE**: Direct Drive, velocidad adaptativa optimizada para filamentos flexibles.
- **Creality K1C**: Alta aceleración (20,000 mm/s²), extrusora Direct Drive reforzada.
- **Creality CR Series**: Sistema Bowden clásico (no recomendado para TPU por riesgos de pandeo/atascamiento).

---

## Heurísticas de Estimación

1. **Tiempo de Impresión**: Se desglosa en tiempo de contornos (paredes), tiempo de retícula (infill), viajes rápidos (travel) y retardos debidos a la velocidad máxima admitida por el filamento (por ejemplo, filamentos elásticos TPU requieren velocidades bajas para evitar pandeo).
2. **Caudal Volumétrico**: Se calcula en base a:
   $$\text{Caudal} = \text{velocidad} \times \text{altura de capa} \times \text{ancho de extrusión}$$
   El motor gráfico emitirá advertencias automáticas si el caudal resultante supera los límites físicos de la boquilla (por ejemplo, 32 mm³/s para la serie K1).

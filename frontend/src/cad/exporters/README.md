# Exportadores Geométricos (STL, G-Code & PDF)

Este módulo gestiona la exportación de archivos físicos listos para impresión 3D a partir de la geometría interna calculada.

---

## Módulos de Exportación

```text
frontend/src/cad/exporters/
 ├── stl.ts      # Generador de archivos de malla binaria STL
 ├── gcode.ts    # Generador de archivos de trayectorias G-Code
 └── pdf.ts      # Generador de informes técnicos de ingeniería
```

---

## 1. Exportación STL
- **Llamada de Endpoint**: Se comunica con el backend de Python a través de `/api/generate_stl` usando una resolución de alta fidelidad.
- **Resultados**: Descarga un archivo binario `.stl` watertight listo para ser arrastrado directamente al slicer.

---

## 2. Generación G-Code
El motor calcula trayectorias realistas capa por capa:
- **Grid / Rectilineo**: Genera rejillas ortogonales cruzadas de líneas rectas.
- **Gyroid / Schwarz P**: Utiliza funciones trigonométricas continuas aproximando curvas sinusoidales espaciales tridimensionales:
  $$x = x_{\text{base}} + a \cdot \sin(y \cdot f)$$
- **Honeycomb**: Modula posiciones hexagonales Voronoi decaladas para trazar panales de abeja continuos.

---

## 3. Informes PDF
- Ejecuta los estilos de hoja CSS de impresión optimizados y abre el diálogo estándar de impresión del sistema para almacenar el informe de la pieza.

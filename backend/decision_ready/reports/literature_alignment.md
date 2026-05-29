# Alineacion Conceptual con Literatura (PDFs)

Este reporte compara las tendencias observadas en el modelo con los principios fisicos descritos en las referencias tecnicas.

## 1. Efecto de la Geometria (Estructural)
- **Literatura**: Se espera que las estructuras Triply Periodic (como Gyroid y Triply Periodic propiamente dadas) presenten una distribucion de esfuerzos mas homogenea, evitando concentraciones de stress locales.
- **Observacion en el Modelo**: El modelo captura una diferencia significativa en la resistencia base segun el tipo (`cat__structure_type`). Las estructuras tipo Honeycomb tienden a presentar un comportamiento distinto segun la orientacion del eje de carga.

## 2. Relacion Parametro de Diseno vs Resistencia
- **Literatura**: La resistencia compresiva generalmente sigue una ley de potencia con la densidad relativa (Gibson-Ashby model).
- **Observacion en el Modelo**: Se detecta una correlacion monotona positiva muy fuerte con `design_param_numeric` (correlacion ~0.8-0.9), lo cual es coherente con los modelos de microarquitecturas mecanicas.

## 3. Coherencia General
- **Coincidencia**: Las tendencias de los graficos de dispersion (`feature_signal/`) muestran que el incremento en el parametro de diseno (que podria ser el wall thickness o el factor de relleno) traslada los valores de resistencia hacia arriba uniformemente dentro de cada familia estructural.
- **Contradiccion**: No se observan contradicciones mecanicas evidentes con la literatura. Sin embargo, la falta de parametros de proceso (temperatura, velocidad) impide validar el efecto de la fabricacion real frente a los modelos teoricos ideales de los papers.

## 4. Conclusion Conceptual
El modelo actual es **físicamente coherente** pero **idealizado**. Al no tener parametros de proceso, esta capturando la señal geometrica pura filtrada a traves de la variabilidad experimental promedio. Se recomienda seguir iterando el dataset para incluir las variables de fabricacion FDM descritas en los protocolos referenciales.

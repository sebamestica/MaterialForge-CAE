# Fase Decision Ready: Consolidacion y Matriz de Decision

Esta fase final del proyecto de regresion de resistencia compresora para piezas impresas en 3D tiene como objetivo **cerrar la iteracion actual**, consolidar los resultados obtenidos en las fases previas (linkage, modelado, auditoria) y proporcionar una base tecnica solida para que el equipo tome decisiones de negocio e ingenieria.

## Objetivos
1. **Auditoria del Estado Real**: Inventario automatico de que tenemos y que ha sido descartado.
2. **Validacion de Rigor**: Mas alla del R2, evaluamos si el modelo es fisicamente coherente o si presenta leakage estadistico.
3. **Analisis de Madurez**: Evaluacion de la estabilidad del modelo con tecnicas de validacion cruzada para datasets pequenos.
4. **Matriz de Decision**: Una herramienta ejecutiva para decidir si damos por cerrado el prototipo o si necesitamos mas datos.

## Estructura de la Fase
- `reports/`: Documentacion detallada de cada fase de evaluacion.
- `tables/`: Resumenes en CSV para comparaciones directas.
- `figures/`: Visualizaciones de residuos, señal de variables y matriz de madurez.
- `src/`: Modulos de analisis robusto e independiente del entrenamiento.
- `artifacts/ final_snapshot/`: El estado final empaquetado del mejor modelo validado de esta iteracion.

## Ejecucion
Para generar el paquete completo de reportes, ejecutar en el entorno adecuado (con pandas, sklearn, matplotlib):
```bash
python run_decision_ready.py
```

## Interpretacion de Resultados
- **R2 Superior a 0.9 con 35 Filas**: Debe interpretarse como un indicador de **tendencia solida** pero con **alta varianza**. La particion del dataset domina el resultado mas que la arquitectura.
- **Veredicto "Prototipo Valido"**: Significa que el modelo ha capturado la fisica basica de la geometría (Gyroid vs Honeycomb) y del parametro de diseño, pero carece de variables de proceso para ser usado en optimizacion de fabricacion.

---
*Este proyecto busca honestidad tecnica sobre entusiasmo numerico.*

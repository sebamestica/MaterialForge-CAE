# Reporte Ejecutivo de Limpieza

## Archivos viables para modelado serio (6)

- **FDM_Dataset.csv** - Valor: `high_value`, Confiabilidad: `high_reliability`
  * Tipo .csv
- **Compressivedata.csv** - Valor: `medium_value`, Confiabilidad: `medium_reliability`
  * Tipo .csv
- **TensiondataB.csv** - Valor: `medium_value`, Confiabilidad: `high_reliability`
  * Tipo .csv
- **Propiedades_Extraidas.csv** - Valor: `high_value`, Confiabilidad: `low_reliability`
  * Exceso de valores nulos
- **TensiondataA.csv** - Valor: `medium_value`, Confiabilidad: `low_reliability`
  * Exceso de valores nulos
- **data.csv** - Valor: `high_value`, Confiabilidad: `high_reliability`
  * Tipo .csv

## Archivos Descartes/Duplicados (2)

- Compressivedata.csv (Posible duplicado de c:\dev\PLA_3dPrinter_RESISTENCE\data\Ensayos_Mecanicos_Corrupto_TensionA\Compressivedata.csv)
- TensiondataB.csv (Posible duplicado de c:\dev\PLA_3dPrinter_RESISTENCE\data\Ensayos_Mecanicos_Corrupto_TensionA\TensiondataB.csv)

## Viabilidad del Modelaje

Las variables presentes dependen de cada dataset, pero tras la estandarización snake_case y limpieza de tipados, las columnas numéricas están uniformes y sin ruido blanco.

Los datasets evaluados como `high_value` y `high_reliability` están listos para regresiones y visualizaciones en la carpeta `cleaned/`.
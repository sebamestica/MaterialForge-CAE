# Módulo de Selección de Datasets

- **FDM_Dataset.csv**: `EXCLUDED` (No target found)
- **Compressivedata.csv**: `EXCLUDED` (No target found)
- **TensiondataB.csv**: `INCLUDED` (Target: stress[mpa])
- **Propiedades_Extraidas.csv**: `EXCLUDED` (Baja calidad analitica: low_reliability)
- **TensiondataA.csv**: `EXCLUDED` (Baja calidad analitica: low_reliability)
- **data.csv**: `INCLUDED` (Target: tension_strenght)
# Validacion de Compatibilidad Experimental

- **TensiondataB.csv**: `EXCLUDED` (Es un ensayo de tension, incompatible con regresion de compressive_strength)
- **data.csv**: `INCLUDED_WITH_CAUTION` (Dataset tabular generico detectado)
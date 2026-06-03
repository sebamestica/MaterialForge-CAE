# Instrucciones de Reversión (Volver al estado anterior)

Si decides que no te gustan los cambios de optimización de rendimiento aplicados a los gráficos y al viewport 3D, puedes volver exactamente al estado actual de las siguientes maneras:

---

## Opción A: Usando Git (Recomendado y 100% Seguro)

Como todos los cambios anteriores se subieron exitosamente al repositorio remoto, el estado actual de tu rama `main` corresponde al commit **`29c2f76`**.

Para deshacer todos los cambios de optimización de rendimiento y volver exactamente a este punto:

1. Abre tu terminal en la raíz del proyecto.
2. Ejecuta los siguientes comandos:
   ```bash
   # Restablecer los archivos locales al commit exacto antes de las optimizaciones
   git reset --hard 29c2f7639f75bf7c87c7b8d00cf0ca41bb25ec1d

   # Forzar el empuje de la reversión a GitHub para actualizar la rama remota
   git push origin main --force
   ```

---

## Opción B: Copias de Seguridad Manuales de los Archivos Modificados

Hemos creado copias de seguridad de los dos únicos archivos que modificaremos para esta optimización. Para restaurarlos manualmente:

1. Ve a la carpeta `frontend/src/rendering/pipelines/tpms/` y elimina `TpmsPipeline.tsx`.
2. Renombra el archivo `TpmsPipeline.tsx.bak` (copia de seguridad) a `TpmsPipeline.tsx`.
3. Ve a la carpeta `frontend/src/rendering/viewport/` y elimina `BaseViewport.tsx`.
4. Renombra el archivo `BaseViewport.tsx.bak` (copia de seguridad) a `BaseViewport.tsx`.

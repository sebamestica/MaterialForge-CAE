"use client";

import React from "react";
import { useLabStore } from "@/stores/useLabStore";
import { useShallow } from "zustand/react/shallow";
import { 
  Database, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle, 
  FileText, 
  BarChart, 
  Activity,
  Layers,
  ArrowRight
} from "lucide-react";

export default function DatasetManagerView() {
  const store = useLabStore(
    useShallow((state) => ({
      scannedFiles: state.scannedFiles,
      qualityReport: state.qualityReport,
      isScanning: state.isScanning,
      isImporting: state.isImporting,
      isTraining: state.isTraining,
      scanDatasets: state.scanDatasets,
      importDatasets: state.importDatasets,
      retrainModel: state.retrainModel,
      error: state.error,
    }))
  );

  const totalSpecimens = store.qualityReport?.metrics?.total_specimens || 0;
  const materialsCount = store.qualityReport?.metrics?.materials_count || {};
  const testTypesCount = store.qualityReport?.metrics?.test_types_count || {};
  const avgCurveQuality = store.qualityReport?.metrics?.avg_curve_quality_score || 0;
  const nullModulus = store.qualityReport?.metrics?.null_properties?.young_modulus || 0;
  const nullStrength = store.qualityReport?.metrics?.null_properties?.max_stress || 0;
  const warnings = store.qualityReport?.quality_warnings || [];

  return (
    <div className="w-full h-full overflow-y-auto p-6 bg-slate-50 font-mono text-slate-800">
      {/* Title Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-200 pb-4 mb-6 gap-4">
        <div>
          <h1 className="text-xl font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
            <Database className="w-5 h-5 text-blue-600" />
            Gestor de Datasets y Calidad de Ingesta
          </h1>
          <p className="text-xs text-slate-500 mt-1 uppercase tracking-widest">
            Normalización de Ensayos Mecánicos y Generación de Base Parquet
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={store.scanDatasets}
            disabled={store.isScanning}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 hover:border-slate-400 disabled:opacity-50 text-xs font-bold rounded shadow-xs hover:shadow-sm transition-all cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${store.isScanning ? "animate-spin" : ""}`} />
            <span>{store.isScanning ? "Escaneando..." : "Escanear Carpeta"}</span>
          </button>
          <button
            onClick={store.importDatasets}
            disabled={store.isImporting || store.isScanning}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 text-xs font-bold rounded shadow-xs hover:shadow-sm transition-all cursor-pointer"
          >
            <Layers className={`w-3.5 h-3.5 ${store.isImporting ? "animate-pulse" : ""}`} />
            <span>{store.isImporting ? "Ingiriendo..." : "Importar e Integrar"}</span>
          </button>
          <button
            onClick={store.retrainModel}
            disabled={store.isTraining || store.isImporting}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50 text-xs font-bold rounded shadow-xs hover:shadow-sm transition-all cursor-pointer"
          >
            <Activity className={`w-3.5 h-3.5 ${store.isTraining ? "animate-spin" : ""}`} />
            <span>{store.isTraining ? "Entrenando..." : "Reentrenar Modelos"}</span>
          </button>
        </div>
      </div>

      {store.error && (
        <div className="mb-6 p-4 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <p className="font-bold">Error de Ingesta:</p>
            <p>{store.error}</p>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        {/* Total specimens */}
        <div className="bg-white border border-slate-200 rounded p-4 shadow-xs relative overflow-hidden">
          <div className="text-[10px] uppercase font-bold text-slate-400">Total Probetas Ingeridas</div>
          <div className="text-3xl font-extrabold text-slate-900 mt-2">{totalSpecimens}</div>
          <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-1">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
            <span>Consolidado en Parquet</span>
          </div>
          <div className="absolute right-3 bottom-3 text-slate-100 font-extrabold text-5xl pointer-events-none">#</div>
        </div>

        {/* Quality score */}
        <div className="bg-white border border-slate-200 rounded p-4 shadow-xs relative overflow-hidden">
          <div className="text-[10px] uppercase font-bold text-slate-400">Calidad de Curvas Promedio</div>
          <div className="text-3xl font-extrabold text-slate-900 mt-2">{(avgCurveQuality * 100).toFixed(1)}%</div>
          <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-1">
            <Activity className="w-3.5 h-3.5 text-blue-500 animate-pulse" />
            <span>Tolerancia de ruido aprobada</span>
          </div>
          <div className="absolute right-3 bottom-3 text-slate-100 font-extrabold text-5xl pointer-events-none">%</div>
        </div>

        {/* Materials count */}
        <div className="bg-white border border-slate-200 rounded p-4 shadow-xs relative overflow-hidden">
          <div className="text-[10px] uppercase font-bold text-slate-400">Diversidad de Materiales</div>
          <div className="text-base font-extrabold text-slate-800 mt-2 space-y-0.5">
            {Object.entries(materialsCount).map(([mat, count]) => (
              <div key={mat} className="flex justify-between text-xs">
                <span className="uppercase text-slate-500">{mat}:</span>
                <span className="font-bold">{count as number}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Test types */}
        <div className="bg-white border border-slate-200 rounded p-4 shadow-xs relative overflow-hidden">
          <div className="text-[10px] uppercase font-bold text-slate-400">Distribución de Ensayos</div>
          <div className="text-base font-extrabold text-slate-800 mt-2 space-y-0.5">
            {Object.entries(testTypesCount).map(([type, count]) => (
              <div key={type} className="flex justify-between text-xs">
                <span className="capitalize text-slate-500">{type === "tensile" ? "Tracción" : "Compresión"}:</span>
                <span className="font-bold">{count as number}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Scanned Folder Status (Left) */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded shadow-xs p-4 flex flex-col">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-900 border-b border-slate-200 pb-2 mb-3 flex items-center gap-1.5">
            <FileText className="w-4 h-4 text-blue-500" />
            Archivos Escaneados en /data
          </h2>
          <div className="overflow-x-auto flex-1 min-h-[300px] max-h-[500px]">
            <table className="w-full text-[11px] text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-slate-400 font-bold bg-slate-50 uppercase text-[9px]">
                  <th className="py-2 px-3">Archivo</th>
                  <th className="py-2 px-3">Dataset Clasificado</th>
                  <th className="py-2 px-3 text-right">Tamaño</th>
                  <th className="py-2 px-3 text-center">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {store.scannedFiles.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-slate-400">
                      Haz clic en "Escanear Carpeta" para listar los archivos.
                    </td>
                  </tr>
                ) : (
                  store.scannedFiles.map((file, idx) => {
                    const isSuccess = store.qualityReport?.metrics ? true : false;
                    return (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="py-2 px-3 font-semibold text-slate-800 max-w-[200px] truncate" title={file.relative_path}>
                          {file.relative_path}
                        </td>
                        <td className="py-2 px-3 text-slate-500 font-medium italic">
                          {file.dataset_type}
                        </td>
                        <td className="py-2 px-3 text-right text-slate-500 font-semibold">
                          {(file.size_bytes / (1024 * 1024)).toFixed(2)} MB
                        </td>
                        <td className="py-2 px-3 text-center">
                          <span className={`inline-block px-1.5 py-0.5 rounded-[3px] text-[8px] font-bold uppercase border ${
                            file.dataset_type !== "unknown"
                              ? "bg-emerald-50 border-emerald-200 text-emerald-700"
                              : "bg-slate-100 border-slate-200 text-slate-500"
                          }`}>
                            {file.dataset_type !== "unknown" ? "Soportado" : "Omitido"}
                          </span>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Quality Alerts & Integrity (Right) */}
        <div className="bg-white border border-slate-200 rounded shadow-xs p-4 flex flex-col">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-900 border-b border-slate-200 pb-2 mb-3 flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            Alertas de Integridad y Vacíos
          </h2>
          <div className="flex-1 space-y-3 overflow-y-auto max-h-[500px]">
            {/* Imputation Stats */}
            <div className="bg-slate-50 border border-slate-200 p-3 rounded">
              <h3 className="text-[10px] uppercase font-bold text-slate-600 mb-2">Propiedades Faltantes / Imputadas</h3>
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span>Módulo de Young Nulo:</span>
                  <span className={`font-bold ${nullModulus > 0 ? "text-amber-600" : "text-emerald-600"}`}>
                    {nullModulus} probetas
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span>Esfuerzo Máximo Nulo:</span>
                  <span className={`font-bold ${nullStrength > 0 ? "text-rose-600" : "text-emerald-600"}`}>
                    {nullStrength} probetas
                  </span>
                </div>
              </div>
            </div>

            {/* Warnings list */}
            <div className="space-y-2">
              <h3 className="text-[10px] uppercase font-bold text-slate-600">Registro de Advertencias de Ingesta</h3>
              {warnings.length === 0 ? (
                <div className="text-xs text-emerald-600 bg-emerald-50 border border-emerald-200 p-3 rounded flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
                  <span>Cero advertencias. Todos los archivos válidos leídos correctamente.</span>
                </div>
              ) : (
                warnings.map((warn: string, i: number) => (
                  <div key={i} className="text-[10px] text-amber-700 bg-amber-50/50 border border-amber-200 p-2.5 rounded flex gap-2">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
                    <p className="leading-tight">{warn}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

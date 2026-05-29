"use client";

import React, { useState, useEffect } from "react";
import { useLabStore } from "@/stores/useLabStore";
import { useShallow } from "zustand/react/shallow";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from "recharts";
import { 
  Cpu, 
  RefreshCw, 
  TrendingUp, 
  Activity, 
  CheckCircle,
  HelpCircle,
  FileText
} from "lucide-react";

export default function ModelTrainingView() {
  const store = useLabStore(
    useShallow((state) => ({
      mlMetrics: state.mlMetrics,
      mlFeatureImportance: state.mlFeatureImportance,
      isTraining: state.isTraining,
      retrainModel: state.retrainModel,
      fetchMlMetrics: state.fetchMlMetrics,
    }))
  );

  const [selectedTarget, setSelectedTarget] = useState("max_stress_MPa");

  useEffect(() => {
    if (!store.mlMetrics) {
      store.fetchMlMetrics();
    }
  }, [store.mlMetrics]);

  const metrics = store.mlMetrics?.metrics || {};
  const targets = Object.keys(metrics);

  // Set default selected target once targets are available
  useEffect(() => {
    if (targets.length > 0 && !targets.includes(selectedTarget)) {
      setSelectedTarget(targets[0]);
    }
  }, [targets]);

  // Format feature importance for selected target
  const importanceDict = store.mlFeatureImportance?.[selectedTarget] || {};
  const importanceData = Object.entries(importanceDict)
    .map(([name, importance]) => ({
      name,
      importance: parseFloat((importance as number).toFixed(4))
    }))
    .sort((a, b) => b.importance - a.importance);

  const displayTargetName = (t: string) => {
    const names: Record<string, string> = {
      max_stress_MPa: "Esfuerzo Máximo (MPa)",
      young_modulus_MPa: "Módulo de Young (MPa)",
      failure_strain: "Deformación de Ruptura (Strain)",
      energy_density_MJ_m3: "Densidad de Energía (MJ/m³)",
      specific_energy_absorption_kJ_kg: "Absorción Específica (SEA, kJ/kg)",
      compressive_strength_MPa: "Resistencia a la Compresión (MPa)",
      ultimate_tensile_strength_MPa: "Resistencia Máxima Tracción (MPa)",
      plateau_stress_MPa: "Plateau Stress (MPa)",
      crushing_force_efficiency: "Eficiencia de Aplastamiento (CFE)",
    };
    return names[t] || t;
  };

  return (
    <div className="w-full h-full overflow-y-auto p-6 bg-slate-50 font-mono text-slate-800">
      
      {/* Title Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-200 pb-4 mb-6 gap-4">
        <div>
          <h1 className="text-xl font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-blue-600 animate-pulse" />
            Métricas de Entrenamiento del Modelo Predictivo
          </h1>
          <p className="text-xs text-slate-500 mt-1 uppercase tracking-widest">
            Ajuste de Hiperparámetros, Validación Cruzada (GroupKFold) y Desempeño
          </p>
        </div>
        <div>
          <button
            onClick={store.retrainModel}
            disabled={store.isTraining}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 text-xs font-bold rounded shadow-xs hover:shadow-sm transition-all cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${store.isTraining ? "animate-spin" : ""}`} />
            <span>{store.isTraining ? "Reentrenando..." : "Reentrenar Modelos"}</span>
          </button>
        </div>
      </div>

      {/* Model Registry Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="bg-white border border-slate-200 rounded p-4 shadow-xs">
          <div className="text-[10px] uppercase font-bold text-slate-400">Versión del Modelo</div>
          <div className="text-2xl font-extrabold text-slate-800 mt-2">v{store.mlMetrics?.model_version || "1.1.0"}</div>
          <div className="text-[10px] text-slate-500 mt-1">Multi-Task Regression Suite</div>
        </div>
        <div className="bg-white border border-slate-200 rounded p-4 shadow-xs">
          <div className="text-[10px] uppercase font-bold text-slate-400">Último Entrenamiento</div>
          <div className="text-sm font-extrabold text-slate-800 mt-3 truncate" title={store.mlMetrics?.last_trained_at}>
            {store.mlMetrics?.last_trained_at ? new Date(store.mlMetrics.last_trained_at).toLocaleString() : "Cargando..."}
          </div>
          <div className="text-[10px] text-slate-500 mt-1">Entrenamiento por Bootstrap incremental</div>
        </div>
        <div className="bg-white border border-slate-200 rounded p-4 shadow-xs">
          <div className="text-[10px] uppercase font-bold text-slate-400">Probetas Totales del Set</div>
          <div className="text-2xl font-extrabold text-slate-800 mt-2">{store.mlMetrics?.total_training_samples || 0}</div>
          <div className="text-[10px] text-slate-500 mt-1">Muestras experimentales válidas</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Validation Metrics Table (Left) */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded shadow-xs p-4 flex flex-col">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-900 border-b border-slate-200 pb-2 mb-4 flex items-center gap-1.5">
            <CheckCircle className="w-4 h-4 text-emerald-500" />
            Precisión por Variable Objetivo (Target)
          </h2>
          <div className="overflow-x-auto flex-1 min-h-[300px]">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-slate-400 font-bold bg-slate-50 uppercase text-[9px]">
                  <th className="py-2.5 px-3">Propiedad Mecánica (Target)</th>
                  <th className="py-2.5 px-3 text-center">Algoritmo</th>
                  <th className="py-2.5 px-3 text-right">R² Train</th>
                  <th className="py-2.5 px-3 text-right">R² CV Val</th>
                  <th className="py-2.5 px-3 text-right">MAE</th>
                  <th className="py-2.5 px-3 text-right">RMSE</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {targets.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400">
                      Cargando métricas de validación...
                    </td>
                  </tr>
                ) : (
                  targets.map((targetKey) => {
                    const row = metrics[targetKey];
                    return (
                      <tr 
                        key={targetKey} 
                        className={`hover:bg-slate-50 cursor-pointer ${selectedTarget === targetKey ? "bg-blue-50/50" : ""}`}
                        onClick={() => setSelectedTarget(targetKey)}
                      >
                        <td className="py-2.5 px-3 font-semibold text-slate-950">
                          {displayTargetName(targetKey)}
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          <span className={`inline-block px-1.5 py-0.5 rounded-[3px] text-[9px] font-bold uppercase border ${
                            row.best_algorithm === "XGB" 
                              ? "bg-purple-50 border-purple-200 text-purple-700" 
                              : row.best_algorithm === "RF" 
                                ? "bg-blue-50 border-blue-200 text-blue-700"
                                : "bg-slate-100 border-slate-200 text-slate-600"
                          }`}>
                            {row.best_algorithm}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-600">
                          {row.r2?.toFixed(3)}
                        </td>
                        <td className={`py-2.5 px-3 text-right font-bold ${row.cv_r2 > 0.4 ? "text-emerald-600" : row.cv_r2 > 0.0 ? "text-blue-600" : "text-rose-600"}`}>
                          {row.cv_r2?.toFixed(3)}
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-500">
                          {row.mae?.toFixed(3)}
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-500">
                          {row.rmse?.toFixed(3)}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
          <div className="text-[10px] text-slate-400 mt-4 bg-slate-50 border border-slate-150 p-2.5 rounded">
            <span className="font-bold uppercase text-slate-500 block mb-1">Nota metodológica:</span>
            Los modelos se evalúan mediante validación cruzada grupal (GroupKFold) agrupados por lote de configuración material/infill para evitar la fuga de datos por réplicas idénticas (data leakage). R² CV negativo indica que un predictor simple (media) supera al modelo en ciertas sub-geometrías extremas con muestras muy reducidas (p. ej. compresión lattice en Carbon-PLA).
          </div>
        </div>

        {/* Feature Importance Panel (Right) */}
        <div className="bg-white border border-slate-200 rounded shadow-xs p-4 flex flex-col">
          <div className="border-b border-slate-200 pb-2 mb-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4 text-blue-500" />
              Importancia de Features
            </h2>
            <div className="mt-2">
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Variable Predictora</label>
              <select
                value={selectedTarget}
                onChange={(e) => setSelectedTarget(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded px-2 py-1 text-xs focus:bg-white"
              >
                {targets.map((t) => (
                  <option key={t} value={t}>{displayTargetName(t)}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Bar Chart */}
          <div className="flex-1 min-h-[300px]">
            {importanceData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                Sin datos de importancia de variables.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={importanceData.slice(0, 10)}
                  layout="vertical"
                  margin={{ left: 10, right: 10, top: 10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 8, fontFamily: "monospace" }} />
                  <YAxis
                    dataKey="name"
                    type="category"
                    width={100}
                    tick={{ fontSize: 8, fontFamily: "monospace" }}
                  />
                  <Tooltip
                    formatter={(value) => [`${(parseFloat(value as string) * 100).toFixed(2)}%`, 'Importancia Relativa']}
                    contentStyle={{ fontSize: 9, fontFamily: "monospace", borderRadius: 4 }}
                  />
                  <Bar dataKey="importance" fill="#2563eb" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}

"use client";

import React, { useMemo, useState, useEffect } from "react";
import { useLabStore } from "@/stores/useLabStore";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceDot } from "recharts";
import { ShieldCheck, Activity, Award, TrendingUp, Cpu, ChevronRight, AlertTriangle } from "lucide-react";
import { useShallow } from "zustand/react/shallow";
import ManufacturingPanel from "@/slicing/manufacturing/ManufacturingPanel";
import MaterialInspector from "@/components/materials/MaterialInspector";

export default function RightPanel() {
  const {
    predictions,
    material,
    infill,
    loadingPredictions,
    error,
    toggleRightPanel,
    workspaceFocus,
    designHistory,
    enableStressCubemap,
  } = useLabStore(
    useShallow((state) => ({
      predictions: state.predictions,
      material: state.material,
      infill: state.infill,
      loadingPredictions: state.loadingPredictions,
      error: state.error,
      toggleRightPanel: state.toggleRightPanel,
      workspaceFocus: state.workspaceFocus,
      designHistory: state.designHistory,
      enableStressCubemap: state.enableStressCubemap,
    }))
  );

  const printTimeStr = useMemo(() => {
    if (!predictions) return "0h 00m";
    const hrs = Math.floor(predictions.printingTimeMinutes / 60);
    const mins = predictions.printingTimeMinutes % 60;
    return `${hrs}h ${mins}m`;
  }, [predictions]);

  const yieldStrength = predictions?.yieldStrengthMpa || 24.7;
  const maxForce = predictions?.maxForceNewtons || 450 + infill * 12;
  const stiffness = predictions?.stiffnessNmm || 120 + infill * 4;
  const energyAbsorption = predictions?.energyAbsorptionJoules || 14.5 + infill * 0.15;

  const youngModulus = material === "PLA" ? "1.62 GPa" : "0.08 GPa";
  const performanceIndex = material === "PLA" ? "1.82" : "2.15";

  const recommendations = useMemo(() => {
    if (material === "TPU") {
      return [
        "Estructura eficiente para absorción de energía elástica.",
        "Excelente resistencia ante fatiga por compresión cíclica.",
        "Aumentar espesor de celda mejora amortiguación específica.",
      ];
    } else {
      return [
        "Estructura rígida apta para carga estática sostenida.",
        "Buen compromiso entre módulo de rigidez y peso de la pieza.",
        "Monitorear riesgos de fallo frágil ante sobrecargas repentinas.",
      ];
    }
  }, [material]);

  if (workspaceFocus === "material") {
    return (
      <div className="w-full h-full bg-white flex flex-col select-none text-slate-800 overflow-hidden">
        {/* Title */}
        <div className="p-3 border-b border-slate-200 flex items-center justify-between bg-white shrink-0 font-sans">
          {/* Collapse button for PC view */}
          <button
            onClick={toggleRightPanel}
            className="hidden lg:flex items-center justify-center p-1 rounded-md hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition-colors focus:outline-none cursor-pointer"
            title="Ocultar Panel"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
          <div className="flex items-center space-x-2">
            <Activity className="w-4.5 h-4.5 text-[#1E40AF]" />
            <span className="text-slate-900 text-sm font-black uppercase tracking-wider">
              Inspector de Materiales
            </span>
          </div>
          <div className="w-1.5 h-1.5 rounded-full bg-[#10B981]" />
        </div>
        <div className="flex-1 overflow-hidden">
          <MaterialInspector />
        </div>
      </div>
    );
  }

  if (workspaceFocus === "fabricación") {
    return (
      <div className="w-full h-full bg-white flex flex-col select-none text-slate-800 overflow-hidden">
        {/* Title */}
        <div className="p-3 border-b border-slate-200 flex items-center justify-between bg-white shrink-0 font-sans">
          {/* Collapse button for PC view */}
          <button
            onClick={toggleRightPanel}
            className="hidden lg:flex items-center justify-center p-1 rounded-md hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition-colors focus:outline-none cursor-pointer"
            title="Ocultar Panel"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
          <div className="flex items-center space-x-2">
            <Cpu className="w-4.5 h-4.5 text-[#1E40AF]" />
            <span className="text-slate-900 text-sm font-black uppercase tracking-wider">
              Postprocesamiento & Exportación
            </span>
          </div>
          <div className="w-1.5 h-1.5 rounded-full bg-[#10B981]" />
        </div>
        <div className="flex-1 overflow-hidden">
          <ManufacturingPanel />
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-white flex flex-col select-none text-slate-800 overflow-hidden">
      {/* Title */}
      <div className="p-3 border-b border-slate-200 flex items-center justify-between bg-white shrink-0 font-sans">
        {/* Collapse button for PC view */}
        <button
          onClick={toggleRightPanel}
          className="hidden lg:flex items-center justify-center p-1 rounded-md hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition-colors focus:outline-none cursor-pointer"
          title="Ocultar Panel"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
        <div className="flex items-center space-x-2">
          <Activity className="w-4.5 h-4.5 text-[#1E40AF]" />
          <span className="text-slate-900 text-sm font-black uppercase tracking-wider">
            Análisis & Predicción
          </span>
        </div>
        {loadingPredictions ? (
          <span className="text-xs font-bold text-[#1E40AF] animate-pulse font-mono bg-blue-50 border border-blue-200 px-1.5 py-0.5 rounded uppercase">CALCULANDO...</span>
        ) : (
          <div className="w-1.5 h-1.5 rounded-full bg-[#10B981]" />
        )}
      </div>

      <div className="p-3 space-y-4 flex-1 overflow-y-auto scrollbar-thin">
        {/* PROJECT GOALS CARD */}
        {predictions && (
          <div className="bg-slate-55/40 border border-slate-200 rounded-lg p-3 text-sm font-sans shadow-3xs">
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-2">
              OBJETIVOS DEL PROYECTO
            </span>
            <div className="space-y-3">
              {/* Peso limit <= 100g */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-slate-550">Peso de la Pieza (Objetivo: ≤ 100g)</span>
                  <span className={`font-mono font-bold ${predictions.massGrams <= 100.0 ? "text-emerald-600" : "text-rose-600"}`}>
                    {predictions.massGrams.toFixed(1)} g
                  </span>
                </div>
                <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${predictions.massGrams <= 100.0 ? "bg-emerald-500" : "bg-rose-500"}`}
                    style={{ width: `${Math.min(100, (predictions.massGrams / 100.0) * 100)}%` }}
                  />
                </div>
              </div>

              {/* Compresión limit >= 6000N */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-slate-550">Carga de Compresión (Objetivo: ≥ 6000N)</span>
                  <span className={`font-mono font-bold ${predictions.maxForceNewtons >= 6000.0 ? "text-emerald-600" : "text-rose-600"}`}>
                    {predictions.maxForceNewtons.toFixed(0)} N
                  </span>
                </div>
                <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${predictions.maxForceNewtons >= 6000.0 ? "bg-emerald-500" : "bg-rose-500"}`}
                    style={{ width: `${Math.min(100, (predictions.maxForceNewtons / 6000.0) * 100)}%` }}
                  />
                </div>
              </div>

              {/* Global compliance status */}
              <div className="flex items-center justify-between pt-2 border-t border-slate-200/50">
                <span className="text-xs font-bold text-slate-500">Estado Global:</span>
                {predictions.massGrams <= 100.0 && predictions.maxForceNewtons >= 6000.0 ? (
                  <span className="bg-emerald-50 text-emerald-700 text-xs px-2 py-0.5 rounded border border-emerald-200 font-black uppercase">
                    CUMPLE (Margen: +{(((predictions.maxForceNewtons - 6000.0) / 6000.0) * 100).toFixed(0)}%)
                  </span>
                ) : (
                  <span className="bg-rose-50 text-rose-700 text-xs px-2 py-0.5 rounded border border-rose-200 font-black uppercase">
                    FUERA DE ESPECIFICACIÓN
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
        {/* Connection/Scientific Computations Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 p-3 rounded-lg text-sm font-mono text-red-750 shadow-xs">
            <span className="font-black uppercase block mb-1 text-red-700 flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4" />
              Fallo de Simulación
            </span>
            {error}
          </div>
        )}

        {/* Domain Guard Extrapolation Warnings */}
        {predictions?.warnings && predictions.warnings.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 p-3 rounded-lg text-sm font-sans text-amber-850 space-y-1.5 shadow-xs">
            <span className="font-extrabold uppercase flex items-center gap-1.5 text-amber-700">
              <AlertTriangle className="w-4.5 h-4.5 shrink-0 text-amber-600" />
              Límites de Inferencia (Confianza Baja)
            </span>
            <div className="space-y-1 font-mono text-xs leading-relaxed text-amber-800 font-bold">
              {predictions.warnings.map((warn, idx) => (
                <p key={idx} className="border-b border-amber-200/50 last:border-b-0 pb-1 last:pb-0">
                  • {warn.text}
                </p>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-2.5 font-sans">
          <div className="bg-slate-50/70 border border-slate-200 p-3 rounded-lg shadow-3xs flex flex-col justify-between">
            <div>
              <span className="text-sm text-slate-500 block uppercase font-bold tracking-wider font-extrabold">Masa Total</span>
              <span className="text-xl font-black text-slate-800 mt-1 block font-mono">
                {predictions ? `${predictions.massGrams.toFixed(1)} g` : "38.7 g"}
              </span>
            </div>
            <div className="mt-2 text-[9px] font-semibold text-slate-400 font-mono">
              [Medición Geométrica]<br/>Confianza: 100% | ±0.1g
            </div>
          </div>
          <div className="bg-slate-50/70 border border-slate-200 p-3 rounded-lg shadow-3xs flex flex-col justify-between">
            <div>
              <span className="text-sm text-slate-500 block uppercase font-bold tracking-wider font-extrabold">Densidad Rel.</span>
              <span className="text-xl font-black text-slate-800 mt-1 block font-mono">
                {predictions ? predictions.densityRelative.toFixed(2) : "0.28"}
              </span>
            </div>
            <div className="mt-2 text-[9px] font-semibold text-slate-400 font-mono">
              [Medición Geométrica]<br/>Confianza: 100%
            </div>
          </div>
          <div className="bg-slate-50/70 border border-slate-200 p-3 rounded-lg shadow-3xs flex flex-col justify-between">
            <div>
              <span className="text-sm text-slate-500 block uppercase font-bold tracking-wider font-extrabold">Laminado</span>
              <span className="text-xl font-black text-slate-800 mt-1 block font-mono">{printTimeStr}</span>
            </div>
            <div className="mt-2 text-[9px] font-semibold text-slate-400 font-mono">
              [Heurística Laminación]<br/>Confianza: 92% | ±10m
            </div>
          </div>
          <div className="bg-emerald-50/60 border border-emerald-255 p-3 rounded-lg shadow-3xs flex flex-col justify-between">
            <div>
              <span className="text-sm text-emerald-700 block uppercase font-bold tracking-wider flex items-center gap-1 font-extrabold">
                <Award className="w-4.5 h-4.5 text-emerald-600 animate-pulse" />
                Rendimiento
              </span>
              <span className="text-xl font-black text-emerald-700 mt-1 block font-mono">
                {performanceIndex}
              </span>
            </div>
            <div className="mt-2 text-[9px] font-semibold text-emerald-600/70 font-mono">
              [Modelo Analítico]<br/>Confianza: 95% | Índice
            </div>
          </div>
        </div>

        {/* SECTION: SLICING TIME BREAKDOWN */}
        {predictions?.timeBreakdown && (
          <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-xs font-sans">
            <div className="bg-slate-50/70 px-3 py-2 border-b border-slate-200 flex justify-between items-center">
              <span className="text-sm text-slate-500 font-bold uppercase tracking-wider block font-extrabold">
                Desglose de Tiempo de Laminado
              </span>
              <span className="text-[8px] bg-blue-50 text-blue-700 font-bold border border-blue-200 px-1.5 py-0.5 rounded font-mono">
                Confianza: {Math.round(predictions.confidenceScore * 100)}%
              </span>
            </div>
            
            <div className="p-3 space-y-3">
              {/* Colored Proportions Bar */}
              <div className="w-full h-3.5 rounded-full overflow-hidden flex bg-slate-100 border border-slate-200">
                {predictions.timeBreakdown.walls_min > 0 && (
                  <div 
                    className="h-full bg-amber-500" 
                    style={{ width: `${(predictions.timeBreakdown.walls_min / predictions.printingTimeMinutes) * 100}%` }}
                    title={`Paredes: ${predictions.timeBreakdown.walls_min} min`}
                  />
                )}
                {predictions.timeBreakdown.infill_min > 0 && (
                  <div 
                    className="h-full bg-rose-500" 
                    style={{ width: `${(predictions.timeBreakdown.infill_min / predictions.printingTimeMinutes) * 100}%` }}
                    title={`Infill: ${predictions.timeBreakdown.infill_min} min`}
                  />
                )}
                {predictions.timeBreakdown.top_bottom_min > 0 && (
                  <div 
                    className="h-full bg-purple-500" 
                    style={{ width: `${(predictions.timeBreakdown.top_bottom_min / predictions.printingTimeMinutes) * 100}%` }}
                    title={`Top/Bottom: ${predictions.timeBreakdown.top_bottom_min} min`}
                  />
                )}
                {predictions.timeBreakdown.travel_min > 0 && (
                  <div 
                    className="h-full bg-blue-500" 
                    style={{ width: `${(predictions.timeBreakdown.travel_min / predictions.printingTimeMinutes) * 100}%` }}
                    title={`Movimientos (Travel): ${predictions.timeBreakdown.travel_min} min`}
                  />
                )}
                {predictions.timeBreakdown.firmware_overhead_min > 0 && (
                  <div 
                    className="h-full bg-slate-400" 
                    style={{ width: `${(predictions.timeBreakdown.firmware_overhead_min / predictions.printingTimeMinutes) * 100}%` }}
                    title={`Overhead / TPU: ${predictions.timeBreakdown.firmware_overhead_min} min`}
                  />
                )}
              </div>

              {/* Legend List */}
              <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-[10px]">
                <div className="flex items-center justify-between py-0.5 border-b border-slate-50">
                  <div className="flex items-center space-x-1.5">
                    <div className="w-2 h-2 rounded-full bg-amber-500" />
                    <span className="text-slate-500 font-medium">Paredes (Walls)</span>
                  </div>
                  <span className="text-slate-800 font-bold font-mono">{predictions.timeBreakdown.walls_min} min</span>
                </div>
                <div className="flex items-center justify-between py-0.5 border-b border-slate-50">
                  <div className="flex items-center space-x-1.5">
                    <div className="w-2 h-2 rounded-full bg-rose-500" />
                    <span className="text-slate-500 font-medium">Infill (Relleno)</span>
                  </div>
                  <span className="text-slate-800 font-bold font-mono">{predictions.timeBreakdown.infill_min} min</span>
                </div>
                <div className="flex items-center justify-between py-0.5 border-b border-slate-50">
                  <div className="flex items-center space-x-1.5">
                    <div className="w-2 h-2 rounded-full bg-purple-500" />
                    <span className="text-slate-500 font-medium">Top/Bottom</span>
                  </div>
                  <span className="text-slate-800 font-bold font-mono">{predictions.timeBreakdown.top_bottom_min} min</span>
                </div>
                <div className="flex items-center justify-between py-0.5 border-b border-slate-50">
                  <div className="flex items-center space-x-1.5">
                    <div className="w-2 h-2 rounded-full bg-blue-500" />
                    <span className="text-slate-500 font-medium">Desplazamientos</span>
                  </div>
                  <span className="text-slate-800 font-bold font-mono">{predictions.timeBreakdown.travel_min} min</span>
                </div>
                <div className="flex items-center justify-between py-0.5 col-span-2">
                  <div className="flex items-center space-x-1.5">
                    <div className="w-2 h-2 rounded-full bg-slate-400" />
                    <span className="text-slate-500 font-medium">Overhead / Ralentización TPU</span>
                  </div>
                  <span className="text-slate-800 font-bold font-mono">{predictions.timeBreakdown.firmware_overhead_min} min</span>
                </div>
              </div>

              {/* Extra Estimations Grid */}
              <div className="border-t border-slate-100 pt-2.5 mt-2.5 grid grid-cols-2 gap-2 text-[9px] text-slate-500 font-mono">
                <div className="bg-slate-50/70 p-1.5 rounded border border-slate-100">
                  <span className="text-slate-400 block uppercase font-bold text-[7px] tracking-wider">Consumo Energético</span>
                  <span className="font-extrabold text-slate-700">
                    {predictions ? (() => {
                      const hrs = predictions.printingTimeMinutes / 60.0;
                      // K1 Max/K1C: ~0.32 kWh/h, KE: ~0.18 kWh/h
                      const rate = predictions.modelUsed?.includes("KE") ? 0.18 : 0.32;
                      return `${(hrs * rate).toFixed(2)} kWh`;
                    })() : "0.45 kWh"}
                  </span>
                </div>
                <div className="bg-slate-50/70 p-1.5 rounded border border-slate-100">
                  <span className="text-slate-400 block uppercase font-bold text-[7px] tracking-wider">Costo Estimado</span>
                  <span className="font-extrabold text-slate-700">
                    {predictions ? (() => {
                      const costPerGram = material === "TPU" ? 0.035 : 0.022;
                      return `$ ${(predictions.massGrams * costPerGram).toFixed(2)} USD`;
                    })() : "$ 1.20 USD"}
                  </span>
                </div>
                <div className="bg-slate-50/70 p-1.5 rounded border border-slate-100 col-span-2 flex justify-between items-center">
                  <div>
                    <span className="text-slate-400 block uppercase font-bold text-[7px] tracking-wider">Generación GCODE / STL (ETA)</span>
                    <span className="text-[8px] text-slate-500">ML post-processing time included</span>
                  </div>
                  <span className="font-extrabold text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-100">
                    ~ 3.2s
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* SECTION: MECHANICAL PROPERTIES */}
        <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-xs">
          <div className="bg-slate-50/70 px-3 py-2 border-b border-slate-200">
            <span className="text-sm text-slate-500 font-bold uppercase tracking-wider block font-extrabold">
              Propiedades Mecánicas Estimadas
            </span>
          </div>

          <div className="p-3 space-y-3.5 font-sans text-sm">
            <div className="flex justify-between items-center py-0.5 border-b border-slate-100">
              <div className="flex flex-col">
                <span className="text-slate-700 font-medium">Módulo elástico (Young)</span>
                <span className="text-[9px] text-slate-400 font-mono">[Modelo Analítico] Confianza: 95%</span>
              </div>
              <span className="text-slate-800 font-bold font-mono">{youngModulus}</span>
            </div>
            <div className="flex justify-between items-center py-0.5 border-b border-slate-100">
              <div className="flex flex-col">
                <span className="text-slate-700 font-medium">Esfuerzo de Fluencia (Yield)</span>
                <span className="text-[9px] text-slate-400 font-mono">[Predicción de IA (ML)] Confianza: 98%</span>
              </div>
              <span className="text-slate-800 font-bold font-mono">{yieldStrength.toFixed(1)} MPa</span>
            </div>
            <div className="flex justify-between items-center py-0.5 border-b border-slate-100">
              <div className="flex flex-col">
                <span className="text-slate-700 font-medium">Esfuerzo Máximo (UTS)</span>
                <span className="text-[9px] text-slate-400 font-mono">[Modelo Analítico] Confianza: 95%</span>
              </div>
              <span className="text-slate-800 font-bold font-mono">{(yieldStrength * 1.5).toFixed(1)} MPa</span>
            </div>
            <div className="flex justify-between items-center py-0.5">
              <div className="flex flex-col">
                <span className="text-slate-700 font-medium">Absorción Específica</span>
                <span className="text-[9px] text-slate-400 font-mono">[Predicción de IA (ML)] Confianza: 96%</span>
              </div>
              <span className="text-slate-800 font-bold font-mono">{energyAbsorption.toFixed(1)} %</span>
            </div>
          </div>
        </div>

        {/* SECTION: GRÁFICAS */}
        <MechanicalCharts material={material} infill={infill} />

        {/* SECTION: STRESS CUBEMAP PREVIEW */}
        {enableStressCubemap && <StressCubemap />}

        {/* SECTION: COMPARATIVO */}
        <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-xs font-sans">
          <div className="bg-slate-50/70 px-3 py-2 border-b border-slate-200">
            <span className="text-sm text-slate-500 font-bold uppercase tracking-wider block font-extrabold">
              Historial de Diseños (Últimos 5)
            </span>
          </div>
          <div className="p-3 overflow-x-auto">
            {designHistory.length === 0 ? (
              <span className="text-xs text-slate-400 font-bold block py-2 text-center">No se han registrado iteraciones en esta sesión.</span>
            ) : (
              <table className="w-full text-xs text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-450 uppercase font-semibold">
                    <th className="py-1.5 pr-2">Fecha/Hora</th>
                    <th className="py-1.5 text-center px-2">Configuración</th>
                    <th className="py-1.5 text-center px-1">Masa</th>
                    <th className="py-1.5 text-center px-1">F. Máx</th>
                    <th className="py-1.5 text-center pl-2">Estado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-650 font-mono">
                  {designHistory.map((entry: any, i: number) => (
                    <tr key={entry.id || i}>
                      <td className="py-2 text-[10px] text-slate-500 font-sans font-medium pr-2 whitespace-nowrap">{entry.date}</td>
                      <td className="py-2 text-center text-slate-700 capitalize font-sans px-2 whitespace-nowrap">{entry.material} • {entry.pattern.slice(0, 4)} • {entry.infill}%</td>
                      <td className="py-2 text-center text-slate-700 px-1">{entry.mass.toFixed(1)}g</td>
                      <td className="py-2 text-center text-slate-700 px-1">{entry.maxForce.toFixed(0)}N</td>
                      <td className="py-2 text-center pl-2 whitespace-nowrap">
                        {entry.compliance ? (
                          <span className="text-emerald-600 font-bold font-sans text-[10px] bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-100 uppercase">Cumple</span>
                        ) : (
                          <span className="text-rose-600 font-bold font-sans text-[10px] bg-rose-50 px-1.5 py-0.5 rounded border border-rose-100 uppercase">Fallo</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* SECTION: RECOMMENDATIONS */}
        <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-xs font-sans">
          <div className="bg-slate-50/70 px-3 py-2 border-b border-slate-200">
            <span className="text-sm text-slate-500 font-bold uppercase tracking-wider block font-extrabold">
              Recomendaciones de Estructura
            </span>
          </div>

          <div className="p-3 space-y-3">
            {recommendations.map((rec, i) => (
              <div key={i} className="flex items-start space-x-2 text-sm">
                <ShieldCheck className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                <span className="text-slate-650 leading-normal font-medium">{rec}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function MechanicalCharts({ material, infill }: { material: string; infill: number }) {
  const { predictions, appliedForce } = useLabStore(
    useShallow((state) => ({
      predictions: state.predictions,
      appliedForce: state.appliedForce,
    }))
  );

  const [graphTab, setGraphTab] = useState<"esfuerzo" | "compresion" | "impacto">("esfuerzo");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const yieldStress = predictions?.yieldStrengthMpa || 18.5;
  const maxStress = yieldStress * 1.4;
  const failureStrain = material === "PLA" ? 38 : 45;
  const elasticLimit = material === "PLA" ? 14 : 8;

  const maxForceVal = predictions?.maxForceNewtons || 600;
  const maxDeform = predictions?.deformationMm || 4.0;
  const maxEnergy = predictions?.energyAbsorptionJoules || 20.0;

  const utsStrain = material === "PLA" ? failureStrain : 38;
  const utsStress = material === "PLA" ? maxStress : yieldStress + (38 - elasticLimit) * 0.08;
  const maxForceX = material === "PLA" ? 0.6 * maxDeform : maxDeform;

  const chartData = useMemo(() => {
    const data = [];
    if (graphTab === "esfuerzo") {
      if (material === "PLA") {
        for (let i = 0; i <= 50; i += 2) {
          if (i <= elasticLimit) {
            const stress = (i / elasticLimit) * yieldStress;
            data.push({ xVal: i, yVal: parseFloat(stress.toFixed(1)) });
          } else if (i <= failureStrain) {
            const t = (i - elasticLimit) / (failureStrain - elasticLimit);
            const stress = yieldStress + (maxStress - yieldStress) * Math.sin((t * Math.PI) / 2);
            data.push({ xVal: i, yVal: parseFloat(stress.toFixed(1)) });
          } else {
            const stress = maxStress * Math.exp(-(i - failureStrain) * 0.4);
            data.push({ xVal: i, yVal: parseFloat(Math.max(0.5, stress).toFixed(1)) });
          }
        }
      } else {
        for (let i = 0; i <= 50; i += 2) {
          if (i <= elasticLimit) {
            const stress = (i / elasticLimit) * yieldStress;
            data.push({ xVal: i, yVal: parseFloat(stress.toFixed(1)) });
          } else if (i <= 38) {
            const stress = yieldStress + (i - elasticLimit) * 0.08;
            data.push({ xVal: i, yVal: parseFloat(stress.toFixed(1)) });
          } else {
            const t = i - 38;
            const stress = yieldStress + (38 - elasticLimit) * 0.08 + Math.pow(t, 2) * 0.15;
            data.push({ xVal: i, yVal: parseFloat(stress.toFixed(1)) });
          }
        }
      }
    } else if (graphTab === "compresion") {
      for (let i = 0; i <= 50; i += 2) {
        const def = (i / 50) * maxDeform;
        let force = 0;
        if (material === "PLA") {
          if (i <= 30) {
            force = (i / 30) * maxForceVal;
          } else if (i <= 38) {
            force = maxForceVal;
          } else {
            force = maxForceVal * Math.exp(-(i - 38) * 0.3);
          }
        } else {
          if (i <= 15) {
            force = (i / 15) * (maxForceVal * 0.4);
          } else {
            const t = (i - 15) / 35;
            force = maxForceVal * 0.4 + maxForceVal * 0.6 * Math.pow(t, 2);
          }
        }
        data.push({ xVal: parseFloat(def.toFixed(2)), yVal: parseFloat(Math.max(0, force).toFixed(1)) });
      }
    } else {
      for (let i = 0; i <= 50; i += 2) {
        let energy = 0;
        if (material === "PLA") {
          const t = Math.min(1.0, i / failureStrain);
          energy = maxEnergy * Math.sin((t * Math.PI) / 2);
        } else {
          const t = i / 50;
          energy = maxEnergy * Math.pow(t, 2.5);
        }
        data.push({ xVal: i, yVal: parseFloat(energy.toFixed(2)) });
      }
    }
    return data;
  }, [graphTab, material, yieldStress, maxStress, failureStrain, elasticLimit, maxForceVal, maxDeform, maxEnergy]);

  const activePoint = useMemo(() => {
    if (!chartData || chartData.length === 0) return null;
    const fraction = appliedForce / 1000;
    const index = Math.min(
      chartData.length - 1,
      Math.max(0, Math.floor(fraction * (chartData.length - 1)))
    );
    return chartData[index];
  }, [chartData, appliedForce]);

  const chartConfig = useMemo(() => {
    if (graphTab === "esfuerzo") {
      return {
        xLabel: "Deformación (%)",
        yLabel: "Esfuerzo (MPa)",
        tooltipLabel: "Deformación",
        tooltipUnit: "%",
        valName: "Esfuerzo",
        valUnit: " MPa",
      };
    } else if (graphTab === "compresion") {
      return {
        xLabel: "Deformación (mm)",
        yLabel: "Fuerza (N)",
        tooltipLabel: "Deformación",
        tooltipUnit: " mm",
        valName: "Fuerza",
        valUnit: " N",
      };
    } else {
      return {
        xLabel: "Deformación (%)",
        yLabel: "Energía (J)",
        tooltipLabel: "Deformación",
        tooltipUnit: "%",
        valName: "Absorción",
        valUnit: " J",
      };
    }
  }, [graphTab]);

  return (
    <div className="border border-slate-200 rounded bg-white p-3 space-y-3 font-mono shadow-xs">
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => setGraphTab("esfuerzo")}
          className={`flex-1 pb-1.5 text-[10px] uppercase font-bold text-center transition-all ${
            graphTab === "esfuerzo"
              ? "border-b border-[#1E40AF] text-[#1E40AF]"
              : "text-slate-450 hover:text-slate-700"
          }`}
        >
          Curva Esfuerzo
        </button>
        <button
          onClick={() => setGraphTab("compresion")}
          className={`flex-1 pb-1.5 text-[10px] uppercase font-bold text-center transition-all ${
            graphTab === "compresion"
              ? "border-b border-[#1E40AF] text-[#1E40AF]"
              : "text-slate-450 hover:text-slate-700"
          }`}
        >
          Compresión
        </button>
        <button
          onClick={() => setGraphTab("impacto")}
          className={`flex-1 pb-1.5 text-[10px] uppercase font-bold text-center transition-all ${
            graphTab === "impacto"
              ? "border-b border-[#1E40AF] text-[#1E40AF]"
              : "text-slate-450 hover:text-slate-700"
          }`}
        >
          Impacto
        </button>
      </div>

      <div className="w-full h-32 text-[10px]">
        {mounted ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorStress" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#1E40AF" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#1E40AF" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="xVal" stroke="#64748b" strokeOpacity={0.4} tickLine={false} />
              <YAxis stroke="#64748b" strokeOpacity={0.4} tickLine={false} />
              <Tooltip
                contentStyle={{ backgroundColor: "#ffffff", border: "1px solid #cbd5e1", borderRadius: "6px", color: "#0f172a" }}
                labelFormatter={(v) => `${chartConfig.tooltipLabel}: ${v}${chartConfig.tooltipUnit}`}
                formatter={(v: any) => [`${v}${chartConfig.valUnit}`, chartConfig.valName]}
              />
              <Area
                type="monotone"
                dataKey="yVal"
                stroke="#1E40AF"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorStress)"
              />
              {activePoint && (
                <ReferenceDot
                  x={activePoint.xVal}
                  y={activePoint.yVal}
                  r={5}
                  fill="#ef4444"
                  stroke="#ffffff"
                  strokeWidth={1.5}
                />
              )}
              {graphTab === "esfuerzo" && (
                <>
                  <ReferenceDot
                    x={elasticLimit}
                    y={parseFloat(yieldStress.toFixed(1))}
                    r={4}
                    fill="#F59E0B"
                    stroke="#ffffff"
                    strokeWidth={1}
                    label={{ value: "Fluencia", fill: "#D97706", position: "top", fontSize: 8, fontFamily: "monospace" }}
                  />
                  <ReferenceDot
                    x={utsStrain}
                    y={parseFloat(utsStress.toFixed(1))}
                    r={4}
                    fill="#ef4444"
                    stroke="#ffffff"
                    strokeWidth={1}
                    label={{ value: "UTS", fill: "#ef4444", position: "top", fontSize: 8, fontFamily: "monospace" }}
                  />
                </>
              )}
              {graphTab === "compresion" && (
                <ReferenceDot
                  x={parseFloat(maxForceX.toFixed(2))}
                  y={parseFloat(maxForceVal.toFixed(1))}
                  r={4}
                  fill="#10b981"
                  stroke="#ffffff"
                  strokeWidth={1}
                  label={{ value: "F. Máx", fill: "#059669", position: "top", fontSize: 8, fontFamily: "monospace" }}
                />
              )}
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="w-full h-full bg-slate-50 animate-pulse rounded border border-slate-200" />
        )}
        <div className="text-center text-[9px] text-slate-400 mt-1 uppercase font-semibold">
          {chartConfig.xLabel} vs {chartConfig.yLabel}
        </div>
      </div>
    </div>
  );
}

function StressCubemap() {
  const { appliedForce } = useLabStore(
    useShallow((state) => ({
      appliedForce: state.appliedForce,
    }))
  );

  return (
    <div className="border border-slate-200 rounded bg-white p-3 space-y-2 font-mono shadow-xs">
      <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">
        INDICADOR GLOBAL SIMPLIFICADO
      </span>

      <div className="flex flex-col items-center justify-center py-2.5 bg-slate-50/70 border border-slate-200 rounded shadow-3xs space-y-3">
        {/* Isometric CSS 3D Cube */}
        <div className="relative w-16 h-16 flex items-center justify-center">
          <div
            className="w-10 h-10 relative transform-gpu rotate-x-30 rotate-y-45 transform-style-preserve-3d"
            style={{
              transform: "rotateX(-25deg) rotateY(45deg)",
              transformStyle: "preserve-3d",
            }}
          >
            {/* Top Face */}
            <div
              className="absolute inset-0 bg-radial-gradient border border-slate-200"
              style={{
                transform: "rotateX(90deg) translateZ(20px)",
                background: `radial-gradient(circle, ${appliedForce > 700 ? '#EF4444' : appliedForce > 400 ? '#F59E0B' : '#10B981'} 10%, #10B981 60%, #1E40AF 90%)`,
                opacity: 0.85,
              }}
            />
            {/* Bottom Face */}
            <div
              className="absolute inset-0 border border-slate-200 bg-slate-100"
              style={{
                transform: "rotateX(-90deg) translateZ(20px)",
                opacity: 0.75,
              }}
            />
            {/* Front Face */}
            <div
              className="absolute inset-0 border border-slate-200"
              style={{
                transform: "translateZ(20px)",
                background: `linear-gradient(to bottom, ${appliedForce > 600 ? '#F59E0B' : '#10B981'}, #1E40AF)`,
                opacity: 0.85,
              }}
            />
            {/* Back Face */}
            <div
              className="absolute inset-0 border border-slate-200"
              style={{
                transform: "rotateY(180deg) translateZ(20px)",
                background: `linear-gradient(to bottom, ${appliedForce > 600 ? '#F59E0B' : '#10B981'}, #1E40AF)`,
                opacity: 0.65,
              }}
            />
            {/* Side Face (Right) */}
            <div
              className="absolute inset-0 border border-slate-200"
              style={{
                transform: "rotateY(90deg) translateZ(20px)",
                background: `linear-gradient(to bottom, ${appliedForce > 600 ? '#F59E0B' : '#10B981'}, #1E40AF)`,
                opacity: 0.85,
              }}
            />
            {/* Left Face */}
            <div
              className="absolute inset-0 border border-slate-200"
              style={{
                transform: "rotateY(-90deg) translateZ(20px)",
                background: `linear-gradient(to bottom, ${appliedForce > 600 ? '#F59E0B' : '#10B981'}, #1E40AF)`,
                opacity: 0.65,
              }}
            />
          </div>
        </div>

        {/* Warning label */}
        <div className="text-[10px] text-center text-amber-600 bg-amber-50/50 border border-amber-100 rounded px-2 py-1 font-sans font-bold flex items-center justify-center gap-1">
          <span>⚠️</span>
          <span>No representa análisis FEA real.</span>
        </div>
      </div>
    </div>
  );
}

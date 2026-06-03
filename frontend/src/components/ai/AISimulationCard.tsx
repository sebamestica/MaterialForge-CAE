"use client";

import React from "react";
import { useDesignStore } from "../../stores/designStore";
import { Shield, ShieldAlert, Sparkles, X } from "lucide-react";

export default function AISimulationCard() {
  const { simulationResults, loading, error } = useDesignStore();

  if (loading) {
    return (
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 font-sans text-xs space-y-2 text-center animate-pulse shadow-3xs">
        <Sparkles className="w-4.5 h-4.5 mx-auto text-blue-600 animate-spin" />
        <span className="text-slate-500 font-semibold">Ejecutando Simulación Estructural ML...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 font-sans text-xs text-rose-700 leading-normal shadow-3xs">
        Error en simulación: {error}
      </div>
    );
  }

  if (!simulationResults) return null;

  const { stressMpa, deformationMm, energyAbsorption, failureRisk, warnings } = simulationResults;

  const riskClasses: Record<string, string> = {
    LOW: "text-emerald-700 border-emerald-250 bg-emerald-50/50",
    MEDIUM: "text-amber-800 border-amber-250 bg-amber-50/50",
    HIGH: "text-rose-700 border-rose-250 bg-rose-50/50"
  };

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 font-sans text-xs space-y-3.5 shadow-2xs animate-fadeIn">
      {/* Title */}
      <div className="flex justify-between items-center border-b border-slate-200 pb-2">
        <span className="font-extrabold uppercase text-[10px] text-slate-755 tracking-wider flex items-center gap-1.5">
          <Shield className="w-4 h-4 text-blue-650" />
          Reporte de Simulación Virtual ML
        </span>
        <button
          onClick={() => useDesignStore.setState({ simulationResults: null })}
          className="text-slate-400 hover:text-slate-650 cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Grid Indicators */}
      <div className="grid grid-cols-2 gap-2.5 text-slate-650">
        <div className="bg-white p-2.5 rounded-lg border border-slate-200 shadow-3xs">
          <span className="block text-[9px] text-slate-400 uppercase font-bold mb-0.5">Esfuerzo Máx</span>
          <span className="text-slate-800 text-sm font-black">{stressMpa.toFixed(2)} MPa</span>
        </div>
        <div className="bg-white p-2.5 rounded-lg border border-slate-200 shadow-3xs">
          <span className="block text-[9px] text-slate-400 uppercase font-bold mb-0.5">Deformación Est.</span>
          <span className="text-slate-800 text-sm font-black">{deformationMm.toFixed(2)} mm</span>
        </div>
        <div className="bg-white p-2.5 rounded-lg border border-slate-200 shadow-3xs">
          <span className="block text-[9px] text-slate-400 uppercase font-bold mb-0.5">Absorción Energía</span>
          <span className="text-slate-800 text-sm font-black">{energyAbsorption.toFixed(2)} MJ/m³</span>
        </div>
        <div className="bg-white p-2.5 rounded-lg border border-slate-200 shadow-3xs flex flex-col justify-between">
          <span className="block text-[9px] text-slate-400 uppercase font-bold mb-1">Riesgo Fallo</span>
          <span className={`px-2 py-0.5 rounded-md text-[9px] font-black border uppercase tracking-wider text-center ${
            riskClasses[failureRisk] || riskClasses.LOW
          }`}>
            {failureRisk}
          </span>
        </div>
      </div>

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 p-2.5 rounded-lg text-amber-800 space-y-1 text-xs">
          <span className="font-extrabold uppercase text-[9px] tracking-wider block flex items-center gap-1 text-amber-750">
            <ShieldAlert className="w-4 h-4 text-amber-600 animate-pulse" />
            Alertas de Inferencia
          </span>
          {warnings.map((w, i) => (
            <p key={i} className="text-[11px] leading-snug">• {w}</p>
          ))}
        </div>
      )}
    </div>
  );
}

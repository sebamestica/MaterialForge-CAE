"use client";

import React from "react";
import { useDesignStore } from "../../stores/designStore";
import { Shield, ShieldAlert, Sparkles, X } from "lucide-react";

export default function AISimulationCard() {
  const { simulationResults, loading, error } = useDesignStore();

  if (loading) {
    return (
      <div className="bg-slate-950/40 border border-slate-800 rounded-lg p-4 font-mono text-[10px] space-y-2 text-center animate-pulse">
        <Sparkles className="w-4 h-4 mx-auto text-blue-500 animate-spin" />
        <span className="text-slate-400">Ejecutando Simulación Estructural ML...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-950/20 border border-rose-900/40 rounded-lg p-3.5 font-mono text-[10px] text-rose-300">
        Error en simulación: {error}
      </div>
    );
  }

  if (!simulationResults) return null;

  const { stressMpa, deformationMm, energyAbsorption, failureRisk, warnings } = simulationResults;

  const riskClasses: Record<string, string> = {
    LOW: "text-emerald-400 border-emerald-950 bg-emerald-950/20",
    MEDIUM: "text-amber-400 border-amber-950 bg-amber-950/20",
    HIGH: "text-rose-400 border-rose-950 bg-rose-950/20"
  };

  return (
    <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3.5 font-mono text-[10px] space-y-3 shadow-md animate-fadeIn">
      {/* Title */}
      <div className="flex justify-between items-center border-b border-slate-900 pb-2">
        <span className="font-extrabold uppercase text-[9px] text-slate-400 tracking-wider flex items-center gap-1.5">
          <Shield className="w-3.5 h-3.5 text-blue-400" />
          Reporte de Simulación Virtual ML
        </span>
        <button
          onClick={() => useDesignStore.setState({ simulationResults: null })}
          className="text-slate-500 hover:text-slate-350 cursor-pointer"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Grid Indicators */}
      <div className="grid grid-cols-2 gap-2 text-slate-400">
        <div className="bg-slate-950/80 p-2 rounded border border-slate-900">
          <span className="block text-[8px] text-slate-500 uppercase font-black">Esfuerzo Máx</span>
          <span className="text-white text-xs font-black">{stressMpa.toFixed(2)} MPa</span>
        </div>
        <div className="bg-slate-950/80 p-2 rounded border border-slate-900">
          <span className="block text-[8px] text-slate-500 uppercase font-black">Deformación Est.</span>
          <span className="text-white text-xs font-black">{deformationMm.toFixed(2)} mm</span>
        </div>
        <div className="bg-slate-950/80 p-2 rounded border border-slate-900">
          <span className="block text-[8px] text-slate-500 uppercase font-black">Absorción Energía</span>
          <span className="text-white text-xs font-black">{energyAbsorption.toFixed(2)} MJ/m³</span>
        </div>
        <div className="bg-slate-950/80 p-2 rounded border border-slate-900 flex flex-col justify-between">
          <span className="block text-[8px] text-slate-500 uppercase font-black">Riesgo Fallo</span>
          <span className={`px-1.5 py-0.5 rounded text-[8px] font-black border uppercase tracking-wider text-center ${
            riskClasses[failureRisk] || riskClasses.LOW
          }`}>
            {failureRisk}
          </span>
        </div>
      </div>

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="bg-amber-950/10 border border-amber-900/30 p-2 rounded text-amber-400 space-y-1">
          <span className="font-extrabold uppercase text-[8px] tracking-wider block flex items-center gap-1">
            <ShieldAlert className="w-3.5 h-3.5" />
            Alertas de Inferencia
          </span>
          {warnings.map((w, i) => (
            <p key={i} className="text-[8px] leading-tight">• {w}</p>
          ))}
        </div>
      )}
    </div>
  );
}

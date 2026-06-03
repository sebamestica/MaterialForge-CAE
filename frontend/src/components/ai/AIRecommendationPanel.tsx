"use client";

import React, { useEffect } from "react";
import { useDesignStore } from "../../stores/designStore";
import { useLabStore } from "../../stores/useLabStore";
import AIActionBar from "./AIActionBar";
import VariantList from "./VariantList";
import ConfigDiff from "./ConfigDiff";
import AISimulationCard from "./AISimulationCard";
import { Activity, Clock, RotateCcw } from "lucide-react";

export default function AIRecommendationPanel() {
  const labStore = useLabStore();
  const {
    aiRecommendations,
    variants,
    variantHistory,
    revertLastPatch,
    fetchHistory,
    compareMode,
    loading
  } = useDesignStore();

  useEffect(() => {
    fetchHistory();
  }, []);

  // Calculate live engineering score for active design state
  const calculateLiveScore = () => {
    const config = {
      material: labStore.material,
      cellSize: labStore.cellSize,
      wallThickness: labStore.wallThickness,
      printSpeed: labStore.printSpeed,
      layerHeight: labStore.layerHeight,
    };
    const predictions = labStore.predictions;
    
    const material = (config.material || "TPU").toUpperCase();
    const maxStress = predictions?.yieldStrengthMpa || 15.0;
    const energyDens = predictions?.energyAbsorptionJoules || 5.0;
    const mass = predictions?.massGrams || 50.0;
    
    const cStrength = Math.min(100.0, maxStress * (material === "PLA" ? 2.0 : 3.5));
    const cSize = config.cellSize || 5.0;
    const wThick = config.wallThickness || 1.2;
    const cStability = Math.min(100.0, Math.max(0.0, (wThick / 2.0) * 60.0 + (1.0 - (Math.abs(cSize - 5.0) / 5.0)) * 40.0));
    const cAbsorption = Math.min(100.0, energyDens * (material === "TPU" ? 6.0 : 15.0));
    const cManufacturability = Math.max(10.0, 100.0 - Math.abs((config.printSpeed || 40.0) - 40.0) * 0.5 - Math.abs((config.layerHeight || 0.2) - 0.2) * 100.0);
    
    let cPrintability = 50.0;
    if (material === "TPU") {
      cPrintability = Math.max(10.0, 100.0 - Math.max(0.0, (config.printSpeed || 30.0) - 25.0) * 1.5);
    } else {
      cPrintability = Math.max(50.0, 100.0 - Math.max(0.0, (config.printSpeed || 50.0) - 60.0) * 0.5);
    }
    
    const cEfficiency = Math.max(0.0, 100.0 - mass);
    
    const overall = (
      0.40 * cStrength +
      0.20 * cStability +
      0.15 * cAbsorption +
      0.10 * cManufacturability +
      0.10 * cPrintability +
      0.05 * cEfficiency
    );
    
    return {
      compression: Math.round(cStrength),
      stability: Math.round(cStability),
      absorption: Math.round(cAbsorption),
      manufacturability: Math.round(cManufacturability),
      printability: Math.round(cPrintability),
      efficiency: Math.round(cEfficiency),
      overall: Math.round(overall)
    };
  };

  const scores = calculateLiveScore();

  // Use chat recommendations if available, otherwise fallback to precompiled variants
  const activeVariants = aiRecommendations?.variants || variants || [];

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-lg p-4 space-y-4 overflow-y-auto font-sans text-xs scrollbar-thin scrollbar-thumb-slate-200">
      
      {/* 1. Header */}
      <div className="flex justify-between items-center border-b border-slate-100 pb-2.5">
        <span className="font-extrabold uppercase text-xs tracking-wider text-slate-800 flex items-center gap-1.5">
          <Activity className="w-4 h-4 text-blue-600 animate-pulse" />
          Métricas de Co-Diseño CAE
        </span>
        <span className="text-[9px] bg-slate-100 border border-slate-200 px-2 py-0.5 rounded-md text-slate-650 uppercase tracking-wider font-bold">
          scoring v1
        </span>
      </div>

      {/* 2. Active Design Score Card */}
      <div className="bg-slate-50 border border-slate-250/70 p-3.5 rounded-xl space-y-3 shadow-3xs">
        <div className="flex justify-between items-center">
          <span className="text-slate-500 font-extrabold uppercase text-[10px] tracking-wider">Score Estructural Actual</span>
          <span className={`text-base font-black ${
            scores.overall >= 75 ? "text-emerald-600" : scores.overall >= 50 ? "text-amber-600" : "text-rose-600"
          }`}>
            {scores.overall}/100
          </span>
        </div>
        
        {/* Progress bar */}
        <div className="w-full h-1.5 bg-slate-200 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-300 ${
              scores.overall >= 75 ? "bg-emerald-500" : scores.overall >= 50 ? "bg-amber-500" : "bg-rose-500"
            }`}
            style={{ width: `${scores.overall}%` }}
          />
        </div>

        {/* Breakdown */}
        <div className="grid grid-cols-3 gap-2 pt-1">
          <div className="bg-white p-2 rounded-lg border border-slate-200/80 shadow-3xs">
            <span className="block text-slate-400 text-[9px] uppercase font-bold leading-tight">Comp. (40%)</span>
            <span className="font-bold text-slate-800 text-sm">{scores.compression}</span>
          </div>
          <div className="bg-white p-2 rounded-lg border border-slate-200/80 shadow-3xs">
            <span className="block text-slate-400 text-[9px] uppercase font-bold leading-tight">Est. (20%)</span>
            <span className="font-bold text-slate-800 text-sm">{scores.stability}</span>
          </div>
          <div className="bg-white p-2 rounded-lg border border-slate-200/80 shadow-3xs">
            <span className="block text-slate-400 text-[9px] uppercase font-bold leading-tight">Abs. (15%)</span>
            <span className="font-bold text-slate-800 text-sm">{scores.absorption}</span>
          </div>
          <div className="bg-white p-2 rounded-lg border border-slate-200/80 shadow-3xs">
            <span className="block text-slate-400 text-[9px] uppercase font-bold leading-tight">Mfg. (10%)</span>
            <span className="font-bold text-slate-800 text-sm">{scores.manufacturability}</span>
          </div>
          <div className="bg-white p-2 rounded-lg border border-slate-200/80 shadow-3xs">
            <span className="block text-slate-400 text-[9px] uppercase font-bold leading-tight">Imp. (10%)</span>
            <span className="font-bold text-slate-800 text-sm">{scores.printability}</span>
          </div>
          <div className="bg-white p-2 rounded-lg border border-slate-200/80 shadow-3xs">
            <span className="block text-slate-400 text-[9px] uppercase font-bold leading-tight">Efic. (5%)</span>
            <span className="font-bold text-slate-800 text-sm">{scores.efficiency}</span>
          </div>
        </div>
      </div>

      {/* 3. Quick Actions Toolbar */}
      <AIActionBar />

      {/* 4. Comparison Overlay panel */}
      {compareMode && <ConfigDiff />}

      {/* 5. Simulation Output Card */}
      <AISimulationCard />

      {/* 6. Generative Candidates List */}
      <div className="space-y-2.5">
        <span className="font-black text-slate-500 uppercase text-[10px] tracking-wider block">
          Candidatos Estructurales
        </span>
        <VariantList variants={activeVariants} />
      </div>

      {/* 7. Change History Logs */}
      <div className="border-t border-slate-200 pt-4 space-y-2.5">
        <div className="flex justify-between items-center text-[10px] uppercase font-black text-slate-500">
          <span className="flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-slate-400" />
            Registro de Operaciones
          </span>
          {variantHistory.length > 0 && (
            <button
              onClick={revertLastPatch}
              disabled={loading}
              className="text-[9px] text-amber-600 hover:text-amber-700 hover:underline flex items-center gap-0.5 cursor-pointer disabled:opacity-40 uppercase font-black tracking-wide"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Deshacer</span>
            </button>
          )}
        </div>

        <div className="max-h-[100px] overflow-y-auto space-y-1.5 text-xs text-slate-600 scrollbar-thin scrollbar-thumb-slate-200">
          {variantHistory.length > 0 ? (
            variantHistory.slice().reverse().map((h, idx) => (
              <div key={idx} className="flex justify-between bg-slate-50 p-2 px-3 rounded-lg border border-slate-200/60 font-mono text-[10px]">
                <span className="text-slate-700">
                  {h.action === "applied_config" ? "🛠 parche aplicado" : "↩ snapshot revertido"}
                </span>
                <span className="text-slate-400">
                  {new Date(h.timestamp).toLocaleTimeString()}
                </span>
              </div>
            ))
          ) : (
            <p className="italic text-slate-400 text-xs text-center p-3.5 border border-slate-200 border-dashed rounded-lg bg-slate-50/50">
              No hay acciones registradas en esta sesión.
            </p>
          )}
        </div>
      </div>

    </div>
  );
}

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
    <div className="flex flex-col h-full bg-slate-950/20 border border-slate-800 rounded-lg p-4 space-y-4 overflow-y-auto font-mono text-[10px] scrollbar-thin scrollbar-thumb-slate-800">
      
      {/* 1. Header */}
      <div className="flex justify-between items-center border-b border-slate-800 pb-2">
        <span className="font-extrabold uppercase text-[10px] tracking-wider text-slate-200 flex items-center gap-1.5">
          <Activity className="w-3.5 h-3.5 text-blue-500" />
          Métricas de Co-Diseño CAE
        </span>
        <span className="text-[8px] bg-slate-900 border border-slate-850 px-1.5 py-0.5 rounded text-slate-500 uppercase tracking-widest font-black">
          scoring v1
        </span>
      </div>

      {/* 2. Active Design Score Card */}
      <div className="bg-slate-950/60 border border-slate-800 p-3 rounded-md space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-slate-500 font-bold uppercase text-[8px] tracking-wider">Score Estructural Actual</span>
          <span className={`text-sm font-black ${
            scores.overall >= 75 ? "text-emerald-400" : scores.overall >= 50 ? "text-amber-400" : "text-rose-400"
          }`}>
            {scores.overall}/100
          </span>
        </div>
        
        {/* Progress bar */}
        <div className="w-full h-1 bg-slate-900 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-300 ${
              scores.overall >= 75 ? "bg-emerald-500" : scores.overall >= 50 ? "bg-amber-500" : "bg-rose-500"
            }`}
            style={{ width: `${scores.overall}%` }}
          />
        </div>

        {/* Breakdown */}
        <div className="grid grid-cols-3 gap-1.5 pt-1.5 text-[8px] text-slate-400">
          <div className="bg-slate-900/50 p-1.5 rounded border border-slate-900">
            <span className="block text-slate-500">Comp. (40%)</span>
            <span className="font-bold text-slate-200">{scores.compression}</span>
          </div>
          <div className="bg-slate-900/50 p-1.5 rounded border border-slate-900">
            <span className="block text-slate-500">Est. (20%)</span>
            <span className="font-bold text-slate-200">{scores.stability}</span>
          </div>
          <div className="bg-slate-900/50 p-1.5 rounded border border-slate-900">
            <span className="block text-slate-500">Abs. (15%)</span>
            <span className="font-bold text-slate-200">{scores.absorption}</span>
          </div>
          <div className="bg-slate-900/50 p-1.5 rounded border border-slate-900">
            <span className="block text-slate-500">Mfg. (10%)</span>
            <span className="font-bold text-slate-200">{scores.manufacturability}</span>
          </div>
          <div className="bg-slate-900/50 p-1.5 rounded border border-slate-900">
            <span className="block text-slate-500">Imp. (10%)</span>
            <span className="font-bold text-slate-200">{scores.printability}</span>
          </div>
          <div className="bg-slate-900/50 p-1.5 rounded border border-slate-900">
            <span className="block text-slate-500">Efic. (5%)</span>
            <span className="font-bold text-slate-200">{scores.efficiency}</span>
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
      <div className="space-y-2">
        <span className="font-black text-slate-400 uppercase text-[9px] tracking-wider block">
          Candidatos Estructurales
        </span>
        <VariantList variants={activeVariants} />
      </div>

      {/* 7. Change History Logs */}
      <div className="border-t border-slate-800 pt-3 space-y-2">
        <div className="flex justify-between items-center text-[9px] uppercase font-black text-slate-450">
          <span className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            Registro de Operaciones
          </span>
          {variantHistory.length > 0 && (
            <button
              onClick={revertLastPatch}
              disabled={loading}
              className="text-[8px] text-amber-500 hover:text-amber-400 hover:underline flex items-center gap-0.5 cursor-pointer disabled:opacity-40 uppercase font-black tracking-wide"
            >
              <RotateCcw className="w-2.5 h-2.5" />
              <span>undo</span>
            </button>
          )}
        </div>

        <div className="max-h-[90px] overflow-y-auto space-y-1.5 text-[8px] text-slate-550 scrollbar-thin scrollbar-thumb-slate-900">
          {variantHistory.length > 0 ? (
            variantHistory.slice().reverse().map((h, idx) => (
              <div key={idx} className="flex justify-between bg-slate-950/40 p-1.5 px-2.5 rounded border border-slate-900">
                <span>
                  {h.action === "applied_config" ? "🛠 applied patch" : "↩ reverted snapshot"}
                </span>
                <span className="text-slate-650">
                  {new Date(h.timestamp).toLocaleTimeString()}
                </span>
              </div>
            ))
          ) : (
            <p className="italic text-slate-600 text-[9px] text-center p-2 border border-slate-900/60 rounded border-dashed">
              No hay acciones registradas en esta sesión.
            </p>
          )}
        </div>
      </div>

    </div>
  );
}

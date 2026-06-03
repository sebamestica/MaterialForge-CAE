"use client";

import React, { useState } from "react";
import { useDesignStore } from "../../stores/designStore";
import { useLabStore } from "../../stores/useLabStore";
import { applyConfigPatch } from "../../utils/applyConfigPatch";
import { Zap, Dumbbell, Shield, Feather, Scale, Check, RefreshCw } from "lucide-react";

type PresetKey = "strength" | "energy" | "weight" | "balance";

interface PresetInfo {
  label: string;
  icon: React.ComponentType<any>;
  desc: string;
  details: string;
  apiTarget: string;
  colorClass: string;
}

const PRESETS: Record<PresetKey, PresetInfo> = {
  strength: {
    label: "Resistencia",
    icon: Dumbbell,
    desc: "Maximiza la capacidad de carga a compresión estructural.",
    details: "Incrementa el infill y el espesor de pared usando filamento rígido.",
    apiTarget: "strength",
    colorClass: "border-rose-900/40 text-rose-400 hover:border-rose-700 bg-rose-950/10",
  },
  energy: {
    label: "Absorción",
    icon: Shield,
    desc: "Maximiza la absorción de impactos y deformación elástica.",
    details: "Utiliza TPU flexible con retícula Gyroid compacta para amortiguar.",
    apiTarget: "energy",
    colorClass: "border-amber-900/40 text-amber-400 hover:border-amber-700 bg-amber-950/10",
  },
  weight: {
    label: "Ligero",
    icon: Feather,
    desc: "Minimiza la masa total del cubo reduciendo filamento.",
    details: "Reduce el porcentaje de infill al mínimo viable aumentando el tamaño de celda.",
    apiTarget: "lightweight",
    colorClass: "border-emerald-900/40 text-emerald-400 hover:border-emerald-700 bg-emerald-950/10",
  },
  balance: {
    label: "Balance",
    icon: Scale,
    desc: "Optimiza la relación entre rigidez, peso y tiempo de laminación.",
    details: "Configura parámetros intermedios y balanceados para uso general.",
    apiTarget: "balance",
    colorClass: "border-blue-900/40 text-blue-400 hover:border-blue-700 bg-blue-950/10",
  },
};

export default function AIActionBar() {
  const optimizeConfig = useLabStore((state) => state.optimizeConfig);
  const optimizationRecommendations = useLabStore((state) => state.optimizationRecommendations);
  const triggerInference = useLabStore((state) => state.triggerInference);
  const triggerMeshGeneration = useLabStore((state) => state.triggerMeshGeneration);
  
  const loading = useDesignStore((state) => state.loading);

  const [activePreset, setActivePreset] = useState<PresetKey | null>(null);
  const [fetchingPreset, setFetchingPreset] = useState(false);
  const [appliedSuccess, setAppliedSuccess] = useState(false);

  const handlePresetSelect = async (key: PresetKey) => {
    setActivePreset(key);
    setFetchingPreset(true);
    setAppliedSuccess(false);
    
    // Call optimize Config store method (maps in backend to pandas query)
    const apiTarget = PRESETS[key].apiTarget;
    await optimizeConfig(apiTarget);
    setFetchingPreset(false);
  };

  const handleApplyPreset = () => {
    if (!optimizationRecommendations || optimizationRecommendations.length === 0) return;
    
    const rec = optimizationRecommendations[0];
    const params = rec.parameters;
    
    // Map backend params to flat ConfigPatch fields
    const patch = {
      material: String(params.material).toUpperCase(),
      infill: Number(params.infill_density_percent),
      pattern: String(params.infill_pattern).toLowerCase(),
      cellSize: params.cell_size_mm ? Number(params.cell_size_mm) : 5.0,
      wallThickness: Number(params.wall_thickness_mm),
      layerHeight: Number(params.layer_height_mm),
      printSpeed: Number(params.print_speed_mm_s)
    };

    const success = applyConfigPatch(patch);
    if (success) {
      setAppliedSuccess(true);
      // Refresh calculations on Lab Store
      triggerInference();
      triggerMeshGeneration();
      
      // Auto-clear success message after 3 seconds
      setTimeout(() => {
        setAppliedSuccess(false);
      }, 3000);
    }
  };

  const selectedRec = optimizationRecommendations && optimizationRecommendations.length > 0
    ? optimizationRecommendations[0]
    : null;

  return (
    <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-3 font-mono text-[10px] space-y-3 shadow-sm">
      {/* Title */}
      <div className="flex items-center justify-between border-b border-slate-900 pb-1.5">
        <span className="font-extrabold uppercase text-[9px] tracking-wider text-slate-400 flex items-center gap-1.5">
          <Zap className="w-3.5 h-3.5 text-blue-500 animate-pulse" />
          Preconfiguraciones de Diseño
        </span>
        <span className="text-[8px] bg-slate-900 border border-slate-800 px-1 py-0.5 rounded text-slate-500 uppercase tracking-widest font-black">
          presets CAE
        </span>
      </div>

      {/* Grid of 2x2 buttons */}
      <div className="grid grid-cols-2 gap-2">
        {(Object.keys(PRESETS) as PresetKey[]).map((key) => {
          const info = PRESETS[key];
          const Icon = info.icon;
          const isSelected = activePreset === key;
          
          return (
            <button
              key={key}
              onClick={() => handlePresetSelect(key)}
              disabled={loading}
              className={`p-2.5 rounded-lg border text-left cursor-pointer transition-all duration-200 flex flex-col space-y-1.5 focus:outline-none ${
                isSelected
                  ? "bg-blue-950/20 border-blue-500 text-blue-400 shadow-md shadow-blue-500/5 ring-1 ring-blue-500"
                  : info.colorClass
              }`}
            >
              <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-[9px]">
                <Icon className="w-3.5 h-3.5 shrink-0" />
                <span>{info.label}</span>
              </div>
              <p className="text-[8px] leading-tight text-slate-450 line-clamp-2">
                {info.desc}
              </p>
            </button>
          );
        })}
      </div>

      {/* Preset Explanation / Recommendation Details Panel */}
      {activePreset && (
        <div className="bg-slate-950/80 border border-slate-850 p-2.5 rounded-lg space-y-2.5 animate-fadeIn">
          {/* Header Info */}
          <div className="space-y-1">
            <span className="text-[9px] font-black uppercase text-blue-400">
              Preset Seleccionado: {PRESETS[activePreset].label}
            </span>
            <p className="text-slate-450 text-[8px] leading-snug">
              {PRESETS[activePreset].details}
            </p>
          </div>

          {/* Loading details state */}
          {fetchingPreset ? (
            <div className="flex items-center justify-center p-3 text-slate-500 gap-1.5">
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Consultando dataset experimental...</span>
            </div>
          ) : selectedRec ? (
            <div className="space-y-2 bg-slate-900/30 p-2 rounded border border-slate-900">
              {/* Parameters Summary */}
              <div className="grid grid-cols-2 gap-x-2 gap-y-1 border-b border-slate-850 pb-2 text-[8px] text-slate-400">
                <div>
                  <span className="text-slate-500 block">Material</span>
                  <span className="font-extrabold text-slate-350">{selectedRec.parameters.material.toUpperCase()}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Relleno (Infill)</span>
                  <span className="font-extrabold text-slate-350 font-mono">{selectedRec.parameters.infill_density_percent}%</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Espesor Pared</span>
                  <span className="font-extrabold text-slate-350 font-mono">{selectedRec.parameters.wall_thickness_mm.toFixed(1)} mm</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Velocidad</span>
                  <span className="font-extrabold text-slate-350 font-mono">{selectedRec.parameters.print_speed_mm_s} mm/s</span>
                </div>
              </div>

              {/* Performance Estimations */}
              <div className="flex justify-between items-center text-[8px]">
                <div className="space-y-0.5">
                  <span className="text-slate-500 block uppercase font-bold">Rendimiento Estimado</span>
                  <div className="flex gap-2">
                    <span className="text-slate-400">Esfuerzo: <b className="text-slate-200 font-mono">{selectedRec.expected_performance.max_stress_MPa.toFixed(1)} MPa</b></span>
                    <span className="text-slate-400">Energía: <b className="text-slate-200 font-mono">{selectedRec.expected_performance.energy_density_MJ_m3.toFixed(2)} MJ</b></span>
                  </div>
                </div>

                {/* Apply Button */}
                <button
                  onClick={handleApplyPreset}
                  disabled={loading}
                  className={`px-3 py-1.5 rounded text-[8px] font-black uppercase tracking-wider cursor-pointer transition-all duration-200 flex items-center gap-1 ${
                    appliedSuccess
                      ? "bg-emerald-600 hover:bg-emerald-500 text-white"
                      : "bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-500/10"
                  }`}
                >
                  {appliedSuccess ? (
                    <>
                      <Check className="w-3 h-3" />
                      <span>Aplicado</span>
                    </>
                  ) : (
                    <span>Aplicar Preset</span>
                  )}
                </button>
              </div>
            </div>
          ) : (
            <p className="text-slate-500 italic p-2 text-center border border-slate-900 border-dashed rounded text-[8px]">
              No se encontraron datos experimentales en la base de datos para este preset.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

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
  activeClass: string;
}

const PRESETS: Record<PresetKey, PresetInfo> = {
  strength: {
    label: "Resistencia",
    icon: Dumbbell,
    desc: "Maximiza la capacidad de carga a compresión estructural.",
    details: "Incrementa el infill y el espesor de pared usando filamento rígido.",
    apiTarget: "strength",
    colorClass: "border-rose-100 text-rose-700 hover:border-rose-350 bg-white hover:bg-rose-50/20",
    activeClass: "bg-rose-50 border-rose-500 text-rose-900 ring-1 ring-rose-500/50 shadow-sm",
  },
  energy: {
    label: "Absorción",
    icon: Shield,
    desc: "Maximiza la absorción de impactos y deformación elástica.",
    details: "Utiliza TPU flexible con retícula Gyroid compacta para amortiguar.",
    apiTarget: "energy",
    colorClass: "border-amber-100 text-amber-750 hover:border-amber-350 bg-white hover:bg-amber-50/20",
    activeClass: "bg-amber-50 border-amber-500 text-amber-900 ring-1 ring-amber-500/50 shadow-sm",
  },
  weight: {
    label: "Ligero",
    icon: Feather,
    desc: "Minimiza la masa total del cubo reduciendo filamento.",
    details: "Reduce el porcentaje de infill al mínimo viable aumentando el tamaño de celda.",
    apiTarget: "lightweight",
    colorClass: "border-emerald-150 text-emerald-750 hover:border-emerald-350 bg-white hover:bg-emerald-50/20",
    activeClass: "bg-emerald-50 border-emerald-500 text-emerald-900 ring-1 ring-emerald-500/50 shadow-sm",
  },
  balance: {
    label: "Balance",
    icon: Scale,
    desc: "Optimiza la relación entre rigidez, peso y tiempo de laminación.",
    details: "Configura parámetros intermedios y balanceados para uso general.",
    apiTarget: "balance",
    colorClass: "border-blue-100 text-blue-700 hover:border-blue-350 bg-white hover:bg-blue-50/20",
    activeClass: "bg-blue-50 border-blue-500 text-blue-900 ring-1 ring-blue-500/50 shadow-sm",
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
    <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3.5 font-sans text-xs space-y-3.5 shadow-3xs">
      {/* Title */}
      <div className="flex items-center justify-between border-b border-slate-200/85 pb-2">
        <span className="font-extrabold uppercase text-[10px] tracking-wider text-slate-700 flex items-center gap-1.5">
          <Zap className="w-4 h-4 text-blue-600 animate-pulse" />
          Preconfiguraciones de Diseño
        </span>
        <span className="text-[9px] bg-slate-200/50 border border-slate-200 px-1.5 py-0.5 rounded text-slate-500 uppercase tracking-wider font-bold">
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
              className={`p-2.5 rounded-lg border text-left cursor-pointer transition-all duration-200 flex flex-col space-y-1.5 focus:outline-none shadow-3xs ${
                isSelected
                  ? info.activeClass
                  : info.colorClass
              }`}
            >
              <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-[10px]">
                <Icon className="w-3.5 h-3.5 shrink-0" />
                <span>{info.label}</span>
              </div>
              <p className="text-[9px] leading-tight text-slate-500 line-clamp-2">
                {info.desc}
              </p>
            </button>
          );
        })}
      </div>

      {/* Preset Explanation / Recommendation Details Panel */}
      {activePreset && (
        <div className="bg-white border border-slate-200/90 p-3 rounded-lg space-y-3 animate-fadeIn text-xs shadow-2xs">
          {/* Header Info */}
          <div className="space-y-1">
            <span className="text-[10px] font-black uppercase text-blue-600">
              Preset Seleccionado: {PRESETS[activePreset].label}
            </span>
            <p className="text-slate-500 text-xs leading-normal">
              {PRESETS[activePreset].details}
            </p>
          </div>

          {/* Loading details state */}
          {fetchingPreset ? (
            <div className="flex items-center justify-center p-3.5 text-slate-500 gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />
              <span className="font-semibold text-xs">Consultando dataset experimental...</span>
            </div>
          ) : selectedRec ? (
            <div className="space-y-3 bg-slate-50/50 p-2.5 rounded-lg border border-slate-200/80">
              {/* Parameters Summary */}
              <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 border-b border-slate-200/75 pb-2.5 text-xs text-slate-600">
                <div>
                  <span className="text-slate-400 block text-[9px] uppercase font-bold">Material</span>
                  <span className="font-extrabold text-slate-800">{selectedRec.parameters.material.toUpperCase()}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[9px] uppercase font-bold">Relleno (Infill)</span>
                  <span className="font-extrabold text-slate-800 font-mono">{selectedRec.parameters.infill_density_percent}%</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[9px] uppercase font-bold">Espesor Pared</span>
                  <span className="font-extrabold text-slate-800 font-mono">{selectedRec.parameters.wall_thickness_mm.toFixed(1)} mm</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[9px] uppercase font-bold">Velocidad</span>
                  <span className="font-extrabold text-slate-800 font-mono">{selectedRec.parameters.print_speed_mm_s} mm/s</span>
                </div>
              </div>

              {/* Performance Estimations */}
              <div className="flex justify-between items-center text-xs">
                <div className="space-y-0.5">
                  <span className="text-slate-400 block uppercase font-bold text-[9px]">Rendimiento Estimado</span>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-slate-600">Esfuerzo: <b className="text-slate-800 font-mono">{selectedRec.expected_performance.max_stress_MPa.toFixed(1)} MPa</b></span>
                    <span className="text-slate-600">Energía: <b className="text-slate-800 font-mono">{selectedRec.expected_performance.energy_density_MJ_m3.toFixed(2)} MJ</b></span>
                  </div>
                </div>

                {/* Apply Button */}
                <button
                  onClick={handleApplyPreset}
                  disabled={loading}
                  className={`px-3.5 py-2 rounded-lg text-xs font-black uppercase tracking-wider cursor-pointer transition-all duration-200 flex items-center gap-1.5 shadow-sm active:scale-97 ${
                    appliedSuccess
                      ? "bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-500/10 border border-emerald-600"
                      : "bg-blue-600 hover:bg-blue-700 text-white shadow-blue-500/10 border border-blue-600"
                  }`}
                >
                  {appliedSuccess ? (
                    <>
                      <Check className="w-3.5 h-3.5" />
                      <span>Aplicado</span>
                    </>
                  ) : (
                    <span>Aplicar Preset</span>
                  )}
                </button>
              </div>
            </div>
          ) : (
            <p className="text-slate-400 italic p-3 text-center border border-slate-200 border-dashed rounded-lg text-xs bg-slate-50/50">
              No se encontraron datos experimentales en la base de datos para este preset.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

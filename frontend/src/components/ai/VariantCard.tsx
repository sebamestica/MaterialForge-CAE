"use client";

import React from "react";
import { VariantData, useDesignStore } from "../../stores/designStore";
import { Play, Eye, Check, Copy, Download, AlertCircle } from "lucide-react";

interface VariantCardProps {
  variant: VariantData;
  isActive: boolean;
  onSelect: () => void;
}

export default function VariantCard({ variant, isActive, onSelect }: VariantCardProps) {
  const {
    applyPatch,
    setCompareMode,
    setCurrentVariant,
    runSimulation,
    duplicateVariant,
    exportVariant,
  } = useDesignStore();

  const handleApply = async (e: React.MouseEvent) => {
    e.stopPropagation();
    await applyPatch(variant.config_patch);
    alert(`Variante "${variant.name}" aplicada correctamente.`);
  };

  const handleCompare = (e: React.MouseEvent) => {
    e.stopPropagation();
    setCurrentVariant(variant);
    setCompareMode(true);
  };

  const handleSimulate = async (e: React.MouseEvent) => {
    e.stopPropagation();
    await runSimulation(variant.id);
  };

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    duplicateVariant(variant);
  };

  const handleExport = (e: React.MouseEvent) => {
    e.stopPropagation();
    exportVariant(variant);
  };

  const riskColors = {
    LOW: "text-emerald-700 border-emerald-250 bg-emerald-50/50",
    MEDIUM: "text-amber-800 border-amber-250 bg-amber-50/50",
    HIGH: "text-rose-700 border-rose-250 bg-rose-50/50"
  };

  return (
    <div
      onClick={onSelect}
      className={`p-4 rounded-xl border transition-all duration-200 cursor-pointer font-sans text-xs select-none shadow-3xs ${
        isActive
          ? "bg-blue-50/40 border-blue-400 shadow-md shadow-blue-500/5 ring-1 ring-blue-400/20"
          : "bg-white border-slate-200 hover:bg-slate-50/50 hover:border-slate-350"
      }`}
    >
      {/* Title & Risk */}
      <div className="flex justify-between items-start gap-2 mb-2.5">
        <div>
          <h4 className="font-extrabold text-slate-900 text-sm tracking-tight">{variant.name}</h4>
          <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{variant.description}</p>
        </div>
        <span className={`px-2 py-0.5 rounded-md text-[9px] font-black border uppercase tracking-wider shrink-0 ${
          riskColors[variant.risk_level] || riskColors.LOW
        }`}>
          {variant.risk_level}
        </span>
      </div>

      {/* Main Score Bar */}
      <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200/80 mb-3.5 flex items-center justify-between">
        <span className="text-slate-500 uppercase font-extrabold text-[9px] tracking-wider">Score Estructural</span>
        <div className="flex items-center gap-2">
          <div className="w-16 h-1.5 bg-slate-200 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${
                variant.score >= 85 ? "bg-emerald-500" : variant.score >= 65 ? "bg-amber-500" : "bg-rose-500"
              }`}
              style={{ width: `${variant.score}%` }}
            />
          </div>
          <span className="font-black text-slate-800 text-xs">{variant.score}/100</span>
        </div>
      </div>

      {/* Sub-scores Grid */}
      <div className="grid grid-cols-2 gap-x-3 gap-y-2 text-xs text-slate-600 mb-3 border-b border-slate-200/80 pb-3">
        <div className="flex justify-between items-center">
          <span className="text-slate-500 font-medium">Compresión:</span>
          <span className="font-bold text-slate-800">{variant.compression_score}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-500 font-medium">Estabilidad:</span>
          <span className="font-bold text-slate-800">{variant.stability_score}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-500 font-medium">Absorción:</span>
          <span className="font-bold text-slate-800">{variant.energy_absorption_score}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-500 font-medium">Imprimibilidad:</span>
          <span className="font-bold text-slate-800">{variant.printability_score}</span>
        </div>
      </div>

      {/* KPIs: Mass & Print Time */}
      <div className="grid grid-cols-2 gap-2 text-xs text-slate-500 mb-3.5">
        <div>
          <span>Masa Est:</span> <b className="text-slate-700">{variant.estimated_mass}</b>
        </div>
        <div>
          <span>Tiempo Est:</span> <b className="text-slate-700">{variant.estimated_print_time}</b>
        </div>
      </div>

      {/* Pros & Cons (Sleek Collapsible or Mini List) */}
      {(variant.pros.length > 0 || variant.cons.length > 0) && (
        <div className="space-y-1.5 border-t border-slate-100 pt-2.5 mb-3.5 text-xs text-slate-600 leading-normal">
          {variant.pros.slice(0, 2).map((p, idx) => (
            <div key={idx} className="flex items-start gap-1">
              <span className="text-emerald-600 font-bold shrink-0">+</span>
              <span>{p}</span>
            </div>
          ))}
          {variant.cons.slice(0, 1).map((c, idx) => (
            <div key={idx} className="flex items-start gap-1">
              <span className="text-rose-600 font-bold shrink-0">-</span>
              <span>{c}</span>
            </div>
          ))}
        </div>
      )}

      {/* Warnings Badges */}
      {variant.warnings.length > 0 && (
        <div className="flex items-center gap-1.5 text-xs text-amber-700 bg-amber-50 border border-amber-200 p-2 rounded-lg mb-3.5 font-sans">
          <AlertCircle className="w-4 h-4 shrink-0 text-amber-600" />
          <span className="truncate">{variant.warnings[0]}</span>
        </div>
      )}

      {/* Minimalist Action Controls */}
      <div className="flex items-center gap-1.5 pt-2.5 border-t border-slate-200/80">
        <button
          onClick={handleApply}
          className="flex-1 py-2 text-[10px] font-black uppercase tracking-wider text-white bg-blue-600 hover:bg-blue-700 border border-blue-600 rounded-lg cursor-pointer transition-all shadow-sm shadow-blue-500/5 text-center flex items-center justify-center gap-1"
        >
          <Check className="w-3.5 h-3.5" />
          <span>Aplicar</span>
        </button>
        <button
          onClick={handleCompare}
          className="px-2.5 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-700 hover:text-slate-900 hover:bg-slate-100 bg-white border border-slate-200 rounded-lg cursor-pointer transition-all text-center"
        >
          Comparar
        </button>
        <button
          onClick={handleSimulate}
          className="px-2.5 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-700 hover:text-slate-900 hover:bg-slate-100 bg-white border border-slate-200 rounded-lg cursor-pointer transition-all text-center flex items-center justify-center gap-1"
        >
          <Play className="w-3 h-3 text-slate-500 fill-slate-500" />
          <span>Simular</span>
        </button>
        <button
          onClick={handleCopy}
          className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 border border-slate-200 rounded-lg bg-white transition-all cursor-pointer flex items-center justify-center shrink-0"
          title="Copiar parche de configuración"
        >
          <Copy className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={handleExport}
          className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 border border-slate-200 rounded-lg bg-white transition-all cursor-pointer flex items-center justify-center shrink-0"
          title="Exportar variante en JSON"
        >
          <Download className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}

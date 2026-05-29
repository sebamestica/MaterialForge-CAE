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
    compareMode
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
    LOW: "text-emerald-400 border-emerald-950 bg-emerald-950/20",
    MEDIUM: "text-amber-400 border-amber-950 bg-amber-950/20",
    HIGH: "text-rose-400 border-rose-950 bg-rose-950/20"
  };

  return (
    <div
      onClick={onSelect}
      className={`p-3.5 rounded-lg border transition-all duration-200 cursor-pointer font-mono text-[11px] select-none ${
        isActive
          ? "bg-slate-900/90 border-slate-700 shadow-md"
          : "bg-slate-950/40 border-slate-850 hover:bg-slate-900/40 hover:border-slate-800"
      }`}
    >
      {/* Title & Risk */}
      <div className="flex justify-between items-start gap-2 mb-2">
        <div>
          <h4 className="font-extrabold text-slate-100 text-xs tracking-tight">{variant.name}</h4>
          <p className="text-[10px] text-slate-500 mt-0.5 leading-snug">{variant.description}</p>
        </div>
        <span className={`px-1.5 py-0.5 rounded text-[8px] font-black border uppercase tracking-wider shrink-0 ${
          riskColors[variant.risk_level] || riskColors.LOW
        }`}>
          {variant.risk_level}
        </span>
      </div>

      {/* Main Score Bar */}
      <div className="bg-slate-950/70 p-2.5 rounded border border-slate-850/80 mb-3 flex items-center justify-between">
        <span className="text-slate-500 uppercase font-black text-[9px] tracking-wider">Score Estructural</span>
        <div className="flex items-center gap-2">
          <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${
                variant.score >= 85 ? "bg-emerald-500" : variant.score >= 65 ? "bg-amber-500" : "bg-rose-500"
              }`}
              style={{ width: `${variant.score}%` }}
            />
          </div>
          <span className="font-black text-white text-xs">{variant.score}/100</span>
        </div>
      </div>

      {/* Sub-scores Grid */}
      <div className="grid grid-cols-2 gap-x-3 gap-y-2 text-[10px] text-slate-400 mb-3.5 border-b border-slate-850/60 pb-3">
        <div className="flex justify-between items-center">
          <span className="text-slate-500">Compresión:</span>
          <span className="font-bold text-slate-200">{variant.compression_score}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-500">Estabilidad:</span>
          <span className="font-bold text-slate-200">{variant.stability_score}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-500">Absorción:</span>
          <span className="font-bold text-slate-200">{variant.energy_absorption_score}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-500">Imprimibilidad:</span>
          <span className="font-bold text-slate-200">{variant.printability_score}</span>
        </div>
      </div>

      {/* KPIs: Mass & Print Time */}
      <div className="grid grid-cols-2 gap-2 text-[9px] text-slate-500 mb-3">
        <div>
          <span>Masa Est:</span> <b className="text-slate-300">{variant.estimated_mass}</b>
        </div>
        <div>
          <span>Tiempo Est:</span> <b className="text-slate-300">{variant.estimated_print_time}</b>
        </div>
      </div>

      {/* Pros & Cons (Sleek Collapsible or Mini List) */}
      {(variant.pros.length > 0 || variant.cons.length > 0) && (
        <div className="space-y-1.5 border-t border-slate-900 pt-2.5 mb-3 text-[9px] text-slate-450 leading-relaxed">
          {variant.pros.slice(0, 2).map((p, idx) => (
            <div key={idx} className="flex items-start gap-1">
              <span className="text-emerald-500 font-bold shrink-0">+</span>
              <span>{p}</span>
            </div>
          ))}
          {variant.cons.slice(0, 1).map((c, idx) => (
            <div key={idx} className="flex items-start gap-1">
              <span className="text-rose-500 font-bold shrink-0">-</span>
              <span>{c}</span>
            </div>
          ))}
        </div>
      )}

      {/* Warnings Badges */}
      {variant.warnings.length > 0 && (
        <div className="flex items-center gap-1 text-[8px] text-amber-500 bg-amber-950/10 border border-amber-900/30 p-1.5 rounded mb-3">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          <span className="truncate">{variant.warnings[0]}</span>
        </div>
      )}

      {/* Minimalist Action Controls */}
      <div className="flex flex-wrap gap-1.5 pt-1.5 border-t border-slate-850/80">
        <button
          onClick={handleApply}
          className="px-2 py-1 text-[8px] uppercase tracking-wider font-extrabold text-slate-300 hover:text-white bg-slate-900 border border-slate-800 hover:border-slate-650 rounded cursor-pointer transition-colors"
        >
          apply
        </button>
        <button
          onClick={handleCompare}
          className="px-2 py-1 text-[8px] uppercase tracking-wider font-extrabold text-slate-300 hover:text-white bg-slate-900 border border-slate-800 hover:border-slate-650 rounded cursor-pointer transition-colors"
        >
          compare
        </button>
        <button
          onClick={handleSimulate}
          className="px-2 py-1 text-[8px] uppercase tracking-wider font-extrabold text-slate-300 hover:text-white bg-slate-900 border border-slate-800 hover:border-slate-650 rounded cursor-pointer transition-colors"
        >
          simulate
        </button>
        <button
          onClick={handleCopy}
          className="p-1 text-slate-400 hover:text-slate-200 border border-slate-800 rounded bg-slate-900/30 hover:bg-slate-800 transition-colors cursor-pointer"
          title="copy config patch"
        >
          <Copy className="w-2.5 h-2.5" />
        </button>
        <button
          onClick={handleExport}
          className="p-1 text-slate-400 hover:text-slate-200 border border-slate-800 rounded bg-slate-900/30 hover:bg-slate-800 transition-colors cursor-pointer"
          title="export variant JSON"
        >
          <Download className="w-2.5 h-2.5" />
        </button>
      </div>
    </div>
  );
}

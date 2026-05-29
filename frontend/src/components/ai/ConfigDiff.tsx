"use client";

import React, { useEffect } from "react";
import { useDesignStore } from "../../stores/designStore";
import { ArrowRight, Check, X } from "lucide-react";

export default function ConfigDiff() {
  const { currentConfig, pendingPatch, syncCurrentConfig, applyPatch, setCompareMode } = useDesignStore();

  useEffect(() => {
    syncCurrentConfig();
  }, []);

  if (!pendingPatch || Object.keys(pendingPatch).length === 0) {
    return (
      <div className="text-center p-3 text-[10px] text-slate-500 font-mono">
        No hay cambios propuestos seleccionados para comparar.
      </div>
    );
  }

  const displayLabels: Record<string, string> = {
    material: "Material",
    infill: "Densidad de Infill",
    pattern: "Patrón de Celda",
    cellSize: "Tamaño Celda",
    cellThickness: "Grosor Celda",
    wallThickness: "Espesor Pared",
    dimX: "Dimensión X",
    dimY: "Dimensión Y",
    dimZ: "Dimensión Z",
    resolution: "Resolución",
    layerHeight: "Altura de Capa",
    printSpeed: "Velocidad de Impresión",
  };

  const suffixMap: Record<string, string> = {
    infill: "%",
    cellSize: " mm",
    cellThickness: " mm",
    wallThickness: " mm",
    dimX: " cm",
    dimY: " cm",
    dimZ: " cm",
    layerHeight: " mm",
    printSpeed: " mm/s",
  };

  // Find actual differences
  const diffEntries = Object.entries(pendingPatch).filter(([key, proposedVal]) => {
    const currentVal = (currentConfig as any)[key];
    return proposedVal !== undefined && proposedVal !== null && currentVal !== proposedVal;
  });

  if (diffEntries.length === 0) {
    return (
      <div className="text-center p-3 text-[10px] text-slate-400 font-mono bg-slate-950/20 border border-slate-900 rounded">
        ✓ El diseño actual ya coincide con esta variante.
      </div>
    );
  }

  const handleApplyDiff = async () => {
    await applyPatch();
    setCompareMode(false);
  };

  return (
    <div className="bg-slate-950/60 border border-slate-800 rounded-lg overflow-hidden font-mono text-[10px] space-y-3 p-3">
      {/* Title */}
      <div className="flex justify-between items-center border-b border-slate-900 pb-2">
        <span className="font-extrabold uppercase text-[9px] text-slate-400 tracking-wider">
          Comparativa de Parámetros
        </span>
        <button
          onClick={() => setCompareMode(false)}
          className="text-slate-500 hover:text-slate-350 cursor-pointer"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Diff Table */}
      <div className="border border-slate-900 rounded bg-slate-950/90 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-900 text-slate-500 text-[8px] uppercase tracking-wider border-b border-slate-850">
            <tr>
              <th className="p-2">Parámetro</th>
              <th className="p-2">Actual</th>
              <th className="p-2">Sugerido</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-900/60">
            {diffEntries.map(([key, proposedVal]) => {
              const currentVal = (currentConfig as any)[key];
              const label = displayLabels[key] || key;
              const suffix = suffixMap[key] || "";

              return (
                <tr key={key} className="hover:bg-slate-900/20">
                  <td className="p-2 text-slate-400 font-bold">{label}</td>
                  <td className="p-2 text-slate-500">{currentVal !== undefined ? `${currentVal}${suffix}` : "-"}</td>
                  <td className="p-2 text-blue-400 font-extrabold flex items-center gap-1">
                    <ArrowRight className="w-2.5 h-2.5 text-slate-600" />
                    <span>{proposedVal}{suffix}</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Minimalist Controls */}
      <div className="flex gap-2 justify-end pt-1">
        <button
          onClick={() => setCompareMode(false)}
          className="px-2.5 py-1 text-[8px] uppercase tracking-wider font-extrabold text-slate-500 hover:text-slate-300 border border-transparent rounded cursor-pointer transition-colors"
        >
          cancel
        </button>
        <button
          onClick={handleApplyDiff}
          className="px-2.5 py-1 text-[8px] uppercase tracking-wider font-extrabold text-slate-300 hover:text-white bg-slate-900 border border-slate-800 hover:border-slate-650 rounded cursor-pointer transition-colors flex items-center gap-1"
        >
          <Check className="w-2.5 h-2.5 text-blue-500" />
          <span>apply changes</span>
        </button>
      </div>
    </div>
  );
}

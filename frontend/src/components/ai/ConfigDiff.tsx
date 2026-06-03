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
    <div className="bg-slate-50 border border-slate-200 rounded-xl overflow-hidden font-sans text-xs space-y-3.5 p-3.5 shadow-2xs">
      {/* Title */}
      <div className="flex justify-between items-center border-b border-slate-200 pb-2">
        <span className="font-extrabold uppercase text-[10px] text-slate-750 tracking-wider">
          Comparativa de Parámetros
        </span>
        <button
          onClick={() => setCompareMode(false)}
          className="text-slate-400 hover:text-slate-650 cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Diff Table */}
      <div className="border border-slate-200 rounded-lg bg-white overflow-hidden shadow-3xs">
        <table className="w-full text-left">
          <thead className="bg-slate-50 text-slate-500 text-[9px] uppercase tracking-wider border-b border-slate-200">
            <tr>
              <th className="p-2.5 font-bold">Parámetro</th>
              <th className="p-2.5 font-bold">Actual</th>
              <th className="p-2.5 font-bold">Sugerido</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-xs">
            {diffEntries.map(([key, proposedVal]) => {
              const currentVal = (currentConfig as any)[key];
              const label = displayLabels[key] || key;
              const suffix = suffixMap[key] || "";

              return (
                <tr key={key} className="hover:bg-slate-50/50 transition-colors">
                  <td className="p-2.5 text-slate-700 font-bold">{label}</td>
                  <td className="p-2.5 text-slate-500">{currentVal !== undefined ? `${currentVal}${suffix}` : "-"}</td>
                  <td className="p-2.5 text-blue-600 font-extrabold flex items-center gap-1.5">
                    <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                    <span className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded border border-blue-100 font-mono text-[11px]">{proposedVal}{suffix}</span>
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
          className="px-3.5 py-2 text-xs font-bold text-slate-500 hover:text-slate-700 rounded-lg cursor-pointer transition-colors"
        >
          Cancelar
        </button>
        <button
          onClick={handleApplyDiff}
          className="px-3.5 py-2 text-xs font-black uppercase tracking-wider text-white bg-blue-600 hover:bg-blue-700 border border-blue-600 rounded-lg cursor-pointer transition-all shadow-sm flex items-center gap-1.5 active:scale-97"
        >
          <Check className="w-3.5 h-3.5" />
          <span>Aplicar Cambios</span>
        </button>
      </div>
    </div>
  );
}

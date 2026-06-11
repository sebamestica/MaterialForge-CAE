"use client";

import React, { useState } from "react";
import { useLabStore, MATERIAL_DATA } from "@/stores/useLabStore";
import { ChevronDown, ChevronRight, ChevronLeft, RefreshCw, Layers, HardHat, Box, Printer, Activity, Sliders } from "lucide-react";
import { useShallow } from "zustand/react/shallow";

// Inline SVG helper to draw dynamic pattern preview
function PatternPreview({ pattern }: { pattern: string }) {
  if (pattern === "gyroid") {
    return (
      <svg className="w-14 h-14 border border-slate-200 bg-[#FAFBFC] rounded" viewBox="0 0 100 100">
        <path
          d="M10,50 Q25,30 40,50 T70,50 T100,50"
          fill="none"
          stroke="#1E40AF"
          strokeWidth="3"
        />
        <path
          d="M10,30 Q25,10 40,30 T70,30 T100,30"
          fill="none"
          stroke="#1E40AF"
          strokeWidth="2"
          opacity="0.5"
        />
        <path
          d="M10,70 Q25,50 40,70 T70,70 T100,70"
          fill="none"
          stroke="#1E40AF"
          strokeWidth="2"
          opacity="0.5"
        />
      </svg>
    );
  }

  if (pattern === "honeycomb") {
    return (
      <svg className="w-14 h-14 border border-slate-200 bg-[#FAFBFC] rounded" viewBox="0 0 100 100">
        <polygon points="50,10 80,25 80,60 50,75 20,60 20,25" fill="none" stroke="#1E40AF" strokeWidth="2.5" />
        <polygon points="50,-25 80,-10 80,25 50,40 20,25 20,-10" fill="none" stroke="#1E40AF" strokeWidth="1.5" opacity="0.4" />
        <polygon points="80,60 110,75 110,110 80,125 50,110 50,75" fill="none" stroke="#1E40AF" strokeWidth="1.5" opacity="0.4" />
        <polygon points="20,60 50,75 50,110 20,125 -10,110 -10,75" fill="none" stroke="#1E40AF" strokeWidth="1.5" opacity="0.4" />
      </svg>
    );
  }

  if (pattern === "grid") {
    return (
      <svg className="w-14 h-14 border border-slate-200 bg-[#FAFBFC] rounded" viewBox="0 0 100 100">
        <line x1="20" y1="10" x2="20" y2="90" stroke="#1E40AF" strokeWidth="2" />
        <line x1="50" y1="10" x2="50" y2="90" stroke="#1E40AF" strokeWidth="2" />
        <line x1="80" y1="10" x2="80" y2="90" stroke="#1E40AF" strokeWidth="2" />
        <line x1="10" y1="20" x2="90" y2="20" stroke="#1E40AF" strokeWidth="2" />
        <line x1="10" y1="50" x2="90" y2="50" stroke="#1E40AF" strokeWidth="2" />
        <line x1="10" y1="80" x2="90" y2="80" stroke="#1E40AF" strokeWidth="2" />
      </svg>
    );
  }

  if (pattern === "diamond") {
    return (
      <svg className="w-14 h-14 border border-slate-200 bg-[#FAFBFC] rounded" viewBox="0 0 100 100">
        <polygon points="50,15 80,50 50,85 20,50" fill="none" stroke="#1E40AF" strokeWidth="3" />
        <polygon points="50,30 70,50 50,70 30,50" fill="none" stroke="#1E40AF" strokeWidth="1.5" opacity="0.6" />
        <line x1="50" y1="15" x2="50" y2="85" stroke="#1E40AF" strokeWidth="1" opacity="0.4" strokeDasharray="3,3" />
        <line x1="20" y1="50" x2="80" y2="50" stroke="#1E40AF" strokeWidth="1" opacity="0.4" strokeDasharray="3,3" />
      </svg>
    );
  }

  // triply_periodic (Schwarz P)
  return (
    <svg className="w-14 h-14 border border-slate-200 bg-[#FAFBFC] rounded" viewBox="0 0 100 100">
      <circle cx="50" cy="50" r="20" fill="none" stroke="#1E40AF" strokeWidth="3" />
      <line x1="50" y1="10" x2="50" y2="30" stroke="#1E40AF" strokeWidth="2.5" />
      <line x1="50" y1="70" x2="50" y2="90" stroke="#1E40AF" strokeWidth="2.5" />
      <line x1="10" y1="50" x2="30" y2="50" stroke="#1E40AF" strokeWidth="2.5" />
      <line x1="70" y1="50" x2="90" y2="50" stroke="#1E40AF" strokeWidth="2.5" />
    </svg>
  );
}

export default function LeftPanel() {
  const store = useLabStore(
    useShallow((state) => ({
      dimX: state.dimX,
      dimY: state.dimY,
      dimZ: state.dimZ,
      wallThickness: state.wallThickness,
      shellLayers: state.shellLayers,
      edgeRounding: state.edgeRounding,
      resolution: state.resolution,
      material: state.material,
      pattern: state.pattern,
      infill: state.infill,
      cellSize: state.cellSize,
      cellThickness: state.cellThickness,
      orientation: state.orientation,
      layerHeight: state.layerHeight,
      printSpeed: state.printSpeed,
      predictions: state.predictions,
      patterns: state.patterns,
      materials: state.materials,
      setParam: state.setParam,
      triggerMeshGeneration: state.triggerMeshGeneration,
      triggerInference: state.triggerInference,
      toggleLeftPanel: state.toggleLeftPanel,
      workspaceFocus: state.workspaceFocus,
      ui_advanced_mode: state.ui_advanced_mode,
      appliedForce: state.appliedForce,
      isSimulating: state.isSimulating,
      runDynamicSimulation: state.runDynamicSimulation,
    }))
  );

  const [activeModule, setActiveModule] = useState<"geom" | "mat" | "infill" | "print" | "sim">("geom");

  React.useEffect(() => {
    if (store.workspaceFocus === "diseño") {
      setActiveModule("geom");
    } else if (store.workspaceFocus === "material") {
      setActiveModule("mat");
    } else if (store.workspaceFocus === "simulación") {
      setActiveModule("sim");
    } else if (store.workspaceFocus === "fabricación") {
      if (store.ui_advanced_mode) {
        setActiveModule("print");
      } else {
        setActiveModule("geom");
      }
    }
  }, [store.workspaceFocus]);

  React.useEffect(() => {
    if (!store.ui_advanced_mode && activeModule === "print") {
      setActiveModule("geom");
    }
  }, [store.ui_advanced_mode, activeModule]);

  const matInfo = store.materials[store.material] || store.materials.PLA || MATERIAL_DATA.PLA;

  const modules = [
    { id: "geom", label: "Geometría", icon: Box, value: `${store.dimX.toFixed(1)}x${store.dimY.toFixed(1)}x${store.dimZ.toFixed(1)} cm` },
    { id: "mat", label: "Material", icon: HardHat, value: store.material },
    { id: "infill", label: "Estructura", icon: Layers, value: `${store.pattern} (${store.infill}%)` },
    ...(store.ui_advanced_mode ? [{ id: "print", label: "Laminado", icon: Printer, value: `${store.layerHeight.toFixed(2)}mm` }] : []),
    { id: "sim", label: "Simulación", icon: Activity, value: `${store.appliedForce} N` },
  ] as const;

  return (
    <div className="w-full h-full bg-white flex flex-col overflow-y-auto select-none text-slate-850 scrollbar-thin">
      {/* Title */}
      <div className="p-3 border-b border-slate-200 flex items-center justify-between bg-white shrink-0">
        <div className="flex items-center space-x-2 font-sans">
          <Sliders className="w-4.5 h-4.5 text-[#1E40AF]" />
          <span className="text-slate-900 text-sm font-black uppercase tracking-wider">
            Parámetros de Diseño
          </span>
        </div>
        {/* Collapse button for PC view */}
        <button
          onClick={store.toggleLeftPanel}
          className="hidden lg:flex items-center justify-center p-1 rounded-md hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition-colors focus:outline-none cursor-pointer"
          title="Ocultar Panel"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
      </div>

      <div className="p-3 space-y-4 flex-1 overflow-y-auto">
        {/* MODE TOGGLE SWITCH */}
        <div className="flex items-center justify-between p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-sans text-slate-700 shadow-3xs shrink-0">
          <span className="font-bold text-slate-800">Modo Avanzado (CAD/CAE)</span>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={store.ui_advanced_mode}
              onChange={(e) => {
                const nextVal = e.target.checked;
                store.setParam("ui_advanced_mode", nextVal);
                if (typeof window !== "undefined") {
                  localStorage.setItem("MaterialForge_ui_advanced_mode", String(nextVal));
                }
              }}
              className="sr-only peer"
            />
            <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#1E40AF]"></div>
          </label>
        </div>

        {/* MODULES BUBBLES / NAV SELECTOR */}
        <div className="grid grid-cols-2 gap-2.5 shrink-0">
          {modules.map((m) => {
            const Icon = m.icon;
            const isActive = activeModule === m.id;
            return (
              <button
                key={m.id}
                onClick={() => setActiveModule(m.id as any)}
                className={`flex flex-col items-center justify-between p-3 rounded-xl border text-center transition-all cursor-pointer select-none ${
                  isActive
                    ? "bg-[#EFF6FF] border-[#1E40AF] shadow-xs ring-1 ring-[#1E40AF]/20"
                    : "bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50/50 shadow-3xs"
                }`}
              >
                <div className="flex items-center justify-center w-8 h-8 rounded-full mb-1">
                  <Icon className={`w-5 h-5 ${isActive ? "text-[#1E40AF]" : "text-slate-400"}`} />
                </div>
                <span className={`text-[11px] font-black uppercase tracking-wider block ${isActive ? "text-[#1E40AF]" : "text-slate-500"}`}>
                  {m.label}
                </span>
                <span className={`text-[10px] font-mono mt-0.5 block truncate max-w-full font-bold ${isActive ? "text-[#1E3A8A]" : "text-slate-455"}`}>
                  {m.value}
                </span>
              </button>
            );
          })}
        </div>

        {/* ACTIVE INSPECTOR CONTAINER */}
        <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-xs p-3.5 space-y-4">
          <div className="text-xs font-black uppercase tracking-wider text-slate-400 border-b border-slate-100 pb-2 flex items-center space-x-2">
            <span>Configurando:</span>
            <span className="text-[#1E40AF]">{modules.find((m) => m.id === activeModule)?.label}</span>
          </div>

          {/* GEOMETRY MODULE CONTROLS */}
          {activeModule === "geom" && (
            <div className="space-y-4 font-sans text-sm">
              <div className="space-y-1.5">
                <span className="text-slate-500 font-bold text-sm cursor-help" title="Dimensiones físicas del bloque en centímetros. Límites permitidos: 1.0 cm a 15.0 cm. Afecta el volumen final y la masa total.">Dimensiones de la Caja Delimitadora ⓘ</span>
                <div className="grid grid-cols-3 gap-2.5">
                  <div>
                    <span className="text-xs text-slate-400 block mb-0.5 text-center font-extrabold">ANCHO X<br/>(cm)</span>
                    <input
                      type="number"
                      value={store.dimX.toFixed(1)}
                      onChange={(e) => store.setParam("dimX", parseFloat(e.target.value) || 5.0)}
                      className="w-full bg-white border border-slate-200 rounded-md px-2 py-1 text-slate-800 text-center font-bold font-mono text-sm focus:border-[#1E40AF] focus:ring-1 focus:ring-[#1E40AF] focus:outline-none"
                    />
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 block mb-0.5 text-center font-extrabold">LARGO Y<br/>(cm)</span>
                    <input
                      type="number"
                      value={store.dimY.toFixed(1)}
                      onChange={(e) => store.setParam("dimY", parseFloat(e.target.value) || 5.0)}
                      className="w-full bg-white border border-slate-200 rounded-md px-2 py-1 text-slate-800 text-center font-bold font-mono text-sm focus:border-[#1E40AF] focus:ring-1 focus:ring-[#1E40AF] focus:outline-none"
                    />
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 block mb-0.5 text-center font-extrabold">ALTO Z<br/>(cm)</span>
                    <input
                      type="number"
                      value={store.dimZ.toFixed(1)}
                      onChange={(e) => store.setParam("dimZ", parseFloat(e.target.value) || 5.0)}
                      className="w-full bg-white border border-slate-200 rounded-md px-2 py-1 text-slate-800 text-center font-bold font-mono text-sm focus:border-[#1E40AF] focus:ring-1 focus:ring-[#1E40AF] focus:outline-none"
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between items-baseline text-slate-700 cursor-help" title="Espesor en milímetros de la carcasa exterior sólida (shell). Límites: 0.4 mm a 10.0 mm.">
                  <span className="font-semibold text-slate-500">Espesor de Pared (Carcasa) ⓘ</span>
                  <span className="text-[#1E40AF] font-bold font-mono text-sm">{store.wallThickness.toFixed(1)} mm</span>
                </div>
                <input
                  type="range"
                  min={0.4}
                  max={4.0}
                  step={0.1}
                  value={store.wallThickness}
                  onChange={(e) => store.setParam("wallThickness", parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-[#1E40AF]"
                />
                <div className="flex justify-between text-xs text-slate-400 font-mono">
                  <span>0.4 mm</span>
                  <span>4.0 mm</span>
                </div>
              </div>

              {store.ui_advanced_mode && (
                <>
                  <div className="space-y-1.5 pt-2 border-t border-slate-100">
                    <div className="flex justify-between items-baseline text-slate-700 cursor-help" title="Número de capas sólidas superiores e inferiores.">
                      <span className="font-semibold text-slate-500">Capas de Carcasa ⓘ</span>
                      <span className="text-[#1E40AF] font-bold font-mono text-sm">{store.shellLayers}</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={5}
                      step={1}
                      value={store.shellLayers}
                      onChange={(e) => store.setParam("shellLayers", parseInt(e.target.value))}
                      className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-[#1E40AF]"
                    />
                    <div className="flex justify-between text-xs text-slate-400 font-mono">
                      <span>0 capas</span>
                      <span>5 capas</span>
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <div className="flex justify-between items-baseline text-slate-700 cursor-help" title="Radio en milímetros del redondeado en las aristas verticales.">
                      <span className="font-semibold text-slate-500">Redondeo de Bordes ⓘ</span>
                      <span className="text-[#1E40AF] font-bold font-mono text-sm">{store.edgeRounding.toFixed(2)} mm</span>
                    </div>
                    <input
                      type="range"
                      min={0.0}
                      max={2.0}
                      step={0.05}
                      value={store.edgeRounding}
                      onChange={(e) => store.setParam("edgeRounding", parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-[#1E40AF]"
                    />
                    <div className="flex justify-between text-xs text-slate-400 font-mono">
                      <span>0.0 mm (Recto)</span>
                      <span>2.0 mm (Máx)</span>
                    </div>
                  </div>

                  <div className="flex justify-between items-center cursor-help font-semibold text-slate-500 pt-3 border-t border-slate-100" title="Resolución superficial de malla. Baja es óptima para rendimiento, Alta para exportar.">
                    <span>Resolución Superficial ⓘ</span>
                    <select
                      value={store.resolution}
                      onChange={(e) => store.setParam("resolution", e.target.value)}
                      className="bg-white border border-slate-200 rounded-md px-2.5 py-1 text-slate-855 text-sm font-bold outline-none focus:border-[#1E40AF] cursor-pointer"
                    >
                      <option value="Baja">Borrador (Baja)</option>
                      <option value="Media">Balanceada (Media)</option>
                      <option value="Alta">Alta</option>
                      <option value="Ultra">Ultra (Industrial)</option>
                    </select>
                  </div>
                </>
              )}
            </div>
          )}

          {/* MATERIAL MODULE CONTROLS */}
          {activeModule === "mat" && (
            <div className="space-y-4 font-sans text-sm">
              <div className="flex justify-between items-center cursor-help font-semibold text-slate-500" title="Tipo de termoplástico utilizado para la predicción de esfuerzo físico.">
                <span>Material del Filamento ⓘ</span>
                <select
                  value={store.material}
                  onChange={(e) => store.setParam("material", e.target.value)}
                  className="bg-white border border-slate-200 rounded-md px-2.5 py-1 text-slate-855 text-sm font-bold outline-none w-36 focus:border-[#1E40AF] cursor-pointer"
                >
                  {Object.entries(store.materials).map(([key, mat]) => (
                    <option key={key} value={key}>{mat.name}</option>
                  ))}
                </select>
              </div>

              <div className="bg-slate-50/70 p-3 rounded-lg border border-slate-150 space-y-2.5">
                <div className="flex justify-between text-sm border-b border-slate-200/50 pb-2">
                  <span className="text-slate-500">Densidad base:</span>
                  <span className="text-slate-800 font-bold font-mono">{matInfo.density}</span>
                </div>
                <div className="flex justify-between text-sm border-b border-slate-200/50 pb-2">
                  <span className="text-slate-500">Módulo elástico:</span>
                  <span className="text-slate-800 font-bold font-mono">{matInfo.modulus}</span>
                </div>
                <div className="flex justify-between text-sm border-b border-slate-200/50 pb-2">
                  <span className="text-slate-500">Resistencia Tracción:</span>
                  <span className="text-slate-800 font-bold font-mono">{matInfo.tensileStrength}</span>
                </div>
                <div className="flex justify-between text-sm border-b border-slate-200/50 pb-2">
                  <span className="text-slate-500">Fusor térmico:</span>
                  <span className="text-slate-800 font-bold font-mono">{matInfo.printTemp}</span>
                </div>
                <div className="flex justify-between text-sm pt-1 items-center">
                  <span className="text-slate-600 font-bold">Masa estimada:</span>
                  <span className="text-[#1E40AF] font-black font-mono text-sm">
                    {store.predictions ? `${store.predictions.massGrams} g` : `${((store.dimX * store.dimY * store.dimZ * 1000) * (store.infill / 100) * (store.material === "PLA" ? 1.24 : 1.20) * 0.001 + 5).toFixed(1)} g`}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* INFILL MODULE CONTROLS */}
          {activeModule === "infill" && (
            <div className="space-y-4 font-sans text-sm">
              <div className="flex justify-between items-center cursor-help font-semibold text-slate-500" title="Patrón geométrico interno usado para la celosía.">
                <span>Patrón de Retícula ⓘ</span>
                <select
                  value={store.pattern}
                  onChange={(e) => store.setParam("pattern", e.target.value)}
                  className="bg-white border border-slate-200 rounded-md px-2.5 py-1.5 text-slate-855 text-sm font-bold outline-none w-36 focus:border-[#1E40AF] cursor-pointer"
                >
                  {Object.entries(store.patterns).map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </div>

              <div className="flex items-center space-x-3 bg-slate-50/70 p-3 rounded-lg border border-slate-150">
                <PatternPreview pattern={store.pattern} />
                <div className="flex-1 space-y-2">
                  <div className="space-y-1.5">
                    <div className="flex justify-between items-baseline text-slate-700 cursor-help" title="Densidad volumétrica del infill celular.">
                      <span className="font-semibold text-sm text-slate-500">Densidad de Relleno ⓘ</span>
                      <span className="text-[#1E40AF] font-bold font-mono text-sm">{store.infill}%</span>
                    </div>
                    <input
                      type="range"
                      min={10}
                      max={100}
                      step={5}
                      value={store.infill}
                      onChange={(e) => store.setParam("infill", parseInt(e.target.value))}
                      className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-[#1E40AF]"
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between items-baseline text-slate-700 cursor-help" title="Tamaño en milímetros de la celda unitaria de retícula.">
                  <span className="font-semibold text-slate-500">Densidad/Tamaño Celda ⓘ</span>
                  <span className="text-[#1E40AF] font-bold font-mono text-sm">{store.cellSize.toFixed(1)} mm</span>
                </div>
                <input
                  type="range"
                  min={1.0}
                  max={10.0}
                  step={0.5}
                  value={store.cellSize}
                  onChange={(e) => store.setParam("cellSize", parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-[#1E40AF]"
                />
                <div className="flex justify-between text-xs text-slate-400 font-mono">
                  <span>1.0 mm (Densa)</span>
                  <span>10.0 mm (Espaciado)</span>
                </div>
              </div>

              {store.ui_advanced_mode && (
                <>
                  <div className="space-y-1.5 pt-2 border-t border-slate-100">
                    <div className="flex justify-between items-baseline text-slate-700 cursor-help" title="Grosor en milímetros de los struts internos del infill.">
                      <span className="font-semibold text-slate-500">Espesor de Celda ⓘ</span>
                      <span className="text-[#1E40AF] font-bold font-mono text-sm">{store.cellThickness.toFixed(2)} mm</span>
                    </div>
                    <input
                      type="range"
                      min={0.1}
                      max={2.0}
                      step={0.05}
                      value={store.cellThickness}
                      onChange={(e) => store.setParam("cellThickness", parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-[#1E40AF]"
                    />
                    <div className="flex justify-between text-xs text-slate-400 font-mono">
                      <span>0.1 mm</span>
                      <span>2.0 mm</span>
                    </div>
                  </div>

                  <div className="flex justify-between items-center cursor-help font-semibold text-slate-500 border-t border-slate-100 pt-3" title="Orientación del estiramiento del infill celular.">
                    <span>Orientación Celular ⓘ</span>
                    <select
                      value={store.orientation}
                      onChange={(e) => store.setParam("orientation", e.target.value)}
                      className="bg-white border border-slate-200 rounded-md px-2.5 py-1 text-slate-855 text-sm font-bold outline-none w-36 focus:border-[#1E40AF] cursor-pointer"
                    >
                      <option value="Isotrópica">Isotrópica</option>
                      <option value="Anisotrópica X">Aniso X</option>
                      <option value="Anisotrópica Y">Aniso Y</option>
                      <option value="Anisotrópica Z">Aniso Z</option>
                    </select>
                  </div>
                </>
              )}
            </div>
          )}

          {/* SLICING MODULE CONTROLS */}
          {activeModule === "print" && store.ui_advanced_mode && (
            <div className="space-y-4 font-sans text-sm">
              <div className="space-y-1.5">
                <div className="flex justify-between items-baseline text-slate-700 cursor-help" title="Altura de capa del extrusor.">
                  <span className="font-semibold text-slate-500">Altura de Capa (Resolución Z) ⓘ</span>
                  <span className="text-[#1E40AF] font-bold font-mono text-sm">{store.layerHeight.toFixed(2)} mm</span>
                </div>
                <input
                  type="range"
                  min={0.10}
                  max={0.40}
                  step={0.05}
                  value={store.layerHeight}
                  onChange={(e) => store.setParam("layerHeight", parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-[#1E40AF]"
                />
                <div className="flex justify-between text-xs text-slate-455 font-mono">
                  <span>0.10 mm (Detalle)</span>
                  <span>0.40 mm (Rápido)</span>
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between items-baseline text-slate-700 cursor-help" title="Velocidad del extrusor en el plano XY.">
                  <span className="font-semibold text-slate-500">Velocidad de Impresión ⓘ</span>
                  <span className="text-[#1E40AF] font-bold font-mono text-sm">{store.printSpeed} mm/s</span>
                </div>
                <input
                  type="range"
                  min={30}
                  max={100}
                  step={5}
                  value={store.printSpeed}
                  onChange={(e) => store.setParam("printSpeed", parseInt(e.target.value))}
                  className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-[#1E40AF]"
                />
                <div className="flex justify-between text-xs text-slate-455 font-mono">
                  <span>30 mm/s</span>
                  <span>100 mm/s</span>
                </div>
              </div>

              <div className="text-xs text-slate-400 pt-2 border-t border-slate-100 font-sans font-bold uppercase tracking-wider flex justify-between">
                <span>Modo de Relleno:</span>
                <span className="text-slate-800 normal-case font-bold">Lattice SDF</span>
              </div>
            </div>
          )}

          {/* SIMULATION MODULE CONTROLS */}
          {activeModule === "sim" && (() => {
            const predictedMaxForce = store.predictions?.maxForceNewtons || (store.material.toUpperCase() === "TPU" ? 1200.0 : 8000.0);
            const maxForceSlider = Math.ceil(predictedMaxForce * 1.25);
            const stepForceSlider = Math.max(10, Math.ceil(maxForceSlider / 100));

            return (
              <div className="space-y-4 font-sans text-sm">
                <div className="space-y-1.5">
                  <div className="flex justify-between items-baseline">
                    <span className="text-slate-500 text-sm font-semibold">Fuerza aplicada</span>
                    <span className="text-[#1E40AF] font-bold font-mono text-sm">{store.appliedForce} N</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={maxForceSlider}
                    step={stepForceSlider}
                    value={store.appliedForce}
                    disabled={store.isSimulating}
                    onChange={(e) => store.setParam("appliedForce", parseInt(e.target.value))}
                    className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-[#1E40AF] disabled:opacity-50"
                  />
                  <div className="flex justify-between text-xs text-slate-400 font-mono font-bold">
                    <span>0 N (Descarga)</span>
                    <span>{maxForceSlider} N (Colapso)</span>
                  </div>
                </div>

                <button
                  onClick={() => store.runDynamicSimulation()}
                  disabled={store.isSimulating}
                  className="w-full bg-[#1E40AF] text-white hover:bg-[#1D4ED8] font-black py-2.5 rounded-lg transition-all text-sm uppercase flex items-center justify-center space-x-2 shadow-sm disabled:bg-slate-100 disabled:text-slate-400 disabled:shadow-none cursor-pointer"
                >
                  {store.isSimulating ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Simulando...</span>
                    </>
                  ) : (
                    <span>Presión Dinámica</span>
                  )}
                </button>

                <div className="text-sm text-slate-500 space-y-1.5 pt-3 border-t border-slate-100 font-sans font-medium">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-450">Velocidad de carga:</span>
                    <span className="text-slate-800 font-bold font-mono">1.5 mm/min</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-450">Eje de compresión:</span>
                    <span className="text-slate-800 font-bold font-mono">Eje Z (Y-WebGL)</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-455">Método predictivo:</span>
                    <span className="text-slate-800 font-bold font-mono">Machine Learning (Gradient Boosting)</span>
                  </div>
                </div>
              </div>
            );
          })()}
        </div>
      </div>
    </div>
  );
}

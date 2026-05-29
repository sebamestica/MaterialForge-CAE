"use client";

import React, { useState, useEffect } from "react";
import { useLabStore } from "@/stores/useLabStore";
import { useShallow } from "zustand/react/shallow";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from "recharts";
import { 
  Activity, 
  Search, 
  Layers, 
  Filter, 
  FileText, 
  Info,
  TrendingUp
} from "lucide-react";

export default function MechanicalCurvesView() {
  const store = useLabStore(
    useShallow((state) => ({
      specimensList: state.specimensList,
      mechanicalProperties: state.mechanicalProperties,
      selectedSpecimen: state.selectedSpecimen,
      selectedSpecimenCurve: state.selectedSpecimenCurve,
      fetchSpecimens: state.fetchSpecimens,
      fetchCurve: state.fetchCurve,
      fetchProperties: state.fetchProperties,
    }))
  );

  const [search, setSearch] = useState("");
  const [filterMaterial, setFilterMaterial] = useState("all");
  const [filterTestType, setFilterTestType] = useState("all");

  useEffect(() => {
    // Initial fetch if empty
    if (store.specimensList.length === 0) {
      store.fetchSpecimens();
      store.fetchProperties();
    }
  }, [store.specimensList.length]);

  // Load default specimen on list load if none selected
  useEffect(() => {
    if (store.specimensList.length > 0 && !store.selectedSpecimen) {
      const firstSpecimen = store.specimensList[0].specimen_id;
      store.fetchCurve(firstSpecimen);
    }
  }, [store.specimensList, store.selectedSpecimen]);

  // Filter list
  const filteredSpecimens = store.specimensList.filter((spec) => {
    const matchesSearch = spec.specimen_id.toLowerCase().includes(search.toLowerCase()) || 
                          (spec.notes && spec.notes.toLowerCase().includes(search.toLowerCase()));
    const matchesMaterial = filterMaterial === "all" || spec.material.toLowerCase() === filterMaterial.toLowerCase();
    const matchesTestType = filterTestType === "all" || spec.test_type.toLowerCase() === filterTestType.toLowerCase();
    return matchesSearch && matchesMaterial && matchesTestType;
  });

  const currentSpecimen = store.specimensList.find(s => s.specimen_id === store.selectedSpecimen);
  const currentProperties = store.mechanicalProperties.find(p => p.specimen_id === store.selectedSpecimen);

  // Chart data formatting: keep every Nth point if there are too many (to prevent Recharts lag)
  const rawPoints = store.selectedSpecimenCurve || [];
  const step = Math.max(1, Math.floor(rawPoints.length / 500));
  const curveData = rawPoints.filter((_, idx) => idx % step === 0).map((pt) => ({
    strain: parseFloat(pt.strain?.toFixed(5) || "0"),
    stress: parseFloat(pt.stress_MPa?.toFixed(3) || "0"),
    displacement: parseFloat(pt.displacement_mm?.toFixed(3) || "0"),
    force: parseFloat(pt.force_N?.toFixed(1) || "0"),
    energy: parseFloat(pt.energy_cumulative_J?.toFixed(3) || "0")
  }));

  // Material and Test options
  const uniqueMaterials = Array.from(new Set(store.specimensList.map(s => s.material.toLowerCase())));
  const uniqueTestTypes = Array.from(new Set(store.specimensList.map(s => s.test_type.toLowerCase())));

  return (
    <div className="w-full h-full overflow-hidden bg-slate-50 flex font-mono text-slate-800">
      
      {/* Sidebar: Specimen Selector */}
      <div className="w-80 border-r border-slate-200 bg-white h-full flex flex-col shrink-0">
        {/* Sidebar Header & Filters */}
        <div className="p-4 border-b border-slate-200 space-y-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-blue-500" />
            Catálogo de Probetas ({filteredSpecimens.length})
          </h2>
          
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-2.5 top-2 w-3.5 h-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Buscar probeta..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded pl-8 pr-2.5 py-1 text-xs focus:bg-white focus:outline-blue-500"
            />
          </div>

          {/* Filter Dropdowns */}
          <div className="grid grid-cols-2 gap-2 text-[10px]">
            <div>
              <label className="text-slate-400 block mb-1 uppercase font-bold">Material</label>
              <select
                value={filterMaterial}
                onChange={(e) => setFilterMaterial(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded px-1.5 py-1 focus:bg-white"
              >
                <option value="all">Todos</option>
                {uniqueMaterials.map(m => (
                  <option key={m} value={m}>{m.toUpperCase()}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-slate-400 block mb-1 uppercase font-bold">Ensayo</label>
              <select
                value={filterTestType}
                onChange={(e) => setFilterTestType(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded px-1.5 py-1 focus:bg-white"
              >
                <option value="all">Todos</option>
                {uniqueTestTypes.map(t => (
                  <option key={t} value={t}>{t === "tensile" ? "Tracción" : "Compresión"}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Specimen List */}
        <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
          {filteredSpecimens.map((spec) => {
            const isSelected = spec.specimen_id === store.selectedSpecimen;
            return (
              <button
                key={spec.specimen_id}
                onClick={() => store.fetchCurve(spec.specimen_id)}
                className={`w-full text-left p-3 text-xs transition-colors cursor-pointer block ${
                  isSelected ? "bg-blue-50 text-blue-800 border-l-4 border-blue-600" : "hover:bg-slate-50"
                }`}
              >
                <div className="font-bold truncate">{spec.specimen_id}</div>
                <div className="flex items-center gap-2 text-[10px] text-slate-500 mt-1 uppercase font-bold">
                  <span className="bg-slate-100 border border-slate-200 px-1 py-0.25 rounded text-slate-700">
                    {spec.material}
                  </span>
                  <span>
                    {spec.test_type === "tensile" ? "Tracción" : "Compresión"}
                  </span>
                  {spec.replicate && <span>R:{spec.replicate}</span>}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Panel: Curve Plots and Calculated Properties */}
      <div className="flex-1 h-full overflow-y-auto p-6 flex flex-col min-w-0">
        
        {/* Summary of Selected Specimen */}
        {currentSpecimen ? (
          <>
            <div className="flex flex-col md:flex-row justify-between border-b border-slate-200 pb-4 mb-6 gap-4">
              <div>
                <h1 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-blue-600 animate-pulse" />
                  Curva Experimental: {currentSpecimen.specimen_id}
                </h1>
                <p className="text-xs text-slate-500 mt-1 font-semibold uppercase">
                  Proceso: {currentSpecimen.manufacturing_process} | Geometría: {currentSpecimen.specimen_geometry || "Estandarizada"} ({currentSpecimen.length_mm || 50}x{currentSpecimen.width_mm || 50}x{currentSpecimen.thickness_mm || 50} mm)
                </p>
              </div>
              {currentProperties?.curve_quality_score !== undefined && (
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Puntaje de Curva:</span>
                  <span className={`inline-block px-2.5 py-1 rounded text-xs font-bold uppercase border ${
                    currentProperties.curve_quality_score > 0.95
                      ? "bg-emerald-50 border-emerald-200 text-emerald-700"
                      : "bg-amber-50 border-amber-200 text-amber-700"
                  }`}>
                    {(currentProperties.curve_quality_score * 100).toFixed(1)}% Calidad
                  </span>
                </div>
              )}
            </div>

            {/* Calculated Properties Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
              <div className="bg-white border border-slate-200 rounded p-3 text-center">
                <div className="text-[9px] uppercase font-bold text-slate-400">Módulo de Young</div>
                <div className="text-base font-extrabold text-slate-800 mt-1">
                  {currentProperties?.young_modulus_MPa ? `${currentProperties.young_modulus_MPa.toFixed(1)} MPa` : "N/A"}
                </div>
              </div>
              <div className="bg-white border border-slate-200 rounded p-3 text-center">
                <div className="text-[9px] uppercase font-bold text-slate-400">Esfuerzo Máximo</div>
                <div className="text-base font-extrabold text-slate-800 mt-1">
                  {currentProperties?.max_stress_MPa ? `${currentProperties.max_stress_MPa.toFixed(2)} MPa` : "N/A"}
                </div>
              </div>
              <div className="bg-white border border-slate-200 rounded p-3 text-center">
                <div className="text-[9px] uppercase font-bold text-slate-400">Esfuerzo de Fluencia</div>
                <div className="text-base font-extrabold text-slate-800 mt-1">
                  {currentProperties?.compressive_strength_MPa || currentProperties?.ultimate_tensile_strength_MPa
                    ? `${(currentProperties.compressive_strength_MPa || currentProperties.ultimate_tensile_strength_MPa).toFixed(2)} MPa`
                    : "N/A"}
                </div>
              </div>
              <div className="bg-white border border-slate-200 rounded p-3 text-center">
                <div className="text-[9px] uppercase font-bold text-slate-400">Absorción Energía (SEA)</div>
                <div className="text-base font-extrabold text-slate-800 mt-1">
                  {currentProperties?.specific_energy_absorption_kJ_kg ? `${currentProperties.specific_energy_absorption_kJ_kg.toFixed(2)} kJ/kg` : "N/A"}
                </div>
              </div>
              <div className="bg-white border border-slate-200 rounded p-3 text-center">
                <div className="text-[9px] uppercase font-bold text-slate-400">Plateau Stress</div>
                <div className="text-base font-extrabold text-slate-800 mt-1">
                  {currentProperties?.plateau_stress_MPa ? `${currentProperties.plateau_stress_MPa.toFixed(2)} MPa` : "N/A"}
                </div>
              </div>
              <div className="bg-white border border-slate-200 rounded p-3 text-center">
                <div className="text-[9px] uppercase font-bold text-slate-400">Crushing Efficiency (CFE)</div>
                <div className="text-base font-extrabold text-slate-800 mt-1">
                  {currentProperties?.crushing_force_efficiency ? `${(currentProperties.crushing_force_efficiency * 100).toFixed(1)}%` : "N/A"}
                </div>
              </div>
            </div>

            {/* Graphs: Stress-Strain and Force-Displacement */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1 min-h-[350px]">
              
              {/* Stress vs Strain */}
              <div className="bg-white border border-slate-200 rounded p-4 flex flex-col shadow-xs">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 border-b border-slate-200 pb-2 mb-4 flex items-center justify-between">
                  <span>Esfuerzo vs Deformación (Stress-Strain)</span>
                  <span className="text-[9px] text-slate-400 uppercase font-semibold">Región Elástica 0.0005–0.0025</span>
                </h3>
                {curveData.length === 0 ? (
                  <div className="flex-1 flex items-center justify-center text-slate-400 text-xs">
                    Cargando puntos de curva...
                  </div>
                ) : (
                  <div className="flex-1 min-h-[280px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={curveData} margin={{ left: -10, right: 10, top: 10, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis 
                          dataKey="strain" 
                          type="number"
                          domain={[0, 'auto']} 
                          tickFormatter={(v) => v.toFixed(3)}
                          label={{ value: "Deformación (Strain)", position: "insideBottom", offset: -5, className: "text-[10px] font-bold fill-slate-500 font-mono" }}
                          tick={{ fontSize: 9, fontFamily: "monospace" }}
                        />
                        <YAxis 
                          label={{ value: "Esfuerzo (MPa)", angle: -90, position: "insideLeft", offset: 15, className: "text-[10px] font-bold fill-slate-500 font-mono" }}
                          tick={{ fontSize: 9, fontFamily: "monospace" }}
                        />
                        <Tooltip 
                          formatter={(value) => [`${value} MPa`, 'Esfuerzo']}
                          labelFormatter={(label) => `Strain: ${parseFloat(label as string).toFixed(5)}`}
                          contentStyle={{ fontSize: 10, fontFamily: "monospace", borderRadius: 4, border: "1px solid #cbd5e1" }}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="stress" 
                          stroke="#2563eb" 
                          dot={false} 
                          strokeWidth={2} 
                        />
                        {/* Reference lines for elastic modulus linear regression boundaries */}
                        <ReferenceLine x={0.0005} stroke="#94a3b8" strokeDasharray="3 3" />
                        <ReferenceLine x={0.0025} stroke="#94a3b8" strokeDasharray="3 3" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>

              {/* Force vs Displacement */}
              <div className="bg-white border border-slate-200 rounded p-4 flex flex-col shadow-xs">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 border-b border-slate-200 pb-2 mb-4">
                  Fuerza vs Desplazamiento (Force-Displacement)
                </h3>
                {curveData.length === 0 ? (
                  <div className="flex-1 flex items-center justify-center text-slate-400 text-xs">
                    Cargando puntos de curva...
                  </div>
                ) : (
                  <div className="flex-1 min-h-[280px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={curveData} margin={{ left: -10, right: 10, top: 10, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis 
                          dataKey="displacement" 
                          type="number"
                          domain={[0, 'auto']} 
                          tickFormatter={(v) => v.toFixed(1)}
                          label={{ value: "Desplazamiento (mm)", position: "insideBottom", offset: -5, className: "text-[10px] font-bold fill-slate-500 font-mono" }}
                          tick={{ fontSize: 9, fontFamily: "monospace" }}
                        />
                        <YAxis 
                          label={{ value: "Fuerza (N)", angle: -90, position: "insideLeft", offset: 15, className: "text-[10px] font-bold fill-slate-500 font-mono" }}
                          tick={{ fontSize: 9, fontFamily: "monospace" }}
                        />
                        <Tooltip 
                          formatter={(value) => [`${value} N`, 'Fuerza']}
                          labelFormatter={(label) => `Disp: ${parseFloat(label as string).toFixed(3)} mm`}
                          contentStyle={{ fontSize: 10, fontFamily: "monospace", borderRadius: 4, border: "1px solid #cbd5e1" }}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="force" 
                          stroke="#db2777" 
                          dot={false} 
                          strokeWidth={2} 
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>

            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-400 gap-2 border-2 border-dashed border-slate-200 rounded">
            <Info className="w-8 h-8 text-slate-300" />
            <span>Selecciona una probeta del catálogo de la izquierda para ver su curva stress-strain.</span>
          </div>
        )}

      </div>
    </div>
  );
}

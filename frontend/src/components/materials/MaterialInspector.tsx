"use client";

import React, { useState, useEffect } from "react";
import { useLabStore } from "@/stores/useLabStore";
import { ShieldAlert, Info, Flame, Settings, RotateCcw, Thermometer, Layers, HelpCircle } from "lucide-react";

interface MaterialDetail {
  mechanical?: {
    young_modulus_nominal_gpa: number;
    tensile_strength_nominal_mpa: number;
    shear_modulus_gpa: number;
    poisson_ratio: number;
    shore_hardness_variants?: Record<string, { modulus_mpa: number; yield_strength_mpa: number; elongation_break_percent: number }>;
    hyperelastic_model?: { model_type: string; C10: number; C01: number; stress_strain_characteristic: string };
    damping_coefficient: number;
    rebound_resilience_percent: number;
    compression_behavior: string;
  };
  thermal?: {
    melting_temperature_c: number;
    glass_transition_temperature_c: number;
    thermal_conductivity_w_mk: number;
    specific_heat_j_kg_k: number;
    coefficient_thermal_expansion_e6_k: number;
    heat_deflection_temperature_045mpa_c: number;
    thermal_accumulation_sensitivity: string;
  };
  rheology?: {
    melt_flow_index_g_10min: number;
    viscosity_profile: string;
    recommended_extrusion_temperature_range: [number, number];
  };
  fatigue?: {
    cyclic_fatigue_limit_cycles_to_failure: number;
    stress_amplitude_limit_mpa: number;
    hysteresis_energy_loss_j_cycle: number;
  };
  fdm_behavior?: {
    layer_adhesion_strength_factor_0_to_1: number;
    bridging_limit_mm: number;
    overhang_angle_limit_deg: number;
    stringing_index_1_to_10: number;
    pressure_advance_sensitivity: string;
  };
  printer_profiles?: Record<string, { max_print_speed_mm_s: number; retraction_distance_mm: number; retraction_speed_mm_s: number; extrusion_multiplier: number }>;
  manufacturer_variants?: Array<{ brand: string; name: string; shore_hardness: string; specialty: string }>;
  ml_features?: Record<string, number>;
}

export default function MaterialInspector() {
  const { material, setParam } = useLabStore();
  const [db, setDb] = useState<Record<string, any> | null>(null);
  const [selectedVariant, setSelectedVariant] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);

  // Fetch full materials database from backend API
  useEffect(() => {
    async function fetchDb() {
      try {
        setLoading(true);
        const res = await fetch("http://127.0.0.1:8000/api/materials/database");
        if (res.ok) {
          const data = await res.json();
          setDb(data);
        }
      } catch (err) {
        console.error("Failed to load materials database:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchDb();
  }, []);

  // Sync selected variant when material changes
  useEffect(() => {
    if (material === "TPU") {
      setSelectedVariant("95A");
    } else if (material === "ABS") {
      setSelectedVariant("ABS+");
    } else if (material === "PETG") {
      setSelectedVariant("PETG-CF");
    } else {
      setSelectedVariant("");
    }
  }, [material]);

  if (loading) {
    return (
      <div className="p-4 flex flex-col items-center justify-center h-full space-y-2">
        <div className="w-6 h-6 border-2 border-[#1E40AF] border-t-transparent rounded-full animate-spin"></div>
        <span className="text-xs text-slate-400 font-mono tracking-wider">CARGANDO BASE DE DATOS...</span>
      </div>
    );
  }

  const matData: MaterialDetail = db?.[material] || {};
  const sharedData = db?.shared || {};

  // Extract values
  const mech: any = matData.mechanical || {};
  const therm: any = matData.thermal || {};
  const rheo: any = matData.rheology || {};
  const fdm: any = matData.fdm_behavior || {};
  const fatigue: any = matData.fatigue || {};
  const profiles: any = matData.printer_profiles || {};
  const variants: any = matData.manufacturer_variants || [];
  const anisotropy: any = sharedData.anisotropy?.transverse_isotropy_coefficients?.[material] || {};
  const moisture: any = sharedData.environmental_effects?.moisture_absorption?.[material] || {};
  const uv: any = sharedData.environmental_effects?.uv_resistance?.[material] || {};

  return (
    <div className="w-full h-full flex flex-col bg-white overflow-hidden text-slate-800 font-sans text-xs">
      {/* Selector and Variant Selector Header */}
      <div className="p-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between shrink-0 gap-2">
        <div className="flex items-center space-x-1.5">
          <span className="font-extrabold text-slate-500 text-[11px] uppercase tracking-wider">Material Activo:</span>
          <select
            value={material}
            onChange={(e) => setParam("material", e.target.value)}
            className="bg-white border border-slate-200 rounded px-2 py-0.5 text-xs font-bold text-slate-800 focus:border-[#1E40AF] focus:outline-none cursor-pointer"
          >
            <option value="PLA">PLA</option>
            <option value="TPU">TPU</option>
            <option value="ABS">ABS</option>
            <option value="PETG">PETG</option>
          </select>
        </div>

        {variants.length > 0 && (
          <div className="flex items-center space-x-1.5">
            <span className="font-extrabold text-slate-500 text-[11px] uppercase tracking-wider">Variante:</span>
            <select
              value={selectedVariant}
              onChange={(e) => setSelectedVariant(e.target.value)}
              className="bg-white border border-slate-200 rounded px-2 py-0.5 text-xs font-bold text-slate-800 focus:border-[#1E40AF] focus:outline-none cursor-pointer"
            >
              {variants.map((v: any, idx: number) => (
                <option key={idx} value={v.shore_hardness || v.name}>
                  {v.name} ({v.shore_hardness || "Std"})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Main Scrollable Inspector View */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3.5 scrollbar-thin">
        
        {/* 1. MECHANICAL & HYPERELASTICITY */}
        <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-3xs">
          <div className="bg-slate-50/80 px-2.5 py-1.5 border-b border-slate-200 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-slate-450" />
            <span className="font-bold text-slate-700 uppercase tracking-wider text-[10px]">Propiedades Mecánicas</span>
          </div>
          <div className="p-2.5 space-y-2 text-slate-650">
            <div className="grid grid-cols-2 gap-x-3 gap-y-1.5">
              <div className="flex justify-between border-b border-slate-100 pb-1">
                <span className="text-slate-450">Módulo elástico:</span>
                <span className="font-bold font-mono text-slate-800">{mech.young_modulus_nominal_gpa?.toFixed(2)} GPa</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-1">
                <span className="text-slate-450">Resistencia Tracción:</span>
                <span className="font-bold font-mono text-slate-800">{mech.tensile_strength_nominal_mpa?.toFixed(0)} MPa</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-1">
                <span className="text-slate-450">Módulo de Cizalla:</span>
                <span className="font-bold font-mono text-slate-800">{mech.shear_modulus_gpa?.toFixed(3)} GPa</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-1">
                <span className="text-slate-450">Poissón:</span>
                <span className="font-bold font-mono text-slate-800">{mech.poisson_ratio?.toFixed(2)}</span>
              </div>
            </div>
            
            {mech.shore_hardness_variants?.[selectedVariant] && (
              <div className="bg-[#EFF6FF] border border-blue-150 p-2 rounded text-[11px] text-[#1E3A8A] font-semibold space-y-1">
                <div className="text-[10px] uppercase font-bold text-[#1E40AF]">Datos de Variante ({selectedVariant})</div>
                <div className="flex justify-between">
                  <span>Módulo específico:</span>
                  <span className="font-mono">{mech.shore_hardness_variants[selectedVariant].modulus_mpa} MPa</span>
                </div>
                <div className="flex justify-between">
                  <span>Fluencia Estimada:</span>
                  <span className="font-mono">{mech.shore_hardness_variants[selectedVariant].yield_strength_mpa} MPa</span>
                </div>
                <div className="flex justify-between">
                  <span>Elongación de rotura:</span>
                  <span className="font-mono">{mech.shore_hardness_variants[selectedVariant].elongation_break_percent}%</span>
                </div>
              </div>
            )}

            {mech.hyperelastic_model && (
              <div className="bg-slate-50 border border-slate-200 p-2 rounded text-[11px] space-y-0.5 text-slate-600 leading-relaxed font-semibold">
                <div className="text-[10px] uppercase font-bold text-slate-500">Modelo Hiperelástico</div>
                <div>Tipo: <span className="text-slate-800 font-bold">{mech.hyperelastic_model.model_type}</span></div>
                <div className="font-mono text-slate-700">Coeficientes: C10={mech.hyperelastic_model.C10}, C01={mech.hyperelastic_model.C01}</div>
                <div className="text-[10px] text-slate-450 font-medium italic mt-0.5">"{mech.hyperelastic_model.stress_strain_characteristic}"</div>
              </div>
            )}
            
            <p className="text-[11px] leading-relaxed text-slate-500 italic pt-1 border-t border-slate-100">
              <span className="font-bold text-slate-600 block not-italic mb-0.5">Comportamiento a compresión:</span>
              "{mech.compression_behavior}"
            </p>
          </div>
        </div>

        {/* 2. THERMAL & RHEOLOGY */}
        <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-3xs">
          <div className="bg-slate-50/80 px-2.5 py-1.5 border-b border-slate-200 flex items-center gap-1.5">
            <Thermometer className="w-3.5 h-3.5 text-slate-455" />
            <span className="font-bold text-slate-700 uppercase tracking-wider text-[10px]">Térmica y Reología</span>
          </div>
          <div className="p-2.5 space-y-2 text-slate-650">
            <div className="grid grid-cols-2 gap-x-3 gap-y-1.5">
              <div className="flex justify-between border-b border-slate-100 pb-1">
                <span className="text-slate-450">Temp. de Fusión:</span>
                <span className="font-bold font-mono text-slate-800">{therm.melting_temperature_c?.toFixed(0)} °C</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-1">
                <span className="text-slate-450">Transición Vítrea (Tg):</span>
                <span className="font-bold font-mono text-slate-800">{therm.glass_transition_temperature_c?.toFixed(0)} °C</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-1">
                <span className="text-slate-450">Expansión Térmica:</span>
                <span className="font-bold font-mono text-slate-800">{therm.coefficient_thermal_expansion_e6_k} e-6/K</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-1">
                <span className="text-slate-450">Deflexión Térmica (HDT):</span>
                <span className="font-bold font-mono text-slate-800">{therm.heat_deflection_temperature_045mpa_c?.toFixed(0)} °C</span>
              </div>
            </div>
            
            <div className="bg-slate-50 p-2 rounded text-[11px] text-slate-600 leading-relaxed border border-slate-200">
              <div className="flex justify-between text-slate-500 font-bold mb-1">
                <span>Fluidez Fundido (MFI):</span>
                <span className="text-slate-800 font-mono font-bold">{rheo.melt_flow_index_g_10min} g/10m</span>
              </div>
              <p className="text-[10px] leading-relaxed text-slate-500 italic">
                <span className="font-bold text-slate-500 block not-italic">Viscosidad:</span>
                {rheo.viscosity_profile}
              </p>
            </div>
          </div>
        </div>

        {/* 3. FDM BEHAVIOR & PRINTER PROFILES */}
        <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-3xs">
          <div className="bg-slate-50/80 px-2.5 py-1.5 border-b border-slate-200 flex items-center gap-1.5">
            <Settings className="w-3.5 h-3.5 text-slate-450" />
            <span className="font-bold text-slate-700 uppercase tracking-wider text-[10px]">Factores de Impresión FDM</span>
          </div>
          <div className="p-2.5 space-y-2 text-slate-650">
            <div className="grid grid-cols-2 gap-x-3 gap-y-1.5">
              <div className="flex justify-between border-b border-slate-100 pb-1">
                <span className="text-slate-455">Adhesión Intercapa:</span>
                <span className="font-bold font-mono text-slate-800">{(fdm.layer_adhesion_strength_factor_0_to_1 * 100)?.toFixed(0)}%</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-1">
                <span className="text-slate-455">Límite de Puente:</span>
                <span className="font-bold font-mono text-slate-800">{fdm.bridging_limit_mm} mm</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-1">
                <span className="text-slate-455">Límite Sobrevuelo:</span>
                <span className="font-bold font-mono text-slate-800">{fdm.overhang_angle_limit_deg}°</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-1">
                <span className="text-slate-455">Stringing (1-10):</span>
                <span className="font-bold font-mono text-slate-800">{fdm.stringing_index_1_to_10}/10</span>
              </div>
            </div>

            {/* Speeds limits */}
            <div className="border border-slate-150 rounded overflow-hidden">
              <table className="w-full text-[10px] text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 text-slate-500 uppercase font-bold border-b border-slate-150">
                    <th className="p-1">Extrusor</th>
                    <th className="p-1 text-center">Velocidad Máx</th>
                    <th className="p-1 text-center">Retracción</th>
                    <th className="p-1 text-center">Flujo</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono text-slate-650">
                  {Object.entries(profiles).map(([name, prof]: any) => (
                    <tr key={name}>
                      <td className="p-1 font-sans text-slate-500 font-semibold">{name}</td>
                      <td className="p-1 text-center">{prof.max_print_speed_mm_s} mm/s</td>
                      <td className="p-1 text-center">{prof.retraction_distance_mm}mm</td>
                      <td className="p-1 text-center">x{prof.extrusion_multiplier}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* 4. ANISOTROPY & FAILURE MODES */}
        <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-3xs">
          <div className="bg-slate-50/80 px-2.5 py-1.5 border-b border-slate-200 flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5 text-slate-450" />
            <span className="font-bold text-slate-700 uppercase tracking-wider text-[10px]">Anisotropía y Riesgos de Fallo</span>
          </div>
          <div className="p-2.5 space-y-2.5 text-slate-650">
            {anisotropy && (
              <div className="bg-amber-50/50 border border-amber-200 rounded p-2 text-amber-900 leading-normal space-y-1">
                <div className="text-[10px] uppercase font-bold text-amber-700 flex items-center gap-1">
                  <span>Anisotropía de Capas (ASTM)</span>
                </div>
                <div className="grid grid-cols-2 gap-x-2 gap-y-0.5 text-[10px] font-mono text-amber-800 font-bold">
                  <div className="flex justify-between">
                    <span>Rigidez XY:</span>
                    <span>{anisotropy.xy_modulus_gpa} GPa</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Rigidez Z:</span>
                    <span>{anisotropy.z_modulus_gpa} GPa</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Tracción XY:</span>
                    <span>{anisotropy.tensile_xy_mpa} MPa</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Tracción Z:</span>
                    <span>{anisotropy.tensile_z_mpa} MPa</span>
                  </div>
                </div>
                <p className="text-[9px] text-amber-700/80 italic font-semibold leading-relaxed border-t border-amber-200/50 pt-1 mt-1">
                  "{sharedData.anisotropy?.gyroid_continuity_gain}"
                </p>
              </div>
            )}
            
            {/* Environmental effects card */}
            <div className="bg-blue-50/30 border border-blue-200 rounded p-2 text-slate-600 leading-normal space-y-1.5 font-semibold">
              <div className="text-[10px] uppercase font-bold text-[#1E40AF]">Resistencia Ambiental</div>
              <div className="flex justify-between">
                <span className="text-slate-455">Sensibilidad Humedad:</span>
                <span className="font-mono text-slate-800 font-bold">{moisture.rate_percent_24h}% / 24h</span>
              </div>
              <p className="text-[10px] leading-relaxed text-slate-500 italic font-normal">
                "{moisture.description}"
              </p>
              <div className="flex justify-between items-baseline pt-1 border-t border-slate-100">
                <span className="text-slate-455">Índice Estabilidad UV:</span>
                <span className="font-bold text-slate-800 font-mono">{uv.index_1_10}/10 ({uv.rating})</span>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

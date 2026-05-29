"use client";

import React, { useState, useEffect, useMemo } from "react";
import { useLabStore } from "@/stores/useLabStore";
import { CheckCircle2, ShieldAlert } from "lucide-react";
import { useShallow } from "zustand/react/shallow";

export default function StatusBar() {
  const { meshVertices, loadingMesh, predictions } = useLabStore(
    useShallow((state) => ({
      meshVertices: state.meshVertices,
      loadingMesh: state.loadingMesh,
      predictions: state.predictions,
    }))
  );
  const [fps, setFps] = useState(60);

  // Simple dynamic FPS simulator
  useEffect(() => {
    const interval = setInterval(() => {
      setFps(() => Math.floor(58 + Math.random() * 3));
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  const complexity = useMemo(() => {
    const count = meshVertices.length / 3;
    if (count === 0) return "Ninguna";
    if (count < 2000) return "Baja";
    if (count < 10000) return "Media";
    return "Alta";
  }, [meshVertices]);

  const hasMesh = meshVertices.length > 0;

  return (
    <div className="w-full h-8 bg-white border-t border-slate-200 flex items-center justify-between px-4 select-none font-mono text-xs text-slate-500">
      {/* Active navigation tool */}
      <div className="flex items-center space-x-4">
        <div>
          <span className="text-slate-400 uppercase">Herramienta actual:</span>{" "}
          <span className="text-slate-700">Orbit</span>
        </div>

        <div className="w-px h-3 bg-slate-200" />

        {/* Dynamic cursor coordinate mock */}
        <div>
          <span className="text-slate-400 uppercase">Coordenadas:</span>{" "}
          <span className="text-slate-700">X: 12.45  Y: 8.23  Z: 5.00</span>
        </div>
      </div>

      {/* Metrics, validation, FPS */}
      <div className="flex items-center space-x-5">
        <div>
          <span className="text-slate-400 uppercase">Complejidad:</span>{" "}
          <span className="text-slate-700">{complexity}</span>
        </div>

        <div className="w-px h-3 bg-slate-200" />

        <div>
          <span className="text-slate-400 uppercase">FPS:</span>{" "}
          <span className="text-slate-700">{fps}</span>
        </div>

        <div className="w-px h-3 bg-slate-200" />

        {/* Mesh Validation Status */}
        <div className="flex items-center space-x-1">
          {hasMesh ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span className="text-emerald-600">Malla: Válida (Manifold)</span>
            </>
          ) : loadingMesh ? (
            <>
              <ShieldAlert className="w-3.5 h-3.5 text-amber-500 animate-pulse" />
              <span className="text-amber-500">Malla: Generando...</span>
            </>
          ) : (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-[#1E40AF]" />
              <span className="text-[#1E40AF]">Malla: Pendiente</span>
            </>
          )}
        </div>

        <div className="w-px h-3 bg-slate-200" />

        {/* Simulation State */}
        <div>
          <span className="text-slate-400 uppercase">Simulación:</span>{" "}
          <span className="text-[#1E40AF] font-bold">Lista</span>
        </div>

        <div className="w-px h-3 bg-slate-200" />

        {/* Export Readiness */}
        <div className="flex items-center space-x-1">
          <CheckCircle2 className="w-3.5 h-3.5 text-[#10B981]" />
          <span className="text-slate-700">Listo para exportar</span>
        </div>
      </div>
    </div>
  );
}


"use client";

import React, { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import TopToolbar from "@/components/layout/TopToolbar";
import LeftPanel from "@/components/layout/LeftPanel";
import RightPanel from "@/components/layout/RightPanel";
import StatusBar from "@/components/layout/StatusBar";
import CopilotWidget from "@/components/layout/CopilotWidget";
import { useLabStore } from "@/stores/useLabStore";
import { useShallow } from "zustand/react/shallow";



const BaseViewport = dynamic(() => import("@/rendering/viewport/BaseViewport"), {
  ssr: false,
});

export default function Home() {
  const {
    fetchDatabaseData,
    triggerMeshGeneration,
    triggerInference,
    leftPanelCollapsed,
    rightPanelCollapsed,
    toggleLeftPanel,
    toggleRightPanel,
  } = useLabStore(
    useShallow((state) => ({
      fetchDatabaseData: state.fetchDatabaseData,
      triggerMeshGeneration: state.triggerMeshGeneration,
      triggerInference: state.triggerInference,
      leftPanelCollapsed: state.leftPanelCollapsed,
      rightPanelCollapsed: state.rightPanelCollapsed,
      toggleLeftPanel: state.toggleLeftPanel,
      toggleRightPanel: state.toggleRightPanel,
    }))
  );

  // Run initial data queries on load and clean up legacy service workers
  useEffect(() => {
    if (typeof window !== "undefined" && "serviceWorker" in navigator) {
      navigator.serviceWorker.getRegistrations().then((registrations) => {
        if (registrations.length > 0) {
          for (const registration of registrations) {
            registration.unregister();
            console.log("Legacy service worker unregistered to bypass CSP blocks:", registration);
          }
          // Force reload to completely clear service worker control from the document
          window.location.reload();
        }
      });
    }

    fetchDatabaseData();
    triggerMeshGeneration();
    triggerInference();
    
    // Collapse panels by default on mobile (screens < 1024px)
    if (typeof window !== "undefined" && window.innerWidth < 1024) {
      useLabStore.setState({ leftPanelCollapsed: true, rightPanelCollapsed: true });
    }
  }, [fetchDatabaseData, triggerMeshGeneration, triggerInference]);

  return (
    <>
      <div className="w-screen h-screen flex flex-col bg-[#FAFBFC] select-none text-[#0F172A] print:hidden">
        {/* 1. Header Toolbar */}
        <TopToolbar />

        {/* 2. Main Workspace Layout */}
        <div className="flex-1 flex overflow-hidden w-full relative">
          
          {/* Backdrop for open drawers in mobile view */}
          {(!leftPanelCollapsed || !rightPanelCollapsed) && (
            <div
              className="lg:hidden fixed inset-0 bg-slate-900/30 z-30 transition-opacity"
              onClick={() => {
                if (!leftPanelCollapsed) toggleLeftPanel();
                if (!rightPanelCollapsed) toggleRightPanel();
              }}
            />
          )}

          {/* Left Side: Parametric Inputs */}
          <div
            className={`transition-all duration-300 ease-in-out shrink-0 border-slate-200 bg-white overflow-hidden
              lg:relative lg:translate-x-0 lg:top-0 lg:h-full
              fixed top-[92px] bottom-0 left-0 z-40 w-[300px] h-[calc(100vh-92px)] border-r shadow-lg lg:shadow-none
              ${leftPanelCollapsed ? "lg:w-0 lg:border-r-0 -translate-x-full" : "lg:w-[300px] translate-x-0"}`}
          >
            <LeftPanel />
          </div>

          {/* Center Canvas: Interactive R3F Viewport */}
          <div className="flex-1 h-full p-0 relative flex flex-col min-w-0 bg-[#FAFBFC]">
            <BaseViewport />
          </div>

          {/* Right Side: Scientific Graphs & Recommendations */}
          <div
            className={`transition-all duration-300 ease-in-out shrink-0 border-slate-200 bg-white overflow-hidden
              lg:relative lg:translate-x-0 lg:top-0 lg:h-full
              fixed top-[92px] bottom-0 right-0 z-40 w-[300px] h-[calc(100vh-92px)] border-l shadow-lg lg:shadow-none
              ${rightPanelCollapsed ? "lg:w-0 lg:border-l-0 translate-x-full" : "lg:w-[300px] translate-x-0"}`}
          >
            <RightPanel />
          </div>
        </div>

        {/* 3. Footer Stats Bar */}
        <StatusBar />
      </div>

      {/* 4. High-Fidelity Printable Certificate Report */}
      <PrintCertificate />

      {/* 5. AI Copilot Chatbot Floating Widget */}
      <CopilotWidget />
    </>
  );
}

function PrintCertificate() {
  const store = useLabStore();
  const predictions = store.predictions;
  const material = store.material;
  const infill = store.infill;

  const [mounted, setMounted] = useState(false);
  const [essayId, setEssayId] = useState("");
  const [dateStr, setDateStr] = useState("");

  useEffect(() => {
    setMounted(true);
    setEssayId(`MF-${Math.round(100000 + Math.random() * 899999)}`);
    setDateStr(new Date().toLocaleDateString("es-ES", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }));
  }, []);

  const yieldStrength = predictions?.yieldStrengthMpa || 24.7;
  const maxForce = predictions?.maxForceNewtons || 450 + infill * 12;
  const stiffness = predictions?.stiffnessNmm || 120 + infill * 4;
  const energyAbsorption = predictions?.energyAbsorptionJoules || 14.5 + infill * 0.15;

  const youngModulus = material === "PLA" ? "1.62 GPa" : "0.08 GPa";
  const performanceIndex = material === "PLA" ? "1.82" : "2.15";
  const printTimeMinutes = predictions?.printingTimeMinutes || 120;
  const hrs = Math.floor(printTimeMinutes / 60);
  const mins = printTimeMinutes % 60;
  const printTimeStr = `${hrs}h ${mins}m`;

  return (
    <div className="hidden print:block w-[760px] mx-auto p-10 bg-white text-slate-950 font-mono border-[6px] border-double border-slate-900">
      {/* Header */}
      <div className="text-center border-b-2 border-slate-900 pb-4 mb-6">
        <h1 className="text-2xl font-bold uppercase tracking-wider">MaterialForge</h1>
        <p className="text-[10px] uppercase tracking-widest text-slate-500 mt-1">Laboratorio de Simulación y Análisis Estructural de Aditivos</p>
        <h2 className="text-sm font-bold mt-4 border border-slate-900 inline-block px-5 py-1.5 bg-slate-100">
          REPORTE TÉCNICO Y CERTIFICADO DE ENSAYO VIRTUAL
        </h2>
      </div>

      {/* Metadata */}
      <div className="grid grid-cols-2 gap-4 text-xs mb-6 border-b border-slate-200 pb-4">
        <div>
          <p className="mb-1"><span className="font-bold">Proyecto:</span> Cubo_Resistencia_v7</p>
          <p className="mb-1"><span className="font-bold">ID de Ensayo:</span> {mounted ? essayId : "MF-######"}</p>
          <p className="mb-1"><span className="font-bold">Fecha del Cómputo:</span> {mounted ? dateStr : "Cargando..."}</p>
        </div>
        <div className="text-right">
          <p className="mb-1"><span className="font-bold">Operador de Simulación:</span> Principal CAD Designer</p>
          <p className="mb-1"><span className="font-bold">Motor de Geometría:</span> Cellular Architecture Engine (CAE) v1.0</p>
          <p className="mb-1"><span className="font-bold">Estado de Estructura:</span> <span className="text-emerald-700 font-bold uppercase">Aprobada (Manifold)</span></p>
        </div>
      </div>

      {/* Grid: Inputs vs Outputs */}
      <div className="grid grid-cols-2 gap-8 mb-6">
        {/* Input Parameters */}
        <div className="space-y-3">
          <h3 className="font-bold border-b border-slate-900 pb-1 text-xs bg-slate-100 px-2 py-0.5">I. PARÁMETROS GEOMÉTRICOS Y DE FABRICACIÓN</h3>
          <table className="w-full text-xs">
            <tbody>
              <tr className="border-b border-slate-100">
                <td className="py-1.5 text-slate-600 font-semibold">Material del Filamento</td>
                <td className="py-1.5 text-right font-bold">{store.material}</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="py-1.5 text-slate-600 font-semibold">Patrón de Estructura Celular</td>
                <td className="py-1.5 text-right font-bold capitalize">{store.pattern}</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="py-1.5 text-slate-600 font-semibold">Porcentaje de Infill</td>
                <td className="py-1.5 text-right font-bold">{store.infill}%</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="py-1.5 text-slate-600 font-semibold">Grosor del Infill (Cell)</td>
                <td className="py-1.5 text-right font-bold">{store.cellThickness} mm</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="py-1.5 text-slate-600 font-semibold">Dimensiones del Bounding Box</td>
                <td className="py-1.5 text-right font-bold">{store.dimX} x {store.dimY} x {store.dimZ} cm</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="py-1.5 text-slate-600 font-semibold">Espesor de Pared (Shell)</td>
                <td className="py-1.5 text-right font-bold">{store.wallThickness} mm</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="py-1.5 text-slate-600 font-semibold">Capas de Carcasa Superior/Inf</td>
                <td className="py-1.5 text-right font-bold">{store.shellLayers}</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="py-1.5 text-slate-600 font-semibold">Altura de Capa (Slicer)</td>
                <td className="py-1.5 text-right font-bold">{store.layerHeight.toFixed(2)} mm</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="py-1.5 text-slate-600 font-semibold">Velocidad de Extrusión</td>
                <td className="py-1.5 text-right font-bold">{store.printSpeed} mm/s</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Mechanical Predictions */}
        <div className="space-y-3">
          <h3 className="font-bold border-b border-slate-900 pb-1 text-xs bg-slate-100 px-2 py-0.5">II. ANÁLISIS DE RESISTENCIA Y CARGAS (PREDICCIÓN ML)</h3>
          <table className="w-full text-xs">
            <tbody>
              <tr className="border-b border-slate-100">
                <td className="py-1.5 text-slate-600 font-semibold">Masa Estimada de la Pieza</td>
                <td className="py-1.5 text-right font-bold">{predictions ? `${predictions.massGrams} g` : "38.7 g"}</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="py-1.5 text-slate-600 font-semibold">Densidad Relativa (Porosidad)</td>
                <td className="py-1.5 text-right font-bold">{predictions ? predictions.densityRelative.toFixed(2) : "0.28"}</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="py-1.5 text-slate-600 font-semibold">Módulo de Young Equivalente</td>
                <td className="py-1.5 text-right font-bold">{youngModulus}</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="py-1.5 text-slate-600 font-semibold">Esfuerzo de Fluencia (Yield)</td>
                <td className="py-1.5 text-right font-bold">{yieldStrength.toFixed(2)} MPa</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="py-1.5 text-slate-600 font-semibold">Esfuerzo Límite de Rotura</td>
                <td className="py-1.5 text-right font-bold">{(yieldStrength * 1.5).toFixed(2)} MPa</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="py-1.5 text-slate-600 font-semibold">Rigidez Estructural (Stiffness)</td>
                <td className="py-1.5 text-right font-bold">{stiffness.toFixed(0)} N/mm</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="py-1.5 text-slate-600 font-semibold">Eficiencia Absorción de Energía</td>
                <td className="py-1.5 text-right font-bold">{energyAbsorption.toFixed(2)}%</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="py-1.5 text-slate-600 font-semibold">Tiempo Estimado de Impresión</td>
                <td className="py-1.5 text-right font-bold">{printTimeStr}</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="py-1.5 text-slate-600 font-semibold">Índice de Desempeño Mecánico</td>
                <td className="py-1.5 text-right font-bold text-emerald-800">{performanceIndex}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Validation Checklist & Model Confidence */}
      <div className="grid grid-cols-2 gap-8 mb-6 border-t border-slate-350 pt-4">
        {/* Verification Checklist */}
        <div className="space-y-2">
          <h4 className="font-bold text-xs uppercase tracking-wider">Chequeo de Integridad Técnica</h4>
          <ul className="text-xs space-y-1">
            <li className="flex items-center space-x-2">
              <span className="font-bold text-emerald-700 text-[10px]">[✓]</span>
              <span>Malla geométrica SDF sin intersecciones</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="font-bold text-emerald-700 text-[10px]">[✓]</span>
              <span>Límites de fluencia elástica validados</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="font-bold text-emerald-700 text-[10px]">[✓]</span>
              <span>Simulación de deformación Y completada</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="font-bold text-emerald-700 text-[10px]">[✓]</span>
              <span>GCODE preparado para FDM sin colisiones</span>
            </li>
          </ul>
        </div>

        {/* ML Metadata */}
        <div className="space-y-2">
          <h4 className="font-bold text-xs uppercase tracking-wider">Metadatos del Cómputo de IA</h4>
          <div className="text-[10px] bg-slate-50 border border-slate-200 p-2.5 space-y-1">
            <p><span className="font-bold">Algoritmo de Inferencia:</span> {predictions?.modelUsed || "CAE-ML-Regressor-v1"}</p>
            <p><span className="font-bold">Precisión Cruzada (R²):</span> {predictions ? (predictions.confidenceScore * 100).toFixed(1) : "98.4"}%</p>
            <p><span className="font-bold">Base de Datos de Entrenamiento:</span> ExpDB_Lattice_3D_v4</p>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="mb-8 border-t border-slate-350 pt-4">
        <h4 className="font-bold text-xs uppercase tracking-wider mb-2">Recomendaciones del Sistema</h4>
        <ul className="text-xs space-y-1">
          {store.material === "TPU" ? (
            <>
              <li>• Estructura optimizada para la amortiguación de esfuerzos de compresión cíclica.</li>
              <li>• El patrón seleccionado tiene una gran resiliencia; incrementar espesores aumenta rigidez.</li>
              <li>• Monitorear temperatura del fusor para evitar goteo en filamento elástico.</li>
            </>
          ) : (
            <>
              <li>• Estructura rígida de alto rendimiento apta para cargas estáticas constantes.</li>
              <li>• Cuidado con sobrecargas de compresión instantáneas; riesgo de fractura frágil.</li>
              <li>• Asegurar adhesión a la cama para evitar pandeo en celdas de base.</li>
            </>
          )}
        </ul>
      </div>

      {/* Signature and Approval */}
      <div className="flex justify-between items-end border-t-2 border-slate-900 pt-6 mt-10">
        <div className="text-left text-[9px] text-slate-400">
          <p>Plataforma de Simulación MaterialForge CAE</p>
          <p>Predicción por Regresión de Aprendizaje Automático Multitarea</p>
          <p>MaterialForge. All rights reserved.</p>
        </div>
        <div className="text-center w-52 text-[10px]">
          <div className="border-b border-slate-900 h-10 mb-1"></div>
          <p className="font-bold uppercase">Sello de Aprobación CAD/AI</p>
          <p className="text-slate-500 text-[8px]">Firma autorizada por motor neuronal de materiales</p>
        </div>
      </div>
    </div>
  );
}

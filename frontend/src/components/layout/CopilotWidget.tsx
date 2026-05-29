"use client";

import React, { useState, useEffect, useRef } from "react";
import { useLabStore } from "@/stores/useLabStore";
import { useDesignStore } from "@/stores/designStore";
import AIChatPanel from "../ai/AIChatPanel";
import AIRecommendationPanel from "../ai/AIRecommendationPanel";
import ManufacturingPanel from "@/slicing/manufacturing/ManufacturingPanel";
import { useShallow } from "zustand/react/shallow";
import {
  Sparkles,
  X,
  Bot,
  Maximize2,
  Minimize2
} from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

export default function CopilotWidget() {
  const store = useLabStore(
    useShallow((state) => ({
      material: state.material,
      infill: state.infill,
      pattern: state.pattern,
      cellSize: state.cellSize,
      cellThickness: state.cellThickness,
      wallThickness: state.wallThickness,
      dimX: state.dimX,
      dimY: state.dimY,
      dimZ: state.dimZ,
      resolution: state.resolution,
      layerHeight: state.layerHeight,
      printSpeed: state.printSpeed,
      viewportMode: state.viewportMode,
      appliedForce: state.appliedForce,
    }))
  );

  const {
    setAiRecommendations,
    fetchHistory,
    fetchVariants
  } = useDesignStore();

  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "MaterialForge CAE/CAD Optimization Kernel Ready.\n- Detect mechanical target constraints.\n- Compute structural cell parameters.\n- Optimize mass and infill density gradients.\n- Export slicing config patches.\n\nInput design target or request optimization candidate.",
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [healthStatus, setHealthStatus] = useState<string>("offline");
  const [bestModel, setBestModel] = useState<string>("");
  const [isExpanded, setIsExpanded] = useState(false);
  const [rightPanelTab, setRightPanelTab] = useState<"cae" | "manufacturing">("cae");

  const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  // Check health on load/open
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/copilot/health`);
        if (res.ok) {
          const data = await res.json();
          setHealthStatus(data.services?.ollama_connection === "online" ? "online" : "degraded");
        } else {
          setHealthStatus("offline");
        }
      } catch (err) {
        setHealthStatus("offline");
      }
    };
    checkHealth();

    if (isOpen) {
      const interval = setInterval(checkHealth, 60000);
      return () => clearInterval(interval);
    }
  }, [isOpen, BACKEND_URL]);

  // Fetch installed models
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/copilot/models`);
        if (res.ok) {
          const data = await res.json();
          setBestModel(data.best_chat_model || "");
        }
      } catch (err) {
        console.warn("Failed to fetch models metadata", err);
      }
    };
    if (isOpen) {
      fetchModels();
    }
  }, [isOpen, BACKEND_URL]);

  // Sync parameters history when opened
  useEffect(() => {
    if (isOpen) {
      fetchHistory();
      fetchVariants();
    }
  }, [
    isOpen,
    store.material,
    store.infill,
    store.pattern,
    store.cellSize,
    store.cellThickness,
    store.wallThickness,
    store.dimX,
    store.dimY,
    store.dimZ,
    store.resolution,
    store.layerHeight,
    store.printSpeed
  ]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessageContent = input.trim();
    setInput("");
    setIsLoading(true);

    const userMsgId = `user-${Date.now()}`;
    const assistantMsgId = `assistant-${Date.now()}`;

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: "user", content: userMessageContent },
    ]);

    setMessages((prev) => [
      ...prev,
      { id: assistantMsgId, role: "assistant", content: "", isStreaming: true },
    ]);

    const configPayload = {
      material: store.material,
      infill: Number(store.infill),
      pattern: store.pattern,
      cellSize: Number(store.cellSize),
      cellThickness: Number(store.cellThickness),
      wallThickness: Number(store.wallThickness),
      dimX: Number(store.dimX),
      dimY: Number(store.dimY),
      dimZ: Number(store.dimZ),
      resolution: store.resolution,
      layerHeight: Number(store.layerHeight),
      printSpeed: Number(store.printSpeed),
      viewportMode: store.viewportMode,
      shapeType: "Cubo",
      geometryId: "cube-default",
      appliedForce: Number(store.appliedForce),
      forceDirX: 0.0,
      forceDirY: 0.0,
      forceDirZ: -1.0,
      targetObjective: "balance",
      testType: "compression",
      loadCase: "static",
      maxMassG: 100.0,
      maxDimCm: 5.0,
    };

    const updatedMessages = [
      ...messages.map((m) => ({ role: m.role, content: m.content })),
      { role: "user", content: userMessageContent },
    ];

    try {
      const response = await fetch(`${BACKEND_URL}/api/copilot/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: updatedMessages,
          config: configPayload,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Error al conectar con el Copiloto.");
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("No readable stream response found.");
      }

      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      let accumulatedText = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const parsed = JSON.parse(line);
            if (parsed.type === "token") {
              accumulatedText += parsed.content;
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId
                    ? { ...msg, content: accumulatedText }
                    : msg
                )
              );
            } else if (parsed.type === "final") {
              const structured = parsed.response;
              
              // Load the parsed structured variants into the Design Store
              if (structured) {
                setAiRecommendations(structured);
              }

              // Update final assistant text with the parsed text summary
              const textContent = structured?.analysis?.text || accumulatedText;
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId
                    ? {
                        ...msg,
                        content: textContent,
                        isStreaming: false,
                      }
                    : msg
                )
              );
              
              // Open sidebar panel automatically if new variants are suggested
              if (structured?.variants?.length > 0) {
                setRightPanelTab("cae");
                if (!isExpanded) {
                  setIsExpanded(true);
                }
              }
            } else if (parsed.type === "error") {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId
                    ? {
                        ...msg,
                        isStreaming: false,
                        content: `Error: ${parsed.content}`,
                      }
                    : msg
                )
              );
            }
          } catch (err) {
            console.warn("Parse stream line failed:", line, err);
          }
        }
      }
    } catch (err: any) {
      console.error(err);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? {
                ...msg,
                isStreaming: false,
                content: `Disculpa, no puedo comunicarme con el modelo de IA local. Asegúrate de tener Ollama activo en el puerto 11434 y de contar con un modelo como qwen2.5-coder:7b o llama3.2 instalado. (${err.message})`,
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed bottom-12 right-6 z-[999] font-mono print:hidden">
      {/* 1. Floating Action Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="w-14 h-14 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-650 text-white flex items-center justify-center shadow-xl hover:shadow-2xl hover:scale-108 active:scale-95 transition-all duration-300 relative group cursor-pointer"
        >
          <div className="absolute inset-0 rounded-full border border-blue-450 animate-ping opacity-30" />
          <Bot className="w-6 h-6 animate-pulse" />
          <span className="absolute right-16 scale-0 group-hover:scale-100 bg-slate-900/90 text-white text-[10px] px-3 py-1.5 rounded-md whitespace-nowrap shadow-md pointer-events-none transition-all duration-300 font-bold border border-slate-700/50">
            Copiloto Científico IA
          </span>
          {healthStatus === "online" && (
            <div className="absolute top-0 right-0 w-3 h-3 bg-emerald-500 rounded-full border-2 border-white" />
          )}
        </button>
      )}

      {/* 2. Main Window */}
      {isOpen && (
        <div
          className={`flex flex-col bg-slate-900/95 text-white rounded-xl shadow-2xl border border-slate-700/50 backdrop-blur-md transition-all duration-350 ease-out
            ${
              isExpanded
                ? "w-[95vw] h-[85vh] md:w-[960px] md:h-[680px]"
                : "w-[90vw] h-[550px] sm:w-[400px] sm:h-[580px]"
            }
          `}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-slate-950/80 rounded-t-xl border-b border-slate-800">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-lg bg-blue-650 flex items-center justify-center text-white shadow-md shadow-blue-500/10">
                <Sparkles className="w-4 h-4 text-blue-100" />
              </div>
              <div>
                <h3 className="text-[11px] font-black uppercase tracking-wider text-slate-100">
                  MaterialForge Copilot
                </h3>
                <p className="text-[9px] text-slate-400">
                  {bestModel ? `${bestModel} • ` : ""}
                  {healthStatus === "online" ? (
                    <span className="text-emerald-400 font-semibold">● Local AI Conectada</span>
                  ) : healthStatus === "degraded" ? (
                    <span className="text-amber-400 font-semibold">▲ Degradado (Sin Ollama)</span>
                  ) : (
                    <span className="text-red-400 font-semibold">○ Desconectado</span>
                  )}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-1">
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="p-1.5 hover:bg-slate-850 rounded-md text-slate-400 hover:text-white transition-colors cursor-pointer"
                title={isExpanded ? "Reducir ventana" : "Expandir Panel de Ingeniería"}
              >
                {isExpanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 hover:bg-slate-850 rounded-md text-slate-400 hover:text-white transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Split Container Layout */}
          <div className="flex flex-1 overflow-hidden">
            {/* Left Column: Conversational Chat */}
            <div className="flex-1 flex flex-col min-w-0 p-3 bg-slate-900/60">
              <AIChatPanel
                messages={messages}
                input={input}
                setInput={setInput}
                isLoading={isLoading}
                handleSend={handleSend}
              />
            </div>

            {/* Right Column: Advanced Engineering Panel */}
            {isExpanded && (
              <div className="w-[460px] border-l border-slate-800 bg-slate-950/60 p-3 overflow-y-auto flex flex-col space-y-3">
                {/* Tabs Header */}
                <div className="flex bg-slate-950/80 border border-slate-800/80 p-0.5 rounded-lg text-xs shrink-0 select-none">
                  <button
                    onClick={() => setRightPanelTab("cae")}
                    className={`flex-1 py-1 text-[9px] font-bold rounded-md uppercase tracking-wider transition-all cursor-pointer text-center ${
                      rightPanelTab === "cae"
                        ? "bg-slate-800 text-slate-200 border border-slate-700/50 shadow-xs"
                        : "text-slate-500 hover:text-slate-350"
                    }`}
                  >
                    CAE / Co-Diseño
                  </button>
                  <button
                    onClick={() => setRightPanelTab("manufacturing")}
                    className={`flex-1 py-1 text-[9px] font-bold rounded-md uppercase tracking-wider transition-all cursor-pointer text-center ${
                      rightPanelTab === "manufacturing"
                        ? "bg-slate-800 text-slate-200 border border-slate-700/50 shadow-xs"
                        : "text-slate-500 hover:text-slate-350"
                    }`}
                  >
                    Impresión FDM
                  </button>
                </div>

                {/* Tab content container */}
                <div className="flex-1 min-h-0">
                  {rightPanelTab === "cae" ? (
                    <AIRecommendationPanel />
                  ) : (
                    <ManufacturingPanel />
                  )}
                </div>
              </div>
            )}
          </div>

        </div>
      )}
    </div>
  );
}

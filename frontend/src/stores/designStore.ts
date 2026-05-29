import { create } from "zustand";
import { useLabStore } from "./useLabStore";
import { applyConfigPatch } from "../utils/applyConfigPatch";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export interface ConfigPatch {
  material?: string;
  infill?: number;
  pattern?: string;
  cellSize?: number;
  cellThickness?: number;
  wallThickness?: number;
  dimX?: number;
  dimY?: number;
  dimZ?: number;
  resolution?: string;
  layerHeight?: number;
  printSpeed?: number;
  shapeType?: string;
}

export interface VariantData {
  id: string;
  name: string;
  description: string;
  score: number;
  compression_score: number;
  energy_absorption_score: number;
  stability_score: number;
  printability_score: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  estimated_print_time: string;
  estimated_mass: string;
  pros: string[];
  cons: string[];
  warnings: string[];
  config_patch: ConfigPatch;
}

export interface AIAnalysis {
  text: string;
  objective_detected: string;
  key_findings: string;
  mechanical_justification: string;
}

export interface AIRecommendations {
  analysis: AIAnalysis;
  variants: VariantData[];
  recommended_variant: string;
  ui_actions: string[];
}

export interface HistoryEntry {
  timestamp: string;
  action: string;
  diff: Record<string, { before: any; after: any }>;
}

export interface SimulationResult {
  stressMpa: number;
  deformationMm: number;
  energyAbsorption: number;
  failureRisk: string; // "LOW", "MEDIUM", "HIGH"
  warnings: string[];
}

interface DesignState {
  currentConfig: Partial<ConfigPatch>;
  currentVariant: VariantData | null;
  variants: VariantData[];
  variantHistory: HistoryEntry[];
  simulationResults: SimulationResult | null;
  aiRecommendations: AIRecommendations | null;
  pendingPatch: ConfigPatch | null;
  compareMode: boolean;
  loading: boolean;
  error: string | null;

  setPendingPatch: (patch: ConfigPatch | null) => void;
  setCurrentVariant: (variant: VariantData | null) => void;
  setCompareMode: (mode: boolean) => void;
  setAiRecommendations: (recs: AIRecommendations | null) => void;
  syncCurrentConfig: () => void;
  
  applyPatch: (patch?: ConfigPatch) => Promise<void>;
  revertLastPatch: () => Promise<void>;
  runSimulation: (variantId: string) => Promise<void>;
  duplicateVariant: (variant: VariantData) => void;
  exportVariant: (variant: VariantData) => void;
  fetchHistory: () => Promise<void>;
  fetchVariants: () => Promise<void>;
}

export const useDesignStore = create<DesignState>((set, get) => ({
  currentConfig: {},
  currentVariant: null,
  variants: [],
  variantHistory: [],
  simulationResults: null,
  aiRecommendations: null,
  pendingPatch: null,
  compareMode: false,
  loading: false,
  error: null,

  setPendingPatch: (patch) => set({ pendingPatch: patch }),
  setCurrentVariant: (variant) => set({ currentVariant: variant }),
  setCompareMode: (mode) => set({ compareMode: mode }),
  setAiRecommendations: (recs) => set({ aiRecommendations: recs, pendingPatch: recs?.variants[0]?.config_patch || null }),
  
  syncCurrentConfig: () => {
    const labStore = useLabStore.getState();
    set({
      currentConfig: {
        material: labStore.material,
        infill: labStore.infill,
        pattern: labStore.pattern,
        cellSize: labStore.cellSize,
        cellThickness: labStore.cellThickness,
        wallThickness: labStore.wallThickness,
        dimX: labStore.dimX,
        dimY: labStore.dimY,
        dimZ: labStore.dimZ,
        resolution: labStore.resolution,
        layerHeight: labStore.layerHeight,
        printSpeed: labStore.printSpeed
      }
    });
  },

  applyPatch: async (customPatch) => {
    const patch = customPatch || get().pendingPatch;
    if (!patch) return;

    set({ loading: true, error: null });
    try {
      const res = await fetch(`${BACKEND_URL}/api/copilot/apply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch)
      });

      if (!res.ok) throw new Error("Error al aplicar parche en el backend");
      const data = await res.json();

      // Synchronize back to the main lab store
      applyConfigPatch(patch);

      set({
        pendingPatch: null,
        variantHistory: data.history,
        loading: false
      });
      get().syncCurrentConfig();
    } catch (err: any) {
      console.error(err);
      set({ error: err.message || "No se pudo aplicar el parche.", loading: false });
    }
  },

  revertLastPatch: async () => {
    set({ loading: true, error: null });
    try {
      const res = await fetch(`${BACKEND_URL}/api/copilot/revert`, {
        method: "POST"
      });

      if (!res.ok) throw new Error("No hay snapshots para revertir en el backend.");
      const data = await res.json();

      // Sync parameters back to labStore
      applyConfigPatch(data.current_config);

      set({
        pendingPatch: null,
        variantHistory: data.history,
        loading: false
      });
      get().syncCurrentConfig();
    } catch (err: any) {
      console.error(err);
      set({ error: err.message || "Error al revertir la configuración.", loading: false });
    }
  },

  runSimulation: async (variantId) => {
    set({ loading: true, error: null, simulationResults: null });
    try {
      const recs = get().aiRecommendations;
      const variant = recs?.variants.find(v => v.id === variantId);
      if (!variant) throw new Error("Variante no encontrada");

      // Merge current config with variant patch
      get().syncCurrentConfig();
      const mergedConfig = { ...get().currentConfig, ...variant.config_patch };

      // Call predict endpoint on FastAPI
      const res = await fetch(`${BACKEND_URL}/api/copilot/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(mergedConfig)
      });

      if (!res.ok) throw new Error("La simulación falló en el backend.");
      const data = await res.json();

      set({
        simulationResults: {
          stressMpa: data.predicted_max_stress_MPa || 15.0,
          deformationMm: data.predicted_specific_energy_absorption_kJ_kg ? 50.0 / data.predicted_specific_energy_absorption_kJ_kg : 1.5,
          energyAbsorption: data.predicted_energy_density_MJ_m3 || 5.0,
          failureRisk: data.confidence_level === "HIGH" ? "LOW" : "MEDIUM",
          warnings: data.warnings || []
        },
        loading: false
      });
    } catch (err: any) {
      set({ error: err.message, loading: false });
    }
  },

  duplicateVariant: (variant) => {
    // Generate a duplicate config block in clipboard or alert
    const configStr = JSON.stringify(variant.config_patch, null, 2);
    navigator.clipboard.writeText(configStr).then(() => {
      alert(`¡Parámetros de "${variant.name}" copiados al portapapeles!`);
    }).catch(() => {
      alert(`Variante "${variant.name}": infill=${variant.config_patch.infill}%, material=${variant.config_patch.material}`);
    });
  },

  exportVariant: (variant) => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(variant, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `variant_${variant.id}_export.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  },

  fetchHistory: async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/copilot/history`);
      if (res.ok) {
        const history = await res.json();
        set({ variantHistory: history });
      }
    } catch (err) {
      console.error("Failed to fetch history:", err);
    }
  },

  fetchVariants: async () => {
    try {
      const labStore = useLabStore.getState();
      const configPayload = {
        material: labStore.material,
        infill: Number(labStore.infill),
        pattern: labStore.pattern,
        cellSize: Number(labStore.cellSize),
        cellThickness: Number(labStore.cellThickness),
        wallThickness: Number(labStore.wallThickness),
        dimX: Number(labStore.dimX),
        dimY: Number(labStore.dimY),
        dimZ: Number(labStore.dimZ),
        resolution: labStore.resolution,
        layerHeight: Number(labStore.layerHeight),
        printSpeed: Number(labStore.printSpeed)
      };

      const res = await fetch(`${BACKEND_URL}/api/copilot/variants`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(configPayload)
      });
      if (res.ok) {
        const data = await res.json();
        if (data.status === "success" && data.variants) {
          const mappedVariants: VariantData[] = data.variants.map((v: any) => ({
            id: v.id,
            name: v.name,
            description: v.description,
            score: v.scores?.overall || 50,
            compression_score: v.scores?.compression || 50,
            energy_absorption_score: v.scores?.absorption || 50,
            stability_score: v.scores?.stability || 50,
            printability_score: v.scores?.printability || 50,
            risk_level: v.scores?.overall > 75 ? "LOW" : v.scores?.overall > 45 ? "MEDIUM" : "HIGH",
            estimated_print_time: v.config?.material === "TPU" ? "2h 15m" : "1h 45m",
            estimated_mass: v.metrics?.predicted_mass_g ? `${v.metrics.predicted_mass_g.toFixed(1)}g` : "50g",
            pros: v.scores?.overall > 70 ? ["Alta resistencia", "Estructura optimizada"] : ["Diseño ligero"],
            cons: v.scores?.printability < 40 ? ["Dificultad de adherencia"] : [],
            warnings: [],
            config_patch: v.config
          }));
          set({ variants: mappedVariants });
        }
      }
    } catch (err) {
      console.error("Failed to fetch variants:", err);
    }
  }
}));

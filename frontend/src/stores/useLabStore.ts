import { create } from "zustand";

export interface TimeBreakdown {
  walls_min: number;
  infill_min: number;
  travel_min: number;
  top_bottom_min: number;
  firmware_overhead_min: number;
}

export interface MechanicalPredictions {
  yieldStrengthMpa: number;
  maxForceNewtons: number;
  deformationMm: number;
  stiffnessNmm: number;
  energyAbsorptionJoules: number;
  densityRelative: number;
  printingTimeMinutes: number;
  massGrams: number;
  confidenceScore: number;
  modelUsed: string;
  warnings?: Array<{ code: string; severity: string; text: string }>;
  timeBreakdown?: TimeBreakdown;
}

export interface MaterialInfo {
  name: string;
  density: string;
  modulus: string;
  tensileStrength: string;
  printTemp: string;
}

export const MATERIAL_DATA: Record<string, MaterialInfo> = {
  PLA: {
    name: "PLA",
    density: "1.24 g/cm³",
    modulus: "3.2 GPa",
    tensileStrength: "60 MPa",
    printTemp: "195 - 220 °C",
  },
  TPU: {
    name: "TPU",
    density: "1.20 g/cm³",
    modulus: "0.05 GPa",
    tensileStrength: "30 MPa",
    printTemp: "220 - 240 °C",
  },
  ABS: {
    name: "ABS",
    density: "1.04 g/cm³",
    modulus: "2.3 GPa",
    tensileStrength: "40 MPa",
    printTemp: "230 - 250 °C",
  },
  PETG: {
    name: "PETG",
    density: "1.27 g/cm³",
    modulus: "2.1 GPa",
    tensileStrength: "50 MPa",
    printTemp: "220 - 240 °C",
  },
};

interface LabState {
  // 1. Geometry
  dimX: number;
  dimY: number;
  dimZ: number;
  wallThickness: number;
  shellLayers: number;
  edgeRounding: number;
  resolution: string;

  // 2. Material
  material: string;

  // 3. Internal Structure
  pattern: string; // gyroid, honeycomb, triply_periodic, grid
  infill: number;
  cellSize: number;
  cellThickness: number;
  orientation: string;

  // 4. Printing & Slicing Parameters
  layerHeight: number; // in mm
  printSpeed: number; // in mm/s

  // Viewport & UI State
  viewportMode: "solid" | "wireframe" | "transparent" | "heatmap" | "slicer" | "layers" | "shell";
  sliceHeight: number; // in mm, 0 to 50
  loadingMesh: boolean;
  loadingPredictions: boolean;
  appliedForce: number; // in Newtons
  cameraAngle: "perspective" | "top" | "front" | "side";
  isSimulating: boolean;
  error: string | null;
  leftPanelCollapsed: boolean;
  rightPanelCollapsed: boolean;

  // Mesh 3D Data
  meshVertices: number[];
  meshFaces: number[];

  // Dynamic DB Data
  patterns: Record<string, string>;
  materials: Record<string, MaterialInfo>;

  // Mechanical Predictions
  predictions: MechanicalPredictions | null;

  // System & Copilot Health/Models
  systemHealth: any;
  copilotModels: any;

  // --- Manufacturing States ---
  selectedPrinter: string;
  printerProfiles: any[];
  showBuildPlate: boolean;
  gcodePreview: string[];
  slicingSummary: any | null;
  orcaslicerProfile: any | null;
  mfgProcessing: boolean;
  mfgSuccess: boolean;
  mfgValidation: any | null;
  mfgMlSettings: any | null;
  mfgPrinterProfile: any | null;
  mfgReports: any | null;
  triggerAiPostprocess: () => Promise<void>;

  // New dataset & ML states
  activeTab: "editor" | "datasets" | "curves" | "training";
  workspaceFocus: "diseño" | "material" | "simulación" | "resultados" | "fabricación";
  scannedFiles: any[];
  qualityReport: any;
  specimensList: any[];
  mechanicalProperties: any[];
  selectedSpecimen: string;
  selectedSpecimenCurve: any[];
  mlMetrics: any;
  mlFeatureImportance: Record<string, Record<string, number>>;
  isTraining: boolean;
  isImporting: boolean;
  isScanning: boolean;
  optimizationRecommendations: any[];

  // Setters & Actions
  setParam: <K extends keyof LabState>(key: K, value: LabState[K]) => void;
  triggerInference: () => void;
  triggerMeshGeneration: () => void;
  savePreset: () => void;
  loadPreset: () => void;
  resetToDefaults: () => void;
  runDynamicSimulation: () => void;
  fetchDatabaseData: () => Promise<void>;
  loadProjectConfig: (config: any) => void;
  toggleLeftPanel: () => void;
  toggleRightPanel: () => void;
  scanDatasets: () => Promise<void>;
  importDatasets: () => Promise<void>;
  fetchReport: () => Promise<void>;
  fetchSpecimens: () => Promise<void>;
  fetchCurve: (id: string) => Promise<void>;
  fetchProperties: () => Promise<void>;
  retrainModel: () => Promise<void>;
  fetchMlMetrics: () => Promise<void>;
  optimizeConfig: (target: string) => Promise<void>;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const fetchWithRetry = async (url: string, options?: RequestInit, retries = 6, delay = 1000): Promise<Response> => {
  try {
    const res = await fetch(url, options);
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    return res;
  } catch (err) {
    if (retries > 0) {
      await new Promise((resolve) => setTimeout(resolve, delay));
      return fetchWithRetry(url, options, retries - 1, delay * 1.5);
    }
    throw err;
  }
};

let predictionDebounceTimer: NodeJS.Timeout | null = null;
let meshDebounceTimer: NodeJS.Timeout | null = null;

let predictionAbortController: AbortController | null = null;
let meshAbortController: AbortController | null = null;
let simulationInterval: NodeJS.Timeout | null = null;

export const useLabStore = create<LabState>((set, get) => ({
  // Defaults
  dimX: 5.0,
  dimY: 5.0,
  dimZ: 5.0,
  wallThickness: 1.2,
  shellLayers: 2,
  edgeRounding: 0.2,
  resolution: "Alta",

  material: "PLA",

  pattern: "gyroid",
  infill: 35,
  cellSize: 3.0,
  cellThickness: 0.6,
  orientation: "Isotrópica",

  layerHeight: 0.20,
  printSpeed: 50,

  viewportMode: "solid",
  sliceHeight: 25.0,
  loadingMesh: false,
  loadingPredictions: false,
  appliedForce: 0,
  cameraAngle: "perspective",
  isSimulating: false,
  error: null,
  leftPanelCollapsed: false,
  rightPanelCollapsed: false,

  meshVertices: [],
  meshFaces: [],
  predictions: null,

  // New Defaults
  activeTab: "editor",
  workspaceFocus: "diseño",
  scannedFiles: [],
  qualityReport: null,
  specimensList: [],
  mechanicalProperties: [],
  selectedSpecimen: "",
  selectedSpecimenCurve: [],
  mlMetrics: null,
  mlFeatureImportance: {},
  isTraining: false,
  isImporting: false,
  isScanning: false,
  optimizationRecommendations: [],

  patterns: {
    gyroid: "Gyroid",
    honeycomb: "Honeycomb",
    triply_periodic: "Schwarz P"
  },
  materials: MATERIAL_DATA,
  systemHealth: null,
  copilotModels: null,

  // --- Manufacturing States Initializers ---
  selectedPrinter: "Creality K1 Max",
  printerProfiles: [],
  showBuildPlate: false,
  gcodePreview: [],
  slicingSummary: null,
  orcaslicerProfile: null,
  mfgProcessing: false,
  mfgSuccess: false,
  mfgValidation: null,
  mfgMlSettings: null,
  mfgPrinterProfile: null,
  mfgReports: null,

  toggleLeftPanel: () => set((state) => ({ leftPanelCollapsed: !state.leftPanelCollapsed })),
  toggleRightPanel: () => set((state) => ({ rightPanelCollapsed: !state.rightPanelCollapsed })),

  setParam: (key, value) => {
    const prevMode = get().viewportMode;
    set({ [key]: value } as any);

    if (key === "workspaceFocus") {
      const focus = value as string;
      if (focus === "diseño") {
        set({ viewportMode: "solid", leftPanelCollapsed: false, rightPanelCollapsed: false, showBuildPlate: false });
      } else if (focus === "material") {
        set({ viewportMode: "solid", leftPanelCollapsed: false, rightPanelCollapsed: false, showBuildPlate: false });
      } else if (focus === "simulación") {
        set({ viewportMode: "heatmap", leftPanelCollapsed: false, rightPanelCollapsed: false, showBuildPlate: false });
      } else if (focus === "resultados") {
        set({ leftPanelCollapsed: true, rightPanelCollapsed: false });
      } else if (focus === "fabricación") {
        set({ viewportMode: "slicer", leftPanelCollapsed: false, rightPanelCollapsed: false, showBuildPlate: true });
      }
    }

    const postMode = get().viewportMode;

    // If changing physical properties, trigger debounced updates
    const triggerKeys = [
      "dimX", "dimY", "dimZ", "wallThickness", "material",
      "pattern", "infill", "cellSize", "cellThickness", "layerHeight", "printSpeed",
      "resolution", "shellLayers", "edgeRounding", "orientation"
    ];

    if (triggerKeys.includes(key as string)) {
      get().triggerInference();
      get().triggerMeshGeneration();
    }

    // Dynamic mesh regeneration when entering or leaving heatmap (stress simulation)
    if (key === "viewportMode" || (key === "workspaceFocus" && prevMode !== postMode)) {
      const isEnteringOrLeavingHeatmap = (prevMode === "heatmap") !== (postMode === "heatmap");
      if (isEnteringOrLeavingHeatmap) {
        get().triggerMeshGeneration();
      }
    }
  },

  triggerInference: () => {
    if (predictionDebounceTimer) {
      clearTimeout(predictionDebounceTimer);
    }

    set({ loadingPredictions: true, error: null });

    predictionDebounceTimer = setTimeout(async () => {
      // Abort any outstanding predictions request
      if (predictionAbortController) {
        predictionAbortController.abort();
      }
      predictionAbortController = new AbortController();
      const signal = predictionAbortController.signal;

      const state = get();

      // Client-side Validation Bounds to prevent crashes and invalid geometry
      if (
        isNaN(state.dimX) || isNaN(state.dimY) || isNaN(state.dimZ) ||
        isNaN(state.infill) || isNaN(state.wallThickness) || isNaN(state.cellThickness)
      ) {
        set({ error: "Todos los parámetros numéricos deben ser valores válidos.", loadingPredictions: false });
        return;
      }
      if (state.dimX < 1.0 || state.dimX > 15.0 || state.dimY < 1.0 || state.dimY > 15.0 || state.dimZ < 1.0 || state.dimZ > 15.0) {
        set({ error: "Las dimensiones del cubo deben estar entre 1.0 cm y 15.0 cm.", loadingPredictions: false });
        return;
      }
      if (state.infill < 5 || state.infill > 100) {
        set({ error: "La densidad de infill debe estar entre 5% y 100%.", loadingPredictions: false });
        return;
      }
      if (state.wallThickness < 0.4 || state.wallThickness > 10.0) {
        set({ error: "El espesor de la pared debe estar entre 0.4 mm y 10.0 mm.", loadingPredictions: false });
        return;
      }
      if (state.cellThickness < 0.1 || state.cellThickness > 5.0) {
        set({ error: "El grosor de la celda de infill debe estar entre 0.1 mm y 5.0 mm.", loadingPredictions: false });
        return;
      }
      if (state.wallThickness >= (state.dimX * 10) / 2) {
        set({ error: "El espesor de la pared debe ser menor a la mitad del tamaño del cubo.", loadingPredictions: false });
        return;
      }

      const payload = {
        source: "experimental_lab",
        geometry: {
          boundingBoxMm: [state.dimX * 10, state.dimY * 10, state.dimZ * 10],
          volumeMm3: state.dimX * 10 * state.dimY * 10 * state.dimZ * 10,
        },
        material: {
          type: state.material.toLowerCase(),
        },
        slicing: {
          patternType: state.pattern,
          infillPercentage: state.infill,
          shellThicknessMm: state.wallThickness,
          printOrientationDeg: 0.0,
          layerHeightMm: state.layerHeight,
          printSpeedMmS: state.printSpeed,
        },
        printerName: state.selectedPrinter,
      };

      try {
        const res = await fetch(`${BACKEND_URL}/api/predict_structural_load`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal,
        });

        if (res.ok) {
          const data = await res.json();
          // Map response fields to predictions state directly from the physics-based backend
          const predictions: MechanicalPredictions = {
            yieldStrengthMpa: data.mechanical.yieldStrengthMpa,
            maxForceNewtons: data.mechanical.maxForceNewtons,
            deformationMm: data.mechanical.deformationMm,
            stiffnessNmm: data.mechanical.stiffnessNmm,
            energyAbsorptionJoules: data.mechanical.energyAbsorptionJoules,
            densityRelative: state.infill / 100.0,
            printingTimeMinutes: Math.round(data.manufacturing.estimatedTimeSeconds / 60),
            massGrams: Math.round(data.manufacturing.estimatedMassGrams * 10) / 10,
            confidenceScore: data.confidenceScore,
            modelUsed: data.modelUsed,
            warnings: data.manufacturing.warnings,
            timeBreakdown: data.manufacturing.timeBreakdown,
          };

          set({ predictions, loadingPredictions: false, error: null });
        } else {
          const errData = await res.json().catch(() => ({}));
          set({ 
            loadingPredictions: false, 
            error: errData.detail || "Error en el servidor al calcular predicciones mecánicas." 
          });
        }
      } catch (err: any) {
        if (err.name === "AbortError") {
          return; // Ignore aborted requests
        }
        console.error("Error fetching predictions:", err);
        set({ 
          loadingPredictions: false, 
          error: "Error de red al conectar con el servidor de inferencia." 
        });
      }
    }, 300);
  },

  triggerMeshGeneration: () => {
    if (meshDebounceTimer) {
      clearTimeout(meshDebounceTimer);
    }

    set({ loadingMesh: true, error: null });

    meshDebounceTimer = setTimeout(async () => {
      // Abort any outstanding mesh generation request
      if (meshAbortController) {
        meshAbortController.abort();
      }
      meshAbortController = new AbortController();
      const signal = meshAbortController.signal;

      const state = get();

      // Client-side Validation Bounds to prevent crashes and invalid geometry
      if (
        isNaN(state.dimX) || isNaN(state.dimY) || isNaN(state.dimZ) ||
        isNaN(state.infill) || isNaN(state.wallThickness) || isNaN(state.cellThickness)
      ) {
        set({ error: "Todos los parámetros numéricos deben ser valores válidos.", loadingMesh: false });
        return;
      }
      if (state.dimX < 1.0 || state.dimX > 15.0 || state.dimY < 1.0 || state.dimY > 15.0 || state.dimZ < 1.0 || state.dimZ > 15.0) {
        set({ error: "Las dimensiones del cubo deben estar entre 1.0 cm y 15.0 cm.", loadingMesh: false });
        return;
      }
      if (state.infill < 5 || state.infill > 100) {
        set({ error: "La densidad de infill debe estar entre 5% y 100%.", loadingMesh: false });
        return;
      }
      if (state.wallThickness < 0.4 || state.wallThickness > 10.0) {
        set({ error: "El espesor de la pared debe estar entre 0.4 mm y 10.0 mm.", loadingMesh: false });
        return;
      }
      if (state.cellThickness < 0.1 || state.cellThickness > 5.0) {
        set({ error: "El grosor de la celda de infill debe estar entre 0.1 mm y 5.0 mm.", loadingMesh: false });
        return;
      }
      if (state.wallThickness >= (state.dimX * 10) / 2) {
        set({ error: "El espesor de la pared debe ser menor a la mitad del tamaño del cubo.", loadingMesh: false });
        return;
      }

      const payload = {
        pattern: state.pattern,
        infillDensity: state.infill,
        wallThickness: state.wallThickness,
        infillThickness: state.cellThickness,
        material: state.material.toLowerCase(),
        size: state.dimX * 10.0, // convert cm to mm
        showShell: state.viewportMode !== "heatmap",
        cellSize: state.cellSize,
        orientation: state.orientation,
        resolution: state.resolution,
      };

      try {
        const res = await fetch(`${BACKEND_URL}/api/generate_mesh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal,
        });

        if (res.ok) {
          const data = await res.json();
          set({
            meshVertices: data.vertices,
            meshFaces: data.faces,
            loadingMesh: false,
            error: null,
          });
        } else {
          const errData = await res.json().catch(() => ({}));
          set({ 
            loadingMesh: false, 
            error: errData.detail || "Error en el servidor al compilar la geometría 3D." 
          });
        }
      } catch (err: any) {
        if (err.name === "AbortError") {
          return; // Ignore aborted requests
        }
        console.error("Error fetching 3D mesh:", err);
        set({ 
          loadingMesh: false, 
          error: "Error de red al conectar con el servidor de geometría." 
        });
      }
    }, 400);
  },

  savePreset: () => {
    const state = get();
    const config = {
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
    };
    localStorage.setItem("MaterialForge_Snapshot", JSON.stringify(config));
  },

  loadPreset: () => {
    try {
      const stored = localStorage.getItem("MaterialForge_Snapshot");
      if (stored) {
        const config = JSON.parse(stored);
        set(config);
        get().triggerInference();
        get().triggerMeshGeneration();
      } else {
        alert("No hay ningún diseño guardado en la memoria local.");
      }
    } catch (e) {
      console.error(e);
    }
  },

  resetToDefaults: () => {
    // Clear any active simulation interval to prevent memory leaks and state thrashing
    if (simulationInterval) {
      clearInterval(simulationInterval);
      simulationInterval = null;
    }
    set({
      dimX: 5.0,
      dimY: 5.0,
      dimZ: 5.0,
      wallThickness: 1.2,
      shellLayers: 2,
      edgeRounding: 0.2,
      resolution: "Alta",
      material: "PLA",
      pattern: "gyroid",
      infill: 35,
      cellSize: 3.0,
      cellThickness: 0.6,
      orientation: "Isotrópica",
      layerHeight: 0.20,
      printSpeed: 50,
      appliedForce: 0,
      cameraAngle: "perspective",
      isSimulating: false,
      error: null,
    });
    get().triggerInference();
    get().triggerMeshGeneration();
  },

  runDynamicSimulation: () => {
    if (get().isSimulating) return;
    if (simulationInterval) {
      clearInterval(simulationInterval);
    }
    set({ isSimulating: true, appliedForce: 0 });

    let currentForce = 0;
    simulationInterval = setInterval(() => {
      currentForce += 20;
      if (currentForce > 1000) {
        if (simulationInterval) {
          clearInterval(simulationInterval);
          simulationInterval = null;
        }
        set({ isSimulating: false });
      } else {
        set({ appliedForce: currentForce });
      }
    }, 40);
  },

  fetchDatabaseData: async () => {
    try {
      const resPatterns = await fetchWithRetry(`${BACKEND_URL}/api/patterns`);
      const patterns = await resPatterns.json();
      set({ patterns });

      const resMaterials = await fetchWithRetry(`${BACKEND_URL}/api/materials`);
      const rawMaterials = await resMaterials.json();
      const materials: Record<string, MaterialInfo> = {};
      for (const key of Object.keys(rawMaterials)) {
        materials[key] = {
          name: rawMaterials[key].name,
          density: rawMaterials[key].density,
          modulus: rawMaterials[key].modulus,
          tensileStrength: rawMaterials[key].tensileStrength,
          printTemp: rawMaterials[key].printTemp,
        };
      }
      set({ materials });

      // Fetch system health
      const resHealth = await fetchWithRetry(`${BACKEND_URL}/api/system/health`);
      const systemHealth = await resHealth.json();
      set({ systemHealth });

      // Fetch copilot models
      const resModels = await fetchWithRetry(`${BACKEND_URL}/api/copilot/models`);
      const copilotModels = await resModels.json();
      set({ copilotModels });

      // Fetch printer profiles
      try {
        const resPrinters = await fetchWithRetry(`${BACKEND_URL}/api/copilot/printers`);
        if (resPrinters.ok) {
          const printerProfiles = await resPrinters.json();
          set({ printerProfiles });
        }
      } catch (err) {
        console.warn("Failed to fetch printer profiles:", err);
      }
    } catch (e) {
      console.error("Failed to fetch database/health/models data after retries:", e);
    }
  },

  scanDatasets: async () => {
    set({ isScanning: true, error: null });
    try {
      const res = await fetch(`${BACKEND_URL}/api/datasets/scan`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        set({ scannedFiles: data.files, isScanning: false });
      } else {
        set({ isScanning: false, error: "Error al escanear los datasets." });
      }
    } catch (e) {
      set({ isScanning: false, error: "Error de red al conectar con el servidor." });
    }
  },

  importDatasets: async () => {
    set({ isImporting: true, error: null });
    try {
      const res = await fetch(`${BACKEND_URL}/api/datasets/import`, { method: "POST" });
      if (res.ok) {
        set({ isImporting: false });
        get().scanDatasets();
        get().fetchReport();
        get().fetchSpecimens();
        get().fetchProperties();
      } else {
        set({ isImporting: false, error: "Error al importar los datasets." });
      }
    } catch (e) {
      set({ isImporting: false, error: "Error de red al importar los datasets." });
    }
  },

  fetchReport: async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/datasets/report`);
      if (res.ok) {
        const data = await res.json();
        set({ qualityReport: data });
      }
    } catch (e) {
      console.error(e);
    }
  },

  fetchSpecimens: async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/mechanical/specimens`);
      if (res.ok) {
        const data = await res.json();
        set({ specimensList: data });
      }
    } catch (e) {
      console.error(e);
    }
  },

  fetchCurve: async (id: string) => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/mechanical/specimens/${id}/curve`);
      if (res.ok) {
        const data = await res.json();
        set({ selectedSpecimen: id, selectedSpecimenCurve: data });
      }
    } catch (e) {
      console.error(e);
    }
  },

  fetchProperties: async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/mechanical/properties`);
      if (res.ok) {
        const data = await res.json();
        set({ mechanicalProperties: data });
      }
    } catch (e) {
      console.error(e);
    }
  },

  retrainModel: async () => {
    set({ isTraining: true, error: null });
    try {
      const res = await fetch(`${BACKEND_URL}/api/ml/retrain`, { method: "POST" });
      if (res.ok) {
        set({ isTraining: false });
        get().fetchMlMetrics();
      } else {
        set({ isTraining: false, error: "Error al reentrenar el modelo." });
      }
    } catch (e) {
      set({ isTraining: false, error: "Error de red al reentrenar el modelo." });
    }
  },

  fetchMlMetrics: async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/ml/metrics`);
      if (res.ok) {
        const data = await res.json();
        set({ 
          mlMetrics: data.registry, 
          mlFeatureImportance: data.feature_importance 
        });
      }
    } catch (e) {
      console.error(e);
    }
  },

  optimizeConfig: async (target: string) => {
    try {
      const payload = { target, material: get().material, test_type: "compression" };
      const res = await fetch(`${BACKEND_URL}/api/ml/optimize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        set({ optimizationRecommendations: data.recommendations });
      }
    } catch (e) {
      console.error(e);
    }
  },

  loadProjectConfig: (config) => {
    if (!config || typeof config !== "object") return;
    
    // Clear simulation
    if (simulationInterval) {
      clearInterval(simulationInterval);
      simulationInterval = null;
    }

    const newParams: Partial<LabState> = {};
    
    // Extract parameters
    const params = config.parameters || config;
    const allowedKeys = [
      "dimX", "dimY", "dimZ", "wallThickness", "shellLayers", "edgeRounding",
      "resolution", "material", "pattern", "infill", "cellSize", "cellThickness",
      "orientation", "layerHeight", "printSpeed"
    ];
    
    for (const key of allowedKeys) {
      if (key in params) {
        (newParams as any)[key] = params[key];
      }
    }

    // Extract viewport
    if (config.viewport) {
      const allowedViewport = ["viewportMode", "cameraAngle", "sliceHeight", "appliedForce"];
      for (const key of allowedViewport) {
        if (key in config.viewport) {
          (newParams as any)[key] = config.viewport[key];
        }
      }
    }

    set(newParams as any);

    // Refresh geometry & simulation predictions
    get().triggerInference();
    get().triggerMeshGeneration();
  },

  triggerAiPostprocess: async () => {
    set({ mfgProcessing: true, mfgSuccess: false, error: null });
    const state = get();
    const payload = {
      pattern: state.pattern,
      infillDensity: Number(state.infill),
      wallThickness: Number(state.wallThickness),
      infillThickness: Number(state.cellThickness),
      material: state.material.toLowerCase(),
      size: Number(state.dimX) * 10.0,
      showShell: state.viewportMode !== "heatmap",
      cellSize: Number(state.cellSize),
      orientation: state.orientation,
      resolution: state.resolution,
      printerName: state.selectedPrinter,
    };
    try {
      const res = await fetch(`${BACKEND_URL}/api/manufacturing/postprocess`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        set({
          mfgValidation: data.validation,
          mfgMlSettings: data.ml_settings,
          mfgPrinterProfile: data.printer_profile,
          mfgReports: data.reports,
          mfgSuccess: true,
          mfgProcessing: false
        });
      } else {
        const errData = await res.json().catch(() => ({}));
        set({
          mfgProcessing: false,
          error: errData.detail || "Fallo en el servidor al ejecutar el postprocesamiento de IA."
        });
      }
    } catch (err: any) {
      console.error(err);
      set({
        mfgProcessing: false,
        error: "Error de red al conectar con el servicio de postprocesamiento."
      });
    }
  },
}));

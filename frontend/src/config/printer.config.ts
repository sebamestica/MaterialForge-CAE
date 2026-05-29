export interface PrinterProfile {
  name: string;
  buildVolume: { x: number; y: number; z: number };
  nozzleDiameters: number[];
  maxAcceleration: number; // mm/s^2
  tpuCompatible: boolean;
  extruderType: 'direct_drive' | 'bowden';
  maxVolumetricFlow: number; // mm^3/s
  bedTempLimit: number;
  hotendTempLimit: number;
}

export const printerConfig: Record<string, PrinterProfile> = {
  "Creality K1 Max": {
    name: "Creality K1 Max",
    buildVolume: { x: 300.0, y: 300.0, z: 300.0 },
    nozzleDiameters: [0.4, 0.6, 0.8],
    maxAcceleration: 20000.0,
    tpuCompatible: true,
    extruderType: "direct_drive",
    maxVolumetricFlow: 32.0,
    bedTempLimit: 120.0,
    hotendTempLimit: 300.0
  },
  "Ender 3 V3 KE": {
    name: "Ender 3 V3 KE",
    buildVolume: { x: 220.0, y: 220.0, z: 240.0 },
    nozzleDiameters: [0.4, 0.6],
    maxAcceleration: 8000.0,
    tpuCompatible: true,
    extruderType: "direct_drive",
    maxVolumetricFlow: 24.0,
    bedTempLimit: 100.0,
    hotendTempLimit: 300.0
  },
  "Creality K1C": {
    name: "Creality K1C",
    buildVolume: { x: 220.0, y: 220.0, z: 250.0 },
    nozzleDiameters: [0.4, 0.6],
    maxAcceleration: 20000.0,
    tpuCompatible: true,
    extruderType: "direct_drive",
    maxVolumetricFlow: 32.0,
    bedTempLimit: 100.0,
    hotendTempLimit: 300.0
  },
  "Creality CR Series": {
    name: "Creality CR Series",
    buildVolume: { x: 300.0, y: 300.0, z: 400.0 },
    nozzleDiameters: [0.4, 0.6, 0.8],
    maxAcceleration: 2500.0,
    tpuCompatible: false,
    extruderType: "bowden",
    maxVolumetricFlow: 15.0,
    bedTempLimit: 100.0,
    hotendTempLimit: 260.0
  }
};

export const defaultPrinterName = "Creality K1 Max";

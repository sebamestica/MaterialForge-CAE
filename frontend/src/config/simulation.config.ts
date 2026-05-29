export interface MaterialMechanicalProperties {
  name: string;
  density: string;
  modulus: string;
  tensileStrength: string;
  printTemp: string;
}

export const simulationConfig = {
  // Hardcoded engineering constants for fallback predictions
  materials: {
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
      printTemp: "220 - 245 °C",
    }
  } as Record<string, MaterialMechanicalProperties>,

  // Mechanical load tests configuration
  loads: {
    minForceNewtons: 0,
    maxForceNewtons: 1000,
    stepNewtons: 10,
    loadingSpeedMmMin: 1.5,
  }
};

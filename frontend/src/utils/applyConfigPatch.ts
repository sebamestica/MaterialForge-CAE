import { useLabStore } from "../stores/useLabStore";
import { ConfigPatch } from "../stores/designStore";

/**
 * Validates, parses, and applies a configuration patch to the active 3D CAD workspace.
 * Automatically triggers 3D geometry rebuilds and structural simulations.
 */
export function applyConfigPatch(patch: ConfigPatch): boolean {
  if (!patch) return false;
  
  try {
    const labStore = useLabStore.getState();
    const numberParams = [
      "infill",
      "cellSize",
      "cellThickness",
      "wallThickness",
      "dimX",
      "dimY",
      "dimZ",
      "layerHeight",
      "printSpeed"
    ];

    Object.entries(patch).forEach(([key, value]) => {
      if (value === undefined || value === null) return;

      let finalValue = value;
      if (key === "pattern" && typeof value === "string") {
        let cleanVal = value.toLowerCase().trim();
        if (cleanVal.endsWith("_tpms")) {
          cleanVal = cleanVal.slice(0, -5);
        }
        finalValue = cleanVal;
      }

      if (numberParams.includes(key)) {
        const numVal = Number(finalValue);
        if (!isNaN(numVal)) {
          labStore.setParam(key as any, numVal);
        }
      } else {
        labStore.setParam(key as any, finalValue);
      }
    });

    return true;
  } catch (err) {
    console.error("Failed to apply configuration patch:", err);
    return false;
  }
}

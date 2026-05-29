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

      if (numberParams.includes(key)) {
        const numVal = Number(value);
        if (!isNaN(numVal)) {
          labStore.setParam(key as any, numVal);
        }
      } else {
        labStore.setParam(key as any, value);
      }
    });

    return true;
  } catch (err) {
    console.error("Failed to apply configuration patch:", err);
    return false;
  }
}

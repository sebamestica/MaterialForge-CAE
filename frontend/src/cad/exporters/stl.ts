/**
 * Sends structural properties to the FastAPI backend STL endpoint,
 * downloads the resulting watertight binary STL file, and triggers client download.
 */
export async function exportStl(params: {
  pattern: string;
  infill: number;
  wallThickness: number;
  cellThickness: number;
  material: string;
  dimX: number;
}) {
  const payload = {
    pattern: params.pattern,
    infillDensity: params.infill,
    wallThickness: params.wallThickness,
    infillThickness: params.cellThickness,
    material: params.material.toLowerCase(),
    size: params.dimX * 10.0,
    showShell: true,
  };

  const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  const res = await fetch(`${BACKEND_URL}/api/generate_stl`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error("Error al generar la geometría STL en el servidor.");
  }

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `cubo_${params.material.toLowerCase()}_${params.pattern}_${params.infill}pct.stl`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

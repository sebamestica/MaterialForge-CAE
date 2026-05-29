/**
 * Generates dynamic machine toolpath configuration paths based on selected parameters,
 * formats layers, includes safety setups, and triggers client file download.
 */
export function generateGcodeString(params: {
  material: string;
  pattern: string;
  infill: number;
  wallThickness: number;
  dimX: number;
  dimY: number;
  dimZ: number;
  layerHeight: number;
  printSpeed: number;
}): string {
  const mat = params.material.toUpperCase();
  let temp = 210;
  let bedTemp = 60;
  if (mat.includes("PLA")) {
    temp = 210;
    bedTemp = 60;
  } else if (mat.includes("TPU")) {
    temp = 230;
    bedTemp = 50;
  } else if (mat.includes("ABS")) {
    temp = 250;
    bedTemp = 100;
  } else if (mat.includes("PETG")) {
    temp = 240;
    bedTemp = 70;
  }

  const gcodeLines = [
    `; MaterialForge G-code Generator v2.0`,
    `; Generated: ${new Date().toISOString()}`,
    `; Design: Cubo_Resistencia_v7`,
    `; Material: ${mat} (Hotend: ${temp}C, Bed: ${bedTemp}C)`,
    `; Dimensions: ${(params.dimX * 10).toFixed(1)} x ${(params.dimY * 10).toFixed(1)} x ${(params.dimZ * 10).toFixed(1)} mm`,
    `; Wall Thickness: ${params.wallThickness.toFixed(2)} mm`,
    `; Infill: ${params.infill}% (${params.pattern})`,
    `; Layer Height: ${params.layerHeight.toFixed(2)} mm`,
    `; Print Speed: ${params.printSpeed} mm/s`,
    `;`,
    `M140 S${bedTemp} ; Set bed temp`,
    `M104 S${temp} ; Set extruder temp`,
    `M190 S${bedTemp} ; Wait for bed temp`,
    `M109 S${temp} ; Wait for extruder temp`,
    `G90 ; use absolute coordinates`,
    `M83 ; extruder relative mode`,
    `G28 ; home all axes`,
    `G29 ; mesh bed leveling`,
    `G1 Z2.0 F3000 ; lift nozzle`,
    `G92 E0 ; reset extruder`
  ];

  const lh = params.layerHeight;
  const size = params.dimX * 10;
  const numLayers = Math.max(1, Math.floor(size / lh));
  const layersToGen = Math.min(150, numLayers);
  const infillRatio = params.infill / 100;
  const feedRate = params.printSpeed * 60;
  const wallT = params.wallThickness;

  for (let layer = 0; layer < layersToGen; layer++) {
    const z = (layer + 1) * lh;
    gcodeLines.push(`\n; --- LAYER ${layer + 1} (Z = ${z.toFixed(2)} mm) ---`);
    gcodeLines.push(`G1 F${feedRate.toFixed(0)} ; Set feedrate`);
    gcodeLines.push(`G1 Z${z.toFixed(2)} ; Z travel`);
    gcodeLines.push(`G1 X0 Y0 F6000 ; Travel to start`);

    // Outer Perimeter
    const ePerim = size * lh * 0.45 * 0.06;
    gcodeLines.push(`G1 X${size.toFixed(2)} Y0.00 E${ePerim.toFixed(4)}`);
    gcodeLines.push(`G1 X${size.toFixed(2)} Y${size.toFixed(2)} E${ePerim.toFixed(4)}`);
    gcodeLines.push(`G1 X0.00 Y${size.toFixed(2)} E${ePerim.toFixed(4)}`);
    gcodeLines.push(`G1 X0.00 Y0.00 E${ePerim.toFixed(4)}`);
    gcodeLines.push(`G1 E-1.0000 F1800 ; Retract`);

    // Infill Paths
    const infStart = wallT;
    const infEnd = size - wallT;
    if (infEnd > infStart) {
      gcodeLines.push(`; Lattice Infill Path (${params.pattern})`);
      if (params.pattern === "grid") {
        const spacing = Math.max(4.0, 20.0 * (1.0 - infillRatio));
        for (let xVal = infStart + spacing / 2; xVal < infEnd; xVal += spacing) {
          gcodeLines.push(`G1 X${xVal.toFixed(2)} Y${infStart.toFixed(2)} F6000 ; Travel`);
          gcodeLines.push(`G1 E1.0000 F1800 ; Prime`);
          const lenInf = infEnd - infStart;
          const eInf = lenInf * lh * 0.45 * 0.06;
          gcodeLines.push(`G1 X${xVal.toFixed(2)} Y${infEnd.toFixed(2)} E${eInf.toFixed(4)} F${feedRate.toFixed(0)}`);
          gcodeLines.push(`G1 E-1.0000 F1800 ; Retract`);
        }
        for (let yVal = infStart + spacing / 2; yVal < infEnd; yVal += spacing) {
          gcodeLines.push(`G1 X${infStart.toFixed(2)} Y${yVal.toFixed(2)} F6000 ; Travel`);
          gcodeLines.push(`G1 E1.0000 F1800 ; Prime`);
          const lenInf = infEnd - infStart;
          const eInf = lenInf * lh * 0.45 * 0.06;
          gcodeLines.push(`G1 X${infEnd.toFixed(2)} Y${yVal.toFixed(2)} E${eInf.toFixed(4)} F${feedRate.toFixed(0)}`);
          gcodeLines.push(`G1 E-1.0000 F1800 ; Retract`);
        }
      } else if (params.pattern === "gyroid" || params.pattern === "triply_periodic") {
        const spacing = Math.max(5.0, 25.0 * (1.0 - infillRatio));
        for (let xVal = infStart + spacing / 2; xVal < infEnd; xVal += spacing) {
          const steps = 15;
          const a = spacing * 0.3;
          const freq = (2 * Math.PI) / spacing;
          
          const x0 = xVal + a * Math.sin(infStart * freq);
          gcodeLines.push(`G1 X${x0.toFixed(2)} Y${infStart.toFixed(2)} F6000 ; Travel`);
          gcodeLines.push(`G1 E1.0000 F1800 ; Prime`);

          let prevX = x0;
          for (let s = 1; s <= steps; s++) {
            const nextY = infStart + (infEnd - infStart) * (s / steps);
            const nextX = xVal + a * Math.sin(nextY * freq);
            const dist = Math.sqrt(Math.pow(nextX - prevX, 2) + Math.pow(nextY - (infStart + (infEnd - infStart) * ((s - 1) / steps)), 2));
            const eStep = dist * lh * 0.45 * 0.06;
            gcodeLines.push(`G1 X${nextX.toFixed(2)} Y${nextY.toFixed(2)} E${eStep.toFixed(4)} F${(feedRate * 0.8).toFixed(0)}`);
            prevX = nextX;
          }
          gcodeLines.push(`G1 E-1.0000 F1800 ; Retract`);
        }
      } else { // honeycomb
        const spacing = Math.max(6.0, 30.0 * (1.0 - infillRatio));
        for (let xVal = infStart + spacing / 2; xVal < infEnd; xVal += spacing) {
          const ySteps: number[] = [];
          for (let y = infStart; y < infEnd; y += spacing) {
            ySteps.push(y);
          }
          if (ySteps.length > 1) {
            gcodeLines.push(`G1 X${xVal.toFixed(2)} Y${ySteps[0].toFixed(2)} F6000 ; Travel`);
            gcodeLines.push(`G1 E1.0000 F1800 ; Prime`);
            for (let idx = 1; idx < ySteps.length; idx++) {
              const nextY = ySteps[idx];
              const offset_x = idx % 2 === 1 ? spacing * 0.25 : -spacing * 0.25;
              const nextX = xVal + offset_x;
              const dist = Math.sqrt(Math.pow(nextX - xVal, 2) + Math.pow(nextY - ySteps[idx - 1], 2));
              const eStep = dist * lh * 0.45 * 0.06;
              gcodeLines.push(`G1 X${nextX.toFixed(2)} Y${nextY.toFixed(2)} E${eStep.toFixed(4)} F${(feedRate * 0.8).toFixed(0)}`);
            }
            gcodeLines.push(`G1 E-1.0000 F1800 ; Retract`);
          }
        }
      }
    }
  }

  gcodeLines.push(`\n; --- END GCODE (Safe teardown) ---`);
  gcodeLines.push(`G91 ; Relative positioning`);
  gcodeLines.push(`G1 Z5.00 F3000 ; Lift nozzle by 5mm`);
  gcodeLines.push(`G90 ; Absolute positioning`);
  gcodeLines.push(`G1 X0.00 Y220.00 F6000 ; Present finished print`);
  gcodeLines.push(`M104 S0 ; Turn off hotend heater`);
  gcodeLines.push(`M140 S0 ; Turn off bed heater`);
  gcodeLines.push(`M107 ; Turn off cooling fan`);
  gcodeLines.push(`M84 ; Disable all stepper motors`);

  return gcodeLines.join("\n") + "\n";
}

export function exportGcode(params: {
  material: string;
  pattern: string;
  infill: number;
  wallThickness: number;
  dimX: number;
  dimY: number;
  dimZ: number;
  layerHeight: number;
  printSpeed: number;
}) {
  const gcodeContent = generateGcodeString(params);
  const blob = new Blob([gcodeContent], { type: "text/plain;charset=utf-8" });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `cubo_${params.material.toLowerCase()}_${params.pattern}_${params.infill}pct.gcode`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

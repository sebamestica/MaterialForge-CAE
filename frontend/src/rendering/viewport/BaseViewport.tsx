"use client";

import React, { useMemo, useEffect, useRef } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { OrbitControls, Html } from "@react-three/drei";
import * as THREE from "three";
import { useLabStore } from "@/stores/useLabStore";
import { useShallow } from "zustand/react/shallow";
import { Box, Layers, Activity, RotateCcw, Compass, Eye, Video } from "lucide-react";

// Component to enable local clipping on the WebGLRenderer
function ClippingEnabler() {
  const { gl } = useThree();
  useEffect(() => {
    gl.localClippingEnabled = true;
  }, [gl]);
  return null;
}

// Controller to position camera based on Right Panel buttons
function CameraController() {
  const { camera } = useThree();
  const cameraAngle = useLabStore((state) => state.cameraAngle);

  useEffect(() => {
    if (cameraAngle === "perspective") {
      camera.position.set(60, 60, 80);
    } else if (cameraAngle === "top") {
      camera.position.set(0, 110, 0);
    } else if (cameraAngle === "front") {
      camera.position.set(0, 0, 110);
    } else if (cameraAngle === "side") {
      camera.position.set(110, 0, 0);
    }
    camera.lookAt(0, 0, 0);
  }, [cameraAngle, camera]);

  return null;
}

// Coordinate axes and bounding box dimension lines
interface DimensionLinesProps {
  size: number; // in mm
}

function DimensionLines({ size }: DimensionLinesProps) {
  const sizeCm = (size / 10).toFixed(2);
  const half = size / 2;

  // Memoize geometry coordinate buffers to prevent inline reallocation in the rendering loop
  const xPositions = useMemo(() => new Float32Array([-half, -half - 5, half + 5, half, -half - 5, half + 5]), [half]);
  const zPositions = useMemo(() => new Float32Array([-half - 5, -half - 5, -half, -half - 5, -half - 5, half]), [half]);
  const yPositions = useMemo(() => new Float32Array([-half - 5, -half, half + 5, -half - 5, half, half + 5]), [half]);

  return (
    <group>
      {/* Outer Bounding Box (Wireframe guide) */}
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[size + 1, size + 1, size + 1]} />
        <meshBasicMaterial
          color="#94a3b8"
          wireframe
          transparent
          opacity={0.3}
        />
      </mesh>

      {/* Axis Guide Lines */}
      {/* X Line (Width, Red) */}
      <line>
        <bufferGeometry attach="geometry">
          <float32BufferAttribute
            attach="attributes-position"
            args={[xPositions, 3]}
          />
        </bufferGeometry>
        <lineBasicMaterial color="#ef4444" linewidth={1} />
      </line>
      <Html
        position={[0, -half - 12, half + 5]}
        center
        className="pointer-events-none select-none font-mono text-xs font-black text-[#ef4444] bg-white/95 border border-slate-200 px-2 py-0.5 rounded shadow-2xs"
      >
        {`${sizeCm} cm`}
      </Html>

      {/* Z Line (Depth, Blue) */}
      <line>
        <bufferGeometry attach="geometry">
          <float32BufferAttribute
            attach="attributes-position"
            args={[zPositions, 3]}
          />
        </bufferGeometry>
        <lineBasicMaterial color="#3b82f6" linewidth={1} />
      </line>
      <Html
        position={[-half - 5, -half - 12, 0]}
        center
        className="pointer-events-none select-none font-mono text-xs font-black text-[#3b82f6] bg-white/95 border border-slate-200 px-2 py-0.5 rounded shadow-2xs"
      >
        {`${sizeCm} cm`}
      </Html>

      {/* Y Line (Height, Green) */}
      <line>
        <bufferGeometry attach="geometry">
          <float32BufferAttribute
            attach="attributes-position"
            args={[yPositions, 3]}
          />
        </bufferGeometry>
        <lineBasicMaterial color="#22c55e" linewidth={1} />
      </line>
      <Html
        position={[-half - 12, 0, half + 5]}
        center
        className="pointer-events-none select-none font-mono text-xs font-black text-[#22c55e] bg-white/95 border border-slate-200 px-2 py-0.5 rounded shadow-2xs"
      >
        {`${sizeCm} cm`}
      </Html>
    </group>
  );
}

// Fast inline HSL to RGB conversion helper for s=1.0, l=0.5
function fastHslToRgb(h: number): [number, number, number] {
  const x = 1 - Math.abs(((h / 60) % 2) - 1);
  if (h < 60) return [1, x, 0];
  if (h < 120) return [x, 1, 0];
  if (h < 180) return [0, 1, x];
  if (h < 240) return [0, x, 1];
  return [0, 0, 1];
}

// Custom mesh renderer connecting vertices and faces
interface LatticeMeshProps {
  vertices: number[];
  faces: number[];
  mode: "solid" | "wireframe" | "transparent" | "heatmap" | "slicer" | "layers" | "shell";
  material: string;
  size: number;
  sliceHeight: number;
}

function LatticeMesh({ vertices, faces, mode, material, size, sliceHeight }: LatticeMeshProps) {
  const appliedForce = useLabStore((state) => state.appliedForce);
  const predictions = useLabStore((state) => state.predictions);
  const infill = useLabStore((state) => state.infill);
  const pattern = useLabStore((state) => state.pattern);
  const cellSize = useLabStore((state) => state.cellSize);
  const orientation = useLabStore((state) => state.orientation);

  const geomRef = useRef<THREE.BufferGeometry | null>(null);
  const baseStressCacheRef = useRef<Float32Array | null>(null);

  // 1. Compile static geometry (position & index only) and manage manual GPU buffer disposal
  const geometry = useMemo(() => {
    const geom = new THREE.BufferGeometry();
    if (vertices.length === 0 || faces.length === 0) return geom;

    const verticesFloat32 = new Float32Array(vertices);
    const indicesUint32 = new Uint32Array(faces);

    geom.setAttribute("position", new THREE.BufferAttribute(verticesFloat32, 3));
    geom.setIndex(new THREE.BufferAttribute(indicesUint32, 1));

    // Initialize custom color attribute buffer
    const colorsFloat32 = new Float32Array(vertices.length);
    geom.setAttribute("color", new THREE.BufferAttribute(colorsFloat32, 3));

    geom.computeVertexNormals();

    // Clean up previous geometry to prevent VRAM memory leak
    if (geomRef.current) {
      geomRef.current.dispose();
    }
    geomRef.current = geom;

    return geom;
  }, [vertices, faces, size]);

  const meshRef = useRef<THREE.Mesh | null>(null);
  const prevMaterialRef = useRef<THREE.Material | THREE.Material[] | null>(null);

  // Clean up materials when they change to prevent VRAM memory leak
  useEffect(() => {
    if (meshRef.current) {
      const currentMat = meshRef.current.material;
      if (prevMaterialRef.current && prevMaterialRef.current !== currentMat) {
        if (Array.isArray(prevMaterialRef.current)) {
          prevMaterialRef.current.forEach((m) => m.dispose());
        } else {
          prevMaterialRef.current.dispose();
        }
      }
      prevMaterialRef.current = currentMat;
    }
  }, [mode, material]);

  // Clean up geometry and materials on unmount
  useEffect(() => {
    return () => {
      if (geomRef.current) {
        geomRef.current.dispose();
        geomRef.current = null;
      }
      if (prevMaterialRef.current) {
        if (Array.isArray(prevMaterialRef.current)) {
          prevMaterialRef.current.forEach((m) => m.dispose());
        } else {
          prevMaterialRef.current.dispose();
        }
        prevMaterialRef.current = null;
      }
    };
  }, []);

  // Precompute base stress values whenever geometry or structural settings change
  useEffect(() => {
    if (vertices.length === 0) {
      baseStressCacheRef.current = null;
      return;
    }

    const numVerts = vertices.length / 3;
    const cache = new Float32Array(numVerts);
    const maxVal = size || 1.0;
    const isTPU = material.toUpperCase() === "TPU";
    const cell = cellSize || 8.0;
    const k = (2 * Math.PI * size) / cell;
    let kx = k;
    let ky = k;
    let kz = k;
    if (orientation === "Anisotrópica X") {
      kx = k * 0.5;
    } else if (orientation === "Anisotrópica Y") {
      ky = k * 0.5;
    } else if (orientation === "Anisotrópica Z") {
      kz = k * 0.5;
    }

    const shearWidth = isTPU ? 0.15 : 0.05;
    const shearFactor = isTPU ? 0.35 : 0.55;
    const contactFactor = isTPU ? 0.25 : 0.45;
    const bucklingFactor = isTPU ? 0.40 : 0.15;

    for (let i = 0; i < numVerts; i++) {
      const x = vertices[i * 3];
      const y = vertices[i * 3 + 1];
      const z = vertices[i * 3 + 2];

      const normY = y / maxVal;
      const normX = x / maxVal;
      const normZ = z / maxVal;

      const shearX = Math.exp(-Math.pow(Math.abs(normX - normY) - 0.1, 2) / shearWidth) +
                     Math.exp(-Math.pow(Math.abs((1.0 - normX) - normY) - 0.1, 2) / shearWidth);
      const shearZ = Math.exp(-Math.pow(Math.abs(normZ - normY) - 0.1, 2) / shearWidth) +
                     Math.exp(-Math.pow(Math.abs((1.0 - normZ) - normY) - 0.1, 2) / shearWidth);
      const shearBands = shearFactor * ((shearX + shearZ) / 2.0);

      const contactStress = contactFactor * (Math.exp(-normY / 0.12) + Math.exp(-(1.0 - normY) / 0.12));

      const bucklingStress = bucklingFactor * Math.sin(normY * Math.PI) * Math.sin(normX * Math.PI) * Math.sin(normZ * Math.PI);

      let localStrut = 0;
      if (pattern === "gyroid") {
        const valX = normX * kx;
        const valY = normY * ky;
        const valZ = normZ * kz;
        localStrut = 0.15 * Math.max(0, Math.cos(valX) * Math.cos(valY) * Math.cos(valZ));
      } else if (pattern === "honeycomb") {
        const k_hex = (2 * Math.PI * size) / (cell * 1.5);
        const kx_hex = orientation === "Anisotrópica X" ? k_hex * 0.5 : k_hex;
        const ky_hex = orientation === "Anisotrópica Y" ? k_hex * 0.5 : k_hex;
        localStrut = 0.15 * Math.max(0, Math.cos(kx_hex * normX) * Math.cos(ky_hex * normY));
      } else if (pattern === "triply_periodic") {
        const valX = normX * kx;
        const valY = normY * ky;
        const valZ = normZ * kz;
        localStrut = 0.18 * Math.max(0, Math.cos(valX) + Math.cos(valY) + Math.cos(valZ));
      } else { // grid
        const valX = normX * kx;
        const valY = normY * ky;
        const valZ = normZ * kz;
        localStrut = 0.15 * Math.max(0, Math.cos(valX) * Math.cos(valY) * Math.cos(valZ));
      }

      cache[i] = 0.05 + contactStress + shearBands + bucklingStress + localStrut;
    }

    baseStressCacheRef.current = cache;
  }, [vertices, size, material, pattern, cellSize, orientation]);

  // 2. Perform in-place updates of the color buffer attribute on appliedForce updates (prevents geometry re-creations)
  useEffect(() => {
    if (mode !== "heatmap") return;
    if (vertices.length === 0 || !geometry || !baseStressCacheRef.current) return;
    const colorAttr = geometry.getAttribute("color") as THREE.BufferAttribute;
    if (!colorAttr) return;

    const numVerts = vertices.length / 3;
    const tempColors = new Float32Array(vertices.length);
    const loadFactor = appliedForce / 1000.0;
    const isTPU = material.toUpperCase() === "TPU";
    const infillRatio = infill / 100.0;
    const localStressConcentration = 1.0 / (infillRatio + 0.1);
    const forceScale = loadFactor * localStressConcentration * (isTPU ? 0.5 : 1.1);

    const cache = baseStressCacheRef.current;

    for (let i = 0; i < numVerts; i++) {
      const baseStress = cache[i];
      const stress = baseStress * forceScale;
      
      const hue = (1.0 - Math.min(1.0, stress)) * 240.0;
      const rgb = fastHslToRgb(hue);
      tempColors[i * 3] = rgb[0];
      tempColors[i * 3 + 1] = rgb[1];
      tempColors[i * 3 + 2] = rgb[2];
    }

    // Direct, highly efficient in-place buffer modification in GPU VRAM
    colorAttr.copyArray(tempColors);
    colorAttr.needsUpdate = true;
  }, [geometry, vertices, mode, appliedForce, material, infill]);

  // Define clipping plane for slicer mode
  const clippingPlane = useMemo(() => {
    const s = size || 50.0;
    const sh = sliceHeight || 25.0;
    const half = s / 2;
    return new THREE.Plane(new THREE.Vector3(0, 0, -1), sh - half);
  }, [sliceHeight, size]);

  if (vertices.length === 0 || faces.length === 0) {
    return (
      <mesh>
        <boxGeometry args={[size - 2, size - 2, size - 2]} />
        <meshStandardMaterial
          color="#334155"
          wireframe
          transparent
          opacity={0.1}
        />
      </mesh>
    );
  }

  const isWireframe = mode === "wireframe";
  const isTransparent = mode === "transparent";
  const isSlicer = mode === "slicer";
  const isHeatmap = mode === "heatmap";
  const isShell = mode === "shell";

  const color = material === "TPU" ? "#2563eb" : "#475569";

  // Calculate physical compression deformation factors (Y is vertical in Three.js)
  const maxDeform = predictions?.deformationMm || 4.0;
  const deformationMm = (appliedForce / 1000.0) * maxDeform;
  const compressionFactor = Math.min(0.20, deformationMm / size); // caps at 20% deformation
  const half = size / 2;
  const yShift = -half * compressionFactor; // locks the bottom of the cube

  return (
    <group
      position={[-size / 2, -size / 2 + yShift, -size / 2]}
      scale={[1, 1 - compressionFactor, 1]}
    >
      <mesh ref={meshRef} geometry={geometry}>
        {isHeatmap ? (
          <meshStandardMaterial
            key={`heatmap-mat-${mode}`}
            vertexColors
            roughness={0.4}
            metalness={0.1}
            side={THREE.DoubleSide}
          />
        ) : isShell ? (
          <meshStandardMaterial
            key="shell-mat"
            color="#2563eb"
            wireframe={true}
            roughness={0.3}
            metalness={0.8}
            side={THREE.DoubleSide}
          />
        ) : (
          <meshStandardMaterial
            key={`standard-mat-${mode}`}
            color={color}
            wireframe={isWireframe}
            transparent={isTransparent || isSlicer}
            opacity={isTransparent ? 0.35 : isSlicer ? 0.25 : 1.0}
            roughness={0.5}
            metalness={0.1}
            side={THREE.DoubleSide}
            clippingPlanes={isSlicer && clippingPlane ? [clippingPlane] : undefined}
          />
        )}
      </mesh>

      {/* Render sliced toolpath indicator */}
      {isSlicer && clippingPlane && (
        <mesh geometry={geometry}>
          <meshStandardMaterial
            key="slicer-indicator-mat"
            color="#38bdf8"
            wireframe
            transparent
            opacity={0.9}
            side={THREE.DoubleSide}
            clippingPlanes={[
              clippingPlane,
              new THREE.Plane(new THREE.Vector3(0, 0, 1), -((sliceHeight || 25.0) - (size || 50.0) / 2 - 1.0)),
            ]}
          />
        </mesh>
      )}
    </group>
  );
}

// Interactive Build Plate component representing the machine bed boundaries and grid
function BuildPlate({ printerName, printerProfiles, size }: { printerName: string; printerProfiles: any[]; size: number }) {
  const profile = printerProfiles.find(p => p.name === printerName);
  const width = profile?.build_volume?.x || 220.0;
  const depth = profile?.build_volume?.y || 220.0;
  const height = profile?.build_volume?.z || 240.0;

  return (
    <group position={[0, -size / 2 - 0.1, 0]}>
      {/* Rejilla de la camilla */}
      <gridHelper args={[width, 20, "#1E40AF", "#cbd5e1"]} />
      
      {/* Límites de la cama y volumen traslúcido de la cámara de impresión */}
      <mesh position={[0, height / 2, 0]}>
        <boxGeometry args={[width, height, depth]} />
        <meshBasicMaterial
          color="#1E40AF"
          wireframe
          transparent
          opacity={0.05}
        />
      </mesh>
      
      {/* Indicador de Origen Máquina (Front-Left en camas Creality) */}
      <mesh position={[-width / 2, 0.2, depth / 2]} rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[3, 3, 0.5, 32]} />
        <meshBasicMaterial color="#ef4444" />
      </mesh>
      <Html position={[-width / 2, 6, depth / 2]} center>
        <div className="pointer-events-none select-none font-mono text-[7px] font-black text-[#ef4444] uppercase tracking-widest bg-white/90 px-1.5 py-0.5 rounded border border-red-200">
          Origen
        </div>
      </Html>
    </group>
  );
}

function PerformanceHUD({ vertices, faces, resolution }: { vertices: number[]; faces: number[]; resolution: string }) {
  const fpsRef = useRef<HTMLSpanElement>(null);
  
  useEffect(() => {
    let lastTime = performance.now();
    let frames = 0;
    let animationFrameId: number;
    
    const tick = () => {
      frames++;
      const now = performance.now();
      if (now >= lastTime + 1000) {
        if (fpsRef.current) {
          fpsRef.current.innerText = `${Math.round((frames * 1000) / (now - lastTime))} FPS`;
        }
        frames = 0;
        lastTime = now;
      }
      animationFrameId = requestAnimationFrame(tick);
    };
    
    animationFrameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animationFrameId);
  }, []);
  
  const triangles = Math.round(faces.length / 3);
  const kTriangles = triangles > 1000 ? `${(triangles / 1000).toFixed(1)}k` : triangles;
  
  return (
    <div className="absolute top-16 left-3 z-10 bg-white/95 border border-slate-200/80 backdrop-blur-md p-2.5 rounded-lg text-xs font-mono text-slate-600 pointer-events-auto flex flex-col gap-1 w-48 shadow-sm">
      <div className="text-slate-800 font-bold flex justify-between">
        <span>DIAGNÓSTICOS CAD</span>
        <span ref={fpsRef} className="text-emerald-600 font-black">-- FPS</span>
      </div>
      <hr className="border-slate-200 my-0.5" />
      <div className="flex justify-between"><span>Triángulos:</span><span className="font-bold text-slate-800">{kTriangles}</span></div>
      <div className="flex justify-between"><span>Vértices:</span><span className="font-bold text-slate-800">{vertices.length / 3}</span></div>
      <div className="flex justify-between"><span>Resolución:</span><span className="font-bold text-slate-800">{resolution}</span></div>
      <div className="flex justify-between"><span>Carga GPU:</span><span className="font-bold text-sky-600">{triangles > 200000 ? "Alta" : triangles > 50000 ? "Media" : "Baja"}</span></div>
    </div>
  );
}

function QualityHUD() {
  const { resolution, setParam } = useLabStore(
    useShallow((state) => ({
      resolution: state.resolution,
      setParam: state.setParam,
    }))
  );
  
  const resolutions = [
    { value: "Baja", label: "Draft" },
    { value: "Media", label: "Balanced" },
    { value: "Alta", label: "High" },
    { value: "Ultra", label: "Ultra" },
  ];
  
  return (
    <div className="absolute top-16 left-1/2 -translate-x-1/2 z-10 bg-white/95 border border-slate-200/80 p-0.5 rounded-lg flex space-x-0.5 shadow-sm text-sm pointer-events-auto">
      {resolutions.map((r) => (
        <button
          key={r.value}
          onClick={() => setParam("resolution", r.value)}
          className={`px-2.5 py-1 text-xs font-bold rounded-md uppercase tracking-wider cursor-pointer transition-all ${
            resolution === r.value
              ? "bg-[#1E40AF] text-white shadow-2xs font-bold"
              : "text-slate-500 hover:text-slate-900 hover:bg-slate-100/60"
          }`}
        >
          {r.label}
        </button>
      ))}
    </div>
  );
}

function PrintEstimationHUD() {
  const { predictions, material, selectedPrinter } = useLabStore(
    useShallow((state) => ({
      predictions: state.predictions,
      material: state.material,
      selectedPrinter: state.selectedPrinter,
    }))
  );

  const printTimeMins = predictions?.printingTimeMinutes || 0;
  const hours = Math.floor(printTimeMins / 60);
  const mins = printTimeMins % 60;
  const timeStr = hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  
  const mass = predictions?.massGrams || 0;
  const speed = useLabStore((state) => state.printSpeed);
  const lh = useLabStore((state) => state.layerHeight);
  const isTPU = material.toUpperCase() === "TPU";
  const maxFlow = isTPU ? 8.0 : 32.0;
  const flowVal = Math.min(maxFlow, speed * lh * 0.45).toFixed(1);

  return (
    <div className="absolute bottom-3 left-3 z-10 bg-white/95 border border-slate-200/80 backdrop-blur-md p-2.5 rounded-lg text-xs font-mono text-slate-600 pointer-events-auto flex flex-col gap-1 w-52 shadow-sm">
      <div className="text-slate-800 font-bold uppercase tracking-wider">
        Estimación Impresión
      </div>
      <hr className="border-slate-200 my-0.5" />
      <div className="flex justify-between"><span>Tiempo:</span><span className="font-bold text-sky-600">{timeStr}</span></div>
      <div className="flex justify-between"><span>Masa:</span><span className="font-bold text-emerald-600">{mass.toFixed(1)} g</span></div>
      <div className="flex justify-between"><span>Flujo:</span><span className="font-bold text-slate-800">{flowVal} mm³/s</span></div>
      <div className="flex justify-between"><span>Perfil:</span><span className="font-bold text-slate-800 truncate max-w-[100px]">{selectedPrinter}</span></div>
    </div>
  );
}

export default function BaseViewport() {
  const {
    dimX,
    viewportMode,
    sliceHeight,
    material,
    meshVertices,
    meshFaces,
    loadingMesh,
    cameraAngle,
    setParam,
    selectedPrinter,
    printerProfiles,
    showBuildPlate,
    resolution,
  } = useLabStore(
    useShallow((state) => ({
      dimX: state.dimX,
      viewportMode: state.viewportMode,
      sliceHeight: state.sliceHeight,
      material: state.material,
      meshVertices: state.meshVertices,
      meshFaces: state.meshFaces,
      loadingMesh: state.loadingMesh,
      cameraAngle: state.cameraAngle,
      setParam: state.setParam,
      selectedPrinter: state.selectedPrinter,
      printerProfiles: state.printerProfiles,
      showBuildPlate: state.showBuildPlate,
      resolution: state.resolution,
    }))
  );

  const sizeMm = dimX * 10; // in mm

  return (
    <div className="relative w-full h-full bg-[#FAFBFC] flex flex-col border border-slate-200 rounded-xl overflow-hidden shadow-sm">
      {/* Floating Viewport Toolbar */}
      <div className="absolute top-3 left-3 right-3 z-10 flex items-center justify-between pointer-events-none">
        {/* Shading / View Modes */}
        <div className="bg-white/95 border border-slate-200/80 p-0.5 rounded-lg flex space-x-0.5 shadow-sm text-sm pointer-events-auto overflow-x-auto max-w-[70%] scrollbar-none font-bold backdrop-blur-xs">
          {(["solid", "shell", "wireframe", "transparent", "heatmap", "slicer"] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => setParam("viewportMode", mode as any)}
              className={`px-2.5 py-1 text-xs lg:text-sm font-black rounded-md capitalize transition-all cursor-pointer whitespace-nowrap ${
                viewportMode === mode
                  ? "bg-[#1E40AF] text-white shadow-2xs font-bold"
                  : "text-slate-500 hover:text-slate-900 hover:bg-slate-100/60"
              }`}
            >
              {mode === "solid"
                ? "Sólido"
                : mode === "shell"
                ? "Carcasa"
                : mode === "wireframe"
                ? "Alámbrico"
                : mode === "transparent"
                ? "Transparente"
                : mode === "heatmap"
                ? "Estrés"
                : "Sección"}
            </button>
          ))}
        </div>

        {/* Camera Preset Angles */}
        <div className="bg-white/95 border border-slate-200/80 p-0.5 rounded-lg flex space-x-0.5 shadow-sm text-sm pointer-events-auto font-bold backdrop-blur-xs">
          {(["perspective", "top", "front", "side"] as const).map((angle) => (
            <button
              key={angle}
              onClick={() => setParam("cameraAngle", angle)}
              className={`px-2.5 py-1 text-xs lg:text-sm font-black rounded-md capitalize transition-all cursor-pointer ${
                cameraAngle === angle
                  ? "bg-[#1E40AF] text-white shadow-2xs font-bold"
                  : "text-slate-500 hover:text-slate-900 hover:bg-slate-100/60"
              }`}
            >
              {angle === "perspective"
                ? "Persp"
                : angle === "top"
                ? "Top"
                : angle === "front"
                ? "Front"
                : "Side"}
            </button>
          ))}
        </div>
      </div>

      {/* Floating HUD Overlays */}
      <PerformanceHUD vertices={meshVertices} faces={meshFaces} resolution={resolution} />
      <QualityHUD />
      <PrintEstimationHUD />

      {/* Loading Overlay */}
      {loadingMesh && (
        <div className="absolute inset-0 bg-slate-950/80 z-20 flex flex-col items-center justify-center backdrop-blur-xs">
          <div className="w-8 h-8 border-3 border-[#38bdf8] border-t-transparent rounded-full animate-spin"></div>
          <span className="mt-3.5 text-sm text-slate-350 font-bold font-mono tracking-widest uppercase">
            COMPILANDO GEOMETRÍA SDF...
          </span>
        </div>
      )}

      {/* Interactive 3D Canvas */}
      <div className="flex-1 w-full">
        <Canvas
          camera={{ position: [60, 60, 80], fov: 45 }}
          gl={{ localClippingEnabled: true }}
        >
          <ClippingEnabler />
          <CameraController />
          <color attach="background" args={["#FAFBFC"]} />
          <ambientLight intensity={0.6} />
          <directionalLight position={[100, 100, 50]} intensity={1.0} />
          <directionalLight position={[-100, -100, -50]} intensity={0.4} />

          <group rotation={[0, 0, 0]}>
            <LatticeMesh
               vertices={meshVertices}
               faces={meshFaces}
               mode={viewportMode}
               material={material}
               size={sizeMm}
               sliceHeight={sliceHeight}
            />
            <DimensionLines size={sizeMm} />
            {showBuildPlate && (
              <BuildPlate
                printerName={selectedPrinter}
                printerProfiles={printerProfiles}
                size={sizeMm}
              />
            )}
          </group>

          <OrbitControls makeDefault enableDamping dampingFactor={0.05} />
        </Canvas>
      </div>

      {/* Bottom Slider for Slicer Height (Z) */}
      {viewportMode === "slicer" && (
        <div className="absolute bottom-16 left-4 right-4 z-10 bg-white/95 border border-slate-200/80 p-3.5 rounded-lg flex flex-col space-y-1.5 shadow-sm font-sans backdrop-blur-xs">
          <div className="flex justify-between items-baseline text-xs lg:text-sm font-semibold">
            <span className="text-slate-550 uppercase tracking-wider">PLANO DE LAMINADO (Z)</span>
            <span className="text-[#1E40AF] font-bold font-mono">{(sliceHeight / 10).toFixed(2)} cm / {sliceHeight.toFixed(1)} mm</span>
          </div>
          <input
            type="range"
            min={0}
            max={sizeMm}
            step={0.5}
            value={sliceHeight}
            onChange={(e) => setParam("sliceHeight", parseFloat(e.target.value))}
            className="w-full h-1 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-[#1E40AF]"
          />
          <div className="flex justify-between text-xs text-slate-400 font-mono">
            <span>Base (0.0 mm)</span>
            <span>Máximo ({sizeMm.toFixed(1)} mm)</span>
          </div>
        </div>
      )}

      {/* Axis compass overlay */}
      <div className="absolute bottom-3 right-3 text-[10px] lg:text-xs font-mono text-slate-550 bg-white/95 p-2.5 rounded-lg border border-slate-200/80 pointer-events-none shadow-sm flex flex-col gap-1 backdrop-blur-xs">
        <div className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500"/>Y: VERTICAL</div>
        <div className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-blue-500"/>Z: PROFUNDIDAD</div>
        <div className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-red-500"/>X: ANCHO</div>
      </div>
    </div>
  );
}

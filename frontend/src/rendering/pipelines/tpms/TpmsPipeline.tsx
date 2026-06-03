"use client";

import React, { useMemo, useEffect, useRef } from "react";
import * as THREE from "three";
import { useLabStore } from "@/stores/useLabStore";
import { Bvh } from "@react-three/drei";
import { PipelineProps } from "../types";
import { computeBoundsTree, disposeBoundsTree, acceleratedRaycast } from "three-mesh-bvh";

// Extend BufferGeometry and Mesh prototypes at file scope to accelerate raycasting and clipping
if (typeof window !== "undefined" && !THREE.BufferGeometry.prototype.computeBoundsTree) {
  THREE.BufferGeometry.prototype.computeBoundsTree = computeBoundsTree as any;
  THREE.BufferGeometry.prototype.disposeBoundsTree = disposeBoundsTree as any;
  THREE.Mesh.prototype.raycast = acceleratedRaycast as any;
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

export function TpmsPipeline({ vertices, faces, mode, material, size, sliceHeight }: PipelineProps) {
  const appliedForce = useLabStore((state) => state.appliedForce);
  const predictions = useLabStore((state) => state.predictions);
  const infill = useLabStore((state) => state.infill);
  const pattern = useLabStore((state) => state.pattern);
  const cellSize = useLabStore((state) => state.cellSize);
  const orientation = useLabStore((state) => state.orientation);

  const baseStressCacheRef = useRef<Float32Array | null>(null);

  // 1. Compile static geometry (position & index only)
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

    // Accelerate raycasting, slicing, and rendering inside Three.js using three-mesh-bvh
    if (geom.computeBoundsTree) {
      geom.computeBoundsTree({
        strategy: 1, // CENTER strategy is highly optimal for dynamic model updates
      });
    }

    return geom;
  }, [vertices, faces]);

  // Clean up geometry and BVH bounds tree to prevent VRAM memory leak
  useEffect(() => {
    return () => {
      if (geometry.disposeBoundsTree) {
        geometry.disposeBoundsTree();
      }
      geometry.dispose();
    };
  }, [geometry]);

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

  // Clean up materials on unmount
  useEffect(() => {
    return () => {
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
    // Baseline preload of 150N to show a beautiful preview gradient when force is 0
    const loadFactor = Math.max(150.0, appliedForce) / 1000.0;
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

  interface PbrParams {
    roughness: number;
    metalness: number;
    clearcoat: number;
    clearcoatRoughness?: number;
    color: string;
  }

  // Advanced premium PBR parameters by material type to simulate high-end filaments
  const pbrParams = useMemo<PbrParams>(() => {
    const matUpper = material.toUpperCase();
    if (matUpper === "TPU") {
      return {
        roughness: 0.55,
        metalness: 0.05,
        clearcoat: 0.15,
        color: "#2563eb", // Vibrant TPU blue
      };
    } else if (matUpper === "PLA") {
      return {
        roughness: 0.22,
        metalness: 0.32, // Metallic flake finish
        clearcoat: 0.85,
        clearcoatRoughness: 0.08,
        color: "#334155", // Charcoal space grey
      };
    } else if (matUpper === "ABS") {
      return {
        roughness: 0.32,
        metalness: 0.12,
        clearcoat: 0.65,
        clearcoatRoughness: 0.12,
        color: "#e11d48", // Sleek red
      };
    } else { // PETG
      return {
        roughness: 0.15,
        metalness: 0.20,
        clearcoat: 0.95,
        clearcoatRoughness: 0.04,
        color: "#059669", // Vibrant teal green
      };
    }
  }, [material]);

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
      <Bvh firstHitOnly>
        <mesh ref={meshRef} geometry={geometry} castShadow receiveShadow>
          {isHeatmap ? (
            <meshPhysicalMaterial
              key={`heatmap-mat-${mode}`}
              vertexColors
              roughness={0.18}
              metalness={0.15}
              clearcoat={0.95}
              clearcoatRoughness={0.06}
              side={THREE.DoubleSide}
              flatShading={false}
              clippingPlanes={isSlicer && clippingPlane ? [clippingPlane] : undefined}
            />
          ) : isShell ? (
            <meshPhysicalMaterial
              key="shell-mat"
              color="#2563eb"
              wireframe={true}
              roughness={0.3}
              metalness={0.8}
              side={THREE.DoubleSide}
              flatShading={false}
            />
          ) : (
            <meshPhysicalMaterial
              key={`physical-mat-${mode}-${material}`}
              color={pbrParams.color}
              roughness={pbrParams.roughness}
              metalness={pbrParams.metalness}
              clearcoat={pbrParams.clearcoat}
              clearcoatRoughness={pbrParams.clearcoatRoughness || 0.1}
              wireframe={isWireframe}
              transparent={isTransparent || isSlicer}
              opacity={isTransparent ? 0.35 : isSlicer ? 0.25 : 1.0}
              side={THREE.DoubleSide}
              clippingPlanes={isSlicer && clippingPlane ? [clippingPlane] : undefined}
              flatShading={false}
            />
          )}
        </mesh>
      </Bvh>

      {/* Render sliced toolpath indicator */}
      {isSlicer && clippingPlane && (
        <mesh geometry={geometry} castShadow receiveShadow>
          <meshPhysicalMaterial
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
            flatShading={false}
          />
        </mesh>
      )}
    </group>
  );
}

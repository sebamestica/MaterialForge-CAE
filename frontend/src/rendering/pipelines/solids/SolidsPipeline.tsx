"use client";

import React, { useMemo, useEffect } from "react";
import * as THREE from "three";
import { Bvh } from "@react-three/drei";
import { PipelineProps } from "../types";

export function SolidsPipeline({ vertices, faces, material, size }: PipelineProps) {
  const geometry = useMemo(() => {
    const geom = new THREE.BufferGeometry();
    if (vertices.length === 0 || faces.length === 0) return geom;

    geom.setAttribute("position", new THREE.BufferAttribute(new Float32Array(vertices), 3));
    geom.setIndex(new THREE.BufferAttribute(new Uint32Array(faces), 1));
    geom.computeVertexNormals();

    return geom;
  }, [vertices, faces]);

  // Clean up geometry to prevent VRAM memory leak
  useEffect(() => {
    return () => {
      geometry.dispose();
    };
  }, [geometry]);

  if (vertices.length === 0 || faces.length === 0) return null;

  return (
    <group position={[-size / 2, -size / 2, -size / 2]}>
      <Bvh firstHitOnly>
        <mesh geometry={geometry}>
          <meshPhysicalMaterial
            color={material === "TPU" ? "#2563eb" : "#475569"}
            roughness={0.4}
            metalness={0.2}
            clearcoat={0.3}
            side={THREE.DoubleSide}
          />
        </mesh>
      </Bvh>
    </group>
  );
}

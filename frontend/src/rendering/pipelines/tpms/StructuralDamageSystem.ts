import * as THREE from "three";

/**
 * MATERIALFORGE — STRUCTURAL DAMAGE SYSTEM (SFVS V2)
 * Centralizes the progressive structural failure visualizer representation,
 * states classification, shader injection scripts, and debris trajectory calculations.
 */

export interface FailureState {
  level: number;
  label: string;
  colorClass: string;
  description: string;
}

export const FAILURE_STATES: FailureState[] = [
  {
    level: 0,
    label: "Elástico",
    colorClass: "text-emerald-600 bg-emerald-50 border-emerald-100",
    description: "Carga baja. Comportamiento puramente elástico, sin daño ni deformaciones permanentes.",
  },
  {
    level: 1,
    label: "Transición",
    colorClass: "text-yellow-600 bg-yellow-50 border-yellow-100",
    description: "Carga media. Concentración moderada de esfuerzos en celdas críticas, deformación visible.",
  },
  {
    level: 2,
    label: "Pre-Falla",
    colorClass: "text-amber-600 bg-amber-50 border-amber-100 animate-pulse",
    description: "Inestabilidad estructural incipiente. Leve micro-vibración localizada en zonas de alto estrés.",
  },
  {
    level: 3,
    label: "Daño Local",
    colorClass: "text-orange-600 bg-orange-50 border-orange-200 animate-pulse",
    description: "Inicio de fractura. Micro-grietas y vacíos en paredes críticas. La estructura sigue estable.",
  },
  {
    level: 4,
    label: "Colapso Parcial",
    colorClass: "text-rose-600 bg-rose-50 border-rose-200 animate-pulse font-extrabold",
    description: "Buckling local y colapso celular asimétrico. Hundimiento y pérdida de material en zonas críticas.",
  },
  {
    level: 5,
    label: "Colapso Global",
    colorClass: "text-red-700 bg-red-50 border-red-200 font-black",
    description: "Pérdida total de capacidad portante. Ruptura extendida y desprendimiento de escombros.",
  },
];

/**
 * Classifies the structural state based on the normalized damageFactor (0.0 to 1.5).
 */
export function getFailureState(damageFactor: number): FailureState {
  if (damageFactor < 0.50) return FAILURE_STATES[0];
  if (damageFactor < 0.75) return FAILURE_STATES[1];
  if (damageFactor < 0.90) return FAILURE_STATES[2];
  if (damageFactor < 1.00) return FAILURE_STATES[3];
  if (damageFactor < 1.15) return FAILURE_STATES[4];
  return FAILURE_STATES[5];
}

/**
 * Shader injections for THREE.MeshPhysicalMaterial onBeforeCompile
 */
export const StructuralDamageShaders = {
  // Vertex Shader Injections
  vertexHeader: `
    uniform float uDamageFactor;
    uniform float uTime;
    varying vec3 vLocalPosition;
  `,
  vertexBody: `
    #include <begin_vertex>
    vLocalPosition = position.xyz;
    
    #ifdef USE_COLOR
      float localStress = color.r; // Red vertex represents high stress
      
      // Level 2+: Pre-falla (uDamageFactor > 0.75) structural micro-vibrations
      if (uDamageFactor > 0.75) {
        float vibeFreq = 55.0;
        float vibeAmp = 0.005 * (uDamageFactor - 0.75);
        float vibe = sin(uTime * vibeFreq + position.y * 3.0) * vibeAmp;
        transformed.x += vibe * localStress;
        transformed.z += vibe * localStress;
      }
      
      // Level 3+: Buckling and localized cellular collapse (cellCollapseFactor)
      if (uDamageFactor > 0.90) {
        // cellCollapseFactor dynamic scaling (0.0 -> 1.0)
        float cellCollapseFactor = clamp((uDamageFactor - 0.90) / 0.25, 0.0, 1.0);
        
        // Localized buckling (stable, non-uniform lateral bending displacement based on height)
        float buckle = sin(position.y * 1.8) * cos(position.x * 1.8) * 0.06 * cellCollapseFactor * localStress;
        transformed.x += buckle;
        transformed.z += buckle;
        
        // Localized sinking/cell collapse in Y axis
        transformed.y -= 0.12 * cellCollapseFactor * localStress * position.y;
      }
    #endif
  `,

  // Fragment Shader Injections
  fragmentHeader: `
    uniform float uDamageFactor;
    uniform float uTime;
    uniform vec3 uBaseColor;
    uniform float uUseHeatmap;
    varying vec3 vLocalPosition;
  `,
  fragmentBody: `
    #ifdef USE_COLOR
      float localStress = vColor.r;
      
      // CrackOverlay: procedural multi-frequency noise to simulate cracks (Phase 5) using local coordinate space
      float n1 = sin(vLocalPosition.x * 1.5) * cos(vLocalPosition.y * 1.5) * sin(vLocalPosition.z * 1.5);
      float n2 = sin(vLocalPosition.y * 8.0) * cos(vLocalPosition.z * 8.0) * 0.3;
      float n3 = sin(vLocalPosition.x * 15.0) * sin(vLocalPosition.y * 15.0) * 0.15;
      float crackPattern = abs(n1 + n2 + n3);
      
      // Level 3+: Discard cracks/voids (failureMask) starting from damageFactor > 0.90
      if (uDamageFactor > 0.90) {
        float limit = (uDamageFactor - 0.90) * 0.40;
        if (localStress > 0.45 && crackPattern < limit) {
          discard;
        }
      }
      
      // Overwrite base color if not in heatmap view
      if (uUseHeatmap < 0.5) {
        diffuseColor.rgb = uBaseColor;
        
        // Level 2+: Darken high-stress zones near crack edges to simulate stress strain/fracture
        if (uDamageFactor > 0.75 && localStress > 0.4) {
          float darkenFactor = 1.0 - clamp((uDamageFactor - 0.75) * 0.5 * localStress, 0.0, 0.6);
          diffuseColor.rgb *= darkenFactor;
        }
      }
      
      // Level 4+: Reduce local opacity for collapsing struts (simulating cell disintegration)
      if (uDamageFactor > 0.90 && localStress > 0.50) {
        float cellCollapseOpacity = 1.0 - clamp((uDamageFactor - 0.90) * 0.7 * localStress, 0.0, 0.8);
        diffuseColor.a *= cellCollapseOpacity;
      }
    #endif
    
    #include <opaque_fragment>
  `
};

/**
 * Precomputes deterministic debris trajectories for 50 particles.
 */
export interface DebrisParticle {
  startPos: THREE.Vector3;
  vel: THREE.Vector3;
  rotAxis: THREE.Vector3;
}

export function generateDebrisParticles(size: number): DebrisParticle[] {
  const list: DebrisParticle[] = [];
  for (let i = 0; i < 50; i++) {
    // Start position distributed around high-stress outer shell surfaces
    const theta = (i * 2.3) % (Math.PI * 2);
    const phi = (i * 3.7) % Math.PI;
    
    const startPos = new THREE.Vector3(
      (Math.sin(phi) * Math.cos(theta) * 0.45 + 0.5) * size,
      (Math.sin(phi) * Math.sin(theta) * 0.45 + 0.5) * size,
      (Math.cos(phi) * 0.45 + 0.5) * size
    );
    
    // upward and outward velocity bias
    const vel = new THREE.Vector3(
      Math.sin(i * 4.3),
      Math.abs(Math.cos(i * 5.7)) * 0.9 + 0.1, // upward bias
      Math.cos(i * 7.1)
    ).normalize().multiplyScalar(size * 0.18 * (0.7 + (i % 5) * 0.2));
    
    // rotation axis
    const rotAxis = new THREE.Vector3(
      Math.sin(i * 1.9),
      Math.cos(i * 2.9),
      Math.sin(i * 3.9)
    ).normalize();
    
    list.push({ startPos, vel, rotAxis });
  }
  return list;
}

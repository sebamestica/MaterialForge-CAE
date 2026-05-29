export const renderingConfig = {
  // Studio background styling
  background: {
    color: '#FAFBFC', // Light studio background
    gridColorPrimary: '#1E40AF',
    gridColorSecondary: '#cbd5e1',
  },

  // Default camera preset locations (X, Y, Z coordinates)
  cameraPresets: {
    perspective: { x: 60, y: 60, z: 80 },
    top: { x: 0, y: 110, z: 0 },
    front: { x: 0, y: 0, z: 110 },
    side: { x: 110, y: 0, z: 0 },
  },

  // Lights configurations
  lighting: {
    ambientIntensity: 0.6,
    directionalMain: {
      position: [100, 100, 50] as [number, number, number],
      intensity: 1.0,
    },
    directionalFill: {
      position: [-100, -100, -50] as [number, number, number],
      intensity: 0.4,
    }
  },

  // Viewport shading options
  shadingModes: [
    { value: 'solid', label: 'Sólido' },
    { value: 'shell', label: 'Carcasa' },
    { value: 'wireframe', label: 'Alámbrico' },
    { value: 'transparent', label: 'Transparente' },
    { value: 'heatmap', label: 'Estrés' },
    { value: 'slicer', label: 'Sección' }
  ]
};

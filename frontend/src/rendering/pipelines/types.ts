export interface PipelineProps {
  vertices: number[];
  faces: number[];
  mode: "solid" | "wireframe" | "transparent" | "heatmap" | "slicer" | "layers" | "shell";
  material: string;
  size: number;
  sliceHeight: number;
  isInteracting?: boolean;
}

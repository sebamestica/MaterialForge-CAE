"use client";

import { PipelineProps } from "../types";

export function ImportedMeshesPipeline({ vertices, faces }: PipelineProps) {
  if (vertices?.length && faces?.length) {
    return null;
  }
  return null;
}

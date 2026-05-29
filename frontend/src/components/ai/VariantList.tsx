"use client";

import React from "react";
import { VariantData, useDesignStore } from "../../stores/designStore";
import VariantCard from "./VariantCard";

interface VariantListProps {
  variants: VariantData[];
}

export default function VariantList({ variants }: VariantListProps) {
  const { currentVariant, setCurrentVariant, setPendingPatch } = useDesignStore();

  if (!variants || variants.length === 0) {
    return (
      <div className="text-center p-4 text-[10px] text-slate-500 font-mono border border-slate-900 border-dashed rounded bg-slate-950/20">
        No hay variantes de diseño disponibles.
      </div>
    );
  }

  const activeId = currentVariant?.id || variants[0]?.id;

  const handleSelect = (v: VariantData) => {
    setCurrentVariant(v);
    setPendingPatch(v.config_patch);
  };

  return (
    <div className="space-y-3.5 max-h-[420px] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-slate-800">
      {variants.map((v) => (
        <VariantCard
          key={v.id}
          variant={v}
          isActive={v.id === activeId}
          onSelect={() => handleSelect(v)}
        />
      ))}
    </div>
  );
}

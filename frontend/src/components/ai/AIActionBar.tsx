"use client";

import React from "react";
import { useDesignStore } from "../../stores/designStore";
import { useLabStore } from "../../stores/useLabStore";
import { Zap } from "lucide-react";

export default function AIActionBar() {
  const optimizeConfig = useLabStore((state) => state.optimizeConfig);
  const loading = useDesignStore((state) => state.loading);

  return (
    <div className="bg-slate-950/40 border border-slate-800 rounded-lg p-2.5 font-mono text-[10px] space-y-2">
      <div className="flex items-center gap-1.5 text-slate-450 text-[9px] uppercase font-black tracking-wider">
        <Zap className="w-3.5 h-3.5 text-blue-500" />
        <span>Optimización Rápida</span>
      </div>
      
      <div className="flex gap-1.5">
        <button
          onClick={() => optimizeConfig("strength")}
          disabled={loading}
          className="px-1.5 py-1 text-[8px] uppercase tracking-wider font-extrabold text-slate-400 hover:text-white bg-slate-900 border border-slate-800 hover:border-slate-650 rounded cursor-pointer disabled:opacity-40 transition-colors flex-1 text-center"
        >
          strength
        </button>
        <button
          onClick={() => optimizeConfig("energy")}
          disabled={loading}
          className="px-1.5 py-1 text-[8px] uppercase tracking-wider font-extrabold text-slate-400 hover:text-white bg-slate-900 border border-slate-800 hover:border-slate-650 rounded cursor-pointer disabled:opacity-40 transition-colors flex-1 text-center"
        >
          energy
        </button>
        <button
          onClick={() => optimizeConfig("lightweight")}
          disabled={loading}
          className="px-1.5 py-1 text-[8px] uppercase tracking-wider font-extrabold text-slate-400 hover:text-white bg-slate-900 border border-slate-800 hover:border-slate-650 rounded cursor-pointer disabled:opacity-40 transition-colors flex-1 text-center"
        >
          weight
        </button>
        <button
          onClick={() => optimizeConfig("balance")}
          disabled={loading}
          className="px-1.5 py-1 text-[8px] uppercase tracking-wider font-extrabold text-slate-400 hover:text-white bg-slate-900 border border-slate-800 hover:border-slate-650 rounded cursor-pointer disabled:opacity-40 transition-colors flex-1 text-center"
        >
          balance
        </button>
      </div>
    </div>
  );
}

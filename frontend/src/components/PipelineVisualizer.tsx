"use client";

import React from "react";
import { motion } from "framer-motion";
import { CheckCircle, Circle, Loader2, AlertTriangle, XCircle } from "lucide-react";

interface PipelineVisualizerProps {
  status: "idle" | "compiling" | "success" | "error";
  metrics: any;
}

const STAGES = [
  "Intent Extraction",
  "System Design",
  "Database Schema",
  "API Schema",
  "UI Schema",
  "Auth Rules",
  "Business Logic"
];

export default function PipelineVisualizer({ status, metrics }: PipelineVisualizerProps) {
  // Mock active stage based on metrics or status
  // In a real streaming app, this would be updated via SSE.
  const isComplete = status === "success";
  const isCompiling = status === "compiling";

  return (
    <div className="bg-[#1e293b] rounded-2xl p-6 shadow-xl border border-[#334155] w-full mt-6">
      <h2 className="text-xl font-bold mb-6 text-white flex items-center">
        Pipeline Visualization
      </h2>

      <div className="relative w-full overflow-x-auto pb-4 hide-scrollbar">
        <div className="min-w-[600px] relative px-4">
          <div className="absolute top-5 left-8 right-8 h-1 bg-[#334155] z-0 rounded-full" />
          {isCompiling && (
             <motion.div 
               className="absolute top-5 left-8 h-1 bg-blue-500 z-0 rounded-full"
               initial={{ width: "0%" }}
               animate={{ width: "calc(100% - 4rem)" }}
               transition={{ duration: 15, ease: "linear" }}
             />
          )}
          {isComplete && (
             <div className="absolute top-5 left-8 right-8 h-1 bg-green-500 z-0 rounded-full" />
          )}

          <div className="relative z-10 flex justify-between">
            {STAGES.map((stage, i) => {
              const isStageDone = isComplete;
              const isCurrent = isCompiling;
              return (
                <div key={stage} className="flex flex-col items-center">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center bg-[#0f172a] border-4 z-10 relative ${isStageDone ? 'border-green-500 text-green-500' : isCurrent ? 'border-blue-500 text-blue-500 animate-pulse' : 'border-[#334155] text-gray-500'}`}>
                    {isStageDone ? <CheckCircle className="w-5 h-5" /> : isCurrent ? <Loader2 className="w-5 h-5 animate-spin" /> : <Circle className="w-5 h-5" />}
                  </div>
                  <span className="text-xs text-gray-400 mt-2 font-semibold w-20 text-center">{stage}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
      
      {metrics?.failures?.length > 0 && (
         <div className="mt-8 bg-red-950/20 border border-red-900/50 rounded-xl p-4">
            <h3 className="text-red-400 font-bold mb-2 flex items-center text-sm"><AlertTriangle className="w-4 h-4 mr-2" /> Repair Actions ({metrics.failures.length})</h3>
            <div className="space-y-2 max-h-32 overflow-y-auto pr-2">
              {metrics.failures.map((f: any, i: number) => (
                <div key={i} className="text-xs text-gray-300 bg-[#0f172a] p-2 rounded border border-red-900/30">
                  <span className="text-red-400 font-bold">Attempt {f.attempt} ({f.schema}):</span> {f.error}
                </div>
              ))}
            </div>
         </div>
      )}
    </div>
  );
}

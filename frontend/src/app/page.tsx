"use client";

import React, { useState } from "react";
import RuntimePreview from "@/components/RuntimePreview";
import { Loader2, Zap, Layout, Code2, Database } from "lucide-react";

export default function Dashboard() {
  const [prompt, setPrompt] = useState("Build an AI Motivation Coach with premium tiers, daily check-ins, and Stripe integration. Include a user dashboard, a subscription form, and an AI chat interface.");
  const [loading, setLoading] = useState(false);
  const [schema, setSchema] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [error, setError] = useState("");

  const handleCompile = async () => {
    setLoading(true);
    setError("");
    setSchema(null);
    setMetrics(null);

    try {
      const res = await fetch("http://localhost:8000/api/compile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to compile");
      
      setSchema(data.data);
      setMetrics(data.metrics);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0f172a] text-white font-sans p-8 flex flex-col">
      <header className="mb-8 flex items-center space-x-3">
        <Zap className="w-8 h-8 text-blue-500" />
        <h1 className="text-3xl font-extrabold tracking-tight">Nexus App Compiler</h1>
        <span className="bg-blue-500/20 text-blue-400 text-xs px-2 py-1 rounded-full font-medium">Pipeline v1.0</span>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 flex-1">
        {/* Left Column: Input and Stats */}
        <div className="space-y-6 flex flex-col">
          <div className="bg-[#1e293b] rounded-2xl p-6 shadow-xl border border-[#334155]">
            <h2 className="text-xl font-bold mb-4 flex items-center"><Code2 className="w-5 h-5 mr-2" /> Application Prompt</h2>
            <textarea
              className="w-full h-32 bg-[#0f172a] border border-[#334155] rounded-xl p-4 text-sm text-gray-200 focus:ring-2 focus:ring-blue-500 outline-none"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
            <button
              onClick={handleCompile}
              disabled={loading}
              className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-xl flex items-center justify-center transition-all disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Zap className="w-5 h-5 mr-2" />}
              {loading ? "Compiling Application..." : "Compile Application"}
            </button>
            {error && <p className="text-red-400 text-sm mt-3">{error}</p>}
          </div>

          {/* Metrics */}
          {metrics && (
            <div className="bg-[#1e293b] rounded-2xl p-6 shadow-xl border border-[#334155]">
              <h2 className="text-xl font-bold mb-4 flex items-center"><Database className="w-5 h-5 mr-2" /> Compiler Metrics</h2>
              <div className="space-y-3">
                <div className="flex justify-between items-center bg-[#0f172a] p-3 rounded-lg border border-[#334155]">
                  <span className="text-gray-400 text-sm">Validation Engine Retries</span>
                  <span className={`font-bold ${metrics.retries > 0 ? "text-yellow-400" : "text-green-400"}`}>
                    {metrics.retries}
                  </span>
                </div>
                {metrics.failures?.length > 0 && (
                  <div className="text-xs text-red-400 bg-red-950/30 p-3 rounded-lg border border-red-900/50 max-h-32 overflow-auto">
                    Repair Engine triggered {metrics.failures.length} times to fix validation failures.
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Runtime Preview */}
        <div className="lg:col-span-2 bg-[#1e293b] rounded-2xl shadow-xl border border-[#334155] flex flex-col overflow-hidden h-[80vh]">
          <div className="p-4 bg-[#334155]/50 border-b border-[#334155] flex items-center justify-between">
            <h2 className="text-lg font-bold flex items-center"><Layout className="w-5 h-5 mr-2 text-purple-400" /> Dynamic Runtime Preview</h2>
          </div>
          <div className="flex-1 p-0 bg-gray-100 overflow-hidden relative">
             <RuntimePreview schema={schema ? schema.ui_schema : null} />
          </div>
        </div>
      </div>
    </div>
  );
}

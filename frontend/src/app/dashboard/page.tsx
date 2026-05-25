"use client";

import React, { useState, useEffect } from "react";
import RuntimePreview from "@/components/RuntimePreview";
import DatabasePreview from "@/components/DatabasePreview";
import ApiPreview from "@/components/ApiPreview";
import PipelineVisualizer from "@/components/PipelineVisualizer";
import { Loader2, Zap, Layout, Code2, Database, Server, Save, FolderOpen, AlertCircle, Download } from "lucide-react";

export default function Dashboard() {
  const [prompt, setPrompt] = useState("Build a CRM with login, admin dashboard, payments, and analytics");
  const [projectName, setProjectName] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [schema, setSchema] = useState<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [metrics, setMetrics] = useState<any>(null);
  const [error, setError] = useState("");
  
  const [activeTab, setActiveTab] = useState<"ui" | "db" | "api" | "metrics">("ui");
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [projects, setProjects] = useState<any[]>([]);

  const fetchProjects = async () => {
    try {
      const API_URL = "https://ai-software-compiler-ct1g.onrender.com";
      const res = await fetch(`${API_URL}/api/projects`);
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
      }
    } catch (e) {
      console.error("Failed to fetch projects", e);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchProjects();
  }, []);

  const handleCompile = async () => {
    setLoading(true);
    setError("");
    setSchema(null);
    setMetrics(null);

    try {
      const API_URL = "https://ai-software-compiler-ct1g.onrender.com";
      const res = await fetch(`${API_URL}/api/compile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to build");
      
      setSchema(data.data);
      setMetrics(data.metrics);
      setActiveTab("ui");
    } catch (err: unknown) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!schema) return;
    if (!projectName.trim()) {
      alert("Please enter a project name before saving.");
      return;
    }
    setSaving(true);
    try {
      const payload = {
        name: projectName,
        prompt: prompt,
        intent_json: JSON.stringify(schema.intent),
        database_schema_json: JSON.stringify(schema.database_schema),
        api_schema_json: JSON.stringify(schema.api_schema),
        ui_schema_json: JSON.stringify(schema.ui_schema),
        auth_rules_json: JSON.stringify(schema.auth_rules || []),
      };

      const API_URL = "https://ai-software-compiler-ct1g.onrender.com";
      const res = await fetch(`${API_URL}/api/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("Failed to save project");
      alert("Project saved successfully!");
      fetchProjects();
    } catch (err: unknown) {
      alert((err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const loadProject = async (id: number) => {
    try {
      const API_URL = "https://ai-software-compiler-ct1g.onrender.com";
      const res = await fetch(`${API_URL}/api/projects/${id}`);
      if (!res.ok) throw new Error("Failed to load project");
      const data = await res.json();
      setPrompt(data.prompt);
      setProjectName(data.name);
      setSchema({
        intent: data.intent,
        database_schema: data.database_schema,
        api_schema: data.api_schema,
        ui_schema: data.ui_schema,
        auth_rules: data.auth_rules
      });
      setMetrics(null);
    } catch (e: unknown) {
      alert((e as Error).message);
    }
  };

  const handleExport = () => {
    if (!schema) return;
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(schema, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href",     dataStr);
    downloadAnchorNode.setAttribute("download", (projectName || "compiler_output") + ".json");
    document.body.appendChild(downloadAnchorNode); // required for firefox
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  };

  return (
    <div className="flex min-h-screen bg-[#020617] text-white font-sans overflow-hidden relative selection:bg-blue-500/30">
      {/* Background glowing orbs */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-blue-600/20 rounded-full blur-[120px] -translate-y-1/2 pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-[600px] h-[600px] bg-purple-600/10 rounded-full blur-[150px] translate-y-1/3 pointer-events-none" />

      {/* Sidebar */}
      <div className="w-64 relative z-10 bg-[#0f172a]/60 backdrop-blur-2xl border-r border-white/5 flex flex-col p-4 overflow-y-auto shadow-2xl">
        <div className="flex items-center space-x-3 mb-8 px-2 mt-4">
          <div className="w-10 h-10 bg-gradient-to-tr from-blue-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-xl font-extrabold tracking-tight">App Studio</h1>
        </div>
        
        <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4 px-2">Saved Projects</h3>
        {projects.length === 0 ? (
          <p className="text-sm text-gray-500 px-2 italic">No projects yet</p>
        ) : (
          <div className="space-y-2">
            {projects.map((p) => (
              <button 
                key={p.id}
                onClick={() => loadProject(p.id)}
                className="w-full text-left p-3 rounded-xl hover:bg-white/5 transition-all flex items-center space-x-3 border border-transparent hover:border-white/10 group"
              >
                <FolderOpen className="w-4 h-4 text-blue-400 flex-shrink-0 group-hover:scale-110 transition-transform" />
                <span className="text-sm text-gray-300 truncate font-medium">{p.name}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col p-8 overflow-y-auto h-screen relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 flex-1">
          {/* Left Column: Input and Stats */}
          <div className="lg:col-span-4 space-y-6 flex flex-col">
            <div className="bg-white/5 backdrop-blur-xl rounded-2xl p-6 shadow-2xl border border-white/10 relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
              <h2 className="text-xl font-bold mb-4 flex items-center"><Code2 className="w-5 h-5 mr-2 text-blue-400" /> Application Prompt</h2>
              <textarea
                className="w-full h-32 bg-black/40 border border-white/10 rounded-xl p-4 text-sm text-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none resize-none shadow-inner"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
              />
              <button
                onClick={handleCompile}
                disabled={loading}
                className="mt-6 w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold py-3.5 rounded-xl flex items-center justify-center transition-all transform hover:scale-[1.02] shadow-lg shadow-blue-500/25 disabled:opacity-50 disabled:hover:scale-100"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Zap className="w-5 h-5 mr-2" />}
                {loading ? "Building Application..." : "Build Application"}
              </button>
              {error && (
                <div className="mt-4 p-4 bg-red-950/40 border border-red-500/30 rounded-xl flex items-start text-red-400 text-sm backdrop-blur-md">
                  <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0 mt-0.5" />
                  <p>{error}</p>
                </div>
              )}
            </div>

            {/* Pipeline Visualizer */}
            {(loading || schema || error) && (
              <PipelineVisualizer 
                status={loading ? "compiling" : error ? "error" : schema ? "success" : "idle"} 
                metrics={metrics} 
              />
            )}
            
            {/* Save Section */}
            {schema && (
              <div className="bg-white/5 backdrop-blur-xl rounded-2xl p-6 shadow-2xl border border-white/10 relative overflow-hidden mt-6">
                <h2 className="text-xl font-bold mb-4 flex items-center"><Save className="w-5 h-5 mr-2 text-green-400" /> Save Project</h2>
                <input
                  type="text"
                  placeholder="Project Name..."
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  className="w-full bg-black/40 border border-white/10 rounded-xl p-3 text-sm text-gray-200 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all outline-none mb-4 shadow-inner"
                />
                <div className="flex space-x-3">
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white font-bold py-3 rounded-xl flex items-center justify-center transition-all shadow-lg shadow-green-500/20 disabled:opacity-50"
                  >
                    {saving ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Save className="w-5 h-5 mr-2" />}
                    {saving ? "Saving..." : "Save"}
                  </button>
                  <button
                    onClick={handleExport}
                    className="flex-1 bg-white/10 hover:bg-white/20 border border-white/5 text-white font-bold py-3 rounded-xl flex items-center justify-center transition-all backdrop-blur-md"
                  >
                    <Download className="w-5 h-5 mr-2" />
                    Export JSON
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Preview Area */}
          <div className="lg:col-span-8 bg-[#0f172a]/80 backdrop-blur-2xl rounded-2xl shadow-2xl border border-white/10 flex flex-col overflow-hidden h-[85vh]">
            <div className="flex bg-black/20 p-2 space-x-2 border-b border-white/10">
              <button 
                onClick={() => setActiveTab("ui")}
                className={`flex-1 flex items-center justify-center py-3 px-4 text-sm font-bold rounded-xl transition-all duration-200 ${activeTab === 'ui' ? 'bg-blue-500/20 text-blue-400 shadow-inner border border-blue-500/30' : 'text-gray-400 hover:text-gray-200 hover:bg-white/5 border border-transparent'}`}
              >
                <Layout className="w-4 h-4 mr-2" /> UI Preview
              </button>
              <button 
                onClick={() => setActiveTab("db")}
                className={`flex-1 flex items-center justify-center py-3 px-4 text-sm font-bold rounded-xl transition-all duration-200 ${activeTab === 'db' ? 'bg-purple-500/20 text-purple-400 shadow-inner border border-purple-500/30' : 'text-gray-400 hover:text-gray-200 hover:bg-white/5 border border-transparent'}`}
              >
                <Database className="w-4 h-4 mr-2" /> Database Schema
              </button>
              <button 
                onClick={() => setActiveTab("api")}
                className={`flex-1 flex items-center justify-center py-3 px-4 text-sm font-bold rounded-xl transition-all duration-200 ${activeTab === 'api' ? 'bg-rose-500/20 text-rose-400 shadow-inner border border-rose-500/30' : 'text-gray-400 hover:text-gray-200 hover:bg-white/5 border border-transparent'}`}
              >
                <Server className="w-4 h-4 mr-2" /> API Endpoints
              </button>
              <button 
                onClick={() => setActiveTab("metrics")}
                className={`flex-1 flex items-center justify-center py-3 px-4 text-sm font-bold rounded-xl transition-all duration-200 ${activeTab === 'metrics' ? 'bg-green-500/20 text-green-400 shadow-inner border border-green-500/30' : 'text-gray-400 hover:text-gray-200 hover:bg-white/5 border border-transparent'}`}
              >
                <Database className="w-4 h-4 mr-2" /> Metrics
              </button>
            </div>
            
            <div className="flex-1 p-0 bg-[#0f172a]/50 overflow-hidden relative">
               {activeTab === "ui" && (
                 <RuntimePreview schema={schema ? schema.ui_schema : null} />
               )}
               {activeTab === "db" && (
                 <div className="h-full overflow-y-auto p-8 bg-white/50 text-gray-900">
                   <DatabasePreview schema={schema ? schema.database_schema : null} />
                 </div>
               )}
               {activeTab === "api" && (
                 <div className="h-full overflow-y-auto p-8 bg-white/50 text-gray-900">
                   <ApiPreview schema={schema ? schema.api_schema : null} />
                 </div>
               )}
               {activeTab === "metrics" && (
                 <div className="h-full overflow-y-auto p-8 bg-transparent text-white">
                   <h2 className="text-2xl font-black mb-6 tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-600">Compiler Metrics</h2>
                   {metrics ? (
                     <div className="space-y-6">
                       <div className="grid grid-cols-2 gap-6">
                         <div className="bg-black/40 backdrop-blur-md p-6 rounded-2xl border border-white/10 shadow-xl">
                           <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-2">Total Retries</h3>
                           <p className="text-5xl font-black text-yellow-400 drop-shadow-md">{metrics.retries}</p>
                         </div>
                         <div className="bg-black/40 backdrop-blur-md p-6 rounded-2xl border border-white/10 shadow-xl">
                           <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-2">Failures Repaired</h3>
                           <p className="text-5xl font-black text-green-400 drop-shadow-md">{metrics.failures?.length || 0}</p>
                         </div>
                       </div>
                       <div className="bg-black/40 backdrop-blur-md p-6 rounded-2xl border border-white/10 shadow-xl">
                          <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-4 flex items-center"><Zap className="w-4 h-4 mr-2 text-blue-400" /> Repair Logs</h3>
                          <div className="bg-[#020617] rounded-xl p-4 border border-white/5 overflow-x-auto">
                            <pre className="text-xs text-blue-300 font-mono leading-relaxed">
                              {JSON.stringify(metrics.failures, null, 2)}
                            </pre>
                          </div>
                       </div>
                     </div>
                   ) : (
                     <div className="flex flex-col items-center justify-center h-64 text-center">
                       <Database className="w-12 h-12 text-gray-600 mb-4" />
                       <p className="text-gray-400 font-medium">No metrics available.<br/>Compile an application to generate telemetry.</p>
                     </div>
                   )}
                 </div>
               )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

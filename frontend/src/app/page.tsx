"use client";

import React, { useState, useEffect } from "react";
import RuntimePreview from "@/components/RuntimePreview";
import DatabasePreview from "@/components/DatabasePreview";
import ApiPreview from "@/components/ApiPreview";
import PipelineVisualizer from "@/components/PipelineVisualizer";
import { Loader2, Zap, Layout, Code2, Database, Server, Save, FolderOpen, AlertCircle } from "lucide-react";

export default function Dashboard() {
  const [prompt, setPrompt] = useState("Build a Habit Tracker app with premium tiers, daily check-ins, and Stripe integration. Include a user dashboard, a subscription form, and a chat interface.");
  const [projectName, setProjectName] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [schema, setSchema] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [error, setError] = useState("");
  
  const [activeTab, setActiveTab] = useState<"ui" | "db" | "api">("ui");
  const [projects, setProjects] = useState<any[]>([]);

  const fetchProjects = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/projects");
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
      }
    } catch (e) {
      console.error("Failed to fetch projects", e);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

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
      if (!res.ok) throw new Error(data.detail || "Failed to build");
      
      setSchema(data.data);
      setMetrics(data.metrics);
      setActiveTab("ui");
    } catch (err: any) {
      setError(err.message);
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

      const res = await fetch("http://localhost:8000/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("Failed to save project");
      alert("Project saved successfully!");
      fetchProjects();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setSaving(false);
    }
  };

  const loadProject = async (id: number) => {
    try {
      const res = await fetch(`http://localhost:8000/api/projects/${id}`);
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
    } catch (e: any) {
      alert(e.message);
    }
  };

  return (
    <div className="flex min-h-screen bg-[#0f172a] text-white font-sans overflow-hidden">
      
      {/* Sidebar */}
      <div className="w-64 bg-[#1e293b] border-r border-[#334155] flex flex-col p-4 overflow-y-auto">
        <div className="flex items-center space-x-3 mb-8 px-2 mt-4">
          <Zap className="w-8 h-8 text-blue-500" />
          <h1 className="text-2xl font-extrabold tracking-tight">App Studio</h1>
        </div>
        
        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4 px-2">Saved Projects</h3>
        {projects.length === 0 ? (
          <p className="text-sm text-gray-500 px-2 italic">No projects yet</p>
        ) : (
          <div className="space-y-2">
            {projects.map((p) => (
              <button 
                key={p.id}
                onClick={() => loadProject(p.id)}
                className="w-full text-left p-3 rounded-lg hover:bg-[#334155] transition-colors flex items-center space-x-2 border border-transparent hover:border-gray-600"
              >
                <FolderOpen className="w-4 h-4 text-blue-400 flex-shrink-0" />
                <span className="text-sm text-gray-300 truncate">{p.name}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col p-8 overflow-y-auto h-screen">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 flex-1">
          {/* Left Column: Input and Stats */}
          <div className="lg:col-span-4 space-y-6 flex flex-col">
            <div className="bg-[#1e293b] rounded-2xl p-6 shadow-xl border border-[#334155]">
              <h2 className="text-xl font-bold mb-4 flex items-center"><Code2 className="w-5 h-5 mr-2 text-blue-400" /> Application Prompt</h2>
              <textarea
                className="w-full h-32 bg-[#0f172a] border border-[#334155] rounded-xl p-4 text-sm text-gray-200 focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
              />
              <button
                onClick={handleCompile}
                disabled={loading}
                className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-xl flex items-center justify-center transition-all disabled:opacity-50"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Zap className="w-5 h-5 mr-2" />}
                {loading ? "Building Application..." : "Build Application"}
              </button>
              {error && (
                <div className="mt-3 p-3 bg-red-900/30 border border-red-500/50 rounded-lg flex items-start text-red-400 text-sm">
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
              <div className="bg-[#1e293b] rounded-2xl p-6 shadow-xl border border-[#334155]">
                <h2 className="text-xl font-bold mb-4 flex items-center"><Save className="w-5 h-5 mr-2 text-green-400" /> Save Project</h2>
                <input
                  type="text"
                  placeholder="Project Name..."
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  className="w-full bg-[#0f172a] border border-[#334155] rounded-xl p-3 text-sm text-gray-200 focus:ring-2 focus:ring-green-500 outline-none mb-4"
                />
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 rounded-xl flex items-center justify-center transition-all disabled:opacity-50"
                >
                  {saving ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Save className="w-5 h-5 mr-2" />}
                  {saving ? "Saving..." : "Save to Workspace"}
                </button>
              </div>
            )}
          </div>

          {/* Right Column: Preview Area */}
          <div className="lg:col-span-8 bg-[#1e293b] rounded-2xl shadow-xl border border-[#334155] flex flex-col overflow-hidden h-[85vh]">
            <div className="flex bg-[#334155]/50 border-b border-[#334155]">
              <button 
                onClick={() => setActiveTab("ui")}
                className={`flex-1 flex items-center justify-center py-4 text-sm font-bold border-b-2 transition-colors ${activeTab === 'ui' ? 'border-blue-500 text-blue-400 bg-[#334155]' : 'border-transparent text-gray-400 hover:text-gray-200 hover:bg-[#334155]/50'}`}
              >
                <Layout className="w-4 h-4 mr-2" /> UI Preview
              </button>
              <button 
                onClick={() => setActiveTab("db")}
                className={`flex-1 flex items-center justify-center py-4 text-sm font-bold border-b-2 transition-colors ${activeTab === 'db' ? 'border-purple-500 text-purple-400 bg-[#334155]' : 'border-transparent text-gray-400 hover:text-gray-200 hover:bg-[#334155]/50'}`}
              >
                <Database className="w-4 h-4 mr-2" /> Database Schema
              </button>
              <button 
                onClick={() => setActiveTab("api")}
                className={`flex-1 flex items-center justify-center py-4 text-sm font-bold border-b-2 transition-colors ${activeTab === 'api' ? 'border-rose-500 text-rose-400 bg-[#334155]' : 'border-transparent text-gray-400 hover:text-gray-200 hover:bg-[#334155]/50'}`}
              >
                <Server className="w-4 h-4 mr-2" /> API Endpoints
              </button>
              <button 
                onClick={() => setActiveTab("metrics")}
                className={`flex-1 flex items-center justify-center py-4 text-sm font-bold border-b-2 transition-colors ${activeTab === 'metrics' ? 'border-green-500 text-green-400 bg-[#334155]' : 'border-transparent text-gray-400 hover:text-gray-200 hover:bg-[#334155]/50'}`}
              >
                <Database className="w-4 h-4 mr-2" /> Metrics
              </button>
            </div>
            
            <div className="flex-1 p-0 bg-gray-100 overflow-hidden relative">
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
                 <div className="h-full overflow-y-auto p-8 bg-[#1e293b] text-white">
                   <h2 className="text-2xl font-bold mb-4">Compiler Metrics</h2>
                   {metrics ? (
                     <div className="space-y-4">
                       <div className="bg-[#0f172a] p-4 rounded-xl border border-[#334155]">
                         <h3 className="text-gray-400 mb-1">Total Retries</h3>
                         <p className="text-3xl font-bold text-yellow-400">{metrics.retries}</p>
                       </div>
                       <div className="bg-[#0f172a] p-4 rounded-xl border border-[#334155]">
                         <h3 className="text-gray-400 mb-1">Failures Repaired</h3>
                         <p className="text-3xl font-bold text-green-400">{metrics.failures?.length || 0}</p>
                       </div>
                       <div className="bg-[#0f172a] p-4 rounded-xl border border-[#334155]">
                          <h3 className="text-gray-400 mb-2">Repair Logs</h3>
                          <pre className="text-xs text-gray-300 overflow-x-auto">
                            {JSON.stringify(metrics.failures, null, 2)}
                          </pre>
                       </div>
                     </div>
                   ) : (
                     <p className="text-gray-500">No metrics available. Compile an application first.</p>
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

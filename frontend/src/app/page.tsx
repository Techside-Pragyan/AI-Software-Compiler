"use client";

import React from "react";
import { motion } from "framer-motion";
import { ArrowRight, Cpu, GitMerge, Layers, Zap } from "lucide-react";
import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#020617] text-white overflow-hidden relative selection:bg-blue-500/30">
      {/* Background glowing orbs */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-blue-600/20 rounded-full blur-[120px] -translate-y-1/2 pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-[600px] h-[600px] bg-purple-600/10 rounded-full blur-[150px] translate-y-1/3 pointer-events-none" />

      <nav className="relative z-10 flex items-center justify-between px-8 py-6 max-w-7xl mx-auto">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-tr from-blue-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <span className="text-xl font-extrabold tracking-tight">App Compiler</span>
        </div>
        <div className="flex items-center space-x-6 text-sm font-medium">
          <a href="#" className="text-gray-400 hover:text-white transition-colors">Documentation</a>
          <a href="#" className="text-gray-400 hover:text-white transition-colors">Architecture</a>
          <Link href="/dashboard" className="px-5 py-2.5 bg-white/10 hover:bg-white/20 border border-white/10 rounded-lg backdrop-blur-md transition-all">
            Open Studio
          </Link>
        </div>
      </nav>

      <main className="relative z-10 flex flex-col items-center justify-center text-center px-4 pt-32 pb-20 max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm font-medium mb-8"
        >
          <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          <span>v2.0 Multi-Stage Engine Live</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-6xl md:text-8xl font-black tracking-tight leading-[1.1] mb-8"
        >
          Compile Ideas Into <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400">
            Software Infrastructure.
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-12 leading-relaxed"
        >
          A deterministic AI compiler pipeline that transforms natural language into production-grade UI, API, and Database schemas with self-healing validation.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="flex items-center justify-center space-x-4"
        >
          <Link href="/dashboard" className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold shadow-lg shadow-blue-500/30 flex items-center transition-all group">
            Start Compiling
            <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
          </Link>
          <a href="https://github.com/pragyan/AI-Software-Compiler" className="px-8 py-4 bg-[#1e293b] hover:bg-[#334155] border border-[#334155] text-white rounded-xl font-bold transition-all">
            View Source
          </a>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="mt-32 grid grid-cols-1 md:grid-cols-3 gap-8 w-full text-left"
        >
          {[
            { icon: Layers, title: "Multi-Stage Pipeline", desc: "No single-prompt generation. Step-by-step orchestration ensures deterministic output." },
            { icon: GitMerge, title: "Cross-Layer Validation", desc: "Strict heuristic checks ensure UI pages map to valid API endpoints and database schemas." },
            { icon: Cpu, title: "Selective Repair Engine", desc: "Automatically detects validation errors and repairs only the broken schema layer." }
          ].map((feature, i) => (
            <div key={i} className="p-6 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors backdrop-blur-sm group">
              <feature.icon className="w-10 h-10 text-blue-400 mb-4 group-hover:scale-110 transition-transform" />
              <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
              <p className="text-gray-400 leading-relaxed text-sm">{feature.desc}</p>
            </div>
          ))}
        </motion.div>
      </main>
    </div>
  );
}

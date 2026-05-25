"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface UiComponent {
  name: string;
  type: string;
  props?: Record<string, unknown>;
  children?: string[];
}

interface UiPage {
  route: string;
  name: string;
  layout: string;
  components: UiComponent[];
}

interface UiSchema {
  pages: UiPage[];
  navigation: string[];
}

export default function RuntimePreview({ schema }: { schema: UiSchema | null }) {
  const [currentRoute, setCurrentRoute] = useState<string>("/");

  if (!schema || !schema.pages || schema.pages.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-gray-500">
        <p>No UI Schema generated yet. Enter a prompt to build the app.</p>
      </div>
    );
  }

  const currentPage = schema.pages.find((p) => p.route === currentRoute) || schema.pages[0];

  const renderComponent = (comp: UiComponent, idx: number) => {
    switch (comp.type.toLowerCase()) {
      case "card":
        return (
          <div key={idx} className="p-6 bg-white shadow rounded-xl border border-gray-100">
            <h3 className="text-lg font-bold">{comp.name}</h3>
            {comp.props?.description && <p className="text-sm text-gray-600 mt-2">{comp.props.description}</p>}
          </div>
        );
      case "list":
        return (
          <div key={idx} className="bg-white shadow rounded-xl border border-gray-100 p-4">
            <h3 className="text-md font-bold mb-4">{comp.name}</h3>
            <ul className="space-y-2">
              <li className="p-3 bg-gray-50 rounded-lg text-sm">Item 1 (Mock)</li>
              <li className="p-3 bg-gray-50 rounded-lg text-sm">Item 2 (Mock)</li>
            </ul>
          </div>
        );
      case "form":
        return (
          <form key={idx} className="p-6 bg-white shadow rounded-xl border border-gray-100 space-y-4">
            <h3 className="text-lg font-bold mb-4">{comp.name}</h3>
            <div>
              <label className="block text-sm font-medium text-gray-700">Mock Input</label>
              <input type="text" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border" />
            </div>
            <button type="button" className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm w-full">Submit</button>
          </form>
        );
      case "dashboard":
        return (
          <div key={idx} className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 bg-blue-50 text-blue-800 rounded-xl font-bold">Metric 1</div>
            <div className="p-6 bg-green-50 text-green-800 rounded-xl font-bold">Metric 2</div>
            <div className="p-6 bg-purple-50 text-purple-800 rounded-xl font-bold">Metric 3</div>
          </div>
        );
      default:
        return (
          <div key={idx} className="p-4 border border-dashed border-gray-300 rounded-lg bg-gray-50 text-center">
            <p className="text-sm text-gray-500">Generic Component: {comp.name} ({comp.type})</p>
          </div>
        );
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50 rounded-xl overflow-hidden border border-gray-200 shadow-inner">
      {/* Dynamic Navigation Bar */}
      <nav className="bg-white border-b px-6 py-4 flex space-x-6">
        <div className="font-bold text-xl mr-8 text-blue-600">DynamicApp</div>
        {schema.navigation.map((navRoute) => (
          <button
            key={navRoute}
            onClick={() => setCurrentRoute(navRoute)}
            className={`text-sm font-medium ${
              currentRoute === navRoute ? "text-blue-600 border-b-2 border-blue-600" : "text-gray-500 hover:text-gray-900"
            }`}
          >
            {navRoute}
          </button>
        ))}
      </nav>

      {/* Dynamic Page Content */}
      <div className="flex-1 p-8 overflow-y-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentRoute}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="space-y-6 max-w-5xl mx-auto"
          >
            <div className="mb-8">
              <h1 className="text-3xl font-extrabold text-gray-900">{currentPage.name}</h1>
              <p className="text-gray-500 text-sm mt-1">Layout: {currentPage.layout}</p>
            </div>

            {currentPage.components.map((comp, idx) => renderComponent(comp, idx))}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}

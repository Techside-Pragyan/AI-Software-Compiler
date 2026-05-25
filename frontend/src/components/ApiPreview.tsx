"use client";
import React from "react";
import { Server, Lock, Globe } from "lucide-react";

interface ApiEndpointSchema {
  method: string;
  path: string;
  description: string;
  request_schema_ref?: string;
  response_schema_ref?: string;
  protected: boolean;
  allowed_roles?: string[];
}

export default function ApiPreview({ schema }: { schema: { endpoints: ApiEndpointSchema[] } | null }) {
  if (!schema || !schema.endpoints) {
    return <div className="text-gray-500 text-center mt-10 p-8 border border-dashed rounded-xl">No API schema generated.</div>;
  }

  const getMethodColor = (method: string) => {
    switch (method.toUpperCase()) {
      case "GET": return "bg-blue-100 text-blue-700 border-blue-200";
      case "POST": return "bg-green-100 text-green-700 border-green-200";
      case "PUT": return "bg-amber-100 text-amber-700 border-amber-200";
      case "DELETE": return "bg-red-100 text-red-700 border-red-200";
      default: return "bg-gray-100 text-gray-700 border-gray-200";
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10">
      <div className="mb-6 flex items-center space-x-2 border-b pb-4">
        <Server className="w-6 h-6 text-rose-500" />
        <h2 className="text-2xl font-bold text-gray-800">REST API Endpoints</h2>
      </div>
      
      <div className="space-y-4">
        {schema.endpoints.map((ep, i) => (
          <div key={i} className="bg-white border border-gray-200 shadow-sm rounded-xl overflow-hidden flex flex-col">
            <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
              <div className="flex items-center space-x-3">
                <span className={`px-2 py-1 text-xs font-bold rounded-md border ${getMethodColor(ep.method)}`}>
                  {ep.method.toUpperCase()}
                </span>
                <span className="font-mono text-sm text-gray-800 font-medium">{ep.path}</span>
              </div>
              <div>
                {ep.protected ? (
                  <div className="flex items-center text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded-md border border-amber-100">
                    <Lock className="w-3 h-3 mr-1" /> Protected
                  </div>
                ) : (
                  <div className="flex items-center text-xs text-green-600 bg-green-50 px-2 py-1 rounded-md border border-green-100">
                    <Globe className="w-3 h-3 mr-1" /> Public
                  </div>
                )}
              </div>
            </div>
            
            <div className="px-5 py-4 text-sm text-gray-600">
              <p className="mb-4">{ep.description}</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                {ep.request_schema_ref && (
                  <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
                    <span className="block text-xs font-bold text-gray-500 mb-1 uppercase tracking-wider">Request Payload</span>
                    <code className="text-xs text-indigo-600">{ep.request_schema_ref}</code>
                  </div>
                )}
                {ep.response_schema_ref && (
                  <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
                    <span className="block text-xs font-bold text-gray-500 mb-1 uppercase tracking-wider">Response</span>
                    <code className="text-xs text-indigo-600">{ep.response_schema_ref}</code>
                  </div>
                )}
              </div>
              
              {ep.allowed_roles && ep.allowed_roles.length > 0 && (
                <div className="mt-4 pt-3 border-t border-gray-100 text-xs">
                  <span className="text-gray-500 font-medium mr-2">Roles:</span>
                  {ep.allowed_roles.map((role, rIndex) => (
                    <span key={rIndex} className="inline-block bg-gray-200 text-gray-700 px-2 py-0.5 rounded mr-1">
                      {role}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

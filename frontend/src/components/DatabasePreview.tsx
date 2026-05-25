"use client";
import React from "react";
import { Database, Table, Key, Hash } from "lucide-react";

interface FieldSchema {
  name: string;
  type: string;
  required: boolean;
  constraints?: string;
}

interface TableSchema {
  name: string;
  fields: FieldSchema[];
  relationships: string[];
  indexes: string[];
}

export default function DatabasePreview({ schema }: { schema: { tables: TableSchema[] } | null }) {
  if (!schema || !schema.tables) {
    return <div className="text-gray-500 text-center mt-10 p-8 border border-dashed rounded-xl">No database schema generated.</div>;
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10">
      <div className="mb-6 flex items-center space-x-2 border-b pb-4">
        <Database className="w-6 h-6 text-indigo-500" />
        <h2 className="text-2xl font-bold text-gray-800">Database Schema</h2>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {schema.tables.map((table, i) => (
          <div key={i} className="bg-white border border-gray-200 shadow-sm rounded-xl overflow-hidden">
            <div className="bg-indigo-50/50 border-b border-gray-200 px-4 py-3 flex items-center">
              <Table className="w-5 h-5 text-indigo-600 mr-2" />
              <h3 className="font-bold text-gray-900">{table.name}</h3>
            </div>
            <div className="p-0">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-gray-500 bg-gray-50 border-b">
                  <tr>
                    <th className="px-4 py-2">Field</th>
                    <th className="px-4 py-2">Type</th>
                    <th className="px-4 py-2 text-center">Required</th>
                  </tr>
                </thead>
                <tbody>
                  {table.fields.map((field, j) => (
                    <tr key={j} className="border-b last:border-0 hover:bg-gray-50/50">
                      <td className="px-4 py-3 font-medium text-gray-900 flex items-center">
                        {field.name.includes("id") ? <Key className="w-3 h-3 text-amber-500 mr-1.5" /> : <Hash className="w-3 h-3 text-gray-400 mr-1.5" />}
                        {field.name}
                      </td>
                      <td className="px-4 py-3 text-indigo-600 font-mono text-xs">{field.type}</td>
                      <td className="px-4 py-3 text-center">
                        {field.required ? (
                          <span className="bg-green-100 text-green-800 text-[10px] px-2 py-0.5 rounded-full font-medium">Yes</span>
                        ) : (
                          <span className="text-gray-400 text-xs">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {table.relationships && table.relationships.length > 0 && (
              <div className="px-4 py-3 bg-gray-50 border-t border-gray-100 text-xs text-gray-600">
                <strong>Relations:</strong> {table.relationships.join(", ")}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

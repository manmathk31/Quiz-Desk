import React, { useState, useEffect } from 'react'
import { Server, CheckCircle2, Shield, Layers, RefreshCw } from 'lucide-react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const Overview: React.FC = () => {
  const [apiStatus, setApiStatus] = useState<'checking' | 'connected' | 'unreachable'>('checking')

  const checkHealth = async () => {
    setApiStatus('checking')
    try {
      const res = await fetch(`${API_BASE_URL}/health`)
      if (res.ok) {
        setApiStatus('connected')
      } else {
        setApiStatus('unreachable')
      }
    } catch {
      setApiStatus('unreachable')
    }
  }

  useEffect(() => {
    checkHealth()
  }, [])

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <h1 className="text-xl sm:text-2xl font-bold text-slate-900">System Foundation Diagnostics</h1>
        <p className="text-sm text-slate-600 mt-1">
          Verification overview for Quizdesk modular monolith core subsystems.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Backend Status Box */}
        <div className="bg-white border border-slate-200 rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2.5">
              <Server className="w-5 h-5 text-slate-700" />
              <h2 className="font-semibold text-slate-900">Backend API Service</h2>
            </div>
            <button
              onClick={checkHealth}
              className="inline-flex items-center text-xs text-blue-600 hover:text-blue-800 font-medium cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5 mr-1" />
              Re-check
            </button>
          </div>

          <div className="space-y-2.5 text-sm">
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Framework</span>
              <span className="font-medium text-slate-800">Python 3.13 / FastAPI 0.115</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Health Endpoint</span>
              <span className="font-mono text-xs text-slate-700">GET /health</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Live Status</span>
              <span>
                {apiStatus === 'connected' && (
                  <span className="inline-flex items-center text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded text-xs font-medium border border-emerald-200">
                    <CheckCircle2 className="w-3 h-3 mr-1 text-emerald-600" />
                    Responding 200 OK
                  </span>
                )}
                {apiStatus === 'unreachable' && (
                  <span className="inline-flex items-center text-slate-600 bg-slate-100 px-2 py-0.5 rounded text-xs font-medium border border-slate-200">
                    Dev Server Standby (Port 8000)
                  </span>
                )}
                {apiStatus === 'checking' && (
                  <span className="text-xs text-slate-400">Pinging...</span>
                )}
              </span>
            </div>
          </div>
        </div>

        {/* Frontend Status Box */}
        <div className="bg-white border border-slate-200 rounded-lg p-5">
          <div className="flex items-center space-x-2.5 mb-4">
            <Layers className="w-5 h-5 text-slate-700" />
            <h2 className="font-semibold text-slate-900">Frontend Client Layer</h2>
          </div>

          <div className="space-y-2.5 text-sm">
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Stack</span>
              <span className="font-medium text-slate-800">React 19 / TypeScript / Vite 8</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Styling System</span>
              <span className="font-medium text-slate-800">Tailwind CSS v4 (Native Vite Plugin)</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Routing</span>
              <span className="font-medium text-slate-800">React Router v7</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Iconography</span>
              <span className="font-medium text-slate-800">Lucide React</span>
            </div>
          </div>
        </div>
      </div>

      {/* Governance & Specifications */}
      <div className="bg-white border border-slate-200 rounded-lg p-5">
        <div className="flex items-center space-x-2.5 mb-3">
          <Shield className="w-5 h-5 text-slate-700" />
          <h2 className="font-semibold text-slate-900">Project Governance Baseline</h2>
        </div>
        <p className="text-sm text-slate-600 mb-4">
          All changes are governed strictly by authoritative ADRs recorded in repository documentation:
        </p>
        <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs text-slate-700">
          <li className="p-2.5 bg-slate-50 rounded border border-slate-200">
            <strong className="text-slate-900">DEC-001</strong>: Modular Monolith Architecture
          </li>
          <li className="p-2.5 bg-slate-50 rounded border border-slate-200">
            <strong className="text-slate-900">DEC-002</strong>: Technology Stack (FastAPI + React TS)
          </li>
          <li className="p-2.5 bg-slate-50 rounded border border-slate-200">
            <strong className="text-slate-900">DEC-003</strong>: Isolated Python venv & Zero Secret Policy
          </li>
          <li className="p-2.5 bg-slate-50 rounded border border-slate-200">
            <strong className="text-slate-900">DEC-004</strong>: Minimalist Academic Visual Design System
          </li>
        </ul>
      </div>
    </div>
  )
}

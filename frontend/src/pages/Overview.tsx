import React, { useState, useEffect, useCallback } from 'react'
import {
  Server,
  CheckCircle2,
  AlertCircle,
  Database,
  Layers,
  RefreshCw,
  Cpu,
  Lock,
} from 'lucide-react'
import { isSupabaseConfigured } from '../lib/supabase'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface SubsystemProbe {
  status: 'checking' | 'connected' | 'unreachable'
  latencyMs: number | null
  lastChecked: string | null
  detail?: string
}

export const Overview: React.FC = () => {
  const [apiProbe, setApiProbe] = useState<SubsystemProbe>({
    status: 'checking',
    latencyMs: null,
    lastChecked: null,
  })
  const [dbProbe, setDbProbe] = useState<SubsystemProbe>({
    status: 'checking',
    latencyMs: null,
    lastChecked: null,
  })
  const [isRefreshing, setIsRefreshing] = useState(false)

  const checkHealth = useCallback(async () => {
    setIsRefreshing(true)
    setApiProbe((prev) => ({ ...prev, status: 'checking' }))
    setDbProbe((prev) => ({ ...prev, status: 'checking' }))

    // 1. Probe API Liveness & measure round-trip latency
    try {
      const start = performance.now()
      const res = await fetch(`${API_BASE_URL}/health/live`)
      const elapsed = Math.round(performance.now() - start)
      if (res.ok) {
        setApiProbe({
          status: 'connected',
          latencyMs: elapsed,
          lastChecked: new Date().toLocaleTimeString(),
          detail: 'HTTP 200 OK — Process Alive',
        })
      } else {
        setApiProbe({
          status: 'unreachable',
          latencyMs: elapsed,
          lastChecked: new Date().toLocaleTimeString(),
          detail: `HTTP ${res.status}`,
        })
      }
    } catch {
      setApiProbe({
        status: 'unreachable',
        latencyMs: null,
        lastChecked: new Date().toLocaleTimeString(),
        detail: 'Network Timeout / Backend Standby',
      })
    }

    // 2. Probe Database Readiness
    try {
      const start = performance.now()
      const res = await fetch(`${API_BASE_URL}/health/ready`)
      const elapsed = Math.round(performance.now() - start)
      if (res.ok) {
        setDbProbe({
          status: 'connected',
          latencyMs: elapsed,
          lastChecked: new Date().toLocaleTimeString(),
          detail: 'PostgreSQL Connection Verified (SELECT 1)',
        })
      } else {
        setDbProbe({
          status: 'unreachable',
          latencyMs: elapsed,
          lastChecked: new Date().toLocaleTimeString(),
          detail: `HTTP ${res.status} Readiness Failure`,
        })
      }
    } catch {
      setDbProbe({
        status: 'unreachable',
        latencyMs: null,
        lastChecked: new Date().toLocaleTimeString(),
        detail: 'Database Probe Standby',
      })
    } finally {
      setIsRefreshing(false)
    }
  }, [])

  useEffect(() => {
    checkHealth()
  }, [checkHealth])

  const allOperational = apiProbe.status === 'connected' && dbProbe.status === 'connected'

  return (
    <div className="space-y-6 max-w-5xl mx-auto py-2">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2.5 mb-1.5">
              <span className="relative flex h-3 w-3">
                <span
                  className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                    allOperational ? 'bg-emerald-400' : 'bg-amber-400'
                  }`}
                ></span>
                <span
                  className={`relative inline-flex rounded-full h-3 w-3 ${
                    allOperational ? 'bg-emerald-500' : 'bg-amber-500'
                  }`}
                ></span>
              </span>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Live Subsystem Telemetry
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              System Foundation Diagnostics
            </h1>
            <p className="text-sm text-slate-600 mt-1">
              Real-time health probes, latency verification, and runtime metrics for Quizdesk.
            </p>
          </div>

          <button
            type="button"
            onClick={checkHealth}
            disabled={isRefreshing}
            className="self-start sm:self-auto inline-flex items-center space-x-2 px-4 py-2.5 bg-slate-900 hover:bg-slate-800 active:bg-slate-950 text-white rounded-xl text-xs font-semibold shadow-sm transition-all disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>{isRefreshing ? 'Probing...' : 'Re-probe Subsystems'}</span>
          </button>
        </div>
      </div>

      {/* Primary Telemetry Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Backend API Service */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
                <Server className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-900">Backend API Gateway</h2>
                <p className="text-xs text-slate-500">FastAPI 0.115 / Python 3.13</p>
              </div>
            </div>

            {apiProbe.status === 'connected' ? (
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-600" />
                Operational
              </span>
            ) : apiProbe.status === 'checking' ? (
              <span className="text-xs text-slate-400 font-mono">Pinging...</span>
            ) : (
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
                <AlertCircle className="w-3.5 h-3.5 mr-1 text-slate-500" />
                Standby
              </span>
            )}
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center py-2 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Liveness Endpoint</span>
              <code className="text-[11px] bg-slate-100 px-2 py-0.5 rounded font-mono text-slate-700">
                GET /health/live
              </code>
            </div>

            <div className="flex justify-between items-center py-2 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Round-trip Latency</span>
              <span className="font-mono font-semibold text-slate-800">
                {apiProbe.latencyMs !== null ? (
                  <span
                    className={
                      apiProbe.latencyMs < 100
                        ? 'text-emerald-600'
                        : apiProbe.latencyMs < 300
                        ? 'text-amber-600'
                        : 'text-rose-600'
                    }
                  >
                    {apiProbe.latencyMs} ms
                  </span>
                ) : (
                  '--'
                )}
              </span>
            </div>

            <div className="flex justify-between items-center py-2">
              <span className="text-slate-500 font-medium">Diagnostics</span>
              <span className="text-slate-700 font-mono text-[11px]">{apiProbe.detail || '--'}</span>
            </div>
          </div>
        </div>

        {/* Database Connectivity Probe */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
                <Database className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-900">PostgreSQL Database</h2>
                <p className="text-xs text-slate-500">Managed Supabase Engine</p>
              </div>
            </div>

            {dbProbe.status === 'connected' ? (
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-600" />
                Ready
              </span>
            ) : dbProbe.status === 'checking' ? (
              <span className="text-xs text-slate-400 font-mono">Querying...</span>
            ) : (
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
                <AlertCircle className="w-3.5 h-3.5 mr-1 text-slate-500" />
                Standby
              </span>
            )}
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center py-2 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Readiness Probe</span>
              <code className="text-[11px] bg-slate-100 px-2 py-0.5 rounded font-mono text-slate-700">
                GET /health/ready
              </code>
            </div>

            <div className="flex justify-between items-center py-2 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Query Latency</span>
              <span className="font-mono font-semibold text-slate-800">
                {dbProbe.latencyMs !== null ? (
                  <span
                    className={
                      dbProbe.latencyMs < 150
                        ? 'text-emerald-600'
                        : dbProbe.latencyMs < 400
                        ? 'text-amber-600'
                        : 'text-rose-600'
                    }
                  >
                    {dbProbe.latencyMs} ms
                  </span>
                ) : (
                  '--'
                )}
              </span>
            </div>

            <div className="flex justify-between items-center py-2">
              <span className="text-slate-500 font-medium">Connection Status</span>
              <span className="text-slate-700 font-mono text-[11px]">{dbProbe.detail || '--'}</span>
            </div>
          </div>
        </div>

        {/* Supabase Identity & Auth Engine */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600">
                <Lock className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-900">Supabase Auth Layer</h2>
                <p className="text-xs text-slate-500">JWT Token Validation & Identity</p>
              </div>
            </div>

            {isSupabaseConfigured ? (
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-600" />
                Configured
              </span>
            ) : (
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-800 border border-amber-200">
                <AlertCircle className="w-3.5 h-3.5 mr-1 text-amber-600" />
                Development Mode
              </span>
            )}
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center py-2 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Algorithm</span>
              <span className="font-mono text-slate-800">HS256 / Symmetric Signature</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Authority Boundary</span>
              <span className="text-slate-800 font-medium">Server-side users.role (DEC-015)</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-slate-500 font-medium">Role Self-Promotion</span>
              <span className="inline-flex items-center text-emerald-700 font-medium">
                Blocked at API Gate
              </span>
            </div>
          </div>
        </div>

        {/* Frontend Edge Layer */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-violet-50 border border-violet-100 flex items-center justify-center text-violet-600">
                <Layers className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-900">Frontend Edge Layer</h2>
                <p className="text-xs text-slate-500">Cloudflare Pages Global CDN</p>
              </div>
            </div>

            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
              <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-600" />
              Edge Active
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center py-2 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Engine & Bundler</span>
              <span className="font-medium text-slate-800">React 19 / TypeScript / Vite 8</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Styling Architecture</span>
              <span className="font-medium text-slate-800">Tailwind CSS v4</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-slate-500 font-medium">Client Security</span>
              <span className="text-slate-800 font-medium">Zero Bundled Secrets (DEC-003)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Architecture & Governance Baseline */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center space-x-2.5 mb-3">
          <Cpu className="w-5 h-5 text-slate-700" />
          <h2 className="font-bold text-slate-900 text-base">Architectural Invariants & SLA</h2>
        </div>
        <p className="text-xs text-slate-600 mb-4 leading-relaxed">
          Quizdesk is engineered to sustain high-concurrency synchronized examination traffic with atomic server-authoritative submission deadlines and zero client answer leakage.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80">
            <div className="text-slate-500 text-[11px] mb-1">State Consistency</div>
            <div className="font-bold text-slate-900">Atomic Autosaves</div>
            <div className="text-[11px] text-slate-500 mt-1">No lost answers on drop</div>
          </div>
          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80">
            <div className="text-slate-500 text-[11px] mb-1">Integrity Gate</div>
            <div className="font-bold text-slate-900">Immutable Quiz Snapshots</div>
            <div className="text-[11px] text-slate-500 mt-1">Published versions locked</div>
          </div>
          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80">
            <div className="text-slate-500 text-[11px] mb-1">Security Standard</div>
            <div className="font-bold text-slate-900">Server-Side Roster Check</div>
            <div className="text-[11px] text-slate-500 mt-1">PRN + Email dual verification</div>
          </div>
        </div>
      </div>
    </div>
  )
}

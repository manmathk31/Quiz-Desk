import React from 'react'
import { Shield, Server } from 'lucide-react'

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 border-t border-slate-800 text-slate-400 text-sm mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <Shield className="w-4 h-4 text-blue-400" />
            <span className="font-medium text-slate-300">Quizdesk Assessment Platform</span>
            <span className="text-slate-600">|</span>
            <span className="text-xs text-slate-400">Institutional Governance & Exam Delivery</span>
          </div>

          <div className="flex items-center space-x-4 text-xs">
            <span className="flex items-center gap-1.5 text-slate-400">
              <Server className="w-3.5 h-3.5 text-emerald-400" />
              FastAPI Modular Monolith
            </span>
            <span className="text-slate-700">|</span>
            <span className="font-mono text-slate-500">v0.1.0-alpha</span>
          </div>
        </div>
      </div>
    </footer>
  )
}

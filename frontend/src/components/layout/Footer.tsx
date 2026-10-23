import React from 'react'
import { Shield } from 'lucide-react'

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

          <div className="flex items-center space-x-4 text-xs text-slate-500">
            <span>MIT Academy of Engineering</span>
            <span className="text-slate-700">•</span>
            <span>Secure Examination Environment</span>
          </div>
        </div>
      </div>
    </footer>
  )
}

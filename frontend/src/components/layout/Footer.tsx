import React from 'react'
import { Link } from 'react-router-dom'
import { Activity } from 'lucide-react'

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 border-t border-slate-800 text-slate-400 text-sm mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-300">Quizdesk</span>
            <span className="text-slate-600">•</span>
            <span className="text-slate-400">MIT Academy of Engineering</span>
          </div>

          <div className="flex items-center space-x-4 text-slate-400">
            <Link to="/student/login" className="hover:text-slate-200 transition-colors">
              Student Entrance
            </Link>
            <span className="text-slate-700">•</span>
            <Link to="/teacher/login" className="hover:text-slate-200 transition-colors">
              Faculty Portal
            </Link>
            <span className="text-slate-700">•</span>
            <Link
              to="/status"
              className="inline-flex items-center space-x-1 text-slate-400 hover:text-emerald-400 transition-colors"
            >
              <Activity className="w-3 h-3 text-emerald-500" />
              <span>System Status</span>
            </Link>
          </div>
        </div>
      </div>
    </footer>
  )
}
